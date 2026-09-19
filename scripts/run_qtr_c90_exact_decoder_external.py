#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures as futures
import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPO = "grandchallenge/QUANTUM-TECHNOLOGIES"
EXPERIMENT_ID = "QTR-C90-EXACT-DECODER-001"
ACTIVATION_HEAD = "0c1f5591a097adc285dec4cbfc320eeebd2c65d3"
VALIDATION_RUN_ID = 35084118529
VALIDATION_ARTIFACT_ID = 10443207511
VALIDATION_ARTIFACT_DIGEST = "sha256:b91dd81d795822bd0f889a32b44f01b716d5b7ae097d83be5f43de95c9964bf8"
CONVENTIONAL_RUN_ID = 32079738866
CONVENTIONAL_ARTIFACT_ID = 9304727792
CONVENTIONAL_ARTIFACT_NAME = "TCM-QDEC-COMPARE-001-exact-head"
CONVENTIONAL_ARTIFACT_DIGEST = "sha256:34f37ec1a351a42e08c7143b359ca40191db4cd92ceeab2881930a67e3942182"
LOGICAL_CLASSES = 256
INPUTS = 347
PER_PROCESS_MEMORY_BYTES = 7 * (1 << 30)
MEMORY_RESERVE_BYTES = 8 * (1 << 30)

SCIENTIFIC_BLOBS = {
    "reference/qtr_c90_exact_native_eval_001.cpp": "92022fa89ceff9cf4ac0c9b6ce8613617664e1a6",
    "reference/qtr_c90_exact_decoder_001.py": "7a275cd40b7ee8861ac1675791490b50d0266c50",
    "reference/qtr_c90_exact_execute_001.py": "f683e2af6671ef7f7908c09514d7fcab993755bc",
    "reference/tcm_c72_interface_001.py": "164761a236ca53c919d810f0832cbcf3c1fb8989",
    "reference/qtr_c90_exact_dag_001.py": "bb2576ea17beb43f1a188eb4a77a280869d0c954",
    "reference/qtr_c90_exact_native_campaign_001.py": "4b5ba1b5819a3ffdee294fb4cb2ab03734793a5d",
}

ALGEBRAS = {
    "sum_product_bsc_p_0_1": {
        "artifact_id": 10442610733,
        "artifact_name": "QTR-C90-same-head-compile-sum_product_bsc_p_0_1",
        "artifact_digest": "sha256:678b39b09023f0adb854a9b0cc28ce0b85c9379e149b0103cfe94a7e4ad0fece",
        "canonical_node_stream_sha256": "e6d34ddfdadb19af9bda02c36997a8c2dd767f4610b178f4cf3d74407445ebb4",
        "compile_receipt_payload_sha256": "630854c30889537c0a248bc245f05286685b515d07743b4c2c811a30ce9f4642",
        "native_binary_sha256": "2efe52e17c6d66920b23738987818184657caf479c60c78712dff6db4a306bde",
        "observed_class0_seconds": 7588,
    },
    "soft_tropical_base_2": {
        "artifact_id": 10442242798,
        "artifact_name": "QTR-C90-same-head-compile-soft_tropical_base_2",
        "artifact_digest": "sha256:c4fa41b35ad5e88e4e58ca9816c78dd296d170a5d86cf9087c51b4fdcce138e8",
        "canonical_node_stream_sha256": "4d8859535f7a3ce814eb6ea459a80870fd645f57af487e5b8a9f99de3d5dccb0",
        "compile_receipt_payload_sha256": "9bc3f78f7b501da1892d8b627cc70b6fa14292a1fec8dac1b722c401a7e114f4",
        "native_binary_sha256": "9647b3e7fb2ee7f6f87d7e3fe6ce6779bd756e100f86f3dc13e7dc5385b5df9a",
        "observed_class0_seconds": 7038,
    },
    "min_plus_hamming": {
        "artifact_id": 10442143252,
        "artifact_name": "QTR-C90-same-head-compile-min_plus_hamming",
        "artifact_digest": "sha256:6b9c94bd62cd4b3818396bc2c48b66cfe63958d37ce8d5ab2b846d0fb701d38f",
        "canonical_node_stream_sha256": "3aa3f0c1d97f7428623a034b6baa20e9c7f113e830b715040dc9e1e62967b4e8",
        "compile_receipt_payload_sha256": "4a58ffb06bac564151c39f49416a9ca2d1b7b5de251fc2cb37046fab84af99f7",
        "native_binary_sha256": "dd58a7e0c59626032d8714827d9f1097a33a78fd426c7d972407b32340890bb0",
        "observed_class0_seconds": 4000,
    },
}

