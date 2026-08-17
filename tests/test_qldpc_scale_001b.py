from __future__ import annotations
import copy, json, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "reference"
if str(REF) not in sys.path:
    sys.path.insert(0, str(REF))

import qldpc_scale_001b as q
import qldpc_scale_001b_report as qreport

class QLDPCScale001BTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = q.load_manifest(ROOT / q.MANIFEST_PATH)
        cls.report = qreport.evaluate(cls.manifest)
        cls.committed = json.loads((ROOT / "evidence/QLDPC-SCALE-001B-report.json").read_text())

    def test_committed_evidence_exactly_replays(self):
        self.assertEqual(self.report, self.committed)
        unsigned = dict(self.committed)
        payload = unsigned.pop("payload_sha256")
        self.assertEqual(payload, "6b8076376eb621710d993d1cb8768c7d4c03b7fe9d67802e6ae2e77212b610fc")
        self.assertEqual(q.digest(unsigned), payload)

    def test_manifest_and_authority_are_frozen(self):
        self.assertEqual(self.manifest["manifest_payload_sha256"], q.MANIFEST_PAYLOAD)
        self.assertEqual([x["n"] for x in self.manifest["ladder"]], [72,90,108,144,288,784])
        self.assertEqual(self.report["authority"]["authorization_comment"], 5315569335)
        self.assertEqual(self.report["manifest"]["commit"], "3fd6d882a5992c1be82e11f1f315a53130ffff8c")

    def test_exact_code_dimensions_and_css_gate(self):
        expected = {72:(12,30,42),90:(8,41,49),108:(8,50,58),144:(12,66,78),288:(12,138,150),784:(24,380,404)}
        for row in self.report["rungs"]:
            k,stab,selector = expected[row["n"]]
            self.assertEqual(row["k"], k)
            self.assertEqual(row["hx_rank"], stab)
            self.assertEqual(row["hz_rank"], stab)
            self.assertEqual(row["selector_rank"], selector)
            self.assertEqual(row["logical_dimension"], k)
            self.assertEqual(row["css_commutation_nonzero_entries"], 0)
            self.assertEqual(row["row_weight_histogram"], {"6": row["n"]//2})
            self.assertEqual(row["column_weight_histogram"], {"3": row["n"]})

    def test_anchor_replays_promoted_001a_identities(self):
        anchor = self.report["rungs"][0]
        self.assertEqual(anchor["n"], 72)
        self.assertEqual(anchor["source_and_basis_digests"]["hx_sha256"], "6c01bd1eceb703a1afbd9897c9ce3810d951bc0d1284588607775e9f875740f2")
        self.assertEqual(anchor["source_and_basis_digests"]["selector_basis_sha256"], "26a3b1ded24edbd0498eb915b7c3209db309be4a1cff8446149d2f78e0f7e524")
        self.assertEqual(anchor["order_audit"]["order_record_sha256"], "304b71f9046a7675c696b97fa7cc1cb0e7d1f14c4a6831e7d89f2f411a7fae4a")

    def test_named_order_widths_are_exact(self):
        self.assertEqual(self.report["finite_ladder"]["named_order_widths"], {
            "lexicographic":[24,28,33,31,71,253],
            "min_fill":[18,25,30,34,79,201],
            "min_degree":[18,25,30,38,83,223],
        })
        for row in self.report["rungs"]:
            self.assertFalse(row["order_audit"]["global_treewidth_optimum_certified"])

    def test_structural_caps_pass_all_post_anchor_rungs(self):
        expected_totals = {90:245158,108:463573,144:957323,288:13239627,784:509630167}
        expected_peaks = {90:1259,108:1637,144:2087,288:8548,784:69939}
        for row in self.report["rungs"][1:]:
            s=row["structural_accounting"]
            self.assertTrue(s["all_level_s_caps_pass"])
            self.assertEqual(s["event_total"], expected_totals[row["n"]])
            self.assertEqual(s["peak_retained_entries"], expected_peaks[row["n"]])
            self.assertLessEqual(s["event_total"], 1 << 30)
            self.assertLessEqual(s["peak_retained_entries"], 1 << 22)

    def test_primary_compilation_cap_exhausts_before_materialization(self):
        expected = {90:1<<26,108:1<<31,144:1<<35,288:1<<80,784:1<<202}
        for row in self.report["rungs"][1:]:
            self.assertEqual(row["compile_boundary"]["primary_peak_joint_table_entries"], expected[row["n"]])
            self.assertEqual(row["compile_boundary"]["cap"], 1 << 20)
            self.assertFalse(row["compile_boundary"]["compilation_reached"])
            self.assertEqual(row["compile_boundary"]["first_crossed_cap"], "max_peak_joint_table_entries")
            self.assertEqual(row["compile_status"], "BOUND_EXHAUSTED_PREMATERIALIZATION_PEAK_JOINT_TABLE")
            self.assertEqual(row["semantic_validation_status"], "NOT_REACHED_COMPILATION_NOT_ADMISSIBLE")

    def test_ladder_adjudication_retains_negative_result(self):
        adj=self.report["adjudication"]
        self.assertEqual(adj["primary_outcome"], "FINITE_LADDER_STRUCTURAL_AUDIT_COMPLETED__COMPILATION_BOUND_EXHAUSTED")
        self.assertEqual(adj["first_primary_compilation_cap_exhaustion"], {
            "n":90,"cap":"max_peak_joint_table_entries","cap_value":1048576,
            "predicted_primary_peak":67108864,"min_fill_induced_width":25,
        })
        self.assertEqual(adj["semantic_validation_reached_post_anchor_rungs"], [])
        self.assertFalse(adj["controlled_approximation_used"])
        self.assertFalse(adj["operational_failure_used_for_scientific_adjudication"])

    def test_finite_nonmonotonicity_is_retained(self):
        predicates=self.report["finite_ladder"]["finite_predicates"]
        self.assertFalse(predicates["lexicographic_width_monotone_non_decreasing"])
        self.assertEqual(predicates["lexicographic_nonmonotonic_witness"], {
            "from_n":108,"from_width":33,"to_n":144,"to_width":31,
        })
        self.assertTrue(predicates["min_fill_width_strictly_increasing"])
        self.assertTrue(predicates["min_degree_width_strictly_increasing"])
        self.assertIn("FINITE_LADDER_NONMONOTONE_STRUCTURE_OBSERVED", self.report["adjudication"]["secondary_outcomes"])

    def test_comparison_maturity_creates_no_authority(self):
        maturity=self.report["comparison_referral_maturity"]
        self.assertEqual(maturity["observed_post72_source_and_structural_certificates"],5)
        self.assertTrue(maturity["certified_deterministic_compilation_bound_exhaustion"])
        self.assertTrue(maturity["maturity_criterion_met"])
        self.assertFalse(maturity["creates_compare_authority"])
        self.assertFalse(self.report["claim_boundary"]["conventional_decoder_comparison_authorized"])

    def test_downstream_and_family_claims_remain_closed(self):
        boundary=self.report["claim_boundary"]
        for key in [
            "global_treewidth_claim","asymptotic_scaling_claim","fitted_scaling_exponent_certified",
            "runtime_superiority_claim","memory_superiority_claim","controlled_approximation_authorized",
            "conventional_decoder_comparison_authorized","circuit_level_authorized",
            "qec_circuit_001_authorized","qldpc_forge_authorized","autonomous_search_authorized",
        ]:
            self.assertFalse(boundary[key])
        self.assertTrue(boundary["finite_named_ladder_only"])
        self.assertFalse(self.report["adjudication"]["downstream_authority_created"])

    def test_manifest_rung_reorder_fails_closed(self):
        altered=copy.deepcopy(self.manifest)
        altered["ladder"][1], altered["ladder"][2] = altered["ladder"][2], altered["ladder"][1]
        altered.pop("manifest_payload_sha256",None)
        altered["manifest_payload_sha256"]=q.digest(altered)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"manifest.json"
            path.write_text(json.dumps(altered))
            with self.assertRaises(ValueError):
                q.load_manifest(path)

    def test_manifest_cap_drift_fails_closed(self):
        altered=copy.deepcopy(self.manifest)
        altered["structural_ledger"]["max_events_per_rung"] += 1
        altered.pop("manifest_payload_sha256",None)
        altered["manifest_payload_sha256"]=q.digest(altered)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"manifest.json"
            path.write_text(json.dumps(altered))
            with self.assertRaises(ValueError):
                q.load_manifest(path)

    def test_manifest_primary_order_drift_fails_closed(self):
        altered=copy.deepcopy(self.manifest)
        altered["order_policy"]["primary"]="deterministic_min_degree"
        altered.pop("manifest_payload_sha256",None)
        altered["manifest_payload_sha256"]=q.digest(altered)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"manifest.json"
            path.write_text(json.dumps(altered))
            with self.assertRaises(ValueError):
                q.load_manifest(path)

    def test_source_and_basis_digests_are_distinct_per_rung(self):
        hx=[r["source_and_basis_digests"]["hx_sha256"] for r in self.report["rungs"]]
        scopes=[r["source_and_basis_digests"]["factor_scope_sha256"] for r in self.report["rungs"]]
        self.assertEqual(len(hx),len(set(hx)))
        self.assertEqual(len(scopes),len(set(scopes)))

if __name__ == "__main__":
    unittest.main()
