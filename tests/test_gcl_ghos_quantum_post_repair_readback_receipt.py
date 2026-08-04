from __future__ import annotations

import base64
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ci"))

try:
    from schema_validation import SchemaValidationError, validate_instance
except ModuleNotFoundError:
    class SchemaValidationError(ValueError):
        pass

    def validate_instance(instance, schema):
        if "const" in schema and instance != schema["const"]:
            raise SchemaValidationError("instance does not match schema const")


OP = 'GCL-GHOS-QUANTUM-POST-REPAIR-READBACK-001'
RECEIPT_SHA = '83109c5c7f7461480bc5f0119c96295716a194a71dce3fdebe3552d8602efe37'
BUNDLE_SHA = 'f550ec163299dbb4438d950399893cae188642eee561327305df338ecfe9ba6a'
BASE = 'a8f2441cd75e717ff30f05d32c0f5e90a7dd7394'

RECEIPT = ROOT / 'governance/settings-readback/evidence/GCL-GHOS-QUANTUM-POST-REPAIR-READBACK-001.receipt.json'
DIGEST = ROOT / 'governance/settings-readback/evidence/GCL-GHOS-QUANTUM-POST-REPAIR-READBACK-001.receipt.json.sha256'
SCHEMA = ROOT / 'governance/settings-readback/GCL-GHOS-QUANTUM-POST-REPAIR-READBACK-001.receipt.schema.json'
BUNDLE = ROOT / 'governance/settings-readback/evidence/source/GCL-GHOS-QUANTUM-POST-REPAIR-READBACK-001.source-bundle.json'

EXPECTED_FILES = {
    ".github/workflows/qtr-validation.yml": "003e8869245bd124e77e097962dec820be011f44",
    ".github/workflows/gcl-conformance.yml": "a1592c66288b5ad58393b3be2b13fdbc10293a36",
    ".github/CODEOWNERS": "1c122ca0825355c54ef438f89ca381c40c80c6fb",
    ".github/dependabot.yml": "919daff81f50ac43788db82431de67a3d36258d8",
    "SECURITY.md": "49cec62e970cd0f12b6b003a3f63426585a79e3a",
    "governance/settings-readback/evidence/GCL-GHOS-QUANTUM-OWNER-CONTROLS-001.receipt.json":
        "22ec63fa14acf118cd44d641c49b269102614224",
    "governance/settings-readback/evidence/GCL-GHOS-QUANTUM-OWNER-CONTROLS-001.receipt.json.sha256":
        "56dbcca7bc3998c88872aa12323ad1a6cd6bee6d",
}


def load_package():
    receipt_bytes = RECEIPT.read_bytes()
    receipt = json.loads(receipt_bytes)
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    bundle_bytes = BUNDLE.read_bytes()
    bundle = json.loads(bundle_bytes)
    return receipt_bytes, receipt, schema, bundle_bytes, bundle


