import copy
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_HEAD = "8177a57b63e3f2c953a028691d305563f298b572"
EXPECTED_MERGE = "7eff1025e97ff962a6fed81e6f2fa0f4d14653a3"
EXPECTED_PAYLOAD = "a5c7e59fa849ddc37c070d78d4a4dab8b07ae5ceccfecefeb5a20f4ae0dc83a7"
EXPECTED_REGISTRY_BLOB = "616f9ca9d81123f5b04d445e1ae5ca01e9559c85"
EXPECTED_EVIDENCE_BLOB = "77b6a05ff245d0292036b7efa47a3fe775f845af"


def git_blob_sha(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def canonical_digest(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def validate(promotion, intake, registry, evidence, registry_raw, evidence_raw):
    if promotion.get("record_id") != "QTR-TCM-QDEC-REVIEW-004-PROMOTION" or promotion.get("status") != "referee_promoted_bounded":
        raise ValueError("promotion identity/status mismatch")
    if promotion.get("reviewed_head") != EXPECTED_HEAD or promotion.get("scientific_merge_commit") != EXPECTED_MERGE:
        raise ValueError("scientific identity mismatch")
    if intake.get("status") != "candidate_executable_not_promoted" or intake.get("review_cycle_status") != "completed_referee_promoted":
        raise ValueError("intake status mismatch")
    experiment = registry.get("experiments", [{}])[0]
    if experiment.get("experiment_id") != "TCM-QDEC-004" or experiment.get("status") != "candidate_executable_not_promoted":
        raise ValueError("registry snapshot changed")
    if evidence.get("experiment_id") != "TCM-QDEC-004" or evidence.get("status") != "candidate_executable_not_promoted":
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
    structure = promotion.get("compiled_structure_evidence", {})
    if structure.get("primary_object_is_complete_answer_cache") is not False or structure.get("selector_values_materialized_during_compilation") != 0:
        raise ValueError("anti-cache certificate changed")
    if [structure.get("sum_product_reachable_nodes"), structure.get("soft_tropical_reachable_nodes"), structure.get("min_plus_reachable_nodes")] != [371,371,388]:
        raise ValueError("compiled DAG size changed")
    eq = promotion.get("equivalence_evidence", {})
    if eq.get("all_exactly_equal_to_tcm_qdec_003") is not True or eq.get("score_entries_checked") != 6144 or eq.get("mapping_entries_checked") != 2048:
        raise ValueError("equivalence evidence changed")
    if eq.get("tie_envelopes", {}).get("min_plus_hamming") != [218,263]:
        raise ValueError("min-plus ambiguity changed")
    aop = promotion.get("aop_evidence", {})
    if aop.get("compiled_one_shot_aop_total") != 12704688 or aop.get("reinstrumented_tcm_qdec_003_aop_total") != 14115840 or aop.get("one_shot_aop_reduction") != 1411152:
        raise ValueError("AOP evidence changed")
    if aop.get("aop_total_is_runtime_model") is not False or aop.get("runtime_or_memory_superiority_inferred") is not False:
        raise ValueError("AOP limitation changed")
    excluded = set(promotion.get("excluded_scope", []))
    for item in ["QLDPC-SCALE-001A", "QLDPC-SCALE-001B", "runtime superiority", "memory superiority", "TCM-QDEC-COMPARE-001", "QEC-CIRCUIT-001", "QLDPC-FORGE"]:
        if item not in excluded:
            raise ValueError("required downstream exclusion missing")


class TCMQDEC004PromotionTests(unittest.TestCase):
    def setUp(self):
        self.promotion = json.loads((ROOT / "reviews" / "QTR-TCM-QDEC-REVIEW-004" / "promotion-record.json").read_text())
        self.intake = json.loads((ROOT / "reviews" / "QTR-TCM-QDEC-REVIEW-004" / "intake.json").read_text())
        self.registry_raw = (ROOT / "registry" / "tcm-qdec-004.json").read_bytes()
        self.evidence_raw = (ROOT / "evidence" / "TCM-QDEC-004-report.json").read_bytes()
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
    def test_answer_cache_tamper_fails_closed(self):
        p=copy.deepcopy(self.promotion); p["compiled_structure_evidence"]["primary_object_is_complete_answer_cache"]=True
        with self.assertRaises(ValueError): self.check(p)
    def test_dag_size_tamper_fails_closed(self):
        p=copy.deepcopy(self.promotion); p["compiled_structure_evidence"]["sum_product_reachable_nodes"]=2048
        with self.assertRaises(ValueError): self.check(p)
    def test_aop_reduction_tamper_fails_closed(self):
        p=copy.deepcopy(self.promotion); p["aop_evidence"]["one_shot_aop_reduction"]=0
        with self.assertRaises(ValueError): self.check(p)
    def test_runtime_inference_tamper_fails_closed(self):
        p=copy.deepcopy(self.promotion); p["aop_evidence"]["runtime_or_memory_superiority_inferred"]=True
        with self.assertRaises(ValueError): self.check(p)
    def test_min_plus_tie_tamper_fails_closed(self):
        p=copy.deepcopy(self.promotion); p["equivalence_evidence"]["tie_envelopes"]["min_plus_hamming"]=[226,226]
        with self.assertRaises(ValueError): self.check(p)
    def test_downstream_exclusion_tamper_fails_closed(self):
        p=copy.deepcopy(self.promotion); p["excluded_scope"].remove("QLDPC-SCALE-001A")
        with self.assertRaises(ValueError): self.check(p)

if __name__ == "__main__": unittest.main()
