#!/usr/bin/env python3
"""Collect and validate the complete QUANTUM post-repair GitHub readback."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from quantum_readback_core import (
    DEFAULT_CONTRACT, SHA40, ReadbackError, byte_sha256, canonical_sha256,
    load_json, require, validate_contract,
)
from quantum_readback_rules import (
    normalize_ruleset, validate_repository, validate_main_ruleset,
    validate_tag_ruleset, normalize_codeql, validate_security,
)
from quantum_readback_evidence import (
    validate_documents, validate_check_runs, validate_codeql_jobs,
    validate_ancestry, scan_for_credentials,
)
from quantum_readback_api import (
    GitHubAPI, gh_token, repo_path, collect_document, fetch_workflow_states,
    security_readback, fetch_rulesets, find_ruleset, fetch_check_runs,
    wait_for_check_runs, comparison,
)

def collect(
    client: GitHubAPI,
    contract: dict[str, Any],
    owner_controls_evidence_merge: str,
    wait_seconds: int,
) -> dict[str, Any]:
    validate_contract(contract)
    require(
        SHA40.fullmatch(owner_controls_evidence_merge) is not None,
        "owner-controls evidence merge must be an exact 40-character commit",
    )
    require(
        owner_controls_evidence_merge
        == contract["authority"]["owner_controls_evidence_merge"],
        "owner-controls evidence merge identity drift",
    )
    repository = contract["repository"]
    base = repo_path(repository)

    _, actor = client.request("/user")
    _, repository_before = client.request(base)
    _, main_before = client.request(f"{base}/commits/{contract['branch']}")
    require(isinstance(actor, dict), "malformed actor readback")
    require(isinstance(repository_before, dict), "malformed repository readback")
    require(isinstance(main_before, dict), "malformed protected-main readback")
    main_sha = str(main_before.get("sha") or "")
    require(SHA40.fullmatch(main_sha) is not None, "malformed protected-main SHA")

    normalized_repository = validate_repository(
        repository_before, contract["expected"]["repository_settings"]
    )

    ancestry: dict[str, Any] = {}
    commits = {
        "owner_controls_evidence_merge": contract["authority"]["owner_controls_evidence_merge"],
        "profile_merge": contract["authority"]["profile_merge"],
        "surfaces_merge": contract["authority"]["surfaces_merge"],
        "action_policy_merge": contract["authority"]["action_policy_merge"],
    }
    for label, commit in commits.items():
        ancestry[label] = validate_ancestry(
            comparison(client, repository, commit, main_sha),
            commit,
            main_sha,
            label=label,
        )

    ruleset_summaries, ruleset_details = fetch_rulesets(client, repository)
    main_detail = find_ruleset(
        ruleset_details,
        name=contract["expected"]["protected_main_ruleset"]["name"],
    )
    tag_detail = find_ruleset(
        ruleset_details,
        ruleset_id=contract["expected"]["immutable_release_tag_ruleset"]["id"],
    )
    normalized_main_ruleset = validate_main_ruleset(
        main_detail, contract["expected"]["protected_main_ruleset"]
    )
    normalized_tag_ruleset = validate_tag_ruleset(
        tag_detail, contract["expected"]["immutable_release_tag_ruleset"]
    )

    security, security_raw = security_readback(client, repository)
    validate_security(security, contract["expected"]["security"])

    workflow_states = fetch_workflow_states(client, repository)
    documents: dict[str, dict[str, Any]] = {}
    for requirement in (
        contract["expected"]["required_workflows"]
        + contract["expected"]["governed_surfaces"]
    ):
        path = requirement["path"]
        state = workflow_states.get(path) if "state" in requirement else None
        documents[path] = collect_document(
            client, repository, path, main_sha, state=state
        )
    normalized_workflows = validate_documents(
        documents,
        contract["expected"]["required_workflows"],
        kind="workflow",
    )
    normalized_surfaces = validate_documents(
        documents,
        contract["expected"]["governed_surfaces"],
        kind="governed surface",
    )

    selected_checks, all_checks = wait_for_check_runs(
        client,
        repository,
        main_sha,
        contract["expected"]["required_check_runs"],
        wait_seconds,
    )

    validation_run = contract["expected"]["security"]["validation_run"]
    _, jobs_payload = client.request(
        f"{base}/actions/runs/{validation_run}/jobs?per_page=100"
    )
    require(isinstance(jobs_payload, dict), "malformed CodeQL validation run")
    codeql_jobs = jobs_payload.get("jobs")
    require(isinstance(codeql_jobs, list), "CodeQL validation run lacks jobs")
    selected_codeql_jobs = validate_codeql_jobs(
        codeql_jobs, contract["expected"]["security"]["validation_jobs"]
    )

    _, repository_after = client.request(base)
    _, main_after = client.request(f"{base}/commits/{contract['branch']}")
    require(isinstance(repository_after, dict), "malformed final repository readback")
    require(isinstance(main_after, dict), "malformed final main readback")
    require(
        main_after.get("sha") == main_sha,
        "protected main moved during the readback",
    )
    require(
        repository_after == repository_before,
        "repository metadata changed during the readback",
    )

    receipt: dict[str, Any] = {
        "schema_version": "1.0.0",
        "operation_id": contract["operation_id"],
        "mode": "readback",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "api_version": contract["api_version"],
        "authority": contract["authority"],
        "owner_controls_evidence_merge": owner_controls_evidence_merge,
        "repository": repository,
        "actor": {
            "login": actor.get("login"),
            "id": actor.get("id"),
            "repository_admin": repository_before.get("permissions", {}).get("admin"),
        },
        "protected_main_before": main_sha,
        "protected_main_after": main_after.get("sha"),
        "ancestry": ancestry,
        "repository_settings": normalized_repository,
        "rulesets": {
            "protected_main": normalized_main_ruleset,
            "immutable_release_tags": normalized_tag_ruleset,
        },
        "security": security,
        "workflows": normalized_workflows,
        "governed_surfaces": normalized_surfaces,
        "protected_main_check_runs": selected_checks,
        "codeql_validation": {
            "run_id": validation_run,
            "jobs": selected_codeql_jobs,
        },
        "raw_readback": {
            "repository": repository_before,
            "ruleset_summaries": ruleset_summaries,
            "ruleset_details": ruleset_details,
            "security": security_raw,
            "workflow_states": workflow_states,
            "documents": {
                path: {
                    key: value
                    for key, value in row.items()
                    if key != "text"
                }
                for path, row in documents.items()
            },
            "all_protected_main_check_runs": all_checks,
            "codeql_validation_jobs": codeql_jobs,
        },
        "verified": True,
        "claim_boundaries": contract["claim_boundaries"],
        "request_contract": {
            "method": "GET only",
            "credentials_retained": False,
            "owner_controls_evidence_merge_required": True,
        },
    }
    scan_for_credentials(receipt)
    receipt["semantic_sha256"] = canonical_sha256(receipt)
    return receipt


def write_receipt(
    receipt: dict[str, Any],
    receipt_path: Path,
    digest_path: Path,
) -> tuple[str, str]:
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(receipt, indent=2, ensure_ascii=False) + "\n"
    receipt_path.write_text(payload, encoding="utf-8")
    file_digest = byte_sha256(payload.encode("utf-8"))
    digest_path.write_text(
        f"{file_digest}  {receipt_path.name}\n", encoding="ascii"
    )
    return receipt["semantic_sha256"], file_digest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contract", type=Path, default=DEFAULT_CONTRACT
    )
    parser.add_argument("--validate-contract", action="store_true")
    parser.add_argument("--owner-controls-evidence-merge")
    parser.add_argument("--output-directory", type=Path, default=Path("."))
    parser.add_argument("--wait-seconds", type=int)
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        contract = load_json(args.contract)
        validate_contract(contract)
        if args.validate_contract:
            print("QUANTUM full readback contract is valid")
            return 0
        if not args.owner_controls_evidence_merge:
            raise ReadbackError(
                "--owner-controls-evidence-merge is required for collection"
            )
        token = os.environ.get(args.token_env, "").strip() or gh_token()
        client = GitHubAPI(token, contract["api_version"])
        wait_seconds = (
            args.wait_seconds
            if args.wait_seconds is not None
            else contract["execution"]["wait_seconds_default"]
        )
        receipt = collect(
            client,
            contract,
            args.owner_controls_evidence_merge,
            wait_seconds,
        )
        receipt_path = args.output_directory / contract["output"]["receipt"]
        digest_path = args.output_directory / contract["output"]["digest"]
        semantic, file_digest = write_receipt(
            receipt, receipt_path, digest_path
        )
        print(json.dumps(receipt, indent=2, ensure_ascii=False))
        print(f"Semantic SHA-256: {semantic}")
        print(f"File SHA-256: {file_digest}")
        print(f"Receipt: {receipt_path.resolve()}")
        print(f"Digest: {digest_path.resolve()}")
        return 0
    except (OSError, json.JSONDecodeError, ReadbackError) as exc:
        print(f"QUANTUM full readback failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