def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()

def canonical_digest(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()

def run(args: list[str], *, capture: bool = False, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.PIPE if capture else None, check=check)

def git_head() -> str:
    return run(["git", "rev-parse", "HEAD"], capture=True).stdout.strip()

def git_blob(path: str) -> str:
    return run(["git", "hash-object", path], capture=True).stdout.strip()

def verify_source() -> None:
    if not (ROOT / ".git").exists():
        raise RuntimeError("runner must execute from a git checkout")
    observed = {path: git_blob(path) for path in SCIENTIFIC_BLOBS}
    if observed != SCIENTIFIC_BLOBS:
        raise RuntimeError(f"frozen scientific blob drift: {observed}")

def mem_available() -> int:
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) * 1024
    except FileNotFoundError:
        pass
    return 0

def safe_worker_limit() -> int:
    cpu = os.cpu_count() or 1
    avail = mem_available()
    by_mem = 1 if avail <= MEMORY_RESERVE_BYTES else max(1, (avail - MEMORY_RESERVE_BYTES) // PER_PROCESS_MEMORY_BYTES)
    return max(1, min(cpu, int(by_mem)))

def host_snapshot() -> dict[str, Any]:
    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python": sys.version,
        "cpu_count": os.cpu_count(),
        "mem_available_bytes": mem_available(),
        "runner_head": git_head(),
    }

def gh_json(endpoint: str) -> dict[str, Any]:
    return json.loads(run(["gh", "api", endpoint], capture=True).stdout)

def verify_gh() -> None:
    if shutil.which("gh") is None:
        raise RuntimeError("gh CLI is required on the external host")
    run(["gh", "auth", "status", "-h", "github.com"], capture=True)

def verify_artifact(artifact_id: int, name: str, digest: str, run_id: int, head: str | None = None) -> None:
    meta = gh_json(f"repos/{REPO}/actions/artifacts/{artifact_id}")
    if meta.get("name") != name or meta.get("digest") != digest or meta.get("expired") is not False:
        raise RuntimeError("artifact identity/digest/expiry drift")
    wr = meta.get("workflow_run") or {}
    if int(wr.get("id", -1)) != run_id:
        raise RuntimeError("artifact run drift")
    if head is not None and wr.get("head_sha") != head:
        raise RuntimeError("artifact head drift")

