import copy
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_HEAD = "e4ba3cddc2440c868584ee675362f7d883855c73"
EXPECTED_MERGE = "c6a7c7b3f7b49d52e22f5a79866c479aad326aa0"
EXPECTED_MANIFEST_BLOB = "b4a8157aac966c6cd5bea08beb945c2f2ccdcc7b"
EXPECTED_MANIFEST_PAYLOAD = "0beef3aa1062bd30c691e3f01d00db0d1d8890d07c0dca2761fa933978ff09f5"
EXPECTED_REGISTRY_BLOB = "26f20f5a27a1488f71da677ecc9ead4fad76a958"
EXPECTED_EVIDENCE_BLOB = "7a368204f3a8202544a8ff4fe720e7f54b1edea5"
EXPECTED_EVIDENCE_PAYLOAD = "6b8076376eb621710d993d1cb8768c7d4c03b7fe9d67802e6ae2e77212b610fc"
EXPECTED_WIDTHS = {
    "lexicographic": [24, 28, 33, 31, 71, 253],
    "min_fill": [18, 25, 30, 34, 79, 201],
    "min_degree": [18, 25, 30, 38, 83, 223],
}


def git_blob_sha(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def canonical_digest(payload):
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    ).hexdigest()


def validate(promotion, intake, manifest, registry, evidence, manifest_raw, registry_raw, evidence_raw):
    if promotion.get("record_id") != "QTR-QLDPC-SCALE-REVIEW-001B-PROMOTION":
        raise ValueError("promotion identity mismatch")
    if promotion.get("status") != "referee_promoted_bounded":
        raise ValueError("promotion status mismatch")
    if promotion.get("reviewed_head") != EXPECTED_HEAD or promotion.get("scientific_merge_commit") != EXPECTED_MERGE:
        raise ValueError("scientific identity mismatch")
    if intake.get("status") != "candidate_executable_not_promoted":
        raise ValueError("intake scientific status changed")
    if intake.get("review_cycle_status") != "completed_referee_promoted":
        raise ValueError("review cycle status mismatch")

    experiment = registry.get("experiments", [{}])[0]
    if experiment.get("experiment_id") != "QLDPC-SCALE-001B" or experiment.get("status") != "candidate_executable_not_promoted":
        raise ValueError("registry snapshot changed")
    if evidence.get("experiment_id") != "QLDPC-SCALE-001B" or evidence.get("status") != "candidate_executable_not_promoted":
        raise ValueError("evidence snapshot changed")

    if evidence.get("payload_sha256") != EXPECTED_EVIDENCE_PAYLOAD:
        raise ValueError("evidence payload changed")
    unsigned = dict(evidence)
    unsigned.pop("payload_sha256", None)
    if canonical_digest(unsigned) != EXPECTED_EVIDENCE_PAYLOAD:
        raise ValueError("evidence payload no longer self-verifies")

    manifest_unsigned = dict(manifest)
    manifest_claimed = manifest_unsigned.pop("manifest_payload_sha256", None)
    if manifest_claimed != EXPECTED_MANIFEST_PAYLOAD or canonical_digest(manifest_unsigned) != EXPECTED_MANIFEST_PAYLOAD:
        raise ValueError("manifest payload changed")

    snapshot = promotion.get("reviewed_snapshot", {})
    if snapshot.get("snapshot_preserved_byte_for_byte") is not True:
        raise ValueError("snapshot preservation missing")
    if snapshot.get("manifest_blob_sha") != EXPECTED_MANIFEST_BLOB or git_blob_sha(manifest_raw) != EXPECTED_MANIFEST_BLOB:
        raise ValueError("manifest blob changed")
    if snapshot.get("registry_blob_sha") != EXPECTED_REGISTRY_BLOB or git_blob_sha(registry_raw) != EXPECTED_REGISTRY_BLOB:
        raise ValueError("registry blob changed")
    if snapshot.get("evidence_blob_sha") != EXPECTED_EVIDENCE_BLOB or git_blob_sha(evidence_raw) != EXPECTED_EVIDENCE_BLOB:
        raise ValueError("evidence blob changed")

    structural = promotion.get("structural_evidence", {})
    if structural.get("named_order_widths") != EXPECTED_WIDTHS:
        raise ValueError("named-order widths changed")
    if structural.get("global_treewidth_optimum_certified") is not False:
        raise ValueError("named width inflated to global treewidth")
    if structural.get("all_post_anchor_level_s_audits_within_frozen_bounds") is not True:
        raise ValueError("Level-S result changed")
    if structural.get("largest_level_s_audit") != {
        "n": 784, "structural_events": 509630167, "peak_retained_entries": 69939
    }:
        raise ValueError("largest structural audit changed")

    compilation = promotion.get("compilation_boundary", {})
    first = compilation.get("first_post_anchor_exhaustion", {})
    if first != {
        "n": 90,
        "min_fill_induced_width": 25,
        "predicted_peak_joint_table_entries": 67108864,
        "first_crossed_cap": "max_peak_joint_table_entries",
        "stopped_before_materialization": True,
    }:
        raise ValueError("first compilation boundary changed")
    if compilation.get("primary_peak_table_cap") != 1048576:
        raise ValueError("Level-C cap changed")
    if compilation.get("post_anchor_exhausted_rungs") != [90,108,144,288,784]:
        raise ValueError("post-anchor exhaustion set changed")
    if compilation.get("post_anchor_compiled_rungs") != [] or compilation.get("post_anchor_semantic_validation_rungs") != []:
        raise ValueError("post-anchor compilation/validation fabricated")
    if compilation.get("intrinsic_intractability_inferred") is not False:
        raise ValueError("cap exhaustion inflated to intractability")
    if compilation.get("runtime_or_memory_inference") is not False:
        raise ValueError("systems inference inflated")

    finite = promotion.get("finite_ladder_evidence", {})
    if finite.get("primary_classification") != "FINITE_LADDER_STRUCTURAL_AUDIT_COMPLETED__COMPILATION_BOUND_EXHAUSTED":
        raise ValueError("primary classification changed")
    if finite.get("secondary_classifications") != ["FINITE_LADDER_NONMONOTONE_STRUCTURE_OBSERVED"]:
        raise ValueError("secondary classification changed")
    if finite.get("lexicographic_nonmonotonic_witness") != {
        "from_n":108,"from_width":33,"to_n":144,"to_width":31
    }:
        raise ValueError("finite nonmonotonicity witness changed")
    if finite.get("finite_named_ladder_only") is not True or finite.get("asymptotic_or_family_scaling_inferred") is not False:
        raise ValueError("finite ladder inflated to family scaling")

    maturity = promotion.get("comparison_referral_maturity", {})
    if maturity.get("maturity_criterion_met") is not True:
        raise ValueError("comparison maturity record changed")
    if maturity.get("creates_compare_authority") is not False:
        raise ValueError("comparison authority created")

    source = promotion.get("source_evidence", {})
    if source.get("post_anchor_distances_independently_certified") is not False:
        raise ValueError("distance provenance inflated")

    excluded = set(promotion.get("excluded_scope", []))
    required = {
        "global treewidth for any named rung or BB family",
        "asymptotic or family scaling law",
        "intrinsic intractability of exact contraction",
        "post-anchor compiled decoder semantics or selector validation",
        "BP, min-sum, or BP-OSD comparison",
        "TCM-QDEC-COMPARE-001 execution authority",
        "QEC-CIRCUIT-001",
        "QLDPC-FORGE",
    }
    if not required.issubset(excluded):
        raise ValueError("required exclusions missing")


