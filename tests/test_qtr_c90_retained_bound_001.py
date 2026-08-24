from __future__ import annotations
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];REF=ROOT/"reference"
if str(REF) not in sys.path:sys.path.insert(0,str(REF))
import qldpc_scale_001a_symbolic as sym
import qtr_c90_retained_bound_001 as t

class TestQTRC90RetainedBound001(unittest.TestCase):
    def test_manifest_authority_and_boundary(self):
        m=t.manifest();self.assertEqual(m["manifest_payload_sha256"],"d9072de9631901a0b97df61c14b8c5dc9d5de7d21ad9d7e181765c69fad223c2");self.assertEqual(m["authority"]["execution_issue"],106);self.assertEqual(m["authority"]["human_steward_comment"],5391086069);self.assertEqual(m["authority"]["protected_predecessor_merge"],"b7e5127fed532a8bc6dc6703bfcac3f58882477f");self.assertEqual(m["bound_invariant"]["formula"],"|K_reachable| <= U_Bk <= U_B0");self.assertEqual(m["abstract_state"]["max_abstract_state_records"],8192)
        for k in ["full_c90_materialization_authorized","canonical_node_set_construction_authorized","frozen_307_validation_authorized","new_structural_method_authorized","adaptive_order_search_authorized","factor_or_aop_coordinate_change_authorized","physical_model_change_authorized","cap_amendment_authorized","probabilistic_distinct_count_certification_authorized","empirical_deduplication_extrapolation_authorized","semantic_simplification_authorized","approximation_authorized","accelerator_native_qec_authorized","qec_circuit_003_authorized","qldpc_forge_authorized"]:self.assertFalse(m["claim_boundary"][k],k)
    def test_predecessors(self):
        r,s,c=t.preds();self.assertEqual(r["payload_sha256"],"0ea802c6ce9c584c52bbc5608ac4a94abec5f29c2939e5c226386c4581205195");self.assertEqual(s["payload_sha256"],"ade245552af2f88d5ecb8c0b7f8eb363510ed678908fb80462b911255dd63d67");self.assertEqual(c["payload_sha256"],"198bb28f47844aa98efa20d8c838c48870a8aef41ccfda266b16661677e363e1");self.assertFalse(r["materialization_performed"]);self.assertFalse(s["phase_d_reached"]);self.assertFalse(s["phase_e_reached"])
    def test_gate_integer_arithmetic(self):
        for live,expected in [(67125266,23808849),(67127314,23808740)]:self.assertEqual(t.ceiling(live)["gate_compatible_node_ceiling"],expected)
    def test_toy_bounds_sound(self):
        scopes=[(0,1),(1,2),(0,2)];sel=[0,2];order=[0,1,2]
        for a in t.ALGS:
            ex=sym.compile_symbolic_metadata(scopes,sel,order,a);vs,_=t.bounds(scopes,sel,order,a,ex["compile_aop"]["NODE_INTERN"]);b0=vs[t.REFS[0]]
            self.assertEqual(b0,ex["compile_aop"]["NODE_INTERN"])
            for r,v in vs.items():self.assertGreaterEqual(v,ex["node_count"],r);self.assertLessEqual(v,b0,r)
            self.assertLessEqual(vs[t.REFS[3]],vs[t.REFS[2]])
    def test_c90_path_never_calls_exact_compiler(self):
        src=(REF/"qtr_c90_retained_bound_001.py").read_text();chunk=src[src.index("def c90run"):src.index("\ndef write",src.index("def c90run"))];self.assertNotIn("compile_symbolic_metadata",chunk);self.assertNotIn("run_validation_parallel",chunk)
if __name__=="__main__":unittest.main()