def download_artifact(run_id: int, name: str, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    run(["gh", "run", "download", str(run_id), "--repo", REPO, "-n", name, "-D", str(dest)])

def find_one(root: Path, pattern: str) -> Path:
    rows = list(root.rglob(pattern))
    if len(rows) != 1:
        raise RuntimeError(f"expected one {pattern}; found {len(rows)}")
    return rows[0]

def ensure_compiled(algebra: str, work: Path) -> Path:
    spec = ALGEBRAS[algebra]
    verify_artifact(spec["artifact_id"], spec["artifact_name"], spec["artifact_digest"],
                    VALIDATION_RUN_ID, ACTIVATION_HEAD)
    dest = work / "cache" / "compiled" / algebra
    binary = dest / f"compiled-{algebra}.qtrbin"
    receipt = dest / f"compile-{algebra}.json"
    if not binary.exists() or not receipt.exists() or sha256_file(binary) != spec["native_binary_sha256"]:
        download_artifact(VALIDATION_RUN_ID, spec["artifact_name"], dest)
        binary = find_one(dest, "compiled-*.qtrbin")
        receipt = find_one(dest, "compile-*.json")
    if sha256_file(binary) != spec["native_binary_sha256"]:
        raise RuntimeError("native binary SHA-256 drift")
    r = json.loads(receipt.read_text())
    c = r.get("compiled") or {}
    if r.get("source_commit") != ACTIVATION_HEAD or r.get("payload_sha256") != spec["compile_receipt_payload_sha256"]:
        raise RuntimeError("compile receipt identity drift")
    if c.get("canonical_node_stream_sha256") != spec["canonical_node_stream_sha256"]:
        raise RuntimeError("canonical stream drift")
    if c.get("native_binary_sha256") != spec["native_binary_sha256"] or r.get("quality_exposed") is not False:
        raise RuntimeError("compile binary/quality boundary drift")
    return binary

def build_evaluator(work: Path) -> Path:
    out = work / "bin" / "qtr-c90-native-eval"
    out.parent.mkdir(parents=True, exist_ok=True)
    run(["g++", "-std=c++17", "-O3", "-DNDEBUG",
         "reference/qtr_c90_exact_native_eval_001.cpp", "-o", str(out)])
    return out

def adapter() -> Path:
    return ROOT / "reference/qtr_c90_exact_native_campaign_001.py"

def write_json(path: Path, payload: dict[str, Any]) -> None:
    p = dict(payload)
    p["payload_sha256"] = canonical_digest(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(p, indent=2, sort_keys=True) + "\n")

def valid_external_shard(class_dir: Path, algebra: str, cls: int) -> bool:
    marker = class_dir / "external-shard.json"
    rows = class_dir / f"rows-{algebra}-class-{cls}.jsonl"
    receipt = class_dir / f"receipt-{algebra}-class-{cls}.json"
    if not (marker.exists() and rows.exists() and receipt.exists()):
        return False
    m = json.loads(marker.read_text())
    return (m.get("execution_substrate") == "external" and m.get("algebra") == algebra
            and int(m.get("logical_class", -1)) == cls and m.get("rows_file_sha256") == sha256_file(rows))

def evaluate_class(algebra: str, cls: int, binary: Path, evaluator: Path, root: Path) -> dict[str, Any]:
    final = root / f"class-{cls}"
    if valid_external_shard(final, algebra, cls):
        return {"class": cls, "status": "RESUME_VALIDATED"}
    tmp = root / f".class-{cls}.tmp-{os.getpid()}-{time.time_ns()}"
    tmp.mkdir(parents=True)
    selectors = tmp / "selectors.txt"
    rows = tmp / f"rows-{algebra}-class-{cls}.jsonl"
    receipt = tmp / f"receipt-{algebra}-class-{cls}.json"
    timefile = tmp / "time.txt"
    run([sys.executable, str(adapter()), "selectors", "--logical-class", str(cls), "--output", str(selectors)])
    if len(selectors.read_text().splitlines()) != INPUTS:
        raise RuntimeError("selector count drift")
    started = utcnow()
    with rows.open("w") as out, (tmp / "stderr.txt").open("w") as err:
        p = subprocess.run(["/usr/bin/time", "-v", "-o", str(timefile), str(evaluator),
                            "--native", str(binary), "--selectors", str(selectors)],
                           cwd=ROOT, text=True, stdout=out, stderr=err, check=False)
    if p.returncode or len(rows.read_text().splitlines()) != INPUTS:
        raise RuntimeError(f"native evaluator failed class={cls} rc={p.returncode}")
    run([sys.executable, str(adapter()), "validate-shard", "--algebra", algebra,
         "--logical-class", str(cls), "--rows", str(rows), "--output", str(receipt)])
    rr = json.loads(receipt.read_text())
    marker = {
        "schema_version": 1,
        "experiment_id": EXPERIMENT_ID,
        "status": "EXTERNAL_SELECTOR_SHARD_COMPLETE",
        "execution_substrate": "external",
        "activation_head": ACTIVATION_HEAD,
        "runner_head": git_head(),
        "algebra": algebra,
        "logical_class": cls,
        "selector_count": INPUTS,
        "started_at": started,
        "finished_at": utcnow(),
        "rows_file_sha256": sha256_file(rows),
        "semantic_rows_sha256": rr["rows_sha256"],
        "time_file_sha256": sha256_file(timefile),
        "host": host_snapshot(),
        "github_hosted_selector_values_used": False,
        "quality_exposed": False,
    }
    write_json(tmp / "external-shard.json", marker)
    if final.exists():
        shutil.rmtree(final)
    tmp.rename(final)
    return {"class": cls, "status": "COMPLETE"}

def evaluate(algebra: str, work: Path, workers: int) -> None:
    verify_source()
    verify_gh()
    if shutil.which("g++") is None or not Path("/usr/bin/time").exists():
        raise RuntimeError("g++ and /usr/bin/time are required")
    safe = safe_worker_limit()
    if workers > safe:
        raise RuntimeError(f"workers={workers} exceeds conservative RAM/CPU limit={safe}")
    binary = ensure_compiled(algebra, work)
    evaluator = build_evaluator(work)
    root = work / "external-shards" / algebra
    root.mkdir(parents=True, exist_ok=True)
    pending = [i for i in range(LOGICAL_CLASSES) if not valid_external_shard(root / f"class-{i}", algebra, i)]
    print(f"[QTR-C90] algebra={algebra} complete={LOGICAL_CLASSES-len(pending)}/256 workers={workers}", flush=True)
    with futures.ThreadPoolExecutor(max_workers=workers) as pool:
        tasks = {pool.submit(evaluate_class, algebra, i, binary, evaluator, root): i for i in pending}
        done = LOGICAL_CLASSES - len(pending)
        for fut in futures.as_completed(tasks):
            r = fut.result()
            done += 1
            print(f"[QTR-C90] {algebra} class={r['class']} {r['status']} complete={done}/256", flush=True)
    missing = [i for i in range(LOGICAL_CLASSES) if not valid_external_shard(root / f"class-{i}", algebra, i)]
    if missing:
        raise RuntimeError(f"incomplete external surface: {missing[:20]}")
    write_json(work / f"evaluate-{algebra}-receipt.json", {
        "schema_version": 1, "experiment_id": EXPERIMENT_ID,
        "status": "EXTERNAL_ALGEBRA_SURFACE_COMPLETE", "activation_head": ACTIVATION_HEAD,
        "runner_head": git_head(), "algebra": algebra, "workers": workers,
        "logical_classes": LOGICAL_CLASSES, "selector_evaluations": LOGICAL_CLASSES * INPUTS,
        "host": host_snapshot(), "github_hosted_selector_values_used": False, "quality_exposed": False,
        "completed_at": utcnow(),
    })

def stage_rows(work: Path, algebra: str, dest: Path) -> None:
    target = dest / algebra
    target.mkdir(parents=True, exist_ok=True)
    for cls in range(LOGICAL_CLASSES):
        srcdir = work / "external-shards" / algebra / f"class-{cls}"
        if not valid_external_shard(srcdir, algebra, cls):
            raise RuntimeError(f"missing external shard {algebra}/{cls}")
        src = srcdir / f"rows-{algebra}-class-{cls}.jsonl"
        link = target / src.name
        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to(src.resolve())

def conventional(work: Path) -> Path:
    verify_artifact(CONVENTIONAL_ARTIFACT_ID, CONVENTIONAL_ARTIFACT_NAME,
                    CONVENTIONAL_ARTIFACT_DIGEST, CONVENTIONAL_RUN_ID)
    dest = work / "cache" / "conventional"
    if not dest.exists() or not any(dest.iterdir()):
        download_artifact(CONVENTIONAL_RUN_ID, CONVENTIONAL_ARTIFACT_NAME, dest)
    return dest

def aggregate_score(work: Path) -> None:
    verify_source()
    verify_gh()
    final = work / "final"
    final.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=work) as tmp:
        staged = Path(tmp) / "rows"
        for algebra in ALGEBRAS:
            stage_rows(work, algebra, staged)
        fixed = final / "fixed-corrections.json"
        report = final / "matched-comparison.json"
        run([sys.executable, str(adapter()), "aggregate",
             "--sum-root", str(staged / "sum_product_bsc_p_0_1"),
             "--soft-root", str(staged / "soft_tropical_base_2"),
             "--min-root", str(staged / "min_plus_hamming"),
             "--orchestration-head", git_head(), "--output", str(fixed)])
        f = json.loads(fixed.read_text())
        if f.get("status") != "C90_EXACT_CORRECTIONS_FIXED" or f.get("quality_exposed") is not False:
            raise RuntimeError("fixed-correction gate failed")
        run([sys.executable, str(adapter()), "score", "--fixed", str(fixed),
             "--conventional-artifact-dir", str(conventional(work)),
             "--orchestration-head", git_head(), "--output", str(report)])
        r = json.loads(report.read_text())
        if r.get("status") != "C90_TCM_MATCHED_COMPARISON_COMPLETED":
            raise RuntimeError("terminal comparison predicate failed")
    write_json(final / "external-authoritative-inventory.json", {
        "schema_version": 1, "experiment_id": EXPERIMENT_ID,
        "status": "EXTERNAL_AUTHORITATIVE_CAMPAIGN_COMPLETE",
        "activation_head": ACTIVATION_HEAD, "runner_head": git_head(),
        "execution_substrate": "external", "github_hosted_selector_values_used": False,
        "external_selector_evaluations": len(ALGEBRAS) * LOGICAL_CLASSES * INPUTS,
        "fixed_corrections_sha256": sha256_file(final / "fixed-corrections.json"),
        "matched_comparison_sha256": sha256_file(final / "matched-comparison.json"),
        "completed_at": utcnow(), "host": host_snapshot(),
    })
    bundle = final / "QTR-C90-EXACT-DECODER-001-external-authoritative.tar.gz"
    with tarfile.open(bundle, "w:gz") as tf:
        for p in sorted(final.iterdir()):
            if p.is_file() and p != bundle:
                tf.add(p, arcname=p.name)
    print(f"[QTR-C90] EXTERNAL_AUTHORITATIVE_CAMPAIGN_COMPLETE bundle={bundle}")

