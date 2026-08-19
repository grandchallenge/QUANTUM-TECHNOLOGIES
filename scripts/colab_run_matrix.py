#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_GPU = {"T4", "L4", "A100", "H100", "G4"}
ALLOWED_TPU = {"v5e1", "v6e1", "V5E1", "V6E1"}


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")


def validate_job(job: dict) -> None:
    required = {
        "schema_version",
        "experiment_id",
        "workload",
        "resource",
        "remote_timeout_seconds",
        "scientific_backend",
        "scientific_execution_authorized",
        "claim_boundary",
        "enabled",
    }
    if set(job) - (required | {"nominal_envelope_multiplier", "required_authorization"}):
        raise ValueError(f"unknown job keys: {sorted(set(job)-required-{'nominal_envelope_multiplier','required_authorization'})}")
    missing = required - set(job)
    if missing:
        raise ValueError(f"missing job keys: {sorted(missing)}")
    if job["schema_version"] != 1:
        raise ValueError("job schema_version must be 1")
    resource = job["resource"]
    if set(resource) != {"variant", "accelerator"}:
        raise ValueError("resource must contain exactly variant and accelerator")
    variant = str(resource["variant"]).upper()
    accelerator = resource["accelerator"]
    if variant in {"CPU", "DEFAULT"}:
        if accelerator not in {None, "", "NONE"}:
            raise ValueError("CPU job may not request accelerator")
    elif variant == "GPU":
        if accelerator not in ALLOWED_GPU:
            raise ValueError(f"unsupported GPU accelerator: {accelerator}")
    elif variant == "TPU":
        if accelerator not in ALLOWED_TPU:
            raise ValueError(f"unsupported TPU accelerator: {accelerator}")
    else:
        raise ValueError(f"unsupported resource variant: {variant}")
    if job["scientific_execution_authorized"] is not False:
        raise ValueError(
            "QTR-COLAB-COMPUTE-001 preparation matrix may not authorize scientific execution"
        )
    if job["workload"] not in {"runtime_probe", "compute_requal_preflight", "c90_exact_candidate"}:
        raise ValueError(f"unsupported workload: {job['workload']}")
    if job["workload"] == "c90_exact_candidate" and job["enabled"]:
        raise ValueError("C90 exact candidate must remain disabled pending separate authority")


def load_matrix(path: Path) -> dict:
    matrix = json.loads(path.read_text(encoding="utf-8"))
    required = {"schema_version", "matrix_id", "status", "jobs", "claim_boundary"}
    if set(matrix) != required:
        raise ValueError("matrix key mismatch")
    if matrix["schema_version"] != 1:
        raise ValueError("matrix schema_version must be 1")
    seen = set()
    for job in matrix["jobs"]:
        validate_job(job)
        if job["experiment_id"] in seen:
            raise ValueError("duplicate experiment_id")
        seen.add(job["experiment_id"])
    return matrix


def latest_green_receipt(experiment_id: str) -> Path | None:
    base = ROOT / "runs" / "hosted" / experiment_id
    for path in sorted(base.glob("*/experiment_receipt.json"), reverse=True):
        try:
            receipt = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if receipt.get("status") == "GREEN_ENGINEERING":
            return path
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("matrix", type=Path)
    parser.add_argument("--continue-on-error", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    matrix = load_matrix(args.matrix)
    matrix_id = matrix["matrix_id"]
    work = ROOT / ".artifacts" / "colab-matrix" / safe_name(matrix_id)
    jobs_dir = work / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for idx, job in enumerate(matrix["jobs"], 1):
        variant = job["resource"]["variant"]
        accel = job["resource"]["accelerator"]
        label = f"{variant}:{accel or 'default'}"
        job_path = jobs_dir / f"{idx:03d}_{safe_name(job['experiment_id'])}.json"
        job_path.write_text(json.dumps(job, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        if not job["enabled"]:
            print(f"[QTR] {matrix_id}: DISABLED {job['experiment_id']} ({label})")
            results.append({"experiment_id": job["experiment_id"], "status": "DISABLED"})
            continue

        if args.resume:
            receipt = latest_green_receipt(job["experiment_id"])
            if receipt is not None:
                print(f"[QTR] {matrix_id}: SKIP green {job['experiment_id']} receipt={receipt}")
                results.append({
                    "experiment_id": job["experiment_id"],
                    "status": "SKIPPED_EXISTING_GREEN",
                    "receipt": str(receipt),
                })
                continue

        print(f"[QTR] {matrix_id}: {idx}/{len(matrix['jobs'])} {job['experiment_id']} ({label})")
        if args.dry_run:
            results.append({"experiment_id": job["experiment_id"], "status": "DRY_RUN"})
            continue

        proc = subprocess.run(
            [str(ROOT / "scripts" / "colab_run_job.sh"), str(job_path)],
            cwd=ROOT,
            check=False,
        )
        status = "GREEN" if proc.returncode == 0 else "FAILED"
        results.append({
            "experiment_id": job["experiment_id"],
            "status": status,
            "returncode": proc.returncode,
        })
        if proc.returncode and not args.continue_on_error:
            break

    summary = {
        "schema_version": 1,
        "matrix_id": matrix_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": args.dry_run,
        "resume": args.resume,
        "continue_on_error": args.continue_on_error,
        "results": results,
        "claim_boundary": matrix["claim_boundary"],
    }
    work.mkdir(parents=True, exist_ok=True)
    (work / "matrix_run.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    failures = [row for row in results if row["status"] == "FAILED"]
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())