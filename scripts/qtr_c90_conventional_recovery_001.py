#!/usr/bin/env python3
"""Verify content-equivalent COMPARE-001 replay evidence without impersonating the lost ZIP.

The frozen reference scorer and scientific source files are not modified.
This adapter is invoked only after all C90 corrections are fixed, and checks
every protected per-input baseline digest before independent scoring.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reference"))
import qtr_c90_exact_decoder_001 as Base
import qtr_c90_exact_execute_001 as Execute
import qtr_c90_exact_native_campaign_001 as Campaign

REPO = "grandchallenge/QUANTUM-TECHNOLOGIES"
EXPERIMENT_ID = "QTR-C90-EXACT-DECODER-001"
RECOVERY_SPEC = {
    "artifact_id": 12738710046,
    "archive_sha256": "dd59ab416d41b1e9025d82319e28bd0ab622e0cdc6e10b097ca470a879dd3a46",
    "run_id": 40511661627,
    "head_sha": "c588cbbc635fe477c8496fd69e6145f62b768b2e",
    "name": "TCM-QDEC-COMPARE-001-exact-head",
}
# All fields except the two actual replay heads are compared literally.
REPLAY_HEAD_COMMON = {
    "bposd_wheel_sha256": "80e439246c11ca824610f9bc7858c68eb1f8a6b7cbb71760cf6c86e03c47ff5d",
    "exact_head_equal": True,
    "execution_mode": "deterministic_3x3_cell_shard_with_exact_basis_oracle",
    "experiment_id": "TCM-QDEC-COMPARE-001",
    "ldpc_sdist_sha256": "3b2652aa993ab71672d680ac76ee2dcf3dc289fc5d11c07d060e5f838d8c3601",
    "manifest_payload_sha256": Execute.HISTORICAL_COMPARE_MANIFEST_PAYLOAD,
    "qec_circuit_001_authorized": False,
    "receipt_version": "0.3.0",
    "report_payload_sha256": Execute.HISTORICAL_COMPARE_REPORT_PAYLOAD,
    "timing_authoritative": False,
}

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as src:
        for chunk in iter(lambda: src.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def fetch_verified_archive(work: Path) -> Path:
    """Pin true October ZIP provenance, including current authenticated metadata."""
    spec = RECOVERY_SPEC
    p = subprocess.run(["gh", "api", f"repos/{REPO}/actions/artifacts/{spec['artifact_id']}"],
                       check=True, capture_output=True, text=True)
    meta = json.loads(p.stdout)
    wr = meta.get("workflow_run") or {}
    if (meta.get("id") != spec["artifact_id"] or meta.get("name") != spec["name"] or
        meta.get("digest") != "sha256:" + spec["archive_sha256"] or
        meta.get("expired") is not False or int(wr.get("id", -1)) != spec["run_id"] or
        wr.get("head_sha") != spec["head_sha"]):
        raise ValueError("recovery archive GitHub identity, run, head, hash, or retention drift")
    dest = work / "cache" / "conventional-replay" / (str(spec["artifact_id"]) + ".zip")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        with tempfile.NamedTemporaryFile(dir=dest.parent, suffix=".partial", delete=False) as tmp:
            partial = Path(tmp.name)
            try:
                subprocess.run(["gh", "api", f"repos/{REPO}/actions/artifacts/{spec['artifact_id']}/zip"],
                               stdout=tmp, check=True)
            except BaseException:
                partial.unlink(missing_ok=True)
                raise
        if sha256_file(partial) != spec["archive_sha256"]:
            partial.unlink(missing_ok=True)
            raise ValueError("downloaded replay ZIP digest mismatch")
        partial.replace(dest)
    if sha256_file(dest) != spec["archive_sha256"]:
        raise ValueError("cached replay ZIP digest mismatch")
    return dest

def verified_replay_outcomes(archive: Path) -> dict:
    """Verify original full report and all C90 cell/outcome hashes, never forge receipt."""
    if sha256_file(archive) != RECOVERY_SPEC["archive_sha256"]:
        raise ValueError("recovery ZIP SHA-256 mismatch")
    spec = RECOVERY_SPEC
    with zipfile.ZipFile(archive) as z:
        def load(name: str) -> dict:
            return json.loads(z.read("tmp/" + name).decode("utf-8"))
        receipt = load("TCM-QDEC-COMPARE-001-exact-head.json")
        if (receipt.get("evaluated_commit") != spec["head_sha"] or
            receipt.get("runtime_head") != spec["head_sha"] or
            {k: v for k, v in receipt.items() if k not in ("evaluated_commit", "runtime_head")}
            != REPLAY_HEAD_COMMON):
            raise ValueError("actual October replay exact-head receipt mismatch")
        report = load("TCM-QDEC-COMPARE-001-report.json")
        unsigned = dict(report)
        claimed = unsigned.pop("payload_sha256", None)
        if (claimed != Execute.HISTORICAL_COMPARE_REPORT_PAYLOAD or
            Base.digest(unsigned) != Execute.HISTORICAL_COMPARE_REPORT_PAYLOAD or
            report.get("manifest", {}).get("payload_sha256") != Execute.HISTORICAL_COMPARE_MANIFEST_PAYLOAD):
            raise ValueError("frozen historical full report digest mismatch")
        members = [n for n in z.namelist() if n.endswith("/TCM-QDEC-COMPARE-001-C90-corpus.json")]
        if len(members) != 1:
            raise ValueError("frozen C90 corpus missing or duplicated")
        corpus = json.loads(z.read(members[0]))
        if len(corpus) != 347 or Base.digest(corpus) != Base.C90_CORPUS_SHA:
            raise ValueError("frozen C90 corpus identity mismatch")
        methods = {}
        for method, expected in Base.EXPECTED_CONVENTIONAL.items():
            cell = load(f"compare-cells/C90-{method}.json")
            needed = ("surface", "method", "package_receipt", "corpus_size",
                      "summary", "outcomes", "result_records_sha256")
            subject = {key: cell[key] for key in needed}
            cell_digest = Execute.EXPECTED_CONVENTIONAL_CELLS[method]
            outcomes = cell.get("outcomes")
            if (set(cell) != set(needed) | {"experiment_id", "manifest_payload_sha256", "cell_payload_sha256"} or
                cell.get("cell_payload_sha256") != cell_digest or Base.digest(subject) != cell_digest or
                report.get("cell_payload_sha256", {}).get("C90/" + method) != cell_digest or
                cell.get("experiment_id") != "TCM-QDEC-COMPARE-001" or
                cell.get("manifest_payload_sha256") != Execute.HISTORICAL_COMPARE_MANIFEST_PAYLOAD or
                cell.get("surface") != "C90" or cell.get("method") != method or
                cell.get("corpus_size") != 347 or
                not isinstance(outcomes, list) or len(outcomes) != 347 or
                any(type(value) is not bool for value in outcomes) or
                Base.digest(outcomes) != Execute.EXPECTED_CONVENTIONAL_OUTCOMES[method] or
                sum(outcomes) != expected["oracle_success"] or
                cell.get("result_records_sha256") != expected["result_records_sha256"] or
                report.get("detailed_result_record_digests", {}).get("C90/" + method) != expected["result_records_sha256"]):
                raise ValueError(f"recovered C90 {method} evidence/record/outcome digest mismatch")
            methods[method] = {
                "outcomes": outcomes, "outcomes_sha256": Execute.EXPECTED_CONVENTIONAL_OUTCOMES[method],
                "cell_payload_sha256": cell_digest,
                "result_records_sha256": expected["result_records_sha256"],
                "oracle_success": expected["oracle_success"],
            }
    return {
        "source": {
            "recovery_type": "OCTOBER_REPLAY_CONTENT_IDENTICAL_TO_PROTECTED_COMPARED_C90_RECORDS",
            "workflow_run": spec["run_id"], "artifact_id": spec["artifact_id"],
            "artifact_digest": "sha256:" + spec["archive_sha256"],
            "head_sha": spec["head_sha"],
            "protected_original_workflow_run": Execute.HISTORICAL_COMPARE_RUN,
            "protected_original_artifact_id": Execute.HISTORICAL_COMPARE_ARTIFACT_ID,
            "protected_original_archive_digest": Execute.HISTORICAL_COMPARE_ARTIFACT_DIGEST,
            "protected_original_archive_not_byte_verified": True,
            "protected_full_report_payload_sha256": Execute.HISTORICAL_COMPARE_REPORT_PAYLOAD,
            "frozen_corpus_sha256": Base.C90_CORPUS_SHA,
        },
        "methods": methods,
    }

def score_fixed_verified_replay(fixed_path: Path, work: Path, orchestrator_head: str, output: Path) -> dict:
    """Original frozen score_and_compare, after original correction-fixing gate."""
    frozen = json.loads(fixed_path.read_text(encoding="utf-8"))
    if (frozen.get("status") != "C90_EXACT_CORRECTIONS_FIXED" or
        frozen.get("quality_exposed") is not False or
        frozen.get("activation_head") != Campaign.ACTIVATION_HEAD or
        frozen.get("orchestration_head") != orchestrator_head):
        raise ValueError("C90 fixed-correction ordering/identity gate failed")
    rows = frozen.get("fixed_decoder_rows", [])
    if (len(rows) != 347 or Base.digest(rows) != frozen.get("fixed_decoder_rows_sha256")
        or [int(x["index"]) for x in rows] != list(range(347))):
        raise ValueError("frozen correction rows digest/index coverage drift")
    conventional = verified_replay_outcomes(fetch_verified_archive(work))
    scored = Execute.score_and_compare(rows, Campaign.frozen_context(),
                                        list(Campaign.frozen_corpus()), conventional)
    if scored.get("status") != "C90_TCM_MATCHED_COMPARISON_COMPLETED":
        raise ValueError("authoritative comparison predicate failed")
    result = {
        "experiment_id": EXPERIMENT_ID,
        "phase": "ACTIVATED_INDEPENDENT_SCORE_AND_MATCHED_COMPARE",
        "status": scored["status"], "activation_head": Campaign.ACTIVATION_HEAD,
        "orchestration_head": orchestrator_head, "manifest_payload_sha256": Base.MANIFEST_PAYLOAD,
        "validation_payload_sha256": Campaign.VALIDATION_PAYLOAD_SHA256,
        "fixed_decoder_rows_sha256": frozen["fixed_decoder_rows_sha256"],
        "scoring_and_comparison": scored,
        "claim_boundary": Base.load_manifest()["claim_boundary"],
        "corrections_fixed_before_scoring": True,
        "independent_scoring_performed": True,
        "matched_comparison_performed": True,
        "quality_exposed": True,
        "scientific_semantics_changed": False,
        "replay_content_equivalence_verified_before_scoring": True,
    }
    Campaign.write_json(output, result)
    return result

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="mode", required=True)
    check = sub.add_parser("verify-local")
    check.add_argument("--archive", type=Path, required=True)
    s = sub.add_parser("score")
    s.add_argument("--fixed", type=Path, required=True)
    s.add_argument("--work-root", type=Path, required=True)
    s.add_argument("--orchestration-head", required=True)
    s.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.mode == "verify-local":
        c = verified_replay_outcomes(args.archive)
        print(json.dumps({"status": "RECOVERED_C90_COMPARISON_OUTCOMES_CONTENT_VERIFIED",
                          "source": c["source"],
                          "successes": {k: v["oracle_success"] for k,v in c["methods"].items()}},
                         sort_keys=True))
    else:
        out = score_fixed_verified_replay(args.fixed, args.work_root,
                                          args.orchestration_head, args.output)
        print(json.dumps({"status": out["status"], "quality_exposed": out["quality_exposed"]}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
