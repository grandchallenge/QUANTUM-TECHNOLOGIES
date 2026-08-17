import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "reference" / "tcm_qdec_003.py"
SPEC = importlib.util.spec_from_file_location("tcm_qdec_003", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class TCMQDEC003Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry_path = ROOT / "registry" / "tcm-qdec-003.json"
        cls.tcm2_registry = json.loads((ROOT / "registry" / "tcm-qdec-002.json").read_text())
        cls.tcm2_evidence = json.loads((ROOT / "evidence" / "TCM-QDEC-002-report.json").read_text())
        cls.tcm2_promotion = json.loads(
            (ROOT / "reviews" / "QTR-TCM-QDEC-REVIEW-002" / "promotion-record.json").read_text()
        )
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
            cls.tcm2_registry,
            cls.tcm2_evidence,
            cls.tcm2_promotion,
            cls.tcm1_registry,
            cls.tcm1_evidence,
            cls.tcm1_promotion,
            cls.fixture1,
            cls.fixture2,
            cls.fixture2_promotion,
        )

    def test_committed_evidence_exactly_replays(self):
        expected = json.loads((ROOT / "evidence" / "TCM-QDEC-003-report.json").read_text())
        self.assertEqual(self.report, expected)
        self.assertEqual(
            self.report["payload_sha256"],
            "f0ecdae04f3da4f0508454da59ce406a4e6c461f88f1784279cb6d7e360b595f",
        )

    def test_stabilizer_and_selector_bases_are_exact(self):
        geometry = self.report["basis_geometry"]
        self.assertEqual(geometry["stabilizer_basis_row_indices"], list(range(7)))
        self.assertEqual(geometry["stabilizer_basis_rank"], 7)
        self.assertEqual(geometry["stabilizer_basis_span_size"], 128)
        self.assertTrue(geometry["stabilizer_basis_equals_promoted_span"])
        self.assertEqual(geometry["selector_seed_basis_qubits"], list(range(11)))
        self.assertEqual(geometry["selector_seed_basis_rank"], 11)
        self.assertEqual(geometry["reachable_selector_count"], 2048)

    def test_factor_scopes_are_sparse_and_bound(self):
        geometry = self.report["basis_geometry"]
        self.assertEqual(geometry["factor_scope_size_histogram"], {"1": 2, "2": 8, "3": 8})
        self.assertEqual(geometry["maximum_initial_factor_arity"], 3)
        self.assertEqual(
            geometry["factor_scope_sha256"],
            "9b9f68ff6cf22447892c6d853defa6daf5f08c5859ffd4352500d1e11b89052d",
        )

    def test_all_5040_elimination_orders_are_audited(self):
        audit = self.report["elimination_order_audit"]
        self.assertEqual(audit["orders_checked"], 5040)
        self.assertEqual(audit["induced_width_histogram"], {"4": 720, "5": 4320})
        self.assertEqual(audit["minimum_induced_width"], 4)
        self.assertEqual(audit["optimal_order_count"], 720)
        self.assertEqual(
            audit["frozen_lexicographically_first_optimal_order"],
            [2, 4, 0, 1, 3, 5, 6],
        )
        self.assertEqual(audit["peak_joint_arity"], 5)
        self.assertEqual(audit["peak_joint_table_entries"], 32)
        self.assertEqual(audit["maximum_output_factor_arity"], 4)
        self.assertEqual(audit["maximum_output_factor_entries"], 16)
        self.assertEqual(audit["assignment_evaluations_per_class_contraction"], 126)
        self.assertEqual(audit["output_factor_entries_emitted_per_class_contraction"], 63)
        self.assertEqual(
            audit["order_audit_sha256"],
            "76e357c69d25f552d21a114c632a322256087b0fd1036d7ee914c02e39c7aff0",
        )
        self.assertEqual(
            audit["frozen_order_trace_sha256"],
            "898704d5fa4599dd4e11b1e85765046d0b6bb41ddfedaa3d4e329cf682dc6566",
        )

    def test_score_and_mapping_identities_equal_predecessor(self):
        contraction = self.report["degeneracy_contraction"]
        self.assertEqual(
            contraction["canonical_class_mapping_sha256"],
            "0d907375404e37533a3dd182eccea7d6a3fd6637801745f8f5b39b7c4b683f8f",
        )
        self.assertEqual(
            contraction["score_table_sha256"],
            {
                "sum_product_bsc_p_0_1": "1b6bd71b9b05f169f57103ae71cd8b540f88e05dbe0302f2b4d9c2562a76a7be",
                "soft_tropical_base_2": "00c4b4c7612b6d05847963c4f8d432160cb2d6ec06fa4813700220461102bad5",
                "min_plus_hamming": "178a357cd13b2b9bbab03bad09f08efafecf37f2b59080bb3a6107e552e3b524",
            },
        )
        predecessor = self.report["predecessor_equivalence"]
        self.assertTrue(predecessor["score_tables_exactly_equal"])
        self.assertTrue(predecessor["class_mapping_exactly_equal"])
        self.assertEqual(predecessor["score_entries_checked"], 6144)
        self.assertEqual(predecessor["class_mapping_entries_checked"], 2048)

    def test_decisions_and_ties_equal_predecessor(self):
        expected_decision = {
            "sum_product_bsc_p_0_1": "05dd32573ee965ce96caf707de3541f8be74b49317ad46b7929ef7dcf3bf64fc",
            "soft_tropical_base_2": "ea2a96e3878758cd2daebd28673d943c27740a3e1c3579d8429a8a658e567393",
            "min_plus_hamming": "88a9a766b64c7e476ac5bb4da877a2b1f6d4e88cee88cde6ea7461cc74179f3f",
        }
        expected_tie = {
            "sum_product_bsc_p_0_1": "3778c019c7e235d916fa27616f83a9f8251a8c2a0276e09e0ea6dc1a6125cd60",
            "soft_tropical_base_2": "bf4297273ca05b1506bde6f5305464e5affdf78ba31b40e20a0fada3e26dd982",
            "min_plus_hamming": "1991fe00aaec2f8ce1163ca7b4192054002a2ef176d4839d6883c01f4e724007",
        }
        self.assertEqual(self.report["winning_class_tie_sets_sha256"], expected_tie)
        for algebra, sha in expected_decision.items():
            self.assertEqual(
                self.report["degeneracy_decisions"][algebra]["decision_table_sha256"],
                sha,
            )
        predecessor = self.report["predecessor_equivalence"]
        self.assertTrue(predecessor["winning_class_tie_sets_exactly_equal"])
        self.assertTrue(predecessor["decision_tables_exactly_equal"])
        self.assertEqual(predecessor["winning_class_tie_set_cells_checked"], 384)
        self.assertEqual(predecessor["decision_entries_checked"], 384)

    def test_frozen_corpus_and_min_plus_ambiguity_are_preserved(self):
        expected = {
            "sum_product_bsc_p_0_1": (263, 263, 263),
            "soft_tropical_base_2": (262, 262, 262),
            "min_plus_hamming": (218, 263, 226),
        }
        for algebra, (lo, hi, default) in expected.items():
            self.assertEqual(
                self.report["degeneracy_decisions"][algebra]["success_total"],
                default,
            )
            tie = self.report["tie_sensitivity"][algebra]
            self.assertEqual(
                tie["frozen_corpus_success_count_envelope_over_winning_class_ties"],
                {"min": lo, "max": hi},
            )
            self.assertEqual(tie["default_lowest_key_success_count"], default)

    def test_operation_tradeoff_is_retained_not_laundered(self):
        contraction = self.report["degeneracy_contraction"]
        self.assertEqual(contraction["class_contractions_total"], 6144)
        self.assertEqual(contraction["assignment_evaluations_total"], 774144)
        self.assertEqual(contraction["predecessor_transition_relaxations_total"], 98298)
        tradeoff = contraction["operation_count_tradeoff"]
        self.assertGreater(
            tradeoff["tcm_qdec_003_assignment_evaluations"],
            tradeoff["tcm_qdec_002_transition_relaxations"],
        )
        self.assertEqual(tradeoff["reduced_ratio"], [43008, 5461])
        self.assertTrue(tradeoff["metrics_are_not_runtime_equivalent"])
        self.assertFalse(tradeoff["arithmetic_reduction_claim"])

    def test_primary_path_and_claim_boundary_remain_bounded(self):
        self.assertFalse(
            self.report["degeneracy_contraction"]["primary_full_physical_state_enumeration"]
        )
        self.assertFalse(
            self.report["predecessor_equivalence"]["oracle_primary_full_physical_state_enumeration"]
        )
        boundary = self.report["claim_boundary"]
        self.assertTrue(boundary["exact_degeneracy_factor_equivalence_only"])
        self.assertTrue(boundary["bounded_exhaustive_order_audit_only"])
        self.assertFalse(boundary["bounded_width_family_claim"])
        self.assertFalse(boundary["scalable_tensor_contraction_claim"])
        self.assertFalse(boundary["asymptotic_or_practical_complexity_advantage_claim"])
        self.assertFalse(boundary["runtime_or_memory_superiority_claim"])
        self.assertFalse(boundary["adaptive_online_contraction_order_authorized"])
        self.assertFalse(boundary["tcm_qdec_004_authorized"])
        self.assertFalse(boundary["qldpc_forge_authorized"])
        self.assertFalse(boundary["autonomous_search_authorized"])

    def _mutated_registry_must_fail(self, mutation):
        registry = json.loads(self.registry_path.read_text())
        mutation(registry["experiments"][0])
        path = ROOT / "tests" / ".tmp-tcm-qdec-003-registry.json"
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

    def test_registry_stabilizer_basis_drift_fails_closed(self):
        self._mutated_registry_must_fail(
            lambda e: e["representation"].__setitem__(
                "expected_stabilizer_basis_row_indices", [0, 1, 2, 3, 4, 5, 7]
            )
        )

    def test_registry_seed_basis_drift_fails_closed(self):
        self._mutated_registry_must_fail(
            lambda e: e["representation"].__setitem__(
                "expected_selector_seed_qubits", list(range(10)) + [11]
            )
        )

    def test_registry_elimination_order_drift_fails_closed(self):
        self._mutated_registry_must_fail(
            lambda e: e["representation"].__setitem__(
                "frozen_elimination_order", [4, 2, 0, 1, 3, 5, 6]
            )
        )

    def test_registry_semiring_drift_fails_closed(self):
        self._mutated_registry_must_fail(
            lambda e: e["semirings"]["sum_product_bsc_p_0_1"].__setitem__(
                "local_bit_weights", [8, 1]
            )
        )

    def test_registry_downstream_authority_drift_fails_closed(self):
        self._mutated_registry_must_fail(
            lambda e: e["claim_boundary"].__setitem__("qldpc_forge_authorized", True)
        )

    def test_tcm_002_evidence_tamper_fails_closed(self):
        evidence = copy.deepcopy(self.tcm2_evidence)
        evidence["payload_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            MODULE.evaluate(
                self.experiment,
                self.tcm2_registry,
                evidence,
                self.tcm2_promotion,
                self.tcm1_registry,
                self.tcm1_evidence,
                self.tcm1_promotion,
                self.fixture1,
                self.fixture2,
                self.fixture2_promotion,
            )

    def test_tcm_002_promotion_tamper_fails_closed(self):
        promotion = copy.deepcopy(self.tcm2_promotion)
        promotion["status"] = "candidate_executable_not_promoted"
        with self.assertRaises(ValueError):
            MODULE.evaluate(
                self.experiment,
                self.tcm2_registry,
                self.tcm2_evidence,
                promotion,
                self.tcm1_registry,
                self.tcm1_evidence,
                self.tcm1_promotion,
                self.fixture1,
                self.fixture2,
                self.fixture2_promotion,
            )


if __name__ == "__main__":
    unittest.main()
