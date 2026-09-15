#!/usr/bin/env python3
"""Exact symbolic-to-narrow-DD hybrid backend for QTR-C90-EXACT-DECODER-001.

This backend changes only temporary compilation topology. It executes the
protected stabilizer elimination order exactly. While the protected frontier is
wide, it uses the shared symbolic stabilizer-choice circuit. When exactly 13
protected stabilizer variables remain, it deterministically converts the live
factors into the existing exact reduced DD whose terminals are frozen
selector-expression DAG nodes, then completes the remaining eliminations with
the original DD algebra.

The crossover is structural and fixed before any decoder quality is exposed.
No approximation, pruning, order search, selector enumeration as the primary
compiled object, injected-error information, or outcome-responsive choice is
used. The retained object contains only the frozen T/I/commutative-semiring
node encoding.
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
import qtr_c90_exact_symbolic_001 as Symbolic

EXPERIMENT_ID = Base.EXPERIMENT_ID
EVALUATOR_VERSION = "0.1.0"
BACKEND = "EXACT_SYMBOLIC_TO_NARROW_DD_HYBRID"
C90_SWITCH_REMAINING_STABILIZERS = 13


def _operations(algebra: str) -> tuple[str, str]:
    if algebra == "min_plus_hamming":
        return "MPMUL", "MPMIN"
    return "MUL", "ADD"


def _symbolic_prefix(
    *,
    scopes: list[tuple[int, ...]],
    selector_qubits: list[int],
    order: list[int],
    algebra: str,
    prefix_steps: int,
    emit_progress: bool,
) -> tuple[Symbolic.SymbolicCircuit, list[tuple[tuple[int, ...], int]], list[dict[str, Any]]]:
    selector_parameter = {int(qubit): i for i, qubit in enumerate(selector_qubits)}
    circuit = Symbolic.SymbolicCircuit(order)
    factors = [
        (
            tuple(scope),
            Symbolic._local_factor(
                circuit,
                qubit=qubit,
                scope=tuple(scope),
                selector_parameter=selector_parameter,
                algebra=algebra,
            ),
        )
        for qubit, scope in enumerate(scopes)
    ]
    multiply, marginal = _operations(algebra)
    trace: list[dict[str, Any]] = []

    for step, variable in enumerate(order[:prefix_steps]):
        involved = [(scope, root) for scope, root in factors if variable in scope]
        rest = [(scope, root) for scope, root in factors if variable not in scope]
        if not involved:
            raise AssertionError(f"frozen elimination variable absent: {variable}")
        union = tuple(sorted(set().union(*(set(scope) for scope, _ in involved))))
        output_scope = tuple(item for item in union if item != variable)

        joint = involved[0][1]
        for _, root in involved[1:]:
            joint = circuit.binary(multiply, joint, root)
        low = circuit.restrict(joint, variable, 0)
        high = circuit.restrict(joint, variable, 1)
        output_root = circuit.binary(marginal, low, high)

        rest.append((output_scope, output_root))
        factors = rest
        active = circuit.compact([root for _, root in factors])
        factors = [(scope, root) for (scope, _), root in zip(factors, active)]
        row = {
            "step": step,
            "variable": int(variable),
            "involved_factor_count": len(involved),
            "union_arity": len(union),
            "output_arity": len(output_scope),
            "active_factor_count": len(factors),
            "retained_symbolic_nodes": len(circuit.nodes),
            "temporary_stabilizer_nodes": sum(1 for node in circuit.nodes if node[0] == "S"),
        }
        trace.append(row)
        if emit_progress:
            print(json.dumps({"phase": "EXACT_HYBRID_SYMBOLIC_PROGRESS", **row}, sort_keys=True), flush=True)

    return circuit, factors, trace


def _stabilizer_support(
    circuit: Symbolic.SymbolicCircuit,
    root: int,
    memo: dict[int, frozenset[int]],
) -> frozenset[int]:
    found = memo.get(int(root))
    if found is not None:
        return found
    node = circuit.nodes[int(root)]
    kind = node[0]
    if kind == "T":
        out = frozenset()
    elif kind == "S":
        out = frozenset({int(node[1])}) | _stabilizer_support(circuit, int(node[2]), memo) | _stabilizer_support(circuit, int(node[3]), memo)
    elif kind == "I":
        out = _stabilizer_support(circuit, int(node[2]), memo) | _stabilizer_support(circuit, int(node[3]), memo)
    elif kind in circuit.FINAL_BINARY:
        out = _stabilizer_support(circuit, int(node[1]), memo) | _stabilizer_support(circuit, int(node[2]), memo)
    else:
        raise AssertionError(f"unknown symbolic node: {kind}")
    memo[int(root)] = out
    return out


def _selector_expression(
    circuit: Symbolic.SymbolicCircuit,
    root: int,
    dag: DAG.ExpressionDAG,
    support_memo: dict[int, frozenset[int]],
    expression_memo: dict[int, int],
) -> int:
    found = expression_memo.get(int(root))
    if found is not None:
        return found
    if _stabilizer_support(circuit, int(root), support_memo):
        raise AssertionError("selector-expression conversion reached unresolved stabilizer")
    node = circuit.nodes[int(root)]
    kind = node[0]
    if kind == "T":
        out = dag.terminal(node[1])
    elif kind == "I":
        out = dag.parameter_choice(
            int(node[1]),
            _selector_expression(circuit, int(node[2]), dag, support_memo, expression_memo),
            _selector_expression(circuit, int(node[3]), dag, support_memo, expression_memo),
        )
    elif kind in circuit.FINAL_BINARY:
        out = dag.binary(
            kind,
            _selector_expression(circuit, int(node[1]), dag, support_memo, expression_memo),
            _selector_expression(circuit, int(node[2]), dag, support_memo, expression_memo),
        )
    elif kind == "S":
        raise AssertionError("temporary stabilizer node reached selector-expression conversion")
    else:
        raise AssertionError(kind)
    expression_memo[int(root)] = out
    return out


def _dd_parameter_choice(
    dd: DAG.DecisionDiagram,
    dag: DAG.ExpressionDAG,
    parameter: int,
    low: int,
    high: int,
    memo: dict[tuple[int, int, int], int],
) -> int:
    if low == high:
        return low
    key = (int(parameter), int(low), int(high))
    found = memo.get(key)
    if found is not None:
        return found
    ln = dd.nodes[int(low)]
    hn = dd.nodes[int(high)]
    if ln[0] == "T" and hn[0] == "T":
        out = dd.terminal(dag.parameter_choice(int(parameter), int(ln[1]), int(hn[1])))
    else:
        lv = dd._top(int(low))
        hv = dd._top(int(high))
        if lv is None:
            top = hv
        elif hv is None:
            top = lv
        else:
            top = lv if dd.rank[lv] <= dd.rank[hv] else hv
        assert top is not None
        ll, lh = (int(ln[2]), int(ln[3])) if lv == top else (int(low), int(low))
        hl, hh = (int(hn[2]), int(hn[3])) if hv == top else (int(high), int(high))
        out = dd.mk(
            int(top),
            _dd_parameter_choice(dd, dag, parameter, ll, hl, memo),
            _dd_parameter_choice(dd, dag, parameter, lh, hh, memo),
        )
    memo[key] = out
    return out


def _convert_symbolic_factors_to_dd(
    circuit: Symbolic.SymbolicCircuit,
    factors: list[tuple[tuple[int, ...], int]],
    remaining_order: list[int],
) -> tuple[DAG.ExpressionDAG, DAG.DecisionDiagram, list[tuple[tuple[int, ...], int]], dict[str, int]]:
    dag = DAG.ExpressionDAG()
    dd = DAG.DecisionDiagram(remaining_order)
    support_memo: dict[int, frozenset[int]] = {}
    expression_memo: dict[int, int] = {}
    conversion_memo: dict[int, int] = {}
    choice_memo: dict[tuple[int, int, int], int] = {}
    remaining = set(int(v) for v in remaining_order)

    def convert(node_id: int) -> int:
        node_id = int(node_id)
        found = conversion_memo.get(node_id)
        if found is not None:
            return found
        support = _stabilizer_support(circuit, node_id, support_memo)
        if not support:
            out = dd.terminal(
                _selector_expression(circuit, node_id, dag, support_memo, expression_memo)
            )
        else:
            if not support.issubset(remaining):
                raise AssertionError(
                    f"hybrid conversion retained already-eliminated stabilizers: {sorted(support - remaining)}"
                )
            node = circuit.nodes[node_id]
            kind = node[0]
            if kind == "S":
                variable = int(node[1])
                low = convert(int(node[2]))
                high = convert(int(node[3]))
                low_top = dd._top(low)
                high_top = dd._top(high)
                if low_top is not None and dd.rank[low_top] <= dd.rank[variable]:
                    raise AssertionError("symbolic-to-DD ordering violation on low branch")
                if high_top is not None and dd.rank[high_top] <= dd.rank[variable]:
                    raise AssertionError("symbolic-to-DD ordering violation on high branch")
                out = dd.mk(variable, low, high)
            elif kind == "I":
                out = _dd_parameter_choice(
                    dd,
                    dag,
                    int(node[1]),
                    convert(int(node[2])),
                    convert(int(node[3])),
                    choice_memo,
                )
            elif kind in circuit.FINAL_BINARY:
                out = dd.apply(kind, convert(int(node[1])), convert(int(node[2])), dag)
            elif kind == "T":
                raise AssertionError("terminal unexpectedly reported stabilizer support")
            else:
                raise AssertionError(kind)
        conversion_memo[node_id] = out
        return out

    converted = [(scope, convert(root)) for scope, root in factors]
    dd.clear_caches()
    roots = [root for _, root in converted]
    expression_ids = dd.terminal_expression_ids(roots)
    _, mapping = dag.compact(expression_ids)
    dd, roots = dd.compact_and_remap_terminals(roots, mapping)
    converted = [(scope, root) for (scope, _), root in zip(converted, roots)]
    return dag, dd, converted, {
        "source_symbolic_nodes": len(circuit.nodes),
        "converted_expression_nodes": len(dag.nodes),
        "converted_dd_nodes": len(dd.nodes),
        "converted_dd_terminals": len(dd.terminal_expression_ids(roots)),
    }


def _gc_dd(
    dag: DAG.ExpressionDAG,
    dd: DAG.DecisionDiagram,
    factors: list[tuple[tuple[int, ...], int]],
) -> tuple[DAG.DecisionDiagram, list[tuple[tuple[int, ...], int]]]:
    dd.clear_caches()
    roots = [root for _, root in factors]
    expression_ids = dd.terminal_expression_ids(roots)
    _, mapping = dag.compact(expression_ids)
    dd, roots = dd.compact_and_remap_terminals(roots, mapping)
    return dd, [(scope, root) for (scope, _), root in zip(factors, roots)]


def compile_factor_graph(
    *,
    scopes: list[tuple[int, ...]],
    selector_qubits: list[int],
    order: list[int],
    algebra: str,
    switch_remaining_stabilizers: int = C90_SWITCH_REMAINING_STABILIZERS,
    emit_progress: bool = False,
) -> dict[str, Any]:
    if algebra not in DAG.ALGEBRAS:
        raise ValueError(algebra)
    if not (0 <= switch_remaining_stabilizers <= len(order)):
        raise ValueError("invalid hybrid switch frontier")
    prefix_steps = len(order) - switch_remaining_stabilizers
    started = time.time()
    multiply, marginal = _operations(algebra)

    circuit, factors, symbolic_trace = _symbolic_prefix(
        scopes=scopes,
        selector_qubits=selector_qubits,
        order=order,
        algebra=algebra,
        prefix_steps=prefix_steps,
        emit_progress=emit_progress,
    )
    remaining_order = [int(v) for v in order[prefix_steps:]]
    dag, dd, factors, conversion = _convert_symbolic_factors_to_dd(
        circuit, factors, remaining_order
    )
    if emit_progress:
        print(
            json.dumps(
                {
                    "phase": "EXACT_HYBRID_CROSSOVER",
                    "prefix_steps": prefix_steps,
                    "remaining_stabilizers": len(remaining_order),
                    **conversion,
                },
                sort_keys=True,
            ),
            flush=True,
        )

    narrow_trace: list[dict[str, Any]] = []
    dd_peak = dd.peak_nodes
    expr_peak = dag.peak_nodes
    for local_step, variable in enumerate(remaining_order):
        step = prefix_steps + local_step
        involved = [(scope, root) for scope, root in factors if variable in scope]
        rest = [(scope, root) for scope, root in factors if variable not in scope]
        if not involved:
            raise AssertionError(f"frozen elimination variable absent after crossover: {variable}")
        union = tuple(sorted(set().union(*(set(scope) for scope, _ in involved))))
        output_scope = tuple(item for item in union if item != variable)

        joint = involved[0][1]
        for _, root in involved[1:]:
            joint = dd.apply(multiply, joint, root, dag)
            dd_peak = max(dd_peak, dd.peak_nodes)
            expr_peak = max(expr_peak, dag.peak_nodes)
        output_root = dd.sum_out(joint, variable, marginal, dag)
        dd_peak = max(dd_peak, dd.peak_nodes)
        expr_peak = max(expr_peak, dag.peak_nodes)
        rest.append((output_scope, output_root))
        factors = rest
        dd, factors = _gc_dd(dag, dd, factors)
        row = {
            "step": step,
            "variable": int(variable),
            "involved_factor_count": len(involved),
            "union_arity": len(union),
            "output_arity": len(output_scope),
            "active_factor_count": len(factors),
            "retained_expression_nodes": len(dag.nodes),
            "retained_temporary_dd_nodes": len(dd.nodes),
        }
        narrow_trace.append(row)
        if emit_progress:
            print(json.dumps({"phase": "EXACT_HYBRID_NARROW_DD_PROGRESS", **row}, sort_keys=True), flush=True)

    if any(scope for scope, _ in factors):
        raise AssertionError("non-scalar factor after frozen hybrid elimination")
    roots = [root for _, root in factors]
    final_root = roots[0]
    for position in range(1, len(roots)):
        final_root = dd.apply(multiply, final_root, roots[position], dag)
        dd_peak = max(dd_peak, dd.peak_nodes)
        expr_peak = max(expr_peak, dag.peak_nodes)
    node = dd.nodes[final_root]
    if node[0] != "T":
        raise AssertionError("hybrid result still depends on eliminated stabilizers")
    expr_root = int(node[1])
    [expr_root], _ = dag.compact([expr_root])
    expr_peak = max(expr_peak, dag.peak_nodes)
    receipt = dag.canonical_receipt(expr_root, algebra)
    receipt.update(
        {
            "algebra": algebra,
            "representation": DAG.REPRESENTATION,
            "backend": BACKEND,
            "elapsed_seconds": time.time() - started,
            "switch_remaining_stabilizers": switch_remaining_stabilizers,
            "symbolic_prefix_steps": prefix_steps,
            "narrow_dd_steps": len(remaining_order),
            "crossover": conversion,
            "symbolic_elimination_trace": symbolic_trace,
            "narrow_dd_elimination_trace": narrow_trace,
            "temporary_dd_nodes_peak": dd_peak,
            "expression_nodes_peak_after_crossover": expr_peak,
            "temporary_stabilizer_nodes_final": 0,
        }
    )
    return {"algebra": algebra, "dag": dag, "root": expr_root, "receipt": receipt}


def compile_c90_algebra(algebra: str, *, emit_progress: bool = True) -> dict[str, Any]:
    preflight = Execute.preflight()
    if preflight.get("quality_exposed") is not False:
        raise AssertionError("quality-blind preflight exposed C90 quality")
    context = Base.load_c90_context()
    code = context["code"]
    order = [int(v) for v in context["order"]]
    if len(order) != 41:
        raise AssertionError("protected C90 stabilizer rank drift")
    item = compile_factor_graph(
        scopes=[tuple(scope) for scope in code["scopes"]],
        selector_qubits=[int(q) for q in code["selector_basis_qubits"]],
        order=order,
        algebra=algebra,
        switch_remaining_stabilizers=C90_SWITCH_REMAINING_STABILIZERS,
        emit_progress=emit_progress,
    )
    if item["receipt"]["symbolic_prefix_steps"] != 28:
        raise AssertionError("protected C90 hybrid crossover step drift")
    return item


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    unsigned = dict(payload)
    payload = dict(payload)
    payload["payload_sha256"] = Base.digest(unsigned)
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
        "phase": "QUALITY_BLIND_COMPILE_ALGEBRA_HYBRID",
        "status": "C90_EXACT_ALGEBRA_COMPILED_QUALITY_BLIND",
        "source_commit": DAG.git_head(),
        "manifest_payload_sha256": Base.MANIFEST_PAYLOAD,
        "algebra": args.algebra,
        "compiled": item["receipt"],
        "quality_exposed": False,
        "scientific_semantics_changed": False,
    }
    write_json(args.output, result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "algebra": args.algebra,
                "canonical_node_stream_sha256": item["receipt"]["canonical_node_stream_sha256"],
                "reachable_nodes": item["receipt"]["reachable_nodes"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
