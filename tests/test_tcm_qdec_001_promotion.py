import copy
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEWED_HEAD = "cba814e5e5fb6db8fba7a8afd8211189a477eecb"
SCIENTIFIC_MERGE = "41524f805dce4f0c7b64b8e743b75a60b4f76773"
EVIDENCE_PAYLOAD = "1b19addcda5e04cf78a834b2162fe0873ed5eb15f3330995d8354906944b7122"
EXPECTED_OFFICES = {
    "Axiomatist": 5310035637,
    "Cartographer": 5310036055,
    "Grammarian": 5310036426,
    "Verifier": 5310036878,
    "Adversary": 5310037859,
    "Formalist": 5310038311,
    "Amanuensis": 5310038740,
    "Referee": 5310039669,
}
EXPECTED_REQUIRED_CHECKS = ["validate", "policy", "security / action-policy"]
REQUIRED_EXCLUSIONS = {
    "TCM-QDEC-002",
    "QLDPC-FORGE",
    "scalable tensor-network contraction or scalable TCM decoder",
    "general qLDPC decoder performance or practical superiority",
    "autonomous code, decoder, circuit, or architecture search",
}


def load_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def validate_promotion(promotion, intake):
    if promotion["record_id"] != "QTR-TCM-QDEC-REVIEW-001-PROMOTION":
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
        raise ValueError("evidence payload mismatch")
    if evidence["test_count"] != 92 or evidence["tcm_qdec_test_count"] != 13:
        raise ValueError("scientific replay count mismatch")
    referee = promotion["referee"]
    if referee["disposition"] != "APPROVE_BOUNDED_SCIENTIFIC_MERGE__TCM_QDEC_001":
        raise ValueError("Referee disposition mismatch")
    if referee["record"] != EXPECTED_OFFICES["Referee"]:
        raise ValueError("Referee record mismatch")
    if referee["live_ruleset_required_approving_reviews"] != 0:
        raise ValueError("live review requirement mismatch")
    protected = promotion["protected_merge"]
    if protected["ruleset_id"] != 20106953:
        raise ValueError("ruleset mismatch")
    if protected["required_status_checks"] != EXPECTED_REQUIRED_CHECKS:
        raise ValueError("required check set mismatch")
    if protected["review_threads_resolved"] is not True:
        raise ValueError("review thread condition mismatch")
    snapshot = promotion["reviewed_snapshot"]
    if snapshot["registry_status_at_review"] != "candidate_executable_not_promoted":
        raise ValueError("reviewed registry status mismatch")
    if snapshot["evidence_status_at_review"] != "candidate_executable_not_promoted":
        raise ValueError("reviewed evidence status mismatch")
    if snapshot["evidence_payload_sha256"] != EVIDENCE_PAYLOAD:
        raise ValueError("reviewed snapshot payload mismatch")
    if snapshot["snapshot_preserved_byte_for_byte"] is not True:
        raise ValueError("snapshot preservation missing")
    if not REQUIRED_EXCLUSIONS.issubset(set(promotion["excluded_scope"])):
        raise ValueError("downstream exclusion boundary weakened")
    ties = promotion["promoted_scope"]["tie_sensitivity"]
    if ties["min_plus_hamming"] != [218, 263]:
        raise ValueError("min-plus tie envelope changed")
    if intake["status"] != "candidate_executable_not_promoted":
        raise ValueError("reviewed intake status changed")
    if intake["review_cycle_status"] != "completed_referee_promoted":
        raise ValueError("review-cycle closure missing")
    if intake["reviewed_head"] != REVIEWED_HEAD:
        raise ValueError("intake reviewed head mismatch")
    if intake["scientific_merge_commit"] != SCIENTIFIC_MERGE:
        raise ValueError("intake scientific merge mismatch")


class TCMQDEC001PromotionTests(unittest.TestCase):
    def setUp(self):
        self.intake = load_json("reviews/QTR-TCM-QDEC-REVIEW-001/intake.json")
        self.promotion = load_json("reviews/QTR-TCM-QDEC-REVIEW-001/promotion-record.json")

    def test_promotion_overlay_matches_immutable_scientific_snapshot(self):
        validate_promotion(self.promotion, self.intake)
        registry = load_json("registry/tcm-qdec.json")
        experiment = registry["experiments"][0]
        evidence = load_json("evidence/TCM-QDEC-001-report.json")
        work_package = (ROOT / "work-packages" / "QTR-TCM-QDEC-001.md").read_text(encoding="utf-8")
        self.assertEqual(experiment["experiment_id"], "TCM-QDEC-001")
        self.assertEqual(experiment["status"], "candidate_executable_not_promoted")
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

    def test_tie_envelope_tamper_fails_closed(self):
        promotion = copy.deepcopy(self.promotion)
        promotion["promoted_scope"]["tie_sensitivity"]["min_plus_hamming"] = [226, 226]
        with self.assertRaises(ValueError):
            validate_promotion(promotion, self.intake)

    def test_downstream_authority_exclusion_tamper_fails_closed(self):
        promotion = copy.deepcopy(self.promotion)
        promotion["excluded_scope"].remove("TCM-QDEC-002")
        with self.assertRaises(ValueError):
            validate_promotion(promotion, self.intake)


if __name__ == "__main__":
    unittest.main()
