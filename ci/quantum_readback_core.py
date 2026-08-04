"""Shared contract and digest primitives for QUANTUM full readback."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "governance" / "quantum_full_readback_contract.json"
API_ROOT = "https://api.github.com"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
FALSE_BOUNDARIES = {
    "settings_or_rulesets_mutated",
    "source_or_workflow_mutated",
    "deviation_disposition_changed",
    "repository_conformance_claimed",
    "organization_wide_conformance_claimed",
    "mathematics_certified",
    "quantum_advantage_proved",
    "hardware_validated",
    "deployment_manufacturing_product_or_commercial_authority",
}

class ReadbackError(RuntimeError):
    """Raised when collection or fail-closed validation fails."""


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ReadbackError(f"JSON root must be an object: {path}")
    return value


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def byte_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def exact_keys(
    value: dict[str, Any], required: set[str], *, path: str
) -> None:
    if not isinstance(value, dict):
        raise ReadbackError(f"{path} must be an object")
    actual = set(value)
    if actual != required:
        raise ReadbackError(
            f"{path} keys drift: expected={sorted(required)} actual={sorted(actual)}"
        )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReadbackError(message)


def validate_contract(contract: dict[str, Any]) -> None:
    exact_keys(
        contract,
        {
            "$schema",
            "schema_version",
            "operation_id",
            "repository",
            "branch",
            "api_version",
            "authority",
            "execution",
            "expected",
            "claim_boundaries",
            "output",
        },
        path="contract",
    )
    require(
        contract["$schema"]
        == "../schemas/quantum_full_readback_contract.schema.json",
        "contract schema identity drift",
    )
    require(contract["schema_version"] == "1.0.0", "contract version drift")
    require(
        contract["operation_id"] == "GCL-GHOS-QUANTUM-FULL-READBACK-001",
        "operation identity drift",
    )
    require(
        contract["repository"] == "grandchallenge/QUANTUM-TECHNOLOGIES",
        "repository identity drift",
    )
    require(contract["branch"] == "main", "branch identity drift")
    require(contract["api_version"] == "2026-03-10", "API version drift")

    authority = contract["authority"]
    expected_authority = {
        "owner_controls_issue": "https://github.com/grandchallenge/QUANTUM-TECHNOLOGIES/issues/21",
        "parent_remediation_issue": "https://github.com/grandchallenge/QUANTUM-TECHNOLOGIES/issues/14",
        "standards_campaign_issue": "https://github.com/grandchallenge/gcl-standards/issues/22",
        "profile_merge": "5ec22de5d18e02ba91b47f74f23c7acde6bc3ddc",
        "surfaces_merge": "cc89ec99493e5ecc2fa54cd5a4698dae0aa2e606",
        "action_policy_merge": "260f469ba7349350c2b192a0e066a24aa670d611",
    }
    exact_keys(authority, set(expected_authority), path="authority")
    require(authority == expected_authority, "authority identity drift")

    execution = contract["execution"]
    exact_keys(
        execution,
        {
            "owner_controls_evidence_merge_required",
            "transport",
            "wait_seconds_default",
        },
        path="execution",
    )
    require(
        execution["owner_controls_evidence_merge_required"] is True,
        "owner-controls evidence merge must be required",
    )
    require(
        execution["transport"] == "authenticated_github_rest_get_only",
        "collector transport drift",
    )
    require(
        isinstance(execution["wait_seconds_default"], int)
        and execution["wait_seconds_default"] >= 0,
        "invalid wait-seconds default",
    )

    expected = contract["expected"]
    exact_keys(
        expected,
        {
            "repository_settings",
            "protected_main_ruleset",
            "immutable_release_tag_ruleset",
            "security",
            "required_workflows",
            "governed_surfaces",
            "required_check_runs",
        },
        path="expected",
    )
    require(
        expected["repository_settings"]
        == {
            "default_branch": "main",
            "archived": False,
            "visibility": "public",
            "allow_merge_commit": True,
            "allow_squash_merge": True,
            "allow_rebase_merge": False,
            "allow_auto_merge": True,
            "allow_update_branch": False,
            "delete_branch_on_merge": True,
        },
        "repository-settings target drift",
    )
    require(
        sorted(expected["required_check_runs"])
        == ["policy", "security / action-policy", "validate"],
        "required check-run set drift",
    )
    require(
        isinstance(expected["required_workflows"], list)
        and len(expected["required_workflows"]) == 2,
        "required workflow inventory drift",
    )
    require(
        isinstance(expected["governed_surfaces"], list)
        and len(expected["governed_surfaces"]) == 3,
        "governed surface inventory drift",
    )

    boundaries = contract["claim_boundaries"]
    require(set(boundaries) == FALSE_BOUNDARIES, "claim-boundary key drift")
    for field in FALSE_BOUNDARIES:
        require(boundaries[field] is False, f"claim-boundary inflation: {field}")

    output = contract["output"]
    exact_keys(output, {"receipt", "digest"}, path="output")
    require(output["receipt"].endswith(".json"), "receipt output must be JSON")
    require(
        output["digest"] == output["receipt"] + ".sha256",
        "digest output must be receipt name plus .sha256",
    )
