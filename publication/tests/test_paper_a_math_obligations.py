"""Independent finite hostile checks for Paper A theorem hypotheses.

Self-contained standard-library tests. They are finite witnesses, not a formal
proof or a certification of the native C72/C90 implementations.
"""
from __future__ import annotations

import itertools
import unittest


N = 6
R = 2
M = N - R
S = ((1 << 4) | (1 << 0) | (1 << 2), (1 << 5) | (1 << 1))
SELECTORS = tuple(range(4))
PHI_ROWS = ((1 << 0) | (1 << 4), (1 << 1) | (1 << 5),
            (1 << 2) | (1 << 4), 1 << 3)


def phi(e: int) -> int:
    return sum(((e & row).bit_count() & 1) << i for i, row in enumerate(PHI_ROWS))


def representative(a: int, z: int) -> int:
    return a ^ (S[0] if z & 1 else 0) ^ (S[1] if z & 2 else 0)


def frozen_fiber(a: int) -> list[int]:
    return [e for e in range(1 << N) if phi(e) == a]


def formal_fiber(a: int) -> list[int]:
    return [representative(a, z) for z in range(1 << R)]


def payload(errors: list[int]) -> tuple[int, int, tuple[int, int], int]:
    return (sum(9 ** (N - e.bit_count()) for e in errors),
            sum(2 ** (N - e.bit_count()) for e in errors),
            min((e.bit_count(), e) for e in errors),
            min(errors))


# A single absorbing infinity sentinel is distinct from every finite pair.
TOP = object()
FINITE = list(itertools.product(range(3), repeat=2))
CARRIER = FINITE + [TOP]


def tropical_plus(a: tuple[int, int] | object, b: tuple[int, int] | object):
    if a is TOP:
        return b
    if b is TOP:
        return a
    return min(a, b)


def tropical_times(a: tuple[int, int] | object, b: tuple[int, int] | object):
    if a is TOP or b is TOP:
        return TOP
    return (a[0] + b[0], a[1] + b[1])


class TestFullKernelAndTropicalHypotheses(unittest.TestCase):
    def test_css_full_kernel_fibers_are_exact_bijections(self):
        # The selected columns are the first M physical unit vectors, and
        # their functional columns are the identity.
        self.assertEqual(tuple(phi(1 << i) for i in SELECTORS), (1, 2, 4, 8))
        self.assertEqual(tuple(phi(s) for s in S), (0, 0))
        for a in range(1 << M):
            lift = formal_fiber(a)
            direct = frozen_fiber(a)
            self.assertEqual(len(lift), 1 << R)
            self.assertEqual(len(set(lift)), len(lift))
            self.assertEqual(sorted(lift), direct)
            self.assertTrue(all(phi(e) == a for e in lift))

    def test_all_three_algebras_and_both_minplus_keys(self):
        for a in range(1 << M):
            self.assertEqual(payload(formal_fiber(a)), payload(frozen_fiber(a)))
        # Distinct global minimizers for the minimum-weight representative
        # and the minimum-integer canonical key can occur in a coset.
        self.assertTrue(any(
            payload(frozen_fiber(a))[2][1] != payload(frozen_fiber(a))[3]
            for a in range(1 << M)
        ))

    def test_strict_subset_does_not_enumerate_full_kernel(self):
        for a in range(1 << M):
            subset = [representative(a, z) for z in range(2)]  # omit S[1]
            self.assertEqual(len(subset), 2)
            self.assertNotEqual(sorted(subset), frozen_fiber(a))
        # This is a meaningful negative control on the old inclusion-only
        # hypothesis span(S) <= ker(Phi), which is insufficient.

    def test_restricted_tropical_semiring_distributivity(self):
        for a, b, c in itertools.product(CARRIER, repeat=3):
            left = tropical_times(a, tropical_plus(b, c))
            right = tropical_plus(tropical_times(a, b), tropical_times(a, c))
            self.assertEqual(left, right)
            self.assertEqual(tropical_plus(a, b), tropical_plus(b, a))
            self.assertEqual(tropical_times(a, b), tropical_times(b, a))
        for a in CARRIER:
            self.assertEqual(tropical_plus(a, TOP), a)
            self.assertIs(tropical_times(a, TOP), TOP)
            self.assertEqual(tropical_times(a, (0, 0)), a)

    def test_unrestricted_partial_infinity_is_not_distributive(self):
        inf = float("inf")
        a, b, c = (0, inf), (1, 0), (inf, 0)
        add = lambda x, y: tuple(u + v for u, v in zip(x, y))
        lhs = add(min(a, b), c)
        rhs = min(add(a, c), add(b, c))
        self.assertNotEqual(lhs, rhs)
        self.assertEqual(lhs, (inf, inf))
        self.assertEqual(rhs, (inf, 0))

    def test_disjoint_factor_provenance_preserves_binary_mask(self):
        for n in range(1, 10):
            parts = [{i} for i in range(n)]
            while len(parts) > 1:
                merged = parts.pop(0) | parts.pop(-1)
                self.assertEqual(len(merged), sum(len(s) for s in (parts + [merged])) - sum(len(s) for s in parts))
                parts.insert(0, merged)
                self.assertEqual(set.union(*parts), set(range(n)))
                self.assertEqual(sum(len(p) for p in parts), n)
                self.assertTrue(all(a.isdisjoint(b)
                    for a, b in itertools.combinations(parts, 2)))
            mask = sum(1 << i for i in parts[0])
            self.assertEqual(mask, (1 << n) - 1)


if __name__ == "__main__":
    unittest.main()
