#!/usr/bin/env python3
"""TCM-QDEC-003: exact stabilizer-degeneracy variable-elimination audit."""

from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
T2_PATH = ROOT / "reference" / "tcm_qdec_002.py"
SPEC = importlib.util.spec_from_file_location("tcm_qdec_002_for_tcm3", T2_PATH)
T2 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(T2)

EVALUATOR_VERSION = "0.1.0"
PREDECESSOR_PAYLOAD = "efd9e76957421494897e2cc319137874b61093d66ea871f0202df3d07e6eb3c0"
PREDECESSOR_SCIENTIFIC_MERGE = "d3340c91df3aa72dc5c7ba75906128c8eef2e174"
PREDECESSOR_PROMOTION_MAIN = "693756a2569e87eb6cfeaf276ccc2bc2474cd92b"
PREDECESSOR_PROMOTION_RECORD = "QTR-TCM-QDEC-REVIEW-002-PROMOTION"

EXPECTED_SCORE_SHA = {
    "sum_product_bsc_p_0_1": "1b6bd71b9b05f169f57103ae71cd8b540f88e05dbe0302f2b4d9c2562a76a7be",
    "soft_tropical_base_2": "00c4b4c7612b6d05847963c4f8d432160cb2d6ec06fa4813700220461102bad5",
    "min_plus_hamming": "178a357cd13b2b9bbab03bad09f08efafecf37f2b59080bb3a6107e552e3b524",
}
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
EXPECTED_MAPPING_SHA = "0d907375404e37533a3dd182eccea7d6a3fd6637801745f8f5b39b7c4b683f8f"
EXPECTED_SCOPE_SHA = "9b9f68ff6cf22447892c6d853defa6daf5f08c5859ffd4352500d1e11b89052d"
EXPECTED_ORDER_AUDIT_SHA = "76e357c69d25f552d21a114c632a322256087b0fd1036d7ee914c02e39c7aff0"
EXPECTED_ORDER_TRACE_SHA = "898704d5fa4599dd4e11b1e85765046d0b6bb41ddfedaa3d4e329cf682dc6566"
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

PREDECESSOR = {
    "experiment_id": "TCM-QDEC-002",
    "registry_path": "registry/tcm-qdec-002.json",
    "evidence_path": "evidence/TCM-QDEC-002-report.json",
    "evidence_payload_sha256": PREDECESSOR_PAYLOAD,
    "scientific_merge_commit": PREDECESSOR_SCIENTIFIC_MERGE,
    "promotion_main_commit": PREDECESSOR_PROMOTION_MAIN,
    "promotion_record_path": "reviews/QTR-TCM-QDEC-REVIEW-002/promotion-record.json",
}

REPRESENTATION = {
    "kind": "exact_stabilizer_degeneracy_factor_elimination",
    "physical_variable_count": 18,
    "stabilizer_generator_count": 7,
    "stabilizer_basis_policy": "lexicographically_first_independent_physical_check_rows",
    "expected_stabilizer_basis_row_indices": [0, 1, 2, 3, 4, 5, 6],
    "selector_seed_basis_policy": "lexicographically_first_independent_combined_selector_columns",
    "expected_selector_seed_qubits": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "reachable_selector_count": 2048,
    "factor_scope_source": "selected_stabilizer_row_support_at_qubit",
    "elimination_order_audit": "exhaustive_all_7_factorial_orders",
    "frozen_elimination_order": [2, 4, 0, 1, 3, 5, 6],
    "primary_full_physical_state_enumeration": False,
    "predecessor_factorized_oracle_comparison_only": True,
}

SEMIRINGS = T2.SEMIRINGS

DECISION_RULE = {
    "winning_class": "exact_semiring_optimum",
    "class_tie_break": "lowest_canonical_stabilizer_coset_key",
    "representative_within_class": "lowest_hamming_weight_then_integer",
}

CLAIM_BOUNDARY = {
    "exact_degeneracy_factor_equivalence_only": True,
    "frozen_tcm_qdec_002_semantics_only": True,
    "bounded_exhaustive_order_audit_only": True,
    "primary_path_avoids_full_physical_state_enumeration": True,
    "bounded_width_family_claim": False,
    "scalable_tensor_contraction_claim": False,
    "asymptotic_or_practical_complexity_advantage_claim": False,
    "runtime_or_memory_superiority_claim": False,
    "larger_code_performance_claim": False,
    "general_qldpc_decoder_claim": False,
    "bp_osd_performance_claim": False,
    "circuit_level_noise_claim": False,
    "hardware_validation_claim": False,
    "threshold_claim": False,
    "learned_decoder_authorized": False,
    "adaptive_online_contraction_order_authorized": False,
    "tcm_qdec_004_authorized": False,
    "qldpc_forge_authorized": False,
    "autonomous_search_authorized": False,
}

