#!/usr/bin/env python3
"""Exact joint stabilizer/selector MTBDD backend for QTR-C90-EXACT-DECODER-001.

The temporary decision diagram contains both unresolved protected stabilizer
variables and all 49 frozen selector parameters.  The 41 stabilizer variables
are eliminated in the protected deterministic min-fill order.  Selector
parameters are retained in canonical parameter-index order and are never
enumerated as a compilation loop.

After stabilizer elimination, the residual reduced multi-terminal DD depends
only on selectors.  It is translated directly into the frozen retained
ExpressionDAG encoding using only exact terminal (T) and parameter-choice (I)
nodes.  Storage/temporary representation is therefore not retained scientific
state.  No approximation, pruning, order search, decoder quality, or injected
error information is used.
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import qtr_c90_exact_decoder_001 as Base
import qtr_c90_exact_dag_001 as DAG
import qtr_c90_exact_execute_001 as Execute

EXPERIMENT_ID = Base.EXPERIMENT_ID
EVALUATOR_VERSION = "0.1.0"
BACKEND = "EXACT_JOINT_STABILIZER_SELECTOR_REDUCED_MTBDD"
SELECTOR_KEY_BASE = 1_000_000


class JointMTBDD:
    """Reduced ordered exact multi-terminal decision diagram."""

    def __init__(self, variable_order: list[int], algebra: str) -> None:
        self.order = list(variable_order)
        self.rank = {int(v): i for i, v in enumerate(variable_order)}
        self.algebra = algebra
        self.nodes: list[tuple[Any, ...]] = []
        self.interned: dict[tuple[Any, ...], int] = {}
        self.apply_cache: dict[tuple[str, int, int], int] = {}
        self.restrict_cache: dict[tuple[int, int, int], int] = {}
        self.peak_nodes = 0
        self.intern_attempts = 0
        self.intern_reuses = 0

    def terminal(self, value: Any) -> int:
        key = ("T", value)
        self.intern_attempts += 1
        found = self.interned.get(key)
        if found is not None:
            self.intern_reuses += 1
            return found
        idx = len(self.nodes)
        self.nodes.append(key)
        self.interned[key] = idx
        self.peak_nodes = max(self.peak_nodes, len(self.nodes))
        return idx

    def mk(self, variable: int, low: int, high: int) -> int:
        if low == high:
            return low
        key = ("D", int(variable), int(low), int(high))
        self.intern_attempts += 1
        found = self.interned.get(key)
        if found is not None:
            self.intern_reuses += 1
            return found
        idx = len(self.nodes)
        self.nodes.append(key)
        self.interned[key] = idx
        self.peak_nodes = max(self.peak_nodes, len(self.nodes))
        return idx

    def top(self, root: int) -> int | None:
        node = self.nodes[root]
        return None if node[0] == "T" else int(node[1])

    def split_on(self, root: int, variable: int) -> tuple[int, int]:
        node = self.nodes[root]
        if node[0] == "T":
            return root, root
        current = int(node[1])
        if current == variable:
            return int(node[2]), int(node[3])
        if self.rank[current] > self.rank[variable]:
            return root, root
        raise AssertionError(
            f"MTBDD ordering violation: encountered {current} before requested {variable}"
        )

    def _terminal_binary(self, operation: str, left: Any, right: Any) -> Any:
        if operation == "MUL":
            return DAG._multiply_value(self.algebra, left, right)
        if operation == "ADD":
            return DAG._marginal_value(self.algebra, left, right)
        raise ValueError(operation)

    def apply(self, operation: str, left: int, right: int) -> int:
        if left > right:
            left, right = right, left
        key = (operation, int(left), int(right))
        found = self.apply_cache.get(key)
        if found is not None:
            return found
        ln, rn = self.nodes[left], self.nodes[right]
        if ln[0] == "T" and rn[0] == "T":
            out = self.terminal(self._terminal_binary(operation, ln[1], rn[1]))
        else:
            lv, rv = self.top(left), self.top(right)
            if lv is None:
                top = rv
            elif rv is None:
                top = lv
            else:
                top = lv if self.rank[lv] <= self.rank[rv] else rv
            assert top is not None
            ll, lh = self.split_on(left, top)
            rl, rh = self.split_on(right, top)
            out = self.mk(top, self.apply(operation, ll, rl), self.apply(operation, lh, rh))
        self.apply_cache[key] = out
        return out

    def restrict(self, root: int, variable: int, bit: int) -> int:
        key = (int(root), int(variable), int(bit))
        found = self.restrict_cache.get(key)
        if found is not None:
            return found
        node = self.nodes[root]
        if node[0] == "T":
            out = root
        else:
            current = int(node[1])
            if current == variable:
                out = int(node[3] if bit else node[2])
            elif self.rank[current] > self.rank[variable]:
                out = root
            else:
                out = self.mk(
                    current,
                    self.restrict(int(node[2]), variable, bit),
                    self.restrict(int(node[3]), variable, bit),
                )
        self.restrict_cache[key] = out
        return out

    def clear_caches(self) -> None:
        self.apply_cache.clear()
        self.restrict_cache.clear()

    def compact(self, roots: list[int]) -> list[int]:
        """Exact reachability GC preserving reduced ordered semantics."""
        old_nodes = self.nodes
        reachable: set[int] = set()
        stack = [int(root) for root in roots]
        while stack:
            node_id = stack.pop()
            if node_id in reachable:
                continue
            reachable.add(node_id)
            node = old_nodes[node_id]
            if node[0] == "D":
                stack.append(int(node[2])); stack.append(int(node[3]))

        order = sorted(reachable)
        rebuilt = JointMTBDD(self.order, self.algebra)
        mapping: dict[int, int] = {}
        # Original node IDs are topological because mk creates parents after children.
        for old_id in order:
            node = old_nodes[old_id]
            if node[0] == "T":
                new_id = rebuilt.terminal(node[1])
            else:
                new_id = rebuilt.mk(
                    int(node[1]), mapping[int(node[2])], mapping[int(node[3])]
                )
            mapping[old_id] = new_id
        old_peak = self.peak_nodes
        old_attempts = self.intern_attempts
        old_reuses = self.intern_reuses
        self.nodes = rebuilt.nodes
        self.interned = rebuilt.interned
        self.apply_cache = {}
        self.restrict_cache = {}
        self.peak_nodes = max(old_peak, rebuilt.peak_nodes)
        self.intern_attempts = old_attempts + rebuilt.intern_attempts
        self.intern_reuses = old_reuses + rebuilt.intern_reuses
        return [mapping[int(root)] for root in roots]

    def fused_marginalized_product(
        self,
        factor_roots: list[int],
        variable: int,
    ) -> tuple[int, dict[str, int]]:
        """Exactly marginalize a factor bucket without constructing its full joint."""
        if not factor_roots:
            raise AssertionError("empty exact factor bucket")
        lane0 = tuple(self.restrict(root, variable, 0) for root in factor_roots)
        lane1 = tuple(self.restrict(root, variable, 1) for root in factor_roots)
        self.clear_caches()
        memo: dict[tuple[tuple[int, ...], tuple[int, ...]], int] = {}
        calls = 0; hits = 0; terminal_states = 0

        def product_terminal(lane: tuple[int, ...]) -> Any:
            values = [self.nodes[root][1] for root in lane]
            value = values[0]
            for other in values[1:]:
                value = DAG._multiply_value(self.algebra, value, other)
            return value

        def visit(low_lane: tuple[int, ...], high_lane: tuple[int, ...]) -> int:
            nonlocal calls, hits, terminal_states
            calls += 1
            key = (low_lane, high_lane)
            found = memo.get(key)
            if found is not None:
                hits += 1
                return found
            tops = [
                top
                for root in low_lane + high_lane
                for top in [self.top(root)]
                if top is not None
            ]
            if not tops:
                terminal_states += 1
                low_value = product_terminal(low_lane)
                high_value = product_terminal(high_lane)
                out = self.terminal(DAG._marginal_value(self.algebra, low_value, high_value))
            else:
                top = min(tops, key=self.rank.__getitem__)
                low0: list[int] = []; low1: list[int] = []
                high0: list[int] = []; high1: list[int] = []
                for root in low_lane:
                    a, b = self.split_on(root, top); low0.append(a); low1.append(b)
                for root in high_lane:
                    a, b = self.split_on(root, top); high0.append(a); high1.append(b)
                lo = visit(tuple(low0), tuple(high0))
                hi = visit(tuple(low1), tuple(high1))
                out = self.mk(top, lo, hi)
            memo[key] = out
            return out

        root = visit(lane0, lane1)
        return root, {
            "fused_recursive_calls": calls,
            "fused_memo_hits": hits,
            "fused_terminal_states": terminal_states,
            "fused_memo_states": len(memo),
        }

    def to_expression_dag(self, root: int, stabilizer_variables: set[int]) -> tuple[DAG.ExpressionDAG, int]:
        dag = DAG.ExpressionDAG()
        memo: dict[int, int] = {}

        def visit(node_id: int) -> int:
            found = memo.get(node_id)
            if found is not None:
                return found
            node = self.nodes[node_id]
            if node[0] == "T":
                out = dag.terminal(node[1])
            else:
                variable = int(node[1])
                if variable in stabilizer_variables:
                    raise AssertionError("residual MTBDD still depends on eliminated stabilizer")
                if variable < SELECTOR_KEY_BASE:
                    raise AssertionError("unknown residual MTBDD variable namespace")
                parameter = variable - SELECTOR_KEY_BASE
                out = dag.parameter_choice(parameter, visit(int(node[2])), visit(int(node[3])))
            memo[node_id] = out
            return out

        expr_root = visit(int(root))
        [expr_root], _ = dag.compact([expr_root])
        return dag, expr_root


def _local_factor(
    dd: JointMTBDD,
    *,
    qubit: int,
    scope: tuple[int, ...],
    selector_parameter: dict[int, int],
) -> int:
    variables = list(scope)
    if qubit in selector_parameter:
        variables.append(SELECTOR_KEY_BASE + selector_parameter[qubit])
    variables.sort(key=dd.rank.__getitem__)
    low = dd.terminal(DAG._terminal_value(dd.algebra, qubit, 0))
    high = dd.terminal(DAG._terminal_value(dd.algebra, qubit, 1))
    memo: dict[tuple[int, int], int] = {}

    def build(position: int, parity: int) -> int:
        key = (position, parity)
        found = memo.get(key)
        if found is not None:
            return found
        if position == len(variables):
            out = low if parity == 0 else high
        else:
            variable = variables[position]
            out = dd.mk(
                variable,
                build(position + 1, parity),
                build(position + 1, parity ^ 1),
            )
        memo[key] = out
        return out

    return build(0, 0)


def compile_factor_graph(
    *,
    scopes: list[tuple[int, ...]],
    selector_qubits: list[int],
    order: list[int],
    algebra: str,
    emit_progress: bool = False,
) -> dict[str, Any]:
    if algebra not in DAG.ALGEBRAS:
        raise ValueError(algebra)
    selector_parameter = {int(qubit): i for i, qubit in enumerate(selector_qubits)}
    selector_keys = [SELECTOR_KEY_BASE + i for i in range(len(selector_qubits))]
    variable_order = [int(v) for v in order] + selector_keys
    dd = JointMTBDD(variable_order, algebra)
    factors = [
        (
            tuple(scope),
            _local_factor(
                dd,
                qubit=qubit,
                scope=tuple(scope),
                selector_parameter=selector_parameter,
            ),
        )
        for qubit, scope in enumerate(scopes)
    ]
    trace: list[dict[str, Any]] = []
    started = time.time()

    for step, variable in enumerate(order):
        involved = [(scope, root) for scope, root in factors if variable in scope]
        rest = [(scope, root) for scope, root in factors if variable not in scope]
        if not involved:
            raise AssertionError(f"frozen elimination variable absent: {variable}")
        union = tuple(sorted(set().union(*(set(scope) for scope, _ in involved))))
        output_scope = tuple(item for item in union if item != variable)
        output_root, fused = dd.fused_marginalized_product(
            [root for _, root in involved], int(variable)
        )
        rest.append((output_scope, output_root))
        factors = rest
        roots = dd.compact([root for _, root in factors])
        factors = [(scope, root) for (scope, _), root in zip(factors, roots)]
        row = {
            "step": step,
            "variable": int(variable),
            "involved_factor_count": len(involved),
            "union_arity": len(union),
            "output_arity": len(output_scope),
            "active_factor_count": len(factors),
            "retained_mtbdd_nodes": len(dd.nodes),
            **fused,
        }
        trace.append(row)
        if emit_progress:
            print(json.dumps({"phase": "EXACT_JOINT_MTBDD_PROGRESS", **row}, sort_keys=True), flush=True)

    if any(scope for scope, _ in factors):
        raise AssertionError("non-scalar stabilizer factor after frozen elimination")
    root = factors[0][1]
    for _, other in factors[1:]:
        root = dd.apply("MUL", root, other)
    [root] = dd.compact([root])
    dag, expr_root = dd.to_expression_dag(root, set(order))
    receipt = dag.canonical_receipt(expr_root, algebra)
    receipt.update(
        {
            "algebra": algebra,
            "representation": DAG.REPRESENTATION,
            "backend": BACKEND,
            "selector_variable_order": list(range(len(selector_qubits))),
            "elapsed_seconds": time.time() - started,
            "temporary_mtbdd_nodes_peak": dd.peak_nodes,
            "temporary_mtbdd_nodes_final": len(dd.nodes),
            "temporary_mtbdd_intern_attempts": dd.intern_attempts,
            "temporary_mtbdd_intern_reuses": dd.intern_reuses,
            "elimination_trace": trace,
        }
    )
    return {"algebra": algebra, "dag": dag, "root": expr_root, "receipt": receipt}


def compile_c90_algebra(algebra: str, *, emit_progress: bool = True) -> dict[str, Any]:
    preflight = Execute.preflight()
    if preflight.get("quality_exposed") is not False:
        raise AssertionError("quality-blind preflight exposed C90 quality")
    context = Base.load_c90_context()
    code = context["code"]
    return compile_factor_graph(
        scopes=[tuple(scope) for scope in code["scopes"]],
        selector_qubits=[int(q) for q in code["selector_basis_qubits"]],
        order=[int(v) for v in context["order"]],
        algebra=algebra,
        emit_progress=emit_progress,
    )


def save_algebra(item: dict[str, Any], path: Path) -> None:
    payload = {
        "schema_version": 1,
        "experiment_id": EXPERIMENT_ID,
        "source_commit": DAG.git_head(),
        "manifest_payload_sha256": Base.MANIFEST_PAYLOAD,
        "representation": DAG.REPRESENTATION,
        "algebra": item["algebra"],
        "root": int(item["root"]),
        "nodes": item["dag"].nodes,
        "receipt": item["receipt"],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=6) as handle:
        json.dump(payload, handle, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
        handle.write("\n")


def write_json(path: Path, result: dict[str, Any]) -> None:
    payload = dict(result)
    payload["payload_sha256"] = Base.digest(result)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--algebra", choices=DAG.ALGEBRAS, required=True)
    parser.add_argument("--compiled-output", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    item = compile_c90_algebra(args.algebra, emit_progress=True)
    save_algebra(item, args.compiled_output)
    result = {
        "experiment_id": EXPERIMENT_ID,
        "evaluator_version": EVALUATOR_VERSION,
        "phase": "QUALITY_BLIND_COMPILE_ALGEBRA_JOINT_MTBDD",
        "status": "C90_EXACT_ALGEBRA_COMPILED_QUALITY_BLIND",
        "source_commit": DAG.git_head(),
        "manifest_payload_sha256": Base.MANIFEST_PAYLOAD,
        "algebra": args.algebra,
        "compiled": item["receipt"],
        "scientific_semantics_changed": False,
        "quality_exposed": False,
    }
    write_json(args.output, result)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
