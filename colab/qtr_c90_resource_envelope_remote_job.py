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
WORK = CONTENT / "qtr_c90_resource_envelope_work"
SOURCE = WORK / "source"
OUT = WORK / "out"
FINAL_RESULT = CONTENT / "gcl_result.json"
RECEIPT = CONTENT / "experiment_receipt.json"
BUNDLE = CONTENT / "gcl_output_bundle.tar.gz"
MANIFEST_PAYLOAD = "d64b770f5cc1fb4c8a0ca8e89dad6d8020a01ae38f2c6868ff3028f53c441651"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def make_bundle() -> None:
    with tarfile.open(BUNDLE, "w:gz") as tf:
        for path in sorted(OUT.glob("*")):
            if path.is_file():
                tf.add(path, arcname=f"out/{path.name}")
        for path in (FINAL_RESULT, RECEIPT, SOURCE_MANIFEST, JOB_PATH):
            if path.exists():
                tf.add(path, arcname=path.name)


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
        if job.get("experiment_id") != "QTR-C90-RESOURCE-ENVELOPE-001":
            raise RuntimeError("wrong experiment_id")
        if job.get("workload") != "c90_resource_envelope_calibration":
            raise RuntimeError("wrong workload")
        if job.get("scientific_backend") != "cpu_reference":
            raise RuntimeError("calibration requires cpu_reference")
        if job.get("scientific_execution_authorized") is not True:
            raise RuntimeError("calibration authorization flag missing")
        if job.get("full_c90_materialization_authorized") is not False:
            raise RuntimeError("materialization must remain prohibited")
        if job.get("manifest_payload_sha256") != MANIFEST_PAYLOAD:
            raise RuntimeError("manifest digest drift")
        session_id = job.get("hosted_session_identity")
        if not isinstance(session_id, str) or not session_id or session_id == "__HOST_RENDERED__":
            raise RuntimeError("hosted session identity was not rendered")

        if WORK.exists():
            shutil.rmtree(WORK)
        OUT.mkdir(parents=True, exist_ok=True)
        safe_extract(PAYLOAD, SOURCE)
        verify_source(source_manifest)

        evaluator = SOURCE / "reference/qtr_c90_resource_envelope_001.py"
        static_path = OUT / "phase_a_b_static.json"
        run_child([sys.executable, str(evaluator), "static", "--output", str(static_path)], "phase_a_b_static")
        static = load_json(static_path)
        if static.get("materialization_performed") is not False:
            raise RuntimeError("static calibration unexpectedly materialized C90")

        probe_path = OUT / "phase_c_d_probe_adjudication.json"
        run_child([
            sys.executable, str(evaluator), "probe",
            "--session-id", session_id,
            "--output", str(probe_path),
        ], "phase_c_d_probe_adjudication")
        result = load_json(probe_path)
        if result.get("materialization_performed") is not False:
            raise RuntimeError("calibration probe unexpectedly materialized C90")
        if result.get("frozen_307_validation_performed") is not False:
            raise RuntimeError("calibration probe unexpectedly validated frozen 307")

        FINAL_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        runtime = result["physical_probe"]["runtime"]
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
            "full_c90_materialization_authorized": False,
        }
        RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        make_bundle()
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
