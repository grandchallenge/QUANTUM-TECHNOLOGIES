#!/usr/bin/env python3
"""Quality-blind validation and activated exact C90 campaign runner."""
from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path
from typing import Any

import qtr_c90_exact_decoder_001 as Base
import qtr_c90_exact_dag_001 as DAG

ROOT = Path(__file__).resolve().parents[1]
EVALUATOR_VERSION = "0.3.1"
HISTORICAL_COMPARE_RUN = 32079738866
HISTORICAL_COMPARE_ARTIFACT_ID = 9304727792
HISTORICAL_COMPARE_ARTIFACT_DIGEST = "sha256:34f37ec1a351a42e08c7143b359ca40191db4cd92ceeab2881930a67e3942182"
HISTORICAL_COMPARE_HEAD = "3ebe409c60e7907b8251d44ee822141159d2879c"
HISTORICAL_COMPARE_MANIFEST_PAYLOAD = "c68830f40733cde6957713060cec35adf317c75572cc960610c07c4d0e24d1e2"
HISTORICAL_COMPARE_REPORT_PAYLOAD = "6385c2da742e14ecf2bc41336c78c2a8ff42b1cdd897fb5e7cfac056e2214146"
EXPECTED_CONVENTIONAL_CELLS = {
    "BP_MIN_SUM": "3c46d32686fcf4c821c9e9e973f107837c56f63abc69e71175cf555cde4979e5",
    "BP_OSD_CS_7": "f86b3764780328a67c7cb84dc92920ebbd499b8c2eeef7cb2c9cf3b9edfbe240",
    "BP_SUM_PRODUCT": "26237bdf051a15b20dc3a0cc2fcc2b02b264a0f7c037d601af21c1fd9fac2ab0",
}
EXPECTED_CONVENTIONAL_OUTCOMES = {
    "BP_MIN_SUM": "9652133baf36b83605c2f394067bd25938b47eb9595435b72470256ca1fe5bae",
    "BP_OSD_CS_7": "bd2141809336ae41db0a5e471be74603e780f6b7beba72a541bdc00132ab50ea",
    "BP_SUM_PRODUCT": "d943dcfbf110e8c1e57558bddec270da374d6ea0abc9be9923d848e30eac3f48",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _unique_file(root: Path, name: str) -> Path:
    matches = list(root.rglob(name))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {name} in historical artifact, found {len(matches)}")
    return matches[0]


def load_conventional_outcomes(artifact_dir: Path) -> dict[str, Any]:
    """Load the original promoted COMPARE-001 artifact; never rerun a decoder."""
    root = Path(artifact_dir)
    exact_head = load_json(_unique_file(root, "TCM-QDEC-COMPARE-001-exact-head.json"))
    if exact_head != {
        "bposd_wheel_sha256": "80e439246c11ca824610f9bc7858c68eb1f8a6b7cbb71760cf6c86e03c47ff5d",
        "evaluated_commit": HISTORICAL_COMPARE_HEAD,
        "exact_head_equal": True,
        "execution_mode": "deterministic_3x3_cell_shard_with_exact_basis_oracle",
        "experiment_id": "TCM-QDEC-COMPARE-001",
        "ldpc_sdist_sha256": "3b2652aa993ab71672d680ac76ee2dcf3dc289fc5d11c07d060e5f838d8c3601",
        "manifest_payload_sha256": HISTORICAL_COMPARE_MANIFEST_PAYLOAD,
        "qec_circuit_001_authorized": False,
        "receipt_version": "0.3.0",
        "report_payload_sha256": HISTORICAL_COMPARE_REPORT_PAYLOAD,
        "runtime_head": HISTORICAL_COMPARE_HEAD,
        "timing_authoritative": False,
    }:
        raise ValueError("historical COMPARE-001 exact-head receipt drift")

    report = load_json(_unique_file(root, "TCM-QDEC-COMPARE-001-report.json"))
    claimed = report.get("payload_sha256")
    unsigned = dict(report)
    unsigned.pop("payload_sha256", None)
    if claimed != HISTORICAL_COMPARE_REPORT_PAYLOAD or Base.digest(unsigned) != HISTORICAL_COMPARE_REPORT_PAYLOAD:
        raise ValueError("historical COMPARE-001 full report digest drift")
    if report.get("manifest", {}).get("payload_sha256") != HISTORICAL_COMPARE_MANIFEST_PAYLOAD:
        raise ValueError("historical COMPARE-001 manifest drift")

    methods: dict[str, Any] = {}
    for method, expected in Base.EXPECTED_CONVENTIONAL.items():
        cell = load_json(_unique_file(root, f"C90-{method}.json"))
        expected_cell = EXPECTED_CONVENTIONAL_CELLS[method]
        if cell.get("cell_payload_sha256") != expected_cell:
            raise ValueError(f"historical C90 cell digest drift: {method}")
        if cell.get("experiment_id") != "TCM-QDEC-COMPARE-001":
            raise ValueError(f"historical C90 cell experiment drift: {method}")
        if cell.get("manifest_payload_sha256") != HISTORICAL_COMPARE_MANIFEST_PAYLOAD:
            raise ValueError(f"historical C90 cell manifest drift: {method}")
        if cell.get("surface") != "C90" or cell.get("method") != method or int(cell.get("corpus_size", -1)) != 347:
            raise ValueError(f"historical C90 cell identity drift: {method}")
        outcomes = cell.get("outcomes", [])
        if len(outcomes) != 347 or any(value not in (True, False) for value in outcomes):
            raise ValueError(f"invalid historical C90 outcomes: {method}")
        if Base.digest(outcomes) != EXPECTED_CONVENTIONAL_OUTCOMES[method]:
            raise ValueError(f"historical C90 per-input outcome digest drift: {method}")
        if sum(outcomes) != expected["oracle_success"]:
            raise ValueError(f"historical C90 success total drift: {method}")
        if cell.get("result_records_sha256") != expected["result_records_sha256"]:
            raise ValueError(f"historical C90 result-record digest drift: {method}")
        report_key = f"C90/{method}"
        if report.get("cell_payload_sha256", {}).get(report_key) != expected_cell:
            raise ValueError(f"historical report/cell digest mismatch: {method}")
        if report.get("detailed_result_record_digests", {}).get(report_key) != expected["result_records_sha256"]:
            raise ValueError(f"historical report/result digest mismatch: {method}")
        methods[method] = {
            "outcomes": outcomes,
            "outcomes_sha256": EXPECTED_CONVENTIONAL_OUTCOMES[method],
            "cell_payload_sha256": expected_cell,
            "result_records_sha256": expected["result_records_sha256"],
            "oracle_success": expected["oracle_success"],
        }

    return {
        "source": {
            "workflow_run": HISTORICAL_COMPARE_RUN,
            "artifact_id": HISTORICAL_COMPARE_ARTIFACT_ID,
            "artifact_digest": HISTORICAL_COMPARE_ARTIFACT_DIGEST,
            "head_sha": HISTORICAL_COMPARE_HEAD,
            "report_payload_sha256": HISTORICAL_COMPARE_REPORT_PAYLOAD,
        },
        "methods": methods,
    }


def verify_conventional_artifact(artifact_dir: Path) -> dict[str, Any]:
    conventional = load_conventional_outcomes(artifact_dir)
    return {
        "experiment_id": Base.EXPERIMENT_ID,
        "evaluator_version": EVALUATOR_VERSION,
        "status": "PROTECTED_CONVENTIONAL_C90_OUTCOMES_VERIFIED",
        "source_commit": DAG.git_head(),
        "manifest_payload_sha256": Base.MANIFEST_PAYLOAD,
        "historical_conventional_source": conventional["source"],
        "methods": {
            method: {
                "oracle_success": row["oracle_success"],
                "cell_payload_sha256": row["cell_payload_sha256"],
                "result_records_sha256": row["result_records_sha256"],
                "outcomes_sha256": row["outcomes_sha256"],
                "outcome_count": len(row["outcomes"]),
            }
            for method, row in conventional["methods"].items()
        },
        "quality_exposed": False,
        "new_c90_tcm_quality_exposed": False,
    }


def preflight() -> dict[str, Any]:
    result = Base.preflight()
    if result["quality_exposed"] is not False:
        raise AssertionError("base preflight exposed quality")
    signature = inspect.signature(Base.decode_c90_syndrome)
    if set(signature.parameters) != {"full_hz_syndrome", "channel_metadata", "compiled", "context"}:
        raise AssertionError("decoder information boundary drift")
    result = dict(result)
    result["evaluator_version"] = EVALUATOR_VERSION
    result["historical_conventional_artifact"] = {
        "workflow_run": HISTORICAL_COMPARE_RUN,
        "artifact_id": HISTORICAL_COMPARE_ARTIFACT_ID,
        "artifact_digest": HISTORICAL_COMPARE_ARTIFACT_DIGEST,
        "head_sha": HISTORICAL_COMPARE_HEAD,
        "report_payload_sha256": HISTORICAL_COMPARE_REPORT_PAYLOAD,
        "restoration_required_for_matched_join": True,
        "conventional_decoder_rerun_allowed": False,
    }
    return result


def compile_validate(compiled_output: Path) -> dict[str, Any]:
    pre = preflight()
    context = Base.load_c90_context()
    compiled = DAG.compile_all(context)
    receipts = compiled.receipts()
    validation = DAG.validate_compiled(compiled)
    DAG.save_compiled(compiled, compiled_output)
    identities = {algebra: receipts[algebra]["canonical_node_stream_sha256"] for algebra in DAG.ALGEBRAS}
    return {
        "experiment_id": Base.EXPERIMENT_ID,
        "evaluator_version": EVALUATOR_VERSION,
        "status": "C90_EXACT_IMPLEMENTATION_QUALITY_BLIND_VALIDATED",
        "source_commit": DAG.git_head(),
        "manifest_payload_sha256": Base.MANIFEST_PAYLOAD,
        "preflight_payload_sha256": Base.digest(pre),
        "compiled": receipts,
        "canonical_node_stream_sha256": identities,
        "independent_repeat_compile": "NOT_PERFORMED_ON_PRIMARY_ROUTE__REPLAY_WHEN_RESOURCES_PERMIT",
        "semantic_validation": validation,
        "quality_exposed": False,
    }


def _fixed_decode_rows(compiled: DAG.CompiledC90, context: dict[str, Any], corpus: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in corpus:
        error = Base.F2.b2i(record["error"])
        syndrome = Base.F2.syndrome(error, context["code"]["hz"])
        decoded = Base.decode_c90_syndrome(syndrome, Base.CHANNEL_METADATA, compiled=compiled, context=context)
        rows.append({
            "index": int(record["index"]),
            "syndrome": Base.F2.i2b(syndrome, len(context["code"]["hz"])),
            "logical_classes_evaluated": decoded["logical_classes_evaluated"],
            "class_score_stream_sha256": Base.digest(decoded["decisions"]),
            "decisions": {
                algebra: {
                    **cell,
                    "correction": Base.F2.i2b(int(cell["correction"]), 90),
                    "canonical_key": Base.F2.i2b(int(cell["canonical_key"]), 90),
                    "tied_canonical_keys": [Base.F2.i2b(int(v), 90) for v in cell["tied_canonical_keys"]],
                }
                for algebra, cell in decoded["decisions"].items()
            },
        })
    return rows


def _rowspace_contains(vector: int, rows: list[int], width: int, expected_rank: int) -> bool:
    return Base.rank_rref(rows + [int(vector)], width)[0] == expected_rank


def score_and_compare(
    fixed_rows: list[dict[str, Any]],
    context: dict[str, Any],
    corpus: list[dict[str, Any]],
    conventional: dict[str, Any],
) -> dict[str, Any]:
    by_index = {int(row["index"]): row for row in fixed_rows}
    if sorted(by_index) != list(range(347)):
        raise AssertionError("fixed C90 correction coverage incomplete")
    totals = {
        algebra: {
            "inputs": 0,
            "syndrome_consistent": 0,
            "syndrome_inconsistent": 0,
            "oracle_success": 0,
            "oracle_failure": 0,
        }
        for algebra in DAG.ALGEBRAS
    }
    scored_rows: list[dict[str, Any]] = []
    outcomes = {algebra: [] for algebra in DAG.ALGEBRAS}
    for corpus_record in corpus:
        index = int(corpus_record["index"])
        error = Base.F2.b2i(corpus_record["error"])
        expected_syndrome = Base.F2.syndrome(error, context["code"]["hz"])
        fixed = by_index[index]
        if Base.F2.b2i(fixed["syndrome"]) != expected_syndrome:
            raise AssertionError("fixed decoder row syndrome drift")
        scored = {"index": index, "algebras": {}}
        for algebra in DAG.ALGEBRAS:
            correction = Base.F2.b2i(fixed["decisions"][algebra]["correction"])
            consistent = Base.F2.syndrome(correction, context["code"]["hz"]) == expected_syndrome
            correct = consistent and _rowspace_contains(
                error ^ correction, context["code"]["hx"], 90, context["hx_rank"]
            )
            bucket = totals[algebra]
            bucket["inputs"] += 1
            bucket["syndrome_consistent" if consistent else "syndrome_inconsistent"] += 1
            bucket["oracle_success" if correct else "oracle_failure"] += 1
            outcomes[algebra].append(bool(correct))
            scored["algebras"][algebra] = {
                "syndrome_consistent": consistent,
                "oracle_correct": bool(correct),
                "correction_weight": correction.bit_count(),
            }
        scored_rows.append(scored)

    pairwise: list[dict[str, Any]] = []
    for algebra in DAG.ALGEBRAS:
        for method in Base.EXPECTED_CONVENTIONAL:
            conv = conventional["methods"][method]["outcomes"]
            tcm = outcomes[algebra]
            both = sum(a and b for a, b in zip(tcm, conv))
            tcm_only = sum(a and not b for a, b in zip(tcm, conv))
            conv_only = sum((not a) and b for a, b in zip(tcm, conv))
            neither = 347 - both - tcm_only - conv_only
            pairwise.append({
                "tcm": algebra,
                "conventional": method,
                "both": both,
                "TCM-only": tcm_only,
                "conventional-only": conv_only,
                "neither": neither,
            })
    complete = all(
        value["inputs"] == 347 and value["syndrome_inconsistent"] == 0
        for value in totals.values()
    )
    return {
        "status": "C90_TCM_MATCHED_COMPARISON_COMPLETED" if complete else "C90_EXACT_SEMANTIC_VALIDATION_FAILED",
        "tcm_totals": totals,
        "pairwise_contingency": pairwise,
        "scored_rows": scored_rows,
        "scored_rows_sha256": Base.digest(scored_rows),
        "protected_conventional_source": conventional["source"],
    }


def campaign(
    activation_head: str,
    compiled_path: Path,
    validation_receipt: Path,
    conventional_artifact_dir: Path,
) -> dict[str, Any]:
    if not activation_head or activation_head != DAG.git_head():
        raise ValueError("campaign requires exact frozen execution-activation head equal to current HEAD")
    pre = preflight()
    context = Base.load_c90_context()
    corpus = Base.c90_corpus_records()
    receipt = load_json(validation_receipt)
    if receipt.get("status") != "C90_EXACT_IMPLEMENTATION_QUALITY_BLIND_VALIDATED":
        raise ValueError("quality-blind validation receipt is not passing")
    if receipt.get("source_commit") != activation_head or receipt.get("quality_exposed") is not False:
        raise ValueError("quality-blind validation receipt is not bound to activation head")
    compiled = DAG.load_compiled(compiled_path, context)
    compiled_ids = {
        algebra: compiled.receipts()[algebra]["canonical_node_stream_sha256"]
        for algebra in DAG.ALGEBRAS
    }
    if compiled_ids != receipt.get("canonical_node_stream_sha256"):
        raise ValueError("compiled representation identities differ from validation receipt")
    validation = receipt.get("semantic_validation", {})
    if validation.get("status") != "C90_EXACT_SEMANTIC_VALIDATION_PASSED" or validation.get("quality_exposed") is not False:
        raise AssertionError("quality-blind semantic validation did not pass")

    conventional = load_conventional_outcomes(conventional_artifact_dir)
    fixed_rows = _fixed_decode_rows(compiled, context, corpus)
    scored = score_and_compare(fixed_rows, context, corpus, conventional)
    return {
        "experiment_id": Base.EXPERIMENT_ID,
        "evaluator_version": EVALUATOR_VERSION,
        "status": scored["status"],
        "source_commit": DAG.git_head(),
        "execution_activation_head": activation_head,
        "manifest_payload_sha256": Base.MANIFEST_PAYLOAD,
        "preflight_payload_sha256": Base.digest(pre),
        "quality_blind_validation_receipt_payload_sha256": receipt.get("payload_sha256"),
        "compiled": compiled.receipts(),
        "semantic_validation": validation,
        "fixed_decoder_rows": fixed_rows,
        "fixed_decoder_rows_sha256": Base.digest(fixed_rows),
        "scoring_and_comparison": scored,
        "claim_boundary": Base.load_manifest()["claim_boundary"],
        "quality_exposed": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=["preflight", "verify-conventional", "compile-validate", "campaign"],
        required=True,
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compiled-output", type=Path)
    parser.add_argument("--activation-head")
    parser.add_argument("--compiled", type=Path)
    parser.add_argument("--validation-receipt", type=Path)
    parser.add_argument("--conventional-artifact-dir", type=Path)
    args = parser.parse_args()

    if args.mode == "preflight":
        result = preflight()
    elif args.mode == "verify-conventional":
        if args.conventional_artifact_dir is None:
            parser.error("--conventional-artifact-dir is required for verify-conventional")
        result = verify_conventional_artifact(args.conventional_artifact_dir)
    elif args.mode == "compile-validate":
        if args.compiled_output is None:
            parser.error("--compiled-output is required for compile-validate")
        result = compile_validate(args.compiled_output)
    else:
        if not args.activation_head:
            parser.error("--activation-head is required for campaign")
        if args.compiled is None or args.validation_receipt is None or args.conventional_artifact_dir is None:
            parser.error("--compiled, --validation-receipt, and --conventional-artifact-dir are required for campaign")
        result = campaign(
            args.activation_head,
            args.compiled,
            args.validation_receipt,
            args.conventional_artifact_dir,
        )

    result["payload_sha256"] = Base.digest(result)
    write_json(args.output, result)
    print(json.dumps({"status": result["status"], "payload_sha256": result["payload_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