class QLDPCScale001BPromotionTests(unittest.TestCase):
    def setUp(self):
        review_dir = ROOT / "reviews" / "QTR-QLDPC-SCALE-REVIEW-001B"
        self.promotion = json.loads((review_dir / "promotion-record.json").read_text())
        self.intake = json.loads((review_dir / "intake.json").read_text())
        self.manifest_raw = (ROOT / "registry" / "qldpc-scale-001b-ladder-manifest.json").read_bytes()
        self.registry_raw = (ROOT / "registry" / "qldpc-scale-001b.json").read_bytes()
        self.evidence_raw = (ROOT / "evidence" / "QLDPC-SCALE-001B-report.json").read_bytes()
        self.manifest = json.loads(self.manifest_raw)
        self.registry = json.loads(self.registry_raw)
        self.evidence = json.loads(self.evidence_raw)

    def check(self, promotion=None):
        validate(
            promotion or self.promotion, self.intake, self.manifest, self.registry, self.evidence,
            self.manifest_raw, self.registry_raw, self.evidence_raw
        )

    def test_promotion_overlay_matches_immutable_scientific_snapshot(self):
        self.check()

    def test_reviewed_head_tamper_fails_closed(self):
        p = copy.deepcopy(self.promotion); p["reviewed_head"] = "0" * 40
        with self.assertRaises(ValueError): self.check(p)

    def test_snapshot_preservation_tamper_fails_closed(self):
        p = copy.deepcopy(self.promotion); p["reviewed_snapshot"]["snapshot_preserved_byte_for_byte"] = False
        with self.assertRaises(ValueError): self.check(p)

    def test_global_treewidth_inflation_fails_closed(self):
        p = copy.deepcopy(self.promotion); p["structural_evidence"]["global_treewidth_optimum_certified"] = True
        with self.assertRaises(ValueError): self.check(p)

    def test_first_cap_boundary_tamper_fails_closed(self):
        p = copy.deepcopy(self.promotion); p["compilation_boundary"]["first_post_anchor_exhaustion"]["n"] = 108
        with self.assertRaises(ValueError): self.check(p)

    def test_post_anchor_validation_fabrication_fails_closed(self):
        p = copy.deepcopy(self.promotion); p["compilation_boundary"]["post_anchor_semantic_validation_rungs"] = [90]
        with self.assertRaises(ValueError): self.check(p)

    def test_asymptotic_scaling_inflation_fails_closed(self):
        p = copy.deepcopy(self.promotion); p["finite_ladder_evidence"]["asymptotic_or_family_scaling_inferred"] = True
        with self.assertRaises(ValueError): self.check(p)

    def test_intractability_inflation_fails_closed(self):
        p = copy.deepcopy(self.promotion); p["compilation_boundary"]["intrinsic_intractability_inferred"] = True
        with self.assertRaises(ValueError): self.check(p)

    def test_compare_authority_drift_fails_closed(self):
        p = copy.deepcopy(self.promotion); p["comparison_referral_maturity"]["creates_compare_authority"] = True
        with self.assertRaises(ValueError): self.check(p)

    def test_downstream_exclusion_tamper_fails_closed(self):
        p = copy.deepcopy(self.promotion); p["excluded_scope"].remove("TCM-QDEC-COMPARE-001 execution authority")
        with self.assertRaises(ValueError): self.check(p)


if __name__ == "__main__":
    unittest.main()
