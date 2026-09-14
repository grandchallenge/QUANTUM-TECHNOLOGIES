from __future__ import annotations

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "reference"
if str(REFERENCE) not in sys.path:
    sys.path.insert(0, str(REFERENCE))

import qtr_c90_exact_dag_001 as DAG
import qtr_c90_exact_execute_001 as Execute


class QTRC90ExactEngine001Tests(unittest.TestCase):
    def test_temporary_dd_compiler_matches_bruteforce_on_tiny_exact_control(self) -> None:
        scopes = [(0,), (0, 1), (1,)]
        selector_qubits = [0, 2]
        order = [0, 1]

        def compile_tiny(algebra: str):
            dag = DAG.ExpressionDAG()
            dd = DAG.DecisionDiagram(order)
            selector_parameter = {q: i for i, q in enumerate(selector_qubits)}
            factors = [
                (
                    scope,
                    DAG._local_symbolic_factor(
                        q, scope, selector_parameter, algebra, dag, dd
                    ),
                )
                for q, scope in enumerate(scopes)
            ]
            multiply = "MPMUL" if algebra == "min_plus_hamming" else "MUL"
            marginal = "MPMIN" if algebra == "min_plus_hamming" else "ADD"
            for variable in order:
                involved = [f for f in factors if variable in f[0]]
                rest = [f for f in factors if variable not in f[0]]
                union = tuple(sorted(set().union(*(set(scope) for scope, _ in involved))))
                joint = involved[0][1]
                for _, root in involved[1:]:
                    joint = dd.apply(multiply, joint, root, dag)
                out = dd.sum_out(joint, variable, marginal, dag)
                rest.append((tuple(v for v in union if v != variable), out))
                factors = rest
                dd.clear_caches()
                active = [root for _, root in factors]
                expression_ids = dd.terminal_expression_ids(active)
                _, mapping = dag.compact(expression_ids)
                dd, active = dd.compact_and_remap_terminals(active, mapping)
                factors = [(scope, root) for (scope, _), root in zip(factors, active)]
            root = factors[0][1]
            for _, other in factors[1:]:
                root = dd.apply(multiply, root, other, dag)
            node = dd.nodes[root]
            self.assertEqual(node[0], "T")
            expression_root = int(node[1])
            [expression_root], _ = dag.compact([expression_root])
            return dag, expression_root

        def brute(algebra: str, coordinate: int):
            selector_parameter = {q: i for i, q in enumerate(selector_qubits)}
            values = []
            for assignment in range(1 << len(order)):
                bits = {
                    variable: (assignment >> index) & 1
                    for index, variable in enumerate(order)
                }
                local = []
                for qubit, scope in enumerate(scopes):
                    bit = (
                        (coordinate >> selector_parameter[qubit]) & 1
                        if qubit in selector_parameter
                        else 0
                    )
                    for variable in scope:
                        bit ^= bits[variable]
                    local.append(DAG._terminal_value(algebra, qubit, bit))
                value = local[0]
                for item in local[1:]:
                    value = DAG._multiply_value(algebra, value, item)
                values.append(value)
            value = values[0]
            for item in values[1:]:
                value = DAG._marginal_value(algebra, value, item)
            return value

        for algebra in DAG.ALGEBRAS:
            dag, root = compile_tiny(algebra)
            for coordinate in range(1 << len(selector_qubits)):
                self.assertEqual(
                    dag.evaluate(root, coordinate, algebra),
                    brute(algebra, coordinate),
                )

    def test_execution_preflight_remains_quality_blind(self) -> None:
        report = Execute.preflight()
        self.assertEqual(report["status"], "PREFLIGHT_PASS__NO_C90_DECODER_QUALITY")
        self.assertIs(report["quality_exposed"], False)
        historical = report["historical_conventional_artifact"]
        self.assertEqual(historical["workflow_run"], Execute.HISTORICAL_COMPARE_RUN)
        self.assertEqual(historical["artifact_id"], Execute.HISTORICAL_COMPARE_ARTIFACT_ID)
        self.assertEqual(historical["head_sha"], Execute.HISTORICAL_COMPARE_HEAD)
        self.assertIs(historical["conventional_decoder_rerun_allowed"], False)


if __name__ == "__main__":
    unittest.main()
