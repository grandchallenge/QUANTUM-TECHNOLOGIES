#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "reference"
if str(REF) not in sys.path:
    sys.path.insert(0, str(REF))

import qldpc_fixture_002 as F2
import tcm_qdec_compare_001 as C

PATH = REF / "tcm_qdec_compare_001_exact_cell.py"
SPEC = importlib.util.spec_from_file_location("compare001_exact_cell_tested", PATH)
M = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(M)


class Compare001OracleEquivalenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        hx, _hz, stabilizers, _corpus, _tables, _ties = C.c18_context()
        cls.hx = hx
        cls.explicit = stabilizers
        cls.basis = F2.basis(hx)

    def test_basis_rank_matches_protected_c18_stabilizer_rank(self):
        self.assertEqual(len(self.basis), 7)
        self.assertEqual(len(self.explicit), 128)

    def test_exhaustive_18_bit_membership_equivalence(self):
        for value in range(1 << 18):
            self.assertEqual(
                value in self.explicit,
                M.in_row_span(value, self.basis, already_basis=True),
                value,
            )

    def test_basis_oracle_does_not_materialize_span(self):
        self.assertEqual(M.in_row_span(0, self.basis, already_basis=True), True)
        nonmember = next(v for v in range(1 << 18) if v not in self.explicit)
        self.assertFalse(M.in_row_span(nonmember, self.basis, already_basis=True))


if __name__ == "__main__":
    unittest.main()
