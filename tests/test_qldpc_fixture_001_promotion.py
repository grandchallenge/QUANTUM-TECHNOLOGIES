import copy
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEWED_HEAD = "a024afb5b3428f49c34d905625f8c56f466528e7"
SCIENTIFIC_MERGE = "b899894cfe17680d556d32ff36e51683cd9f6b32"
EVIDENCE_PAYLOAD = "6c2095f48762178bf0fe5c2b5fce8299261733912a1cccc7884d11f344718427"
DECODER_DIGEST = "96ce94c378b7b1fc5fe032fbd253aa932c1ca8abcb17b3d3c89b3ecda601da29"

EXPECTED_OFFICES = {
    "Axiomatist": 5306485934,
    "Cartographer": 5306486331,
    "Grammarian": 5306486803,
    "Verifier": 5306487235,
    "Adversary": 5306488453,
    "Formalist": 5306489043,
    "Amanuensis": 5306489589,
    "Referee": 5306491335,
}

EXPECTED_REQUIRED_CHECKS = [
    "validate",
    "policy",
    "security / action-policy",
]

REQUIRED_EXCLUSIONS = {
    "QLDPC-FIXTURE-002",
    "TCM-QDEC",
    "QLDPC-FORGE",
    "autonomous code, decoder, circuit, or architecture search",
}


def load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def validate_promotion(promotion, intake):
    expected_promotion_keys = {
        "record_version",
        "record_id",
        "status",
        "reviewed_head",
        "scientific_merge_commit",
        "pull_request",
        "review_issue",
        "documentary_issue",
        "workflow_evidence",
        "office_records",
        "referee",
        "protected_merge",
        "promoted_scope",
        "reviewed_snapshot",
        "excluded_scope",
    }
    if set(promotion) != expected_promotion_keys:
        raise ValueError("promotion record key-set mismatch")
    if promotion["record_version"] != "0.1.0":
        raise ValueError("promotion record version mismatch")
    if promotion["record_id"] != "QTR-QLDPC-REVIEW-001-PROMOTION":
        raise ValueError("promotion record identity mismatch")
    if promotion["status"] != "referee_promoted_bounded":
        raise ValueError("promotion status mismatch")
    if promotion["reviewed_head"] != REVIEWED_HEAD:
        raise ValueError("reviewed head mismatch")
    if promotion["scientific_merge_commit"] != SCIENTIFIC_MERGE:
        raise ValueError("scientific merge mismatch")
    if promotion["office_records"] != EXPECTED_OFFICES:
        raise ValueError("office record mismatch")

    evidence = promotion["workflow_evidence"]
    if evidence["evidence_payload_sha256"] != EVIDENCE_PAYLOAD:
        raise ValueError("reviewed evidence payload mismatch")
    if evidence["decoder_table_sha256"] != DECODER_DIGEST:
        raise ValueError("decoder table digest mismatch")
    if evidence["test_count"] != 61:
        raise ValueError("scientific exact-head test count mismatch")

    referee = promotion["referee"]
    if referee["disposition"] != "APPROVE_BOUNDED_SCIENTIFIC_MERGE__QLDPC_FIXTURE_001_R2":
        raise ValueError("Referee disposition mismatch")
    if referee["record"] != EXPECTED_OFFICES["Referee"]:
        raise ValueError("Referee record mismatch")
    if referee["submitted_pull_request_review"] is not None:
        raise ValueError("unexpected submitted PR review")
    if referee["live_ruleset_required_approving_reviews"] != 0:
        raise ValueError("live review requirement mismatch")

    protected = promotion["protected_merge"]
    if protected["ruleset_id"] != 20106953:
        raise ValueError("ruleset mismatch")
    if protected["required_status_checks"] != EXPECTED_REQUIRED_CHECKS:
        raise ValueError("required status-check set mismatch")
    if protected["review_threads_resolved"] is not True:
        raise ValueError("review threads were not resolved")

    snapshot = promotion["reviewed_snapshot"]
    if snapshot["registry_status_at_review"] != "candidate_executable_not_promoted":
        raise ValueError("reviewed registry status mismatch")
    if snapshot["evidence_status_at_review"] != "candidate_executable_not_promoted":
        raise ValueError("reviewed evidence status mismatch")
    if snapshot["evidence_payload_sha256"] != EVIDENCE_PAYLOAD:
        raise ValueError("reviewed snapshot payload mismatch")
    if snapshot["snapshot_preserved_byte_for_byte"] is not True:
        raise ValueError("reviewed snapshot preservation missing")

    if not REQUIRED_EXCLUSIONS.issubset(set(promotion["excluded_scope"])):
        raise ValueError("downstream exclusion boundary weakened")

    if intake["status"] != "candidate_executable_not_promoted":
        raise ValueError("reviewed intake status changed")
    if intake["review_cycle_status"] != "completed_referee_promoted":
        raise ValueError("review cycle closure missing")
    if intake["reviewed_head"] != REVIEWED_HEAD:
        raise ValueError("intake reviewed head mismatch")
    if intake["scientific_merge_commit"] != SCIENTIFIC_MERGE:
        raise ValueError("intake scientific merge mismatch")
    if intake["referee_record"] != EXPECTED_OFFICES["Referee"]:
        raise ValueError("intake Referee record mismatch")
    if not REQUIRED_EXCLUSIONS.issubset(set(intake["excluded_scope"])):
        raise ValueError("intake exclusion boundary weakened")


class QLDPCFixture001PromotionTests(unittest.TestCase):
    def setUp(self):
        self.intake = load_json("reviews/QTR-QLDPC-REVIEW-001/intake.json")
        self.promotion = load_json("reviews/QTR-QLDPC-REVIEW-001/promotion-record.json")

    def test_promotion_overlay_matches_immutable_reviewed_snapshot(self):
        validate_promotion(self.promotion, self.intake)
        registry = load_json("registry/qldpc-fixtures.json")
        fixture = registry["fixtures"][0]
        evidence = load_json("evidence/QLDPC-FIXTURE-001-report.json")
        work_package = (ROOT / "work-packages" / "QTR-QLDPC-FIXTURE-001.md").read_text(
            encoding="utf-8"
        )

        self.assertEqual(fixture["fixture_id"], "QLDPC-FIXTURE-001")
        self.assertEqual(fixture["status"], "candidate_executable_not_promoted")
        self.assertEqual(evidence["status"], "candidate_executable_not_promoted")
        self.assertEqual(evidence["payload_sha256"], EVIDENCE_PAYLOAD)
        self.assertIn("Status: `referee_promoted_bounded`", work_package)
        self.assertIn(REVIEWED_HEAD, work_package)
        self.assertIn(SCIENTIFIC_MERGE, work_package)

    def test_reviewed_head_tamper_fails_closed(self):
        promotion = copy.deepcopy(self.promotion)
        promotion["reviewed_head"] = "0" * 40
        with self.assertRaises(ValueError):
            validate_promotion(promotion, self.intake)

    def test_snapshot_preservation_tamper_fails_closed(self):
        promotion = copy.deepcopy(self.promotion)
        promotion["reviewed_snapshot"]["snapshot_preserved_byte_for_byte"] = False
        with self.assertRaises(ValueError):
            validate_promotion(promotion, self.intake)

    def test_downstream_authority_exclusion_tamper_fails_closed(self):
        promotion = copy.deepcopy(self.promotion)
        promotion["excluded_scope"].remove("TCM-QDEC")
        with self.assertRaises(ValueError):
            validate_promotion(promotion, self.intake)


if __name__ == "__main__":
    unittest.main()