digest = T2.digest
i2b = T2.i2b
syndrome = T2.syndrome


def keys(mapping: dict[str, Any], expected: set[str], where: str) -> None:
    if set(mapping) != expected:
        raise ValueError(
            f"{where} key mismatch: missing={sorted(expected-set(mapping))}, "
            f"extra={sorted(set(mapping)-expected)}"
        )


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_registry(path: Path) -> dict[str, Any]:
    data = load_json(path)
    keys(data, {"registry_version", "experiments"}, "registry")
    if data["registry_version"] != "0.1.0" or not isinstance(data["experiments"], list):
        raise ValueError("invalid TCM-QDEC-003 registry")
    matches = [x for x in data["experiments"] if x.get("experiment_id") == "TCM-QDEC-003"]
    if len(matches) != 1:
        raise ValueError("TCM-QDEC-003 must appear exactly once")
    e = matches[0]
    keys(
        e,
        {
            "experiment_id", "programme", "status", "predecessor", "representation",
            "semirings", "decision_rule", "claim_boundary",
        },
        "experiment",
    )
    if e["programme"] != "QTR" or e["status"] != "candidate_executable_not_promoted":
        raise ValueError("TCM-QDEC-003 identity/status changed")
    for name, observed, expected in (
        ("predecessor", e["predecessor"], PREDECESSOR),
        ("representation", e["representation"], REPRESENTATION),
        ("semirings", e["semirings"], SEMIRINGS),
        ("decision_rule", e["decision_rule"], DECISION_RULE),
        ("claim_boundary", e["claim_boundary"], CLAIM_BOUNDARY),
    ):
        if observed != expected:
            raise ValueError(f"{name} unexpectedly changed")
    return e


def gf2_rank(vectors: list[int]) -> int:
    basis: dict[int, int] = {}
    for original in vectors:
        value = original
        while value:
            pivot = value.bit_length() - 1
            if pivot in basis:
                value ^= basis[pivot]
            else:
                basis[pivot] = value
                break
    return len(basis)


def gf2_span(vectors: list[int]) -> set[int]:
    out = {0}
    independent: list[int] = []
    for vector in vectors:
        if gf2_rank(independent + [vector]) > len(independent):
            independent.append(vector)
            out |= {x ^ vector for x in tuple(out)}
    return out


def greedy_independent_indices(vectors: list[int], target_rank: int) -> list[int]:
    selected: list[int] = []
    basis: list[int] = []
    for index, vector in enumerate(vectors):
        if gf2_rank(basis + [vector]) > len(basis):
            selected.append(index)
            basis.append(vector)
            if len(selected) == target_rank:
                break
    if len(selected) != target_rank:
        raise ValueError("unable to recover requested independent basis")
    return selected


def combined_selector(error: int, rows: list[int], logical_z: list[int]) -> int:
    return syndrome(error, rows) | (T2.logical_label(error, logical_z) << len(rows))


