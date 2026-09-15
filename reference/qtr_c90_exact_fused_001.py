#!/usr/bin/env python3
"""Exact fused bucket-elimination step for QTR-C90-EXACT-DECODER-001.

This is an execution-backend refinement only.  For the current frozen
elimination variable v, instead of materializing the complete product DD and
then applying sum_out(v), it uses the exact identity

  marginal_v(prod_i f_i) = marginal(prod_i f_i|v=0, prod_i f_i|v=1)

and constructs the marginalized DD directly by simultaneous Shannon recursion.
The factor sequence, binary expression association, semiring operations,
frozen elimination order, selector parameters, and final canonical expression
semantics are unchanged.  No approximation, pruning, order search, or quality
information is used.
"""
from __future__ import annotations

import argparse
import gc
import json
import time
from pathlib import Path
from typing import Any

import qtr_c90_exact_decoder_001 as Base
import qtr_c90_exact_dag_001 as DAG
import qtr_c90_exact_resumable_001 as R

EXPERIMENT_ID = Base.EXPERIMENT_ID
EVALUATOR_VERSION = "0.1.0"


def _node_top(dd: DAG.DecisionDiagram, root: int) -> int | None:
    node = dd.nodes[root]
    return None if node[0] == "T" else int(node[1])


def _split_on(dd: DAG.DecisionDiagram, root: int, variable: int) -> tuple[int, int]:
    node = dd.nodes[root]
    if node[0] == "T":
        return root, root
    current = int(node[1])
    if current == variable:
        return int(node[2]), int(node[3])
    if dd.rank[current] > dd.rank[variable]:
        return root, root
    raise AssertionError(
        f"fused contraction encountered earlier uneliminated variable {current} before {variable}"
    )


def _multiply_terminal_expressions(
    dag: DAG.ExpressionDAG,
    operation: str,
    roots: tuple[int, ...],
) -> int:
    if not roots:
        raise AssertionError("empty exact product lane")
    first = dd_node = None
    # roots here are expression-node ids, not DD ids.
    value = int(roots[0])
    for other in roots[1:]:
        value = dag.binary(operation, value, int(other))
    return value


