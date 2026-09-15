#!/usr/bin/env python3
"""Aggregate complete quality-blind compact-native C90 semantic validation."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import qtr_c90_exact_decoder_001 as Base
import qtr_c90_exact_dag_001 as DAG

EXPERIMENT_ID = Base.EXPERIMENT_ID
COMPILED_HEAD = "c4e1d757bdf89fa5eceaf2e38b8a34ff3ee3a78c"
EXPECTED_CANONICAL = {
    "sum_product_bsc_p_0_1": "e6d34ddfdadb19af9bda02c36997a8c2dd767f4610b178f4cf3d74407445ebb4",
    "soft_tropical_base_2": "4d8859535f7a3ce814eb6ea459a80870fd645f57af487e5b8a9f99de3d5dccb0",
    "min_plus_hamming": "3aa3f0c1d97f7428623a034b6baa20e9c7f113e830b715040dc9e1e62967b4e8",
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, payload: dict[str, Any]) -> None:
    unsigned = dict(payload)
    payload = dict(payload)
    payload["payload_sha256"] = Base.digest(unsigned)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def aggregate(paths: list[Path], output: Path) -> dict[str, Any]:
    if len(paths) != 24:
        raise ValueError(f"expected 24 validation shards, got {len(paths)}")
    coordinates = Base.frozen_validation_coordinates()
    if len(coordinates) != 307 or Base.digest(coordinates) != Base.C90_VALIDATION_SET_SHA:
        raise AssertionError("frozen validation coordinate set drift")

    by_algebra: dict[str, list[dict[str, Any]]] = {algebra: [] for algebra in DAG.ALGEBRAS}
    validation_subjects: set[str] = set()
    native_binary_sha: dict[str, set[str]] = {algebra: set() for algebra in DAG.ALGEBRAS}
    canonical_sha: dict[str, set[str]] = {algebra: set() for algebra in DAG.ALGEBRAS}

    for path in paths:
        shard = load(path)
        algebra = shard.get("algebra")
        if algebra not in by_algebra:
            raise ValueError(f"unexpected validation algebra: {algebra}")
        if shard.get("experiment_id") != EXPERIMENT_ID:
            raise ValueError("validation experiment identity drift")
        if shard.get("status") != "C90_EXACT_ALGEBRA_VALIDATION_SHARD_PASSED":
            raise ValueError("validation shard did not pass")
        if shard.get("compiled_source_commit") != COMPILED_HEAD:
            raise ValueError("compiled source commit drift")
        if shard.get("manifest_payload_sha256") != Base.MANIFEST_PAYLOAD:
            raise ValueError("validation manifest drift")
        if shard.get("representation") != DAG.REPRESENTATION:
            raise ValueError("validation representation drift")
        if shard.get("validation_set_sha256") != Base.C90_VALIDATION_SET_SHA:
            raise ValueError("validation selector-set drift")
        if shard.get("all_exact_equal") is not True:
            raise ValueError("validation shard exact equality not certified")
        if shard.get("quality_exposed") is not False:
            raise ValueError("validation shard exposed quality")
        if shard.get("injected_error_success_used") is not False:
            raise ValueError("validation shard used injected-error success")
        validation_subjects.add(str(shard.get("validation_subject_commit")))
        native_binary_sha[algebra].add(str(shard.get("compiled_native_binary_sha256")))
        canonical_sha[algebra].add(str(shard.get("compiled_canonical_node_stream_sha256")))
        by_algebra[algebra].append(shard)

    if len(validation_subjects) != 1:
        raise ValueError(f"validation subject head drift across shards: {validation_subjects}")

    algebra_receipts: dict[str, Any] = {}
    all_rows_digest_input: list[dict[str, Any]] = []
    for algebra in DAG.ALGEBRAS:
        shards = sorted(by_algebra[algebra], key=lambda item: int(item["selector_index_start"]))
        if len(shards) != 8:
            raise ValueError(f"expected 8 shards for {algebra}, got {len(shards)}")
        if canonical_sha[algebra] != {EXPECTED_CANONICAL[algebra]}:
            raise ValueError(f"compiled canonical SHA drift for {algebra}: {canonical_sha[algebra]}")
        if len(native_binary_sha[algebra]) != 1:
            raise ValueError(f"compiled native binary SHA drift for {algebra}")
        rows: list[dict[str, Any]] = []
        expected_start = 0
        shard_receipts: list[dict[str, Any]] = []
        for shard in shards:
            start = int(shard["selector_index_start"])
            stop = int(shard["selector_index_stop"])
            if start != expected_start or not start < stop <= 307:
                raise ValueError(f"selector shard coverage drift for {algebra}: {start}:{stop}")
            shard_rows = list(shard["rows"])
            if len(shard_rows) != stop - start:
                raise ValueError(f"selector shard row count drift for {algebra}: {start}:{stop}")
            for offset, row in enumerate(shard_rows):
                index = start + offset
                if int(row["selector_index"]) != index:
                    raise ValueError(f"selector row index drift for {algebra}:{index}")
                if int(row["selector_coordinate"]) != coordinates[index]:
                    raise ValueError(f"selector row coordinate drift for {algebra}:{index}")
            rows.extend(shard_rows)
            shard_receipts.append(
                {
                    "start": start,
                    "stop": stop,
                    "rows_sha256": shard["rows_sha256"],
                    "payload_sha256": shard["payload_sha256"],
                }
            )
            expected_start = stop
        if expected_start != 307 or len(rows) != 307:
            raise ValueError(f"incomplete selector coverage for {algebra}")
        rows_sha = Base.digest(rows)
        algebra_receipts[algebra] = {
            "selector_count": 307,
            "canonical_node_stream_sha256": EXPECTED_CANONICAL[algebra],
            "native_binary_sha256": next(iter(native_binary_sha[algebra])),
            "rows_sha256": rows_sha,
            "shards": shard_receipts,
        }
        all_rows_digest_input.append({"algebra": algebra, "rows_sha256": rows_sha})

    validation_subject = next(iter(validation_subjects))
    report = {
        "experiment_id": EXPERIMENT_ID,
        "phase": "QUALITY_BLIND_NATIVE_SEMANTIC_VALIDATION_AGGREGATE",
        "status": "C90_EXACT_IMPLEMENTATION_QUALITY_BLIND_VALIDATED",
        "semantic_validation": {
            "status": "C90_EXACT_SEMANTIC_VALIDATION_PASSED",
            "selector_count_per_algebra": 307,
            "algebra_count": 3,
            "validation_set_sha256": Base.C90_VALIDATION_SET_SHA,
            "all_exact_equal": True,
            "validation_outputs_sha256": Base.digest(all_rows_digest_input),
            "quality_exposed": False,
        },
        "compiled_source_commit": COMPILED_HEAD,
        "validation_subject_commit": validation_subject,
        "manifest_payload_sha256": Base.MANIFEST_PAYLOAD,
        "representation": DAG.REPRESENTATION,
        "algebras": algebra_receipts,
        "quality_exposed": False,
        "injected_error_success_used": False,
        "activation_eligible": False,
        "activation_blocker": "compiled artifact head differs from validation-tooling head; recompute compile+validation on final immutable execution head",
    }
    write(output, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validation", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = aggregate(args.validation, args.output)
    print(
        json.dumps(
            {
                "status": report["status"],
                "semantic_status": report["semantic_validation"]["status"],
                "validation_outputs_sha256": report["semantic_validation"]["validation_outputs_sha256"],
                "quality_exposed": False,
                "activation_eligible": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
