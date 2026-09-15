#!/usr/bin/env python3
"""Dependency-factored exact symbolic backend for QTR-C90-EXACT-DECODER-001.

The retained scientific object is unchanged: exact terminals, selector choices,
and commutative semiring binary nodes. Temporary unresolved stabilizer choices
are eliminated in the protected deterministic order.

This backend uses only exact semiring identities to avoid duplicating already
marginalized symbolic structure:

  sum_v (A (+) B) = sum_v A (+) sum_v B
  sum_v choice(p,A,B) = choice(p,sum_v A,sum_v B)
  sum_v (A (*) B) = (sum_v A) (*) B, when B is independent of v

where (+) is the protected semiring marginal and (*) its multiplication. When
both multiplicative operands depend on v, the implementation uses the exact
correlated cofactors A[v=0]B[v=0] (+) A[v=1]B[v=1]. No approximation,
pruning, order search, selector enumeration, or quality information is used.
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
BACKEND = "EXACT_DEPENDENCY_FACTORED_SYMBOLIC_ELIMINATION"


def _operations(algebra: str) -> tuple[str, str]:
    if algebra == "min_plus_hamming":
        return "MPMUL", "MPMIN"
    return "MUL", "ADD"


def marginalize_factored(
    circuit: Symbolic.SymbolicCircuit,
    root: int,
    variable: int,
    *,
    multiply: str,
    marginal: str,
) -> tuple[int, dict[str, int]]:
    """Exactly marginalize one protected stabilizer with semiring factoring."""
    depends_memo: dict[int, bool] = {}
    restrict_memo: dict[tuple[int, int], int] = {}
    marginal_memo: dict[int, int] = {}
    stats = {
        "dependency_queries": 0,
        "dependency_hits": 0,
        "restrict_calls": 0,
        "restrict_hits": 0,
        "marginal_calls": 0,
        "marginal_hits": 0,
        "distributed_marginal_nodes": 0,
        "distributed_selector_nodes": 0,
        "distributed_other_stabilizer_nodes": 0,
        "factored_product_nodes": 0,
        "correlated_product_fallbacks": 0,
        "independent_duplicates": 0,
    }

    def depends(node_id: int) -> bool:
        node_id = int(node_id)
        stats["dependency_queries"] += 1
        if node_id in depends_memo:
            stats["dependency_hits"] += 1
            return depends_memo[node_id]
        node = circuit.nodes[node_id]
        kind = node[0]
        if kind == "T":
            out = False
        elif kind == "S":
            out = int(node[1]) == variable or depends(int(node[2])) or depends(int(node[3]))
        elif kind == "I":
            out = depends(int(node[2])) or depends(int(node[3]))
        elif kind in circuit.FINAL_BINARY:
            out = depends(int(node[1])) or depends(int(node[2]))
        else:
            raise AssertionError(f"unknown symbolic node: {kind}")
        depends_memo[node_id] = out
        return out

    def restrict(node_id: int, bit: int) -> int:
        node_id = int(node_id)
        key = (node_id, int(bit))
        stats["restrict_calls"] += 1
        found = restrict_memo.get(key)
        if found is not None:
            stats["restrict_hits"] += 1
            return found
        if not depends(node_id):
            out = node_id
        else:
            node = circuit.nodes[node_id]
            kind = node[0]
            if kind == "T":
                out = node_id
            elif kind == "S":
                current = int(node[1])
                if current == variable:
                    out = restrict(int(node[3] if bit else node[2]), bit)
                else:
                    out = circuit.stabilizer_choice(
                        current,
                        restrict(int(node[2]), bit),
                        restrict(int(node[3]), bit),
                    )
            elif kind == "I":
                out = circuit.selector_choice(
                    int(node[1]),
                    restrict(int(node[2]), bit),
                    restrict(int(node[3]), bit),
                )
            elif kind in circuit.FINAL_BINARY:
                out = circuit.binary(
                    kind,
                    restrict(int(node[1]), bit),
                    restrict(int(node[2]), bit),
                )
            else:
                raise AssertionError(kind)
        restrict_memo[key] = out
        return out

    def visit(node_id: int) -> int:
        node_id = int(node_id)
        stats["marginal_calls"] += 1
        found = marginal_memo.get(node_id)
        if found is not None:
            stats["marginal_hits"] += 1
            return found
        if not depends(node_id):
            stats["independent_duplicates"] += 1
            out = circuit.binary(marginal, node_id, node_id)
        else:
            node = circuit.nodes[node_id]
            kind = node[0]
            if kind == "S":
                current = int(node[1])
                if current == variable:
                    out = circuit.binary(marginal, int(node[2]), int(node[3]))
                else:
                    stats["distributed_other_stabilizer_nodes"] += 1
                    out = circuit.stabilizer_choice(
                        current,
                        visit(int(node[2])),
                        visit(int(node[3])),
                    )
            elif kind == "I":
                stats["distributed_selector_nodes"] += 1
                out = circuit.selector_choice(
                    int(node[1]),
                    visit(int(node[2])),
                    visit(int(node[3])),
                )
            elif kind == marginal:
                stats["distributed_marginal_nodes"] += 1
                out = circuit.binary(
                    marginal,
                    visit(int(node[1])),
                    visit(int(node[2])),
                )
            elif kind == multiply:
                left = int(node[1]); right = int(node[2])
                left_dep = depends(left); right_dep = depends(right)
                if left_dep and not right_dep:
                    stats["factored_product_nodes"] += 1
                    out = circuit.binary(multiply, visit(left), right)
                elif right_dep and not left_dep:
                    stats["factored_product_nodes"] += 1
                    out = circuit.binary(multiply, left, visit(right))
                elif left_dep and right_dep:
                    stats["correlated_product_fallbacks"] += 1
                    low = circuit.binary(multiply, restrict(left, 0), restrict(right, 0))
                    high = circuit.binary(multiply, restrict(left, 1), restrict(right, 1))
                    out = circuit.binary(marginal, low, high)
                else:
                    raise AssertionError("dependent product node has no dependent operand")
            elif kind in circuit.FINAL_BINARY:
                raise AssertionError(
                    f"unexpected semiring node {kind} for multiply={multiply} marginal={marginal}"
                )
            elif kind == "T":
                raise AssertionError("terminal unexpectedly depends on stabilizer")
            else:
                raise AssertionError(kind)
        marginal_memo[node_id] = out
        return out

    output = visit(int(root))
    stats["dependency_cache_size"] = len(depends_memo)
    stats["restrict_cache_size"] = len(restrict_memo)
    stats["marginal_cache_size"] = len(marginal_memo)
    return output, stats


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
    started = time.time()

    for step, variable in enumerate(order):
        involved = [(scope, root) for scope, root in factors if variable in scope]
        rest = [(scope, root) for scope, root in factors if variable not in scope]
        if not involved:
            raise AssertionError(f"frozen elimination variable absent: {variable}")
        union = tuple(sorted(set().union(*(set(scope) for scope, _ in involved))))
        output_scope = tuple(item for item in union if item != variable)

        joint = involved[0][1]
        for _, root in involved[1:]:
            joint = circuit.binary(multiply, joint, root)
        output_root, factor_stats = marginalize_factored(
            circuit,
            joint,
            int(variable),
            multiply=multiply,
            marginal=marginal,
        )

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
            **factor_stats,
        }
        trace.append(row)
        if emit_progress:
            print(json.dumps({"phase": "EXACT_FACTORED_SYMBOLIC_PROGRESS", **row}, sort_keys=True), flush=True)

    if any(scope for scope, _ in factors):
        raise AssertionError("non-scalar factor after frozen elimination")
    final_root = factors[0][1]
    for _, root in factors[1:]:
        final_root = circuit.binary(multiply, final_root, root)
    [final_root] = circuit.compact([final_root])
    if circuit.reachable_stabilizer_nodes(final_root) != 0:
        raise AssertionError("factored elimination left unresolved stabilizer choices")

    dag, expr_root = circuit.to_expression_dag(final_root)
    receipt = dag.canonical_receipt(expr_root, algebra)
    receipt.update(
        {
            "algebra": algebra,
            "representation": DAG.REPRESENTATION,
            "backend": BACKEND,
            "elapsed_seconds": time.time() - started,
            "symbolic_nodes_peak": circuit.peak_nodes,
            "symbolic_intern_attempts": circuit.created,
            "symbolic_intern_reuses": circuit.reused,
            "elimination_trace": trace,
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
        "phase": "QUALITY_BLIND_COMPILE_ALGEBRA_FACTORED",
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
