#!/usr/bin/env python3
"""TCM-QDEC-004: exact selector-parametric shared compilation audit.

The primary path symbolically eliminates the seven promoted stabilizer-degeneracy
variables while retaining the eleven promoted selector coordinates as explicit
parameters.  It compiles a canonical hash-consed exact expression DAG for each
algebra, then reuses that DAG across all 2048 selector evaluations.

The compiled DAG is structural: it contains parameter-choice and semiring
operation nodes, not a table of the 2048 evaluated selector answers.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVALUATOR_VERSION = "0.1.0"

PREDECESSOR_PAYLOAD = "f0ecdae04f3da4f0508454da59ce406a4e6c461f88f1784279cb6d7e360b595f"
PREDECESSOR_SCIENTIFIC_MERGE = "2925a41343c8e4592c1bf558d86ea461e0e1c7d4"
PREDECESSOR_PROMOTION_MAIN = "4524be6fd51eb78b627e4303cd713b5c215fc7a8"
PREDECESSOR_PROMOTION_RECORD = "QTR-TCM-QDEC-REVIEW-003-PROMOTION"
PREDECESSOR_REVIEWED_HEAD = "968029c156a3d668a0adc9adce850b62cd249671"

EXPECTED_SCOPE_SHA = "9b9f68ff6cf22447892c6d853defa6daf5f08c5859ffd4352500d1e11b89052d"
EXPECTED_SCORE_SHA = {
    "sum_product_bsc_p_0_1": "1b6bd71b9b05f169f57103ae71cd8b540f88e05dbe0302f2b4d9c2562a76a7be",
    "soft_tropical_base_2": "00c4b4c7612b6d05847963c4f8d432160cb2d6ec06fa4813700220461102bad5",
    "min_plus_hamming": "178a357cd13b2b9bbab03bad09f08efafecf37f2b59080bb3a6107e552e3b524",
}
EXPECTED_MAPPING_SHA = "0d907375404e37533a3dd182eccea7d6a3fd6637801745f8f5b39b7c4b683f8f"
EXPECTED_DECISION_SHA = {
    "sum_product_bsc_p_0_1": "05dd32573ee965ce96caf707de3541f8be74b49317ad46b7929ef7dcf3bf64fc",
    "soft_tropical_base_2": "ea2a96e3878758cd2daebd28673d943c27740a3e1c3579d8429a8a658e567393",
    "min_plus_hamming": "88a9a766b64c7e476ac5bb4da877a2b1f6d4e88cee88cde6ea7461cc74179f3f",
}
EXPECTED_TIE_SHA = {
    "sum_product_bsc_p_0_1": "3778c019c7e235d916fa27616f83a9f8251a8c2a0276e09e0ea6dc1a6125cd60",
    "soft_tropical_base_2": "bf4297273ca05b1506bde6f5305464e5affdf78ba31b40e20a0fada3e26dd982",
    "min_plus_hamming": "1991fe00aaec2f8ce1163ca7b4192054002a2ef176d4839d6883c01f4e724007",
}
EXPECTED_SUCCESS = {
    "sum_product_bsc_p_0_1": 263,
    "soft_tropical_base_2": 262,
    "min_plus_hamming": 226,
}
EXPECTED_TIE_ENVELOPES = {
    "sum_product_bsc_p_0_1": [263, 263],
    "soft_tropical_base_2": [262, 262],
    "min_plus_hamming": [218, 263],
}
EXPECTED_ORDER = [2, 4, 0, 1, 3, 5, 6]
EXPECTED_STABILIZER_BASIS = [0, 1, 2, 3, 4, 5, 6]
EXPECTED_SELECTOR_BASIS = list(range(11))

PREDECESSOR = {
    "experiment_id": "TCM-QDEC-003",
    "registry_path": "registry/tcm-qdec-003.json",
    "evidence_path": "evidence/TCM-QDEC-003-report.json",
    "evidence_payload_sha256": PREDECESSOR_PAYLOAD,
    "reviewed_head": PREDECESSOR_REVIEWED_HEAD,
    "scientific_merge_commit": PREDECESSOR_SCIENTIFIC_MERGE,
    "promotion_main_commit": PREDECESSOR_PROMOTION_MAIN,
    "promotion_record_path": "reviews/QTR-TCM-QDEC-REVIEW-003/promotion-record.json",
}

SEMIRINGS = {
    "min_plus_hamming": {
        "interpretation": "minimum Hamming-weight tropical score",
        "kind": "min_plus",
        "local_bit_costs": [0, 1],
        "score_direction": "minimize",
    },
    "soft_tropical_base_2": {
        "interpretation": "exact partition score equivalent in ranking to beta=ln(2) soft-min",
        "kind": "soft_tropical",
        "local_bit_weights": [2, 1],
        "score_direction": "maximize",
    },
    "sum_product_bsc_p_0_1": {
        "interpretation": "exact numerator proportional to BSC p=0.1 likelihood",
        "kind": "sum_product",
        "local_bit_weights": [9, 1],
        "score_direction": "maximize",
    },
}

DECISION_RULE = {
    "winning_class": "exact_semiring_optimum",
    "class_tie_break": "lowest_canonical_stabilizer_coset_key",
    "representative_within_class": "lowest_hamming_weight_then_integer",
}

AOP_TYPES = [
    "GF2_XOR",
    "GF2_AND",
    "EXACT_INT_ADD",
    "EXACT_INT_MUL",
    "EXACT_COMPARE",
    "TABLE_READ",
    "TABLE_WRITE",
    "NODE_INTERN",
]

REPRESENTATION = {
    "kind": "exact_selector_parametric_hash_consed_expression_dag",
    "physical_variable_count": 18,
    "stabilizer_generator_count": 7,
    "selector_parameter_count": 11,
    "reachable_selector_count": 2048,
    "stabilizer_basis_row_indices": EXPECTED_STABILIZER_BASIS,
    "selector_seed_basis_qubits": EXPECTED_SELECTOR_BASIS,
    "frozen_degeneracy_elimination_order": EXPECTED_ORDER,
    "compile_policy": "symbolically_eliminate_z_keep_a_explicit",
    "parameter_interface": "eleven_boolean_selector_coordinates",
    "canonicalization": "hash_cons_exact_expression_nodes_with_commutative_binary_operand_order",
    "anti_cache_rule": "complete_selector_answer_tables_are_not_admissible_primary_compiled_objects",
    "primary_full_selector_enumeration_during_compilation": False,
    "primary_full_physical_state_enumeration": False,
    "operation_taxonomy": AOP_TYPES,
}

CLAIM_BOUNDARY = {
    "exact_shared_compilation_on_fixed_fixture_only": True,
    "exact_predecessor_semantics_required": True,
    "selector_answer_cache_primary_object_allowed": False,
    "abstract_operation_reduction_claim_only": True,
    "runtime_superiority_claim": False,
    "memory_superiority_claim": False,
    "asymptotic_complexity_claim": False,
    "bounded_width_family_claim": False,
    "larger_code_authorized": False,
    "multi_size_scaling_authorized": False,
    "bp_min_sum_bp_osd_comparison_authorized": False,
    "circuit_level_noise_authorized": False,
    "repeated_syndrome_authorized": False,
    "learned_decoder_authorized": False,
    "adaptive_online_contraction_order_authorized": False,
    "qldpc_forge_authorized": False,
    "autonomous_search_authorized": False,
}

SOURCE_LOGICAL_Z = [
    ["L0", "L2", "L3", "L4", "L8", "R0"],
    ["L0", "L2", "L4", "L5", "L6", "L7"],
    ["L1", "L2", "L7", "R1"],
    ["L0", "L1", "L6", "R0"],
]


def digest(payload: Any) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def i2b(value: int, width: int) -> str:
    return "".join("1" if value & (1 << index) else "0" for index in range(width))


def exact_keys(mapping: dict[str, Any], expected: set[str], where: str) -> None:
    if set(mapping) != expected:
        raise ValueError(f"{where} key mismatch")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_registry(path: Path) -> dict[str, Any]:
    data = load_json(path)
    exact_keys(data, {"registry_version", "experiments"}, "registry")
    if data["registry_version"] != "0.1.0" or not isinstance(data["experiments"], list):
        raise ValueError("invalid TCM-QDEC-004 registry")
    matches = [x for x in data["experiments"] if x.get("experiment_id") == "TCM-QDEC-004"]
    if len(matches) != 1:
        raise ValueError("TCM-QDEC-004 must appear exactly once")
    experiment = matches[0]
    expected = {
        "experiment_id", "programme", "status", "predecessor", "representation",
        "semirings", "decision_rule", "claim_boundary",
    }
    exact_keys(experiment, expected, "experiment")
    if experiment["programme"] != "QTR" or experiment["status"] != "candidate_executable_not_promoted":
        raise ValueError("TCM-QDEC-004 identity/status changed")
    for name, observed, wanted in (
        ("predecessor", experiment["predecessor"], PREDECESSOR),
        ("representation", experiment["representation"], REPRESENTATION),
        ("semirings", experiment["semirings"], SEMIRINGS),
        ("decision_rule", experiment["decision_rule"], DECISION_RULE),
        ("claim_boundary", experiment["claim_boundary"], CLAIM_BOUNDARY),
    ):
        if observed != wanted:
            raise ValueError(f"{name} unexpectedly changed")
    return experiment


def validate_predecessor(
    tcm3_registry: dict[str, Any], tcm3_evidence: dict[str, Any], tcm3_promotion: dict[str, Any]
) -> None:
    matches = [x for x in tcm3_registry.get("experiments", []) if x.get("experiment_id") == "TCM-QDEC-003"]
    if len(matches) != 1 or matches[0].get("status") != "candidate_executable_not_promoted":
        raise ValueError("TCM-QDEC-003 immutable registry identity changed")
    if tcm3_evidence.get("experiment_id") != "TCM-QDEC-003":
        raise ValueError("TCM-QDEC-003 evidence identity changed")
    if tcm3_evidence.get("status") != "candidate_executable_not_promoted":
        raise ValueError("TCM-QDEC-003 evidence status changed")
    if tcm3_evidence.get("payload_sha256") != PREDECESSOR_PAYLOAD:
        raise ValueError("TCM-QDEC-003 payload changed")
    unsigned = dict(tcm3_evidence)
    unsigned.pop("payload_sha256", None)
    if digest(unsigned) != PREDECESSOR_PAYLOAD:
        raise ValueError("TCM-QDEC-003 payload fails self-verification")
    geometry = tcm3_evidence.get("basis_geometry", {})
    if geometry.get("stabilizer_basis_row_indices") != EXPECTED_STABILIZER_BASIS:
        raise ValueError("TCM-QDEC-003 stabilizer basis changed")
    if geometry.get("selector_seed_basis_qubits") != EXPECTED_SELECTOR_BASIS:
        raise ValueError("TCM-QDEC-003 selector basis changed")
    if geometry.get("factor_scope_sha256") != EXPECTED_SCOPE_SHA:
        raise ValueError("TCM-QDEC-003 factor scopes changed")
    audit = tcm3_evidence.get("elimination_order_audit", {})
    if audit.get("frozen_lexicographically_first_optimal_order") != EXPECTED_ORDER:
        raise ValueError("TCM-QDEC-003 elimination order changed")
    contraction = tcm3_evidence.get("degeneracy_contraction", {})
    if contraction.get("score_table_sha256") != EXPECTED_SCORE_SHA:
        raise ValueError("TCM-QDEC-003 score identities changed")
    if contraction.get("canonical_class_mapping_sha256") != EXPECTED_MAPPING_SHA:
        raise ValueError("TCM-QDEC-003 mapping identity changed")
    if tcm3_evidence.get("winning_class_tie_sets_sha256") != EXPECTED_TIE_SHA:
        raise ValueError("TCM-QDEC-003 tie identities changed")
    for algebra, expected in EXPECTED_DECISION_SHA.items():
        cell = tcm3_evidence.get("degeneracy_decisions", {}).get(algebra, {})
        if cell.get("decision_table_sha256") != expected or cell.get("success_total") != EXPECTED_SUCCESS[algebra]:
            raise ValueError(f"TCM-QDEC-003 decision identity changed: {algebra}")
    if tcm3_promotion.get("record_id") != PREDECESSOR_PROMOTION_RECORD:
        raise ValueError("TCM-QDEC-003 promotion identity changed")
    if tcm3_promotion.get("status") != "referee_promoted_bounded":
        raise ValueError("TCM-QDEC-003 is not bounded promoted")
    if tcm3_promotion.get("reviewed_head") != PREDECESSOR_REVIEWED_HEAD:
        raise ValueError("TCM-QDEC-003 reviewed head changed")
    if tcm3_promotion.get("scientific_merge_commit") != PREDECESSOR_SCIENTIFIC_MERGE:
        raise ValueError("TCM-QDEC-003 scientific merge changed")
    snapshot = tcm3_promotion.get("reviewed_snapshot", {})
    if snapshot.get("evidence_payload_sha256") != PREDECESSOR_PAYLOAD or snapshot.get("snapshot_preserved_byte_for_byte") is not True:
        raise ValueError("TCM-QDEC-003 reviewed snapshot changed")
    if "TCM-QDEC-004" not in tcm3_promotion.get("excluded_scope", []):
        raise ValueError("TCM-QDEC-003 downstream gate changed")


def identity(n: int) -> list[list[int]]:
    return [[int(i == j) for j in range(n)] for i in range(n)]


def cyclic_shift(n: int) -> list[list[int]]:
    return [[int(j == (i + 1) % n) for j in range(n)] for i in range(n)]


def transpose(matrix: list[list[int]]) -> list[list[int]]:
    return [list(column) for column in zip(*matrix)]


def matmul_mod2(left: list[list[int]], right: list[list[int]]) -> list[list[int]]:
    right_t = transpose(right)
    return [[sum(a * b for a, b in zip(row, col)) % 2 for col in right_t] for row in left]


def matrix_add_mod2(*matrices: list[list[int]]) -> list[list[int]]:
    return [[sum(matrix[i][j] for matrix in matrices) % 2 for j in range(len(matrices[0][0]))] for i in range(len(matrices[0]))]


def matrix_power_mod2(matrix: list[list[int]], exponent: int) -> list[list[int]]:
    result = identity(len(matrix))
    base = matrix
    while exponent:
        if exponent & 1:
            result = matmul_mod2(result, base)
        base = matmul_mod2(base, base)
        exponent >>= 1
    return result


def kron(left: list[list[int]], right: list[list[int]]) -> list[list[int]]:
    return [[left[i][j] * right[r][c] for j in range(len(left[0])) for c in range(len(right[0]))] for i in range(len(left)) for r in range(len(right))]


def row_to_int(row: list[int]) -> int:
    return sum(bit << index for index, bit in enumerate(row))


def parse_operator(labels: list[str]) -> int:
    value = 0
    for label in labels:
        local = int(label[1:])
        index = local if label[0] == "L" else 9 + local
        value |= 1 << index
    return value


def construct_code() -> tuple[list[int], list[int]]:
    x = kron(cyclic_shift(3), identity(3))
    y = kron(identity(3), cyclic_shift(3))
    A = matrix_add_mod2(matrix_power_mod2(x, 1), matrix_power_mod2(y, 0), matrix_power_mod2(y, 2))
    B = matrix_add_mod2(matrix_power_mod2(y, 1), matrix_power_mod2(x, 0), matrix_power_mod2(x, 2))
    rows = [row_to_int(left + right) for left, right in zip(A, B)]
    logical_z = [parse_operator(labels) for labels in SOURCE_LOGICAL_Z]
    return rows, logical_z


def syndrome(error: int, rows: list[int]) -> int:
    return sum((((error & row).bit_count() & 1) << index) for index, row in enumerate(rows))


def logical_label(error: int, logical_z: list[int]) -> int:
    return sum((((error & op).bit_count() & 1) << index) for index, op in enumerate(logical_z))


def combined_selector(error: int, rows: list[int], logical_z: list[int]) -> int:
    return syndrome(error, rows) | (logical_label(error, logical_z) << len(rows))


def gf2_span(vectors: list[int]) -> set[int]:
    out = {0}
    for vector in vectors:
        out |= {value ^ vector for value in tuple(out)}
    return out


class Ledger:
    def __init__(self) -> None:
        self.counts: Counter[str] = Counter()

    def add(self, kind: str, count: int = 1) -> None:
        if kind not in AOP_TYPES:
            raise ValueError(f"unknown AOP type: {kind}")
        self.counts[kind] += count

    def vector(self) -> dict[str, int]:
        return {kind: self.counts[kind] for kind in AOP_TYPES}

    def total(self) -> int:
        return sum(self.counts.values())


class ExpressionDAG:
    def __init__(self, ledger: Ledger) -> None:
        self.ledger = ledger
        self.nodes: list[tuple[Any, ...]] = []
        self.interned: dict[tuple[Any, ...], int] = {}
        self.peak_nodes = 0

    def _intern(self, node: tuple[Any, ...]) -> int:
        if node[0] in {"MUL", "ADD", "MPMUL", "MPMIN"}:
            op, left, right = node
            self.ledger.add("EXACT_COMPARE")
            if left > right:
                left, right = right, left
            node = (op, left, right)
        self.ledger.add("NODE_INTERN")
        self.ledger.add("TABLE_READ")
        if node in self.interned:
            return self.interned[node]
        index = len(self.nodes)
        self.nodes.append(node)
        self.interned[node] = index
        self.ledger.add("TABLE_WRITE")
        self.peak_nodes = max(self.peak_nodes, len(self.nodes))
        return index

    def terminal(self, value: Any) -> int:
        return self._intern(("T", repr(value), value))

    def parameter_choice(self, parameter: int, low: int, high: int) -> int:
        if low == high:
            return low
        return self._intern(("ITE", parameter, low, high))

    def binary(self, operation: str, left: int, right: int) -> int:
        return self._intern((operation, left, right))

    def evaluate(self, root: int, selector_coordinate: int, ledger: Ledger) -> tuple[Any, int]:
        memo: dict[int, Any] = {}

        def visit(node_id: int) -> Any:
            ledger.add("TABLE_READ")
            if node_id in memo:
                return memo[node_id]
            ledger.add("TABLE_READ")
            node = self.nodes[node_id]
            kind = node[0]
            if kind == "T":
                value = node[2]
            elif kind == "ITE":
                ledger.add("GF2_AND")
                branch = node[3] if selector_coordinate & (1 << node[1]) else node[2]
                value = visit(branch)
            else:
                left = visit(node[1])
                right = visit(node[2])
                if kind == "MUL":
                    ledger.add("EXACT_INT_MUL")
                    value = left * right
                elif kind == "ADD":
                    ledger.add("EXACT_INT_ADD")
                    value = left + right
                elif kind == "MPMUL":
                    ledger.add("EXACT_INT_ADD", 3)
                    value = (
                        (left[0][0] + right[0][0], left[0][1] + right[0][1]),
                        left[1] + right[1],
                    )
                elif kind == "MPMIN":
                    ledger.add("EXACT_COMPARE", 2)
                    value = (min(left[0], right[0]), min(left[1], right[1]))
                else:
                    raise AssertionError(f"unknown expression node: {kind}")
            memo[node_id] = value
            ledger.add("TABLE_WRITE")
            return value

        return visit(root), len(memo)

    def canonical_object(self, root: int) -> dict[str, Any]:
        seen: set[int] = set()
        order: list[int] = []

        def visit(node_id: int) -> None:
            if node_id in seen:
                return
            node = self.nodes[node_id]
            if node[0] == "ITE":
                visit(node[2])
                visit(node[3])
            elif node[0] in {"MUL", "ADD", "MPMUL", "MPMIN"}:
                visit(node[1])
                visit(node[2])
            seen.add(node_id)
            order.append(node_id)

        visit(root)
        remap = {old: new for new, old in enumerate(order)}
        records: list[dict[str, Any]] = []
        for old in order:
            node = self.nodes[old]
            if node[0] == "T":
                records.append({"kind": "terminal", "value": node[2]})
            elif node[0] == "ITE":
                records.append({
                    "kind": "parameter_choice",
                    "parameter": node[1],
                    "low": remap[node[2]],
                    "high": remap[node[3]],
                })
            else:
                records.append({
                    "kind": "binary",
                    "operation": node[0],
                    "left": remap[node[1]],
                    "right": remap[node[2]],
                })
        return {"root": remap[root], "nodes": records}


def terminal_value(kind: str, qubit: int, bit: int) -> Any:
    if kind == "sum9":
        return 9 if bit == 0 else 1
    if kind == "sum2":
        return 2 if bit == 0 else 1
    integer = (1 << qubit) if bit else 0
    return ((bit, integer), integer)


def compile_symbolic(kind: str, scopes: list[tuple[int, ...]]) -> tuple[ExpressionDAG, int, dict[str, Any]]:
    ledger = Ledger()
    dag = ExpressionDAG(ledger)
    factors: list[tuple[tuple[int, ...], list[int]]] = []

    for qubit, scope in enumerate(scopes):
        table: list[int] = []
        for assignment in range(1 << len(scope)):
            ledger.add("GF2_AND", len(scope))
            parity = assignment.bit_count() & 1
            low = dag.terminal(terminal_value(kind, qubit, parity))
            if qubit < 11:
                high = dag.terminal(terminal_value(kind, qubit, parity ^ 1))
                expression = dag.parameter_choice(qubit, low, high)
            else:
                expression = low
            table.append(expression)
            ledger.add("TABLE_WRITE")
        factors.append((scope, table))

    def combine(expressions: list[int]) -> int:
        operation = "MUL" if kind in {"sum9", "sum2"} else "MPMUL"
        result = expressions[0]
        for expression in expressions[1:]:
            result = dag.binary(operation, result, expression)
        return result

    def marginal(left: int, right: int) -> int:
        operation = "ADD" if kind in {"sum9", "sum2"} else "MPMIN"
        return dag.binary(operation, left, right)

    trace: list[dict[str, Any]] = []
    for variable in EXPECTED_ORDER:
        involved = [factor for factor in factors if variable in factor[0]]
        rest = [factor for factor in factors if variable not in factor[0]]
        union = tuple(sorted(set().union(*(set(scope) for scope, _ in involved))))
        output_scope = tuple(item for item in union if item != variable)
        output: list[int] = []
        for output_assignment in range(1 << len(output_scope)):
            bits = {item: (output_assignment >> position) & 1 for position, item in enumerate(output_scope)}
            branches: list[int] = []
            for variable_bit in (0, 1):
                bits[variable] = variable_bit
                expressions: list[int] = []
                for scope, table in involved:
                    index = sum(bits[item] << position for position, item in enumerate(scope))
                    ledger.add("TABLE_READ")
                    expressions.append(table[index])
                branches.append(combine(expressions))
            output.append(marginal(branches[0], branches[1]))
            ledger.add("TABLE_WRITE")
        rest.append((output_scope, output))
        factors = rest
        trace.append({"variable": variable, "unique_nodes": len(dag.nodes), "factor_count": len(factors)})

    root = combine([table[0] for scope, table in factors])
    compiled = dag.canonical_object(root)
    encoded = json.dumps(compiled, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    metadata = {
        "canonical_sha256": digest(compiled),
        "canonical_serialized_bytes": len(encoded),
        "retained_reachable_nodes": len(compiled["nodes"]),
        "unique_nodes_created": len(dag.nodes),
        "peak_nodes_during_compilation": dag.peak_nodes,
        "node_intern_attempts": ledger.counts["NODE_INTERN"],
        "hash_cons_reuses": ledger.counts["NODE_INTERN"] - len(dag.nodes),
        "compile_aop": ledger.vector(),
        "compile_aop_total": ledger.total(),
        "elimination_trace": trace,
    }
    return dag, root, metadata


def multiply_plain(values: list[Any], kind: str, ledger: Ledger) -> Any:
    if kind in {"sum9", "sum2"}:
        result = 1
        for value in values:
            ledger.add("EXACT_INT_MUL")
            result *= value
        return result
    weight = representative = canonical = 0
    for (delta, integer), key in values:
        ledger.add("EXACT_INT_ADD", 3)
        weight += delta
        representative += integer
        canonical += key
    return ((weight, representative), canonical)


def marginal_plain(left: Any, right: Any, kind: str, ledger: Ledger) -> Any:
    if kind in {"sum9", "sum2"}:
        ledger.add("EXACT_INT_ADD")
        return left + right
    ledger.add("EXACT_COMPARE", 2)
    return (min(left[0], right[0]), min(left[1], right[1]))


def classwise_contract(seed: int, scopes: list[tuple[int, ...]], kind: str, ledger: Ledger) -> Any:
    factors: list[tuple[tuple[int, ...], list[Any]]] = []
    for qubit, scope in enumerate(scopes):
        table: list[Any] = []
        for assignment in range(1 << len(scope)):
            ledger.add("GF2_AND")
            bit = (seed >> qubit) & 1
            for position in range(len(scope)):
                ledger.add("GF2_AND")
                if assignment & (1 << position):
                    ledger.add("GF2_XOR")
                    bit ^= 1
            table.append(terminal_value(kind, qubit, bit))
            ledger.add("TABLE_WRITE")
        factors.append((scope, table))

    for variable in EXPECTED_ORDER:
        involved = [factor for factor in factors if variable in factor[0]]
        rest = [factor for factor in factors if variable not in factor[0]]
        union = tuple(sorted(set().union(*(set(scope) for scope, _ in involved))))
        output_scope = tuple(item for item in union if item != variable)
        output: list[Any] = []
        for output_assignment in range(1 << len(output_scope)):
            bits = {item: (output_assignment >> position) & 1 for position, item in enumerate(output_scope)}
            aggregate: Any | None = None
            for variable_bit in (0, 1):
                bits[variable] = variable_bit
                values: list[Any] = []
                for scope, table in involved:
                    index = sum(bits[item] << position for position, item in enumerate(scope))
                    ledger.add("TABLE_READ")
                    values.append(table[index])
                joint = multiply_plain(values, kind, ledger)
                aggregate = joint if aggregate is None else marginal_plain(aggregate, joint, kind, ledger)
            output.append(aggregate)
            ledger.add("TABLE_WRITE")
        rest.append((output_scope, output))
        factors = rest

    values: list[Any] = []
    for scope, table in factors:
        if scope:
            raise AssertionError("non-scalar factor remains")
        ledger.add("TABLE_READ")
        values.append(table[0])
    return multiply_plain(values, kind, ledger)


def selector_from_coordinate(coordinate: int, selector_columns: list[int], ledger: Ledger) -> int:
    selector = 0
    for qubit in EXPECTED_SELECTOR_BASIS:
        ledger.add("GF2_AND")
        if coordinate & (1 << qubit):
            ledger.add("GF2_XOR")
            selector ^= selector_columns[qubit]
    return selector


def make_corpus(n: int = 18, maximum_weight: int = 4) -> list[int]:
    corpus: list[int] = []
    for weight in range(maximum_weight + 1):
        for support in itertools.combinations(range(n), weight):
            corpus.append(sum(1 << index for index in support))
    return corpus


def classify(corpus: list[int], rows: list[int], stabilizers: set[int], table: dict[int, int]) -> dict[str, Any]:
    success_by_weight: Counter[int] = Counter()
    nonzero = wrong = 0
    for error in corpus:
        correction = table[syndrome(error, rows)]
        residual = error ^ correction
        if syndrome(residual, rows) != 0:
            nonzero += 1
        elif residual in stabilizers:
            success_by_weight[error.bit_count()] += 1
        else:
            wrong += 1
    success = sum(success_by_weight.values())
    return {
        "success_total": success,
        "failure_total": len(corpus) - success,
        "success_by_error_weight": {str(weight): success_by_weight[weight] for weight in range(5)},
        "failure_modes": {
            "nonzero_residual_syndrome": nonzero,
            "zero_syndrome_wrong_logical_coset": wrong,
        },
    }


def semantic_products(
    values: dict[str, dict[int, int]], representatives: dict[int, int], class_keys: dict[int, int],
    rows: list[int], logical_z: list[int], stabilizers: set[int],
) -> tuple[dict[str, Any], dict[str, dict[int, int]], dict[str, dict[int, list[tuple[int, int]]]]]:
    mapping_records: list[dict[str, Any]] = []
    for selector in sorted(values["min_plus_hamming"]):
        syn = selector & ((1 << len(rows)) - 1)
        mapping_records.append({
            "selector": i2b(selector, len(rows) + len(logical_z)),
            "syndrome": i2b(syn, len(rows)),
            "logical_label": i2b(selector >> len(rows), len(logical_z)),
            "canonical_coset_key": i2b(class_keys[selector], 18),
            "minimum_representative": i2b(representatives[selector], 18),
            "minimum_weight": values["min_plus_hamming"][selector],
        })
    mapping_sha = digest(mapping_records)
    if mapping_sha != EXPECTED_MAPPING_SHA:
        raise AssertionError("compiled mapping identity changed")

    score_sha: dict[str, str] = {}
    for algebra in SEMIRINGS:
        records = [{"selector": i2b(selector, 13), "score": values[algebra][selector]} for selector in sorted(values[algebra])]
        score_sha[algebra] = digest(records)
    if score_sha != EXPECTED_SCORE_SHA:
        raise AssertionError("compiled score identities changed")

    by_syndrome: dict[int, list[int]] = {}
    for selector in sorted(values["min_plus_hamming"]):
        by_syndrome.setdefault(selector & 511, []).append(selector)
    if len(by_syndrome) != 128 or set(map(len, by_syndrome.values())) != {16}:
        raise AssertionError("selector geometry changed")

    tables: dict[str, dict[int, int]] = {algebra: {} for algebra in SEMIRINGS}
    ties: dict[str, dict[int, list[tuple[int, int]]]] = {algebra: {} for algebra in SEMIRINGS}
    tie_sha: dict[str, str] = {}
    decision_sha: dict[str, str] = {}
    for algebra in SEMIRINGS:
        tie_records: list[dict[str, Any]] = []
        maximize = SEMIRINGS[algebra]["score_direction"] == "maximize"
        for syn, selectors in sorted(by_syndrome.items()):
            scores = [values[algebra][selector] for selector in selectors]
            best = max(scores) if maximize else min(scores)
            tied = [selector for selector in selectors if values[algebra][selector] == best]
            tied.sort(key=lambda item: class_keys[item])
            choices = [(class_keys[item], representatives[item]) for item in tied]
            ties[algebra][syn] = choices
            tables[algebra][syn] = choices[0][1]
            tie_records.append({
                "syndrome": i2b(syn, 9),
                "canonical_coset_keys": [i2b(key, 18) for key, _ in choices],
            })
        tie_sha[algebra] = digest(tie_records)
        decision_records = [{"syndrome": i2b(syn, 9), "correction": i2b(correction, 18)} for syn, correction in sorted(tables[algebra].items())]
        decision_sha[algebra] = digest(decision_records)
    if tie_sha != EXPECTED_TIE_SHA or decision_sha != EXPECTED_DECISION_SHA:
        raise AssertionError("compiled tie/decision identity changed")

    corpus = make_corpus()
    decisions: dict[str, Any] = {}
    tie_report: dict[str, Any] = {}
    by_corpus_syndrome: dict[int, list[int]] = {}
    for error in corpus:
        by_corpus_syndrome.setdefault(syndrome(error, rows), []).append(error)

    for algebra in SEMIRINGS:
        result = classify(corpus, rows, stabilizers, tables[algebra])
        if result["success_total"] != EXPECTED_SUCCESS[algebra]:
            raise AssertionError(f"success total changed: {algebra}")
        decisions[algebra] = {**result, "decision_table_sha256": decision_sha[algebra]}
        histogram = Counter(len(choices) for choices in ties[algebra].values())
        minimum = maximum = 0
        for syn, choices in ties[algebra].items():
            errors = by_corpus_syndrome.get(syn, [])
            successes = [sum((error ^ correction) in stabilizers for error in errors) for _, correction in choices]
            minimum += min(successes)
            maximum += max(successes)
        expected = EXPECTED_TIE_ENVELOPES[algebra]
        if [minimum, maximum] != expected:
            raise AssertionError(f"tie envelope changed: {algebra}")
        tie_report[algebra] = {
            "winning_class_count_histogram": {str(key): value for key, value in sorted(histogram.items())},
            "frozen_corpus_success_count_envelope_over_winning_class_ties": {"min": minimum, "max": maximum},
            "default_lowest_key_success_count": result["success_total"],
            "success_count_invariant_under_winning_class_tie_break": minimum == maximum,
        }

    semantic = {
        "score_entries_checked": 6144,
        "score_tables_exactly_equal": True,
        "class_mapping_entries_checked": 2048,
        "class_mapping_exactly_equal": True,
        "winning_class_tie_set_cells_checked": 384,
        "winning_class_tie_sets_exactly_equal": True,
        "decision_entries_checked": 384,
        "decision_tables_exactly_equal": True,
        "score_table_sha256": score_sha,
        "canonical_class_mapping_sha256": mapping_sha,
        "winning_class_tie_sets_sha256": tie_sha,
        "decision_table_sha256": decision_sha,
        "frozen_corpus_success_totals": EXPECTED_SUCCESS,
        "tie_envelopes": EXPECTED_TIE_ENVELOPES,
    }
    return {"equivalence": semantic, "decisions": decisions, "tie_sensitivity": tie_report}, tables, ties


def add_vectors(vectors: list[dict[str, int]]) -> dict[str, int]:
    return {kind: sum(vector[kind] for vector in vectors) for kind in AOP_TYPES}


def evaluate_core(experiment: dict[str, Any]) -> dict[str, Any]:
    rows, logical_z = construct_code()
    basis_rows = [rows[index] for index in EXPECTED_STABILIZER_BASIS]
    stabilizers = gf2_span(basis_rows)
    if len(stabilizers) != 128:
        raise AssertionError("stabilizer basis span changed")
    scopes = [tuple(variable for variable, row in enumerate(basis_rows) if row & (1 << qubit)) for qubit in range(18)]
    scope_records = [{"qubit": qubit, "stabilizer_variables": list(scopes[qubit])} for qubit in range(18)]
    scope_sha = digest(scope_records)
    if scope_sha != EXPECTED_SCOPE_SHA:
        raise AssertionError("factor scope identity changed")
    selector_columns = [combined_selector(1 << qubit, rows, logical_z) for qubit in range(18)]
    seed_selectors: set[int] = set()
    for coordinate in range(2048):
        selector = 0
        for qubit in EXPECTED_SELECTOR_BASIS:
            if coordinate & (1 << qubit):
                selector ^= selector_columns[qubit]
        seed_selectors.add(selector)
    if len(seed_selectors) != 2048:
        raise AssertionError("selector basis lost rank")

    kind_by_algebra = {
        "sum_product_bsc_p_0_1": "sum9",
        "soft_tropical_base_2": "sum2",
        "min_plus_hamming": "min",
    }
    compiled_metadata: dict[str, Any] = {}
    values: dict[str, dict[int, int]] = {algebra: {} for algebra in SEMIRINGS}
    representatives: dict[int, int] = {}
    class_keys: dict[int, int] = {}
    evaluation_cost: dict[str, Any] = {}
    baseline_cost: dict[str, Any] = {}

    for algebra in SEMIRINGS:
        kind = kind_by_algebra[algebra]
        dag, root, metadata = compile_symbolic(kind, scopes)
        compiled_metadata[algebra] = metadata
        evaluation_ledger = Ledger()
        evaluation_totals: list[int] = []
        visited_counts: list[int] = []
        for coordinate in range(2048):
            local_ledger = Ledger()
            result, visited = dag.evaluate(root, coordinate, local_ledger)
            selector = selector_from_coordinate(coordinate, selector_columns, local_ledger)
            for aop, count in local_ledger.counts.items():
                evaluation_ledger.add(aop, count)
            evaluation_totals.append(local_ledger.total())
            visited_counts.append(visited)
            if kind == "min":
                (minimum_weight, representative), canonical = result
                values[algebra][selector] = minimum_weight
                representatives[selector] = representative
                class_keys[selector] = canonical
            else:
                values[algebra][selector] = result

        evaluation_cost[algebra] = {
            "aop": evaluation_ledger.vector(),
            "aop_total": evaluation_ledger.total(),
            "per_selector_aop_min": min(evaluation_totals),
            "per_selector_aop_max": max(evaluation_totals),
            "per_selector_aop_mean_numerator": sum(evaluation_totals),
            "per_selector_aop_mean_denominator": len(evaluation_totals),
            "visited_compiled_nodes_per_selector_min": min(visited_counts),
            "visited_compiled_nodes_per_selector_max": max(visited_counts),
        }

        baseline_ledger = Ledger()
        for coordinate in range(2048):
            replay = classwise_contract(coordinate, scopes, kind, baseline_ledger)
            selector = selector_from_coordinate(coordinate, selector_columns, baseline_ledger)
            if kind == "min":
                (weight, representative), canonical = replay
                if (
                    weight != values[algebra][selector]
                    or representative != representatives[selector]
                    or canonical != class_keys[selector]
                ):
                    raise AssertionError("compiled path disagrees with classwise TCM-QDEC-003 replay")
            elif replay != values[algebra][selector]:
                raise AssertionError("compiled path disagrees with classwise TCM-QDEC-003 replay")
        baseline_cost[algebra] = {"aop": baseline_ledger.vector(), "aop_total": baseline_ledger.total()}

    semantic, _, _ = semantic_products(values, representatives, class_keys, rows, logical_z, stabilizers)

    compile_vectors = [compiled_metadata[algebra]["compile_aop"] for algebra in SEMIRINGS]
    eval_vectors = [evaluation_cost[algebra]["aop"] for algebra in SEMIRINGS]
    baseline_vectors = [baseline_cost[algebra]["aop"] for algebra in SEMIRINGS]
    compile_vector = add_vectors(compile_vectors)
    eval_vector = add_vectors(eval_vectors)
    baseline_vector = add_vectors(baseline_vectors)
    compile_total = sum(compile_vector.values())
    eval_total = sum(eval_vector.values())
    baseline_total = sum(baseline_vector.values())
    one_shot = compile_total + eval_total
    reduction = baseline_total - one_shot
    if reduction <= 0:
        outcome = "EXACT_SHARED_COMPILATION_NO_COST_REDUCTION"
        break_even = None
    else:
        outcome = "EXACT_SHARED_COMPILATION_WITH_REDUCED_DUPLICATION"
        denominator = baseline_total - eval_total
        break_even = (compile_total + denominator - 1) // denominator

    report: dict[str, Any] = {
        "experiment_id": "TCM-QDEC-004",
        "evaluator_version": EVALUATOR_VERSION,
        "status": "candidate_executable_not_promoted",
        "predecessor": experiment["predecessor"],
        "claim_boundary": experiment["claim_boundary"],
        "representation": experiment["representation"],
        "semirings": experiment["semirings"],
        "decision_rule": experiment["decision_rule"],
        "basis_geometry": {
            "stabilizer_basis_row_indices": EXPECTED_STABILIZER_BASIS,
            "stabilizer_span_size": len(stabilizers),
            "selector_seed_basis_qubits": EXPECTED_SELECTOR_BASIS,
            "reachable_selector_count": len(seed_selectors),
            "factor_scope_size_histogram": {str(size): count for size, count in sorted(Counter(map(len, scopes)).items())},
            "factor_scope_sha256": scope_sha,
            "frozen_degeneracy_elimination_order": EXPECTED_ORDER,
        },
        "compiled_structure": {
            "primary_object_is_complete_answer_cache": False,
            "selector_values_materialized_during_compilation": 0,
            "selector_parameters_enter_only_through_parameter_choice_nodes": True,
            "per_algebra": compiled_metadata,
            "retained_reachable_nodes_total": sum(compiled_metadata[a]["retained_reachable_nodes"] for a in SEMIRINGS),
            "canonical_serialized_bytes_total": sum(compiled_metadata[a]["canonical_serialized_bytes"] for a in SEMIRINGS),
        },
        "semantic_equivalence": semantic["equivalence"],
        "compiled_decisions": semantic["decisions"],
        "tie_sensitivity": semantic["tie_sensitivity"],
        "cost_accounting": {
            "aop_types": AOP_TYPES,
            "aop_total_is_runtime_model": False,
            "runtime_or_memory_superiority_inferred": False,
            "compile": {"aop": compile_vector, "aop_total": compile_total},
            "evaluate_all_2048_selectors": {"aop": eval_vector, "aop_total": eval_total, "per_algebra": evaluation_cost},
            "one_shot": {"aop_total": one_shot},
            "tcm_qdec_003_reinstrumented_classwise_replay": {
                "aop": baseline_vector,
                "aop_total": baseline_total,
                "per_algebra": baseline_cost,
                "original_assignment_evaluations_preserved": 774144,
                "original_predecessor_transition_relaxations_preserved": 98298,
                "original_counters_not_translated_to_aop": True,
            },
            "one_shot_aop_reduction": reduction,
            "compiled_one_shot_uses_fewer_aops": reduction > 0,
            "repeated_complete_sweep_formula": "C_compile + k*C_eval_all versus k*C_003_all",
            "break_even_complete_sweeps": break_even,
        },
        "adjudication": {
            "outcome": outcome,
            "exact_semantics_preserved": True,
            "nontrivial_shared_structural_object": True,
            "complete_answer_cache_disallowed_and_not_used": True,
            "abstract_operation_reduction_observed": reduction > 0,
            "runtime_superiority_claim": False,
            "memory_superiority_claim": False,
            "downstream_authority_created": False,
        },
    }
    report["payload_sha256"] = digest(report)
    return report


def evaluate(
    experiment: dict[str, Any],
    tcm3_registry: dict[str, Any],
    tcm3_evidence: dict[str, Any],
    tcm3_promotion: dict[str, Any],
) -> dict[str, Any]:
    validate_predecessor(tcm3_registry, tcm3_evidence, tcm3_promotion)
    return evaluate_core(experiment)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default=str(ROOT / "registry" / "tcm-qdec-004.json"))
    parser.add_argument("--tcm-003-registry", default=str(ROOT / "registry" / "tcm-qdec-003.json"))
    parser.add_argument("--tcm-003-evidence", default=str(ROOT / "evidence" / "TCM-QDEC-003-report.json"))
    parser.add_argument("--tcm-003-promotion", default=str(ROOT / "reviews" / "QTR-TCM-QDEC-REVIEW-003" / "promotion-record.json"))
    parser.add_argument("--output", default=str(ROOT / "evidence" / "TCM-QDEC-004-report.json"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    experiment = load_registry(Path(args.registry))
    report = evaluate(
        experiment,
        load_json(Path(args.tcm_003_registry)),
        load_json(Path(args.tcm_003_evidence)),
        load_json(Path(args.tcm_003_promotion)),
    )
    output = Path(args.output)
    if args.check:
        if load_json(output) != report:
            raise SystemExit("committed TCM-QDEC-004 evidence does not exactly replay")
    else:
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
