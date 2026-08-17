#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence/TCM-QDEC-COMPARE-001-report.json"
REGISTRY = ROOT / "registry/tcm-qdec-compare-001.json"
MANIFEST = ROOT / "registry/tcm-qdec-compare-001-manifest.json"


def cbytes(x):
    return json.dumps(
        x, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def digest(x):
    return hashlib.sha256(cbytes(x)).hexdigest()


class Compare001EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        cls.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))["experiments"][0]
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_evidence_self_digest(self):
        payload = self.evidence["payload_sha256"]
        unsigned = dict(self.evidence)
        unsigned.pop("payload_sha256")
        self.assertEqual(
            payload,
            "9bd93dd1f0b6c5d7ca59523c7dfd382524639adf77aefaedd8900b2b01de6b7c",
        )
        self.assertEqual(digest(unsigned), payload)
        self.assertEqual(
            self.evidence["full_report_payload_sha256"],
            "6385c2da742e14ecf2bc41336c78c2a8ff42b1cdd897fb5e7cfac056e2214146",
        )

    def test_registry_binds_candidate_evidence(self):
        self.assertEqual(self.registry["experiment_id"], "TCM-QDEC-COMPARE-001")
        self.assertEqual(self.registry["status"], "candidate_executable_not_promoted")
        self.assertEqual(
            self.registry["evidence"]["committed_projection_payload_sha256"],
            self.evidence["payload_sha256"],
        )
        self.assertEqual(
            self.registry["evidence"]["full_exact_report_payload_sha256"],
            self.evidence["full_report_payload_sha256"],
        )
        self.assertEqual(self.registry["authority"]["authorization_comment"], 5320400759)

    def test_manifest_remains_pre_measurement_identity(self):
        self.assertEqual(
            self.evidence["manifest"]["first_commit"],
            "a187bcbd52d032ab62c85d5aa9c4e5d44576b45b",
        )
        self.assertEqual(
            self.evidence["manifest"]["payload_sha256"],
            "c68830f40733cde6957713060cec35adf317c75572cc960610c07c4d0e24d1e2",
        )
        claimed = self.manifest["manifest_payload_sha256"]
        unsigned = dict(self.manifest)
        unsigned.pop("manifest_payload_sha256")
        self.assertEqual(digest(unsigned), claimed)

    def test_c18_is_only_quality_head_to_head_surface(self):
        self.assertEqual(self.evidence["surfaces"]["C18"]["role"], "matched_quality_head_to_head")
        self.assertEqual(self.evidence["surfaces"]["C72"]["role"], "conventional_reach_status_only")
        self.assertEqual(self.evidence["surfaces"]["C90"]["role"], "conventional_reach_status_only")
        self.assertEqual(
            self.evidence["surfaces"]["C72"]["quality_comparison_with_tcm"],
            "COMPARISON_CELL_UNDEFINED",
        )
        self.assertEqual(
            self.evidence["surfaces"]["C90"]["quality_comparison_with_tcm"],
            "COMPARISON_CELL_UNDEFINED",
        )

    def test_c18_exact_totals_and_min_plus_tie_envelope(self):
        c18 = self.evidence["surfaces"]["C18"]
        self.assertEqual(c18["conventional"]["BP_MIN_SUM"]["totals"]["oracle_success"], 145)
        self.assertEqual(c18["conventional"]["BP_OSD_CS_7"]["totals"]["oracle_success"], 244)
        self.assertEqual(c18["conventional"]["BP_SUM_PRODUCT"]["totals"]["oracle_success"], 19)
        self.assertEqual(c18["tcm"]["sum_product_bsc_p_0_1"]["success_total"], 263)
        self.assertEqual(c18["tcm"]["soft_tropical_base_2"]["success_total"], 262)
        self.assertEqual(c18["tcm"]["min_plus_hamming"]["success_total"], 226)
        self.assertEqual(c18["tcm"]["min_plus_hamming"]["tie_envelope"], [218, 263])

    def test_c18_pairwise_relations_are_noncollapsed(self):
        pairs = {
            (x["left"], x["right"]): x
            for x in self.evidence["surfaces"]["C18"]["pairwise_quality"]
        }
        bp_osd_sum = pairs[("BP_OSD_CS_7", "TCM::sum_product_bsc_p_0_1")]
        self.assertEqual(bp_osd_sum["success_difference_left_minus_right"], -19)
        self.assertEqual(bp_osd_sum["left_only_success"], 178)
        self.assertEqual(bp_osd_sum["right_only_success"], 197)
        bp_osd_min = pairs[("BP_OSD_CS_7", "TCM::min_plus_hamming")]
        self.assertEqual(bp_osd_min["success_difference_left_minus_right"], 18)
        self.assertEqual(bp_osd_min["left_only_success"], 191)
        self.assertEqual(bp_osd_min["right_only_success"], 173)
        self.assertEqual(bp_osd_min["scope"], "C18_MATCHED_CELL_ONLY")

    def test_larger_surface_conventional_totals_do_not_define_tcm_quality(self):
        c72 = self.evidence["surfaces"]["C72"]
        c90 = self.evidence["surfaces"]["C90"]
        self.assertEqual(c72["tcm"]["status"], "SHARED_DECODER_INTERFACE_NOT_CERTIFIED")
        self.assertEqual(c90["tcm"]["status"], "NOT_REACHED_EXACT_COMPILATION_BOUND")
        self.assertEqual(c72["conventional"]["BP_MIN_SUM"]["totals"]["oracle_success"], 161)
        self.assertEqual(c72["conventional"]["BP_OSD_CS_7"]["totals"]["oracle_success"], 161)
        self.assertEqual(c72["conventional"]["BP_SUM_PRODUCT"]["totals"]["oracle_success"], 144)
        self.assertEqual(c90["conventional"]["BP_MIN_SUM"]["totals"]["oracle_success"], 200)
        self.assertEqual(c90["conventional"]["BP_OSD_CS_7"]["totals"]["oracle_success"], 211)
        self.assertEqual(c90["conventional"]["BP_SUM_PRODUCT"]["totals"]["oracle_success"], 171)

    def test_corpus_and_package_receipts_are_locked(self):
        self.assertEqual(
            self.evidence["corpus_receipts"]["C72"]["sha256"],
            "23b49e39eafd70c9619f8837dfcb0046e13a1600cd7176d42a6018814f518050",
        )
        self.assertEqual(
            self.evidence["corpus_receipts"]["C90"]["sha256"],
            "b053a27a9c346832d6008987e204c88162dc1797e0367b38705861049059e086",
        )
        self.assertEqual(self.evidence["package_receipt"]["ldpc_metadata_version"], "0.1.53")
        self.assertEqual(self.evidence["package_receipt"]["bposd_metadata_version"], "1.6")

    def test_adjudication_and_downstream_boundaries(self):
        adj = self.evidence["adjudication"]
        self.assertEqual(adj["primary_outcome"], "SHARED_INTERFACE_COMPARISON_COMPLETED_ON_C18")
        self.assertFalse(adj["c72_tcm_quality_defined"])
        self.assertFalse(adj["c90_tcm_quality_defined"])
        self.assertFalse(adj["cross_surface_winner_defined"])
        boundary = self.evidence["claim_boundary"]
        self.assertFalse(boundary["general_decoder_superiority"])
        self.assertFalse(boundary["runtime_or_memory_superiority"])
        self.assertFalse(boundary["qec_circuit_001_authorized"])
        self.assertFalse(boundary["qldpc_forge_authorized"])

    def test_no_missing_value_imputation_or_aggregate_winner(self):
        relation = self.evidence["comparison_relation"]
        self.assertFalse(relation["missing_value_imputation"])
        self.assertFalse(relation["cross_surface_aggregate_winner"])
        self.assertIn("not_reached", relation["undefined_if"])


if __name__ == "__main__":
    unittest.main()
