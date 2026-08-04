from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ci"))

from schema_validation import SchemaValidationError, validate_instance

OP = 'GCL-GHOS-QUANTUM-OWNER-CONTROLS-001'
RECEIPT = ROOT / 'governance/settings-readback/evidence/GCL-GHOS-QUANTUM-OWNER-CONTROLS-001.receipt.json'
DIGEST = ROOT / 'governance/settings-readback/evidence/GCL-GHOS-QUANTUM-OWNER-CONTROLS-001.receipt.json.sha256'
SCHEMA = ROOT / 'governance/settings-readback/GCL-GHOS-QUANTUM-OWNER-CONTROLS-001.receipt.schema.json'
TAG_SOURCE = ROOT / 'governance/settings-readback/evidence/source/GCL-GHOS-QUANTUM-OWNER-CONTROLS-001.immutable-release-tags.receipt.json'
SECURITY_SOURCE = ROOT / 'governance/settings-readback/evidence/source/GCL-GHOS-QUANTUM-OWNER-CONTROLS-001.security-controls.receipt.json'
READBACK_SOURCE = ROOT / 'governance/settings-readback/evidence/source/GCL-GHOS-QUANTUM-OWNER-CONTROLS-001.protected-main-readback.json'

TAG_SHA = 'abb9380aa64387ae45c1078d9bc7612814c51a40968d7d204fc56ada50719067'
SECURITY_SHA = '318f527bfae3826f4b37cc7b50b1e28dbb89aaa43aead40ec40512a6606e7272'
READBACK_SHA = 'eb7894acb4de2e63134d8c5684c7073a3e5670b0fa21194f4bd3bd6ae15dbba4'
RECEIPT_SHA = '9eb34868b7f47759bf4210b4fc433c0942e602988a0b4bcd40745396bca6af04'


