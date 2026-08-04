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

from schema_validation import SchemaValidationError, validate_instance

OP = "GCL-GHOS-QUANTUM-POST-REPAIR-READBACK-001"
BASE = "a8f2441cd75e717ff30f05d32c0f5e90a7dd7394"
RECEIPT_SHA = "83109c5c7f7461480bc5f0119c96295716a194a71dce3fdebe3552d8602efe37"
BUNDLE_SHA = "2bae1813706334f7571c144fa647da3ce2b9c9e791d5653246d34cc180179cae"

RECEIPT = ROOT / "governance/settings-readback/evidence/GCL-GHOS-QUANTUM-POST-REPAIR-READBACK-001.receipt.json"
DIGEST = ROOT / "governance/settings-readback/evidence/GCL-GHOS-QUANTUM-POST-REPAIR-READBACK-001.receipt.json.sha256"
SCHEMA = ROOT / "governance/settings-readback/GCL-GHOS-QUANTUM-POST-REPAIR-READBACK-001.receipt.schema.json"
BUNDLE = ROOT / "governance/settings-readback/evidence/source/GCL-GHOS-QUANTUM-POST-REPAIR-READBACK-001.source-bundle.json"

EXPECTED_FILES = {
    ".github/workflows/qtr-validation.yml": "003e8869245bd124e77e097962dec820be011f44",
    ".github/workflows/gcl-conformance.yml": "a1592c66288b5ad58393b3be2b13fdbc10293a36",
    ".github/CODEOWNERS": "1c122ca0825355c54ef438f89ca381c40c80c6fb",
    ".github/dependabot.yml": "919daff81f50ac43788db82431de67a3d36258d8",
    "SECURITY.md": "49cec62e970cd0f12b6b003a3f63426585a79e3a",
    "governance/settings-readback/evidence/GCL-GHOS-QUANTUM-OWNER-CONTROLS-001.receipt.json": "22ec63fa14acf118cd44d641c49b269102614224",
    "governance/settings-readback/evidence/GCL-GHOS-QUANTUM-OWNER-CONTROLS-001.receipt.json.sha256": "56dbcca7bc3998c88872aa12323ad1a6cd6bee6d",
}


def load():
    receipt_bytes = RECEIPT.read_bytes()
    receipt = json.loads(receipt_bytes)
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    bundle_bytes = BUNDLE.read_bytes()
    bundle = json.loads(bundle_bytes)
    return receipt_bytes, receipt, schema, bundle_bytes, bundle


def validate_semantics(receipt):
    assert receipt["operation_id"] == OP
    assert receipt["protected_main"]["protected_main"] == BASE
    assert receipt["actor"] == {
        "login": "fyremael",
        "id": 17925951,
        "repository_admin": True,
    }
    assert receipt["repository_record"]["settings"] == {
        "allow_merge_commit": True,
        "allow_squash_merge": True,
        "allow_rebase_merge": False,
        "allow_auto_merge": True,
        "allow_update_branch": False,
        "delete_branch_on_merge": True,
    }
    main = receipt["rulesets"]["protected_main"]
    assert main["id"] == 20106953
    assert main["bypass_actor_count"] == 0
    assert main["dismiss_stale_reviews_on_push"] is True
    assert main["required_review_thread_resolution"] is True
    assert main["allowed_merge_methods"] == ["merge", "squash"]
    assert main["strict_required_status_checks_policy"] is True
    assert main["required_status_checks"] == [
        "policy",
        "security / action-policy",
        "validate",
    ]
    tag = receipt["rulesets"]["immutable_release_tags"]
    assert tag["id"] == 20355165
    assert tag["bypass_actor_count"] == 0
    assert tag["ref_include"] == ["refs/tags/*"]
    assert tag["rule_types"] == ["deletion", "non_fast_forward"]
    sec = receipt["security_controls"]
    assert sec["vulnerability_alerts_and_dependency_graph_enabled"] is True
    assert sec["dependabot_security_updates_enabled"] is True
    assert sec["dependabot_security_updates_paused"] is False
    assert sec["private_vulnerability_reporting_enabled"] is True
    assert sec["codeql_languages"] == ["actions", "python"]
    assert sec["codeql_query_suite"] == "extended"
    assert sec["codeql_threat_model"] == "remote"
    assert sec["codeql_runner_type"] == "standard"
    assert {item["path"]: item["git_blob_sha"] for item in receipt["protected_files"]} == EXPECTED_FILES
    assert receipt["readback_gaps"] == []
    assert all(receipt["validation"].values())
    assert not any(receipt["boundaries"].values())


