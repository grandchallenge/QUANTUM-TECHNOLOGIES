import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "reference" / "tcm_qdec_002.py"
SPEC = importlib.util.spec_from_file_location("tcm_qdec_002", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class TCMQDEC002Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry_path = ROOT / "registry" / "tcm-qdec-002.json"
        cls.tcm1_registry = json.loads((ROOT / "registry" / "tcm-qdec.json").read_text())
        cls.tcm1_evidence = json.loads((ROOT / "evidence" / "TCM-QDEC-001-report.json").read_text())
        cls.tcm1_promotion = json.loads(
            (ROOT / "reviews" / "QTR-TCM-QDEC-REVIEW-001" / "promotion-record.json").read_text()
        )
        cls.fixture1 = json.loads((ROOT / "evidence" / "QLDPC-FIXTURE-001-report.json").read_text())
        cls.fixture2 = json.loads((ROOT / "evidence" / "QLDPC-FIXTURE-002-report.json").read_text())
        cls.fixture2_promotion = json.loads(
            (ROOT / "reviews" / "QTR-QLDPC-REVIEW-002" / "promotion-record.json").read_text()
        )
        cls.experiment = MODULE.load_registry(cls.registry_path)
        cls.report = MODULE.evaluate(
            cls.experiment,
            cls.tcm1_registry,
            cls.tcm1_evidence,
            cls.tcm1_promotion,
            cls.fixture1,
            cls.fixture2,
            cls.fixture2_promotion,
        )

    def test_committed_evidence_exactly_replays(self):
        expected = json.loads((ROOT / "evidence" / "TCM-QDEC-002-report.json").read_text())
        self.assertEqual(self.report, expected)
        self.assertEqual(
            self.report["payload_sha256"],
            "efd9e76957421494897e2cc319137874b61093d66ea871f0202df3d07e6eb3c0",
        )

    def test_factorization_geometry_is_exact_and_bounded(self):
        g = self.report["factorization_geometry"]
        self.assertEqual(g["check_rank"], 7)
        self.assertEqual(g["combined_check_logical_rank"], 11)
        self.assertEqual(g["redundant_selector_bits"], 2)
        self.assertEqual(g["reachable_syndromes"], 128)
        self.assertEqual(g["logical_classes_per_syndrome"], 16)
        self.assertEqual(g["reachable_combined_labels"], 2048)
        self.assertEqual(g["selector_space_capacity"], 8192)
        self.assertEqual(g["stabilizer_span_size"], 128)
        self.assertTrue(g["stabilizers_zero_logical_label"])
        self.assertEqual(
            g["prefix_combined_ranks"],
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 11, 11, 11, 11, 11, 11, 11],
        )
        self.assertEqual(
            g["prefix_active_state_counts"],
            [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048],
        )
        self.assertEqual(g["peak_active_state_count"], 2048)
        self.assertEqual(
            g["column_signature_sha256"],
            "2010b2f40048062203e8ee7607989ee30797e5ec37b0e94d5a5fd4eac8bfd023",
        )

    def test_exact_score_and_class_mapping_digests(self):
        c = self.report["factorized_contraction"]
        self.assertEqual(c["transition_relaxations_per_algebra"], 32766)
        self.assertEqual(c["transition_relaxations_total"], 98298)
        self.assertEqual(c["final_score_entry_count_per_algebra"], 2048)
        self.assertEqual(c["sum_product_total_partition_mass"], 10**18)
        self.assertEqual(c["soft_tropical_total_partition_mass"], 3**18)
        self.assertEqual(
            c["minimum_weight_histogram_over_combined_labels"],
            {"0": 1, "1": 18, "2": 153, "3": 636, "4": 870, "5": 370},
        )
        self.assertEqual(
            c["canonical_class_mapping_sha256"],
            "0d907375404e37533a3dd182eccea7d6a3fd6637801745f8f5b39b7c4b683f8f",
        )
        self.assertEqual(
            c["score_table_sha256"],
            {
                "sum_product_bsc_p_0_1": "1b6bd71b9b05f169f57103ae71cd8b540f88e05dbe0302f2b4d9c2562a76a7be",
                "soft_tropical_base_2": "00c4b4c7612b6d05847963c4f8d432160cb2d6ec06fa4813700220461102bad5",
                "min_plus_hamming": "178a357cd13b2b9bbab03bad09f08efafecf37f2b59080bb3a6107e552e3b524",
            },
        )

    def test_factorized_decisions_equal_promoted_oracle(self):
        expected_sha = {
            "sum_product_bsc_p_0_1": "05dd32573ee965ce96caf707de3541f8be74b49317ad46b7929ef7dcf3bf64fc",
            "soft_tropical_base_2": "ea2a96e3878758cd2daebd28673d943c27740a3e1c3579d8429a8a658e567393",
            "min_plus_hamming": "88a9a766b64c7e476ac5bb4da877a2b1f6d4e88cee88cde6ea7461cc74179f3f",
        }
        expected_success = {
            "sum_product_bsc_p_0_1": 263,
            "soft_tropical_base_2": 262,
            "min_plus_hamming": 226,
        }
        for algebra in expected_sha:
            cell = self.report["factorized_decisions"][algebra]
            self.assertEqual(cell["decision_table_sha256"], expected_sha[algebra])
            self.assertEqual(cell["success_total"], expected_success[algebra])
            self.assertEqual(cell["failure_modes"]["nonzero_residual_syndrome"], 0)
        oracle = self.report["oracle_equivalence"]
        self.assertTrue(oracle["winning_class_tie_sets_exactly_equal"])
        self.assertTrue(oracle["decision_tables_exactly_equal"])
        self.assertEqual(oracle["winning_class_tie_set_cells_checked"], 384)
        self.assertEqual(oracle["decision_entries_checked"], 384)

    def test_tie_sets_and_envelopes_are_preserved(self):
        self.assertEqual(
            self.report["winning_class_tie_sets_sha256"],
            {
                "sum_product_bsc_p_0_1": "3778c019c7e235d916fa27616f83a9f8251a8c2a0276e09e0ea6dc1a6125cd60",
                "soft_tropical_base_2": "bf4297273ca05b1506bde6f5305464e5affdf78ba31b40e20a0fada3e26dd982",
                "min_plus_hamming": "1991fe00aaec2f8ce1163ca7b4192054002a2ef176d4839d6883c01f4e724007",
            },
        )
        expected = {
            "sum_product_bsc_p_0_1": (263, 263, 263),
            "soft_tropical_base_2": (262, 262, 262),
            "min_plus_hamming": (218, 263, 226),
        }
        for algebra, (lo, hi, default) in expected.items():
            t = self.report["tie_sensitivity"][algebra]
            self.assertEqual(
                t["frozen_corpus_success_count_envelope_over_winning_class_ties"],
                {"min": lo, "max": hi},
            )
            self.assertEqual(t["default_lowest_key_success_count"], default)

    def test_primary_path_does_not_claim_full_enumeration_or_scalability(self):
        self.assertFalse(self.report["factorized_contraction"]["primary_full_physical_state_enumeration"])
        self.assertEqual(self.report["oracle_equivalence"]["oracle_full_state_enumeration_count"], 262144)
        boundary = self.report["claim_boundary"]
        self.assertTrue(boundary["exact_factorized_equivalence_only"])
        self.assertFalse(boundary["scalable_tensor_contraction_claim"])
        self.assertFalse(boundary["asymptotic_or_practical_complexity_advantage_claim"])
        self.assertFalse(boundary["larger_code_performance_claim"])
        self.assertFalse(boundary["tcm_qdec_003_authorized"])
        self.assertFalse(boundary["qldpc_forge_authorized"])
        self.assertFalse(boundary["autonomous_search_authorized"])

    def _mutated_registry_must_fail(self, mutation):
        registry = json.loads(self.registry_path.read_text())
        mutation(registry["experiments"][0])
        path = ROOT / "tests" / ".tmp-tcm-qdec-002-registry.json"
        try:
            path.write_text(json.dumps(registry))
            with self.assertRaises(ValueError):
                MODULE.load_registry(path)
        finally:
            path.unlink(missing_ok=True)

    def test_registry_predecessor_drift_fails_closed(self):
        self._mutated_registry_must_fail(
            lambda e: e["predecessor"].__setitem__("evidence_payload_sha256", "0" * 64)
        )

    def test_registry_semiring_drift_fails_closed(self):
        self._mutated_registry_must_fail(
            lambda e: e["semirings"]["sum_product_bsc_p_0_1"].__setitem__("local_bit_weights", [8, 1])
        )

    def test_registry_contraction_order_drift_fails_closed(self):
        self._mutated_registry_must_fail(
            lambda e: e["representation"].__setitem__("qubit_contraction_order", list(reversed(range(18))))
        )

    def test_registry_downstream_authority_drift_fails_closed(self):
        self._mutated_registry_must_fail(
            lambda e: e["claim_boundary"].__setitem__("qldpc_forge_authorized", True)
        )

    def test_tcm_001_evidence_tamper_fails_closed(self):
        evidence = copy.deepcopy(self.tcm1_evidence)
        evidence["payload_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            MODULE.evaluate(
                self.experiment, self.tcm1_registry, evidence, self.tcm1_promotion,
                self.fixture1, self.fixture2, self.fixture2_promotion,
            )

    def test_tcm_001_promotion_tamper_fails_closed(self):
        promotion = copy.deepcopy(self.tcm1_promotion)
        promotion["status"] = "candidate_executable_not_promoted"
        with self.assertRaises(ValueError):
            MODULE.evaluate(
                self.experiment, self.tcm1_registry, self.tcm1_evidence, promotion,
                self.fixture1, self.fixture2, self.fixture2_promotion,
            )

    def test_logical_basis_tamper_fails_closed(self):
        fixture1 = copy.deepcopy(self.fixture1)
        fixture1["logical_basis"]["z_bitstrings"][0] = "0" * 18
        with self.assertRaises(ValueError):
            MODULE.evaluate(
                self.experiment, self.tcm1_registry, self.tcm1_evidence, self.tcm1_promotion,
                fixture1, self.fixture2, self.fixture2_promotion,
            )


if __name__ == "__main__":
    unittest.main()
