import copy
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_HEAD = "1bf76b536d9cd59d8a4b6b3518764df8e526986e"
EXPECTED_MERGE = "e30e64adcbd67ab015b04415135bb167b3132a02"
EXPECTED_PAYLOAD = "198bb28f47844aa98efa20d8c838c48870a8aef41ccfda266b16661677e363e1"
EXPECTED_REGISTRY_BLOB = "9cf5ed39bd51c3e4f920e4b5b4687fc4eacec386"
EXPECTED_EVIDENCE_BLOB = "268a5bfa9ed35ad3cd5984031de20487835643d0"
EXPECTED_VALIDATION_SET = "2eabc60f4ea2d64be6e4fea5ee33e527de46b115e727a8607b5332b19ba1e1bf"
EXPECTED_VALIDATION_OUTPUTS = "b5e168d3c8f4b420c8f2c1129ea23a3a4c5d6be946053aac7f1650cc4dd79189"


def git_blob_sha(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def canonical_digest(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def validate(promotion, intake, registry, evidence, registry_raw, evidence_raw):
    if promotion.get("record_id") != "QTR-QLDPC-SCALE-REVIEW-001A-PROMOTION" or promotion.get("status") != "referee_promoted_bounded":
        raise ValueError("promotion identity/status mismatch")
    if promotion.get("reviewed_head") != EXPECTED_HEAD or promotion.get("scientific_merge_commit") != EXPECTED_MERGE:
        raise ValueError("scientific identity mismatch")
    if intake.get("status") != "candidate_executable_not_promoted" or intake.get("review_cycle_status") != "completed_referee_promoted":
        raise ValueError("intake status mismatch")

    experiment = registry.get("experiments", [{}])[0]
    if experiment.get("experiment_id") != "QLDPC-SCALE-001A" or experiment.get("status") != "candidate_executable_not_promoted":
        raise ValueError("registry snapshot changed")
    if evidence.get("experiment_id") != "QLDPC-SCALE-001A" or evidence.get("status") != "candidate_executable_not_promoted":
        raise ValueError("evidence snapshot changed")
    if evidence.get("payload_sha256") != EXPECTED_PAYLOAD:
        raise ValueError("payload changed")
    unsigned = dict(evidence)
    unsigned.pop("payload_sha256", None)
    if canonical_digest(unsigned) != EXPECTED_PAYLOAD:
        raise ValueError("payload no longer self-verifies")

    snapshot = promotion.get("reviewed_snapshot", {})
    if snapshot.get("snapshot_preserved_byte_for_byte") is not True:
        raise ValueError("snapshot preservation missing")
    if snapshot.get("registry_blob_sha") != EXPECTED_REGISTRY_BLOB or git_blob_sha(registry_raw) != EXPECTED_REGISTRY_BLOB:
        raise ValueError("registry blob changed")
    if snapshot.get("evidence_blob_sha") != EXPECTED_EVIDENCE_BLOB or git_blob_sha(evidence_raw) != EXPECTED_EVIDENCE_BLOB:
        raise ValueError("evidence blob changed")

    source = promotion.get("source_evidence", {})
    if source.get("source_reported_parameters") != [72,12,6] or source.get("distance_status") != "SOURCE_REPORTED_DISTANCE":
        raise ValueError("source/distance boundary changed")
    if source.get("distance_independently_certified") is not False:
        raise ValueError("distance claim inflated")

    structural = promotion.get("structural_evidence", {})
    if [structural.get("independent_stabilizer_generators"), structural.get("selector_rank")] != [30,42]:
        raise ValueError("structural dimensions changed")
    if structural.get("predeclared_induced_widths") != {"lexicographic":24,"min_fill":18,"min_degree":18}:
        raise ValueError("order audit changed")
    if structural.get("primary_order") != "min_fill" or structural.get("primary_peak_joint_table_entries") != 524288:
        raise ValueError("primary order/result changed")
    if structural.get("global_treewidth_optimum_certified") is not False:
        raise ValueError("global treewidth claim inflated")

    compilation = promotion.get("compilation_evidence", {})
    if compilation.get("primary_object_is_answer_cache") is not False or compilation.get("answer_cache_entries") != 0:
        raise ValueError("anti-cache certificate changed")
    if compilation.get("selector_values_materialized_during_compilation") != 0 or compilation.get("repeated_evaluation_recompiles_descriptor") is not False:
        raise ValueError("compiled reuse boundary changed")
    if compilation.get("descriptor_sha256") != "c47e85efbad65619eea5d2be84bc63185d81bbac08a5e82ea71330a5b858dd5c":
        raise ValueError("descriptor identity changed")
    if compilation.get("all_primary_compilation_caps_pass") is not True:
        raise ValueError("resource-cap result changed")
    if compilation.get("aop_total_is_runtime_model") is not False or compilation.get("runtime_or_memory_superiority_inferred") is not False:
        raise ValueError("systems claim inflated")

    validation = promotion.get("validation_evidence", {})
    if validation.get("frozen_selector_count") != 300 or validation.get("pseudorandom_selector_count") != 256:
        raise ValueError("validation sample changed")
    if validation.get("validation_set_sha256") != EXPECTED_VALIDATION_SET or validation.get("validation_outputs_sha256") != EXPECTED_VALIDATION_OUTPUTS:
        raise ValueError("validation identity changed")
    if validation.get("compiled_vs_independent_oracle_all_equal") is not True:
        raise ValueError("validation equality changed")
    if validation.get("exhaustive_all_selector_equivalence") is not False:
        raise ValueError("sampled equality inflated to exhaustive")

    scope = promotion.get("promoted_scope", {})
    if scope.get("classification") != "FEASIBLE_EXACT_WITHIN_BOUND":
        raise ValueError("classification changed")
    excluded = set(promotion.get("excluded_scope", []))
    for item in [
        "exhaustive equivalence over the full 2^42 selector space",
        "global treewidth 18",
        "independently certified distance 6",
        "multi-size scaling law, slope, exponent, or monotonic growth claim",
        "runtime superiority",
        "memory superiority",
        "QLDPC-SCALE-001B",
        "TCM-QDEC-COMPARE-001",
        "QEC-CIRCUIT-001",
        "QLDPC-FORGE"
    ]:
        if item not in excluded:
            raise ValueError("required exclusion missing")


class QLDPCScale001APromotionTests(unittest.TestCase):
    def setUp(self):
        review_dir = ROOT / "reviews" / "QTR-QLDPC-SCALE-REVIEW-001A"
        self.promotion = json.loads((review_dir / "promotion-record.json").read_text())
        self.intake = json.loads((review_dir / "intake.json").read_text())
        self.registry_raw = (ROOT / "registry" / "qldpc-scale-001a.json").read_bytes()
        self.evidence_raw = (ROOT / "evidence" / "QLDPC-SCALE-001A-report.json").read_bytes()
        self.registry = json.loads(self.registry_raw)
        self.evidence = json.loads(self.evidence_raw)

    def check(self, promotion=None):
        validate(promotion or self.promotion, self.intake, self.registry, self.evidence, self.registry_raw, self.evidence_raw)

    def test_promotion_overlay_matches_immutable_scientific_snapshot(self):
        self.check()

    def test_reviewed_head_tamper_fails_closed(self):
        p = copy.deepcopy(self.promotion); p["reviewed_head"] = "0" * 40
        with self.assertRaises(ValueError): self.check(p)

    def test_snapshot_preservation_tamper_fails_closed(self):
        p = copy.deepcopy(self.promotion); p["reviewed_snapshot"]["snapshot_preserved_byte_for_byte"] = False
        with self.assertRaises(ValueError): self.check(p)

    def test_distance_inflation_fails_closed(self):
        p = copy.deepcopy(self.promotion); p["source_evidence"]["distance_independently_certified"] = True
        with self.assertRaises(ValueError): self.check(p)

    def test_global_treewidth_inflation_fails_closed(self):
        p = copy.deepcopy(self.promotion); p["structural_evidence"]["global_treewidth_optimum_certified"] = True
        with self.assertRaises(ValueError): self.check(p)

    def test_answer_cache_tamper_fails_closed(self):
        p = copy.deepcopy(self.promotion); p["compilation_evidence"]["primary_object_is_answer_cache"] = True
        with self.assertRaises(ValueError): self.check(p)

    def test_exhaustive_selector_inflation_fails_closed(self):
        p = copy.deepcopy(self.promotion); p["validation_evidence"]["exhaustive_all_selector_equivalence"] = True
        with self.assertRaises(ValueError): self.check(p)

    def test_runtime_inference_tamper_fails_closed(self):
        p = copy.deepcopy(self.promotion); p["compilation_evidence"]["runtime_or_memory_superiority_inferred"] = True
        with self.assertRaises(ValueError): self.check(p)

    def test_downstream_exclusion_tamper_fails_closed(self):
        p = copy.deepcopy(self.promotion); p["excluded_scope"].remove("QLDPC-SCALE-001B")
        with self.assertRaises(ValueError): self.check(p)


if __name__ == "__main__":
    unittest.main()
