from __future__ import annotations
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from qldpc_scale_001a_shared import *
from qldpc_scale_001a_math import scope_work

class SymbolicCompiler:
    def __init__(self, algebra: str, selector_basis: list[int]) -> None:
        self.algebra = algebra
        self.selector_parameter = {qubit: index for index, qubit in enumerate(selector_basis)}
        self.nodes: list[tuple[Any, ...]] = []
        self.interned: dict[tuple[Any, ...], int] = {}
        self.ledger: Counter[str] = Counter()

    def add(self, kind: str, count: int = 1) -> None:
        self.ledger[kind] += count

    def intern(self, node: tuple[Any, ...], commutative: bool = False) -> int:
        if commutative:
            operation, left, right = node
            self.add("EXACT_COMPARE")
            if left > right:
                left, right = right, left
            node = (operation, left, right)
        self.add("NODE_INTERN"); self.add("TABLE_READ")
        if node in self.interned:
            return self.interned[node]
        if len(self.nodes) >= RESOURCE_ENVELOPE["max_retained_canonical_structural_nodes_or_entries_per_algebra"]:
            raise ValueError("symbolic node resource cap exceeded")
        index = len(self.nodes)
        self.nodes.append(node); self.interned[node] = index; self.add("TABLE_WRITE")
        return index

    def terminal(self, qubit: int, bit: int) -> int:
        if self.algebra == "sum_product_bsc_p_0_1":
            value: Any = 9 if bit == 0 else 1
        elif self.algebra == "soft_tropical_base_2":
            value = 2 if bit == 0 else 1
        else:
            integer = (1 << qubit) if bit else 0
            value = ((bit, integer), integer)
        return self.intern(("T", value))

    def ite(self, parameter: int, low: int, high: int) -> int:
        return low if low == high else self.intern(("I", parameter, low, high))

    def binary(self, operation: str, left: int, right: int) -> int:
        return self.intern((operation, left, right), commutative=True)


