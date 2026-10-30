"""Exact regressions for the corrected QTR publication theorem.

No external scientific execution or certification is implied by these finite tests.
"""
import itertools
import unittest


TOP = object()


def lex_min(x, y):
    if x is TOP:
        return y
    if y is TOP:
        return x
    return min(x, y)


def pair_product(x, y):
    if x is TOP or y is TOP:
        return TOP
    return (x[0] + y[0], x[1] + y[1])


def phi(error):
    return (
        (error.bit_count() & 1),
        ((error & 0b0011).bit_count() & 1),
    )


def selector_lift(a):
    return (1 if a & 1 else 0) ^ (4 if a & 2 else 0)


def stabilizer(z):
    return (0b0011 if z & 1 else 0) ^ (0b1100 if z & 2 else 0)


class QTRPublicationTheoremRegressions(unittest.TestCase):
    def test_finite_pair_single_top_is_distributive(self):
        domain = [TOP] + list(itertools.product(range(4), repeat=2))
        for a, b, c in itertools.product(domain, repeat=3):
            self.assertEqual(
                pair_product(lex_min(a, b), c),
                lex_min(pair_product(a, c), pair_product(b, c)),
            )
            self.assertEqual(
                pair_product(a, lex_min(b, c)),
                lex_min(pair_product(a, b), pair_product(a, c)),
            )

    def test_partial_infinity_pairs_are_not_valid(self):
        infinity = float("inf")
        x, y, c = (0, 10), (1, 0), (infinity, 0)
        prod = lambda p, q: (p[0] + q[0], p[1] + q[1])
        self.assertNotEqual(prod(min(x, y), c), min(prod(x, c), prod(y, c)))

    def test_css_full_kernel_fibers_are_bijective(self):
        # HX rows 0011,1100; HZ row 1111; logical-Z row 0011.
        # Rank HX=2, rank HZ=1, k=1, rank Phi=2, n=4, r=n-m=2.
        for a in range(4):
            target = phi(selector_lift(a))
            fiber = {e for e in range(16) if phi(e) == target}
            represented = {selector_lift(a) ^ stabilizer(z) for z in range(4)}
            self.assertEqual(len(fiber), 4)
            self.assertEqual(len(represented), 4)
            self.assertEqual(fiber, represented)

    def test_kernel_inclusion_without_completeness_is_insufficient(self):
        # Phi(e0,e1)=e0; an empty stabilizer basis covers only error 00.
        # A BSC numerator with w(0)=9, w(1)=1 differs on the full fiber.
        represented_score = 9 * 9
        full_fiber_score = represented_score + 9 * 1
        self.assertEqual(represented_score, 81)
        self.assertEqual(full_fiber_score, 90)
        self.assertNotEqual(represented_score, full_fiber_score)


if __name__ == "__main__":
    unittest.main()
