from __future__ import annotations

import importlib.util
import math
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "reference"

spec = importlib.util.spec_from_file_location(
    "dense", REF / "qtr_c90_exact_dense_oracle_001.py"
)
dense = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(dense)


class DenseExactOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.exe = Path(cls.tmp.name) / "dense-oracle"
        subprocess.run(
            [
                "g++",
                "-O2",
                "-std=c++20",
                "-fopenmp",
                "-Wall",
                "-Wextra",
                "-Werror",
                str(REF / "qtr_c90_exact_dense_oracle_001.cpp"),
                "-o",
                str(cls.exe),
            ],
            check=True,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    @staticmethod
    def _brute(
        algebra: str,
        coordinate: int,
        selector_basis: list[int],
        scopes: list[tuple[int, ...]],
        variable_count: int,
    ):
        selector_map = {qubit: i for i, qubit in enumerate(selector_basis)}
        rows = []
        for assignment in range(1 << variable_count):
            bits = []
            for qubit, scope in enumerate(scopes):
                bit = (
                    (coordinate >> selector_map[qubit]) & 1
                    if qubit in selector_map
                    else 0
                )
                bit ^= sum((assignment >> variable) & 1 for variable in scope) & 1
                bits.append(bit)
            if algebra == "sum_product_bsc_p_0_1":
                rows.append(math.prod(1 if bit else 9 for bit in bits))
            elif algebra == "soft_tropical_base_2":
                rows.append(math.prod(1 if bit else 2 for bit in bits))
            else:
                representative = sum(
                    (1 << qubit) for qubit, bit in enumerate(bits) if bit
                )
                rows.append((sum(bits), representative))
        if algebra != "min_plus_hamming":
            return sum(rows)
        minimum_weight = min(weight for weight, _ in rows)
        representative = min(
            value for weight, value in rows if weight == minimum_weight
        )
        canonical = min(value for _, value in rows)
        return minimum_weight, representative, canonical

    def test_modulus_certificate(self) -> None:
        dense._verify_modulus_certificate()
        self.assertGreater(
            math.prod(dense.MODULI), dense.SUM_PRODUCT_BOUND_EXCLUSIVE
        )

    def test_toy_exact_all_algebras_and_selectors(self) -> None:
        scopes = [(0, 1), (1, 2), (0, 2), (0,), (2,), (0, 1, 2)]
        order = [1, 0, 2]
        selector_basis = [0, 3, 5]
        for coordinate in range(1 << len(selector_basis)):
            for algebra in dense.ALGEBRA_IDS:
                observed = dense.run_raw(
                    executable=self.exe,
                    algebra=algebra,
                    coordinate=coordinate,
                    order=order,
                    selector_basis=selector_basis,
                    scopes=scopes,
                )
                expected = self._brute(
                    algebra, coordinate, selector_basis, scopes, 3
                )
                if algebra != "min_plus_hamming":
                    self.assertEqual(
                        observed["residues"],
                        [expected % modulus for modulus in dense.MODULI],
                    )
                else:
                    self.assertEqual(observed["minimum_weight"], expected[0])
                    self.assertEqual(
                        int(observed["minimum_representative_hex"], 16), expected[1]
                    )
                    self.assertEqual(
                        int(observed["canonical_hex"], 16), expected[2]
                    )

    def test_numeric_residue_certificate_proves_native_equality(self) -> None:
        value = 123456789012345678901234567890
        oracle = {
            "coordinate": 0,
            "residues": [value % modulus for modulus in dense.MODULI],
        }
        native = {
            "status": "C90_COMPACT_NATIVE_SELECTOR_EVALUATED",
            "algebra_id": 0,
            "selector_coordinate": 0,
            "value_hex": hex(value),
            "quality_exposed": False,
        }
        encoding = dense._require_exact_native_equality(
            "sum_product_bsc_p_0_1", oracle, native
        )
        self.assertEqual(encoding["value_hex"], hex(value))
        oracle["residues"][0] ^= 1
        with self.assertRaises(AssertionError):
            dense._require_exact_native_equality(
                "sum_product_bsc_p_0_1", oracle, native
            )


if __name__ == "__main__":
    unittest.main()
