from __future__ import annotations

import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "reference"
if str(REFERENCE) not in sys.path:
    sys.path.insert(0, str(REFERENCE))

import qtr_c90_exact_dag_001 as DAG
import qtr_c90_exact_symbolic_001 as Symbolic


class QTRC90ExactCompactNative001Tests(unittest.TestCase):
    SCOPES = [(0,), (0, 1), (1,)]
    SELECTOR_QUBITS = [0, 2]
    ORDER = [0, 1]
    CPP = REFERENCE / "qtr_c90_exact_compact_native_001.cpp"

    @classmethod
    def setUpClass(cls) -> None:
        compiler = shutil.which("g++")
        if compiler is None:
            raise unittest.SkipTest("g++ is required for compact-native equivalence control")
        if sys.byteorder != "little":
            raise unittest.SkipTest("compact-native binary control is specified for little-endian CI hosts")
        cls._tmp = tempfile.TemporaryDirectory(prefix="qtr-c90-compact-native-")
        cls.binary = Path(cls._tmp.name) / "qtr_c90_exact_compact_native_001"
        subprocess.run(
            [compiler, "-std=c++17", "-O2", "-DNDEBUG", str(cls.CPP), "-o", str(cls.binary)],
            cwd=ROOT,
            check=True,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        if hasattr(cls, "_tmp"):
            cls._tmp.cleanup()

    @staticmethod
    def _algebra_id(algebra: str) -> int:
        return {
            "sum_product_bsc_p_0_1": 0,
            "soft_tropical_base_2": 1,
            "min_plus_hamming": 2,
        }[algebra]

    @classmethod
    def _write_input(cls, path: Path, algebra: str) -> None:
        tokens: list[str] = [str(cls._algebra_id(algebra)), str(len(cls.ORDER))]
        tokens.extend(str(v) for v in cls.ORDER)
        tokens.append(str(len(cls.SELECTOR_QUBITS)))
        tokens.extend(str(q) for q in cls.SELECTOR_QUBITS)
        tokens.append(str(len(cls.SCOPES)))
        for scope in cls.SCOPES:
            tokens.append(str(len(scope)))
            tokens.extend(str(v) for v in scope)
        path.write_text(" ".join(tokens) + "\n", encoding="utf-8")

    @staticmethod
    def _terminal_value(algebra: str, code: int):
        if algebra == "sum_product_bsc_p_0_1":
            if code not in (0, 1):
                raise AssertionError(code)
            return 9 if code == 0 else 1
        if algebra == "soft_tropical_base_2":
            if code not in (0, 1):
                raise AssertionError(code)
            return 2 if code == 0 else 1
        if code == 0:
            return ((0, 0), 0)
        qubit = code - 1
        integer = 1 << qubit
        return ((1, integer), integer)

    @classmethod
    def _read_output(cls, path: Path, algebra: str) -> tuple[list[tuple], int]:
        raw = path.read_bytes()
        header = struct.Struct("<8sIQI")
        node_struct = struct.Struct("<BIII")
        magic, algebra_id, count, root = header.unpack_from(raw, 0)
        cls.assertEqual(cls, magic, b"QTRC90N1")
        cls.assertEqual(cls, algebra_id, cls._algebra_id(algebra))
        expected_size = header.size + count * node_struct.size
        cls.assertEqual(cls, len(raw), expected_size)

        kinds = {
            1: "I",
            2: "S",
            3: "MUL",
            4: "ADD",
            5: "MPMUL",
            6: "MPMIN",
        }
        nodes: list[tuple] = []
        offset = header.size
        for _ in range(count):
            kind, a, b, c = node_struct.unpack_from(raw, offset)
            offset += node_struct.size
            if kind == 0:
                nodes.append(("T", cls._terminal_value(algebra, a)))
            elif kind == 1:
                nodes.append(("I", int(a), int(b), int(c)))
            elif kind == 2:
                nodes.append(("S", int(a), int(b), int(c)))
            else:
                nodes.append((kinds[kind], int(a), int(b)))
        return nodes, int(root)

    def _compile_native(self, algebra: str) -> tuple[list[tuple], int]:
        with tempfile.TemporaryDirectory(prefix="qtr-c90-native-case-") as tmp:
            input_path = Path(tmp) / "input.txt"
            output_path = Path(tmp) / "compiled.bin"
            self._write_input(input_path, algebra)
            result = subprocess.run(
                [str(self.binary), "--input", str(input_path), "--output", str(output_path)],
                cwd=ROOT,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertIn("EXACT_COMPACT_NATIVE_COMPLETED", result.stdout)
            return self._read_output(output_path, algebra)

    def test_native_matches_python_semantic_node_stream_for_every_algebra(self) -> None:
        for algebra in DAG.ALGEBRAS:
            with self.subTest(algebra=algebra):
                reference = Symbolic.compile_factor_graph(
                    scopes=self.SCOPES,
                    selector_qubits=self.SELECTOR_QUBITS,
                    order=self.ORDER,
                    algebra=algebra,
                )
                native_nodes, native_root = self._compile_native(algebra)
                self.assertFalse(any(node[0] == "S" for node in native_nodes))
                self.assertEqual(native_nodes, reference["dag"].nodes)
                self.assertEqual(native_root, reference["root"])

                native_dag = DAG.ExpressionDAG()
                native_dag.nodes = native_nodes
                native_dag.interned = {node: i for i, node in enumerate(native_nodes)}
                native_dag.peak_nodes = len(native_nodes)
                native_receipt = native_dag.canonical_receipt(native_root, algebra)
                self.assertEqual(
                    native_receipt["canonical_node_stream_sha256"],
                    reference["receipt"]["canonical_node_stream_sha256"],
                )

    def test_native_compile_is_deterministic(self) -> None:
        for algebra in DAG.ALGEBRAS:
            with self.subTest(algebra=algebra):
                left = self._compile_native(algebra)
                right = self._compile_native(algebra)
                self.assertEqual(left, right)


if __name__ == "__main__":
    unittest.main()
