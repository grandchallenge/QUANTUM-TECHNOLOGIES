#!/usr/bin/env python3
"""Exact selector-parametric C90 DAG compiler for QTR-C90-EXACT-DECODER-001.

The retained scientific representation contains only exact terminals, selector
parameter choices, and commutative semiring binary nodes. A reduced ordered
multi-terminal decision diagram over the 41 eliminated stabilizer variables is
used only as a temporary exact compilation data structure. Removing unreachable
temporary nodes is garbage collection, not approximation or pruning.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import subprocess
import time
from collections import Counter
from pathlib import Path
from typing import Any

import qtr_c90_exact_decoder_001 as Base

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = Base.EXPERIMENT_ID
MANIFEST_PAYLOAD = Base.MANIFEST_PAYLOAD
ALGEBRAS = ("sum_product_bsc_p_0_1", "soft_tropical_base_2", "min_plus_hamming")
REPRESENTATION = "EXACT_SELECTOR_PARAMETRIC_HASH_CONSED_DAG_C90"


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "UNKNOWN"


def _terminal_value(algebra: str, qubit: int, bit: int) -> Any:
    if algebra == "sum_product_bsc_p_0_1":
        return 9 if bit == 0 else 1
    if algebra == "soft_tropical_base_2":
        return 2 if bit == 0 else 1
    integer = (1 << qubit) if bit else 0
    return ((bit, integer), integer)


def _multiply_value(algebra: str, left: Any, right: Any) -> Any:
    if algebra != "min_plus_hamming":
        return left * right
    return ((left[0][0] + right[0][0], left[0][1] + right[0][1]), left[1] + right[1])


def _marginal_value(algebra: str, left: Any, right: Any) -> Any:
    if algebra != "min_plus_hamming":
        return left + right
    return (min(left[0], right[0]), min(left[1], right[1]))


class ExpressionDAG:
    """Hash-consed exact DAG over the 49 frozen selector parameters."""
    def __init__(self) -> None:
        self.nodes: list[tuple[Any, ...]] = []
        self.interned: dict[tuple[Any, ...], int] = {}
        self.created = 0
        self.reused = 0
        self.peak_nodes = 0

    def _intern(self, node: tuple[Any, ...], commutative: bool = False) -> int:
        if commutative:
            op, left, right = node
            if left > right:
                left, right = right, left
            node = (op, left, right)
        self.created += 1
        found = self.interned.get(node)
        if found is not None:
            self.reused += 1
            return found
        idx = len(self.nodes)
        self.nodes.append(node)
        self.interned[node] = idx
        self.peak_nodes = max(self.peak_nodes, len(self.nodes))
        return idx

    def terminal(self, value: Any) -> int:
        return self._intern(("T", value))

    def parameter_choice(self, parameter: int, low: int, high: int) -> int:
        if low == high:
            return low
        return self._intern(("I", int(parameter), low, high))

    def binary(self, operation: str, left: int, right: int) -> int:
        return self._intern((operation, left, right), commutative=True)

    def evaluate(self, root: int, selector_coordinate: int, algebra: str) -> Any:
        memo: dict[int, Any] = {}
        def visit(node_id: int) -> Any:
            if node_id in memo:
                return memo[node_id]
            node = self.nodes[node_id]
            kind = node[0]
            if kind == "T":
                value = node[1]
            elif kind == "I":
                branch = node[3] if selector_coordinate & (1 << node[1]) else node[2]
                value = visit(branch)
            elif kind in {"MUL", "MPMUL"}:
                value = _multiply_value(algebra, visit(node[1]), visit(node[2]))
            elif kind in {"ADD", "MPMIN"}:
                value = _marginal_value(algebra, visit(node[1]), visit(node[2]))
            else:
                raise AssertionError(f"unknown expression node {kind}")
            memo[node_id] = value
            return value
        return visit(root)

    def compact(self, roots: list[int]) -> tuple[list[int], dict[int, int]]:
        seen: set[int] = set(); order: list[int] = []
        def visit(node_id: int) -> None:
            if node_id in seen:
                return
            node = self.nodes[node_id]
            if node[0] == "I":
                visit(node[2]); visit(node[3])
            elif node[0] in {"MUL", "MPMUL", "ADD", "MPMIN"}:
                visit(node[1]); visit(node[2])
            seen.add(node_id); order.append(node_id)
        for root in roots:
            visit(root)
        mapping: dict[int, int] = {}; new_nodes: list[tuple[Any, ...]] = []
        for old in order:
            node = self.nodes[old]
            if node[0] == "T":
                rebuilt = node
            elif node[0] == "I":
                rebuilt = ("I", node[1], mapping[node[2]], mapping[node[3]])
            else:
                left, right = mapping[node[1]], mapping[node[2]]
                if left > right:
                    left, right = right, left
                rebuilt = (node[0], left, right)
            mapping[old] = len(new_nodes); new_nodes.append(rebuilt)
        self.nodes = new_nodes
        self.interned = {node: i for i, node in enumerate(new_nodes)}
        self.peak_nodes = max(self.peak_nodes, len(new_nodes))
        return [mapping[root] for root in roots], mapping

    def canonical_receipt(self, root: int, algebra: str) -> dict[str, Any]:
        seen: set[int] = set(); order: list[int] = []
        def visit(node_id: int) -> None:
            if node_id in seen:
                return
            node = self.nodes[node_id]
            if node[0] == "I":
                visit(node[2]); visit(node[3])
            elif node[0] in {"MUL", "MPMUL", "ADD", "MPMIN"}:
                visit(node[1]); visit(node[2])
            seen.add(node_id); order.append(node_id)
        visit(root)
        remap = {old: new for new, old in enumerate(order)}
        h = hashlib.sha256()
        header = {"format": "QTR-C90-EXACT-DECODER-001-DAG-v1", "algebra": algebra, "root": remap[root]}
        h.update(json.dumps(header, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode() + b"\n")
        kinds: Counter[str] = Counter(); serialized_bytes = 0
        for old in order:
            node = self.nodes[old]; kinds[node[0]] += 1
            if node[0] == "T":
                record: Any = ["T", node[1]]
            elif node[0] == "I":
                record = ["I", node[1], remap[node[2]], remap[node[3]]]
            else:
                record = [node[0], remap[node[1]], remap[node[2]]]
            raw = json.dumps(record, separators=(",", ":"), ensure_ascii=True).encode() + b"\n"
            h.update(raw); serialized_bytes += len(raw)
        return {
            "canonical_node_stream_sha256": h.hexdigest(), "root": remap[root],
            "reachable_nodes": len(order), "node_kind_counts": dict(sorted(kinds.items())),
            "canonical_node_stream_bytes_excluding_header": serialized_bytes,
        }


class DecisionDiagram:
    """Temporary exact reduced ordered DD over eliminated X variables."""
    def __init__(self, order: list[int]) -> None:
        self.rank = {var: i for i, var in enumerate(order)}
        self.nodes: list[tuple[Any, ...]] = []
        self.interned: dict[tuple[Any, ...], int] = {}
        self.apply_cache: dict[tuple[str, int, int], int] = {}
        self.restrict_cache: dict[tuple[int, int, int], int] = {}
        self.peak_nodes = 0

    def terminal(self, expression: int) -> int:
        key = ("T", int(expression)); found = self.interned.get(key)
        if found is not None: return found
        idx = len(self.nodes); self.nodes.append(key); self.interned[key] = idx
        self.peak_nodes = max(self.peak_nodes, len(self.nodes)); return idx

    def mk(self, variable: int, low: int, high: int) -> int:
        if low == high: return low
        key = ("D", int(variable), int(low), int(high)); found = self.interned.get(key)
        if found is not None: return found
        idx = len(self.nodes); self.nodes.append(key); self.interned[key] = idx
        self.peak_nodes = max(self.peak_nodes, len(self.nodes)); return idx

    def _top(self, node_id: int) -> int | None:
        node = self.nodes[node_id]
        return None if node[0] == "T" else int(node[1])

    def apply(self, operation: str, left: int, right: int, dag: ExpressionDAG) -> int:
        if left > right: left, right = right, left
        key = (operation, left, right); found = self.apply_cache.get(key)
        if found is not None: return found
        ln, rn = self.nodes[left], self.nodes[right]
        if ln[0] == "T" and rn[0] == "T":
            out = self.terminal(dag.binary(operation, int(ln[1]), int(rn[1])))
        else:
            lv, rv = self._top(left), self._top(right)
            if lv is None: top = rv
            elif rv is None: top = lv
            else: top = lv if self.rank[lv] <= self.rank[rv] else rv
            assert top is not None
            ll, lh = (int(ln[2]), int(ln[3])) if lv == top else (left, left)
            rl, rh = (int(rn[2]), int(rn[3])) if rv == top else (right, right)
            out = self.mk(top, self.apply(operation, ll, rl, dag), self.apply(operation, lh, rh, dag))
        self.apply_cache[key] = out; return out

    def restrict(self, root: int, variable: int, bit: int) -> int:
        key = (root, variable, bit); found = self.restrict_cache.get(key)
        if found is not None: return found
        node = self.nodes[root]
        if node[0] == "T": out = root
        else:
            current = int(node[1])
            if current == variable: out = int(node[3] if bit else node[2])
            elif self.rank[current] > self.rank[variable]: out = root
            else: out = self.mk(current, self.restrict(int(node[2]), variable, bit), self.restrict(int(node[3]), variable, bit))
        self.restrict_cache[key] = out; return out

    def sum_out(self, root: int, variable: int, operation: str, dag: ExpressionDAG) -> int:
        return self.apply(operation, self.restrict(root, variable, 0), self.restrict(root, variable, 1), dag)

    def clear_caches(self) -> None:
        self.apply_cache.clear(); self.restrict_cache.clear()

    def terminal_expression_ids(self, roots: list[int]) -> list[int]:
        seen: set[int] = set(); values: set[int] = set(); stack = list(roots)
        while stack:
            node_id = stack.pop()
            if node_id in seen: continue
            seen.add(node_id); node = self.nodes[node_id]
            if node[0] == "T": values.add(int(node[1]))
            else: stack.extend((int(node[2]), int(node[3])))
        return sorted(values)

    def compact_and_remap_terminals(self, roots: list[int], mapping: dict[int, int]) -> tuple["DecisionDiagram", list[int]]:
        new = DecisionDiagram([var for var, _ in sorted(self.rank.items(), key=lambda item: item[1])])
        memo: dict[int, int] = {}
        def clone(node_id: int) -> int:
            if node_id in memo: return memo[node_id]
            node = self.nodes[node_id]
            if node[0] == "T": out = new.terminal(mapping[int(node[1])])
            else: out = new.mk(int(node[1]), clone(int(node[2])), clone(int(node[3])))
            memo[node_id] = out; return out
        return new, [clone(root) for root in roots]


def _local_symbolic_factor(qubit: int, scope: tuple[int, ...], selector_parameter: dict[int, int], algebra: str, dag: ExpressionDAG, dd: DecisionDiagram) -> int:
    low_terminal = dag.terminal(_terminal_value(algebra, qubit, 0))
    high_terminal = dag.terminal(_terminal_value(algebra, qubit, 1))
    if qubit in selector_parameter:
        p = selector_parameter[qubit]
        even_expr = dag.parameter_choice(p, low_terminal, high_terminal)
        odd_expr = dag.parameter_choice(p, high_terminal, low_terminal)
    else:
        even_expr, odd_expr = low_terminal, high_terminal
    ordered_scope = sorted(scope, key=dd.rank.__getitem__); memo: dict[tuple[int, int], int] = {}
    def build(position: int, parity: int) -> int:
        key = (position, parity)
        if key in memo: return memo[key]
        if position == len(ordered_scope): out = dd.terminal(even_expr if parity == 0 else odd_expr)
        else:
            variable = ordered_scope[position]
            out = dd.mk(variable, build(position + 1, parity), build(position + 1, parity ^ 1))
        memo[key] = out; return out
    return build(0, 0)


def compile_algebra(context: dict[str, Any], algebra: str) -> dict[str, Any]:
    if algebra not in ALGEBRAS: raise ValueError(algebra)
    code = context["code"]; scopes = [tuple(scope) for scope in code["scopes"]]; order = list(context["order"])
    selector_parameter = {qubit: i for i, qubit in enumerate(code["selector_basis_qubits"])}
    dag = ExpressionDAG(); dd = DecisionDiagram(order)
    factors = [(scope, _local_symbolic_factor(qubit, scope, selector_parameter, algebra, dag, dd)) for qubit, scope in enumerate(scopes)]
    multiply = "MPMUL" if algebra == "min_plus_hamming" else "MUL"
    marginal = "MPMIN" if algebra == "min_plus_hamming" else "ADD"
    trace: list[dict[str, Any]] = []; peak_dd = len(dd.nodes); peak_expr = len(dag.nodes); started = time.time()
    for step, variable in enumerate(order):
        involved = [factor for factor in factors if variable in factor[0]]
        rest = [factor for factor in factors if variable not in factor[0]]
        if not involved: raise AssertionError(f"frozen elimination variable absent: {variable}")
        union = tuple(sorted(set().union(*(set(scope) for scope, _ in involved))))
        output_scope = tuple(item for item in union if item != variable)
        joint = involved[0][1]
        for _, root in involved[1:]: joint = dd.apply(multiply, joint, root, dag)
        output_root = dd.sum_out(joint, variable, marginal, dag)
        rest.append((output_scope, output_root)); factors = rest
        peak_dd = max(peak_dd, dd.peak_nodes); peak_expr = max(peak_expr, dag.peak_nodes)
        dd.clear_caches()
        active_roots = [root for _, root in factors]
        expr_ids = dd.terminal_expression_ids(active_roots)
        _, mapping = dag.compact(expr_ids)
        dd, active_roots = dd.compact_and_remap_terminals(active_roots, mapping)
        factors = [(scope, root) for (scope, _), root in zip(factors, active_roots)]
        trace.append({"step": step, "variable": variable, "involved_factor_count": len(involved), "union_arity": len(union), "output_arity": len(output_scope), "active_factor_count": len(factors), "retained_expression_nodes": len(dag.nodes), "retained_temporary_dd_nodes": len(dd.nodes)})
    final_root = factors[0][1]
    for scope, root in factors[1:]:
        if scope: raise AssertionError("non-scalar factor after frozen elimination")
        final_root = dd.apply(multiply, final_root, root, dag)
    node = dd.nodes[final_root]
    if node[0] != "T": raise AssertionError("compiled C90 result still depends on eliminated variables")
    expr_root = int(node[1]); [expr_root], _ = dag.compact([expr_root])
    receipt = dag.canonical_receipt(expr_root, algebra)
    receipt.update({"algebra": algebra, "representation": REPRESENTATION, "elapsed_seconds": time.time() - started, "expression_nodes_peak": peak_expr, "temporary_dd_nodes_peak": peak_dd, "intern_attempts": dag.created, "intern_reuses": dag.reused, "elimination_trace": trace})
    return {"algebra": algebra, "dag": dag, "root": expr_root, "receipt": receipt}


class CompiledC90:
    def __init__(self, context: dict[str, Any], compiled: dict[str, dict[str, Any]]) -> None:
        self.context = context; self.compiled = compiled

    def evaluate_algebra(self, algebra: str, selector_coordinate: int) -> Any:
        item = self.compiled[algebra]
        return item["dag"].evaluate(item["root"], selector_coordinate, algebra)

    def evaluate_class(self, *, selector_coordinate: int, functional_value: int, logical_class: int) -> dict[str, Any]:
        sum9 = self.evaluate_algebra("sum_product_bsc_p_0_1", selector_coordinate)
        sum2 = self.evaluate_algebra("soft_tropical_base_2", selector_coordinate)
        minimum = self.evaluate_algebra("min_plus_hamming", selector_coordinate)
        (minimum_weight, representative), canonical = minimum
        rows = self.context["selector_rows"]
        if Base.C72.selector_functional_value(representative, rows) != functional_value: raise AssertionError("minimum representative leaves requested selector class")
        if Base.C72.selector_functional_value(canonical, rows) != functional_value: raise AssertionError("canonical class key leaves requested selector class")
        return {"logical_class": int(logical_class), "selector_coordinate": int(selector_coordinate), "score_sum_product": int(sum9), "score_soft_tropical": int(sum2), "minimum_weight": int(minimum_weight), "minimum_representative": int(representative), "canonical_key": int(canonical)}

    def receipts(self) -> dict[str, Any]:
        return {algebra: self.compiled[algebra]["receipt"] for algebra in ALGEBRAS}


def compile_all(context: dict[str, Any] | None = None) -> CompiledC90:
    context = context or Base.load_c90_context()
    return CompiledC90(context, {algebra: compile_algebra(context, algebra) for algebra in ALGEBRAS})


def _freeze_json(value: Any) -> Any:
    if isinstance(value, list): return tuple(_freeze_json(item) for item in value)
    if isinstance(value, dict): return {key: _freeze_json(item) for key, item in value.items()}
    return value


def save_compiled(compiled: CompiledC90, path: Path) -> None:
    payload = {"schema_version": 1, "experiment_id": EXPERIMENT_ID, "source_commit": git_head(), "manifest_payload_sha256": MANIFEST_PAYLOAD, "representation": REPRESENTATION, "algebras": {algebra: {"root": int(compiled.compiled[algebra]["root"]), "nodes": compiled.compiled[algebra]["dag"].nodes, "receipt": compiled.compiled[algebra]["receipt"]} for algebra in ALGEBRAS}}
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=6) as handle:
        json.dump(payload, handle, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False); handle.write("\n")


def load_compiled(path: Path, context: dict[str, Any] | None = None) -> CompiledC90:
    with gzip.open(path, "rt", encoding="utf-8") as handle: payload = json.load(handle)
    if payload.get("schema_version") != 1 or payload.get("experiment_id") != EXPERIMENT_ID: raise ValueError("compiled C90 artifact identity drift")
    if payload.get("source_commit") != git_head(): raise ValueError("compiled C90 artifact is not bound to current HEAD")
    if payload.get("manifest_payload_sha256") != MANIFEST_PAYLOAD or payload.get("representation") != REPRESENTATION: raise ValueError("compiled C90 artifact contract drift")
    context = context or Base.load_c90_context(); out: dict[str, dict[str, Any]] = {}
    for algebra in ALGEBRAS:
        cell = payload.get("algebras", {}).get(algebra)
        if not isinstance(cell, dict): raise ValueError(f"compiled C90 algebra missing: {algebra}")
        dag = ExpressionDAG(); dag.nodes = [tuple(_freeze_json(node)) for node in cell["nodes"]]
        dag.interned = {node: index for index, node in enumerate(dag.nodes)}; dag.peak_nodes = len(dag.nodes)
        root = int(cell["root"]); receipt = cell["receipt"]; observed = dag.canonical_receipt(root, algebra)
        for key in ("canonical_node_stream_sha256", "root", "reachable_nodes", "node_kind_counts", "canonical_node_stream_bytes_excluding_header"):
            if observed.get(key) != receipt.get(key): raise ValueError(f"compiled C90 canonical receipt drift: {algebra}:{key}")
        out[algebra] = {"algebra": algebra, "dag": dag, "root": root, "receipt": receipt}
    return CompiledC90(context, out)


class NumericDD:
    """Independent exact numeric contraction for quality-blind selector controls."""
    def __init__(self, order: list[int], algebra: str) -> None:
        self.rank = {v: i for i, v in enumerate(order)}; self.algebra = algebra
        self.nodes: list[tuple[Any, ...]] = []; self.interned: dict[tuple[Any, ...], int] = {}
        self.cache: dict[tuple[str, int, int], int] = {}; self.rcache: dict[tuple[int, int, int], int] = {}

    def terminal(self, value: Any) -> int:
        key = ("T", value); found = self.interned.get(key)
        if found is not None: return found
        idx = len(self.nodes); self.nodes.append(key); self.interned[key] = idx; return idx

    def mk(self, var: int, low: int, high: int) -> int:
        if low == high: return low
        key = ("D", var, low, high); found = self.interned.get(key)
        if found is not None: return found
        idx = len(self.nodes); self.nodes.append(key); self.interned[key] = idx; return idx

    def apply(self, op: str, a: int, b: int) -> int:
        if a > b: a, b = b, a
        key = (op, a, b); found = self.cache.get(key)
        if found is not None: return found
        x, y = self.nodes[a], self.nodes[b]
        if x[0] == y[0] == "T":
            value = _multiply_value(self.algebra, x[1], y[1]) if op == "mul" else _marginal_value(self.algebra, x[1], y[1]); out = self.terminal(value)
        else:
            xv = None if x[0] == "T" else x[1]; yv = None if y[0] == "T" else y[1]
            top = yv if xv is None else xv if yv is None or self.rank[xv] <= self.rank[yv] else yv
            xl, xh = (x[2], x[3]) if xv == top else (a, a); yl, yh = (y[2], y[3]) if yv == top else (b, b)
            out = self.mk(top, self.apply(op, xl, yl), self.apply(op, xh, yh))
        self.cache[key] = out; return out

    def restrict(self, root: int, var: int, bit: int) -> int:
        key = (root, var, bit); found = self.rcache.get(key)
        if found is not None: return found
        node = self.nodes[root]
        if node[0] == "T": out = root
        elif node[1] == var: out = node[3] if bit else node[2]
        elif self.rank[node[1]] > self.rank[var]: out = root
        else: out = self.mk(node[1], self.restrict(node[2], var, bit), self.restrict(node[3], var, bit))
        self.rcache[key] = out; return out


def direct_contract_selector(context: dict[str, Any], algebra: str, coordinate: int) -> Any:
    code = context["code"]; order = list(context["order"]); dd = NumericDD(order, algebra)
    selector_parameter = {q: i for i, q in enumerate(code["selector_basis_qubits"])}; factors: list[tuple[tuple[int, ...], int]] = []
    for qubit, raw_scope in enumerate(code["scopes"]):
        scope = tuple(raw_scope); seed_bit = 1 if qubit in selector_parameter and coordinate & (1 << selector_parameter[qubit]) else 0
        ordered = sorted(scope, key=dd.rank.__getitem__); memo: dict[tuple[int, int], int] = {}
        def build(pos: int, parity: int) -> int:
            key = (pos, parity)
            if key in memo: return memo[key]
            if pos == len(ordered): out = dd.terminal(_terminal_value(algebra, qubit, parity ^ seed_bit))
            else: out = dd.mk(ordered[pos], build(pos + 1, parity), build(pos + 1, parity ^ 1))
            memo[key] = out; return out
        factors.append((scope, build(0, 0)))
    for var in order:
        involved = [f for f in factors if var in f[0]]; rest = [f for f in factors if var not in f[0]]
        joint = involved[0][1]
        for _, root in involved[1:]: joint = dd.apply("mul", joint, root)
        out = dd.apply("marg", dd.restrict(joint, var, 0), dd.restrict(joint, var, 1))
        union = tuple(sorted(set().union(*(set(s) for s, _ in involved)))); rest.append((tuple(x for x in union if x != var), out)); factors = rest
        dd.cache.clear(); dd.rcache.clear()
    root = factors[0][1]
    for _, other in factors[1:]: root = dd.apply("mul", root, other)
    node = dd.nodes[root]
    if node[0] != "T": raise AssertionError("numeric control did not contract to scalar")
    return node[1]


def validate_compiled(compiled: CompiledC90) -> dict[str, Any]:
    coordinates = Base.frozen_validation_coordinates(); context = compiled.context; rows: list[dict[str, Any]] = []
    for coordinate in coordinates:
        row: dict[str, Any] = {"selector_coordinate": coordinate, "algebras": {}}
        for algebra in ALGEBRAS:
            observed = compiled.evaluate_algebra(algebra, coordinate); expected = direct_contract_selector(context, algebra, coordinate)
            if observed != expected: raise AssertionError(f"C90 exact semantic mismatch: {algebra} selector={coordinate}")
            row["algebras"][algebra] = Base.digest({"value": observed})
        rows.append(row)
    return {"status": "C90_EXACT_SEMANTIC_VALIDATION_PASSED", "selector_count": len(coordinates), "validation_set_sha256": Base.digest(coordinates), "validation_outputs_sha256": Base.digest(rows), "all_exact_equal": True, "quality_exposed": False}
