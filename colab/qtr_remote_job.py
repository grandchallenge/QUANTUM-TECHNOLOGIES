#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
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
JOB_PATH = CONTENT / "gcl_job.json"
MANIFEST_PATH = CONTENT / "gcl_manifest.json"
WORK_ROOT = CONTENT / "qtr_colab_work"
SOURCE_ROOT = WORK_ROOT / "source"
RESULT_PATH = CONTENT / "gcl_result.json"
RECEIPT_PATH = CONTENT / "experiment_receipt.json"
BUNDLE_PATH = CONTENT / "gcl_output_bundle.tar.gz"
STDOUT_PATH = CONTENT / "qtr_job_stdout.txt"
STDERR_PATH = CONTENT / "qtr_job_stderr.txt"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
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
                raise RuntimeError(f"links are not permitted in source payload: {member.name}")
        tf.extractall(dest, filter="data")


def verify_payload(manifest: dict[str, Any]) -> None:
    if sha256_file(PAYLOAD) != manifest["payload_sha256"]:
        raise RuntimeError("source payload digest mismatch")
    expected = {row["path"]: row for row in manifest["files"]}
    observed = {}
    for path in SOURCE_ROOT.rglob("*"):
        if path.is_file():
            rel = path.relative_to(SOURCE_ROOT).as_posix()
            observed[rel] = {
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
    if set(observed) != set(expected):
        raise RuntimeError("source payload file-set mismatch")
    for rel, row in expected.items():
        if observed[rel]["bytes"] != row["bytes"] or observed[rel]["sha256"] != row["sha256"]:
            raise RuntimeError(f"source payload file drift: {rel}")


def run_command(argv: list[str]) -> int:
    with STDOUT_PATH.open("w", encoding="utf-8") as out, STDERR_PATH.open(
        "w", encoding="utf-8"
    ) as err:
        proc = subprocess.run(
            argv,
            cwd=SOURCE_ROOT,
            stdout=out,
            stderr=err,
            text=True,
            check=False,
        )
    return proc.returncode


def make_bundle() -> None:
    with tarfile.open(BUNDLE_PATH, "w:gz") as tf:
        for path in (RESULT_PATH, RECEIPT_PATH, STDOUT_PATH, STDERR_PATH, MANIFEST_PATH, JOB_PATH):
            if path.exists():
                tf.add(path, arcname=path.name)


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    job: dict[str, Any] = {}
    manifest: dict[str, Any] = {}
    runtime: dict[str, Any] = {}
    status = "RED_ENGINEERING"
    returncode = 99
    fatal_error = None
    try:
        job = json.loads(JOB_PATH.read_text(encoding="utf-8"))
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if WORK_ROOT.exists():
            shutil.rmtree(WORK_ROOT)
        safe_extract(PAYLOAD, SOURCE_ROOT)
        verify_payload(manifest)

        sys.path.insert(0, str(SOURCE_ROOT / "reference"))
        from qtr_colab_runtime_probe import (
            detect_runtime,
            validate_job,
            validate_requested_runtime,
        )

        validate_job(job)
        runtime = detect_runtime()
        validate_requested_runtime(job, runtime)

        workload = job["workload"]
        if workload == "runtime_probe":
            argv = [
                sys.executable,
                str(SOURCE_ROOT / "reference/qtr_colab_runtime_probe.py"),
                "--job",
                str(JOB_PATH),
                "--output",
                str(RESULT_PATH),
            ]
        elif workload == "compute_requal_preflight":
            if job["scientific_backend"] != "cpu_reference":
                raise RuntimeError("compute requalification preflight is bound to cpu_reference")
            argv = [
                sys.executable,
                str(SOURCE_ROOT / "reference/qtr_compute_requal_001.py"),
                "--job",
                str(JOB_PATH),
                "--output",
                str(RESULT_PATH),
            ]
        elif workload == "c90_exact_candidate":
            raise RuntimeError(
                "C90 exact candidate is intentionally disabled in QTR-COLAB-COMPUTE-001; "
                "separate scientific execution authority is required"
            )
        else:
            raise RuntimeError(f"unsupported workload: {workload}")

        returncode = run_command(argv)
        if returncode != 0:
            raise RuntimeError(f"workload exited with code {returncode}")
        result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
        if not str(result.get("status", "")).startswith("GREEN_ENGINEERING"):
            raise RuntimeError(f"unexpected workload status: {result.get('status')}")
        status = "GREEN_ENGINEERING"
        returncode = 0
    except Exception as exc:
        fatal_error = f"{type(exc).__name__}: {exc}"
        STDERR_PATH.write_text(
            (STDERR_PATH.read_text(encoding="utf-8") if STDERR_PATH.exists() else "")
            + "\n"
            + traceback.format_exc(),
            encoding="utf-8",
        )
    finally:
        receipt = {
            "schema_version": 1,
            "experiment_id": job.get("experiment_id"),
            "status": status,
            "started_at": started,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "source_commit": manifest.get("source_commit"),
            "source_payload_sha256": manifest.get("payload_sha256"),
            "job_sha256": sha256_file(JOB_PATH) if JOB_PATH.exists() else None,
            "result_sha256": sha256_file(RESULT_PATH) if RESULT_PATH.exists() else None,
            "runtime": runtime,
            "workload": job.get("workload"),
            "scientific_backend": job.get("scientific_backend"),
            "scientific_execution_authorized": job.get("scientific_execution_authorized", False),
            "promotion_claim": False,
            "fatal_error": fatal_error,
            "returncode": returncode,
            "claim_boundary": job.get("claim_boundary"),
        }
        RECEIPT_PATH.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        make_bundle()
    return returncode if status == "GREEN_ENGINEERING" else max(1, returncode)


if __name__ == "__main__":
    raise SystemExit(main())