def plan(workers: int | None) -> None:
    verify_source()
    use = workers or safe_worker_limit()
    print(json.dumps({
        "activation_head": ACTIVATION_HEAD,
        "host": host_snapshot(),
        "safe_worker_limit": safe_worker_limit(),
        "requested_workers": use,
        "per_process_memory_guard_bytes": PER_PROCESS_MEMORY_BYTES,
        "selector_evaluations_per_algebra": LOGICAL_CLASSES * INPUTS,
        "total_selector_evaluations": len(ALGEBRAS) * LOGICAL_CLASSES * INPUTS,
        "estimated_wall_hours": {
            name: round(spec["observed_class0_seconds"] * LOGICAL_CLASSES / max(1, use) / 3600, 2)
            for name, spec in ALGEBRAS.items()
        },
        "github_hosted_selector_values_authoritative": False,
    }, indent=2, sort_keys=True))

def main() -> int:
    p = argparse.ArgumentParser(description="External authoritative QTR-C90 exact-decoder runner")
    sub = p.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("plan"); q.add_argument("--workers", type=int)
    q = sub.add_parser("evaluate"); q.add_argument("--algebra", choices=tuple(ALGEBRAS), required=True)
    q.add_argument("--workers", type=int); q.add_argument("--work-root", type=Path, default=ROOT / "runs/external" / EXPERIMENT_ID)
    q = sub.add_parser("aggregate-score"); q.add_argument("--work-root", type=Path, default=ROOT / "runs/external" / EXPERIMENT_ID)
    args = p.parse_args()
    if args.cmd == "plan":
        plan(args.workers); return 0
    work = args.work_root.resolve()
    if args.cmd == "evaluate":
        evaluate(args.algebra, work, args.workers or safe_worker_limit()); return 0
    aggregate_score(work); return 0

if __name__ == "__main__":
    raise SystemExit(main())
