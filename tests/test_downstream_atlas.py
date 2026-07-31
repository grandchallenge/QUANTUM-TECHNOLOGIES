import copy
import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reference"))
sys.path.insert(0, str(ROOT / "ci"))

import downstream_atlas as da
import validate_downstream as vd


class DownstreamAtlasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads((ROOT / "registry/downstream-atlas.json").read_text())
        cls.wp00 = json.loads((ROOT / "registry/signal-candidates.json").read_text())

    def reports(self):
        payload = da.evaluate_registry(self.registry)
        return {
            package: {record["record_id"]: record for record in payload[package]}
            for package in ("WP01", "WP02", "WP03")
        }

    def test_binomial_orbits(self):
        for report in self.reports()["WP01"].values():
            self.assertTrue(report["orbit_sizes_match_binomial"])

    def test_parity_four_boundaries(self):
        self.assertEqual(
            self.reports()["WP01"]["sym_parity_n4"]["boundary_count"], 4
        )

    def test_exact_weight_two_boundaries(self):
        self.assertEqual(
            self.reports()["WP01"]["sym_exact_weight_2_n4"]["boundary_count"], 2
        )

    def test_or_rank_kernel(self):
        rows = self.reports()["WP02"]["lin_or_marked_row_n4"]["by_hamming_weight"]
        self.assertEqual((rows[0]["rank"], rows[0]["kernel_dimension"]), (0, 4))
        self.assertTrue(
            all((row["rank"], row["kernel_dimension"]) == (1, 3) for row in rows[1:])
        )

    def test_majority_singular_sign_loss(self):
        report = self.reports()["WP02"]["lin_majority_signed_scalar_n5"]
        self.assertTrue(report["signed_channel"]["semantically_sufficient"])
        self.assertFalse(report["singular_value_channel"]["semantically_sufficient"])
        self.assertEqual(
            report["singular_value_channel"]["cross_label_collision_pairs"], 126
        )

    def test_or_certificate_pair(self):
        report = self.reports()["WP03"]["or_n4_star_span"]
        self.assertTrue(report["certificate_objectives_match"])
        self.assertTrue(math.isclose(report["adversary_certificate"]["objective"], 2.0))

    def test_bad_star_fails_closed(self):
        bad = copy.deepcopy(self.registry["WP03"][0])
        bad["adversary_certificate"]["one_inputs"][0] = "1100"
        with self.assertRaises(ValueError):
            da.evaluate_wp03(bad)

    def test_unknown_record_field_fails_closed(self):
        bad = copy.deepcopy(self.registry["WP02"][0])
        bad["hidden_preprocessing"] = "answer"
        with self.assertRaises(vd.ValidationError):
            vd.validate_wp02(bad)

    def test_boolean_input_width_fails_closed(self):
        bad = copy.deepcopy(self.registry["WP01"][0])
        bad["input_width"] = True
        with self.assertRaises(vd.ValidationError):
            vd.validate_wp01(bad)

    def test_orbit_partition_length_fails_closed(self):
        bad = copy.deepcopy(self.registry["WP01"][0])
        bad["expected"]["orbit_sizes"] = [1, 4, 6, 5]
        with self.assertRaises(vd.ValidationError):
            vd.validate_wp01(bad)

    def test_duplicate_wp00_sources_fail_closed(self):
        bad = copy.deepcopy(self.registry["WP01"][0])
        bad["source_candidates"] = ["or_marked_amplitude_n4"] * 2
        with self.assertRaises(vd.ValidationError):
            vd.validate_wp01(bad)

    def test_marked_row_shape_fails_closed(self):
        bad = copy.deepcopy(self.registry["WP02"][0])
        bad["construction"]["operator_shape"] = [1, 1]
        with self.assertRaises(vd.ValidationError):
            vd.validate_wp02(bad)

    def test_nonpositive_centered_scale_fails_closed(self):
        bad = copy.deepcopy(self.registry["WP02"][3])
        bad["construction"]["scale"] = 0
        with self.assertRaises(vd.ValidationError):
            vd.validate_wp02(bad)

    def test_negative_status_must_match_singular_failure(self):
        bad = copy.deepcopy(self.registry["WP02"][1])
        bad["claim_status"] = "finite_exhaustive_evidence"
        with self.assertRaises(vd.ValidationError):
            vd.validate_wp02(bad)

    def test_duplicate_star_leaves_fail_closed(self):
        bad = copy.deepcopy(self.registry["WP03"][0])
        bad["adversary_certificate"]["one_inputs"][1] = bad[
            "adversary_certificate"
        ]["one_inputs"][0]
        with self.assertRaises(vd.ValidationError):
            vd.validate_wp03(bad)

    def test_wrong_span_vector_count_fails_closed(self):
        bad = copy.deepcopy(self.registry["WP03"][0])
        bad["span_program"]["input_vectors"].pop()
        with self.assertRaises(vd.ValidationError):
            vd.validate_wp03(bad)

    def test_wp01_source_interface_mismatch_fails_closed(self):
        bad = copy.deepcopy(self.registry)
        bad["WP01"][0]["source_candidates"] = ["majority_hamming_n5"]
        with self.assertRaises(vd.ValidationError):
            vd.validate_interfaces(bad, self.wp00)

    def test_wp02_source_interface_mismatch_fails_closed(self):
        bad = copy.deepcopy(self.registry)
        bad["WP02"][0]["source_invariant_record"] = "sym_parity_n4"
        with self.assertRaises(vd.ValidationError):
            vd.validate_interfaces(bad, self.wp00)

    def test_wp03_source_interface_mismatch_fails_closed(self):
        bad = copy.deepcopy(self.registry)
        bad["WP03"][0]["source_linearization_record"] = (
            "lin_majority_signed_scalar_n5"
        )
        with self.assertRaises(vd.ValidationError):
            vd.validate_interfaces(bad, self.wp00)


if __name__ == "__main__":
    unittest.main()
