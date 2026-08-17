import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("qldpc_scale_001a", ROOT / "reference" / "qldpc_scale_001a.py")
M = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(M)


class QLDPCScale001ATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry_path = ROOT / "registry" / "qldpc-scale-001a.json"
        cls.registry = M.load_registry(cls.registry_path)
        cls.pred_registry = json.loads((ROOT / "registry" / "tcm-qdec-004.json").read_text())
        cls.pred_evidence = json.loads((ROOT / "evidence" / "TCM-QDEC-004-report.json").read_text())
        cls.pred_promotion = json.loads((ROOT / M.PREDECESSOR["promotion_record_path"]).read_text())
        cls.report = M.evaluate(cls.registry, cls.pred_registry, cls.pred_evidence, cls.pred_promotion, full_validation=False)

    def test_committed_evidence_exactly_replays(self):
        expected = json.loads((ROOT / "evidence" / "QLDPC-SCALE-001A-report.json").read_text())
        if self.report != expected:
            for key in sorted(set(self.report) | set(expected)):
                if self.report.get(key) != expected.get(key):
                    print("QLDPC_SCALE_001A_DIFF", key)
                    print("OBSERVED", json.dumps(self.report.get(key), sort_keys=True))
                    print("EXPECTED", json.dumps(expected.get(key), sort_keys=True))
        self.assertEqual(self.report, expected)
        self.assertEqual(self.report["payload_sha256"], "198bb28f47844aa98efa20d8c838c48870a8aef41ccfda266b16661677e363e1")

    def test_source_and_code_gate(self):
        s, c = self.report["source_binding"], self.report["code_reconstruction"]
        self.assertEqual((s["source_commit"], s["source_blob_sha"]), ("fa77e3333d3ec44c79d8f914dd24c040d1da471b", "7ec5a36732a2a6dd229ab74405dedf36139ccda4"))
        self.assertEqual((s["ell"], s["m"], s["a_exponents"], s["b_exponents"]), (6, 6, [3,1,2], [3,1,2]))
        self.assertEqual((c["hx_shape"], c["hz_shape"], c["hx_rank"], c["hz_rank"], c["k"]), ([36,72], [36,72], 30, 30, 12))
        self.assertEqual(c["css_commutation_nonzero_entries"], 0)
        self.assertEqual(c["hx_row_weight_histogram"], {"6":36})
        self.assertEqual(c["hx_column_weight_histogram"], {"3":72})

    def test_distance_is_source_reported_only(self):
        self.assertEqual(self.report["adjudication"]["distance_status"], "SOURCE_REPORTED_DISTANCE")
        self.assertFalse(self.report["source_binding"]["independent_distance_certification_performed"])
        self.assertFalse(self.report["claim_boundary"]["distance_independently_certified"])

    def test_factor_and_selector_geometry(self):
        c, f = self.report["code_reconstruction"], self.report["factor_graph"]
        self.assertEqual((c["selector_rank"], c["logical_classes_per_syndrome"], f["independent_stabilizer_generators"]), (42, 4096, 30))
        self.assertEqual(f["factor_arity_histogram"], {"1":7,"2":22,"3":43})
        self.assertEqual(f["factor_scope_sha256"], M.EXPECTED_DIGESTS["factor_scopes"])

    def test_orders_are_predeclared_and_primary_fixed(self):
        a = self.report["elimination_order_audit"]
        self.assertEqual(a["induced_width"], {"lexicographic":24,"min_degree":18,"min_fill":18})
        self.assertEqual(a["peak_joint_table_entries"]["min_fill"], 1 << 19)
        self.assertEqual(a["primary_order"], "min_fill")
        self.assertFalse(a["primary_order_switched_post_hoc"])
        self.assertFalse(a["global_treewidth_optimum_certified"])
        self.assertTrue(a["lexicographic_diagnostic_exceeds_primary_peak_table_cap"])
        self.assertEqual(a["order_record_sha256"], M.EXPECTED_DIGESTS["orders"])

    def test_all_primary_compilation_caps_pass(self):
        cert = self.report["symbolic_representation_certificate"]
        self.assertTrue(cert["all_primary_compilation_caps_pass"])
        for cell in cert["resource_cap_checks"].values():
            self.assertTrue(all(cell.values()))
        self.assertFalse(self.report["resource_accounting"]["wall_clock_time_used_for_adjudication"])

    def test_compiled_descriptor_is_not_answer_cache(self):
        d = self.report["compiled_descriptor"]
        self.assertFalse(d["primary_object_is_answer_cache"])
        self.assertEqual((d["answer_cache_entries"], d["selector_values_materialized_during_compilation"]), (0,0))
        self.assertFalse(d["repeated_evaluation_recompiles_descriptor"])
        self.assertEqual((d["step_count"], d["canonical_serialized_bytes"], d["canonical_sha256"]), (30,14912,M.EXPECTED_DIGESTS["compiled_descriptor"]))

    def test_symbolic_identities(self):
        for algebra, wanted in M.EXPECTED_SYMBOLIC.items():
            got = self.report["symbolic_representation_certificate"]["per_algebra"][algebra]
            for key, value in wanted.items():
                self.assertEqual(got[key], value)

    def test_frozen_validation_is_exact_not_exhaustive(self):
        v = self.report["selector_validation"]
        self.assertEqual((v["total_frozen_validation_count"], v["pseudorandom_count"], v["selector_rank"]), (300,256,42))
        self.assertTrue(v["compiled_vs_independent_oracle_all_equal"])
        self.assertFalse(v["exhaustive_all_selector_equivalence"])
        self.assertEqual(v["validation_set_sha256"], M.EXPECTED_DIGESTS["validation_set"])
        self.assertEqual(v["validation_outputs_sha256"], M.EXPECTED_DIGESTS["validation_outputs"])

    def test_descriptor_reuse_does_not_recompile(self):
        code = M.construct_code()
        audit = M.order_audit(code["scopes"])
        descriptor, meta = M.compile_descriptor(code["scopes"], code["selector_basis_qubits"], audit["orders"]["min_fill"])
        before = M.digest(descriptor)
        self.assertNotEqual(M.evaluate_compiled_descriptor(0, code["scopes"], descriptor), M.evaluate_compiled_descriptor(1, code["scopes"], descriptor))
        self.assertEqual((M.digest(descriptor), before, meta["canonical_sha256"]), (before, M.EXPECTED_DIGESTS["compiled_descriptor"], before))

    def test_candidate_adjudication_is_bounded(self):
        a = self.report["adjudication"]
        self.assertEqual(a["outcome"], "FEASIBLE_EXACT_WITHIN_BOUND")
        self.assertTrue(a["source_reconstruction_certified"])
        self.assertTrue(a["factor_graph_structural_audit_completed"])
        self.assertTrue(a["primary_parametric_compilation_within_all_declared_caps"])
        self.assertTrue(a["exact_semantic_equality_on_frozen_validation_set"])
        self.assertFalse(a["controlled_approximation_used"])
        self.assertFalse(a["downstream_authority_created"])

    def test_all_downstream_claims_remain_closed(self):
        b = self.report["claim_boundary"]
        self.assertTrue(b["single_larger_instance_feasibility_only"])
        for k in ("exhaustive_all_selector_equivalence","family_relation_to_18_qubit_fixture_certified","multi_size_scaling_claim","bounded_treewidth_family_claim","asymptotic_complexity_claim","runtime_superiority_claim","memory_superiority_claim","controlled_approximation_authorized","bp_min_sum_bp_osd_comparison_authorized","circuit_level_noise_authorized","repeated_syndrome_authorized","learned_decoder_authorized","adaptive_online_ordering_authorized","qldpc_scale_001b_authorized","qldpc_forge_authorized","autonomous_search_authorized"):
            self.assertFalse(b[k], k)

    def _registry_mutation_fails(self, mutate):
        data = json.loads(self.registry_path.read_text())
        mutate(data["experiments"][0])
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "r.json"; p.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                M.load_registry(p)

    def test_target_drift_fails(self):
        self._registry_mutation_fails(lambda e: e["target"]["source"].__setitem__("ell", 7))

    def test_order_drift_fails(self):
        self._registry_mutation_fails(lambda e: e["order_policy"].__setitem__("primary", "deterministic_min_degree"))

    def test_resource_cap_drift_fails(self):
        self._registry_mutation_fails(lambda e: e["resource_envelope"].__setitem__("max_peak_joint_table_entries", 1 << 21))

    def test_validation_sample_drift_fails(self):
        self._registry_mutation_fails(lambda e: e["validation_policy"].__setitem__("random_distinct_non_reserved", 255))

    def test_taxonomy_drift_fails(self):
        self._registry_mutation_fails(lambda e: e["operation_taxonomy"]["extended_validation_types"].pop())

    def test_downstream_authority_drift_fails(self):
        self._registry_mutation_fails(lambda e: e["claim_boundary"].__setitem__("qldpc_scale_001b_authorized", True))

    def test_predecessor_evidence_tamper_fails(self):
        evidence = copy.deepcopy(self.pred_evidence); evidence["payload_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            M.validate_predecessor(self.pred_registry, evidence, self.pred_promotion)

    def test_predecessor_promotion_tamper_fails(self):
        promotion = copy.deepcopy(self.pred_promotion); promotion["status"] = "candidate_executable_not_promoted"
        with self.assertRaises(ValueError):
            M.validate_predecessor(self.pred_registry, self.pred_evidence, promotion)


if __name__ == "__main__":
    unittest.main()
