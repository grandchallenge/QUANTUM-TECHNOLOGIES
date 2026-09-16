#!/usr/bin/env python3
"""Aggregate same-head frozen-307 exact semantic validation for QTR-C90."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import qtr_c90_exact_decoder_001 as Base
import qtr_c90_exact_dense_batch_validate_001 as Batch
import qtr_c90_exact_dense_oracle_001 as Dense

EXPERIMENT_ID = Base.EXPERIMENT_ID


def _verify_payload(payload: dict[str, Any]) -> None:
    unsigned = dict(payload)
    observed = unsigned.pop("payload_sha256", None)
    if observed is None or Base.digest(unsigned) != observed:
        raise ValueError("validation shard payload digest drift")


def aggregate_reports(reports: Iterable[dict[str, Any]], *, subject_sha: str) -> dict[str, Any]:
    payloads = list(reports)
    expected_total = len(Dense.ALGEBRA_IDS) * Batch.SHARD_COUNT
    if len(payloads) != expected_total:
        raise ValueError(f"expected {expected_total} validation shards, got {len(payloads)}")
    coords = [int(v) for v in Base.frozen_validation_coordinates()]
    if len(coords) != 307 or Base.digest(coords) != Base.C90_VALIDATION_SET_SHA:
        raise AssertionError("frozen selector set drift")

    grouped: dict[str, dict[int, dict[str, Any]]] = {algebra: {} for algebra in Dense.ALGEBRA_IDS}
    for report in payloads:
        _verify_payload(report)
        if report.get("status") != "C90_EXACT_DENSE_VALIDATION_SHARD_PASSED":
            raise ValueError("validation shard status drift")
        if report.get("validation_subject_commit") != subject_sha:
            raise ValueError("validation subject mismatch")
        if report.get("compiled_source_commit") != subject_sha:
            raise ValueError("compile/validation exact-head mismatch")
        if report.get("quality_exposed") is not False:
            raise ValueError("validation shard quality boundary drift")
        if report.get("injected_error_success_used") is not False:
            raise ValueError("validation shard injected-error boundary drift")
        if report.get("decoder_execution_performed") is not False:
            raise ValueError("validation shard decoder-execution boundary drift")
        if report.get("scientific_semantics_changed") is not False:
            raise ValueError("validation shard semantics drift")
        if report.get("validation_set_sha256") != Base.C90_VALIDATION_SET_SHA:
            raise ValueError("validation-set digest drift")
        algebra = str(report.get("algebra"))
        if algebra not in grouped:
            raise ValueError("unknown validation algebra")
        shard = int(report.get("shard_index", -1))
        if shard in grouped[algebra]:
            raise ValueError("duplicate validation shard")
        grouped[algebra][shard] = report

    compile_identities: dict[str, dict[str, Any]] = {}
    total_comparisons = 0
    for algebra in Dense.ALGEBRA_IDS:
        shards = grouped[algebra]
        if sorted(shards) != list(range(Batch.SHARD_COUNT)):
            raise ValueError(f"incomplete shard coverage for {algebra}")
        canonical_values: set[str] = set()
        binary_values: set[str] = set()
        receipt_values: set[str] = set()
        observed_indices: list[int] = []
        observed_coords: list[int] = []
        for shard_index in range(Batch.SHARD_COUNT):
            report = shards[shard_index]
            start, stop = Batch.shard_bounds(shard_index, len(coords))
            expected_indices = list(range(start, stop))
            expected_coords = coords[start:stop]
            if report.get("selector_indices") != expected_indices:
                raise ValueError("validation shard index partition drift")
            if report.get("selector_coordinates") != expected_coords:
                raise ValueError("validation shard coordinate partition drift")
            results = report.get("results")
            if not isinstance(results, list) or len(results) != len(expected_indices):
                raise ValueError("validation shard result-count drift")
            if int(report.get("exact_equal_count", -1)) != len(results):
                raise ValueError("validation shard exact-equality count drift")
            for expected_index, expected_coordinate, result in zip(
                expected_indices, expected_coords, results, strict=True
            ):
                if int(result.get("selector_index", -1)) != expected_index:
                    raise ValueError("validation result selector-index drift")
                if int(result.get("selector_coordinate", -1)) != expected_coordinate:
                    raise ValueError("validation result selector-coordinate drift")
                if result.get("exact_equal") is not True:
                    raise ValueError("dense/native exact semantic mismatch")
            canonical_values.add(str(report["canonical_node_stream_sha256"]))
            binary_values.add(str(report["native_binary_sha256"]))
            receipt_values.add(str(report["compile_receipt_payload_sha256"]))
            observed_indices.extend(expected_indices)
            observed_coords.extend(expected_coords)
            total_comparisons += len(results)

        if observed_indices != list(range(len(coords))) or observed_coords != coords:
            raise ValueError(f"frozen selector coverage drift for {algebra}")
        if canonical_values != {Batch.EXPECTED_CANONICAL_STREAMS[algebra]}:
            raise ValueError(f"canonical node-stream identity drift for {algebra}")
        if len(binary_values) != 1 or len(receipt_values) != 1:
            raise ValueError(f"compile artifact identity drift across shards for {algebra}")
        compile_identities[algebra] = {
            "canonical_node_stream_sha256": next(iter(canonical_values)),
            "native_binary_sha256": next(iter(binary_values)),
            "compile_receipt_payload_sha256": next(iter(receipt_values)),
            "compiled_source_commit": subject_sha,
        }

    if total_comparisons != len(coords) * len(Dense.ALGEBRA_IDS):
        raise ValueError("full validation comparison count drift")

    output: dict[str, Any] = {
        "experiment_id": EXPERIMENT_ID,
        "phase": "QUALITY_BLIND_FROZEN_307_THREE_ALGEBRA_SEMANTIC_VALIDATION",
        "status": "C90_EXACT_IMPLEMENTATION_QUALITY_BLIND_VALIDATED",
        "semantic_validation_status": "C90_EXACT_SEMANTIC_VALIDATION_PASSED",
        "validation_subject_commit": subject_sha,
        "compiled_source_commit": subject_sha,
        "representation": "EXACT_SELECTOR_PARAMETRIC_HASH_CONSED_DAG_C90",
        "compile_identities": compile_identities,
        "dense_backend": Dense.BACKEND,
        "validation_set_sha256": Base.C90_VALIDATION_SET_SHA,
        "frozen_selector_count": len(coords),
        "algebra_count": len(Dense.ALGEBRA_IDS),
        "exact_comparison_count": total_comparisons,
        "expected_exact_comparison_count": 921,
        "shard_size": Batch.SHARD_SIZE,
        "shards_per_algebra": Batch.SHARD_COUNT,
        "same_head_compile_and_validation": True,
        "canonical_compile_identity_reproduced": True,
        "quality_exposed": False,
        "injected_error_success_used": False,
        "decoder_execution_performed": False,
        "scientific_semantics_changed": False,
        "activation_eligible": True,
    }
    output["payload_sha256"] = Base.digest(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--subject-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = sorted(args.input_dir.rglob("*.json"))
    reports = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    output = aggregate_reports(reports, subject_sha=args.subject_sha)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": output["status"],
                "semantic_validation_status": output["semantic_validation_status"],
                "validation_subject_commit": output["validation_subject_commit"],
                "exact_comparison_count": output["exact_comparison_count"],
                "activation_eligible": output["activation_eligible"],
                "payload_sha256": output["payload_sha256"],
                "quality_exposed": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