def fused_marginalized_product(
    dd: DAG.DecisionDiagram,
    dag: DAG.ExpressionDAG,
    factor_roots: list[int],
    variable: int,
    multiply: str,
    marginal: str,
) -> tuple[int, dict[str, int]]:
    """Return exact DD for marginal_v(product(factor_roots)) without the full joint."""
    if not factor_roots:
        raise AssertionError("cannot eliminate empty factor bucket")

    # Restriction distributes over pointwise multiplication exactly.  Because
    # variable is the next frozen elimination variable, these restrictions are
    # small and occur before the 26-variable joint can be created.
    lane0 = tuple(dd.restrict(root, variable, 0) for root in factor_roots)
    lane1 = tuple(dd.restrict(root, variable, 1) for root in factor_roots)
    dd.clear_caches()

    memo: dict[tuple[tuple[int, ...], tuple[int, ...]], int] = {}
    calls = 0
    memo_hits = 0
    terminal_states = 0
    peak_memo = 0

    def visit(low_lane: tuple[int, ...], high_lane: tuple[int, ...]) -> int:
        nonlocal calls, memo_hits, terminal_states, peak_memo
        calls += 1
        key = (low_lane, high_lane)
        found = memo.get(key)
        if found is not None:
            memo_hits += 1
            return found

        tops = [
            top
            for root in low_lane + high_lane
            for top in [_node_top(dd, root)]
            if top is not None
        ]
        if not tops:
            terminal_states += 1
            low_exprs = tuple(int(dd.nodes[root][1]) for root in low_lane)
            high_exprs = tuple(int(dd.nodes[root][1]) for root in high_lane)
            low_expr = _multiply_terminal_expressions(dag, multiply, low_exprs)
            high_expr = _multiply_terminal_expressions(dag, multiply, high_exprs)
            out = dd.terminal(dag.binary(marginal, low_expr, high_expr))
        else:
            top = min(tops, key=dd.rank.__getitem__)
            low0: list[int] = []
            low1: list[int] = []
            high0: list[int] = []
            high1: list[int] = []
            for root in low_lane:
                a, b = _split_on(dd, root, top)
                low0.append(a); low1.append(b)
            for root in high_lane:
                a, b = _split_on(dd, root, top)
                high0.append(a); high1.append(b)
            lo = visit(tuple(low0), tuple(high0))
            hi = visit(tuple(low1), tuple(high1))
            out = dd.mk(top, lo, hi)

        memo[key] = out
        if len(memo) > peak_memo:
            peak_memo = len(memo)
            if peak_memo % 100000 == 0:
                print(
                    json.dumps(
                        {
                            "phase": "FUSED_EXACT_CONTRACTION_PROGRESS",
                            "variable": variable,
                            "memo_states": peak_memo,
                            "dd_nodes": len(dd.nodes),
                            "expression_nodes": len(dag.nodes),
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )
        return out

    output = visit(lane0, lane1)
    stats = {
        "fused_recursive_calls": calls,
        "fused_memo_hits": memo_hits,
        "fused_terminal_states": terminal_states,
        "fused_peak_memo_states": peak_memo,
    }
    memo.clear()
    gc.collect()
    return output, stats


def advance_one_fused(state_path: Path) -> dict[str, Any]:
    started = time.time()
    state = R._load_pickle(state_path)
    context = Base.load_c90_context()
    R._verify_header(state, context)
    algebra = str(state["algebra"])
    order = list(context["order"])
    step = int(state["next_step"])
    if state.get("complete"):
        raise ValueError("resumable compiler state already finalized")
    if not (0 <= step < len(order)):
        raise ValueError("resumable compiler next_step overflow")

    dag, dd, factors = R._restore(state, context)
    variable = order[step]
    multiply = "MPMUL" if algebra == "min_plus_hamming" else "MUL"
    marginal = "MPMIN" if algebra == "min_plus_hamming" else "ADD"

    involved = [(scope, root) for scope, root in factors if variable in scope]
    rest = [(scope, root) for scope, root in factors if variable not in scope]
    if not involved:
        raise AssertionError(f"frozen elimination variable absent: {variable}")
    union = tuple(sorted(set().union(*(set(scope) for scope, _ in involved))))
    output_scope = tuple(item for item in union if item != variable)

    output_root, fused_stats = fused_marginalized_product(
        dd,
        dag,
        [root for _, root in involved],
        variable,
        multiply,
        marginal,
    )
    state["peak_dd"] = max(int(state["peak_dd"]), dd.peak_nodes)
    state["peak_expr"] = max(int(state["peak_expr"]), dag.peak_nodes)

    # Exact reachability GC across the newly marginalized factor plus every
    # unaffected active factor.  This is storage reclamation only.
    live = [output_root] + [root for _, root in rest]
    dd, live = R._exact_gc(dag, dd, live)
    output_root = live[0]
    rest = [(scope, root) for (scope, _), root in zip(rest, live[1:])]
    rest.append((output_scope, output_root))
    factors = rest

    trace_row = {
        "step": step,
        "variable": variable,
        "involved_factor_count": len(involved),
        "involved_scope_arities": [len(scope) for scope, _ in involved],
        "union_arity": len(union),
        "output_arity": len(output_scope),
        "active_factor_count": len(factors),
        "retained_expression_nodes": len(dag.nodes),
        "retained_temporary_dd_nodes": len(dd.nodes),
        "backend": "FUSED_EXACT_MARGINALIZED_PRODUCT_DD",
        **fused_stats,
    }
    state["trace"].append(trace_row)
    state["next_step"] = step + 1
    state["elapsed_seconds"] = float(state["elapsed_seconds"]) + (time.time() - started)
    R._store_runtime(state, dag, dd, factors)
    R._atomic_pickle(state_path, state)

    return {
        "experiment_id": EXPERIMENT_ID,
        "evaluator_version": EVALUATOR_VERSION,
        "status": "C90_EXACT_RESUMABLE_ELIMINATION_STEP_COMPLETED",
        "source_commit": DAG.git_head(),
        "algebra": algebra,
        "completed_step": step,
        "completed_variable": variable,
        "next_step": step + 1,
        "elimination_variable_count": len(order),
        "union_arity": len(union),
        "output_arity": len(output_scope),
        "retained_expression_nodes": len(dag.nodes),
        "retained_temporary_dd_nodes": len(dd.nodes),
        "backend": "FUSED_EXACT_MARGINALIZED_PRODUCT_DD",
        **fused_stats,
        "quality_exposed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = advance_one_fused(args.state)
    result["payload_sha256"] = Base.digest(result)
    R.write_json(args.output, result)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