def validate_predecessor(
    tcm2_registry: dict[str, Any],
    tcm2_evidence: dict[str, Any],
    tcm2_promotion: dict[str, Any],
    tcm1_registry: dict[str, Any],
    tcm1_evidence: dict[str, Any],
    tcm1_promotion: dict[str, Any],
    fixture1: dict[str, Any],
    fixture2: dict[str, Any],
    fixture2_promotion: dict[str, Any],
) -> tuple[list[int], set[int], int, list[int]]:
    keys(tcm2_registry, {"registry_version", "experiments"}, "TCM-QDEC-002 registry")
    if tcm2_registry["registry_version"] != "0.1.0" or not isinstance(tcm2_registry["experiments"], list):
        raise ValueError("TCM-QDEC-002 registry version/shape mismatch")
    matches = [x for x in tcm2_registry["experiments"] if x.get("experiment_id") == "TCM-QDEC-002"]
    if len(matches) != 1:
        raise ValueError("TCM-QDEC-002 registry identity mismatch")
    predecessor_experiment = matches[0]
    if predecessor_experiment.get("programme") != "QTR":
        raise ValueError("TCM-QDEC-002 programme changed")
    if predecessor_experiment.get("status") != "candidate_executable_not_promoted":
        raise ValueError("TCM-QDEC-002 immutable registry status changed")
    if predecessor_experiment.get("representation") != T2.REPRESENTATION:
        raise ValueError("TCM-QDEC-002 representation changed")
    if predecessor_experiment.get("semirings") != T2.SEMIRINGS:
        raise ValueError("TCM-QDEC-002 semirings changed")
    if predecessor_experiment.get("decision_rule") != T2.DECISION_RULE:
        raise ValueError("TCM-QDEC-002 decision rule changed")
    if predecessor_experiment.get("claim_boundary") != T2.CLAIM_BOUNDARY:
        raise ValueError("TCM-QDEC-002 claim boundary changed")

    if tcm2_evidence.get("experiment_id") != "TCM-QDEC-002":
        raise ValueError("TCM-QDEC-002 evidence identity mismatch")
    if tcm2_evidence.get("status") != "candidate_executable_not_promoted":
        raise ValueError("TCM-QDEC-002 immutable evidence status changed")
    if tcm2_evidence.get("payload_sha256") != PREDECESSOR_PAYLOAD:
        raise ValueError("TCM-QDEC-002 evidence payload mismatch")
    unsigned = dict(tcm2_evidence)
    unsigned.pop("payload_sha256", None)
    if digest(unsigned) != PREDECESSOR_PAYLOAD:
        raise ValueError("TCM-QDEC-002 evidence payload does not self-verify")
    if tcm2_evidence.get("claim_boundary") != T2.CLAIM_BOUNDARY:
        raise ValueError("TCM-QDEC-002 evidence claim boundary changed")
    contraction = tcm2_evidence.get("factorized_contraction", {})
    if contraction.get("canonical_class_mapping_sha256") != EXPECTED_MAPPING_SHA:
        raise ValueError("TCM-QDEC-002 canonical class mapping changed")
    if contraction.get("score_table_sha256") != EXPECTED_SCORE_SHA:
        raise ValueError("TCM-QDEC-002 score-table identities changed")
    if tcm2_evidence.get("winning_class_tie_sets_sha256") != EXPECTED_TIE_SHA:
        raise ValueError("TCM-QDEC-002 tie-set identities changed")
    for algebra, expected_sha in EXPECTED_DECISION_SHA.items():
        cell = tcm2_evidence.get("factorized_decisions", {}).get(algebra, {})
        if cell.get("decision_table_sha256") != expected_sha:
            raise ValueError(f"TCM-QDEC-002 decision identity changed: {algebra}")
        if cell.get("success_total") != EXPECTED_SUCCESS[algebra]:
            raise ValueError(f"TCM-QDEC-002 success total changed: {algebra}")
        env = tcm2_evidence.get("tie_sensitivity", {}).get(algebra, {}).get(
            "frozen_corpus_success_count_envelope_over_winning_class_ties"
        )
        expected_env = EXPECTED_TIE_ENVELOPES[algebra]
        if env != {"min": expected_env[0], "max": expected_env[1]}:
            raise ValueError(f"TCM-QDEC-002 tie envelope changed: {algebra}")

    if tcm2_promotion.get("record_id") != PREDECESSOR_PROMOTION_RECORD:
        raise ValueError("TCM-QDEC-002 promotion identity mismatch")
    if tcm2_promotion.get("status") != "referee_promoted_bounded":
        raise ValueError("TCM-QDEC-002 is not bounded promoted")
    if tcm2_promotion.get("scientific_merge_commit") != PREDECESSOR_SCIENTIFIC_MERGE:
        raise ValueError("TCM-QDEC-002 scientific merge mismatch")
    snapshot = tcm2_promotion.get("reviewed_snapshot", {})
    if (
        snapshot.get("evidence_payload_sha256") != PREDECESSOR_PAYLOAD
        or snapshot.get("snapshot_preserved_byte_for_byte") is not True
    ):
        raise ValueError("TCM-QDEC-002 reviewed snapshot mismatch")
    if "TCM-QDEC-003" not in tcm2_promotion.get("excluded_scope", []):
        raise ValueError("TCM-QDEC-002 downstream gate changed")

    rows, stabilizers, n, logical_z = T2.validate_predecessor(
        tcm1_registry, tcm1_evidence, tcm1_promotion,
        fixture1, fixture2, fixture2_promotion,
    )
    return rows, stabilizers, n, logical_z


def stabilizer_basis_and_scopes(
    rows: list[int], stabilizers: set[int], n: int
) -> tuple[list[int], list[int], list[tuple[int, ...]], str]:
    indices = greedy_independent_indices(rows, 7)
    if indices != REPRESENTATION["expected_stabilizer_basis_row_indices"]:
        raise AssertionError("unexpected stabilizer-basis row indices")
    basis_rows = [rows[index] for index in indices]
    recovered = gf2_span(basis_rows)
    if recovered != stabilizers or len(recovered) != 128:
        raise AssertionError("selected stabilizer basis does not recover promoted span")
    scopes = [
        tuple(variable for variable, row in enumerate(basis_rows) if row & (1 << qubit))
        for qubit in range(n)
    ]
    records = [
        {"qubit": qubit, "stabilizer_variables": list(scopes[qubit])}
        for qubit in range(n)
    ]
    scope_sha = digest(records)
    if scope_sha != EXPECTED_SCOPE_SHA:
        raise AssertionError("degeneracy factor-scope identity changed")
    return indices, basis_rows, scopes, scope_sha


