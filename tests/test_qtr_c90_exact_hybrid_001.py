from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "reference"
if str(REFERENCE) not in sys.path:
    sys.path.insert(0, str(REFERENCE))

import qtr_c90_exact_dag_001 as DAG
import qtr_c90_exact_hybrid_001 as Hybrid


class QTRC90ExactHybrid001Tests(unittest.TestCase):
    # Three stabilizers force a non-empty symbolic prefix and a non-empty DD
    # suffix when switch_remaining_stabilizers=1.
    SCOPES = [(0, 1), (0, 2), (1, 2), (2,)]
    SELECTOR_QUBITS = [0, 3]
    ORDER = [0, 1, 2]

    def _compile_dd(self, algebra: str) -> tuple[DAG.ExpressionDAG, int]:
        dag = DAG.ExpressionDAG()
        dd = DAG.DecisionDiagram(self.ORDER)
        selector_parameter = {q: i for i, q in enumerate(self.SELECTOR_QUBITS)}
        factors = [
            (
                tuple(scope),
                DAG._local_symbolic_factor(
                    qubit,
                    tuple(scope),
                    selector_parameter,
                    algebra,
                    dag,
                    dd,
                ),
            )
            for qubit, scope in enumerate(self.SCOPES)
        ]
        multiply = "MPMUL" if algebra == "min_plus_hamming" else "MUL"
        marginal = "MPMIN" if algebra == "min_plus_hamming" else "ADD"
        for variable in self.ORDER:
            involved = [factor for factor in factors if variable in factor[0]]
            rest = [factor for factor in factors if variable not in factor[0]]
            union = tuple(sorted(set().union(*(set(scope) for scope, _ in involved))))
            joint = involved[0][1]
            for _, root in involved[1:]:
                joint = dd.apply(multiply, joint, root, dag)
            out = dd.sum_out(joint, variable, marginal, dag)
            rest.append((tuple(v for v in union if v != variable), out))
            factors = rest
            dd.clear_caches()
            roots = [root for _, root in factors]
            expression_ids = dd.terminal_expression_ids(roots)
            _, mapping = dag.compact(expression_ids)
            dd, roots = dd.compact_and_remap_terminals(roots, mapping)
            factors = [(scope, root) for (scope, _), root in zip(factors, roots)]
        final = factors[0][1]
        for scope, root in factors[1:]:
            self.assertFalse(scope)
            final = dd.apply(multiply, final, root, dag)
        node = dd.nodes[final]
        self.assertEqual(node[0], "T")
        expression_root = int(node[1])
        [expression_root], _ = dag.compact([expression_root])
        return dag, expression_root

    def _brute(self, algebra: str, coordinate: int):
        selector_parameter = {q: i for i, q in enumerate(self.SELECTOR_QUBITS)}
        values = []
        for assignment in range(1 << len(self.ORDER)):
            bits = {
                variable: (assignment >> index) & 1
                for index, variable in enumerate(self.ORDER)
            }
            local = []
            for qubit, scope in enumerate(self.SCOPES):
                bit = (
                    (coordinate >> selector_parameter[qubit]) & 1
                    if qubit in selector_parameter
                    else 0
                )
                for variable in scope:
                    bit ^= bits[variable]
                local.append(DAG._terminal_value(algebra, qubit, bit))
            value = local[0]
            for other in local[1:]:
                value = DAG._multiply_value(algebra, value, other)
            values.append(value)
        value = values[0]
        for other in values[1:]:
            value = DAG._marginal_value(algebra, value, other)
        return value

    def test_hybrid_matches_full_dd_and_bruteforce_across_both_phases(self) -> None:
        for algebra in DAG.ALGEBRAS:
            old_dag, old_root = self._compile_dd(algebra)
            hybrid = Hybrid.compile_factor_graph(
                scopes=[tuple(scope) for scope in self.SCOPES],
                selector_qubits=self.SELECTOR_QUBITS,
                order=self.ORDER,
                algebra=algebra,
                switch_remaining_stabilizers=1,
            )
            self.assertEqual(hybrid["receipt"]["symbolic_prefix_steps"], 2)
            self.assertEqual(hybrid["receipt"]["narrow_dd_steps"], 1)
            self.assertEqual(hybrid["receipt"]["temporary_stabilizer_nodes_final"], 0)
            for coordinate in range(1 << len(self.SELECTOR_QUBITS)):
                expected = self._brute(algebra, coordinate)
                self.assertEqual(old_dag.evaluate(old_root, coordinate, algebra), expected)
                self.assertEqual(
                    hybrid["dag"].evaluate(hybrid["root"], coordinate, algebra),
                    expected,
                )

    def test_hybrid_compile_is_deterministic(self) -> None:
        for algebra in DAG.ALGEBRAS:
            left = Hybrid.compile_factor_graph(
                scopes=[tuple(scope) for scope in self.SCOPES],
                selector_qubits=self.SELECTOR_QUBITS,
                order=self.ORDER,
                algebra=algebra,
                switch_remaining_stabilizers=1,
            )
            right = Hybrid.compile_factor_graph(
                scopes=[tuple(scope) for scope in self.SCOPES],
                selector_qubits=self.SELECTOR_QUBITS,
                order=self.ORDER,
                algebra=algebra,
                switch_remaining_stabilizers=1,
            )
            self.assertEqual(left["dag"].nodes, right["dag"].nodes)
            self.assertEqual(left["root"], right["root"])
            self.assertEqual(
                left["receipt"]["canonical_node_stream_sha256"],
                right["receipt"]["canonical_node_stream_sha256"],
            )

    def test_c90_crossover_constant_is_predeclared(self) -> None:
        self.assertEqual(Hybrid.C90_SWITCH_REMAINING_STABILIZERS, 13)


if __name__ == "__main__":
    unittest.main()
