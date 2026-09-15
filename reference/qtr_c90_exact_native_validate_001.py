#!/usr/bin/env python3
"""Quality-blind semantic validation for compact-native C90 DAG artifacts.

For a predeclared frozen selector index range, this driver evaluates the compact
native semantic DAG and independently contracts the protected C90 factor graph
through qtr_c90_exact_dag_001.direct_contract_selector. It compares exact
values only. It never receives injected errors or decoder success outcomes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import qtr_c90_exact_decoder_001 as Base
import qtr_c90_exact_dag_001 as DAG

EXPERIMENT_ID = Base.EXPERIMENT_ID
EVALUATOR_VERSION = "0.1.0"
COMPILED_HEAD = "c4e1d757bdf89fa5eceaf2e38b8a34ff3ee3a78c"
ALGEBRA_IDS = {
    "sum_product_bsc_p_0_1": 0,
    "soft_tropical_base_2": 1,
    "min_plus_hamming": 2,
}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    unsigned = dict(payload)
    payload = dict(payload)
    payload["payload_sha256"] = Base.digest(unsigned)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_receipt(path: Path, algebra: str) -> dict[str, Any]:
    receipt = json.loads(path.read_text(encoding="utf-8"))
    if receipt.get("experiment_id") != EXPERIMENT_ID:
        raise ValueError("compiled artifact experiment identity drift")
    if receipt.get("source_commit") != COMPILED_HEAD:
        raise ValueError("compiled artifact source head drift")
    if receipt.get("manifest_payload_sha256") != Base.MANIFEST_PAYLOAD:
        raise ValueError("compiled artifact manifest drift")
    if receipt.get("algebra") != algebra:
        raise ValueError("compiled artifact algebra drift")
    if receipt.get("status") != "C90_EXACT_ALGEBRA_COMPILED_QUALITY_BLIND":
        raise ValueError("compiled artifact status drift")
    if receipt.get("quality_exposed") is not False:
        raise ValueError("compiled artifact quality boundary drift")
    compiled = receipt.get("compiled")
    if not isinstance(compiled, dict):
        raise ValueError("compiled artifact receipt missing")
    if compiled.get("backend") != "EXACT_COMPACT_NATIVE_HASH_CONS":
        raise ValueError("compiled artifact backend drift")
    if compiled.get("representation") != DAG.REPRESENTATION:
        raise ValueError("compiled artifact representation drift")
    if compiled.get("temporary_stabilizer_nodes_final") != 0:
        raise ValueError("compiled artifact retains temporary stabilizer nodes")
    return receipt


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(8 << 20)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _parse_native_value(algebra: str, row: dict[str, Any]) -> Any:
    if row.get("algebra_id") != ALGEBRA_IDS[algebra]:
        raise ValueError("native evaluator algebra id drift")
    if row.get("quality_exposed") is not False:
        raise ValueError("native evaluator quality boundary drift")
    if algebra != "min_plus_hamming":
        return int(row["value_hex"], 16)
    return (
        (int(row["minimum_weight"]), int(row["minimum_representative_hex"], 16)),
        int(row["canonical_hex"], 16),
    )


def validate_shard(
    *,
    algebra: str,
    native_executable: Path,
    native_binary: Path,
    compiled_receipt_path: Path,
    start: int,
    stop: int,
    output: Path,
) -> dict[str, Any]:
    if algebra not in DAG.ALGEBRAS:
        raise ValueError(algebra)
    coordinates = Base.frozen_validation_coordinates()
    if Base.digest(coordinates) != Base.C90_VALIDATION_SET_SHA:
        raise AssertionError("frozen validation selector set digest drift")
    if not (0 <= start < stop <= len(coordinates)):
        raise ValueError("invalid validation selector shard bounds")

    compiled_receipt = _load_receipt(compiled_receipt_path, algebra)
    compiled = compiled_receipt["compiled"]
    if native_binary.stat().st_size != int(compiled["native_binary_bytes"]):
        raise ValueError("native binary size drift")
    observed_binary_sha = _file_sha256(native_binary)
    if observed_binary_sha != compiled["native_binary_sha256"]:
        raise ValueError("native binary sha256 drift")

    selector_file = output.with_suffix(".selectors.txt")
    selector_file.parent.mkdir(parents=True, exist_ok=True)
    selector_file.write_text(
        "".join(f"{index} {coordinates[index]}\n" for index in range(start, stop)),
        encoding="utf-8",
    )
    completed = subprocess.run(
        [
            str(native_executable),
            "--native",
            str(native_binary),
            "--selectors",
            str(selector_file),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    native_rows = [json.loads(line) for line in completed.stdout.splitlines() if line.strip()]
    if len(native_rows) != stop - start:
        raise AssertionError("native evaluator selector count drift")

    context = Base.load_c90_context()
    rows: list[dict[str, Any]] = []
    for expected_index, native_row in zip(range(start, stop), native_rows):
        coordinate = coordinates[expected_index]
        if native_row.get("status") != "C90_COMPACT_NATIVE_SELECTOR_EVALUATED":
            raise AssertionError("native evaluator status drift")
        if native_row.get("selector_index") != expected_index:
            raise AssertionError("native evaluator selector index drift")
        if native_row.get("selector_coordinate") != coordinate:
            raise AssertionError("native evaluator selector coordinate drift")
        observed = _parse_native_value(algebra, native_row)
        expected = DAG.direct_contract_selector(context, algebra, coordinate)
        if observed != expected:
            raise AssertionError(
                f"C90 exact semantic mismatch: {algebra} selector_index={expected_index} coordinate={coordinate}"
            )
        rows.append(
            {
                "selector_index": expected_index,
                "selector_coordinate": coordinate,
                "value_sha256": Base.digest({"value": observed}),
                "reachable_nodes": int(native_row["reachable_nodes"]),
                "peak_live_values": int(native_row["peak_live_values"]),
            }
        )

    report = {
        "experiment_id": EXPERIMENT_ID,
        "evaluator_version": EVALUATOR_VERSION,
        "phase": "QUALITY_BLIND_NATIVE_VALIDATE_SHARD",
        "status": "C90_EXACT_ALGEBRA_VALIDATION_SHARD_PASSED",
        "validation_subject_commit": DAG.git_head(),
        "compiled_source_commit": COMPILED_HEAD,
        "manifest_payload_sha256": Base.MANIFEST_PAYLOAD,
        "representation": DAG.REPRESENTATION,
        "algebra": algebra,
        "selector_index_start": start,
        "selector_index_stop": stop,
        "selector_count": len(rows),
        "validation_set_sha256": Base.C90_VALIDATION_SET_SHA,
        "compiled_canonical_node_stream_sha256": compiled["canonical_node_stream_sha256"],
        "compiled_native_binary_sha256": compiled["native_binary_sha256"],
        "rows": rows,
        "rows_sha256": Base.digest(rows),
        "all_exact_equal": True,
        "quality_exposed": False,
        "injected_error_success_used": False,
    }
    _write_json(output, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--algebra", choices=DAG.ALGEBRAS, required=True)
    parser.add_argument("--native-executable", type=Path, required=True)
    parser.add_argument("--native-binary", type=Path, required=True)
    parser.add_argument("--compiled-receipt", type=Path, required=True)
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--stop", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = validate_shard(
        algebra=args.algebra,
        native_executable=args.native_executable,
        native_binary=args.native_binary,
        compiled_receipt_path=args.compiled_receipt,
        start=args.start,
        stop=args.stop,
        output=args.output,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "algebra": report["algebra"],
                "selector_index_start": report["selector_index_start"],
                "selector_index_stop": report["selector_index_stop"],
                "rows_sha256": report["rows_sha256"],
                "quality_exposed": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
