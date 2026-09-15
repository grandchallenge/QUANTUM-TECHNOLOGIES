#!/usr/bin/env python3
"""Resumable exact C90 algebra compiler for hosted-runner recovery.

This module preserves QTR-C90-EXACT-DECODER-001 scientific semantics.  It
executes the frozen elimination order one variable per process and serializes
only exact intermediate compiler state between processes.  Additional garbage
collection removes unreachable temporary DD/DAG nodes; it performs no pruning,
approximation, reordering, or outcome-dependent adaptation.
"""
from __future__ import annotations

import argparse
import gc
import gzip
import json
import os
import pickle
import tempfile
import time
from pathlib import Path
from typing import Any

import qtr_c90_exact_decoder_001 as Base
import qtr_c90_exact_dag_001 as DAG
import qtr_c90_exact_execute_001 as Execute

EXPERIMENT_ID = Base.EXPERIMENT_ID
EVALUATOR_VERSION = "0.1.0"
STATE_SCHEMA_VERSION = 1


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _atomic_pickle(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=3, mtime=0) as handle:
                pickle.dump(payload, handle, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def _load_pickle(path: Path) -> dict[str, Any]:
    with gzip.open(path, "rb") as handle:
        payload = pickle.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("resumable compiler state is not a mapping")
    return payload


def _state_header(algebra: str, context: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "experiment_id": EXPERIMENT_ID,
        "source_commit": DAG.git_head(),
        "manifest_payload_sha256": Base.MANIFEST_PAYLOAD,
        "representation": DAG.REPRESENTATION,
        "algebra": algebra,
        "frozen_order_sha256": Base.digest(list(context["order"])),
    }


def _verify_header(state: dict[str, Any], context: dict[str, Any]) -> None:
    expected = _state_header(str(state.get("algebra")), context)
    for key, value in expected.items():
        if state.get(key) != value:
            raise ValueError(f"resumable compiler state drift: {key}")
    if state.get("algebra") not in DAG.ALGEBRAS:
        raise ValueError("resumable compiler algebra drift")


def _restore(state: dict[str, Any], context: dict[str, Any]) -> tuple[DAG.ExpressionDAG, DAG.DecisionDiagram, list[tuple[tuple[int, ...], int]]]:
    dag = DAG.ExpressionDAG()
    dag.nodes = state["dag_nodes"]
    dag.interned = {node: i for i, node in enumerate(dag.nodes)}
    dag.created = int(state["dag_created"])
    dag.reused = int(state["dag_reused"])
    dag.peak_nodes = int(state["dag_peak_nodes"])

    dd = DAG.DecisionDiagram(list(context["order"]))
    dd.nodes = state["dd_nodes"]
    dd.interned = {node: i for i, node in enumerate(dd.nodes)}
    dd.peak_nodes = int(state["dd_peak_nodes"])
    dd.clear_caches()

    factors = [(tuple(scope), int(root)) for scope, root in state["factors"]]
    return dag, dd, factors


def _store_runtime(
    state: dict[str, Any],
    dag: DAG.ExpressionDAG,
    dd: DAG.DecisionDiagram,
    factors: list[tuple[tuple[int, ...], int]],
) -> None:
    state["dag_nodes"] = dag.nodes
    state["dag_created"] = dag.created
    state["dag_reused"] = dag.reused
    state["dag_peak_nodes"] = dag.peak_nodes
    state["dd_nodes"] = dd.nodes
    state["dd_peak_nodes"] = dd.peak_nodes
    state["factors"] = factors


def _exact_gc(
    dag: DAG.ExpressionDAG,
    dd: DAG.DecisionDiagram,
    roots: list[int],
) -> tuple[DAG.DecisionDiagram, list[int]]:
    """Collect unreachable temporary state while preserving every live root."""
    if not roots:
        return dd, roots
    dd.clear_caches()
    expression_ids = dd.terminal_expression_ids(roots)
    _, mapping = dag.compact(expression_ids)
    dd, roots = dd.compact_and_remap_terminals(roots, mapping)
    dd.clear_caches()
    gc.collect()
    return dd, roots


def initialize(algebra: str, state_path: Path) -> dict[str, Any]:
    if algebra not in DAG.ALGEBRAS:
        raise ValueError(algebra)
    preflight = Execute.preflight()
    if preflight.get("quality_exposed") is not False:
        raise AssertionError("preflight exposed C90 quality")
    context = Base.load_c90_context()
    code = context["code"]
    order = list(context["order"])
    scopes = [tuple(scope) for scope in code["scopes"]]
    selector_parameter = {qubit: i for i, qubit in enumerate(code["selector_basis_qubits"])}
    dag = DAG.ExpressionDAG()
    dd = DAG.DecisionDiagram(order)
    factors = [
        (scope, DAG._local_symbolic_factor(qubit, scope, selector_parameter, algebra, dag, dd))
        for qubit, scope in enumerate(scopes)
    ]
    state: dict[str, Any] = {
        **_state_header(algebra, context),
        "next_step": 0,
        "trace": [],
        "peak_dd": len(dd.nodes),
        "peak_expr": len(dag.nodes),
        "elapsed_seconds": 0.0,
        "complete": False,
    }
    _store_runtime(state, dag, dd, factors)
    _atomic_pickle(state_path, state)
    return {
        "experiment_id": EXPERIMENT_ID,
        "evaluator_version": EVALUATOR_VERSION,
        "status": "C90_EXACT_RESUMABLE_STATE_INITIALIZED",
        "source_commit": DAG.git_head(),
        "algebra": algebra,
        "next_step": 0,
        "elimination_variable_count": len(order),
        "quality_exposed": False,
    }


def advance_one(state_path: Path) -> dict[str, Any]:
    started = time.time()
    state = _load_pickle(state_path)
    context = Base.load_c90_context()
    _verify_header(state, context)
    algebra = str(state["algebra"])
    order = list(context["order"])
    step = int(state["next_step"])
    if state.get("complete"):
        raise ValueError("resumable compiler state already finalized")
    if not (0 <= step < len(order)):
        raise ValueError("resumable compiler next_step overflow")

    dag, dd, factors = _restore(state, context)
    variable = order[step]
    multiply = "MPMUL" if algebra == "min_plus_hamming" else "MUL"
    marginal = "MPMIN" if algebra == "min_plus_hamming" else "ADD"

    involved = [(scope, root) for scope, root in factors if variable in scope]
    rest = [(scope, root) for scope, root in factors if variable not in scope]
    if not involved:
        raise AssertionError(f"frozen elimination variable absent: {variable}")
    union = tuple(sorted(set().union(*(set(scope) for scope, _ in involved))))
    output_scope = tuple(item for item in union if item != variable)

    remaining_roots = [root for _, root in involved]
    joint = remaining_roots[0]
    for position in range(1, len(remaining_roots)):
        joint = dd.apply(multiply, joint, remaining_roots[position], dag)
        state["peak_dd"] = max(int(state["peak_dd"]), dd.peak_nodes)
        state["peak_expr"] = max(int(state["peak_expr"]), dag.peak_nodes)
        live = [joint] + [root for _, root in rest] + remaining_roots[position + 1 :]
        dd, live = _exact_gc(dag, dd, live)
        joint = live[0]
        rest_roots = live[1 : 1 + len(rest)]
        rest = [(scope, root) for (scope, _), root in zip(rest, rest_roots)]
        remaining_roots[position + 1 :] = live[1 + len(rest) :]

    low = dd.restrict(joint, variable, 0)
    high = dd.restrict(joint, variable, 1)
    state["peak_dd"] = max(int(state["peak_dd"]), dd.peak_nodes)
    live = [low, high] + [root for _, root in rest]
    dd, live = _exact_gc(dag, dd, live)
    low, high = live[0], live[1]
    rest = [(scope, root) for (scope, _), root in zip(rest, live[2:])]

    output_root = dd.apply(marginal, low, high, dag)
    state["peak_dd"] = max(int(state["peak_dd"]), dd.peak_nodes)
    state["peak_expr"] = max(int(state["peak_expr"]), dag.peak_nodes)
    live = [output_root] + [root for _, root in rest]
    dd, live = _exact_gc(dag, dd, live)
    output_root = live[0]
    rest = [(scope, root) for (scope, _), root in zip(rest, live[1:])]
    rest.append((output_scope, output_root))
    factors = rest

    state["trace"].append(
        {
            "step": step,
            "variable": variable,
            "involved_factor_count": len(involved),
            "union_arity": len(union),
            "output_arity": len(output_scope),
            "active_factor_count": len(factors),
            "retained_expression_nodes": len(dag.nodes),
            "retained_temporary_dd_nodes": len(dd.nodes),
        }
    )
    state["next_step"] = step + 1
    state["elapsed_seconds"] = float(state["elapsed_seconds"]) + (time.time() - started)
    _store_runtime(state, dag, dd, factors)
    _atomic_pickle(state_path, state)
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
        "retained_expression_nodes": len(dag.nodes),
        "retained_temporary_dd_nodes": len(dd.nodes),
        "quality_exposed": False,
    }


