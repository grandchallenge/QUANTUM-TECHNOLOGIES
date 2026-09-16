#!/usr/bin/env python3
"""Quality-blind frozen-selector semantic validation for QTR-C90.

This driver compares the exact compact-native DAG evaluator against the
independent fixed-selector dense oracle on a bounded shard of the predeclared
307-selector validation set. It receives no injected error and cannot score
C90 decoder quality.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import qtr_c90_exact_compact_native_001 as Compile
import qtr_c90_exact_decoder_001 as Base
import qtr_c90_exact_dense_oracle_001 as Dense

EXPERIMENT_ID = Base.EXPERIMENT_ID
SHARD_SIZE = 4
SHARD_COUNT = 77
EXPECTED_CANONICAL_STREAMS = {
    "sum_product_bsc_p_0_1": "e6d34ddfdadb19af9bda02c36997a8c2dd767f4610b178f4cf3d74407445ebb4",
    "soft_tropical_base_2": "4d8859535f7a3ce814eb6ea459a80870fd645f57af487e5b8a9f99de3d5dccb0",
    "min_plus_hamming": "3aa3f0c1d97f7428623a034b6baa20e9c7f113e830b715040dc9e1e62967b4e8",
}


def shard_bounds(shard_index: int, total: int = 307, shard_size: int = SHARD_SIZE) -> tuple[int, int]:
    if shard_index < 0:
        raise ValueError("negative shard index")
    start = shard_index * shard_size
    stop = min(total, start + shard_size)
    if start >= total:
        raise ValueError("shard index outside frozen validation set")
    return start, stop


def _verify_payload(payload: dict[str, Any]) -> None:
    unsigned = dict(payload)
    observed = unsigned.pop("payload_sha256", None)
    if observed is None or Base.digest(unsigned) != observed:
        raise ValueError("payload digest drift")


def _load_compile_receipt(path: Path, *, algebra: str, subject_sha: str, binary: Path) -> dict[str, Any]:
    receipt = json.loads(path.read_text(encoding="utf-8"))
    _verify_payload(receipt)
    if receipt.get("status") != "C90_EXACT_ALGEBRA_COMPILED_QUALITY_BLIND":
        raise ValueError("compile receipt status drift")
    if receipt.get("source_commit") != subject_sha:
        raise ValueError("compile/validation head mismatch")
    if receipt.get("algebra") != algebra:
        raise ValueError("compile receipt algebra drift")
    if receipt.get("quality_exposed") is not False:
        raise ValueError("compile receipt quality boundary drift")
    if receipt.get("selector_enumeration_performed") is not False:
        raise ValueError("compile receipt selector-enumeration drift")
    compiled = receipt.get("compiled", {})
    if compiled.get("backend") != "EXACT_COMPACT_NATIVE_HASH_CONS":
        raise ValueError("compile backend drift")
    if compiled.get("canonical_node_stream_sha256") != EXPECTED_CANONICAL_STREAMS[algebra]:
        raise ValueError("canonical node-stream digest drift")
    if compiled.get("native_binary_sha256") != Compile.file_sha256(binary):
        raise ValueError("compiled native binary digest drift")
    return receipt


def _native_rows(
    *,
    executable: Path,
    binary: Path,
    selector_file: Path,
    expected_count: int,
) -> list[dict[str, Any]]:
    completed = subprocess.run(
        [str(executable), "--native", str(binary), "--selectors", str(selector_file)],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    )
    rows = [json.loads(line) for line in completed.stdout.splitlines() if line.strip()]
    if len(rows) != expected_count:
        raise AssertionError("native evaluator row-count drift")
    return rows


def validate_shard(
    *,
    algebra: str,
    shard_index: int,
    subject_sha: str,
    native_executable: Path,
    native_binary: Path,
    compile_receipt: Path,
    dense_executable: Path,
    output: Path,
) -> dict[str, Any]:
    if algebra not in Dense.ALGEBRA_IDS:
        raise ValueError(algebra)
    coords = [int(v) for v in Base.frozen_validation_coordinates()]
    if len(coords) != 307 or Base.digest(coords) != Base.C90_VALIDATION_SET_SHA:
        raise AssertionError("frozen selector set drift")
    start, stop = shard_bounds(shard_index, len(coords))
    selected = list(enumerate(coords[start:stop], start=start))

    receipt = _load_compile_receipt(
        compile_receipt,
        algebra=algebra,
        subject_sha=subject_sha,
        binary=native_binary,
    )
    selector_file = output.with_suffix(".selectors.txt")
    selector_file.parent.mkdir(parents=True, exist_ok=True)
    selector_file.write_text(
        "".join(f"{index} {coordinate}\n" for index, coordinate in selected),
        encoding="utf-8",
    )
    native_rows = _native_rows(
        executable=native_executable,
        binary=native_binary,
        selector_file=selector_file,
        expected_count=len(selected),
    )

    context = Base.load_c90_context()
    code = context["code"]
    order = [int(v) for v in context["order"]]
    selector_basis = [int(v) for v in code["selector_basis_qubits"]]
    scopes = [tuple(int(v) for v in scope) for scope in code["scopes"]]

    results: list[dict[str, Any]] = []
    for (expected_index, expected_coordinate), native in zip(selected, native_rows, strict=True):
        if native.get("status") != "C90_COMPACT_NATIVE_SELECTOR_EVALUATED":
            raise AssertionError("native evaluator status drift")
        if int(native.get("selector_index", -1)) != expected_index:
            raise AssertionError("native selector-index drift")
        if int(native.get("selector_coordinate", -1)) != expected_coordinate:
            raise AssertionError("native selector-coordinate drift")
        if native.get("algebra_id") != Dense.ALGEBRA_IDS[algebra]:
            raise AssertionError("native algebra identity drift")
        if native.get("quality_exposed") is not False:
            raise AssertionError("native evaluator crossed quality boundary")

        oracle = Dense.run_raw(
            executable=dense_executable,
            algebra=algebra,
            coordinate=expected_coordinate,
            order=order,
            selector_basis=selector_basis,
            scopes=scopes,
        )
        native_encoding = Dense._require_exact_native_equality(algebra, oracle, native)
        results.append(
            {
                "selector_index": expected_index,
                "selector_coordinate": expected_coordinate,
                "native_value_sha256": Base.digest(native_encoding),
                "dense_certificate_sha256": Base.digest(oracle),
                "exact_equal": True,
                "native_reachable_nodes": int(native["reachable_nodes"]),
                "native_peak_live_values": int(native["peak_live_values"]),
            }
        )

    compiled = receipt["compiled"]
    report: dict[str, Any] = {
        "experiment_id": EXPERIMENT_ID,
        "phase": "QUALITY_BLIND_FROZEN_307_DENSE_SEMANTIC_VALIDATION_SHARD",
        "status": "C90_EXACT_DENSE_VALIDATION_SHARD_PASSED",
        "validation_subject_commit": subject_sha,
        "compiled_source_commit": receipt["source_commit"],
        "algebra": algebra,
        "algebra_id": Dense.ALGEBRA_IDS[algebra],
        "compile_receipt_payload_sha256": receipt["payload_sha256"],
        "canonical_node_stream_sha256": compiled["canonical_node_stream_sha256"],
        "native_binary_sha256": compiled["native_binary_sha256"],
        "reachable_nodes": int(compiled["reachable_nodes"]),
        "dense_backend": Dense.BACKEND,
        "validation_set_sha256": Base.C90_VALIDATION_SET_SHA,
        "frozen_selector_count": len(coords),
        "shard_size": SHARD_SIZE,
        "shard_count": SHARD_COUNT,
        "shard_index": shard_index,
        "start_index": start,
        "stop_index_exclusive": stop,
        "selector_indices": [index for index, _ in selected],
        "selector_coordinates": [coordinate for _, coordinate in selected],
        "results": results,
        "exact_equal_count": len(results),
        "quality_exposed": False,
        "injected_error_success_used": False,
        "decoder_execution_performed": False,
        "scientific_semantics_changed": False,
    }
    report["payload_sha256"] = Base.digest(report)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--algebra", choices=tuple(Dense.ALGEBRA_IDS), required=True)
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--subject-sha", required=True)
    parser.add_argument("--native-executable", type=Path, required=True)
    parser.add_argument("--native-binary", type=Path, required=True)
    parser.add_argument("--compile-receipt", type=Path, required=True)
    parser.add_argument("--dense-executable", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = validate_shard(
        algebra=args.algebra,
        shard_index=args.shard_index,
        subject_sha=args.subject_sha,
        native_executable=args.native_executable,
        native_binary=args.native_binary,
        compile_receipt=args.compile_receipt,
        dense_executable=args.dense_executable,
        output=args.output,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "algebra": report["algebra"],
                "shard_index": report["shard_index"],
                "selector_count": len(report["results"]),
                "exact_equal_count": report["exact_equal_count"],
                "payload_sha256": report["payload_sha256"],
                "quality_exposed": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
