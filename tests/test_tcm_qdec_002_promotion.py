import copy
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_REVIEWED_HEAD = "9123a9c6cc2c163031d8bff0c46e0a9dd4c8f8fd"
EXPECTED_SCIENTIFIC_MERGE = "d3340c91df3aa72dc5c7ba75906128c8eef2e174"
EXPECTED_PAYLOAD = "efd9e76957421494897e2cc319137874b61093d66ea871f0202df3d07e6eb3c0"
EXPECTED_REGISTRY_BLOB = "e112e4cace80caf7d40c504eb9944d31e3c0ec21"
EXPECTED_EVIDENCE_BLOB = "9d759709ee67da8fb064f674f34068d2134cfc15"


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def canonical_digest(payload):
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_overlay(promotion, intake, registry, evidence, registry_raw, evidence_raw):
    if promotion.get("record_id") != "QTR-TCM-QDEC-REVIEW-002-PROMOTION":
        raise ValueError("promotion identity mismatch")
    if promotion.get("status") != "referee_promoted_bounded":
        raise ValueError("bounded promotion status missing")
    if promotion.get("reviewed_head") != EXPECTED_REVIEWED_HEAD:
        raise ValueError("reviewed head mismatch")
    if promotion.get("scientific_merge_commit") != EXPECTED_SCIENTIFIC_MERGE:
        raise ValueError("scientific merge mismatch")
    if intake.get("status") != "candidate_executable_not_promoted":
        raise ValueError("review intake rewrote scientific status")
    if intake.get("review_cycle_status") != "completed_referee_promoted":
        raise ValueError("review cycle not closed")
    if registry.get("registry_version") != "0.1.0" or len(registry.get("experiments", [])) != 1:
        raise ValueError("reviewed registry shape changed")
    experiment = registry["experiments"][0]
    if experiment.get("experiment_id") != "TCM-QDEC-002":
        raise ValueError("reviewed experiment identity changed")
    if experiment.get("status") != "candidate_executable_not_promoted":
        raise ValueError("reviewed registry status changed")
    if evidence.get("experiment_id") != "TCM-QDEC-002":
        raise ValueError("reviewed evidence identity changed")
    if evidence.get("status") != "candidate_executable_not_promoted":
        raise ValueError("reviewed evidence status changed")
    if evidence.get("payload_sha256") != EXPECTED_PAYLOAD:
        raise ValueError("reviewed evidence payload changed")
    unsigned = dict(evidence)
    unsigned.pop("payload_sha256", None)
    if canonical_digest(unsigned) != EXPECTED_PAYLOAD:
        raise ValueError("reviewed evidence no longer self-verifies")

    snapshot = promotion.get("reviewed_snapshot", {})
    if snapshot.get("snapshot_preserved_byte_for_byte") is not True:
        raise ValueError("snapshot preservation assertion missing")
    if snapshot.get("registry_blob_sha") != EXPECTED_REGISTRY_BLOB:
        raise ValueError("recorded registry blob changed")
    if snapshot.get("evidence_blob_sha") != EXPECTED_EVIDENCE_BLOB:
        raise ValueError("recorded evidence blob changed")
    if git_blob_sha(registry_raw) != EXPECTED_REGISTRY_BLOB:
        raise ValueError("actual registry blob changed")
    if git_blob_sha(evidence_raw) != EXPECTED_EVIDENCE_BLOB:
        raise ValueError("actual evidence blob changed")
    if snapshot.get("evidence_payload_sha256") != EXPECTED_PAYLOAD:
        raise ValueError("snapshot payload changed")

    factor = promotion.get("factorization_evidence", {})
    if factor.get("combined_check_logical_rank") != 11:
        raise ValueError("combined rank changed")
    if factor.get("reachable_combined_labels") != 2048:
        raise ValueError("reachable label count changed")
    if factor.get("peak_active_state_count") != 2048:
        raise ValueError("finite support diagnostic changed")
    if factor.get("transition_relaxations_per_algebra") != 32766:
        raise ValueError("transition count changed")

    promoted = promotion.get("promoted_scope", {})
    if promoted.get("tie_sensitivity", {}).get("min_plus_hamming") != [218, 263]:
        raise ValueError("min-plus ambiguity envelope changed")
    if promoted.get("frozen_corpus_success_totals") != {
        "sum_product_bsc_p_0_1": 263,
        "soft_tropical_base_2": 262,
        "min_plus_hamming": 226,
    }:
        raise ValueError("frozen success totals changed")

    excluded = set(promotion.get("excluded_scope", []))
    required_exclusions = {
        "scalable tensor-network or transfer decoding",
        "bounded contraction width for a qLDPC code family",
        "asymptotic or practical complexity advantage",
        "TCM-QDEC-003",
        "QLDPC-FORGE",
        "autonomous code, decoder, circuit, or architecture search",
    }
    if not required_exclusions <= excluded:
        raise ValueError("downstream exclusion missing")


class TCMQDEC002PromotionTests(unittest.TestCase):
    def setUp(self):
        self.promotion = json.loads(
            (ROOT / "reviews" / "QTR-TCM-QDEC-REVIEW-002" / "promotion-record.json").read_text()
        )
        self.intake = json.loads(
            (ROOT / "reviews" / "QTR-TCM-QDEC-REVIEW-002" / "intake.json").read_text()
        )
        self.registry_path = ROOT / "registry" / "tcm-qdec-002.json"
        self.evidence_path = ROOT / "evidence" / "TCM-QDEC-002-report.json"
        self.registry_raw = self.registry_path.read_bytes()
        self.evidence_raw = self.evidence_path.read_bytes()
        self.registry = json.loads(self.registry_raw)
        self.evidence = json.loads(self.evidence_raw)

    def check(self, promotion=None, intake=None):
        validate_overlay(
            promotion or self.promotion,
            intake or self.intake,
            self.registry,
            self.evidence,
            self.registry_raw,
            self.evidence_raw,
        )

    def test_promotion_overlay_matches_immutable_scientific_snapshot(self):
        self.check()

    def test_reviewed_head_tamper_fails_closed(self):
        promotion = copy.deepcopy(self.promotion)
        promotion["reviewed_head"] = "0" * 40
        with self.assertRaises(ValueError):
            self.check(promotion=promotion)

    def test_snapshot_preservation_tamper_fails_closed(self):
        promotion = copy.deepcopy(self.promotion)
        promotion["reviewed_snapshot"]["snapshot_preserved_byte_for_byte"] = False
        with self.assertRaises(ValueError):
            self.check(promotion=promotion)

    def test_factorization_rank_tamper_fails_closed(self):
        promotion = copy.deepcopy(self.promotion)
        promotion["factorization_evidence"]["combined_check_logical_rank"] = 10
        with self.assertRaises(ValueError):
            self.check(promotion=promotion)

    def test_min_plus_tie_envelope_tamper_fails_closed(self):
        promotion = copy.deepcopy(self.promotion)
        promotion["promoted_scope"]["tie_sensitivity"]["min_plus_hamming"] = [226, 226]
        with self.assertRaises(ValueError):
            self.check(promotion=promotion)

    def test_downstream_authority_exclusion_tamper_fails_closed(self):
        promotion = copy.deepcopy(self.promotion)
        promotion["excluded_scope"].remove("TCM-QDEC-003")
        with self.assertRaises(ValueError):
            self.check(promotion=promotion)


if __name__ == "__main__":
    unittest.main()
