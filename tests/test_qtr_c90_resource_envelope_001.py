from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "reference"
if str(REFERENCE) not in sys.path:
    sys.path.insert(0, str(REFERENCE))

import qtr_c90_resource_envelope_001 as target


class TestQTRC90ResourceEnvelope001(unittest.TestCase):
    def test_manifest_self_digest_and_authority(self):
        manifest = target.load_manifest()
        self.assertEqual(manifest["manifest_payload_sha256"], "d64b770f5cc1fb4c8a0ca8e89dad6d8020a01ae38f2c6868ff3028f53c441651")
        self.assertEqual(manifest["authority"]["council_issue"], 100)
        self.assertEqual(manifest["authority"]["execution_issue"], 102)
        self.assertEqual(manifest["authority"]["human_steward_comment"], 5389645111)
        self.assertEqual(manifest["authority"]["protected_predecessor_merge"], "c5719a623310432c4e97a5863428176ff739cbd7")
        self.assertFalse(manifest["claim_boundary"]["full_c90_materialization_authorized"])

    def test_sensitivity_grid_is_fixed_and_machine_checkable(self):
        report = target.evaluate_static()
        self.assertFalse(report["materialization_performed"])
        expected = {
            "S0_BASELINE": ["DEFINITE_FAIL", "CERTIFIED_PASS", "CERTIFIED_PASS", "CERTIFIED_PASS"],
            "S1_GF2_CONSTRAINT_ELIMINATION": ["DEFINITE_FAIL", "CERTIFIED_PASS", "CERTIFIED_PASS", "CERTIFIED_PASS"],
            "S2_SEPARATOR_INTERFACE_COMPILATION": ["DEFINITE_FAIL", "INDETERMINATE", "CERTIFIED_PASS", "CERTIFIED_PASS"],
            "S3_GF2_PLUS_SEPARATOR": ["DEFINITE_FAIL", "INDETERMINATE", "CERTIFIED_PASS", "CERTIFIED_PASS"],
        }
        for method, statuses in expected.items():
            rows = report["methods"][method]["sensitivity"]
            self.assertEqual([row["multiplier"] for row in rows], [1, 2, 4, 8])
            self.assertEqual([row["status"] for row in rows], statuses)
            self.assertTrue(rows[1]["definite_historical_blockers_cleared"])

    def test_representation_quantities_are_typed_and_retained_is_upper_bound(self):
        report = target.evaluate_static()
        for method, row in report["methods"].items():
            rep = row["representation"]
            self.assertEqual(rep["retained_canonical_nodes_or_entries"]["type"], "upper_bound")
            self.assertIn("not an exact retained-node count", rep["retained_canonical_nodes_or_entries"]["basis"])
            self.assertEqual(rep["live_factor_table_entries"]["type"], "exact")
            self.assertEqual(rep["maximum_individual_table_entries"]["type"], "exact")
            self.assertEqual(rep["canonical_serialized_bytes"]["type"], "upper_bound")
            self.assertGreater(rep["live_factor_table_entries"]["value"], 0)
            self.assertGreater(rep["canonical_serialized_bytes"]["value"], 0)

    def test_predecessor_is_immutable_and_bound(self):
        predecessor = target.load_predecessor()
        self.assertEqual(predecessor["payload_sha256"], "ade245552af2f88d5ecb8c0b7f8eb363510ed678908fb80462b911255dd63d67")
        self.assertEqual(predecessor["overall_outcome"], "C90_PREDECLARED_EXACT_STRUCTURAL_FAMILY_EXHAUSTED")
        self.assertFalse(predecessor["phase_d_reached"])
        self.assertFalse(predecessor["phase_e_reached"])

    def test_no_materialization_authority(self):
        manifest = target.load_manifest()
        boundary = manifest["claim_boundary"]
        prohibited = [
            "full_c90_materialization_authorized",
            "frozen_307_validation_authorized",
            "adopt_larger_cap_authorized",
            "new_structural_method_authorized",
            "adaptive_order_search_authorized",
            "approximation_authorized",
            "learned_decoding_authorized",
            "accelerator_native_qec_authorized",
            "qec_circuit_003_authorized",
            "qldpc_forge_authorized",
        ]
        for key in prohibited:
            self.assertFalse(boundary[key], key)


if __name__ == "__main__":
    unittest.main()