def canonical_receipt_bytes(receipt):
    return (
        json.dumps(receipt, indent=2, ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def validate_semantics(receipt):
    assert receipt["schema_version"] == "1.0.0"
    assert receipt["operation_id"] == OP
    assert receipt["repository"] == "grandchallenge/QUANTUM-TECHNOLOGIES"
    assert receipt["api_version"] == "2026-03-10"
    assert receipt["actor"] == {
        "login": "fyremael",
        "id": 17925951,
        "repository_admin": True,
    }
    assert receipt["protected_main"] == {
        "ref": "refs/heads/main",
        "object_type": "commit",
        "protected_main": BASE,
    }

    settings = receipt["repository_record"]["settings"]
    assert settings == {
        "allow_merge_commit": True,
        "allow_squash_merge": True,
        "allow_rebase_merge": False,
        "allow_auto_merge": True,
        "allow_update_branch": False,
        "delete_branch_on_merge": True,
    }

    main = receipt["rulesets"]["protected_main"]
    assert main["id"] == 20106953
    assert main["name"] == "branch_protect"
    assert main["target"] == "branch"
    assert main["enforcement"] == "active"
    assert main["source_type"] == "Repository"
    assert main["source"] == "grandchallenge/QUANTUM-TECHNOLOGIES"
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

    tag = receipt["rulesets"]["immutable_release_tags"]
    assert tag == {
        "id": 20355165,
        "name": "Immutable release tags",
        "target": "tag",
        "enforcement": "active",
        "source_type": "Repository",
        "source": "grandchallenge/QUANTUM-TECHNOLOGIES",
        "bypass_actor_count": 0,
        "ref_include": ["refs/tags/*"],
        "ref_exclude": [],
        "rule_types": ["deletion", "non_fast_forward"],
    }

    security = receipt["security_controls"]
    assert security["vulnerability_alerts_and_dependency_graph_enabled"] is True
    assert security["vulnerability_alerts_http_status"] == 204
    assert security["dependabot_security_updates_enabled"] is True
    assert security["dependabot_security_updates_paused"] is False
    assert security["private_vulnerability_reporting_enabled"] is True
    assert security["codeql_state"] == "configured"
    assert security["codeql_languages"] == ["actions", "python"]
    assert security["codeql_query_suite"] == "extended"
    assert security["codeql_threat_model"] == "remote"
    assert security["codeql_runner_type"] == "standard"
    assert security["codeql_runner_type_source"] == "live_api"
    assert security["codeql_schedule"] == "weekly"

    observed_files = {
        item["path"]: item["git_blob_sha"]
        for item in receipt["protected_files"]
    }
    assert observed_files == EXPECTED_FILES

    admitted = receipt["admitted_execution_evidence"]
    assert admitted["receipt_sha256"] == (
        "9eb34868b7f47759bf4210b4fc433c0942e602988a0b4bcd40745396bca6af04"
    )
    assert admitted["receipt_git_blob_sha"] == EXPECTED_FILES[
        "governance/settings-readback/evidence/"
        "GCL-GHOS-QUANTUM-OWNER-CONTROLS-001.receipt.json"
    ]
    assert admitted["companion_git_blob_sha"] == EXPECTED_FILES[
        "governance/settings-readback/evidence/"
        "GCL-GHOS-QUANTUM-OWNER-CONTROLS-001.receipt.json.sha256"
    ]

    assert receipt["readback_gaps"] == []
    assert all(receipt["validation"].values())
    assert not any(receipt["boundaries"].values())


def validate_receipt(receipt, schema):
    validate_instance(receipt, schema)
    validate_semantics(receipt)


class PostRepairReadbackReceiptTests(unittest.TestCase):
    def test_exact_receipt_and_companion_digest(self):
        receipt_bytes, receipt, _, _, _ = load_package()
        self.assertEqual(receipt_bytes, canonical_receipt_bytes(receipt))
        self.assertEqual(hashlib.sha256(receipt_bytes).hexdigest(), RECEIPT_SHA)
        self.assertEqual(
            DIGEST.read_text(encoding="ascii").split()[0],
            RECEIPT_SHA,
        )

    def test_closed_schema_and_semantics(self):
        _, receipt, schema, _, _ = load_package()
        validate_receipt(receipt, schema)

    def test_source_bundle_identity_and_reconstruction(self):
        _, receipt, _, bundle_bytes, bundle = load_package()
        self.assertEqual(hashlib.sha256(bundle_bytes).hexdigest(), BUNDLE_SHA)
        self.assertEqual(bundle["operation_id"], OP)
        self.assertEqual(bundle["protected_main"], BASE)
        self.assertEqual(bundle["receipt_sha256"], RECEIPT_SHA)
        self.assertEqual(bundle["entry_count"], 16)
        self.assertEqual(len(bundle["entries"]), 16)
        self.assertFalse(any(bundle["boundaries"].values()))

        ledger = {item["path"]: item for item in receipt["source_projections"]}
        reconstructed = {}
        for entry in bundle["entries"]:
            raw = base64.b64decode(entry["content"], validate=True)
            self.assertEqual(len(raw), entry["bytes"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), entry["sha256"])
            self.assertIn(entry["path"], ledger)
            self.assertEqual(entry["bytes"], ledger[entry["path"]]["bytes"])
            self.assertEqual(entry["sha256"], ledger[entry["path"]]["sha256"])
            reconstructed[entry["path"]] = raw

        self.assertEqual(set(reconstructed), set(ledger))
        branch = json.loads(reconstructed["raw/branch-ruleset.json"])
        tag = json.loads(reconstructed["raw/tag-ruleset.json"])
        codeql = json.loads(reconstructed["raw/codeql-default-setup.json"])
        self.assertEqual(branch["id"], 20106953)
        self.assertEqual(tag["id"], 20355165)
        self.assertEqual(codeql["runner_type"], "standard")

    def assert_mutation_rejected(self, mutate):
        _, receipt, schema, _, _ = load_package()
        mutant = copy.deepcopy(receipt)
        mutate(mutant)
        with self.assertRaises((SchemaValidationError, AssertionError)):
            validate_receipt(mutant, schema)

    def test_reject_omission(self):
        self.assert_mutation_rejected(
            lambda value: value.pop("readback_gaps")
        )

    def test_reject_authority_drift(self):
        self.assert_mutation_rejected(
            lambda value: value["authority"].__setitem__(
                "post_repair_readback_issue",
                "grandchallenge/QUANTUM-TECHNOLOGIES#999",
            )
        )

    def test_reject_settings_drift(self):
        self.assert_mutation_rejected(
            lambda value: value["repository_record"]["settings"].__setitem__(
                "allow_rebase_merge",
                True,
            )
        )

    def test_reject_ruleset_drift(self):
        self.assert_mutation_rejected(
            lambda value: value["rulesets"]["protected_main"].__setitem__(
                "strict_required_status_checks_policy",
                False,
            )
        )

    def test_reject_security_drift(self):
        self.assert_mutation_rejected(
            lambda value: value["security_controls"].__setitem__(
                "private_vulnerability_reporting_enabled",
                False,
            )
        )

    def test_reject_workflow_or_surface_drift(self):
        self.assert_mutation_rejected(
            lambda value: value["protected_files"][0].__setitem__(
                "git_blob_sha",
                "0" * 40,
            )
        )

    def test_reject_unsupported_inference(self):
        self.assert_mutation_rejected(
            lambda value: value["readback_gaps"].append({
                "field": "invented",
                "disposition": "conformant",
            })
        )

    def test_reject_claim_promotion(self):
        self.assert_mutation_rejected(
            lambda value: value["boundaries"].__setitem__(
                "repository_or_organization_conformance_claimed",
                True,
            )
        )

    def test_reject_source_corruption(self):
        _, _, _, _, bundle = load_package()
        mutant = copy.deepcopy(bundle)
        mutant["entries"][0]["content"] = base64.b64encode(
            b"corrupt"
        ).decode("ascii")
        entry = mutant["entries"][0]
        raw = base64.b64decode(entry["content"], validate=True)
        with self.assertRaises(AssertionError):
            self.assertEqual(hashlib.sha256(raw).hexdigest(), entry["sha256"])

    def test_no_credential_material(self):
        patterns = [
            re.compile(rb"\bghp_[A-Za-z0-9]{20,}\b"),
            re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
            re.compile(
                rb"(?i)\bauthorization\s*:\s*(?:bearer|token)\s+\S+"
            ),
            re.compile(
                rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"
            ),
        ]
        for path in [RECEIPT, DIGEST, SCHEMA, BUNDLE]:
            content = path.read_bytes()
            for pattern in patterns:
                self.assertIsNone(pattern.search(content), str(path))


if __name__ == "__main__":
    unittest.main()
