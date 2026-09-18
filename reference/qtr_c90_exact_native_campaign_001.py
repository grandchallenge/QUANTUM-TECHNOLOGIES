#!/usr/bin/env python3
"""Activated exact native campaign adapter for QTR-C90-EXACT-DECODER-001.

This module does not change the frozen scientific semantics. It transports the
three validated native DAG outputs into the already-frozen C72 decision rule,
fixes all 347 corrections, and only in a later mode invokes the independently
frozen scoring / matched-comparison procedure.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import qtr_c90_exact_decoder_001 as Base
import qtr_c90_exact_dag_001 as DAG
import qtr_c90_exact_execute_001 as Execute
import tcm_c72_interface_001 as C72

ACTIVATION_HEAD = "0c1f5591a097adc285dec4cbfc320eeebd2c65d3"
VALIDATION_RUN_ID = 35084118529
VALIDATION_ARTIFACT_ID = 10443207511
VALIDATION_ARTIFACT_DIGEST = "sha256:b91dd81d795822bd0f889a32b44f01b716d5b7ae097d83be5f43de95c9964bf8"
VALIDATION_PAYLOAD_SHA256 = "3a46e8006a75bcd4eacdd421410da50809b71018b77a2dbbb930cfe44b4f80a0"
ACTIVATION_COMMENT_ID = 5737017921
LOGICAL_CLASSES = 256
INPUTS = 347
SELECTORS_PER_ALGEBRA = INPUTS * LOGICAL_CLASSES

ALGEBRA_IDS = {
    "sum_product_bsc_p_0_1": 0,
    "soft_tropical_base_2": 1,
    "min_plus_hamming": 2,
}

COMPILE_IDENTITIES = {
    "sum_product_bsc_p_0_1": {
        "artifact_id": 10442610733,
        "artifact_name": "QTR-C90-same-head-compile-sum_product_bsc_p_0_1",
        "artifact_digest": "sha256:678b39b09023f0adb854a9b0cc28ce0b85c9379e149b0103cfe94a7e4ad0fece",
        "canonical_node_stream_sha256": "e6d34ddfdadb19af9bda02c36997a8c2dd767f4610b178f4cf3d74407445ebb4",
        "compile_receipt_payload_sha256": "630854c30889537c0a248bc245f05286685b515d07743b4c2c811a30ce9f4642",
        "native_binary_sha256": "2efe52e17c6d66920b23738987818184657caf479c60c78712dff6db4a306bde",
    },
    "soft_tropical_base_2": {
        "artifact_id": 10442242798,
        "artifact_name": "QTR-C90-same-head-compile-soft_tropical_base_2",
        "artifact_digest": "sha256:c4fa41b35ad5e88e4e58ca9816c78dd296d170a5d86cf9087c51b4fdcce138e8",
        "canonical_node_stream_sha256": "4d8859535f7a3ce814eb6ea459a80870fd645f57af487e5b8a9f99de3d5dccb0",
        "compile_receipt_payload_sha256": "9bc3f78f7b501da1892d8b627cc70b6fa14292a1fec8dac1b722c401a7e114f4",
        "native_binary_sha256": "9647b3e7fb2ee7f6f87d7e3fe6ce6779bd756e100f86f3dc13e7dc5385b5df9a",
    },
    "min_plus_hamming": {
        "artifact_id": 10442143252,
        "artifact_name": "QTR-C90-same-head-compile-min_plus_hamming",
        "artifact_digest": "sha256:6b9c94bd62cd4b3818396bc2c48b66cfe63958d37ce8d5ab2b846d0fb701d38f",
        "canonical_node_stream_sha256": "3aa3f0c1d97f7428623a034b6baa20e9c7f113e830b715040dc9e1e62967b4e8",
        "compile_receipt_payload_sha256": "4a58ffb06bac564151c39f49416a9ca2d1b7b5de251fc2cb37046fab84af99f7",
        "native_binary_sha256": "dd58a7e0c59626032d8714827d9f1097a33a78fd426c7d972407b32340890bb0",
    },
}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    unsigned = dict(payload)
    payload = dict(payload)
    payload["payload_sha256"] = Base.digest(unsigned)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@lru_cache(maxsize=1)
def frozen_context() -> dict[str, Any]:
    return Base.load_c90_context()


@lru_cache(maxsize=1)
def frozen_corpus() -> tuple[dict[str, Any], ...]:
    rows = Base.c90_corpus_records()
    if len(rows) != INPUTS or Base.digest(rows) != Base.C90_CORPUS_SHA:
        raise AssertionError("frozen C90 corpus identity drift")
    if [int(row["index"]) for row in rows] != list(range(INPUTS)):
        raise AssertionError("frozen C90 corpus index drift")
    return tuple(rows)


def selector_metadata(logical_class: int) -> list[dict[str, int]]:
    if not 0 <= int(logical_class) < LOGICAL_CLASSES:
        raise ValueError("logical class outside frozen domain")
    logical_class = int(logical_class)
    context = frozen_context()
    result: list[dict[str, int]] = []
    for row in frozen_corpus():
        index = int(row["index"])
        error = Base.F2.b2i(row["error"])
        syndrome = Base.F2.syndrome(error, context["code"]["hz"])
        _, coordinate, functional = Base.selector_seed_for(
            context, syndrome, logical_class
        )
        expected_functional = (
            C72.independent_syndrome_from_full(
                syndrome, context["code"]["z_indices"]
            )
            | (logical_class << 41)
        )
        if functional != expected_functional:
            raise AssertionError("selector functional drift")
        result.append(
            {
                "global_index": index * LOGICAL_CLASSES + logical_class,
                "input_index": index,
                "logical_class": logical_class,
                "syndrome": int(syndrome),
                "coordinate": int(coordinate),
                "functional": int(functional),
            }
        )
    if len(result) != INPUTS:
        raise AssertionError("selector shard cardinality drift")
    return result


def write_selector_file(logical_class: int, output: Path) -> None:
    metadata = selector_metadata(logical_class)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(
            f"{row['global_index']} {row['coordinate']}\n"
            for row in metadata
        ),
        encoding="utf-8",
    )


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        raise ValueError(f"empty JSONL: {path}")
    return rows


def verify_native_rows(
    algebra: str,
    logical_class: int,
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if algebra not in ALGEBRA_IDS:
        raise ValueError(algebra)
    expected = {
        row["global_index"]: row for row in selector_metadata(logical_class)
    }
    if len(rows) != INPUTS:
        raise AssertionError("native shard row count drift")
    observed: dict[int, dict[str, Any]] = {}
    context = frozen_context()
    for row in rows:
        if row.get("status") != "C90_COMPACT_NATIVE_SELECTOR_EVALUATED":
            raise AssertionError("native evaluator status drift")
        if int(row.get("algebra_id", -1)) != ALGEBRA_IDS[algebra]:
            raise AssertionError("native algebra identity drift")
        if row.get("quality_exposed") is not False:
            raise AssertionError("native evaluator crossed quality boundary")
        global_index = int(row["selector_index"])
        if global_index in observed:
            raise AssertionError("duplicate native selector row")
        meta = expected.get(global_index)
        if meta is None:
            raise AssertionError("native selector index outside frozen shard")
        if int(row["selector_coordinate"]) != meta["coordinate"]:
            raise AssertionError("native selector coordinate drift")
        if algebra == "min_plus_hamming":
            weight = int(row["minimum_weight"])
            representative = int(row["minimum_representative_hex"], 16)
            canonical = int(row["canonical_hex"], 16)
            if not (0 <= weight <= 90):
                raise AssertionError("min-plus weight drift")
            if representative >= (1 << 90) or canonical >= (1 << 90):
                raise AssertionError("min-plus representative width drift")
            if C72.selector_functional_value(
                representative, context["selector_rows"]
            ) != meta["functional"]:
                raise AssertionError("min-plus representative leaves frozen class")
            if C72.selector_functional_value(
                canonical, context["selector_rows"]
            ) != meta["functional"]:
                raise AssertionError("min-plus canonical key leaves frozen class")
        else:
            value = int(row["value_hex"], 16)
            if value < 0:
                raise AssertionError("negative exact numeric score")
        observed[global_index] = row
    if set(observed) != set(expected):
        raise AssertionError("native shard coverage drift")
    return [observed[row["global_index"]] for row in selector_metadata(logical_class)]


def validate_shard(
    algebra: str,
    logical_class: int,
    rows_path: Path,
    output: Path,
) -> dict[str, Any]:
    rows = verify_native_rows(algebra, logical_class, load_jsonl(rows_path))
    identity = COMPILE_IDENTITIES[algebra]
    report: dict[str, Any] = {
        "experiment_id": Base.EXPERIMENT_ID,
        "phase": "ACTIVATED_EXACT_NATIVE_SELECTOR_SHARD",
        "status": "C90_ACTIVATED_SELECTOR_SHARD_EVALUATED",
        "activation_head": ACTIVATION_HEAD,
        "orchestration_head": DAG.git_head(),
        "validation_run_id": VALIDATION_RUN_ID,
        "validation_artifact_id": VALIDATION_ARTIFACT_ID,
        "validation_artifact_digest": VALIDATION_ARTIFACT_DIGEST,
        "validation_payload_sha256": VALIDATION_PAYLOAD_SHA256,
        "activation_comment_id": ACTIVATION_COMMENT_ID,
        "manifest_payload_sha256": Base.MANIFEST_PAYLOAD,
        "algebra": algebra,
        "algebra_id": ALGEBRA_IDS[algebra],
        "logical_class": int(logical_class),
        "selector_count": len(rows),
        "global_selector_index_min": min(int(row["selector_index"]) for row in rows),
        "global_selector_index_max": max(int(row["selector_index"]) for row in rows),
        "rows_sha256": Base.digest(rows),
        "compile_identity": identity,
        "corrections_fixed": False,
        "independent_scoring_performed": False,
        "matched_comparison_performed": False,
        "quality_exposed": False,
        "scientific_semantics_changed": False,
    }
    write_json(output, report)
    return report


def _rows_for_algebra(root: Path, algebra: str) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for logical_class in range(LOGICAL_CLASSES):
        path = root / f"rows-{algebra}-class-{logical_class}.jsonl"
        if not path.is_file():
            matches = list(root.rglob(path.name))
            if len(matches) != 1:
                raise ValueError(
                    f"expected one {path.name}; found {len(matches)}"
                )
            path = matches[0]
        rows = verify_native_rows(algebra, logical_class, load_jsonl(path))
        for row in rows:
            global_index = int(row["selector_index"])
            if global_index in result:
                raise AssertionError("duplicate algebra campaign row")
            result[global_index] = row
    if len(result) != SELECTORS_PER_ALGEBRA:
        raise AssertionError("algebra campaign coverage incomplete")
    return result


def class_record_from_native(
    *,
    logical_class: int,
    meta: dict[str, int],
    sum_row: dict[str, Any],
    soft_row: dict[str, Any],
    min_row: dict[str, Any],
) -> dict[str, Any]:
    for algebra, row in (
        ("sum_product_bsc_p_0_1", sum_row),
        ("soft_tropical_base_2", soft_row),
        ("min_plus_hamming", min_row),
    ):
        if int(row["selector_coordinate"]) != meta["coordinate"]:
            raise AssertionError(f"{algebra} selector coordinate mismatch")
    representative = int(min_row["minimum_representative_hex"], 16)
    canonical = int(min_row["canonical_hex"], 16)
    context = frozen_context()
    if C72.selector_functional_value(
        representative, context["selector_rows"]
    ) != meta["functional"]:
        raise AssertionError("assembled representative leaves requested class")
    if C72.selector_functional_value(
        canonical, context["selector_rows"]
    ) != meta["functional"]:
        raise AssertionError("assembled canonical key leaves requested class")
    return {
        "logical_class": int(logical_class),
        "selector_coordinate": int(meta["coordinate"]),
        "score_sum_product": int(sum_row["value_hex"], 16),
        "score_soft_tropical": int(soft_row["value_hex"], 16),
        "minimum_weight": int(min_row["minimum_weight"]),
        "minimum_representative": representative,
        "canonical_key": canonical,
    }


def aggregate_fixed_rows(
    *,
    sum_root: Path,
    soft_root: Path,
    min_root: Path,
    orchestration_head: str,
    output: Path,
) -> dict[str, Any]:
    if not orchestration_head:
        raise ValueError("orchestration head required")
    sum_rows = _rows_for_algebra(sum_root, "sum_product_bsc_p_0_1")
    soft_rows = _rows_for_algebra(soft_root, "soft_tropical_base_2")
    min_rows = _rows_for_algebra(min_root, "min_plus_hamming")
    context = frozen_context()
    corpus = frozen_corpus()
    fixed_rows: list[dict[str, Any]] = []
    for corpus_row in corpus:
        input_index = int(corpus_row["index"])
        error = Base.F2.b2i(corpus_row["error"])
        syndrome = Base.F2.syndrome(error, context["code"]["hz"])
        class_records: list[dict[str, Any]] = []
        for logical_class in range(LOGICAL_CLASSES):
            global_index = input_index * LOGICAL_CLASSES + logical_class
            _, coordinate, functional = Base.selector_seed_for(
                context, syndrome, logical_class
            )
            meta = {
                "global_index": global_index,
                "input_index": input_index,
                "logical_class": logical_class,
                "syndrome": int(syndrome),
                "coordinate": int(coordinate),
                "functional": int(functional),
            }
            class_records.append(
                class_record_from_native(
                    logical_class=logical_class,
                    meta=meta,
                    sum_row=sum_rows[global_index],
                    soft_row=soft_rows[global_index],
                    min_row=min_rows[global_index],
                )
            )
        if len(class_records) != LOGICAL_CLASSES:
            raise AssertionError("logical-class assembly incomplete")
        decisions = C72.decision_from_class_records(class_records, 90)
        decision_digest = Base.digest(decisions)
        serialized = {
            algebra: {
                **cell,
                "correction": Base.F2.i2b(int(cell["correction"]), 90),
                "canonical_key": Base.F2.i2b(int(cell["canonical_key"]), 90),
                "tied_canonical_keys": [
                    Base.F2.i2b(int(value), 90)
                    for value in cell["tied_canonical_keys"]
                ],
            }
            for algebra, cell in decisions.items()
        }
        fixed_rows.append(
            {
                "index": input_index,
                "syndrome": Base.F2.i2b(
                    int(syndrome), len(context["code"]["hz"])
                ),
                "logical_classes_evaluated": LOGICAL_CLASSES,
                "class_score_stream_sha256": decision_digest,
                "decisions": serialized,
            }
        )
    if [int(row["index"]) for row in fixed_rows] != list(range(INPUTS)):
        raise AssertionError("fixed decoder row coverage incomplete")
    report: dict[str, Any] = {
        "experiment_id": Base.EXPERIMENT_ID,
        "phase": "ACTIVATED_EXACT_DECODE_FIX_CORRECTIONS",
        "status": "C90_EXACT_CORRECTIONS_FIXED",
        "activation_head": ACTIVATION_HEAD,
        "orchestration_head": orchestration_head,
        "manifest_payload_sha256": Base.MANIFEST_PAYLOAD,
        "validation_payload_sha256": VALIDATION_PAYLOAD_SHA256,
        "input_count": INPUTS,
        "logical_classes_per_input": LOGICAL_CLASSES,
        "selector_evaluations_per_algebra": SELECTORS_PER_ALGEBRA,
        "total_selector_evaluations": 3 * SELECTORS_PER_ALGEBRA,
        "compile_identities": COMPILE_IDENTITIES,
        "fixed_decoder_rows": fixed_rows,
        "fixed_decoder_rows_sha256": Base.digest(fixed_rows),
        "corrections_fixed": True,
        "independent_scoring_performed": False,
        "matched_comparison_performed": False,
        "quality_exposed": False,
        "scientific_semantics_changed": False,
    }
    write_json(output, report)
    return report


def score_fixed_rows(
    *,
    fixed_path: Path,
    conventional_artifact_dir: Path,
    orchestration_head: str,
    output: Path,
) -> dict[str, Any]:
    fixed = json.loads(fixed_path.read_text(encoding="utf-8"))
    if fixed.get("status") != "C90_EXACT_CORRECTIONS_FIXED":
        raise ValueError("fixed-correction receipt is not passing")
    if fixed.get("activation_head") != ACTIVATION_HEAD:
        raise ValueError("fixed-correction activation head drift")
    if fixed.get("orchestration_head") != orchestration_head:
        raise ValueError("fixed-correction orchestration head drift")
    rows = fixed.get("fixed_decoder_rows", [])
    if len(rows) != INPUTS or Base.digest(rows) != fixed.get(
        "fixed_decoder_rows_sha256"
    ):
        raise ValueError("fixed decoder row digest drift")
    context = frozen_context()
    corpus = list(frozen_corpus())
    conventional = Execute.load_conventional_outcomes(
        conventional_artifact_dir
    )
    scored = Execute.score_and_compare(
        rows, context, corpus, conventional
    )
    if scored.get("status") != "C90_TCM_MATCHED_COMPARISON_COMPLETED":
        raise AssertionError("terminal C90 comparison predicate not satisfied")
    report: dict[str, Any] = {
        "experiment_id": Base.EXPERIMENT_ID,
        "phase": "ACTIVATED_INDEPENDENT_SCORE_AND_MATCHED_COMPARE",
        "status": scored["status"],
        "activation_head": ACTIVATION_HEAD,
        "orchestration_head": orchestration_head,
        "manifest_payload_sha256": Base.MANIFEST_PAYLOAD,
        "validation_payload_sha256": VALIDATION_PAYLOAD_SHA256,
        "fixed_decoder_rows_sha256": fixed["fixed_decoder_rows_sha256"],
        "scoring_and_comparison": scored,
        "claim_boundary": Base.load_manifest()["claim_boundary"],
        "corrections_fixed_before_scoring": True,
        "independent_scoring_performed": True,
        "matched_comparison_performed": True,
        "quality_exposed": True,
        "scientific_semantics_changed": False,
    }
    write_json(output, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)

    p = sub.add_parser("selectors")
    p.add_argument("--logical-class", type=int, required=True)
    p.add_argument("--output", type=Path, required=True)

    p = sub.add_parser("validate-shard")
    p.add_argument("--algebra", choices=tuple(ALGEBRA_IDS), required=True)
    p.add_argument("--logical-class", type=int, required=True)
    p.add_argument("--rows", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)

    p = sub.add_parser("aggregate")
    p.add_argument("--sum-root", type=Path, required=True)
    p.add_argument("--soft-root", type=Path, required=True)
    p.add_argument("--min-root", type=Path, required=True)
    p.add_argument("--orchestration-head", required=True)
    p.add_argument("--output", type=Path, required=True)

    p = sub.add_parser("score")
    p.add_argument("--fixed", type=Path, required=True)
    p.add_argument("--conventional-artifact-dir", type=Path, required=True)
    p.add_argument("--orchestration-head", required=True)
    p.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()
    if args.mode == "selectors":
        write_selector_file(args.logical_class, args.output)
        result = {
            "status": "C90_ACTIVATED_SELECTOR_INPUT_SHARD_PREPARED",
            "logical_class": args.logical_class,
            "selector_count": INPUTS,
            "quality_exposed": False,
        }
    elif args.mode == "validate-shard":
        result = validate_shard(
            args.algebra, args.logical_class, args.rows, args.output
        )
    elif args.mode == "aggregate":
        result = aggregate_fixed_rows(
            sum_root=args.sum_root,
            soft_root=args.soft_root,
            min_root=args.min_root,
            orchestration_head=args.orchestration_head,
            output=args.output,
        )
    else:
        result = score_fixed_rows(
            fixed_path=args.fixed,
            conventional_artifact_dir=args.conventional_artifact_dir,
            orchestration_head=args.orchestration_head,
            output=args.output,
        )
    print(
        json.dumps(
            {
                "status": result["status"],
                "payload_sha256": result.get("payload_sha256"),
                "quality_exposed": result.get("quality_exposed", False),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
