from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class QECCircuit001PromotionTests(unittest.TestCase):
    def load(self, path: str):
        return json.loads((ROOT / path).read_text(encoding="utf-8"))

    def blob(self, path: str) -> str:
        return subprocess.check_output(
            ["git", "hash-object", str(ROOT / path)], text=True
        ).strip()

    def test_promotion_overlay_preserves_scientific_snapshot(self):
        promotion = self.load(
            "reviews/QTR-QEC-CIRCUIT-REVIEW-001/promotion-record.json"
        )
        intake = self.load("reviews/QTR-QEC-CIRCUIT-REVIEW-001/intake.json")
        manifest = self.load("registry/qec-circuit-001-manifest.json")
        amendment = self.load("registry/qec-circuit-001-manifest-amendment-001.json")
        registry = self.load("registry/qec-circuit-001.json")
        evidence = self.load("evidence/QEC-CIRCUIT-001-report.json")

        self.assertEqual(promotion["status"], "referee_promoted_bounded")
        self.assertEqual(
            promotion["promotion_authorization"]["disposition"],
            "ADOPT_WITH_AMENDMENTS__AUTHORIZE_QEC_CIRCUIT_001_DOCUMENTARY_PROMOTION_ONLY",
        )
        self.assertEqual(promotion["promotion_authorization"]["comment"], 5322340585)
        self.assertEqual(
            promotion["referee"]["disposition"],
            "APPROVE_BOUNDED_SCIENTIFIC_MERGE__QEC_CIRCUIT_001",
        )
        self.assertEqual(
            promotion["reviewed_head"],
            "32bbb7117670a30fad70ee9969e2699239678a09",
        )
        self.assertEqual(
            promotion["scientific_merge_commit"],
            "da820411b45f2e23fe961ed9fb4597a3b3d3e774",
        )
        self.assertTrue(
            promotion["reviewed_snapshot"]["snapshot_preserved_byte_for_byte"]
        )
        self.assertEqual(promotion["promotion_authority_location"], "documentary_overlay_only")

        self.assertEqual(
            self.blob("registry/qec-circuit-001-manifest.json"),
            "f426fdc88cfefbdcd6e712b29c1243952276d18b",
        )
        self.assertEqual(
            self.blob("registry/qec-circuit-001-manifest-amendment-001.json"),
            "92820d7eb66f0e24d4b004fc8e6dfb73f5939b66",
        )
        self.assertEqual(
            self.blob("registry/qec-circuit-001.json"),
            "80af09123128bbaebadc24dfe4345799405b3f82",
        )
        self.assertEqual(
            self.blob("evidence/QEC-CIRCUIT-001-report.json"),
            "4ebdcc1b94391973535df15c5bb377e96decc3b5",
        )

        self.assertEqual(
            manifest["manifest_payload_sha256"],
            "15962fa93eb92632e760e62a54fbd03a8322fb09b8c3b41de2f0b4225fb52dfb",
        )
        self.assertEqual(
            amendment["amendment_payload_sha256"],
            "8be8637ef976c9096b22259f0f849e2350a997b80038f4815302fbefa5f2ad19",
        )
        experiment = registry["experiments"][0]
        self.assertEqual(experiment["status"], "candidate_executable_not_promoted")
        self.assertEqual(evidence["status"], "candidate_executable_not_promoted")
        self.assertEqual(
            evidence["payload_sha256"],
            "e7c6f3479f5f06b56df95452833e22b59a9db97a9de5d18491c040238f36fed0",
        )
        self.assertEqual(
            evidence["measurement_origin"]["bound_full_exact_report_payload_sha256"],
            "6138aaf0630a5e222c8ae8688d03ce5a48015d506bfc5000e3e19b3f93fb0d6f",
        )

        self.assertEqual(intake["status"], "candidate_executable_not_promoted")
        self.assertEqual(intake["review_cycle_status"], "completed_referee_promoted")
        self.assertTrue(intake["snapshot_preserved_byte_for_byte"])
        self.assertEqual(intake["referee_record"], promotion["office_records"]["Referee"])

    def test_promoted_scope_is_finite_and_noninflationary(self):
        promotion = self.load(
            "reviews/QTR-QEC-CIRCUIT-REVIEW-001/promotion-record.json"
        )
        scope = promotion["promoted_scope"]

        self.assertEqual(scope["corpus_size"], 2851)
        self.assertEqual(
            scope["conventional_success_totals"],
            {
                "TEMP_BP_MIN_SUM": 2430,
                "TEMP_BP_OSD_CS_7": 2520,
                "TEMP_BP_SUM_PRODUCT": 1736,
            },
        )
        self.assertEqual(scope["detector_fiber_ambiguity"]["distinct_detector_vectors"], 2517)
        self.assertEqual(
            scope["detector_fiber_ambiguity"]["fibers_with_multiple_terminal_stabilizer_classes"],
            135,
        )
        self.assertEqual(
            scope["detector_fiber_ambiguity"]["authoritative_histories_in_ambiguous_fibers"],
            405,
        )
        self.assertEqual(scope["quarantined_workflow_run"], 32085478805)
        self.assertFalse(promotion["quarantine"]["results_admitted"])

        tcm = scope["tcm"]
        self.assertEqual(tcm["status"], "TEMPORAL_TCM_EXACT_BOUND_EXHAUSTED")
        self.assertFalse(tcm["quality_defined"])
        self.assertFalse(tcm["tcm_vs_conventional_quality_ordering_defined"])
        self.assertEqual(tcm["induced_width"], 34)
        self.assertEqual(tcm["predicted_peak_joint_table_entries"], 1 << 35)
        self.assertEqual(tcm["frozen_peak_joint_table_cap"], 1 << 20)

        excluded = set(promotion["excluded_scope"])
        self.assertIn("gate-level syndrome extraction", excluded)
        self.assertIn("threshold or pseudo-threshold claims", excluded)
        self.assertIn("runtime or memory superiority or inferiority", excluded)
        self.assertIn("later QEC-CIRCUIT subgates", excluded)
        self.assertIn("QLDPC-FORGE", excluded)

    def test_documentary_surfaces_state_promotion_without_downstream_authority(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        wp = (ROOT / "work-packages/QTR-QEC-CIRCUIT-001.md").read_text(
            encoding="utf-8"
        )
        readme_flat = " ".join(readme.split())
        wp_flat = " ".join(wp.split())

        marker = "reviews/QTR-QEC-CIRCUIT-REVIEW-001/promotion-record.json"
        self.assertIn(marker, readme)
        self.assertIn(marker, wp)
        self.assertIn("Referee-promoted", readme)
        self.assertIn("Referee-promoted bounded temporal authority", wp)
        self.assertIn("TCM quality remains undefined", readme_flat)
        self.assertIn("no TCM-vs-conventional quality ordering is defined", wp_flat)
        self.assertIn("`QLDPC-FORGE` remains unauthorized", wp_flat)
        self.assertIn("Later `QEC-CIRCUIT` subgates remain unauthorized", wp_flat)


if __name__ == "__main__":
    unittest.main()
