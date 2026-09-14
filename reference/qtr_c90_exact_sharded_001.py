#!/usr/bin/env python3
"""Sharded quality-blind exact C90 compilation/validation transport.

This module changes only execution topology. Each frozen algebra is compiled
independently with qtr_c90_exact_dag_001.compile_algebra, and the already-frozen
307-selector exact semantic validation is partitioned into deterministic index
ranges. Aggregation requires complete exact coverage before producing the same
combined activation-candidate representation consumed by the campaign runner.
"""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
from typing import Any

import qtr_c90_exact_decoder_001 as Base
import qtr_c90_exact_dag_001 as DAG
import qtr_c90_exact_execute_001 as Execute

EXPERIMENT_ID = Base.EXPERIMENT_ID
EVALUATOR_VERSION = "0.1.0"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _freeze_json(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(_freeze_json(item) for item in value)
    if isinstance(value, dict):
        return {key: _freeze_json(item) for key, item in value.items()}
    return value


def save_algebra(item: dict[str, Any], path: Path) -> None:
    payload = {
        "schema_version": 1,
        "experiment_id": EXPERIMENT_ID,
        "source_commit": DAG.git_head(),
        "manifest_payload_sha256": Base.MANIFEST_PAYLOAD,
        "representation": DAG.REPRESENTATION,
        "algebra": item["algebra"],
        "root": int(item["root"]),
        "nodes": item["dag"].nodes,
        "receipt": item["receipt"],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=6) as handle:
        json.dump(
            payload,
            handle,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        handle.write("\n")


def load_algebra(path: Path, context: dict[str, Any] | None = None) -> dict[str, Any]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)
    if payload.get("schema_version") != 1 or payload.get("experiment_id") != EXPERIMENT_ID:
        raise ValueError("sharded compiled C90 artifact identity drift")
    if payload.get("source_commit") != DAG.git_head():
        raise ValueError("sharded compiled C90 artifact is not bound to current HEAD")
    if payload.get("manifest_payload_sha256") != Base.MANIFEST_PAYLOAD:
        raise ValueError("sharded compiled C90 manifest drift")
    if payload.get("representation") != DAG.REPRESENTATION:
        raise ValueError("sharded compiled C90 representation drift")
    algebra = payload.get("algebra")
    if algebra not in DAG.ALGEBRAS:
        raise ValueError("sharded compiled C90 algebra drift")
    dag = DAG.ExpressionDAG()
    dag.nodes = [tuple(_freeze_json(node)) for node in payload["nodes"]]
    dag.interned = {node: index for index, node in enumerate(dag.nodes)}
    dag.peak_nodes = len(dag.nodes)
    root = int(payload["root"])
    receipt = payload["receipt"]
    observed = dag.canonical_receipt(root, algebra)
    for key in (
        "canonical_node_stream_sha256",
        "root",
        "reachable_nodes",
        "node_kind_counts",
        "canonical_node_stream_bytes_excluding_header",
    ):
        if observed.get(key) != receipt.get(key):
            raise ValueError(f"sharded compiled C90 canonical receipt drift: {algebra}:{key}")
    return {"algebra": algebra, "dag": dag, "root": root, "receipt": receipt}


def compile_one(algebra: str, compiled_output: Path) -> dict[str, Any]:
    if algebra not in DAG.ALGEBRAS:
        raise ValueError(algebra)
    preflight = Execute.preflight()
    if preflight.get("quality_exposed") is not False:
        raise AssertionError("preflight exposed C90 quality")
    context = Base.load_c90_context()
    item = DAG.compile_algebra(context, algebra)
    save_algebra(item, compiled_output)
    return {
        "experiment_id": EXPERIMENT_ID,
        "evaluator_version": EVALUATOR_VERSION,
        "phase": "QUALITY_BLIND_COMPILE_ALGEBRA",
        "status": "C90_EXACT_ALGEBRA_COMPILED_QUALITY_BLIND",
        "source_commit": DAG.git_head(),
        "manifest_payload_sha256": Base.MANIFEST_PAYLOAD,
        "algebra": algebra,
        "compiled": item["receipt"],
        "quality_exposed": False,
    }


def validate_shard(
    algebra: str,
    compiled_path: Path,
    start: int,
    stop: int,
) -> dict[str, Any]:
    if algebra not in DAG.ALGEBRAS:
        raise ValueError(algebra)
    coordinates = Base.frozen_validation_coordinates()
    if not (0 <= start < stop <= len(coordinates)):
        raise ValueError("invalid frozen validation shard bounds")
    context = Base.load_c90_context()
    item = load_algebra(compiled_path, context)
    if item["algebra"] != algebra:
        raise ValueError("validation shard algebra/artifact mismatch")
    rows: list[dict[str, Any]] = []
    for index in range(start, stop):
        coordinate = coordinates[index]
        observed = item["dag"].evaluate(item["root"], coordinate, algebra)
        expected = DAG.direct_contract_selector(context, algebra, coordinate)
        if observed != expected:
            raise AssertionError(
                f"C90 exact semantic mismatch: {algebra} selector_index={index} coordinate={coordinate}"
            )
        rows.append(
            {
                "selector_index": index,
                "selector_coordinate": coordinate,
                "value_sha256": Base.digest({"value": observed}),
            }
        )
    return {
        "experiment_id": EXPERIMENT_ID,
        "evaluator_version": EVALUATOR_VERSION,
        "phase": "QUALITY_BLIND_VALIDATE_SHARD",
        "status": "C90_EXACT_ALGEBRA_VALIDATION_SHARD_PASSED",
        "source_commit": DAG.git_head(),
        "manifest_payload_sha256": Base.MANIFEST_PAYLOAD,
        "algebra": algebra,
        "selector_index_start": start,
        "selector_index_stop": stop,
        "selector_count": len(rows),
        "validation_set_sha256": Base.C90_VALIDATION_SET_SHA,
        "compiled_canonical_node_stream_sha256": item["receipt"]["canonical_node_stream_sha256"],
        "rows": rows,
        "rows_sha256": Base.digest(rows),
        "quality_exposed": False,
    }


def aggregate(
    compiled_paths: list[Path],
    validation_paths: list[Path],
    combined_output: Path,
) -> dict[str, Any]:
    context = Base.load_c90_context()
    coordinates = Base.frozen_validation_coordinates()
    compiled_items: dict[str, dict[str, Any]] = {}
    for path in compiled_paths:
        item = load_algebra(path, context)
        algebra = item["algebra"]
        if algebra in compiled_items:
            raise ValueError(f"duplicate compiled algebra: {algebra}")
        compiled_items[algebra] = item
    if set(compiled_items) != set(DAG.ALGEBRAS):
        raise ValueError(f"incomplete compiled algebra set: {sorted(compiled_items)}")

    validation_rows: dict[str, dict[int, dict[str, Any]]] = {
        algebra: {} for algebra in DAG.ALGEBRAS
    }
    shard_receipts: list[dict[str, Any]] = []
    for path in validation_paths:
        receipt = load_json(path)
        if receipt.get("status") != "C90_EXACT_ALGEBRA_VALIDATION_SHARD_PASSED":
            raise ValueError("nonpassing validation shard supplied")
        if receipt.get("source_commit") != DAG.git_head():
            raise ValueError("validation shard is not bound to current HEAD")
        if receipt.get("manifest_payload_sha256") != Base.MANIFEST_PAYLOAD:
            raise ValueError("validation shard manifest drift")
        if receipt.get("validation_set_sha256") != Base.C90_VALIDATION_SET_SHA:
            raise ValueError("validation shard selector-set drift")
        if receipt.get("quality_exposed") is not False:
            raise ValueError("validation shard exposed C90 quality")
        algebra = receipt.get("algebra")
        if algebra not in DAG.ALGEBRAS:
            raise ValueError("validation shard algebra drift")
        expected_identity = compiled_items[algebra]["receipt"]["canonical_node_stream_sha256"]
        if receipt.get("compiled_canonical_node_stream_sha256") != expected_identity:
            raise ValueError("validation shard compiled identity drift")
        if receipt.get("rows_sha256") != Base.digest(receipt.get("rows", [])):
            raise ValueError("validation shard rows digest drift")
        for row in receipt.get("rows", []):
            index = int(row["selector_index"])
            if not (0 <= index < len(coordinates)):
                raise ValueError("validation shard selector index overflow")
            if int(row["selector_coordinate"]) != coordinates[index]:
                raise ValueError("validation shard selector coordinate drift")
            if index in validation_rows[algebra]:
                raise ValueError(f"duplicate validation selector: {algebra}:{index}")
            validation_rows[algebra][index] = row
        shard_receipts.append(
            {
                "algebra": algebra,
                "selector_index_start": receipt["selector_index_start"],
                "selector_index_stop": receipt["selector_index_stop"],
                "rows_sha256": receipt["rows_sha256"],
            }
        )

    canonical_rows: dict[str, list[dict[str, Any]]] = {}
    for algebra in DAG.ALGEBRAS:
        observed_indices = sorted(validation_rows[algebra])
        if observed_indices != list(range(len(coordinates))):
            missing = sorted(set(range(len(coordinates))) - set(observed_indices))
            raise ValueError(
                f"incomplete exact validation coverage for {algebra}: missing={missing[:10]} count={len(missing)}"
            )
        canonical_rows[algebra] = [validation_rows[algebra][i] for i in observed_indices]

    compiled = DAG.CompiledC90(context, compiled_items)
    DAG.save_compiled(compiled, combined_output)
    receipts = compiled.receipts()
    semantic_validation = {
        "status": "C90_EXACT_SEMANTIC_VALIDATION_PASSED",
        "selector_count": len(coordinates),
        "validation_set_sha256": Base.digest(coordinates),
        "per_algebra_rows_sha256": {
            algebra: Base.digest(canonical_rows[algebra]) for algebra in DAG.ALGEBRAS
        },
        "validation_outputs_sha256": Base.digest(canonical_rows),
        "shard_receipts_sha256": Base.digest(
            sorted(
                shard_receipts,
                key=lambda row: (
                    row["algebra"],
                    row["selector_index_start"],
                    row["selector_index_stop"],
                ),
            )
        ),
        "quality_exposed": False,
    }
    preflight = Execute.preflight()
    return {
        "experiment_id": EXPERIMENT_ID,
        "evaluator_version": EVALUATOR_VERSION,
        "status": "C90_EXACT_IMPLEMENTATION_QUALITY_BLIND_VALIDATED",
        "source_commit": DAG.git_head(),
        "manifest_payload_sha256": Base.MANIFEST_PAYLOAD,
        "preflight_payload_sha256": Base.digest(preflight),
        "compiled": receipts,
        "canonical_node_stream_sha256": {
            algebra: receipts[algebra]["canonical_node_stream_sha256"]
            for algebra in DAG.ALGEBRAS
        },
        "execution_topology": {
            "compile": "one_frozen_algebra_per_job",
            "validation": "frozen_307_selector_set_partitioned_by_predeclared_index_ranges",
            "scientific_semantics_changed": False,
        },
        "semantic_validation": semantic_validation,
        "quality_exposed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("compile-algebra")
    p.add_argument("--algebra", required=True, choices=DAG.ALGEBRAS)
    p.add_argument("--compiled-output", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)

    p = sub.add_parser("validate-shard")
    p.add_argument("--algebra", required=True, choices=DAG.ALGEBRAS)
    p.add_argument("--compiled", type=Path, required=True)
    p.add_argument("--start", type=int, required=True)
    p.add_argument("--stop", type=int, required=True)
    p.add_argument("--output", type=Path, required=True)

    p = sub.add_parser("aggregate")
    p.add_argument("--compiled", type=Path, action="append", required=True)
    p.add_argument("--validation", type=Path, action="append", required=True)
    p.add_argument("--combined-output", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "compile-algebra":
        result = compile_one(args.algebra, args.compiled_output)
    elif args.command == "validate-shard":
        result = validate_shard(args.algebra, args.compiled, args.start, args.stop)
    else:
        result = aggregate(args.compiled, args.validation, args.combined_output)
    result["payload_sha256"] = Base.digest(result)
    write_json(args.output, result)
    print(json.dumps({"status": result["status"], "payload_sha256": result["payload_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
