"""QTR Paper A C72 coordinate/redundancy certificate: source-bound finite review.

This checks the protected linear-algebra identity, not a new decoder quality
campaign, competitor implementation replay or runtime comparison.
"""
from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reference"))
from qldpc_scale_001a_math import (
    construct_code, rank_rref, canonical_nullspace_basis,
    transpose_rows, matrix_record,
)
from qldpc_scale_001a_shared import digest, EXPECTED_DIGESTS


EXPECTED_KERNEL = (
    "01b6c06db", "02db40b6d", "14f9de891",
    "28553c7b9", "4453e77a2", "88a78ff05",
)
EXPECTED_INDEPENDENT_INDICES = tuple(range(28)) + (30, 31)
EXPECTED_HX_SHA256 = "6c01bd1eceb703a1afbd9897c9ce3810d951bc0d1284588607775e9f875740f2"


class TestProtectedC72CoordinateEquivalence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code = construct_code()
        cls.hx = cls.code["hx"]
        cls.free, cls.kernel = canonical_nullspace_basis(
            transpose_rows(cls.hx, 72), 36
        )

    @classmethod
    def syndrome_from_check_coordinates(cls, coeff: int) -> int:
        error = 0
        for index, row in enumerate(cls.hx):
            if coeff & (1 << index):
                error ^= row
        return error

    def test_frozen_matrix_and_full_rowspace(self):
        self.assertEqual(len(self.hx), 36)
        self.assertEqual(
            digest(matrix_record(self.hx, 72)),
            EXPECTED_HX_SHA256
        )
        self.assertEqual(EXPECTED_DIGESTS["hx"], EXPECTED_HX_SHA256)
        self.assertEqual(rank_rref(self.hx, 72)[0], 30)
        self.assertEqual(tuple(self.code["x_indices"]), EXPECTED_INDEPENDENT_INDICES)
        selected = [self.hx[i] for i in self.code["x_indices"]]
        self.assertEqual(rank_rref(selected, 72)[0], 30)
        for row in self.hx:
            self.assertEqual(rank_rref(selected + [row], 72)[0], 30)

    def test_six_exact_independent_redundancy_generators(self):
        self.assertEqual(len(self.kernel), 6)
        self.assertEqual(rank_rref(self.kernel, 36)[0], 6)
        self.assertEqual(tuple(f"{k:09x}" for k in self.kernel), EXPECTED_KERNEL)
        for relation in self.kernel:
            self.assertEqual(self.syndrome_from_check_coordinates(relation), 0)

    def test_exact_sixty_four_coefficient_preimages(self):
        kernel_elements = []
        for mask in range(64):
            coeff = 0
            for index, generator in enumerate(self.kernel):
                if mask & (1 << index):
                    coeff ^= generator
            kernel_elements.append(coeff)
        self.assertEqual(len(set(kernel_elements)), 64)

        for seed in [0, (1 << 36) - 1] + [
            random.Random(20261119 + index).getrandbits(36)
            for index in range(32)
        ]:
            image = self.syndrome_from_check_coordinates(seed)
            self.assertEqual(len({
                self.syndrome_from_check_coordinates(seed ^ relation)
                for relation in kernel_elements
            }), 1)
            self.assertEqual(len({seed ^ relation for relation in kernel_elements}), 64)
            self.assertEqual(self.syndrome_from_check_coordinates(seed), image)

        # Rank-nullity proves the same multiplicity for every coefficient
        # vector, not only the finitely checked seeds. Therefore a full
        # sum-product partition gains factor 64 with all 36 check variables;
        # a min-plus optimum does not change under duplicate terms.


if __name__ == "__main__":
    unittest.main()

