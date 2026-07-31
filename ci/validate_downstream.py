#!/usr/bin/env python3
"""Fail-closed validation for QTR-SIG-WP01, WP02, and bounded WP03."""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reference"))
sys.path.insert(0, str(ROOT / "ci"))

import downstream_atlas as da  # noqa: E402
from schema_validation import SchemaValidationError, validate_instance  # noqa: E402

RECORD_ID = re.compile(r"^[a-z][a-z0-9_]{2,79}$")
BIT_STRING = re.compile(r"^[01]+$")
SUPPORTED_PREDICATES = {"or", "majority", "parity", "exact_weight"}
SUPPORTED_CONSTRUCTIONS = {
    "marked_row",
    "signed_hamming_scalar",
    "centered_weight_scalar",
}


class ValidationError(RuntimeError):
    """Raised when a governed downstream record violates its contract."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValidationError(f"cannot load {path.relative_to(ROOT)}: {exc}") from exc


def exact_keys(
    record: dict[str, Any],
    required: set[str],
    optional: set[str] | None = None,
    *,
    path: str = "record",
) -> None:
    require(isinstance(record, dict), f"{path}: expected object")
    optional = optional or set()
    missing = required - set(record)
    extra = set(record) - required - optional
    require(not missing, f"{path}: missing keys {sorted(missing)}")
    require(not extra, f"{path}: unknown keys {sorted(extra)}")


def require_int(value: Any, message: str, *, minimum: int | None = None) -> int:
    require(isinstance(value, int) and not isinstance(value, bool), message)
    if minimum is not None:
        require(value >= minimum, message)
    return value


def require_number(value: Any, message: str, *, positive: bool = False) -> float:
    require(
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value)),
        message,
    )
    numeric = float(value)
    if positive:
        require(numeric > 0.0, message)
    return numeric


def require_nonempty_string(value: Any, message: str) -> str:
    require(isinstance(value, str) and bool(value.strip()), message)
    return value


def require_unique_strings(value: Any, message: str, *, allow_empty: bool = False) -> list[str]:
    require(isinstance(value, list), message)
    if not allow_empty:
        require(bool(value), message)
    require(all(isinstance(item, str) and item.strip() for item in value), message)
    require(len(value) == len(set(value)), message)
    return value


def validate_record_identity(record: dict[str, Any], package: str) -> None:
    record_id = require_nonempty_string(record["record_id"], f"{package}: invalid record_id")
    require(RECORD_ID.fullmatch(record_id) is not None, f"{record_id}: invalid record identifier")


def validate_predicate(record: dict[str, Any], package: str) -> tuple[str, int]:
    predicate_id = require_nonempty_string(
        record["predicate_id"], f"{package}: invalid predicate_id"
    )
    require(
        predicate_id in SUPPORTED_PREDICATES,
        f"{record['record_id']}: unsupported predicate {predicate_id}",
    )
    width = require_int(
        record["input_width"],
        f"{record['record_id']}: input_width must be an integer in [1, 16]",
        minimum=1,
    )
    require(width <= 16, f"{record['record_id']}: input_width exceeds finite replay bound")

    parameters = record.get("predicate_parameters", {})
    require(isinstance(parameters, dict), f"{record['record_id']}: predicate parameters must be an object")
    if predicate_id == "exact_weight":
        exact_keys(
            parameters,
            {"target_weight"},
            path=f"{record['record_id']}.predicate_parameters",
        )
        target = require_int(
            parameters["target_weight"],
            f"{record['record_id']}: target_weight must be an integer in range",
            minimum=0,
        )
        require(target <= width, f"{record['record_id']}: target_weight exceeds input width")
    else:
        require(not parameters, f"{record['record_id']}: unexpected predicate parameters")
    return predicate_id, width


def validate_wp01(record: dict[str, Any]) -> None:
    exact_keys(
        record,
        {
            "record_id",
            "predicate_id",
            "predicate_parameters",
            "input_width",
            "group_action",
            "invariant_coordinates",
            "source_candidates",
            "claim_status",
            "expected",
        },
        path="WP01 record",
    )
    validate_record_identity(record, "WP01")
    _, width = validate_predicate(record, "WP01")
    require(
        record["group_action"] == "S_n_coordinate_permutations",
        f"{record['record_id']}: WP01 action is not locked",
    )
    require(
        record["invariant_coordinates"] == ["hamming_weight"],
        f"{record['record_id']}: WP01 invariant is not locked",
    )
    require_unique_strings(
        record["source_candidates"],
        f"{record['record_id']}: source candidates must be unique strings",
        allow_empty=True,
    )
    require(
        record["claim_status"] == "finite_exhaustive_evidence",
        f"{record['record_id']}: WP01 claim status invalid",
    )

    expected = record["expected"]
    exact_keys(
        expected,
        {"orbit_count", "orbit_sizes", "labels_by_orbit", "boundary_count"},
        path=f"{record['record_id']}.expected",
    )
    orbit_count = require_int(
        expected["orbit_count"],
        f"{record['record_id']}: orbit_count must be a positive integer",
        minimum=1,
    )
    require(orbit_count == width + 1, f"{record['record_id']}: orbit count must equal n+1")

    orbit_sizes = expected["orbit_sizes"]
    require(isinstance(orbit_sizes, list), f"{record['record_id']}: orbit_sizes must be an array")
    require(len(orbit_sizes) == orbit_count, f"{record['record_id']}: orbit_sizes length mismatch")
    require(
        all(isinstance(size, int) and not isinstance(size, bool) and size > 0 for size in orbit_sizes),
        f"{record['record_id']}: orbit sizes must be positive integers",
    )
    require(sum(orbit_sizes) == 2**width, f"{record['record_id']}: orbit sizes do not cover domain")

    labels = expected["labels_by_orbit"]
    require(isinstance(labels, list) and len(labels) == orbit_count, f"{record['record_id']}: labels length mismatch")
    for index, label_set in enumerate(labels):
        require(
            isinstance(label_set, list)
            and bool(label_set)
            and len(label_set) == len(set(label_set))
            and all(label in (0, 1) and not isinstance(label, bool) for label in label_set),
            f"{record['record_id']}: invalid label set at orbit {index}",
        )

    boundary_count = require_int(
        expected["boundary_count"],
        f"{record['record_id']}: boundary_count must be a nonnegative integer",
        minimum=0,
    )
    require(boundary_count <= width, f"{record['record_id']}: boundary count exceeds n")


def validate_wp02(record: dict[str, Any]) -> None:
    exact_keys(
        record,
        {
            "record_id",
            "predicate_id",
            "predicate_parameters",
            "input_width",
            "source_invariant_record",
            "construction",
            "claim_status",
            "expected",
        },
        path="WP02 record",
    )
    validate_record_identity(record, "WP02")
    _, width = validate_predicate(record, "WP02")
    require_nonempty_string(
        record["source_invariant_record"],
        f"{record['record_id']}: missing WP01 source record",
    )

    construction = record["construction"]
    exact_keys(
        construction,
        {"kind", "operator_shape", "definition"},
        {"target_weight", "scale"},
        path=f"{record['record_id']}.construction",
    )
    kind = require_nonempty_string(
        construction["kind"], f"{record['record_id']}: invalid construction kind"
    )
    require(kind in SUPPORTED_CONSTRUCTIONS, f"{record['record_id']}: unsupported construction")
    require_nonempty_string(
        construction["definition"], f"{record['record_id']}: missing construction definition"
    )

    shape = construction["operator_shape"]
    require(
        isinstance(shape, list)
        and len(shape) == 2
        and all(isinstance(item, int) and not isinstance(item, bool) and item > 0 for item in shape),
        f"{record['record_id']}: invalid operator shape",
    )
    if kind == "marked_row":
        require(shape == [1, width], f"{record['record_id']}: marked row shape must be [1, n]")
        require("target_weight" not in construction and "scale" not in construction, f"{record['record_id']}: marked row has scalar-only fields")
    elif kind == "signed_hamming_scalar":
        require(shape == [1, 1], f"{record['record_id']}: signed scalar shape must be [1, 1]")
        require("target_weight" not in construction and "scale" not in construction, f"{record['record_id']}: signed scalar has centered-only fields")
    else:
        require(shape == [1, 1], f"{record['record_id']}: centered scalar shape must be [1, 1]")
        target = require_int(
            construction.get("target_weight"),
            f"{record['record_id']}: centered target_weight must be an integer",
            minimum=0,
        )
        require(target <= width, f"{record['record_id']}: centered target exceeds width")
        require_number(
            construction.get("scale"),
            f"{record['record_id']}: centered scale must be positive and finite",
            positive=True,
        )
        require(
            record["predicate_id"] == "exact_weight"
            and record["predicate_parameters"].get("target_weight") == target,
            f"{record['record_id']}: centered construction and predicate target disagree",
        )

    require(
        record["claim_status"] in {"finite_exhaustive_evidence", "finite_negative_result"},
        f"{record['record_id']}: WP02 claim status invalid",
    )
    expected = record["expected"]
    exact_keys(
        expected,
        {
            "signed_collision_pairs",
            "singular_collision_pairs",
            "singular_semantically_sufficient",
        },
        path=f"{record['record_id']}.expected",
    )
    require_int(
        expected["signed_collision_pairs"],
        f"{record['record_id']}: signed collision count must be nonnegative",
        minimum=0,
    )
    singular_pairs = require_int(
        expected["singular_collision_pairs"],
        f"{record['record_id']}: singular collision count must be nonnegative",
        minimum=0,
    )
    require(
        isinstance(expected["singular_semantically_sufficient"], bool),
        f"{record['record_id']}: singular sufficiency must be boolean",
    )
    require(
        expected["singular_semantically_sufficient"] == (singular_pairs == 0),
        f"{record['record_id']}: collision count and sufficiency disagree",
    )
    require(
        (record["claim_status"] == "finite_negative_result")
        == (not expected["singular_semantically_sufficient"]),
        f"{record['record_id']}: negative-result status does not match singular channel",
    )


def validate_wp03(record: dict[str, Any]) -> None:
    exact_keys(
        record,
        {
            "record_id",
            "predicate_id",
            "input_width",
            "certificate_family",
            "source_linearization_record",
            "adversary_certificate",
            "span_program",
            "claim_status",
            "limitations",
            "sources",
        },
        path="WP03 record",
    )
    validate_record_identity(record, "WP03")
    predicate_id, width = validate_predicate(record, "WP03")
    require(predicate_id == "or", f"{record['record_id']}: bounded WP03 is restricted to OR")
    require_nonempty_string(
        record["source_linearization_record"],
        f"{record['record_id']}: missing WP02 source record",
    )
    require(
        record["certificate_family"] == "or_star_and_unit_span_program",
        f"{record['record_id']}: WP03 family invalid",
    )
    require(
        record["claim_status"] == "finite_certificate",
        f"{record['record_id']}: WP03 claim status invalid",
    )

    adversary = record["adversary_certificate"]
    exact_keys(
        adversary,
        {"zero_input", "one_inputs", "definition"},
        path=f"{record['record_id']}.adversary_certificate",
    )
    zero_input = require_nonempty_string(
        adversary["zero_input"], f"{record['record_id']}: invalid zero input"
    )
    require(
        BIT_STRING.fullmatch(zero_input) is not None
        and len(zero_input) == width
        and set(zero_input) == {"0"},
        f"{record['record_id']}: zero input must be the all-zero n-bit string",
    )
    one_inputs = require_unique_strings(
        adversary["one_inputs"],
        f"{record['record_id']}: one inputs must be unique nonempty bit strings",
    )
    require(len(one_inputs) == width, f"{record['record_id']}: star must have n leaves")
    for item in one_inputs:
        require(
            BIT_STRING.fullmatch(item) is not None
            and len(item) == width
            and item.count("1") == 1,
            f"{record['record_id']}: invalid weight-one star leaf {item!r}",
        )
    require_nonempty_string(
        adversary["definition"], f"{record['record_id']}: adversary definition missing"
    )

    span = record["span_program"]
    exact_keys(
        span,
        {"vector_space_dimension", "target", "input_vectors", "availability_rule"},
        path=f"{record['record_id']}.span_program",
    )
    require_int(
        span["vector_space_dimension"],
        f"{record['record_id']}: vector-space dimension must be one",
        minimum=1,
    )
    require(span["vector_space_dimension"] == 1, f"{record['record_id']}: only the one-dimensional OR span program is admitted")
    require(span["target"] == [1.0], f"{record['record_id']}: span target must be [1.0]")
    vectors = span["input_vectors"]
    require(
        isinstance(vectors, list)
        and len(vectors) == width
        and all(vector == [1.0] for vector in vectors),
        f"{record['record_id']}: span input vectors must be n copies of [1.0]",
    )
    require_nonempty_string(
        span["availability_rule"], f"{record['record_id']}: availability rule missing"
    )
    require_unique_strings(
        record["limitations"], f"{record['record_id']}: limitations must be unique and nonempty"
    )
    sources = require_unique_strings(
        record["sources"], f"{record['record_id']}: sources must be unique and nonempty"
    )
    require(
        all(source.startswith("arXiv:") or source.lower().startswith("doi:") for source in sources),
        f"{record['record_id']}: sources must use stable arXiv or DOI identifiers",
    )


def validate_interfaces(registry: dict[str, Any], wp00_registry: dict[str, Any]) -> None:
    wp00 = {record["candidate_id"]: record for record in wp00_registry["candidates"]}
    wp01 = {record["record_id"]: record for record in registry["WP01"]}
    wp02 = {record["record_id"]: record for record in registry["WP02"]}

    for package in ("WP01", "WP02", "WP03"):
        identifiers = [record["record_id"] for record in registry[package]]
        require(
            len(identifiers) == len(set(identifiers)),
            f"{package}: duplicate record identifiers",
        )

    for record in registry["WP01"]:
        for source_id in record["source_candidates"]:
            require(source_id in wp00, f"{record['record_id']}: missing WP00 source {source_id}")
            source = wp00[source_id]
            require(
                source["predicate_id"] == record["predicate_id"]
                and source["input_width"] == record["input_width"],
                f"{record['record_id']}: WP00 source predicate or width mismatch",
            )

    for record in registry["WP02"]:
        source_id = record["source_invariant_record"]
        require(source_id in wp01, f"{record['record_id']}: missing WP01 source")
        source = wp01[source_id]
        require(
            source["predicate_id"] == record["predicate_id"]
            and source["predicate_parameters"] == record["predicate_parameters"]
            and source["input_width"] == record["input_width"],
            f"{record['record_id']}: WP01 source interface mismatch",
        )

    for record in registry["WP03"]:
        source_id = record["source_linearization_record"]
        require(source_id in wp02, f"{record['record_id']}: missing WP02 source")
        source = wp02[source_id]
        require(
            source["predicate_id"] == record["predicate_id"]
            and source["input_width"] == record["input_width"],
            f"{record['record_id']}: WP02 source interface mismatch",
        )


def validate_all() -> dict[str, Any]:
    schema = load(ROOT / "schemas" / "downstream-atlas.schema.json")
    registry = load(ROOT / "registry" / "downstream-atlas.json")
    wp00_registry = load(ROOT / "registry" / "signal-candidates.json")
    intake = load(ROOT / "reviews" / "QTR-SIG-NEXT-001" / "intake.json")

    try:
        validate_instance(registry, schema)
    except SchemaValidationError as exc:
        raise ValidationError(str(exc)) from exc

    require(
        registry["authority"]["charter_adoption_merge"]
        == "0743ac9947cc835de817d50d92cf3df444132449",
        "wrong adoption authority",
    )
    require(
        registry["authority"]["adoption_pin_merge"]
        == "468f22e694c569969602ec68812c57b9109dc8ad",
        "wrong adoption pin",
    )
    require(
        all(isinstance(registry[package], list) and registry[package] for package in ("WP01", "WP02", "WP03")),
        "every downstream package must contain at least one governed record",
    )

    for record in registry["WP01"]:
        validate_wp01(record)
    for record in registry["WP02"]:
        validate_wp02(record)
    for record in registry["WP03"]:
        validate_wp03(record)
    validate_interfaces(registry, wp00_registry)

    require(
        intake["status"] == "candidate_implementation_ready",
        "downstream intake status is stale",
    )
    require("QTR-SIG-WP04" in intake["excluded_scope"], "WP04 gate is not explicit")

    report = da.evaluate_registry(registry)
    expected = load(ROOT / "evidence" / "downstream-atlas-report.json")
    require(report == expected, "downstream evidence mismatch")

    for record, observed in zip(registry["WP01"], report["WP01"]):
        wanted = record["expected"]
        require(
            observed["orbit_count"] == wanted["orbit_count"]
            and observed["orbit_sizes"] == wanted["orbit_sizes"]
            and observed["labels_by_orbit"] == wanted["labels_by_orbit"]
            and observed["boundary_count"] == wanted["boundary_count"],
            f"{record['record_id']}: WP01 expected mismatch",
        )
        require(
            observed["quotient_semantically_sufficient"],
            f"{record['record_id']}: quotient collision",
        )

    for record, observed in zip(registry["WP02"], report["WP02"]):
        wanted = record["expected"]
        require(
            observed["signed_channel"]["cross_label_collision_pairs"]
            == wanted["signed_collision_pairs"],
            f"{record['record_id']}: signed mismatch",
        )
        require(
            observed["singular_value_channel"]["cross_label_collision_pairs"]
            == wanted["singular_collision_pairs"],
            f"{record['record_id']}: singular mismatch",
        )
        require(
            observed["singular_value_channel"]["semantically_sufficient"]
            == wanted["singular_semantically_sufficient"],
            f"{record['record_id']}: singular status mismatch",
        )

    for record, observed in zip(registry["WP03"], report["WP03"]):
        require(
            math.isclose(observed["adversary_certificate"]["objective"], 2.0),
            f"{record['record_id']}: WP03 objective mismatch",
        )
        require(
            math.isclose(observed["span_program"]["witness_size_complexity"], 2.0),
            f"{record['record_id']}: WP03 span mismatch",
        )
        require(
            observed["certificate_objectives_match"],
            f"{record['record_id']}: WP03 objectives disagree",
        )
    return report


def main() -> int:
    report = validate_all()
    print(f"QTR-SIG-NEXT-001 validation passed: {report['payload_sha256']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        print(f"QTR downstream validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
