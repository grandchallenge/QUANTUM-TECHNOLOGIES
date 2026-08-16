import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "reference" / "tcm_qdec_001.py"
SPEC = importlib.util.spec_from_file_location("tcm_qdec_001", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

EXPECTED_PAYLOAD = "1b19addcda5e04cf78a834b2162fe0873ed5eb15f3330995d8354906944b7122"


class TCMQDEC001Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry_path = ROOT / "registry" / "tcm-qdec.json"
        cls.fixture1_path = ROOT / "evidence" / "QLDPC-FIXTURE-001-report.json"
        cls.fixture2_path = ROOT / "evidence" / "QLDPC-FIXTURE-002-report.json"
        cls.promotion2_path = (
            ROOT / "reviews" / "QTR-QLDPC-REVIEW-002" / "promotion-record.json"
        )
        cls.experiment = MODULE.load_registry(cls.registry_path)
        cls.fixture1 = MODULE.load_json(cls.fixture1_path)
        cls.fixture2 = MODULE.load_json(cls.fixture2_path)
        cls.promotion2 = MODULE.load_json(cls.promotion2_path)
        cls.report = MODULE.evaluate(
            cls.experiment, cls.fixture1, cls.fixture2, cls.promotion2
        )

    def test_committed_evidence_exactly_replays(self):
        expected = MODULE.load_json(ROOT / "evidence" / "TCM-QDEC-001-report.json")
        self.assertEqual(self.report, expected)
        self.assertEqual(self.report["payload_sha256"], EXPECTED_PAYLOAD)

    def test_full_state_space_geometry_and_frozen_corpus(self):
        state = self.report["state_space"]
        self.assertEqual(state["full_state_enumeration_count"], 262144)
        self.assertEqual(state["reachable_syndromes"], 128)
        self.assertEqual(state["states_per_syndrome"], 2048)
        self.assertEqual(state["stabilizer_span_size"], 128)
        self.assertEqual(state["logical_cosets_per_syndrome"], 16)
        self.assertEqual(state["corpus_size"], 4048)
        self.assertEqual(
            state["replayed_corpus_sha256"],
            "260b1a43cf1d777f28c475918e91a5f7cefc5d28a2bfb556338f7e30058f58a8",
        )

    def test_exact_six_cell_success_matrix(self):
        matrix = self.report["inference_matrix"]
        naive = matrix["representative_naive_marginals"]
        quotient = matrix["stabilizer_coset_aggregate"]
        self.assertEqual(naive["sum_product_bsc_p_0_1"]["success_total"], 37)
        self.assertEqual(naive["soft_tropical_base_2"]["success_total"], 1)
        self.assertEqual(naive["min_plus_hamming"]["success_total"], 37)
        self.assertEqual(quotient["sum_product_bsc_p_0_1"]["success_total"], 263)
        self.assertEqual(quotient["soft_tropical_base_2"]["success_total"], 262)
        self.assertEqual(quotient["min_plus_hamming"]["success_total"], 226)

    def test_representative_outputs_preserve_syndrome_failures_as_evidence(self):
        matrix = self.report["inference_matrix"]["representative_naive_marginals"]
        self.assertEqual(
            matrix["sum_product_bsc_p_0_1"]["decision_diagnostics"][
                "syndrome_invalid_decisions"
            ],
            91,
        )
        self.assertEqual(
            matrix["soft_tropical_base_2"]["decision_diagnostics"][
                "syndrome_invalid_decisions"
            ],
            127,
        )
        self.assertEqual(
            matrix["min_plus_hamming"]["decision_diagnostics"][
                "syndrome_invalid_decisions"
            ],
            91,
        )

    def test_quotient_outputs_realize_every_input_syndrome(self):
        quotient = self.report["inference_matrix"]["stabilizer_coset_aggregate"]
        for algebra in MODULE.SEMIRINGS:
            diagnostics = quotient[algebra]["decision_diagnostics"]
            self.assertEqual(diagnostics["syndrome_valid_decisions"], 128)
            self.assertEqual(diagnostics["syndrome_invalid_decisions"], 0)

    def test_quotient_repairs_matched_representative_without_hidden_breaks(self):
        comparisons = self.report["comparisons"]
        expected_repairs = {
            "sum_product_bsc_p_0_1": 226,
            "soft_tropical_base_2": 261,
            "min_plus_hamming": 189,
        }
        for algebra, repairs in expected_repairs.items():
            delta = comparisons[algebra]["quotient_vs_representative"]
            self.assertEqual(delta["repaired_by_second"], repairs)
            self.assertEqual(delta["broken_by_second"], 0)
            self.assertTrue(delta["repaired_witnesses"])

    def test_fixture_002_baselines_replay_and_net_gain_is_not_monotone_superiority(self):
        baselines = self.report["fixture_002_baselines"]
        self.assertEqual(baselines["exact_coset_lookup"]["success_total"], 240)
        self.assertEqual(baselines["greedy_syndrome_descent"]["success_total"], 125)
        sum_product = self.report["comparisons"]["sum_product_bsc_p_0_1"]
        self.assertEqual(sum_product["quotient_minus_fixture_002_exact_success_count"], 23)
        exact_delta = sum_product["quotient_vs_fixture_002_exact"]
        self.assertEqual(exact_delta["repaired_by_second"], 131)
        self.assertEqual(exact_delta["broken_by_second"], 108)

    def test_tie_sensitivity_is_retained(self):
        ties = self.report["tie_sensitivity"]
        self.assertEqual(
            ties["sum_product_bsc_p_0_1"][
                "frozen_corpus_success_count_envelope_over_winning_class_ties"
            ],
            {"min": 263, "max": 263},
        )
        self.assertTrue(
            ties["sum_product_bsc_p_0_1"][
                "success_count_invariant_under_winning_class_tie_break"
            ]
        )
        self.assertEqual(
            ties["soft_tropical_base_2"][
                "frozen_corpus_success_count_envelope_over_winning_class_ties"
            ],
            {"min": 262, "max": 262},
        )
        self.assertTrue(
            ties["soft_tropical_base_2"][
                "success_count_invariant_under_winning_class_tie_break"
            ]
        )
        self.assertEqual(
            ties["min_plus_hamming"][
                "frozen_corpus_success_count_envelope_over_winning_class_ties"
            ],
            {"min": 218, "max": 263},
        )
        self.assertEqual(ties["min_plus_hamming"]["default_lowest_key_success_count"], 226)
        self.assertFalse(
            ties["min_plus_hamming"][
                "success_count_invariant_under_winning_class_tie_break"
            ]
        )

    def test_registry_semiring_drift_fails_closed(self):
        registry = MODULE.load_json(self.registry_path)
        registry["experiments"][0]["semirings"]["soft_tropical_base_2"][
            "exact_state_weight"
        ] = "3**(n-hamming_weight)"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "registry.json"
            path.write_text(json.dumps(registry), encoding="utf-8")
            with self.assertRaises(ValueError):
                MODULE.load_registry(path)

    def test_registry_downstream_authority_tamper_fails_closed(self):
        registry = MODULE.load_json(self.registry_path)
        registry["experiments"][0]["claim_boundary"]["qldpc_forge_authorized"] = True
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "registry.json"
            path.write_text(json.dumps(registry), encoding="utf-8")
            with self.assertRaises(ValueError):
                MODULE.load_registry(path)

    def test_fixture_002_payload_tamper_fails_closed(self):
        fixture2 = copy.deepcopy(self.fixture2)
        fixture2["payload_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            MODULE.validate_predecessors(self.fixture1, fixture2, self.promotion2)

    def test_fixture_002_promotion_tamper_fails_closed(self):
        promotion = copy.deepcopy(self.promotion2)
        promotion["status"] = "candidate_executable_not_promoted"
        with self.assertRaises(ValueError):
            MODULE.validate_predecessors(self.fixture1, self.fixture2, promotion)

    def test_downstream_and_performance_authority_remain_closed(self):
        boundary = self.report["claim_boundary"]
        self.assertTrue(boundary["finite_semiring_comparison_only"])
        for key in (
            "scalable_tensor_contraction_claim",
            "general_qldpc_decoder_claim",
            "decoder_performance_superiority_claim",
            "bp_osd_performance_claim",
            "circuit_level_noise_claim",
            "hardware_validation_claim",
            "threshold_claim",
            "portable_latency_or_memory_claim",
            "learned_decoder_authorized",
            "tcm_qdec_002_authorized",
            "qldpc_forge_authorized",
            "autonomous_search_authorized",
        ):
            self.assertFalse(boundary[key], key)


if __name__ == "__main__":
    unittest.main()
