#!/usr/bin/env python3
"""Fail-closed structural and executable validation for QTR-SIG-WP00."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reference"))
sys.path.insert(0, str(ROOT / "ci"))

import signal_discovery as sd  # noqa: E402
from schema_validation import SchemaValidationError, validate_instance  # noqa: E402


class ValidationError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"Missing required file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def validate_semantic_constraints(candidate: dict[str, Any]) -> None:
    candidate_id = candidate["candidate_id"]
    require(candidate["predicate_id"] in sd.PREDICATES, f"{candidate_id}: unknown predicate")
    implementation = candidate["signal"]["implementation"]
    require(implementation in sd.SIGNALS, f"{candidate_id}: unknown signal implementation")

    promise = candidate["promise_domain"]
    if promise["kind"] == "hamming_weights":
        weights = promise["weights"]
        require(weights, f"{candidate_id}: empty promised weight set")
        require(
            all(0 <= weight <= candidate["input_width"] for weight in weights),
            f"{candidate_id}: promised weight outside input range",
        )

    policy = candidate["numerics"]["equivalence_policy"]
    require(
        math.isclose(
            policy["absolute_tolerance"],
            10.0 ** (-policy["digits"]),
            rel_tol=0.0,
            abs_tol=1e-18,
        ),
        f"{candidate_id}: decimal digits and absolute tolerance disagree",
    )

    if candidate["cost"]["optimality_status"] == "certified_optimal":
        require(
            any("arXiv:" in source or "doi:" in source.lower()
                for source in candidate["provenance"]["sources"]),
            f"{candidate_id}: optimality claim lacks an identified source",
        )


def validate_expected_metrics(candidate: dict[str, Any], report: dict[str, Any]) -> None:
    expected = candidate["expected_metrics"]
    candidate_id = candidate["candidate_id"]
    require(
        report["semantic_sufficient_on_domain"]
        == expected["semantic_sufficient_on_domain"],
        f"{candidate_id}: semantic sufficiency mismatch",
    )
    require(
        report["cross_label_collisions"] == expected["cross_label_collisions"],
        f"{candidate_id}: collision count mismatch",
    )
    require(
        math.isclose(report["empirical_gap"], expected["empirical_gap"], abs_tol=1e-10),
        f"{candidate_id}: empirical gap mismatch",
    )
    require(
        report["alternation_degree_lower_bound"]
        == expected["alternation_degree_lower_bound"],
        f"{candidate_id}: alternation lower-bound mismatch",
    )
    require(
        report["numerical_conventions"] == candidate["numerics"],
        f"{candidate_id}: evaluator did not emit declared numerical conventions",
    )


def validate_migration_manifest(manifest: dict[str, Any]) -> None:
    require(manifest["programme_id"] == "QTR", "Migration manifest has wrong programme")
    require(
        manifest["target_repository"] == "grandchallenge/QUANTUM-TECHNOLOGIES",
        "Migration manifest has wrong target repository",
    )
    require(manifest["status"] == "migrated_candidate", "Migration status must be current")
    historical = manifest["historical_migration"]
    require(
        historical["source_commit"] == "33b87f2f15f3af6c6e3b9e38ed3d0d3ba6244835",
        "Historical source commit is not pinned",
    )
    require(
        historical["target_payload_commit"] == "871da6e9c1953b7dcbbf84a20121995b98d6c366",
        "Historical target payload commit is not pinned",
    )
    for relative in manifest["required_files"]:
        require((ROOT / relative).is_file(), f"Migration manifest references missing file: {relative}")


def validate_review_docket(docket: dict[str, Any]) -> None:
    require(docket["status"] == "correction_implemented", "Review docket status is stale")
    require(docket["entry_conditions"]["repository_public"] is True, "Public status is stale")
    protection = docket["entry_conditions"]["protected_main"]
    require(protection["status"] == "owner_attested", "Protected-main status is stale")
    require(protection["ruleset_name"] == "branch_protect", "Unexpected ruleset identity")
    require(
        docket["previous_cycle"]["referee"]["disposition"] == "revise",
        "Previous Referee disposition is missing",
    )
    require(
        docket["current_cycle"]["status"] == "corrective_head_pending_replay",
        "Current review cycle status is not replay-gated",
    )


def main() -> int:
    schema = load_json(ROOT / "schemas" / "signal-candidate.schema.json")
    registry = load_json(ROOT / "registry" / "signal-candidates.json")
    manifest = load_json(ROOT / "MIGRATION_MANIFEST.json")
    baseline = load_json(ROOT / "evidence" / "baseline-report.json")
    docket = load_json(ROOT / "reviews" / "QTR-ADOPT-001" / "review-docket.json")

    require(schema.get("additionalProperties") is False, "Schema must fail closed")
    require(registry.get("registry_version") == "0.2.0", "Unexpected registry version")
    candidates = registry.get("candidates")
    require(isinstance(candidates, list) and candidates, "Registry candidates must be nonempty")

    seen: set[str] = set()
    for candidate in candidates:
        try:
            validate_instance(candidate, schema)
        except SchemaValidationError as exc:
            raise ValidationError(str(exc)) from exc
        candidate_id = candidate["candidate_id"]
        require(candidate_id not in seen, f"Duplicate candidate identifier: {candidate_id}")
        seen.add(candidate_id)
        validate_semantic_constraints(candidate)
        report = sd.evaluate_candidate(candidate)
        validate_expected_metrics(candidate, report)

    replay = sd.evaluate_registry(registry)
    require(replay == baseline, "Baseline report does not match deterministic replay")
    validate_migration_manifest(manifest)
    validate_review_docket(docket)

    print(
        f"QTR-SIG-WP00 validation passed: {len(candidates)} candidates, "
        f"payload {replay['payload_sha256']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        print(f"QTR validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
