import copy
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEWED_HEAD = "e7b2eb0060e51d4157a6666f2e857c1fb19aaff1"
SCIENTIFIC_MERGE = "51c31bde2e0630314d3d48dceb9b92969c37c228"
PREDECESSOR_PAYLOAD = "6c2095f48762178bf0fe5c2b5fce8299261733912a1cccc7884d11f344718427"
EVIDENCE_PAYLOAD = "d98c5d73f7fdf9259a35be60580dc9b6c32c5e4483cd765ed0dcba594b9299e5"
CORPUS_DIGEST = "260b1a43cf1d777f28c475918e91a5f7cefc5d28a2bfb556338f7e30058f58a8"
DECODER_DIGEST = "96ce94c378b7b1fc5fe032fbd253aa932c1ca8abcb17b3d3c89b3ecda601da29"
SOURCE_BLOB = "df82b3a6aa17b969a50b1b143cc10136cb24547f"

EXPECTED_OFFICES = {
    "Axiomatist": 5306871426,
    "Cartographer": 5306872120,
    "Grammarian": 5306872830,
    "Verifier": 5306874672,
    "Adversary": 5306876505,
    "Formalist": 5306877250,
    "Amanuensis": 5306877837,
    "Referee": 5306878917,
}

EXPECTED_REQUIRED_CHECKS = [
    "validate",
    "policy",
    "security / action-policy",
]

REQUIRED_EXCLUSIONS = {
    "experimental-data reproduction",
    "circuit-level or Pauli+ noise-model validation",
    "BP-OSD performance or superiority",
    "Kunlun hardware validation",
    "threshold or pseudo-threshold claims",
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
        "tracking_issue",
        "review_issue",
        "documentary_issue",
        "predecessor",
        "workflow_evidence",
        "source_context_lock",
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
    if promotion["record_id"] != "QTR-QLDPC-REVIEW-002-PROMOTION":
        raise ValueError("promotion record identity mismatch")
    if promotion["status"] != "referee_promoted_bounded":
        raise ValueError("promotion status mismatch")
    if promotion["reviewed_head"] != REVIEWED_HEAD:
        raise ValueError("reviewed head mismatch")
    if promotion["scientific_merge_commit"] != SCIENTIFIC_MERGE:
        raise ValueError("scientific merge mismatch")
    if promotion["office_records"] != EXPECTED_OFFICES:
        raise ValueError("office record mismatch")

    predecessor = promotion["predecessor"]
    if predecessor["fixture_id"] != "QLDPC-FIXTURE-001":
        raise ValueError("predecessor fixture mismatch")
    if predecessor["evidence_payload_sha256"] != PREDECESSOR_PAYLOAD:
        raise ValueError("predecessor payload mismatch")

    evidence = promotion["workflow_evidence"]
    if evidence["evidence_payload_sha256"] != EVIDENCE_PAYLOAD:
        raise ValueError("reviewed evidence payload mismatch")
    if evidence["corpus_sha256"] != CORPUS_DIGEST:
        raise ValueError("corpus digest mismatch")
    if evidence["exact_decoder_table_sha256"] != DECODER_DIGEST:
        raise ValueError("decoder table digest mismatch")
    if evidence["test_count"] != 74:
        raise ValueError("scientific exact-head test count mismatch")
    if evidence["codeql_conclusion"] != "success":
        raise ValueError("CodeQL conclusion mismatch")

    source_lock = promotion["source_context_lock"]
    if source_lock["experiment_decoder_git_ref"] != "v1.1.3":
        raise ValueError("source tag mismatch")
    if source_lock["experiment_decoder_git_blob_sha"] != SOURCE_BLOB:
        raise ValueError("source blob mismatch")
    if source_lock["executed_by_fixture"] is not False:
        raise ValueError("source execution boundary changed")

    referee = promotion["referee"]
    if referee["disposition"] != "APPROVE_BOUNDED_SCIENTIFIC_MERGE__QLDPC_FIXTURE_002_R2":
        raise ValueError("Referee disposition mismatch")
    if referee["record"] != EXPECTED_OFFICES["Referee"]:
        raise ValueError("Referee record mismatch")
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
    if snapshot["corpus_sha256"] != CORPUS_DIGEST:
        raise ValueError("reviewed snapshot corpus mismatch")
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


class QLDPCFixture002PromotionTests(unittest.TestCase):
    def setUp(self):
        self.intake = load_json("reviews/QTR-QLDPC-REVIEW-002/intake.json")
        self.promotion = load_json("reviews/QTR-QLDPC-REVIEW-002/promotion-record.json")

    def test_promotion_overlay_matches_immutable_reviewed_snapshot(self):
        validate_promotion(self.promotion, self.intake)
        registry = load_json("registry/qldpc-benchmarks.json")
        benchmark = registry["benchmarks"][0]
        evidence = load_json("evidence/QLDPC-FIXTURE-002-report.json")
        work_package = (ROOT / "work-packages" / "QTR-QLDPC-FIXTURE-002.md").read_text(
            encoding="utf-8"
        )

        self.assertEqual(benchmark["fixture_id"], "QLDPC-FIXTURE-002")
        self.assertEqual(benchmark["status"], "candidate_executable_not_promoted")
        self.assertEqual(evidence["status"], "candidate_executable_not_promoted")
        self.assertEqual(evidence["payload_sha256"], EVIDENCE_PAYLOAD)
        self.assertEqual(evidence["corpus"]["corpus_sha256"], CORPUS_DIGEST)
        self.assertEqual(
            benchmark["source_context"]["experiment_decoder"]["git_blob_sha"], SOURCE_BLOB
        )
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

    def test_source_blob_tamper_fails_closed(self):
        promotion = copy.deepcopy(self.promotion)
        promotion["source_context_lock"]["experiment_decoder_git_blob_sha"] = "0" * 40
        with self.assertRaises(ValueError):
            validate_promotion(promotion, self.intake)

    def test_downstream_authority_exclusion_tamper_fails_closed(self):
        promotion = copy.deepcopy(self.promotion)
        promotion["excluded_scope"].remove("TCM-QDEC")
        with self.assertRaises(ValueError):
            validate_promotion(promotion, self.intake)


if __name__ == "__main__":
    unittest.main()
