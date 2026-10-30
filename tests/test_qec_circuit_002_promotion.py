from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class QECCircuit002PromotionTests(unittest.TestCase):
    def load(self, path: str):
        return json.loads((ROOT / path).read_text(encoding="utf-8"))

    def blob(self, path: str) -> str:
        return subprocess.check_output(
            ["git", "hash-object", str(ROOT / path)], text=True
        ).strip()

    def test_promotion_overlay_preserves_scientific_snapshot(self):
        promotion = self.load(
            "reviews/QTR-QEC-CIRCUIT-REVIEW-002/promotion-record.json"
        )
        intake = self.load("reviews/QTR-QEC-CIRCUIT-REVIEW-002/intake.json")
        manifest = self.load("registry/qec-circuit-002-manifest.json")
        registry = self.load("registry/qec-circuit-002.json")
        evidence = self.load("evidence/QEC-CIRCUIT-002-report.json")

        self.assertEqual(promotion["status"], "referee_promoted_bounded")
        self.assertEqual(
            promotion["promotion_authorization"]["disposition"],
            "ADOPT_WITH_AMENDMENTS__AUTHORIZE_QEC_CIRCUIT_002_DOCUMENTARY_PROMOTION_ONLY",
        )
        self.assertEqual(promotion["promotion_authorization"]["comment"], 5335168196)
        self.assertEqual(promotion["promotion_authorization"]["issue"], 86)
        self.assertEqual(
            promotion["referee"]["disposition"],
            "APPROVE_BOUNDED_SCIENTIFIC_MERGE__QEC_CIRCUIT_002",
        )
        self.assertEqual(promotion["referee"]["record"], 5334661008)
        self.assertEqual(
            promotion["reviewed_head"],
            "695ea1da951cd2b4f9d5a6a07c30b090cfd37709",
        )
        self.assertEqual(
            promotion["scientific_merge_commit"],
            "e85d67619a0d739fe039cca8f271f9a32ae2f3db",
        )
        self.assertEqual(
            promotion["reviewed_snapshot"]["first_preoutcome_manifest_commit"],
            "ace579c9f3856349da612ac243d37970967f2562",
        )
        self.assertTrue(
            promotion["reviewed_snapshot"]["snapshot_preserved_byte_for_byte"]
        )
        self.assertEqual(
            promotion["promotion_authority_location"], "documentary_overlay_only"
        )

        immutable_blobs = {
            "registry/qec-circuit-002-manifest.json": "fdbec274a7520cf718d9b8b247fccfc9f83b3495",
            "registry/qec-circuit-002.json": "67560eb2c2955bd79fb6a3f7c3b0a35d83b1a17a",
            "evidence/QEC-CIRCUIT-002-report.json": "90d1f462e8666dbe5f26fbb241e6befa29ef6916",
            "reference/qec_circuit_002.py": "92f8bafbc3460d18d9a3b9d316848d289f4b545f",
            "reference/qec_circuit_002_evidence.py": "9f2d5eaadb8ca948f3e9229fe43cb0e9cc5b4957",
        }
        for path, expected in immutable_blobs.items():
            self.assertEqual(self.blob(path), expected, path)

        # Restore both independently admitted CI action-pin updates before
        # checking the original reviewed scientific workflow blob. Neither
        # dependency maintenance change may weaken the scientific snapshot.
        # Any other workflow change must still fail this exact blob check.
        workflow = (ROOT / ".github/workflows/qtr-qec-circuit-002.yml").read_text(
            encoding="utf-8"
        )
        previous_pin = "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1"
        current_pin = "actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2"
        self.assertEqual(workflow.count(current_pin), 1)
        self.assertNotIn(previous_pin, workflow)
        previous_setup = "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0"
        current_setup = "actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0 # v7.1.0"
        self.assertEqual(workflow.count(current_setup), 1)
        self.assertNotIn(previous_setup, workflow)
        historical_workflow = workflow.replace(current_pin, previous_pin).replace(
            current_setup, previous_setup
        )
        historical_blob = subprocess.run(
            ["git", "hash-object", "--stdin"],
            input=historical_workflow,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        self.assertEqual(
            historical_blob,
            "84716388da3004ee658f7c83fba9984c151fb5c1",
            "QEC-CIRCUIT-002 historical reviewed workflow, modulo action pin",
        )

        self.assertEqual(
            manifest["manifest_payload_sha256"],
            "9ba84244f828bc0c4f9f128e54d2c89693930c2280540f9dc420ae13e964aa29",
        )
        experiment = registry["experiments"][0]
        self.assertEqual(experiment["status"], "candidate_executable_not_promoted")
        self.assertEqual(evidence["status"], "candidate_executable_not_promoted")
        self.assertEqual(
            evidence["payload_sha256"],
            "cb9915e3d9bb32dc5abf1705c3dc7709082b79e3c5b91b391fb2aca0e632fcc3",
        )
        self.assertEqual(
            evidence["full_exact_report_payload_sha256"],
            "90d73b06e3778fea7322435f1ff7db74fc3cb708038057ef338643082aa25c28",
        )

        self.assertEqual(intake["status"], "candidate_executable_not_promoted")
        self.assertEqual(intake["review_cycle_status"], "completed_referee_promoted")
        self.assertTrue(intake["snapshot_preserved_byte_for_byte"])
        self.assertEqual(intake["referee_record"], promotion["office_records"]["Referee"])
        self.assertEqual(intake["referral_referee_record"], 5334690079)

    def test_promoted_scope_is_finite_and_noninflationary(self):
        promotion = self.load(
            "reviews/QTR-QEC-CIRCUIT-REVIEW-002/promotion-record.json"
        )
        scope = promotion["promoted_scope"]

        self.assertEqual(
            scope["classification"],
            "TEMPORAL_PREDECLARED_DECOMPOSITION_FAMILY_EXHAUSTED",
        )
        self.assertEqual(scope["frozen_peak_joint_table_cap"], 1 << 20)
        self.assertFalse(scope["successor_representation_compiled"])
        self.assertFalse(scope["quality_boundary"]["temporal_tcm_quality_defined"])
        self.assertFalse(
            scope["quality_boundary"]["tcm_vs_conventional_quality_ordering_defined"]
        )

        family = scope["representation_family"]
        self.assertEqual(family["R0_BASELINE_107_FACTOR"]["induced_width"], 34)
        for name in (
            "R1_TERMINAL_DIRECT_AUX",
            "R2_TERMINAL_CHAIN_AUX",
            "R3_CAUSAL_STATE_CHAIN",
        ):
            self.assertEqual(family[name]["induced_width"], 36)
            self.assertEqual(
                family[name]["semantic_status"],
                "TEMPORAL_DECOMPOSITION_SEMANTIC_EQUIVALENCE_CERTIFIED",
            )
            self.assertEqual(
                family[name]["status"],
                "TEMPORAL_DECOMPOSITION_EXACT_BOUND_EXHAUSTED",
            )

        excluded = set(promotion["excluded_scope"])
        self.assertIn("global treewidth", excluded)
        self.assertIn("intrinsic intractability", excluded)
        self.assertIn("runtime or memory superiority or inferiority", excluded)
        self.assertIn("QEC-CIRCUIT-003 or any later QEC-CIRCUIT subgate", excluded)
        self.assertIn("QLDPC-FORGE", excluded)

        timeout = promotion["workflow_evidence"]["timeout_provenance"]
        self.assertEqual(timeout["diagnostic_run"], 32095587023)
        self.assertFalse(timeout["test_only_repair_scientific_result_changed"])
        self.assertEqual(
            promotion["workflow_evidence"]["codeql_execution_docket_receipt"],
            5334640843,
        )
        self.assertEqual(promotion["workflow_evidence"]["codeql_open_exact_head_alerts"], 0)

    def test_documentary_surfaces_state_promotion_without_downstream_authority(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        wp = (ROOT / "work-packages/QTR-QEC-CIRCUIT-002.md").read_text(
            encoding="utf-8"
        )
        readme_flat = " ".join(readme.split())
        wp_flat = " ".join(wp.split())

        marker = "reviews/QTR-QEC-CIRCUIT-REVIEW-002/promotion-record.json"
        self.assertIn(marker, readme)
        self.assertIn(marker, wp)
        self.assertIn("QTR-QEC-CIRCUIT-002", readme)
        self.assertIn("Referee-promoted", readme)
        self.assertIn("Referee-promoted bounded representation authority", wp)
        self.assertIn("TCM quality remains undefined", readme_flat)
        self.assertIn("no TCM-vs-conventional quality ordering is defined", wp_flat)
        self.assertIn("`QEC-CIRCUIT-003` remains unauthorized", wp_flat)
        self.assertIn("`QLDPC-FORGE` remains unauthorized", wp_flat)
        self.assertIn("candidate_executable_not_promoted", wp_flat)


if __name__ == "__main__":
    unittest.main()
