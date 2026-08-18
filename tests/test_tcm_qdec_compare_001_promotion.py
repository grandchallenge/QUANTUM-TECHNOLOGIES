from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TCMQDECCompare001PromotionTests(unittest.TestCase):
    def load(self, path: str):
        return json.loads((ROOT / path).read_text(encoding="utf-8"))

    def blob(self, path: str) -> str:
        return subprocess.check_output(
            ["git", "hash-object", str(ROOT / path)], text=True
        ).strip()

    def test_promotion_overlay_preserves_scientific_snapshot(self):
        promotion = self.load(
            "reviews/QTR-TCM-QDEC-COMPARE-REVIEW-001/promotion-record.json"
        )
        intake = self.load(
            "reviews/QTR-TCM-QDEC-COMPARE-REVIEW-001/intake.json"
        )
        manifest = self.load("registry/tcm-qdec-compare-001-manifest.json")
        registry = self.load("registry/tcm-qdec-compare-001.json")
        evidence = self.load("evidence/TCM-QDEC-COMPARE-001-report.json")

        self.assertEqual(promotion["status"], "referee_promoted_bounded")
        self.assertEqual(
            promotion["referee"]["disposition"],
            "APPROVE_BOUNDED_SCIENTIFIC_MERGE__TCM_QDEC_COMPARE_001",
        )
        self.assertEqual(
            promotion["reviewed_head"],
            "3ebe409c60e7907b8251d44ee822141159d2879c",
        )
        self.assertEqual(
            promotion["scientific_merge_commit"],
            "18f04d4af18582bbd00ae2769927408dce9b04ee",
        )
        self.assertTrue(
            promotion["reviewed_snapshot"]["snapshot_preserved_byte_for_byte"]
        )

        self.assertEqual(
            self.blob("registry/tcm-qdec-compare-001-manifest.json"),
            "577cc70f78ef588e2212aa48a1ab44b2a44a64fc",
        )
        self.assertEqual(
            self.blob("registry/tcm-qdec-compare-001.json"),
            "828498bf4d2a1b4a559700698bc324f9c1925e02",
        )
        self.assertEqual(
            self.blob("evidence/TCM-QDEC-COMPARE-001-report.json"),
            "86a8acaceebb3caaaf7be4e3447f1fdcdaeeedaa",
        )

        self.assertEqual(
            manifest["manifest_payload_sha256"],
            "c68830f40733cde6957713060cec35adf317c75572cc960610c07c4d0e24d1e2",
        )
        experiment = registry["experiments"][0]
        self.assertEqual(experiment["status"], "candidate_executable_not_promoted")
        self.assertEqual(evidence["status"], "candidate_executable_not_promoted")
        self.assertEqual(
            evidence["payload_sha256"],
            "9bd93dd1f0b6c5d7ca59523c7dfd382524639adf77aefaedd8900b2b01de6b7c",
        )
        self.assertEqual(
            evidence["full_report_payload_sha256"],
            "6385c2da742e14ecf2bc41336c78c2a8ff42b1cdd897fb5e7cfac056e2214146",
        )

        self.assertEqual(intake["status"], "candidate_executable_not_promoted")
        self.assertEqual(intake["review_cycle_status"], "completed_referee_promoted")
        self.assertTrue(intake["snapshot_preserved_byte_for_byte"])
        self.assertEqual(
            intake["referee_record"], promotion["office_records"]["Referee"]
        )

    def test_promoted_scope_remains_partial_and_bounded(self):
        promotion = self.load(
            "reviews/QTR-TCM-QDEC-COMPARE-REVIEW-001/promotion-record.json"
        )
        comp = promotion["comparison_evidence"]

        self.assertEqual(
            promotion["promoted_scope"]["classification"],
            "SHARED_INTERFACE_COMPARISON_COMPLETED_ON_C18",
        )
        self.assertEqual(comp["c18"]["min_plus_tie_envelope"], [218, 263])
        self.assertFalse(comp["cross_surface_aggregate_winner_defined"])
        self.assertEqual(
            comp["c72"]["quality_comparison_with_tcm"],
            "COMPARISON_CELL_UNDEFINED",
        )
        self.assertEqual(
            comp["c90"]["quality_comparison_with_tcm"],
            "COMPARISON_CELL_UNDEFINED",
        )
        self.assertEqual(
            comp["c72"]["tcm_status"],
            "SHARED_DECODER_INTERFACE_NOT_CERTIFIED",
        )
        self.assertEqual(
            comp["c90"]["tcm_status"],
            "NOT_REACHED_EXACT_COMPILATION_BOUND",
        )
        self.assertEqual(
            comp["c18"]["pairwise_bp_osd"]["TCM::min_plus_hamming"]
            ["success_difference_bp_minus_tcm_default"],
            18,
        )

        excluded = set(promotion["excluded_scope"])
        self.assertIn("QEC-CIRCUIT-001", excluded)
        self.assertIn("QLDPC-FORGE", excluded)
        self.assertIn("runtime superiority or inferiority", excluded)
        self.assertIn("asymptotic or family decoder scaling law", excluded)

    def test_documentary_surfaces_state_promotion_without_downstream_authority(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        wp = (ROOT / "work-packages/QTR-TCM-QDEC-COMPARE-001.md").read_text(
            encoding="utf-8"
        )
        readme_flat = " ".join(readme.split())
        wp_flat = " ".join(wp.split())

        marker = "reviews/QTR-TCM-QDEC-COMPARE-REVIEW-001/promotion-record.json"
        self.assertIn(marker, readme)
        self.assertIn(marker, wp)
        self.assertIn("Referee-promoted", readme)
        self.assertIn("Referee-promoted bounded comparison authority", wp)
        self.assertIn(
            "`QEC-CIRCUIT-001` and `QLDPC-FORGE` remain unauthorized", wp_flat
        )
        self.assertIn(
            "C72 and C90 TCM quality comparisons remain undefined", readme_flat
        )


if __name__ == "__main__":
    unittest.main()
