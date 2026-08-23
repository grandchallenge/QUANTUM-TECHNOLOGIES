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
WORK = CONTENT / "qtr_c90_structure_work"
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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_child(args: list[str], name: str) -> int:
    stdout = OUT / f"{name}.stdout.txt"
    stderr = OUT / f"{name}.stderr.txt"
    with stdout.open("w", encoding="utf-8") as out, stderr.open("w", encoding="utf-8") as err:
        proc = subprocess.run(args, cwd=SOURCE, stdout=out, stderr=err, text=True, check=False)
    return proc.returncode


def mem_available_bytes() -> int:
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) * 1024
    raise RuntimeError("MemAvailable unavailable")


def canonical_digest(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


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
        if job.get("experiment_id") != "QTR-C90-STRUCTURE-001":
            raise RuntimeError("wrong experiment_id")
        if job.get("workload") != "c90_structure_conditional":
            raise RuntimeError("wrong workload")
        if job.get("scientific_backend") != "cpu_reference":
            raise RuntimeError("structure contract requires cpu_reference")
        if job.get("scientific_execution_authorized") is not True:
            raise RuntimeError("scientific authorization flag missing")
        if job.get("manifest_payload_sha256") != "205ecca612ae366694d4c17b6ce518727abf80114b6e52598073b238946f2a6a":
            raise RuntimeError("manifest digest drift")
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

        evaluator = SOURCE / "reference/qtr_c90_structure_001.py"
        static_path = OUT / "phase_b_c_static.json"
        rc = run_child([sys.executable, str(evaluator), "--phase", "static", "--output", str(static_path)], "phase_b_c_static")
        if rc:
            raise RuntimeError(f"static/control subprocess failed rc={rc}")
        static = load_json(static_path)

        eligible = [
            name for name, row in static["c90_methods"].items()
            if name != "S0_BASELINE" and row.get("c90_status") == "C90_STATIC_ALL_CAPS_PASS"
        ]
        method_results: dict[str, Any] = {}
        for method in eligible:
            before = mem_available_bytes()
            algebra_rows = []
            for algebra in job["algebra_order"]:
                path = OUT / f"{method}__{algebra}.json"
                rc = run_child([
                    sys.executable, str(evaluator),
                    "--phase", "materialize-one",
                    "--method", method,
                    "--algebra", algebra,
                    "--output", str(path),
                ], f"materialize_{method}_{algebra}")
                if not path.exists():
                    raise RuntimeError(f"missing materialization receipt {method}/{algebra}")
                row = load_json(path)
                algebra_rows.append({
                    "algebra": algebra,
                    "status": row["status"],
                    "sha256": sha256_file(path),
                    "returncode": rc,
                })
                if rc or row["status"] != "C90_MATERIALIZATION_COMPLETED":
                    break
            method_results[method] = {
                "memavailable_before_method_bytes": before,
                "algebras": algebra_rows,
                "all_algebras_completed": len(algebra_rows) == len(job["algebra_order"]) and all(
                    row["status"] == "C90_MATERIALIZATION_COMPLETED" and row["returncode"] == 0
                    for row in algebra_rows
                ),
            }

        validation_results: dict[str, Any] = {}
        if any(row["all_algebras_completed"] for row in method_results.values()):
            import qtr_c90_structure_001 as structure
            import qtr_c90_exact_requal_001 as predecessor
            import qldpc_scale_001a_math as math001a
            from qldpc_scale_001a_shared import digest

            pmanifest = predecessor.load_manifest()
            _, code, baseline_order, _ = predecessor.reconstruct_target(pmanifest)
            coords = predecessor.frozen_validation_coordinates(len(code["selector_basis_qubits"]))
            if len(coords) != 307 or digest(coords) != structure.load_manifest()["target"]["validation_set_sha256"]:
                raise RuntimeError("frozen-307 selector identity drift")
            for method, mrow in method_results.items():
                if not mrow["all_algebras_completed"]:
                    continue
                order = baseline_order if method == "S1_GF2_CONSTRAINT_ELIMINATION" else structure.junction_tree(
                    code["scopes"], baseline_order
                )["separator_elimination_order"]
                descriptor, meta = math001a.compile_descriptor(code["scopes"], code["selector_basis_qubits"], order)
                rows = math001a.run_validation_parallel(
                    coords, code["scopes"], code["selector_basis_qubits"], order, descriptor
                )
                validation_results[method] = {
                    "status": "C90_FROZEN_307_VALIDATED",
                    "selector_count": len(rows),
                    "validation_outputs_sha256": digest(rows),
                    "compiled_descriptor_sha256": meta["canonical_sha256"],
                    "independent_oracle_checked_per_selector": True,
                }

        final = {
            "schema_version": 1,
            "experiment_id": "QTR-C90-STRUCTURE-001",
            "status": "candidate_executable_not_promoted",
            "hosted_session_identity": session_id,
            "source_commit": source_manifest.get("source_commit"),
            "manifest_payload_sha256": job["manifest_payload_sha256"],
            "runtime": runtime,
            "phase_b_c": {
                "static_report_sha256": sha256_file(static_path),
                "phase_c_disposition": static["phase_c_disposition"],
                "overall_outcome": static["overall_outcome"],
                "eligible_methods": eligible,
            },
            "phase_d": {
                "attempted": bool(eligible),
                "methods": method_results,
            },
            "phase_e": {
                "attempted": bool(validation_results),
                "methods": validation_results,
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