def selector_seed_map(
    rows: list[int], logical_z: list[int], n: int
) -> tuple[list[int], dict[int, int]]:
    columns = T2.transfer_columns(rows, logical_z, n)
    target_rank = gf2_rank(rows + logical_z)
    basis_qubits = greedy_independent_indices(columns, target_rank)
    if basis_qubits != REPRESENTATION["expected_selector_seed_qubits"]:
        raise AssertionError("unexpected selector-seed basis")
    seed_map: dict[int, int] = {}
    for mask in range(1 << target_rank):
        selector = 0
        seed = 0
        for position, qubit in enumerate(basis_qubits):
            if mask & (1 << position):
                selector ^= columns[qubit]
                seed |= 1 << qubit
        if selector in seed_map:
            raise AssertionError("selector seed basis is not injective")
        seed_map[selector] = seed
    if len(seed_map) != REPRESENTATION["reachable_selector_count"]:
        raise AssertionError("unexpected reachable selector count")
    for selector, seed in seed_map.items():
        if combined_selector(seed, rows, logical_z) != selector:
            raise AssertionError("selector seed does not realize selector")
    return basis_qubits, seed_map


def order_metrics(
    order: tuple[int, ...], scopes: list[tuple[int, ...]]
) -> tuple[int, int, int, list[dict[str, Any]]]:
    factors = [set(scope) for scope in scopes if scope]
    peak_joint_arity = 0
    assignment_evaluations = 0
    output_entries_emitted = 0
    trace: list[dict[str, Any]] = []
    for variable in order:
        involved = [factor for factor in factors if variable in factor]
        if not involved:
            union: set[int] = {variable}
        else:
            union = set().union(*involved)
        output = union - {variable}
        peak_joint_arity = max(peak_joint_arity, len(union))
        assignment_evaluations += 1 << len(union)
        output_entries_emitted += 1 << len(output)
        factors = [factor for factor in factors if variable not in factor]
        if output:
            factors.append(output)
        trace.append(
            {
                "variable": variable,
                "joint_scope": sorted(union),
                "joint_arity": len(union),
                "output_scope": sorted(output),
                "output_arity": len(output),
                "assignment_evaluations": 1 << len(union),
            }
        )
    return peak_joint_arity, assignment_evaluations, output_entries_emitted, trace


