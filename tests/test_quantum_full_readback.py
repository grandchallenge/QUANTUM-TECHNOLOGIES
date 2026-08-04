from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "ci"))
SPEC = importlib.util.spec_from_file_location(
    "quantum_full_readback", ROOT / "ci" / "quantum_full_readback.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def contract() -> dict:
    return json.loads(
        (ROOT / "governance" / "quantum_full_readback_contract.json").read_text(
            encoding="utf-8"
        )
    )


def main_ruleset() -> dict:
    return {
        "id": 200,
        "name": "branch_protect",
        "target": "branch",
        "enforcement": "active",
        "source_type": "Repository",
        "bypass_actors": [],
        "conditions": {
            "ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}
        },
        "rules": [
            {"type": "deletion"},
            {"type": "non_fast_forward"},
            {
                "type": "pull_request",
                "parameters": {
                    "required_approving_review_count": 0,
                    "dismiss_stale_reviews_on_push": True,
                    "require_code_owner_review": False,
                    "require_last_push_approval": False,
                    "required_review_thread_resolution": True,
                    "allowed_merge_methods": ["merge", "squash"],
                },
            },
            {
                "type": "required_status_checks",
                "parameters": {
                    "strict_required_status_checks_policy": True,
                    "required_status_checks": [
                        {"context": "validate"},
                        {"context": "policy"},
                        {"context": "security / action-policy"},
                    ],
                },
            },
        ],
    }


def tag_ruleset() -> dict:
    return {
        "id": 20355165,
        "name": "Immutable release tags",
        "target": "tag",
        "enforcement": "active",
        "source_type": "Repository",
        "bypass_actors": [],
        "conditions": {
            "ref_name": {"include": ["refs/tags/*"], "exclude": []}
        },
        "rules": [{"type": "deletion"}, {"type": "non_fast_forward"}],
    }


class QuantumFullReadbackTests(unittest.TestCase):
    def test_contract_is_closed_and_valid(self) -> None:
        value = contract()
        MODULE.validate_contract(value)
        schema = json.loads(
            (ROOT / "schemas" / "quantum_full_readback_contract.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]), set(value))
        self.assertEqual(
            schema["properties"]["expected"]["const"], value["expected"]
        )

    def test_contract_rejects_authority_substitution(self) -> None:
        value = contract()
        value["authority"]["surfaces_merge"] = "0" * 40
        with self.assertRaises(MODULE.ReadbackError):
            MODULE.validate_contract(value)

    def test_contract_rejects_claim_inflation(self) -> None:
        value = contract()
        value["claim_boundaries"]["repository_conformance_claimed"] = True
        with self.assertRaisesRegex(MODULE.ReadbackError, "claim-boundary"):
            MODULE.validate_contract(value)

    def test_client_rejects_non_get_transport_before_network(self) -> None:
        client = MODULE.GitHubAPI("not-a-real-token", "2026-03-10")
        with self.assertRaisesRegex(MODULE.ReadbackError, "GET-only"):
            client.request("/user", method="PATCH")

    def test_repository_settings_validate_exactly(self) -> None:
        expected = contract()["expected"]["repository_settings"]
        repository = {
            **expected,
            "permissions": {"admin": True},
        }
        self.assertEqual(
            MODULE.validate_repository(repository, expected), expected
        )
        repository["delete_branch_on_merge"] = False
        with self.assertRaisesRegex(MODULE.ReadbackError, "settings drift"):
            MODULE.validate_repository(repository, expected)

    def test_protected_main_ruleset_validates(self) -> None:
        expected = contract()["expected"]["protected_main_ruleset"]
        observed = MODULE.validate_main_ruleset(main_ruleset(), expected)
        self.assertEqual(
            observed["required_status_checks"][
                "strict_required_status_checks_policy"
            ],
            True,
        )

    def test_protected_main_rejects_non_strict_checks(self) -> None:
        detail = main_ruleset()
        detail["rules"][3]["parameters"][
            "strict_required_status_checks_policy"
        ] = False
        with self.assertRaisesRegex(MODULE.ReadbackError, "strict-check"):
            MODULE.validate_main_ruleset(
                detail, contract()["expected"]["protected_main_ruleset"]
            )

    def test_protected_main_rejects_check_substitution(self) -> None:
        detail = main_ruleset()
        detail["rules"][3]["parameters"]["required_status_checks"][0][
            "context"
        ] = "replacement"
        with self.assertRaisesRegex(MODULE.ReadbackError, "required-check"):
            MODULE.validate_main_ruleset(
                detail, contract()["expected"]["protected_main_ruleset"]
            )

    def test_protected_main_rejects_bypass_actor(self) -> None:
        detail = main_ruleset()
        detail["bypass_actors"] = [{"actor_type": "Team", "actor_id": 1}]
        with self.assertRaisesRegex(MODULE.ReadbackError, "bypass"):
            MODULE.validate_main_ruleset(
                detail, contract()["expected"]["protected_main_ruleset"]
            )

    def test_tag_ruleset_validates_exactly(self) -> None:
        expected = contract()["expected"]["immutable_release_tag_ruleset"]
        observed = MODULE.validate_tag_ruleset(tag_ruleset(), expected)
        self.assertEqual(observed["id"], 20355165)

    def test_tag_ruleset_rejects_ref_drift(self) -> None:
        detail = tag_ruleset()
        detail["conditions"]["ref_name"]["include"] = ["refs/tags/v*"]
        with self.assertRaisesRegex(MODULE.ReadbackError, "tag ref"):
            MODULE.validate_tag_ruleset(
                detail, contract()["expected"]["immutable_release_tag_ruleset"]
            )

    def test_security_readback_validates(self) -> None:
        expected = contract()["expected"]["security"]
        observed = {
            "vulnerability_alerts": True,
            "dependabot_security_updates_enabled": True,
            "dependabot_security_updates_paused": False,
            "private_vulnerability_reporting": True,
            "codeql": {
                "state": "configured",
                "languages": ["actions", "python"],
                "query_suite": "extended",
                "threat_model": "remote",
                "runner": "standard",
            },
        }
        MODULE.validate_security(observed, expected)
        observed["codeql"]["query_suite"] = "default"
        with self.assertRaisesRegex(MODULE.ReadbackError, "query-suite"):
            MODULE.validate_security(observed, expected)

    def test_workflow_and_surface_content_fail_closed(self) -> None:
        requirements = [
            {
                "path": "a.yml",
                "state": "active",
                "required_fragments": ["required"],
                "git_blob_sha1": "a" * 40,
            }
        ]
        documents = {
            "a.yml": {
                "text": "required\n",
                "git_blob_sha1": "a" * 40,
                "size_bytes": 9,
                "sha256": "b" * 64,
                "state": "active",
            }
        }
        MODULE.validate_documents(documents, requirements, kind="workflow")
        documents["a.yml"]["text"] = "removed\n"
        with self.assertRaisesRegex(MODULE.ReadbackError, "content drift"):
            MODULE.validate_documents(documents, requirements, kind="workflow")

    def test_required_check_runs_need_success(self) -> None:
        names = contract()["expected"]["required_check_runs"]
        rows = [
            {
                "id": index,
                "name": name,
                "status": "completed",
                "conclusion": "success",
                "completed_at": f"2026-08-04T00:00:0{index}Z",
            }
            for index, name in enumerate(names, 1)
        ]
        self.assertEqual(len(MODULE.validate_check_runs(rows, names)), 3)
        rows[0]["conclusion"] = "failure"
        with self.assertRaisesRegex(MODULE.ReadbackError, "not successful"):
            MODULE.validate_check_runs(rows, names)

    def test_codeql_jobs_need_both_languages(self) -> None:
        expected = contract()["expected"]["security"]["validation_jobs"]
        rows = [
            {
                "id": 1,
                "name": "Analyze (actions)",
                "status": "completed",
                "conclusion": "success",
            },
            {
                "id": 2,
                "name": "Analyze (python)",
                "status": "completed",
                "conclusion": "success",
            },
        ]
        self.assertEqual(len(MODULE.validate_codeql_jobs(rows, expected)), 2)
        rows.pop()
        with self.assertRaisesRegex(MODULE.ReadbackError, "missing"):
            MODULE.validate_codeql_jobs(rows, expected)

    def test_ancestry_requires_exact_merge_base(self) -> None:
        base, head = "a" * 40, "b" * 40
        comparison = {
            "base_commit": {"sha": base},
            "head_commit": {"sha": head},
            "merge_base_commit": {"sha": base},
            "status": "ahead",
            "ahead_by": 3,
            "behind_by": 0,
        }
        MODULE.validate_ancestry(comparison, base, head, label="evidence")
        comparison["merge_base_commit"]["sha"] = "c" * 40
        with self.assertRaisesRegex(MODULE.ReadbackError, "not an ancestor"):
            MODULE.validate_ancestry(comparison, base, head, label="evidence")

    def test_receipt_credential_scan_fails_closed(self) -> None:
        MODULE.scan_for_credentials({"safe": True})
        with self.assertRaisesRegex(MODULE.ReadbackError, "credential"):
            MODULE.scan_for_credentials({"header": "Bearer secret"})

    def test_semantic_digest_is_key_order_stable(self) -> None:
        self.assertEqual(
            MODULE.canonical_sha256({"b": 2, "a": 1}),
            MODULE.canonical_sha256({"a": 1, "b": 2}),
        )

    def test_final_file_digest_binds_serialized_bytes(self) -> None:
        receipt = {"operation_id": "x", "semantic_sha256": "a" * 64}
        with tempfile.TemporaryDirectory() as directory:
            receipt_path = Path(directory) / "receipt.json"
            digest_path = Path(directory) / "receipt.json.sha256"
            semantic, file_digest = MODULE.write_receipt(
                receipt, receipt_path, digest_path
            )
            self.assertEqual(semantic, "a" * 64)
            self.assertEqual(
                file_digest,
                MODULE.byte_sha256(receipt_path.read_bytes()),
            )
            self.assertTrue(
                digest_path.read_text(encoding="ascii").startswith(file_digest)
            )


if __name__ == "__main__":
    unittest.main()