def canonical_bytes(value):
    return (
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def load_package():
    receipt_bytes = RECEIPT.read_bytes()
    receipt = json.loads(receipt_bytes)
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    return receipt_bytes, receipt, schema


def validate_semantics(receipt):
    assert receipt["operation_id"] == OP
    assert receipt["repository"] == "grandchallenge/QUANTUM-TECHNOLOGIES"
    assert receipt["actor"] == {
        "id": 17925951,
        "login": "fyremael",
        "repository_admin": True,
    }

    state = receipt["target_state"]
    assert state["protected_main"] == '260f469ba7349350c2b192a0e066a24aa670d611'
    assert state["repository_settings"] == {
        "allow_auto_merge": True,
        "allow_merge_commit": True,
        "allow_rebase_merge": False,
        "allow_squash_merge": True,
        "allow_update_branch": False,
        "delete_branch_on_merge": True,
    }

    main = state["protected_main_ruleset"]
    assert main["id"] == 20106953
    assert main["name"] == "branch_protect"
    assert main["target"] == "branch"
    assert main["enforcement"] == "active"
    assert main["bypass_actor_count"] == 0
    assert main["ref_include"] == ["~DEFAULT_BRANCH"]
    assert main["ref_exclude"] == []
    assert main["rule_types"] == [
        "deletion",
        "non_fast_forward",
        "pull_request",
        "required_status_checks",
    ]
    assert main["required_approving_review_count"] == 0
    assert main["dismiss_stale_reviews_on_push"] is True
    assert main["require_code_owner_review"] is False
    assert main["require_last_push_approval"] is False
    assert main["required_review_thread_resolution"] is True
    assert main["allowed_merge_methods"] == ["merge", "squash"]
    assert main["strict_required_status_checks_policy"] is True
    assert main["required_status_checks"] == [
        "policy",
        "security / action-policy",
        "validate",
    ]

    tag = state["immutable_release_tag_ruleset"]
    assert tag == {
        "bypass_actor_count": 0,
        "enforcement": "active",
        "id": 20355165,
        "name": "Immutable release tags",
        "ref_exclude": [],
        "ref_include": ["refs/tags/*"],
        "rule_types": ["deletion", "non_fast_forward"],
        "target": "tag",
    }

    security = state["security_controls"]
    assert security["vulnerability_alerts_and_dependency_graph_enabled"] is True
    assert security["dependabot_security_updates_enabled"] is True
    assert security["dependabot_security_updates_paused"] is False
    assert security["private_vulnerability_reporting_enabled"] is True
    assert security["codeql_state"] == "configured"
    assert security["codeql_languages"] == ["actions", "python"]
    assert security["codeql_query_suite"] == "extended"
    assert security["codeql_threat_model"] == "remote"
    assert security["codeql_runner_type"] == "standard"
    assert security["codeql_schedule"] == "weekly"

    codeql = state["codeql_validation"]
    assert codeql["run_id"] == 30883403446
    assert codeql["head_sha"] == '260f469ba7349350c2b192a0e066a24aa670d611'
    assert codeql["status"] == "completed"
    assert codeql["conclusion"] == "success"
    assert codeql["jobs"] == [
        {
            "conclusion": "success",
            "id": 91909321755,
            "name": "Analyze (actions)",
        },
        {
            "conclusion": "success",
            "id": 91909321786,
            "name": "Analyze (python)",
        },
    ]

    assert all(receipt["validation"].values())
    assert not any(receipt["boundaries"].values())


def validate_receipt(receipt, schema):
    validate_instance(receipt, schema)
    validate_semantics(receipt)


class OwnerControlsReceiptTests(unittest.TestCase):
    def test_canonical_receipt_and_companion_digest(self):
        receipt_bytes, receipt, _ = load_package()
        self.assertEqual(receipt_bytes, canonical_bytes(receipt))
        actual = hashlib.sha256(receipt_bytes).hexdigest()
        expected = DIGEST.read_text(encoding="ascii").split()[0]
        self.assertEqual(actual, RECEIPT_SHA)
        self.assertEqual(expected, RECEIPT_SHA)

    def test_source_evidence_digests(self):
        self.assertEqual(hashlib.sha256(TAG_SOURCE.read_bytes()).hexdigest(), TAG_SHA)
        self.assertEqual(
            hashlib.sha256(SECURITY_SOURCE.read_bytes()).hexdigest(),
            SECURITY_SHA,
        )
        self.assertEqual(
            hashlib.sha256(READBACK_SOURCE.read_bytes()).hexdigest(),
            READBACK_SHA,
        )

    def test_schema_and_semantics(self):
        _, receipt, schema = load_package()
        validate_receipt(receipt, schema)

    def test_source_records_match_consolidated_state(self):
        _, receipt, _ = load_package()
        tag = json.loads(TAG_SOURCE.read_bytes())
        security = json.loads(SECURITY_SOURCE.read_bytes())
        readback = json.loads(READBACK_SOURCE.read_bytes())

        self.assertEqual(tag["operation"], OP)
        self.assertEqual(tag["suboperation"], "immutable_release_tags")
        normalized_tag = {
            key: tag["ruleset"][key]
            for key in (
                "id",
                "name",
                "target",
                "enforcement",
                "bypass_actor_count",
                "ref_include",
                "ref_exclude",
                "rule_types",
            )
        }
        self.assertEqual(
            normalized_tag,
            receipt["target_state"]["immutable_release_tag_ruleset"],
        )
        self.assertFalse(any(tag["boundaries"].values()))

        self.assertEqual(security["operation"], OP)
        self.assertEqual(security["suboperation"], "security_controls")
        self.assertEqual(security["post_state"]["codeql_default_setup"]["state"], "configured")
        self.assertEqual(security["post_state"]["codeql_default_setup"]["languages"], ["actions", "python"])
        self.assertEqual(security["codeql"]["validation_run_id"], 30883403446)
        self.assertEqual(security["codeql"]["validation_run_conclusion"], "success")
        self.assertFalse(any(security["boundaries"].values()))

        self.assertEqual(readback["protected_main"], '260f469ba7349350c2b192a0e066a24aa670d611')
        self.assertEqual(
            readback["validated_target_state"]["repository_settings"],
            receipt["target_state"]["repository_settings"],
        )
        self.assertEqual(
            readback["validated_target_state"]["protected_main_ruleset"],
            receipt["target_state"]["protected_main_ruleset"],
        )
        self.assertEqual(
            readback["validated_target_state"]["immutable_release_tag_ruleset"],
            receipt["target_state"]["immutable_release_tag_ruleset"],
        )
        self.assertFalse(any(readback["boundaries"].values()))

    def assert_mutation_rejected(self, mutate):
        _, receipt, schema = load_package()
        mutant = copy.deepcopy(receipt)
        mutate(mutant)
        with self.assertRaises((SchemaValidationError, AssertionError)):
            validate_receipt(mutant, schema)

    def test_reject_authority_drift(self):
        self.assert_mutation_rejected(
            lambda value: value["authority"].__setitem__(
                "evidence_issue",
                "grandchallenge/QUANTUM-TECHNOLOGIES#999",
            )
        )

    def test_reject_merge_setting_drift(self):
        self.assert_mutation_rejected(
            lambda value: value["target_state"]["repository_settings"].__setitem__(
                "allow_rebase_merge",
                True,
            )
        )

    def test_reject_protected_main_ruleset_drift(self):
        self.assert_mutation_rejected(
            lambda value: value["target_state"]["protected_main_ruleset"].__setitem__(
                "strict_required_status_checks_policy",
                False,
            )
        )

    def test_reject_required_check_drift(self):
        self.assert_mutation_rejected(
            lambda value: value["target_state"]["protected_main_ruleset"][
                "required_status_checks"
            ].remove("security / action-policy")
        )

    def test_reject_release_tag_drift(self):
        self.assert_mutation_rejected(
            lambda value: value["target_state"]["immutable_release_tag_ruleset"].__setitem__(
                "bypass_actor_count",
                1,
            )
        )

    def test_reject_security_drift(self):
        self.assert_mutation_rejected(
            lambda value: value["target_state"]["security_controls"].__setitem__(
                "private_vulnerability_reporting_enabled",
                False,
            )
        )

    def test_reject_codeql_drift(self):
        self.assert_mutation_rejected(
            lambda value: value["target_state"]["codeql_validation"]["jobs"][1].__setitem__(
                "conclusion",
                "failure",
            )
        )

    def test_reject_claim_promotion(self):
        self.assert_mutation_rejected(
            lambda value: value["boundaries"].__setitem__(
                "quantum_advantage_proved",
                True,
            )
        )

    def test_no_credential_material(self):
        patterns = [
            re.compile(rb"\bghp_[A-Za-z0-9]{20,}\b"),
            re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
            re.compile(rb"(?i)\bauthorization\s*:\s*(?:bearer|token)\s+\S+"),
        ]
        for path in [RECEIPT, SCHEMA, TAG_SOURCE, SECURITY_SOURCE, READBACK_SOURCE]:
            content = path.read_bytes()
            for pattern in patterns:
                self.assertIsNone(pattern.search(content), str(path))


if __name__ == "__main__":
    unittest.main()