def compile_symbolic_metadata(scopes: list[tuple[int, ...]], selector_basis: list[int], order: list[int], algebra: str) -> dict[str, Any]:
    compiler = SymbolicCompiler(algebra, selector_basis)
    factors: list[tuple[tuple[int, ...], list[int]]] = []
    local_entries = 0
    for qubit, scope in enumerate(scopes):
        table = []
        for assignment in range(1 << len(scope)):
            compiler.add("GF2_AND", len(scope))
            parity = assignment.bit_count() & 1
            low = compiler.terminal(qubit, parity)
            if qubit in compiler.selector_parameter:
                high = compiler.terminal(qubit, parity ^ 1)
                expression = compiler.ite(compiler.selector_parameter[qubit], low, high)
            else:
                expression = low
            table.append(expression); compiler.add("TABLE_WRITE"); local_entries += 1
        factors.append((scope, table))

    multiply = "MUL" if algebra != "min_plus_hamming" else "MPMUL"
    marginal = "ADD" if algebra != "min_plus_hamming" else "MPMIN"
    joint_total = 0; peak_joint = 0
    for variable in order:
        involved = [factor for factor in factors if variable in factor[0]]
        rest = [factor for factor in factors if variable not in factor[0]]
        union = tuple(sorted(set().union(*(set(scope) for scope, _ in involved))))
        output_scope = tuple(item for item in union if item != variable)
        joint_total += 1 << len(union); peak_joint = max(peak_joint, 1 << len(union))
        output: list[int] = []
        for output_assignment in range(1 << len(output_scope)):
            bits = {item: (output_assignment >> position) & 1 for position, item in enumerate(output_scope)}
            branches = []
            for variable_bit in (0, 1):
                bits[variable] = variable_bit
                expressions = []
                for scope, table in involved:
                    index = sum(bits[item] << position for position, item in enumerate(scope))
                    compiler.add("TABLE_READ"); expressions.append(table[index])
                result = expressions[0]
                for expression in expressions[1:]:
                    result = compiler.binary(multiply, result, expression)
                branches.append(result)
            output.append(compiler.binary(marginal, branches[0], branches[1])); compiler.add("TABLE_WRITE")
        rest.append((output_scope, output)); factors = rest
    root = factors[0][1][0]
    for _, table in factors[1:]:
        root = compiler.binary(multiply, root, table[0])

    hasher = hashlib.sha256(); serialized_bytes = 0
    header = json.dumps({"format": "QTR-QLDPC-SCALE-001A-DAG-v1", "algebra": algebra, "root": root}, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode() + b"\n"
    hasher.update(header); serialized_bytes += len(header)
    for node in compiler.nodes:
        encoded = json.dumps(node, separators=(",", ":"), ensure_ascii=True).encode() + b"\n"
        hasher.update(encoded); serialized_bytes += len(encoded)
    return {
        "algebra": algebra,
        "node_count": len(compiler.nodes),
        "node_kind_counts": dict(sorted(Counter(node[0] for node in compiler.nodes).items())),
        "compile_aop": {kind: compiler.ledger[kind] for kind in COMPILE_AOP_TYPES},
        "compile_aop_total": sum(compiler.ledger.values()),
        "local_factor_entries": local_entries,
        "elimination_joint_assignments": joint_total,
        "factor_table_entry_evaluations": local_entries + joint_total,
        "peak_joint_table_entries": peak_joint,
        "canonical_serialized_bytes": serialized_bytes,
        "canonical_sha256": hasher.hexdigest(),
    }


def frozen_validation_coordinates(selector_rank: int) -> list[int]:
    reserved = {0, (1 << selector_rank) - 1} | {1 << index for index in range(selector_rank)}
    random_values: list[int] = []
    seen = set(reserved)
    counter = 0
    while len(random_values) < RANDOM_VALIDATION_COUNT:
        block = hashlib.sha256(VALIDATION_SEED + counter.to_bytes(8, "big")).digest()
        coordinate = 0
        position = 0
        for byte in block:
            for shift in range(7, -1, -1):
                if position >= selector_rank:
                    break
                if (byte >> shift) & 1:
                    coordinate |= 1 << position
                position += 1
            if position >= selector_rank:
                break
        if coordinate not in seen:
            seen.add(coordinate); random_values.append(coordinate)
        counter += 1
    return [0] + [1 << index for index in range(selector_rank)] + [(1 << selector_rank) - 1] + random_values


def validation_work_counts(scopes: list[tuple[int, ...]], order: list[int], selector_count: int) -> dict[str, Any]:
    work = scope_work(scopes, order)
    per_selector_partition = {kind: 0 for kind in EXTENDED_VALIDATION_TYPES}
    per_selector_partition.update({"GF2_XOR": work["local_factor_gf2_xor_events"], "EXACT_INT_ADD": work["marginal_events"], "EXACT_INT_MUL": work["semiring_multiply_events"], "TABLE_READ": work["factor_table_reads"], "TABLE_WRITE": work["table_write_events"], "INDEX_PROJECT": work["index_project_events"]})
    per_selector_min = {kind: 0 for kind in EXTENDED_VALIDATION_TYPES}
    per_selector_min.update({"GF2_XOR": work["local_factor_gf2_xor_events"], "EXACT_INT_ADD": work["semiring_multiply_events"], "EXACT_COMPARE": 2 * work["marginal_events"], "TABLE_READ": work["factor_table_reads"], "TABLE_WRITE": work["table_write_events"], "INDEX_PROJECT": work["index_project_events"], "BITSET_OR": 2 * work["semiring_multiply_events"]})
    return {"per_selector_partition_algebra": per_selector_partition, "per_selector_min_plus": per_selector_min, "frozen_selector_count": selector_count, "aggregate_partition_algebra_per_300": {kind: count * selector_count for kind, count in per_selector_partition.items()}, "aggregate_min_plus_per_300": {kind: count * selector_count for kind, count in per_selector_min.items()}, "counts_are_abstract_exact_scalar_events_not_runtime_model": True}
