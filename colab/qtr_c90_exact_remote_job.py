#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONTENT = Path("/content")
PAYLOAD = CONTENT / "gcl_source.tar.gz"
SOURCE_MANIFEST = CONTENT / "gcl_manifest.json"
JOB_PATH = CONTENT / "gcl_job.json"
WORK = CONTENT / "qtr_c90_exact_work"
SOURCE = WORK / "source"
OUT = WORK / "out"
FINAL_RESULT = CONTENT / "gcl_result.json"
RECEIPT = CONTENT / "experiment_receipt.json"
BUNDLE = CONTENT / "gcl_output_bundle.tar.gz"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe_extract(archive: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    base = dest.resolve()
    with tarfile.open(archive, "r:gz") as tf:
        for member in tf.getmembers():
            target = (dest / member.name).resolve()
            if target != base and base not in target.parents:
                raise RuntimeError(f"unsafe archive member: {member.name}")
            if member.issym() or member.islnk():
                raise RuntimeError(f"links forbidden in source payload: {member.name}")
        tf.extractall(dest, filter="data")


def verify_source(manifest: dict[str, Any]) -> None:
    if sha256_file(PAYLOAD) != manifest["payload_sha256"]:
        raise RuntimeError("source payload digest mismatch")
    expected = {row["path"]: row for row in manifest["files"]}
    observed = {}
    for path in SOURCE.rglob("*"):
        if path.is_file():
            rel = path.relative_to(SOURCE).as_posix()
            observed[rel] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    if set(observed) != set(expected):
        raise RuntimeError("source payload file-set mismatch")
    for rel, row in expected.items():
        if observed[rel] != {"bytes": row["bytes"], "sha256": row["sha256"]}:
            raise RuntimeError(f"source payload file drift: {rel}")


def run_child(args: list[str], name: str) -> None:
    stdout = OUT / f"{name}.stdout.txt"
    stderr = OUT / f"{name}.stderr.txt"
    with stdout.open("w", encoding="utf-8") as out, stderr.open("w", encoding="utf-8") as err:
        proc = subprocess.run(args, cwd=SOURCE, stdout=out, stderr=err, text=True, check=False)
    if proc.returncode:
        raise RuntimeError(f"{name} subprocess failed rc={proc.returncode}")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def make_bundle() -> None:
    with tarfile.open(BUNDLE, "w:gz") as tf:
        for path in sorted(OUT.glob("*")):
            if path.is_file():
                tf.add(path, arcname=f"out/{path.name}")
        for path in (FINAL_RESULT, RECEIPT, SOURCE_MANIFEST, JOB_PATH):
            if path.exists():
                tf.add(path, arcname=path.name)


def canonical_digest(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    status = "RED_OPERATIONAL"
    error = None
    source_manifest: dict[str, Any] = {}
    job: dict[str, Any] = {}
    runtime: dict[str, Any] = {}
    returncode = 1
    try:
        source_manifest = load_json(SOURCE_MANIFEST)
        job = load_json(JOB_PATH)
        if job.get("experiment_id") != "QTR-C90-EXACT-REQUAL-001":
            raise RuntimeError("wrong experiment_id")
        if job.get("workload") != "c90_exact_requal_conditional":
            raise RuntimeError("wrong workload")
        if job.get("scientific_backend") != "cpu_reference":
            raise RuntimeError("C90 contract requires cpu_reference")
        if job.get("scientific_execution_authorized") is not True:
            raise RuntimeError("scientific authorization flag missing")
        session_id = job.get("hosted_session_identity")
        if not isinstance(session_id, str) or not session_id or session_id == "__HOST_RENDERED__":
            raise RuntimeError("hosted session identity was not rendered")
        if WORK.exists():
            shutil.rmtree(WORK)
        OUT.mkdir(parents=True, exist_ok=True)
        safe_extract(PAYLOAD, SOURCE)
        verify_source(source_manifest)

        sys.path.insert(0, str(SOURCE / "reference"))
        from qtr_colab_runtime_probe import detect_runtime
        runtime = detect_runtime()
        if runtime.get("observed_variant") != "CPU":
            raise RuntimeError(f"CPU reference required, observed {runtime.get('observed_variant')}")
        if runtime.get("observed_accelerator") not in {None, ""}:
            raise RuntimeError("CPU reference receipt unexpectedly contains accelerator")

        evaluator = SOURCE / "reference/qtr_c90_exact_requal_001.py"
        static_path = OUT / "phase_m_static.json"
        run_child([sys.executable, str(evaluator), "static", "--output", str(static_path)], "phase_m_static")
        static = load_json(static_path)
        static_status = static["phase_m_static_adjudication"]["status"]

        calibration_path = None
        phase_m_path = OUT / "phase_m_adjudication.json"
        if static_status == "STATIC_CLEAR_FOR_BOUNDED_CALIBRATION":
            calibration_path = OUT / "phase_m_calibration.json"
            run_child([
                sys.executable, str(evaluator), "calibrate",
                "--static", str(static_path), "--session-id", session_id,
                "--output", str(calibration_path),
            ], "phase_m_calibration")
        adjudicate_args = [
            sys.executable, str(evaluator), "adjudicate",
            "--static", str(static_path), "--session-id", session_id,
            "--output", str(phase_m_path),
        ]
        if calibration_path is not None:
            adjudicate_args.extend(["--calibration", str(calibration_path)])
        run_child(adjudicate_args, "phase_m_adjudication")
        phase_m = load_json(phase_m_path)

        compiles: list[Path] = []
        if phase_m["status"] == "C90_MEMORY_STORAGE_QUALIFIED_WITHIN_BOUND":
            for index, algebra in enumerate([
                "sum_product_bsc_p_0_1", "soft_tropical_base_2", "min_plus_hamming"
            ], 1):
                path = OUT / f"phase_x_{index}_{algebra}.json"
                run_child([
                    sys.executable, str(evaluator), "compile-algebra",
                    "--algebra", algebra, "--phase-m", str(phase_m_path),
                    "--session-id", session_id, "--output", str(path),
                ], f"phase_x_{index}_{algebra}")
                row = load_json(path)
                compiles.append(path)
                if row["status"] != "C90_EXACT_COMPILATION_COMPLETED":
                    break

        validation_path = None
        if len(compiles) == 3 and all(load_json(p)["status"] == "C90_EXACT_COMPILATION_COMPLETED" for p in compiles):
            validation_path = OUT / "validation_307.json"
            args = [sys.executable, str(evaluator), "validate"]
            for path in compiles:
                args.extend(["--compile", str(path)])
            args.extend(["--output", str(validation_path)])
            run_child(args, "validation_307")

        final = {
            "schema_version": 1,
            "experiment_id": "QTR-C90-EXACT-REQUAL-001",
            "status": "candidate_executable_not_promoted",
            "hosted_session_identity": session_id,
            "source_commit": source_manifest.get("source_commit"),
            "manifest_payload_sha256": job.get("manifest_payload_sha256"),
            "runtime": runtime,
            "phase_m": {
                "static_status": static_status,
                "adjudication_status": phase_m["status"],
                "static_report_sha256": sha256_file(static_path),
                "calibration_performed": calibration_path is not None,
                "adjudication_report_sha256": sha256_file(phase_m_path),
            },
            "phase_x": {
                "attempted": bool(compiles),
                "compile_receipts": [
                    {"path": p.name, "sha256": sha256_file(p), "status": load_json(p)["status"], "algebra": load_json(p)["algebra"]}
                    for p in compiles
                ],
            },
            "validation": {
                "attempted": validation_path is not None,
                "receipt_sha256": sha256_file(validation_path) if validation_path else None,
                "status": load_json(validation_path)["status"] if validation_path else None,
            },
            "claim_boundary": job["claim_boundary"],
        }
        final["payload_sha256"] = canonical_digest(final)
        FINAL_RESULT.write_text(json.dumps(final, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        status = "GREEN_SCIENTIFIC_CANDIDATE"
        returncode = 0
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "fatal_traceback.txt").write_text(traceback.format_exc(), encoding="utf-8")
        returncode = 1
    finally:
        receipt = {
            "schema_version": 1,
            "experiment_id": job.get("experiment_id"),
            "status": status,
            "started_at": started,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "source_commit": source_manifest.get("source_commit"),
            "source_payload_sha256": source_manifest.get("payload_sha256"),
            "job_sha256": sha256_file(JOB_PATH) if JOB_PATH.exists() else None,
            "result_sha256": sha256_file(FINAL_RESULT) if FINAL_RESULT.exists() else None,
            "hosted_session_identity": job.get("hosted_session_identity"),
            "runtime": runtime,
            "fatal_error": error,
            "returncode": returncode,
            "promotion_claim": False,
            "scientific_backend": job.get("scientific_backend"),
        }
        RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        make_bundle()
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
