from __future__ import annotations

import json
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


class QTRC90ExactNativeEval001Tests(unittest.TestCase):
    SCOPES = [(0,), (0, 1), (1,)]
    SELECTOR_QUBITS = [0, 2]
    ORDER = [0, 1]
    COMPILER_CPP = REFERENCE / "qtr_c90_exact_compact_native_001.cpp"
    EVALUATOR_CPP = REFERENCE / "qtr_c90_exact_native_eval_001.cpp"
    NATIVE_HEADER = struct.Struct("<8sIQI")

    @classmethod
    def setUpClass(cls) -> None:
        compiler = shutil.which("g++")
        if compiler is None:
            raise unittest.SkipTest("g++ is required for native evaluator controls")
        cls._tmp = tempfile.TemporaryDirectory(prefix="qtr-c90-native-eval-")
        cls.native_compiler = Path(cls._tmp.name) / "qtr-c90-compile"
        cls.native_evaluator = Path(cls._tmp.name) / "qtr-c90-eval"
        subprocess.run(
            [compiler, "-std=c++17", "-O2", "-DNDEBUG", str(cls.COMPILER_CPP), "-o", str(cls.native_compiler)],
            cwd=ROOT,
            check=True,
        )
        subprocess.run(
            [compiler, "-std=c++17", "-O2", "-DNDEBUG", str(cls.EVALUATOR_CPP), "-o", str(cls.native_evaluator)],
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
    def _write_compile_input(cls, path: Path, algebra: str) -> None:
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
    def _parse_hex(value: str) -> int:
        if not value.startswith("0x"):
            raise AssertionError(value)
        return int(value, 16)

    @classmethod
    def _parse_native_value(cls, algebra: str, row: dict):
        if algebra != "min_plus_hamming":
            return cls._parse_hex(row["value_hex"])
        return (
            (
                int(row["minimum_weight"]),
                cls._parse_hex(row["minimum_representative_hex"]),
            ),
            cls._parse_hex(row["canonical_hex"]),
        )

    @classmethod
    def _brute_force(cls, algebra: str, coordinate: int):
        selector_parameter = {qubit: p for p, qubit in enumerate(cls.SELECTOR_QUBITS)}
        total = None
        for assignment in range(1 << len(cls.ORDER)):
            product = None
            for qubit, scope in enumerate(cls.SCOPES):
                parity = 0
                for variable in scope:
                    parity ^= (assignment >> cls.ORDER.index(variable)) & 1
                parameter = selector_parameter.get(qubit)
                if parameter is not None:
                    parity ^= (coordinate >> parameter) & 1
                value = DAG._terminal_value(algebra, qubit, parity)
                product = value if product is None else DAG._multiply_value(algebra, product, value)
            if product is None:
                raise AssertionError("empty product")
            total = product if total is None else DAG._marginal_value(algebra, total, product)
        if total is None:
            raise AssertionError("empty marginal")
        return total

    def _compile_native(self, algebra: str, directory: Path) -> Path:
        input_path = directory / f"{algebra}.input.txt"
        output_path = directory / f"{algebra}.qtrbin"
        self._write_compile_input(input_path, algebra)
        subprocess.run(
            [str(self.native_compiler), "--input", str(input_path), "--output", str(output_path)],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return output_path

    def _evaluate_native(self, algebra: str, native_path: Path) -> list[dict]:
        selector_path = native_path.with_suffix(".selectors.txt")
        selector_path.write_text(
            "".join(f"{coordinate} {coordinate}\n" for coordinate in range(1 << len(self.SELECTOR_QUBITS))),
            encoding="utf-8",
        )
        completed = subprocess.run(
            [
                str(self.native_evaluator),
                "--native",
                str(native_path),
                "--selectors",
                str(selector_path),
            ],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        rows = [json.loads(line) for line in completed.stdout.splitlines() if line.strip()]
        self.assertEqual(len(rows), 1 << len(self.SELECTOR_QUBITS))
        for row in rows:
            self.assertEqual(row["status"], "C90_COMPACT_NATIVE_SELECTOR_EVALUATED")
            self.assertEqual(row["algebra_id"], self._algebra_id(algebra))
            self.assertFalse(row["quality_exposed"])
            self.assertGreater(row["reachable_nodes"], 0)
            self.assertGreater(row["peak_live_values"], 0)
        return rows

    def test_native_evaluator_matches_symbolic_and_bruteforce_every_selector(self) -> None:
        with tempfile.TemporaryDirectory(prefix="qtr-c90-native-eval-case-") as tmp:
            directory = Path(tmp)
            for algebra in DAG.ALGEBRAS:
                with self.subTest(algebra=algebra):
                    native_path = self._compile_native(algebra, directory)
                    rows = self._evaluate_native(algebra, native_path)
                    reference = Symbolic.compile_factor_graph(
                        scopes=self.SCOPES,
                        selector_qubits=self.SELECTOR_QUBITS,
                        order=self.ORDER,
                        algebra=algebra,
                    )
                    for coordinate, row in enumerate(rows):
                        self.assertEqual(row["selector_index"], coordinate)
                        self.assertEqual(row["selector_coordinate"], coordinate)
                        observed = self._parse_native_value(algebra, row)
                        symbolic = reference["dag"].evaluate(reference["root"], coordinate, algebra)
                        brute = self._brute_force(algebra, coordinate)
                        self.assertEqual(observed, symbolic)
                        self.assertEqual(observed, brute)

    def test_native_checkpoint_resume_matches_uninterrupted_every_algebra(self) -> None:
        binding = "0123456789abcdef" * 4
        with tempfile.TemporaryDirectory(prefix="qtr-c90-native-checkpoint-") as tmp:
            directory = Path(tmp)
            for algebra in DAG.ALGEBRAS:
                with self.subTest(algebra=algebra):
                    native_path = self._compile_native(algebra, directory)
                    selector_path = directory / f"{algebra}.selector0.txt"
                    selector_path.write_text("0 0\n", encoding="utf-8")
                    uninterrupted = subprocess.run(
                        [
                            str(self.native_evaluator),
                            "--native",
                            str(native_path),
                            "--selectors",
                            str(selector_path),
                        ],
                        cwd=ROOT,
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                    full_row = json.loads(uninterrupted.stdout.strip())
                    with native_path.open("rb") as handle:
                        magic, algebra_id, count, root = self.NATIVE_HEADER.unpack(handle.read(self.NATIVE_HEADER.size))
                    self.assertEqual(magic, b"QTRC90N1")
                    self.assertEqual(algebra_id, self._algebra_id(algebra))
                    self.assertLess(root, count)
                    stop_node = max(1, min(count - 1, count // 2))
                    checkpoint = directory / f"{algebra}.checkpoint.bin"
                    partial = subprocess.run(
                        [
                            str(self.native_evaluator),
                            "--native",
                            str(native_path),
                            "--selectors",
                            str(selector_path),
                            "--checkpoint-out",
                            str(checkpoint),
                            "--checkpoint-binding",
                            binding,
                            "--stop-node",
                            str(stop_node),
                        ],
                        cwd=ROOT,
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                    partial_row = json.loads(partial.stdout.strip())
                    self.assertEqual(partial_row["status"], "C90_COMPACT_NATIVE_SELECTOR_CHECKPOINTED")
                    self.assertEqual(partial_row["next_node"], stop_node)
                    self.assertFalse(partial_row["quality_exposed"])
                    resumed = subprocess.run(
                        [
                            str(self.native_evaluator),
                            "--native",
                            str(native_path),
                            "--selectors",
                            str(selector_path),
                            "--checkpoint-in",
                            str(checkpoint),
                            "--checkpoint-binding",
                            binding,
                        ],
                        cwd=ROOT,
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                    resumed_row = json.loads(resumed.stdout.strip())
                    self.assertEqual(resumed_row, full_row)

    def test_native_evaluator_repeat_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory(prefix="qtr-c90-native-eval-repeat-") as tmp:
            directory = Path(tmp)
            for algebra in DAG.ALGEBRAS:
                with self.subTest(algebra=algebra):
                    native_path = self._compile_native(algebra, directory)
                    left = self._evaluate_native(algebra, native_path)
                    right = self._evaluate_native(algebra, native_path)
                    self.assertEqual(left, right)


if __name__ == "__main__":
    unittest.main()
