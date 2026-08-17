import copy
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_HEAD = "968029c156a3d668a0adc9adce850b62cd249671"
EXPECTED_MERGE = "2925a41343c8e4592c1bf558d86ea461e0e1c7d4"
EXPECTED_PAYLOAD = "f0ecdae04f3da4f0508454da59ce406a4e6c461f88f1784279cb6d7e360b595f"
EXPECTED_REGISTRY_BLOB = "f47a2c3baae2e33e5b069eb06d78f406676fe257"
EXPECTED_EVIDENCE_BLOB = "df8d664307e2080fe2ad764066f384975bab59c0"


def git_blob_sha(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def canonical_digest(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def validate(promotion, intake, registry, evidence, registry_raw, evidence_raw):
    if promotion.get("record_id") != "QTR-TCM-QDEC-REVIEW-003-PROMOTION" or promotion.get("status") != "referee_promoted_bounded":
        raise ValueError("promotion identity/status mismatch")
    if promotion.get("reviewed_head") != EXPECTED_HEAD or promotion.get("scientific_merge_commit") != EXPECTED_MERGE:
        raise ValueError("scientific identity mismatch")
    if intake.get("status") != "candidate_executable_not_promoted" or intake.get("review_cycle_status") != "completed_referee_promoted":
        raise ValueError("intake status mismatch")
    experiment = registry.get("experiments", [{}])[0]
    if experiment.get("experiment_id") != "TCM-QDEC-003" or experiment.get("status") != "candidate_executable_not_promoted":
        raise ValueError("registry snapshot changed")
    if evidence.get("experiment_id") != "TCM-QDEC-003" or evidence.get("status") != "candidate_executable_not_promoted":
        raise ValueError("evidence snapshot changed")
    if evidence.get("payload_sha256") != EXPECTED_PAYLOAD:
        raise ValueError("payload changed")
    unsigned = dict(evidence); unsigned.pop("payload_sha256", None)
    if canonical_digest(unsigned) != EXPECTED_PAYLOAD:
        raise ValueError("payload no longer self-verifies")
    snapshot = promotion.get("reviewed_snapshot", {})
    if snapshot.get("snapshot_preserved_byte_for_byte") is not True:
        raise ValueError("snapshot preservation missing")
    if snapshot.get("registry_blob_sha") != EXPECTED_REGISTRY_BLOB or git_blob_sha(registry_raw) != EXPECTED_REGISTRY_BLOB:
        raise ValueError("registry blob changed")
    if snapshot.get("evidence_blob_sha") != EXPECTED_EVIDENCE_BLOB or git_blob_sha(evidence_raw) != EXPECTED_EVIDENCE_BLOB:
        raise ValueError("evidence blob changed")
    width = promotion.get("basis_and_width_evidence", {})
    if width.get("minimum_induced_width") != 4 or width.get("orders_checked") != 5040 or width.get("optimal_order_count") != 720:
        raise ValueError("width certificate changed")
    if width.get("frozen_order") != [2,4,0,1,3,5,6] or width.get("peak_joint_table_entries") != 32:
        raise ValueError("frozen order certificate changed")
    if width.get("assignment_evaluations_total") != 774144 or width.get("predecessor_transition_relaxations_total") != 98298:
        raise ValueError("negative systems evidence changed")
    eq = promotion.get("equivalence_evidence", {})
    if eq.get("all_exactly_equal_to_tcm_qdec_002") is not True or eq.get("score_entries_checked") != 6144 or eq.get("mapping_entries_checked") != 2048:
        raise ValueError("equivalence evidence changed")
    if eq.get("tie_envelopes", {}).get("min_plus_hamming") != [218,263]:
        raise ValueError("min-plus ambiguity changed")
    excluded = set(promotion.get("excluded_scope", []))
    for item in ["TCM-QDEC-004", "QLDPC-FORGE", "bounded contraction width for a qLDPC code family", "runtime or memory superiority"]:
        if item not in excluded:
            raise ValueError("required downstream exclusion missing")


class TCMQDEC003PromotionTests(unittest.TestCase):
    def setUp(self):
        self.promotion = json.loads((ROOT / "reviews" / "QTR-TCM-QDEC-REVIEW-003" / "promotion-record.json").read_text())
        self.intake = json.loads((ROOT / "reviews" / "QTR-TCM-QDEC-REVIEW-003" / "intake.json").read_text())
        self.registry_raw = (ROOT / "registry" / "tcm-qdec-003.json").read_bytes()
        self.evidence_raw = (ROOT / "evidence" / "TCM-QDEC-003-report.json").read_bytes()
        self.registry = json.loads(self.registry_raw)
        self.evidence = json.loads(self.evidence_raw)

    def check(self, promotion=None):
        validate(promotion or self.promotion, self.intake, self.registry, self.evidence, self.registry_raw, self.evidence_raw)

    def test_promotion_overlay_matches_immutable_scientific_snapshot(self): self.check()
    def test_reviewed_head_tamper_fails_closed(self):
        p=copy.deepcopy(self.promotion); p["reviewed_head"]="0"*40
        with self.assertRaises(ValueError): self.check(p)
    def test_snapshot_preservation_tamper_fails_closed(self):
        p=copy.deepcopy(self.promotion); p["reviewed_snapshot"]["snapshot_preserved_byte_for_byte"]=False
        with self.assertRaises(ValueError): self.check(p)
    def test_width_tamper_fails_closed(self):
        p=copy.deepcopy(self.promotion); p["basis_and_width_evidence"]["minimum_induced_width"]=3
        with self.assertRaises(ValueError): self.check(p)
    def test_negative_tradeoff_tamper_fails_closed(self):
        p=copy.deepcopy(self.promotion); p["basis_and_width_evidence"]["assignment_evaluations_total"]=98298
        with self.assertRaises(ValueError): self.check(p)
    def test_min_plus_tie_tamper_fails_closed(self):
        p=copy.deepcopy(self.promotion); p["equivalence_evidence"]["tie_envelopes"]["min_plus_hamming"]=[226,226]
        with self.assertRaises(ValueError): self.check(p)
    def test_downstream_exclusion_tamper_fails_closed(self):
        p=copy.deepcopy(self.promotion); p["excluded_scope"].remove("TCM-QDEC-004")
        with self.assertRaises(ValueError): self.check(p)

if __name__ == "__main__": unittest.main()
