"""Bounded structural verification for QTR-C72-COMMON-GRAPH-001.

All tests are quality blind and run on the locked code matrices only.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"publication"/"research"))
from qtr_c72_common_graph_001 import compute,primal,eliminate,EXPECTED_WIDTHS

class TestC72CommonGraph(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=compute()

    def test_exact_source_matrix_and_dual_counts(self):
        r=self.result
        self.assertEqual(r["code_hx_sha256"],
            "6c01bd1eceb703a1afbd9897c9ce3810d951bc0d1284588607775e9f875740f2")
        self.assertEqual(r["full_check_kernel_dimension"],6)
        self.assertEqual(r["full_check_coefficient_multiplicity"],64)
        self.assertEqual(r["independent_row_indices"],list(range(28))+[30,31])
        self.assertEqual({k:v["variables"] for k,v in r["graphs"].items()},
            {"all_36_check_coefficients":36,"independent_30_stabilizers":30})

    def test_factor_and_graph_structures(self):
        all_g=self.result["graphs"]["all_36_check_coefficients"]
        ind=self.result["graphs"]["independent_30_stabilizers"]
        self.assertEqual(all_g["factor_scope_arity_histogram"],{"3":72})
        self.assertEqual(ind["factor_scope_arity_histogram"],{"1":7,"2":22,"3":43})
        self.assertEqual(all_g["physical_factors"],72)
        self.assertEqual(ind["physical_factors"],72)
        self.assertEqual(all_g["primal_edges"],216)
        self.assertEqual(ind["primal_edges"],151)

    def test_identical_algorithm_applied_to_both_graphs(self):
        for label,expected in EXPECTED_WIDTHS.items():
            actual={name:v["induced_width"] for name,v in self.result["graphs"][label]["orders"].items()}
            self.assertEqual(actual,expected)
        self.assertEqual(self.result["graphs"]["all_36_check_coefficients"]["orders"]["min_fill"]["peak_joint_assignments"],1<<24)
        self.assertEqual(self.result["graphs"]["independent_30_stabilizers"]["orders"]["min_fill"]["peak_joint_assignments"],1<<19)

    def test_exact_elimination_invariants(self):
        for label,g in self.result["graphs"].items():
            n=g["variables"]
            for item in g["orders"].values():
                self.assertEqual(sorted(item["order"]),list(range(n)))
                self.assertEqual(len(set(item["order"])),n)
                self.assertEqual(item["peak_joint_assignments"],1<<(item["induced_width"]+1))
                self.assertEqual(len(item["trace_sha256"]),64)

    def test_small_graph_tie_rule_and_guard(self):
        # Path 0--1--2--3: degree and min-fill choose endpoint 0.
        g=primal([(0,1),(1,2),(2,3)],4)
        self.assertEqual(eliminate(g,"min_degree")["order"],[0,1,2,3])
        self.assertEqual(eliminate(g,"min_fill")["order"],[0,1,2,3])
        with self.assertRaisesRegex(ValueError,"out of graph range"):
            primal([(0,4)],4)
        with self.assertRaisesRegex(ValueError,"unknown policy"):
            eliminate(g,"random")


if __name__=="__main__":
    unittest.main()