def validate_receipt(receipt, schema):
    validate_instance(receipt, schema)
    validate_semantics(receipt)


class PostRepairReadbackReceiptTests(unittest.TestCase):
    def test_exact_receipt_schema_and_digest(self):
        receipt_bytes, receipt, schema, _, _ = load()
        self.assertEqual(hashlib.sha256(receipt_bytes).hexdigest(), RECEIPT_SHA)
        self.assertEqual(DIGEST.read_text(encoding="ascii").split()[0], RECEIPT_SHA)
        validate_receipt(receipt, schema)

    def test_source_bundle_identity_and_reconstruction(self):
        _, receipt, _, bundle_bytes, bundle = load()
        self.assertEqual(hashlib.sha256(bundle_bytes).hexdigest(), BUNDLE_SHA)
        self.assertEqual(bundle["operation_id"], OP)
        self.assertEqual(bundle["protected_main"], BASE)
        self.assertEqual(bundle["receipt_sha256"], RECEIPT_SHA)
        self.assertEqual(bundle["entry_count"], 16)
        self.assertEqual(len(bundle["entries"]), 16)
        self.assertFalse(any(bundle["boundaries"].values()))

        ledger = {item["path"]: item for item in receipt["source_projections"]}
        seen = set()
        for entry in bundle["entries"]:
            raw = base64.b64decode(entry["content"], validate=True)
            self.assertEqual(len(raw), entry["bytes"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), entry["sha256"])
            self.assertIn(entry["path"], ledger)
            self.assertEqual(entry["bytes"], ledger[entry["path"]]["bytes"])
            self.assertEqual(entry["sha256"], ledger[entry["path"]]["sha256"])
            seen.add(entry["path"])
        self.assertEqual(seen, set(ledger))

    def assert_mutation_rejected(self, mutate):
        _, receipt, schema, _, _ = load()
        mutant = copy.deepcopy(receipt)
        mutate(mutant)
        with self.assertRaises((SchemaValidationError, AssertionError)):
            validate_receipt(mutant, schema)

    def test_reject_omission_and_authority_drift(self):
        self.assert_mutation_rejected(lambda v: v.pop("readback_gaps"))
        self.assert_mutation_rejected(
            lambda v: v["authority"].__setitem__(
                "post_repair_readback_issue",
                "grandchallenge/QUANTUM-TECHNOLOGIES#999",
            )
        )

    def test_reject_settings_ruleset_and_security_drift(self):
        self.assert_mutation_rejected(
            lambda v: v["repository_record"]["settings"].__setitem__(
                "allow_rebase_merge", True
            )
        )
        self.assert_mutation_rejected(
            lambda v: v["rulesets"]["protected_main"].__setitem__(
                "strict_required_status_checks_policy", False
            )
        )
        self.assert_mutation_rejected(
            lambda v: v["security_controls"].__setitem__(
                "private_vulnerability_reporting_enabled", False
            )
        )

    def test_reject_workflow_drift_unsupported_inference_and_claim_promotion(self):
        self.assert_mutation_rejected(
            lambda v: v["protected_files"][0].__setitem__(
                "git_blob_sha", "0" * 40
            )
        )
        self.assert_mutation_rejected(
            lambda v: v["readback_gaps"].append(
                {"field": "invented", "disposition": "conformant"}
            )
        )
        self.assert_mutation_rejected(
            lambda v: v["boundaries"].__setitem__(
                "repository_or_organization_conformance_claimed", True
            )
        )

    def test_reject_source_corruption(self):
        _, _, _, _, bundle = load()
        mutant = copy.deepcopy(bundle)
        mutant["entries"][0]["content"] = base64.b64encode(b"corrupt").decode("ascii")
        entry = mutant["entries"][0]
        raw = base64.b64decode(entry["content"], validate=True)
        with self.assertRaises(AssertionError):
            self.assertEqual(hashlib.sha256(raw).hexdigest(), entry["sha256"])

    def test_no_credential_material(self):
        patterns = [
            re.compile(rb"\bghp_[A-Za-z0-9]{20,}\b"),
            re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
            re.compile(rb"(?i)\bauthorization\s*:\s*(?:bearer|token)\s+\S+"),
            re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
        ]
        for path in (RECEIPT, DIGEST, SCHEMA, BUNDLE):
            content = path.read_bytes()
            for pattern in patterns:
                self.assertIsNone(pattern.search(content), str(path))


if __name__ == "__main__":
    unittest.main()
