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
EVALUATOR_VERSION = "0.2.0"
CONVENTIONAL_OUTCOMES_PATH = ROOT / "registry" / "qtr-c90-exact-decoder-001-conventional-outcomes.json"
CONVENTIONAL_OUTCOMES_PAYLOAD = "0355c5a7d57b881661126aa897ea9622b1a0672d15db7d801c71fefe14652423"
EXPECTED_CONVENTIONAL_CELLS = {
    "BP_MIN_SUM": "3c46d32686fcf4c821c9e9e973f107837c56f63abc69e71175cf555cde4979e5",
    "BP_OSD_CS_7": "f86b3764780328a67c7cb84dc92920ebbd499b8c2eeef7cb2c9cf3b9edfbe240",
    "BP_SUM_PRODUCT": "26237bdf051a15b20dc3a0cc2fcc2b02b264a0f7c037d601af21c1fd9fac2ab0",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_conventional_outcomes() -> dict[str, Any]:
    data = load_json(CONVENTIONAL_OUTCOMES_PATH)
    claimed = data.get("payload_sha256"); unsigned = dict(data); unsigned.pop("payload_sha256", None)
    if claimed != CONVENTIONAL_OUTCOMES_PAYLOAD or Base.digest(unsigned) != CONVENTIONAL_OUTCOMES_PAYLOAD:
        raise ValueError("protected conventional outcome fixture digest drift")
    if data.get("corpus") != {"size": 347, "sha256": Base.C90_CORPUS_SHA}:
        raise ValueError("protected conventional outcome corpus drift")
    for method, expected in Base.EXPECTED_CONVENTIONAL.items():
        cell = data.get("methods", {}).get(method, {}); outcomes = cell.get("outcomes", [])
        if len(outcomes) != 347 or any(value not in (True, False) for value in outcomes):
            raise ValueError(f"invalid protected conventional outcomes: {method}")
        if sum(outcomes) != expected["oracle_success"]: raise ValueError(f"protected conventional success total drift: {method}")
        if cell.get("result_records_sha256") != expected["result_records_sha256"]: raise ValueError(f"protected conventional record digest drift: {method}")
        if cell.get("cell_payload_sha256") != EXPECTED_CONVENTIONAL_CELLS[method]: raise ValueError(f"protected conventional cell payload drift: {method}")
    return data


def preflight() -> dict[str, Any]:
    result = Base.preflight(); fixture = load_conventional_outcomes()
    if result["quality_exposed"] is not False: raise AssertionError("base preflight exposed quality")
    signature = inspect.signature(Base.decode_c90_syndrome)
    if set(signature.parameters) != {"full_hz_syndrome", "channel_metadata", "compiled", "context"}:
        raise AssertionError("decoder information boundary drift")
    result = dict(result)
    result["evaluator_version"] = EVALUATOR_VERSION
    result["conventional_per_input_outcomes"] = {"payload_sha256": fixture["payload_sha256"], "source": fixture["source"]}
    return result


def compile_validate(compiled_output: Path) -> dict[str, Any]:
    pre = preflight(); context = Base.load_c90_context(); compiled = DAG.compile_all(context)
    receipts = compiled.receipts(); validation = DAG.validate_compiled(compiled); DAG.save_compiled(compiled, compiled_output)
    identities = {algebra: receipts[algebra]["canonical_node_stream_sha256"] for algebra in DAG.ALGEBRAS}
    return {
        "experiment_id": Base.EXPERIMENT_ID, "evaluator_version": EVALUATOR_VERSION,
        "status": "C90_EXACT_IMPLEMENTATION_QUALITY_BLIND_VALIDATED", "source_commit": DAG.git_head(),
        "manifest_payload_sha256": Base.MANIFEST_PAYLOAD, "preflight_payload_sha256": Base.digest(pre),
        "compiled": receipts, "canonical_node_stream_sha256": identities,
        "independent_repeat_compile": "NOT_PERFORMED_ON_PRIMARY_ROUTE__REPLAY_WHEN_RESOURCES_PERMIT",
        "semantic_validation": validation, "quality_exposed": False,
    }


def _fixed_decode_rows(compiled: DAG.CompiledC90, context: dict[str, Any], corpus: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in corpus:
        error = Base.F2.b2i(record["error"])
        syndrome = Base.F2.syndrome(error, context["code"]["hz"])
        decoded = Base.decode_c90_syndrome(syndrome, Base.CHANNEL_METADATA, compiled=compiled, context=context)
        rows.append({
            "index": int(record["index"]), "syndrome": Base.F2.i2b(syndrome, len(context["code"]["hz"])),
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


def score_and_compare(fixed_rows: list[dict[str, Any]], context: dict[str, Any], corpus: list[dict[str, Any]]) -> dict[str, Any]:
    by_index = {int(row["index"]): row for row in fixed_rows}
    if sorted(by_index) != list(range(347)): raise AssertionError("fixed C90 correction coverage incomplete")
    totals = {a: {"inputs": 0, "syndrome_consistent": 0, "syndrome_inconsistent": 0, "oracle_success": 0, "oracle_failure": 0} for a in DAG.ALGEBRAS}
    scored_rows: list[dict[str, Any]] = []; outcomes = {a: [] for a in DAG.ALGEBRAS}
    for corpus_record in corpus:
        index = int(corpus_record["index"]); error = Base.F2.b2i(corpus_record["error"])
        expected_syndrome = Base.F2.syndrome(error, context["code"]["hz"]); fixed = by_index[index]
        if Base.F2.b2i(fixed["syndrome"]) != expected_syndrome: raise AssertionError("fixed decoder row syndrome drift")
        scored = {"index": index, "algebras": {}}
        for algebra in DAG.ALGEBRAS:
            correction = Base.F2.b2i(fixed["decisions"][algebra]["correction"])
            consistent = Base.F2.syndrome(correction, context["code"]["hz"]) == expected_syndrome
            correct = consistent and _rowspace_contains(error ^ correction, context["code"]["hx"], 90, context["hx_rank"])
            bucket = totals[algebra]; bucket["inputs"] += 1
            bucket["syndrome_consistent" if consistent else "syndrome_inconsistent"] += 1
            bucket["oracle_success" if correct else "oracle_failure"] += 1; outcomes[algebra].append(bool(correct))
            scored["algebras"][algebra] = {"syndrome_consistent": consistent, "oracle_correct": bool(correct), "correction_weight": correction.bit_count()}
        scored_rows.append(scored)
    conventional = load_conventional_outcomes(); pairwise: list[dict[str, Any]] = []
    for algebra in DAG.ALGEBRAS:
        for method in Base.EXPECTED_CONVENTIONAL:
            conv = conventional["methods"][method]["outcomes"]; tcm = outcomes[algebra]
            both = sum(a and b for a, b in zip(tcm, conv)); tcm_only = sum(a and not b for a, b in zip(tcm, conv)); conv_only = sum((not a) and b for a, b in zip(tcm, conv)); neither = 347 - both - tcm_only - conv_only
            pairwise.append({"tcm": algebra, "conventional": method, "both": both, "TCM-only": tcm_only, "conventional-only": conv_only, "neither": neither})
    complete = all(v["inputs"] == 347 and v["syndrome_inconsistent"] == 0 for v in totals.values())
    return {"status": "C90_TCM_MATCHED_COMPARISON_COMPLETED" if complete else "C90_EXACT_SEMANTIC_VALIDATION_FAILED", "tcm_totals": totals, "pairwise_contingency": pairwise, "scored_rows": scored_rows, "scored_rows_sha256": Base.digest(scored_rows), "protected_conventional_outcomes_payload_sha256": conventional["payload_sha256"]}


def campaign(activation_head: str, compiled_path: Path, validation_receipt: Path) -> dict[str, Any]:
    if not activation_head or activation_head != DAG.git_head(): raise ValueError("campaign requires exact frozen execution-activation head equal to current HEAD")
    pre = preflight(); context = Base.load_c90_context(); corpus = Base.c90_corpus_records(); receipt = load_json(validation_receipt)
    if receipt.get("status") != "C90_EXACT_IMPLEMENTATION_QUALITY_BLIND_VALIDATED": raise ValueError("quality-blind validation receipt is not passing")
    if receipt.get("source_commit") != activation_head or receipt.get("quality_exposed") is not False: raise ValueError("quality-blind validation receipt is not bound to activation head")
    compiled = DAG.load_compiled(compiled_path, context)
    compiled_ids = {a: compiled.receipts()[a]["canonical_node_stream_sha256"] for a in DAG.ALGEBRAS}
    if compiled_ids != receipt.get("canonical_node_stream_sha256"): raise ValueError("compiled representation identities differ from validation receipt")
    validation = receipt.get("semantic_validation", {})
    if validation.get("status") != "C90_EXACT_SEMANTIC_VALIDATION_PASSED" or validation.get("quality_exposed") is not False: raise AssertionError("quality-blind semantic validation did not pass")
    fixed_rows = _fixed_decode_rows(compiled, context, corpus); scored = score_and_compare(fixed_rows, context, corpus)
    return {
        "experiment_id": Base.EXPERIMENT_ID, "evaluator_version": EVALUATOR_VERSION, "status": scored["status"],
        "source_commit": DAG.git_head(), "execution_activation_head": activation_head,
        "manifest_payload_sha256": Base.MANIFEST_PAYLOAD, "preflight_payload_sha256": Base.digest(pre),
        "quality_blind_validation_receipt_payload_sha256": receipt.get("payload_sha256"),
        "compiled": compiled.receipts(), "semantic_validation": validation,
        "fixed_decoder_rows": fixed_rows, "fixed_decoder_rows_sha256": Base.digest(fixed_rows),
        "scoring_and_comparison": scored, "claim_boundary": Base.load_manifest()["claim_boundary"], "quality_exposed": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["preflight", "compile-validate", "campaign"], required=True)
    parser.add_argument("--output", type=Path, required=True); parser.add_argument("--compiled-output", type=Path)
    parser.add_argument("--activation-head"); parser.add_argument("--compiled", type=Path); parser.add_argument("--validation-receipt", type=Path)
    args = parser.parse_args()
    if args.mode == "preflight": result = preflight()
    elif args.mode == "compile-validate":
        if args.compiled_output is None: parser.error("--compiled-output is required for compile-validate")
        result = compile_validate(args.compiled_output)
    else:
        if not args.activation_head: parser.error("--activation-head is required for campaign")
        if args.compiled is None or args.validation_receipt is None: parser.error("--compiled and --validation-receipt are required for campaign")
        result = campaign(args.activation_head, args.compiled, args.validation_receipt)
    result["payload_sha256"] = Base.digest(result); write_json(args.output, result)
    print(json.dumps({"status": result["status"], "payload_sha256": result["payload_sha256"]}, sort_keys=True)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
