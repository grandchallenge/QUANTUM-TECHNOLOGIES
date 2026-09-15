from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "reference"
if str(REFERENCE) not in sys.path:
    sys.path.insert(0, str(REFERENCE))

import qtr_c90_exact_dag_001 as DAG
import qtr_c90_exact_factored_001 as Factored
import qtr_c90_exact_symbolic_001 as Symbolic


class QTRC90ExactFactored001Tests(unittest.TestCase):
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

    def _brute(self, algebra: str, coordinate: int) -> Any:
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

    def _evaluate_symbolic(
        self,
        circuit: Symbolic.SymbolicCircuit,
        root: int,
        algebra: str,
        stabilizers: dict[int, int],
        selector_coordinate: int,
    ) -> Any:
        memo: dict[int, Any] = {}

        def visit(node_id: int) -> Any:
            if node_id in memo:
                return memo[node_id]
            node = circuit.nodes[node_id]
            kind = node[0]
            if kind == "T":
                value = node[1]
            elif kind == "S":
                bit = stabilizers[int(node[1])]
                value = visit(int(node[3] if bit else node[2]))
            elif kind == "I":
                bit = (selector_coordinate >> int(node[1])) & 1
                value = visit(int(node[3] if bit else node[2]))
            elif kind in {"MUL", "MPMUL"}:
                value = DAG._multiply_value(algebra, visit(int(node[1])), visit(int(node[2])))
            elif kind in {"ADD", "MPMIN"}:
                value = DAG._marginal_value(algebra, visit(int(node[1])), visit(int(node[2])))
            else:
                raise AssertionError(kind)
            memo[node_id] = value
            return value

        return visit(int(root))

    def test_factored_matches_full_dd_and_bruteforce_for_every_selector(self) -> None:
        for algebra in DAG.ALGEBRAS:
            old_dag, old_root = self._compile_dd(algebra)
            new = Factored.compile_factor_graph(
                scopes=[tuple(scope) for scope in self.SCOPES],
                selector_qubits=self.SELECTOR_QUBITS,
                order=self.ORDER,
                algebra=algebra,
            )
            self.assertEqual(new["receipt"]["temporary_stabilizer_nodes_final"], 0)
            for coordinate in range(1 << len(self.SELECTOR_QUBITS)):
                expected = self._brute(algebra, coordinate)
                self.assertEqual(old_dag.evaluate(old_root, coordinate, algebra), expected)
                self.assertEqual(new["dag"].evaluate(new["root"], coordinate, algebra), expected)

    def test_factored_compile_is_deterministic(self) -> None:
        for algebra in DAG.ALGEBRAS:
            left = Factored.compile_factor_graph(
                scopes=[tuple(scope) for scope in self.SCOPES],
                selector_qubits=self.SELECTOR_QUBITS,
                order=self.ORDER,
                algebra=algebra,
            )
            right = Factored.compile_factor_graph(
                scopes=[tuple(scope) for scope in self.SCOPES],
                selector_qubits=self.SELECTOR_QUBITS,
                order=self.ORDER,
                algebra=algebra,
            )
            self.assertEqual(left["dag"].nodes, right["dag"].nodes)
            self.assertEqual(left["root"], right["root"])
            self.assertEqual(
                left["receipt"]["canonical_node_stream_sha256"],
                right["receipt"]["canonical_node_stream_sha256"],
            )

    def test_dependency_factoring_matches_direct_correlated_cofactors(self) -> None:
        for algebra in DAG.ALGEBRAS:
            multiply, marginal = Factored._operations(algebra)
            circuit = Symbolic.SymbolicCircuit([0, 1])
            z0 = circuit.terminal(DAG._terminal_value(algebra, 0, 0))
            z1 = circuit.terminal(DAG._terminal_value(algebra, 0, 1))
            w0 = circuit.terminal(DAG._terminal_value(algebra, 1, 0))
            w1 = circuit.terminal(DAG._terminal_value(algebra, 1, 1))

            a = circuit.stabilizer_choice(0, z0, z1)
            b = circuit.stabilizer_choice(0, w1, w0)
            selector_low = circuit.selector_choice(0, z0, w0)
            selector_high = circuit.selector_choice(0, z1, w1)
            c = circuit.stabilizer_choice(1, selector_low, selector_high)

            correlated = circuit.binary(multiply, a, b)
            one_dependent = circuit.binary(multiply, a, c)
            nested_marginal = circuit.binary(marginal, correlated, one_dependent)
            root = circuit.binary(multiply, nested_marginal, c)

            out, stats = Factored.marginalize_factored(
                circuit,
                root,
                0,
                multiply=multiply,
                marginal=marginal,
            )
            self.assertGreater(stats["distributed_marginal_nodes"], 0)
            self.assertGreater(stats["factored_product_nodes"], 0)
            self.assertGreater(stats["correlated_product_fallbacks"], 0)

            for other_bit in (0, 1):
                for coordinate in (0, 1):
                    low = self._evaluate_symbolic(
                        circuit,
                        root,
                        algebra,
                        {0: 0, 1: other_bit},
                        coordinate,
                    )
                    high = self._evaluate_symbolic(
                        circuit,
                        root,
                        algebra,
                        {0: 1, 1: other_bit},
                        coordinate,
                    )
                    expected = DAG._marginal_value(algebra, low, high)
                    observed0 = self._evaluate_symbolic(
                        circuit,
                        out,
                        algebra,
                        {0: 0, 1: other_bit},
                        coordinate,
                    )
                    observed1 = self._evaluate_symbolic(
                        circuit,
                        out,
                        algebra,
                        {0: 1, 1: other_bit},
                        coordinate,
                    )
                    self.assertEqual(observed0, expected)
                    self.assertEqual(observed1, expected)


if __name__ == "__main__":
    unittest.main()
