import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "reference" / "qldpc_fixture_001.py"
SPEC = importlib.util.spec_from_file_location("qldpc_fixture_001", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class QLDPCFixture001Tests(unittest.TestCase):
    def setUp(self):
        self.fixture = MODULE.load_fixture(ROOT / "registry" / "qldpc-fixtures.json")

    def test_committed_evidence_exactly_replays(self):
        observed = MODULE.evaluate_fixture(self.fixture)
        expected = json.loads(
            (ROOT / "evidence" / "QLDPC-FIXTURE-001-report.json").read_text()
        )
        self.assertEqual(observed, expected)

    def test_core_exact_invariants(self):
        report = MODULE.evaluate_fixture(self.fixture)
        exact = report["exact_invariants"]
        self.assertEqual((exact["n"], exact["k"], exact["d"]), (18, 4, 4))
        self.assertEqual((exact["rank_hx"], exact["rank_hz"]), (7, 7))
        self.assertTrue(exact["css_commutes"])
        self.assertTrue(report["construction"]["hx_equals_hz"])
        self.assertEqual(set(exact["row_weights_hx"]), {6})
        self.assertEqual(set(exact["column_weights_hx"]), {3})
        self.assertEqual(report["logical_basis"]["canonical_pairing"], [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ])

    def test_reference_decoder_guarantees_all_single_qubit_errors(self):
        report = MODULE.evaluate_fixture(self.fixture)
        counts = report["reference_decoder"]["exact_success_counts_by_error_weight"]
        self.assertEqual(counts["0"], {"success": 1, "total": 1})
        self.assertEqual(counts["1"], {"success": 18, "total": 18})
        self.assertFalse(report["reference_decoder"]["performance_comparison_authorized"])

    def test_declared_parameter_tamper_fails_closed(self):
        fixture = copy.deepcopy(self.fixture)
        fixture["source_declared_code"]["d"] = 5
        with self.assertRaises(ValueError):
            MODULE.evaluate_fixture(fixture)

    def test_logical_operator_tamper_fails_closed(self):
        fixture = copy.deepcopy(self.fixture)
        fixture["logical_operators"]["x"][0] = ["L0"]
        with self.assertRaises(ValueError):
            MODULE.evaluate_fixture(fixture)

    def test_claim_boundary_tamper_fails_closed(self):
        fixture = copy.deepcopy(self.fixture)
        fixture["claim_boundary"]["tcm_qdec_authorized"] = True
        with self.assertRaises(ValueError):
            MODULE.evaluate_fixture(fixture)


if __name__ == "__main__":
    unittest.main()
