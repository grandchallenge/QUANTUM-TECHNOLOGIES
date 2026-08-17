import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "reference" / "tcm_qdec_004.py"
SPEC = importlib.util.spec_from_file_location("tcm_qdec_004", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class TCMQDEC004Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry_path = ROOT / "registry" / "tcm-qdec-004.json"
        cls.tcm3_registry = json.loads((ROOT / "registry" / "tcm-qdec-003.json").read_text())
        cls.tcm3_evidence = json.loads((ROOT / "evidence" / "TCM-QDEC-003-report.json").read_text())
        cls.tcm3_promotion = json.loads(
            (ROOT / "reviews" / "QTR-TCM-QDEC-REVIEW-003" / "promotion-record.json").read_text()
        )
        cls.experiment = MODULE.load_registry(cls.registry_path)
        cls.report = MODULE.evaluate(
            cls.experiment, cls.tcm3_registry, cls.tcm3_evidence, cls.tcm3_promotion
        )

    def test_committed_evidence_exactly_replays(self):
        expected = json.loads((ROOT / "evidence" / "TCM-QDEC-004-report.json").read_text())
        self.assertEqual(self.report, expected)
        self.assertEqual(
            self.report["payload_sha256"],
            "a5c7e59fa849ddc37c070d78d4a4dab8b07ae5ceccfecefeb5a20f4ae0dc83a7",
        )

    def test_compiled_object_is_structural_not_answer_cache(self):
        compiled = self.report["compiled_structure"]
        self.assertFalse(compiled["primary_object_is_complete_answer_cache"])
        self.assertEqual(compiled["selector_values_materialized_during_compilation"], 0)
        self.assertTrue(compiled["selector_parameters_enter_only_through_parameter_choice_nodes"])
        self.assertEqual(compiled["retained_reachable_nodes_total"], 1130)
        self.assertEqual(compiled["canonical_serialized_bytes_total"], 65506)
        expected = {
            "sum_product_bsc_p_0_1": (371, "74a20187b141813772400944962462b0fd4859f253b161bedc3d871231cfad8e"),
            "soft_tropical_base_2": (371, "e15b58e494d5ff75efd8778210d1d195701e71dea84a8d8dff4eafe02dcf2d68"),
            "min_plus_hamming": (388, "daaa544340d1d101c402f0f7be0d95eaf75c8f861fe7018f12cf29a797b35339"),
        }
        for algebra, (nodes, sha) in expected.items():
            cell = compiled["per_algebra"][algebra]
            self.assertEqual(cell["retained_reachable_nodes"], nodes)
            self.assertEqual(cell["canonical_sha256"], sha)
            self.assertLess(nodes, 2048)
            self.assertGreater(cell["hash_cons_reuses"], 0)

    def test_full_predecessor_semantic_boundary_is_exact(self):
        exact = self.report["semantic_equivalence"]
        self.assertEqual(exact["score_entries_checked"], 6144)
        self.assertEqual(exact["class_mapping_entries_checked"], 2048)
        self.assertEqual(exact["winning_class_tie_set_cells_checked"], 384)
        self.assertEqual(exact["decision_entries_checked"], 384)
        self.assertTrue(exact["score_tables_exactly_equal"])
        self.assertTrue(exact["class_mapping_exactly_equal"])
        self.assertTrue(exact["winning_class_tie_sets_exactly_equal"])
        self.assertTrue(exact["decision_tables_exactly_equal"])
        self.assertEqual(exact["score_table_sha256"], MODULE.EXPECTED_SCORE_SHA)
        self.assertEqual(exact["canonical_class_mapping_sha256"], MODULE.EXPECTED_MAPPING_SHA)
        self.assertEqual(exact["winning_class_tie_sets_sha256"], MODULE.EXPECTED_TIE_SHA)
        self.assertEqual(exact["decision_table_sha256"], MODULE.EXPECTED_DECISION_SHA)

    def test_min_plus_tie_ambiguity_is_retained(self):
        tie = self.report["tie_sensitivity"]["min_plus_hamming"]
        self.assertEqual(
            tie["frozen_corpus_success_count_envelope_over_winning_class_ties"],
            {"min": 218, "max": 263},
        )
        self.assertEqual(tie["default_lowest_key_success_count"], 226)
        self.assertFalse(tie["success_count_invariant_under_winning_class_tie_break"])

    def test_common_aop_accounting_is_exact_and_positive(self):
        cost = self.report["cost_accounting"]
        self.assertEqual(cost["aop_types"], MODULE.AOP_TYPES)
        self.assertEqual(cost["compile"]["aop_total"], 10160)
        self.assertEqual(cost["evaluate_all_2048_selectors"]["aop_total"], 12694528)
        self.assertEqual(cost["one_shot"]["aop_total"], 12704688)
        self.assertEqual(
            cost["tcm_qdec_003_reinstrumented_classwise_replay"]["aop_total"],
            14115840,
        )
        self.assertEqual(cost["one_shot_aop_reduction"], 1411152)
        self.assertTrue(cost["compiled_one_shot_uses_fewer_aops"])
        self.assertEqual(cost["break_even_complete_sweeps"], 1)
        self.assertFalse(cost["aop_total_is_runtime_model"])
        self.assertFalse(cost["runtime_or_memory_superiority_inferred"])

    def test_original_non_equivalent_counters_are_preserved(self):
        replay = self.report["cost_accounting"]["tcm_qdec_003_reinstrumented_classwise_replay"]
        self.assertEqual(replay["original_assignment_evaluations_preserved"], 774144)
        self.assertEqual(replay["original_predecessor_transition_relaxations_preserved"], 98298)
        self.assertTrue(replay["original_counters_not_translated_to_aop"])

    def test_adjudication_is_bounded_positive_result(self):
        result = self.report["adjudication"]
        self.assertEqual(result["outcome"], "EXACT_SHARED_COMPILATION_WITH_REDUCED_DUPLICATION")
        self.assertTrue(result["exact_semantics_preserved"])
        self.assertTrue(result["nontrivial_shared_structural_object"])
        self.assertTrue(result["complete_answer_cache_disallowed_and_not_used"])
        self.assertTrue(result["abstract_operation_reduction_observed"])
        self.assertFalse(result["runtime_superiority_claim"])
        self.assertFalse(result["memory_superiority_claim"])
        self.assertFalse(result["downstream_authority_created"])

    def test_downstream_claim_boundary_remains_closed(self):
        boundary = self.report["claim_boundary"]
        self.assertTrue(boundary["exact_shared_compilation_on_fixed_fixture_only"])
        self.assertFalse(boundary["runtime_superiority_claim"])
        self.assertFalse(boundary["memory_superiority_claim"])
        self.assertFalse(boundary["asymptotic_complexity_claim"])
        self.assertFalse(boundary["bounded_width_family_claim"])
        self.assertFalse(boundary["larger_code_authorized"])
        self.assertFalse(boundary["multi_size_scaling_authorized"])
        self.assertFalse(boundary["bp_min_sum_bp_osd_comparison_authorized"])
        self.assertFalse(boundary["circuit_level_noise_authorized"])
        self.assertFalse(boundary["qldpc_forge_authorized"])

    def test_repeated_evaluation_does_not_recompile(self):
        rows, _ = MODULE.construct_code()
        scopes = [
            tuple(variable for variable, row in enumerate(rows[:7]) if row & (1 << qubit))
            for qubit in range(18)
        ]
        dag, root, metadata = MODULE.compile_symbolic("sum9", scopes)
        node_count = len(dag.nodes)
        compile_vector = dict(dag.ledger.vector())
        first = MODULE.Ledger()
        second = MODULE.Ledger()
        value_a, _ = dag.evaluate(root, 0, first)
        value_b, _ = dag.evaluate(root, 1, second)
        self.assertNotEqual(value_a, value_b)
        self.assertEqual(len(dag.nodes), node_count)
        self.assertEqual(dag.ledger.vector(), compile_vector)
        self.assertEqual(metadata["retained_reachable_nodes"], 371)

    def test_compiled_object_tamper_changes_digest(self):
        rows, _ = MODULE.construct_code()
        scopes = [
            tuple(variable for variable, row in enumerate(rows[:7]) if row & (1 << qubit))
            for qubit in range(18)
        ]
        dag, root, metadata = MODULE.compile_symbolic("sum9", scopes)
        obj = dag.canonical_object(root)
        tampered = copy.deepcopy(obj)
        tampered["nodes"][0]["value"] = 123456
        self.assertEqual(MODULE.digest(obj), metadata["canonical_sha256"])
        self.assertNotEqual(MODULE.digest(tampered), metadata["canonical_sha256"])

    def _mutated_registry_must_fail(self, mutation):
        registry = json.loads(self.registry_path.read_text())
        mutation(registry["experiments"][0])
        path = ROOT / "tests" / ".tmp-tcm-qdec-004-registry.json"
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

    def test_registry_ant_cache_drift_fails_closed(self):
        self._mutated_registry_must_fail(
            lambda e: e["representation"].__setitem__(
                "anti_cache_rule", "complete_answer_cache_is_allowed"
            )
        )

    def test_registry_operation_taxonomy_drift_fails_closed(self):
        self._mutated_registry_must_fail(
            lambda e: e["representation"].__setitem__(
                "operation_taxonomy", e["representation"]["operation_taxonomy"][:-1]
            )
        )

    def test_registry_downstream_authority_drift_fails_closed(self):
        self._mutated_registry_must_fail(
            lambda e: e["claim_boundary"].__setitem__("larger_code_authorized", True)
        )

    def test_tcm_003_evidence_tamper_fails_closed(self):
        evidence = copy.deepcopy(self.tcm3_evidence)
        evidence["payload_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            MODULE.validate_predecessor(self.tcm3_registry, evidence, self.tcm3_promotion)

    def test_tcm_003_promotion_tamper_fails_closed(self):
        promotion = copy.deepcopy(self.tcm3_promotion)
        promotion["status"] = "candidate_executable_not_promoted"
        with self.assertRaises(ValueError):
            MODULE.validate_predecessor(self.tcm3_registry, self.tcm3_evidence, promotion)


if __name__ == "__main__":
    unittest.main()