def audit_orders(scopes: list[tuple[int, ...]]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    best_key: tuple[Any, ...] | None = None
    best_record: dict[str, Any] | None = None
    width_histogram: Counter[int] = Counter()
    for order in itertools.permutations(range(7)):
        peak, evaluations, output_entries, _ = order_metrics(order, scopes)
        induced_width = peak - 1
        width_histogram[induced_width] += 1
        record = {
            "order": list(order),
            "peak_joint_arity": peak,
            "induced_width": induced_width,
            "assignment_evaluations": evaluations,
            "output_entries_emitted": output_entries,
        }
        records.append(record)
        key = (induced_width, evaluations, output_entries, order)
        if best_key is None or key < best_key:
            best_key = key
            best_record = record
    assert best_record is not None
    minimum_width = best_record["induced_width"]
    optimal_count = sum(1 for record in records if record["induced_width"] == minimum_width)
    order = tuple(best_record["order"])
    peak, evaluations, output_entries, trace = order_metrics(order, scopes)
    audit_sha = digest(records)
    trace_sha = digest(trace)
    if audit_sha != EXPECTED_ORDER_AUDIT_SHA:
        raise AssertionError("elimination-order audit identity changed")
    if trace_sha != EXPECTED_ORDER_TRACE_SHA:
        raise AssertionError("frozen elimination-order trace changed")
    if list(order) != REPRESENTATION["frozen_elimination_order"]:
        raise AssertionError("lexicographically first optimal order changed")
    if (
        minimum_width != 4
        or optimal_count != 720
        or peak != 5
        or evaluations != 126
        or output_entries != 63
        or dict(sorted(width_histogram.items())) != {4: 720, 5: 4320}
    ):
        raise AssertionError("unexpected finite elimination-width geometry")
    return {
        "orders_checked": len(records),
        "induced_width_histogram": {str(k): v for k, v in sorted(width_histogram.items())},
        "minimum_induced_width": minimum_width,
        "optimal_order_count": optimal_count,
        "frozen_lexicographically_first_optimal_order": list(order),
        "peak_joint_arity": peak,
        "peak_joint_table_entries": 1 << peak,
        "maximum_output_factor_arity": peak - 1,
        "maximum_output_factor_entries": 1 << (peak - 1),
        "assignment_evaluations_per_class_contraction": evaluations,
        "output_factor_entries_emitted_per_class_contraction": output_entries,
        "order_audit_sha256": audit_sha,
        "frozen_order_trace_sha256": trace_sha,
    }


Factor = tuple[tuple[int, ...], dict[int, Any]]


def factor_index(scope: tuple[int, ...], bits: dict[int, int]) -> int:
    return sum(bits[variable] << position for position, variable in enumerate(scope))


def local_factor(seed: int, qubit: int, scope: tuple[int, ...], kind: str) -> Factor:
    table: dict[int, Any] = {}
    for assignment in range(1 << len(scope)):
        bit = (seed >> qubit) & 1
        for position in range(len(scope)):
            if assignment & (1 << position):
                bit ^= 1
        if kind == "sum9":
            value: Any = 9 if bit == 0 else 1
        elif kind == "sum2":
            value = 2 if bit == 0 else 1
        elif kind == "min_product":
            integer = (1 << qubit) if bit else 0
            value = ((bit, integer), integer)
        else:
            raise ValueError(f"unknown contraction kind: {kind}")
        table[assignment] = value
    return scope, table


def multiply_values(values: list[Any], kind: str) -> Any:
    if kind in {"sum9", "sum2"}:
        out = 1
        for value in values:
            out *= value
        return out
    weight = representative = canonical = 0
    for value in values:
        (dw, di), dc = value
        weight += dw
        representative += di
        canonical += dc
    return ((weight, representative), canonical)


def marginal_add(left: Any | None, right: Any, kind: str) -> Any:
    if left is None:
        return right
    if kind in {"sum9", "sum2"}:
        return left + right
    return (min(left[0], right[0]), min(left[1], right[1]))


def eliminate_variable(factors: list[Factor], variable: int, kind: str) -> list[Factor]:
    involved = [factor for factor in factors if variable in factor[0]]
    rest = [factor for factor in factors if variable not in factor[0]]
    if not involved:
        return rest
    union = tuple(sorted(set().union(*(set(scope) for scope, _ in involved))))
    output_scope = tuple(v for v in union if v != variable)
    output_table: dict[int, Any] = {}
    for output_assignment in range(1 << len(output_scope)):
        bits = {
            v: (output_assignment >> position) & 1
            for position, v in enumerate(output_scope)
        }
        aggregate: Any | None = None
        for variable_bit in (0, 1):
            bits[variable] = variable_bit
            values = [
                table[factor_index(scope, bits)]
                for scope, table in involved
            ]
            joint = multiply_values(values, kind)
            aggregate = marginal_add(aggregate, joint, kind)
        output_table[output_assignment] = aggregate
    rest.append((output_scope, output_table))
    return rest


def contract_class(
    seed: int, scopes: list[tuple[int, ...]], order: list[int], kind: str, n: int
) -> Any:
    factors = [local_factor(seed, qubit, scopes[qubit], kind) for qubit in range(n)]
    for variable in order:
        factors = eliminate_variable(factors, variable, kind)
    values = []
    for scope, table in factors:
        if scope:
            raise AssertionError("non-scalar factor remains after elimination")
        values.append(table[0])
    return multiply_values(values, kind)


def primary_tables(
    rows: list[int],
    stabilizers: set[int],
    n: int,
    logical_z: list[int],
    seed_map: dict[int, int],
    scopes: list[tuple[int, ...]],
    order_audit: dict[str, Any],
) -> tuple[
    dict[str, dict[int, int]],
    dict[str, dict[int, list[int]]],
    dict[str, Any],
]:
    order = order_audit["frozen_lexicographically_first_optimal_order"]
    scores: dict[str, dict[int, int]] = {
        "sum_product_bsc_p_0_1": {},
        "soft_tropical_base_2": {},
        "min_plus_hamming": {},
    }
    representatives: dict[int, int] = {}
    class_keys: dict[int, int] = {}

    for selector, seed in sorted(seed_map.items()):
        scores["sum_product_bsc_p_0_1"][selector] = contract_class(
            seed, scopes, order, "sum9", n
        )
        scores["soft_tropical_base_2"][selector] = contract_class(
            seed, scopes, order, "sum2", n
        )
        min_product = contract_class(seed, scopes, order, "min_product", n)
        (minimum_weight, representative), canonical_key = min_product
        scores["min_plus_hamming"][selector] = minimum_weight
        representatives[selector] = representative
        class_keys[selector] = canonical_key
        if combined_selector(representative, rows, logical_z) != selector:
            raise AssertionError("minimum representative left selector class")
        if combined_selector(canonical_key, rows, logical_z) != selector:
            raise AssertionError("canonical key left selector class")

    if len(set(class_keys.values())) != 2048:
        raise AssertionError("canonical keys do not distinguish all classes")

    syndrome_mask = (1 << len(rows)) - 1
    by_syndrome: dict[int, list[int]] = {}
    mapping_records: list[dict[str, Any]] = []
    for selector in sorted(seed_map):
        syn = selector & syndrome_mask
        by_syndrome.setdefault(syn, []).append(selector)
        mapping_records.append(
            {
                "selector": i2b(selector, len(rows) + len(logical_z)),
                "syndrome": i2b(syn, len(rows)),
                "logical_label": i2b(selector >> len(rows), len(logical_z)),
                "canonical_coset_key": i2b(class_keys[selector], n),
                "minimum_representative": i2b(representatives[selector], n),
                "minimum_weight": scores["min_plus_hamming"][selector],
            }
        )
    if len(by_syndrome) != 128 or set(map(len, by_syndrome.values())) != {16}:
        raise AssertionError("unexpected syndrome/logical class geometry")

    score_digests: dict[str, str] = {}
    for algebra in SEMIRINGS:
        records = [
            {
                "selector": i2b(selector, len(rows) + len(logical_z)),
                "score": scores[algebra][selector],
            }
            for selector in sorted(scores[algebra])
        ]
        score_digests[algebra] = digest(records)
    mapping_sha = digest(mapping_records)
    if mapping_sha != EXPECTED_MAPPING_SHA:
        raise AssertionError("degeneracy contraction class mapping changed")
    if score_digests != EXPECTED_SCORE_SHA:
        raise AssertionError("degeneracy contraction score identities changed")

    tables: dict[str, dict[int, int]] = {algebra: {} for algebra in SEMIRINGS}
    ties: dict[str, dict[int, list[int]]] = {algebra: {} for algebra in SEMIRINGS}
    tie_records: dict[str, list[dict[str, Any]]] = {algebra: [] for algebra in SEMIRINGS}
    for algebra in SEMIRINGS:
        maximize = SEMIRINGS[algebra]["score_direction"] == "maximize"
        for syn in sorted(by_syndrome):
            selectors = by_syndrome[syn]
            values = [scores[algebra][selector] for selector in selectors]
            best = max(values) if maximize else min(values)
            tied = [selector for selector in selectors if scores[algebra][selector] == best]
            tied.sort(key=lambda selector: class_keys[selector])
            tied_keys = [class_keys[selector] for selector in tied]
            ties[algebra][syn] = tied_keys
            tables[algebra][syn] = representatives[tied[0]]
            tie_records[algebra].append(
                {
                    "syndrome": i2b(syn, len(rows)),
                    "canonical_coset_keys": [i2b(key, n) for key in tied_keys],
                }
            )

    decision_digests: dict[str, str] = {}
    for algebra in SEMIRINGS:
        records = [
            {"syndrome": i2b(syn, len(rows)), "correction": i2b(correction, n)}
            for syn, correction in sorted(tables[algebra].items())
        ]
        decision_digests[algebra] = digest(records)
    tie_digests = {
        algebra: digest(tie_records[algebra]) for algebra in SEMIRINGS
    }
    if decision_digests != EXPECTED_DECISION_SHA:
        raise AssertionError("degeneracy contraction decision identities changed")
    if tie_digests != EXPECTED_TIE_SHA:
        raise AssertionError("degeneracy contraction tie identities changed")

    diagnostics = {
        "scores": scores,
        "representatives": representatives,
        "class_keys": class_keys,
        "canonical_class_mapping_sha256": mapping_sha,
        "score_table_sha256": score_digests,
        "decision_table_sha256": decision_digests,
        "winning_class_tie_sets_sha256": tie_digests,
    }
    return tables, ties, diagnostics


def compare_predecessor_oracle(
    rows: list[int],
    stabilizers: set[int],
    n: int,
    logical_z: list[int],
    tables: dict[str, dict[int, int]],
    ties: dict[str, dict[int, list[int]]],
    diagnostics: dict[str, Any],
) -> dict[str, Any]:
    columns = T2.transfer_columns(rows, logical_z, n)
    mass9 = T2.transfer_mass(columns, 9)
    mass2 = T2.transfer_mass(columns, 2)
    minimum = T2.transfer_minimum_representatives(columns)
    oracle_scores = {
        "sum_product_bsc_p_0_1": mass9,
        "soft_tropical_base_2": mass2,
        "min_plus_hamming": {selector: value[0] for selector, value in minimum.items()},
    }
    for algebra in SEMIRINGS:
        if diagnostics["scores"][algebra] != oracle_scores[algebra]:
            raise AssertionError(f"score table disagrees with TCM-QDEC-002: {algebra}")
    for selector, (weight, representative) in minimum.items():
        if diagnostics["representatives"][selector] != representative:
            raise AssertionError("minimum representative disagrees with TCM-QDEC-002")
        if diagnostics["scores"]["min_plus_hamming"][selector] != weight:
            raise AssertionError("minimum weight disagrees with TCM-QDEC-002")
        if diagnostics["class_keys"][selector] != T2.canonical_key(representative, stabilizers):
            raise AssertionError("canonical class key disagrees with TCM-QDEC-002")

    oracle_tables, oracle_ties, oracle_diagnostics = T2.factorized_tables(
        rows, stabilizers, n, logical_z
    )
    for algebra in SEMIRINGS:
        if tables[algebra] != oracle_tables[algebra]:
            raise AssertionError(f"decision table disagrees with TCM-QDEC-002: {algebra}")
        if ties[algebra] != oracle_ties[algebra]:
            raise AssertionError(f"winning-class ties disagree with TCM-QDEC-002: {algebra}")
    if oracle_diagnostics["canonical_class_mapping_sha256"] != EXPECTED_MAPPING_SHA:
        raise AssertionError("TCM-QDEC-002 mapping oracle changed")
    if oracle_diagnostics["score_table_sha256"] != EXPECTED_SCORE_SHA:
        raise AssertionError("TCM-QDEC-002 score oracle changed")
    return {
        "oracle_experiment_id": "TCM-QDEC-002",
        "oracle_primary_full_physical_state_enumeration": False,
        "score_entries_checked": len(SEMIRINGS) * 2048,
        "score_tables_exactly_equal": True,
        "class_mapping_entries_checked": 2048,
        "class_mapping_exactly_equal": True,
        "winning_class_tie_set_cells_checked": len(SEMIRINGS) * 128,
        "winning_class_tie_sets_exactly_equal": True,
        "decision_entries_checked": len(SEMIRINGS) * 128,
        "decision_tables_exactly_equal": True,
        "promoted_score_table_sha256": EXPECTED_SCORE_SHA,
        "promoted_canonical_class_mapping_sha256": EXPECTED_MAPPING_SHA,
        "promoted_decision_table_sha256": EXPECTED_DECISION_SHA,
        "promoted_success_totals": EXPECTED_SUCCESS,
        "promoted_tie_envelopes": EXPECTED_TIE_ENVELOPES,
    }


def evaluate(
    experiment: dict[str, Any],
    tcm2_registry: dict[str, Any],
    tcm2_evidence: dict[str, Any],
    tcm2_promotion: dict[str, Any],
    tcm1_registry: dict[str, Any],
    tcm1_evidence: dict[str, Any],
    tcm1_promotion: dict[str, Any],
    fixture1: dict[str, Any],
    fixture2: dict[str, Any],
    fixture2_promotion: dict[str, Any],
) -> dict[str, Any]:
    rows, stabilizers, n, logical_z = validate_predecessor(
        tcm2_registry, tcm2_evidence, tcm2_promotion,
        tcm1_registry, tcm1_evidence, tcm1_promotion,
        fixture1, fixture2, fixture2_promotion,
    )
    basis_indices, basis_rows, scopes, scope_sha = stabilizer_basis_and_scopes(
        rows, stabilizers, n
    )
    seed_basis, seed_map = selector_seed_map(rows, logical_z, n)
    order_audit = audit_orders(scopes)

    tables, ties, diagnostics = primary_tables(
        rows, stabilizers, n, logical_z, seed_map, scopes, order_audit
    )

    corpus = T2.T1.F2.make_corpus(n, 4)
    if len(corpus) != 4048:
        raise AssertionError("Fixture 002 corpus size changed")
    decision_results: dict[str, Any] = {}
    for algebra in SEMIRINGS:
        result, _ = T2.T1.classify(corpus, rows, stabilizers, tables[algebra])
        if result["success_total"] != EXPECTED_SUCCESS[algebra]:
            raise AssertionError(f"frozen-corpus success total changed: {algebra}")
        decision_results[algebra] = {
            **result,
            "decision_table_sha256": diagnostics["decision_table_sha256"][algebra],
        }

    tie_report = T2.factorized_tie_sensitivity(corpus, rows, stabilizers, ties)
    for algebra, expected in EXPECTED_TIE_ENVELOPES.items():
        envelope = tie_report[algebra][
            "frozen_corpus_success_count_envelope_over_winning_class_ties"
        ]
        if envelope != {"min": expected[0], "max": expected[1]}:
            raise AssertionError(f"frozen tie envelope changed: {algebra}")

    oracle = compare_predecessor_oracle(
        rows, stabilizers, n, logical_z, tables, ties, diagnostics
    )

    assignment_per_class = order_audit["assignment_evaluations_per_class_contraction"]
    class_contractions_total = 2048 * len(SEMIRINGS)
    assignment_total = assignment_per_class * class_contractions_total
    predecessor_transitions = 98298
    if assignment_total != 774144:
        raise AssertionError("unexpected degeneracy contraction assignment count")
    if assignment_total <= predecessor_transitions:
        raise AssertionError("arithmetic tradeoff unexpectedly disappeared")

    report: dict[str, Any] = {
        "experiment_id": "TCM-QDEC-003",
        "evaluator_version": EVALUATOR_VERSION,
        "status": "candidate_executable_not_promoted",
        "predecessor": experiment["predecessor"],
        "claim_boundary": experiment["claim_boundary"],
        "representation": experiment["representation"],
        "semirings": experiment["semirings"],
        "decision_rule": experiment["decision_rule"],
        "basis_geometry": {
            "stabilizer_basis_row_indices": basis_indices,
            "stabilizer_basis_rank": gf2_rank(basis_rows),
            "stabilizer_basis_span_size": len(gf2_span(basis_rows)),
            "stabilizer_basis_equals_promoted_span": gf2_span(basis_rows) == stabilizers,
            "selector_seed_basis_qubits": seed_basis,
            "selector_seed_basis_rank": gf2_rank(
                [T2.transfer_columns(rows, logical_z, n)[q] for q in seed_basis]
            ),
            "reachable_selector_count": len(seed_map),
            "factor_scope_size_histogram": {
                str(size): count
                for size, count in sorted(Counter(map(len, scopes)).items())
            },
            "maximum_initial_factor_arity": max(map(len, scopes)),
            "factor_scope_sha256": scope_sha,
        },
        "elimination_order_audit": order_audit,
        "degeneracy_contraction": {
            "primary_full_physical_state_enumeration": False,
            "class_score_entries_per_algebra": 2048,
            "class_contractions_per_algebra": 2048,
            "algebra_contractions": len(SEMIRINGS),
            "class_contractions_total": class_contractions_total,
            "assignment_evaluations_per_class_contraction": assignment_per_class,
            "assignment_evaluations_total": assignment_total,
            "predecessor_transition_relaxations_total": predecessor_transitions,
            "operation_count_tradeoff": {
                "tcm_qdec_003_assignment_evaluations": assignment_total,
                "tcm_qdec_002_transition_relaxations": predecessor_transitions,
                "reduced_ratio": [43008, 5461],
                "metrics_are_not_runtime_equivalent": True,
                "arithmetic_reduction_claim": False,
            },
            "canonical_class_mapping_sha256": diagnostics[
                "canonical_class_mapping_sha256"
            ],
            "score_table_sha256": diagnostics["score_table_sha256"],
        },
        "degeneracy_decisions": decision_results,
        "winning_class_tie_sets_sha256": diagnostics[
            "winning_class_tie_sets_sha256"
        ],
        "tie_sensitivity": tie_report,
        "predecessor_equivalence": oracle,
    }
    report["payload_sha256"] = digest(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default=str(ROOT / "registry" / "tcm-qdec-003.json"))
    parser.add_argument("--tcm-002-registry", default=str(ROOT / "registry" / "tcm-qdec-002.json"))
    parser.add_argument("--tcm-002-evidence", default=str(ROOT / "evidence" / "TCM-QDEC-002-report.json"))
    parser.add_argument(
        "--tcm-002-promotion",
        default=str(ROOT / "reviews" / "QTR-TCM-QDEC-REVIEW-002" / "promotion-record.json"),
    )
    parser.add_argument("--tcm-001-registry", default=str(ROOT / "registry" / "tcm-qdec.json"))
    parser.add_argument("--tcm-001-evidence", default=str(ROOT / "evidence" / "TCM-QDEC-001-report.json"))
    parser.add_argument(
        "--tcm-001-promotion",
        default=str(ROOT / "reviews" / "QTR-TCM-QDEC-REVIEW-001" / "promotion-record.json"),
    )
    parser.add_argument("--fixture-001", default=str(ROOT / "evidence" / "QLDPC-FIXTURE-001-report.json"))
    parser.add_argument("--fixture-002", default=str(ROOT / "evidence" / "QLDPC-FIXTURE-002-report.json"))
    parser.add_argument(
        "--fixture-002-promotion",
        default=str(ROOT / "reviews" / "QTR-QLDPC-REVIEW-002" / "promotion-record.json"),
    )
    parser.add_argument("--output")
    args = parser.parse_args()
    report = evaluate(
        load_registry(Path(args.registry)),
        load_json(Path(args.tcm_002_registry)),
        load_json(Path(args.tcm_002_evidence)),
        load_json(Path(args.tcm_002_promotion)),
        load_json(Path(args.tcm_001_registry)),
        load_json(Path(args.tcm_001_evidence)),
        load_json(Path(args.tcm_001_promotion)),
        load_json(Path(args.fixture_001)),
        load_json(Path(args.fixture_002)),
        load_json(Path(args.fixture_002_promotion)),
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