def _save_final_algebra(item: dict[str, Any], path: Path) -> None:
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


def finalize(state_path: Path, compiled_output: Path) -> dict[str, Any]:
    started = time.time()
    state = _load_pickle(state_path)
    context = Base.load_c90_context()
    _verify_header(state, context)
    algebra = str(state["algebra"])
    order = list(context["order"])
    if int(state["next_step"]) != len(order):
        raise ValueError("cannot finalize incomplete resumable compiler state")
    if state.get("complete"):
        raise ValueError("resumable compiler state already finalized")

    dag, dd, factors = _restore(state, context)
    multiply = "MPMUL" if algebra == "min_plus_hamming" else "MUL"
    if any(scope for scope, _ in factors):
        raise AssertionError("non-scalar factor after frozen elimination")
    roots = [root for _, root in factors]
    final_root = roots[0]
    for position in range(1, len(roots)):
        final_root = dd.apply(multiply, final_root, roots[position], dag)
        state["peak_dd"] = max(int(state["peak_dd"]), dd.peak_nodes)
        state["peak_expr"] = max(int(state["peak_expr"]), dag.peak_nodes)
        live = [final_root] + roots[position + 1 :]
        dd, live = _exact_gc(dag, dd, live)
        final_root = live[0]
        roots[position + 1 :] = live[1:]

    node = dd.nodes[final_root]
    if node[0] != "T":
        raise AssertionError("compiled C90 result still depends on eliminated variables")
    expr_root = int(node[1])
    [expr_root], _ = dag.compact([expr_root])
    state["peak_expr"] = max(int(state["peak_expr"]), dag.peak_nodes)
    receipt = dag.canonical_receipt(expr_root, algebra)
    state["elapsed_seconds"] = float(state["elapsed_seconds"]) + (time.time() - started)
    receipt.update(
        {
            "algebra": algebra,
            "representation": DAG.REPRESENTATION,
            "elapsed_seconds": float(state["elapsed_seconds"]),
            "expression_nodes_peak": int(state["peak_expr"]),
            "temporary_dd_nodes_peak": int(state["peak_dd"]),
            "intern_attempts": dag.created,
            "intern_reuses": dag.reused,
            "elimination_trace": state["trace"],
            "execution_topology": "one_frozen_elimination_variable_per_process_with_exact_gc",
        }
    )
    item = {"algebra": algebra, "dag": dag, "root": expr_root, "receipt": receipt}
    _save_final_algebra(item, compiled_output)
    state["complete"] = True
    state["final_canonical_node_stream_sha256"] = receipt["canonical_node_stream_sha256"]
    _store_runtime(state, dag, dd, [((), final_root)])
    _atomic_pickle(state_path, state)
    return {
        "experiment_id": EXPERIMENT_ID,
        "evaluator_version": EVALUATOR_VERSION,
        "phase": "QUALITY_BLIND_COMPILE_ALGEBRA_RESUMABLE",
        "status": "C90_EXACT_ALGEBRA_COMPILED_QUALITY_BLIND",
        "source_commit": DAG.git_head(),
        "manifest_payload_sha256": Base.MANIFEST_PAYLOAD,
        "algebra": algebra,
        "compiled": receipt,
        "quality_exposed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init")
    p.add_argument("--algebra", required=True, choices=DAG.ALGEBRAS)
    p.add_argument("--state", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)

    p = sub.add_parser("step")
    p.add_argument("--state", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)

    p = sub.add_parser("finalize")
    p.add_argument("--state", type=Path, required=True)
    p.add_argument("--compiled-output", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "init":
        result = initialize(args.algebra, args.state)
    elif args.command == "step":
        result = advance_one(args.state)
    else:
        result = finalize(args.state, args.compiled_output)
    result["payload_sha256"] = Base.digest(result)
    write_json(args.output, result)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
