#!/usr/bin/env python3
"""Exact shared symbolic C90 compiler for QTR-C90-EXACT-DECODER-001.

This module is a quality-blind compilation backend for the frozen
EXACT_SELECTOR_PARAMETRIC_HASH_CONSED_DAG_C90 representation.  It preserves the
protected elimination order, factor ordering, semiring operations, selector
parameters, and final node encoding.

The temporary compiler adds only one non-retained node kind, S(variable, low,
high), for an unresolved protected stabilizer choice.  Exact restriction and
semiring marginalization eliminate S nodes in the frozen order.  After all 41
protected stabilizer variables are eliminated, no S node may remain; the
reachable graph is rebuilt through qtr_c90_exact_dag_001.ExpressionDAG and is
therefore serialized with exactly the frozen retained node encoding.

No approximation, pruning, variable reordering, selector enumeration, decoder
quality, or injected-error success information is used.
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
BACKEND = "EXACT_SHARED_SYMBOLIC_STABILIZER_CHOICE_CIRCUIT"


class SymbolicCircuit:
    """Hash-consed exact circuit with temporary stabilizer-choice nodes."""

    FINAL_BINARY = {"MUL", "ADD", "MPMUL", "MPMIN"}

    def __init__(self, order: list[int]) -> None:
        self.rank = {int(variable): index for index, variable in enumerate(order)}
        self.nodes: list[tuple[Any, ...]] = []
        self.interned: dict[tuple[Any, ...], int] = {}
        self.created = 0
        self.reused = 0
        self.peak_nodes = 0

    def _intern(self, node: tuple[Any, ...], *, commutative: bool = False) -> int:
        if commutative:
            op, left, right = node
            if int(left) > int(right):
                left, right = right, left
            node = (op, int(left), int(right))
        self.created += 1
        found = self.interned.get(node)
        if found is not None:
            self.reused += 1
            return found
        index = len(self.nodes)
        self.nodes.append(node)
        self.interned[node] = index
        self.peak_nodes = max(self.peak_nodes, len(self.nodes))
        return index

    def terminal(self, value: Any) -> int:
        return self._intern(("T", value))

    def selector_choice(self, parameter: int, low: int, high: int) -> int:
        if low == high:
            return low
        return self._intern(("I", int(parameter), int(low), int(high)))

    def stabilizer_choice(self, variable: int, low: int, high: int) -> int:
        if low == high:
            return low
        return self._intern(("S", int(variable), int(low), int(high)))

    def binary(self, operation: str, left: int, right: int) -> int:
        if operation not in self.FINAL_BINARY:
            raise ValueError(operation)
        return self._intern((operation, int(left), int(right)), commutative=True)

    def restrict(self, root: int, variable: int, bit: int) -> int:
        """Exactly substitute one stabilizer variable throughout a circuit."""
        if bit not in (0, 1):
            raise ValueError(bit)
        memo: dict[int, int] = {}

        def visit(node_id: int) -> int:
            found = memo.get(node_id)
            if found is not None:
                return found
            node = self.nodes[node_id]
            kind = node[0]
            if kind == "T":
                out = node_id
            elif kind == "S":
                current = int(node[1])
                if current == variable:
                    branch = int(node[3] if bit else node[2])
                    out = visit(branch)
                else:
                    out = self.stabilizer_choice(current, visit(int(node[2])), visit(int(node[3])))
            elif kind == "I":
                out = self.selector_choice(int(node[1]), visit(int(node[2])), visit(int(node[3])))
            elif kind in self.FINAL_BINARY:
                out = self.binary(kind, visit(int(node[1])), visit(int(node[2])))
            else:
                raise AssertionError(f"unknown symbolic node: {kind}")
            memo[node_id] = out
            return out

        return visit(int(root))

    def compact(self, roots: list[int]) -> list[int]:
        """Exact reachability GC over all active factor roots."""
        old_nodes = self.nodes
        seen: set[int] = set()
        order: list[int] = []

        def mark(node_id: int) -> None:
            if node_id in seen:
                return
            node = old_nodes[node_id]
            kind = node[0]
            if kind in {"S", "I"}:
                mark(int(node[2])); mark(int(node[3]))
            elif kind in self.FINAL_BINARY:
                mark(int(node[1])); mark(int(node[2]))
            seen.add(node_id)
            order.append(node_id)

        for root in roots:
            mark(int(root))

        rebuilt = SymbolicCircuit([v for v, _ in sorted(self.rank.items(), key=lambda item: item[1])])
        mapping: dict[int, int] = {}
        for old_id in order:
            node = old_nodes[old_id]
            kind = node[0]
            if kind == "T":
                new_id = rebuilt.terminal(node[1])
            elif kind == "S":
                new_id = rebuilt.stabilizer_choice(
                    int(node[1]), mapping[int(node[2])], mapping[int(node[3])]
                )
            elif kind == "I":
                new_id = rebuilt.selector_choice(
                    int(node[1]), mapping[int(node[2])], mapping[int(node[3])]
                )
            elif kind in self.FINAL_BINARY:
                new_id = rebuilt.binary(kind, mapping[int(node[1])], mapping[int(node[2])])
            else:
                raise AssertionError(kind)
            mapping[old_id] = new_id

        self.nodes = rebuilt.nodes
        self.interned = rebuilt.interned
        self.created += rebuilt.created
        self.reused += rebuilt.reused
        self.peak_nodes = max(self.peak_nodes, rebuilt.peak_nodes)
        return [mapping[int(root)] for root in roots]

    def reachable_stabilizer_nodes(self, root: int) -> int:
        seen: set[int] = set(); stack = [int(root)]; count = 0
        while stack:
            node_id = stack.pop()
            if node_id in seen:
                continue
            seen.add(node_id)
            node = self.nodes[node_id]
            kind = node[0]
            if kind == "S":
                count += 1; stack.extend((int(node[2]), int(node[3])))
            elif kind == "I":
                stack.extend((int(node[2]), int(node[3])))
            elif kind in self.FINAL_BINARY:
                stack.extend((int(node[1]), int(node[2])))
        return count

    def to_expression_dag(self, root: int) -> tuple[DAG.ExpressionDAG, int]:
        """Rebuild a stabilizer-free result through the frozen final DAG API."""
        if self.reachable_stabilizer_nodes(root) != 0:
            raise AssertionError("temporary stabilizer-choice nodes remain after frozen elimination")
        dag = DAG.ExpressionDAG()
        memo: dict[int, int] = {}

        def visit(node_id: int) -> int:
            found = memo.get(node_id)
            if found is not None:
                return found
            node = self.nodes[node_id]
            kind = node[0]
            if kind == "T":
                out = dag.terminal(node[1])
            elif kind == "I":
                out = dag.parameter_choice(int(node[1]), visit(int(node[2])), visit(int(node[3])))
            elif kind in self.FINAL_BINARY:
                out = dag.binary(kind, visit(int(node[1])), visit(int(node[2])))
            elif kind == "S":
                raise AssertionError("temporary stabilizer node reached final conversion")
            else:
                raise AssertionError(kind)
            memo[node_id] = out
            return out

        expr_root = visit(int(root))
        [expr_root], _ = dag.compact([expr_root])
        return dag, expr_root


def _local_factor(
    circuit: SymbolicCircuit,
    *,
    qubit: int,
    scope: tuple[int, ...],
    selector_parameter: dict[int, int],
    algebra: str,
) -> int:
    low_terminal = circuit.terminal(DAG._terminal_value(algebra, qubit, 0))
    high_terminal = circuit.terminal(DAG._terminal_value(algebra, qubit, 1))
    if qubit in selector_parameter:
        parameter = selector_parameter[qubit]
        even = circuit.selector_choice(parameter, low_terminal, high_terminal)
        odd = circuit.selector_choice(parameter, high_terminal, low_terminal)
    else:
        even, odd = low_terminal, high_terminal

    ordered_scope = sorted(scope, key=circuit.rank.__getitem__)
    memo: dict[tuple[int, int], int] = {}

    def build(position: int, parity: int) -> int:
        key = (position, parity)
        found = memo.get(key)
        if found is not None:
            return found
        if position == len(ordered_scope):
            out = even if parity == 0 else odd
        else:
            variable = ordered_scope[position]
            out = circuit.stabilizer_choice(
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
    """Compile an exact factor graph into the frozen final expression DAG."""
    if algebra not in DAG.ALGEBRAS:
        raise ValueError(algebra)
    selector_parameter = {int(qubit): i for i, qubit in enumerate(selector_qubits)}
    circuit = SymbolicCircuit(order)
    factors = [
        (
            tuple(scope),
            _local_factor(
                circuit,
                qubit=qubit,
                scope=tuple(scope),
                selector_parameter=selector_parameter,
                algebra=algebra,
            ),
        )
        for qubit, scope in enumerate(scopes)
    ]
    multiply = "MPMUL" if algebra == "min_plus_hamming" else "MUL"
    marginal = "MPMIN" if algebra == "min_plus_hamming" else "ADD"
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
            "temporary_stabilizer_nodes": sum(
                1 for node in circuit.nodes if node[0] == "S"
            ),
        }
        trace.append(row)
        if emit_progress:
            print(json.dumps({"phase": "EXACT_SYMBOLIC_ELIMINATION_PROGRESS", **row}, sort_keys=True), flush=True)

    if any(scope for scope, _ in factors):
        raise AssertionError("non-scalar factor after frozen elimination")
    final_root = factors[0][1]
    for _, root in factors[1:]:
        final_root = circuit.binary(multiply, final_root, root)
    [final_root] = circuit.compact([final_root])
    if circuit.reachable_stabilizer_nodes(final_root) != 0:
        raise AssertionError("frozen elimination left unresolved stabilizer choices")

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
    return {
        "algebra": algebra,
        "dag": dag,
        "root": expr_root,
        "receipt": receipt,
    }


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
        "phase": "QUALITY_BLIND_COMPILE_ALGEBRA_SYMBOLIC",
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
