"""Ruleset, repository, and security validators for QUANTUM readback."""
from __future__ import annotations

from typing import Any

from quantum_readback_core import ReadbackError, require

def repo_path(repository: str) -> str:
    return f"/repos/{repository}"


def rule(detail: dict[str, Any], kind: str) -> dict[str, Any]:
    rows = [
        row
        for row in detail.get("rules", [])
        if isinstance(row, dict) and row.get("type") == kind
    ]
    if len(rows) != 1:
        raise ReadbackError(f"expected exactly one ruleset rule of type {kind}")
    return rows[0]


def normalize_ruleset(detail: dict[str, Any]) -> dict[str, Any]:
    pull = rule(detail, "pull_request")["parameters"] if any(
        isinstance(row, dict) and row.get("type") == "pull_request"
        for row in detail.get("rules", [])
    ) else None
    status = rule(detail, "required_status_checks")["parameters"] if any(
        isinstance(row, dict) and row.get("type") == "required_status_checks"
        for row in detail.get("rules", [])
    ) else None
    return {
        "id": detail.get("id"),
        "name": detail.get("name"),
        "target": detail.get("target"),
        "enforcement": detail.get("enforcement"),
        "ref_include": list(
            detail.get("conditions", {}).get("ref_name", {}).get("include") or []
        ),
        "ref_exclude": list(
            detail.get("conditions", {}).get("ref_name", {}).get("exclude") or []
        ),
        "rule_types": sorted(
            str(row.get("type"))
            for row in detail.get("rules", [])
            if isinstance(row, dict)
        ),
        "bypass_actors": list(detail.get("bypass_actors") or []),
        "pull_request": pull,
        "required_status_checks": status,
    }


def validate_repository(
    repository: dict[str, Any], expected: dict[str, Any]
) -> dict[str, Any]:
    require(
        repository.get("permissions", {}).get("admin") is True,
        "authenticated actor lacks repository-admin permission",
    )
    observed = {name: repository.get(name) for name in expected}
    require(observed == expected, f"repository settings drift: {observed!r}")
    return observed


def validate_main_ruleset(
    detail: dict[str, Any], expected: dict[str, Any]
) -> dict[str, Any]:
    current = normalize_ruleset(detail)
    require(current["id"] == expected["id"], "main ruleset ID drift")
    require(current["name"] == expected["name"], "main ruleset name drift")
    require(current["target"] == expected["target"], "main ruleset target drift")
    require(
        current["enforcement"] == expected["enforcement"],
        "main ruleset enforcement drift",
    )
    require(
        len(current["ref_include"]) == 1
        and current["ref_include"][0] in expected["allowed_ref_includes"],
        "main ruleset ref target drift",
    )
    require(current["ref_exclude"] == [], "main ruleset has excluded refs")
    require(
        current["rule_types"] == sorted(expected["exact_rule_types"]),
        "main ruleset rule-type drift",
    )
    require(
        (not current["bypass_actors"]) == expected["zero_bypass"],
        "main ruleset bypass drift",
    )
    pull = current["pull_request"]
    require(isinstance(pull, dict), "main ruleset pull-request rule missing")
    for field in (
        "required_approving_review_count",
        "dismiss_stale_reviews_on_push",
        "require_code_owner_review",
        "require_last_push_approval",
        "required_review_thread_resolution",
    ):
        require(
            pull.get(field) == expected[field],
            f"main ruleset pull-request drift: {field}",
        )
    require(
        sorted(pull.get("allowed_merge_methods") or [])
        == sorted(expected["allowed_merge_methods"]),
        "main ruleset merge-method drift",
    )
    status = current["required_status_checks"]
    require(isinstance(status, dict), "main ruleset status-check rule missing")
    require(
        status.get("strict_required_status_checks_policy")
        == expected["strict_required_status_checks_policy"],
        "main ruleset strict-check drift",
    )
    contexts = sorted(
        str(row.get("context"))
        for row in status.get("required_status_checks") or []
        if isinstance(row, dict)
    )
    require(
        contexts == sorted(expected["required_status_checks"]),
        f"main ruleset required-check drift: {contexts!r}",
    )
    return current


def validate_tag_ruleset(
    detail: dict[str, Any], expected: dict[str, Any]
) -> dict[str, Any]:
    current = normalize_ruleset(detail)
    require(current["id"] == expected["id"], "tag ruleset ID drift")
    require(current["name"] == expected["name"], "tag ruleset name drift")
    require(current["target"] == expected["target"], "tag ruleset target drift")
    require(
        current["enforcement"] == expected["enforcement"],
        "tag ruleset enforcement drift",
    )
    require(current["ref_include"] == expected["ref_include"], "tag ref drift")
    require(current["ref_exclude"] == [], "tag ruleset has excluded refs")
    require(
        current["rule_types"] == sorted(expected["exact_rule_types"]),
        "tag ruleset rule-type drift",
    )
    require(
        (not current["bypass_actors"]) == expected["zero_bypass"],
        "tag ruleset bypass drift",
    )
    return current


def normalize_codeql(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "state": payload.get("state"),
        "languages": sorted(str(value) for value in payload.get("languages") or []),
        "query_suite": payload.get("query_suite"),
        "threat_model": payload.get("threat_model"),
        "runner": payload.get("runner_type") or payload.get("runner_label"),
    }


def validate_security(
    security: dict[str, Any], expected: dict[str, Any]
) -> dict[str, Any]:
    require(
        security.get("vulnerability_alerts") is expected["vulnerability_alerts"],
        "vulnerability-alert state drift",
    )
    require(
        security.get("dependabot_security_updates_enabled")
        is expected["dependabot_security_updates_enabled"],
        "Dependabot security-update state drift",
    )
    require(
        security.get("dependabot_security_updates_paused")
        is expected["dependabot_security_updates_paused"],
        "Dependabot pause state drift",
    )
    require(
        security.get("private_vulnerability_reporting")
        is expected["private_vulnerability_reporting"],
        "private vulnerability-reporting state drift",
    )
    codeql = security.get("codeql")
    require(isinstance(codeql, dict), "CodeQL readback missing")
    require(codeql.get("state") == expected["codeql_state"], "CodeQL state drift")
    require(
        sorted(codeql.get("languages") or [])
        == sorted(expected["codeql_languages"]),
        "CodeQL language drift",
    )
    require(
        codeql.get("query_suite") == expected["codeql_query_suite"],
        "CodeQL query-suite drift",
    )
    require(
        codeql.get("threat_model") == expected["codeql_threat_model"],
        "CodeQL threat-model drift",
    )
    require(
        codeql.get("runner") == expected["codeql_runner"],
        "CodeQL runner drift",
    )
    return security
