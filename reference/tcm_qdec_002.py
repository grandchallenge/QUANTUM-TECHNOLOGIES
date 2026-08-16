#!/usr/bin/env python3
"""TCM-QDEC-002: exact factorized contraction equivalence audit."""

from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
T1_PATH = ROOT / "reference" / "tcm_qdec_001.py"
SPEC = importlib.util.spec_from_file_location("tcm_qdec_001_for_tcm2", T1_PATH)
T1 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(T1)

EVALUATOR_VERSION = "0.1.0"
PREDECESSOR_PAYLOAD = "1b19addcda5e04cf78a834b2162fe0873ed5eb15f3330995d8354906944b7122"
PREDECESSOR_SCIENTIFIC_MERGE = "41524f805dce4f0c7b64b8e743b75a60b4f76773"
PREDECESSOR_PROMOTION_MAIN = "be022e3d1dd8490fd3856414908c6cdcb8b06ea4"
PREDECESSOR_PROMOTION_RECORD = "QTR-TCM-QDEC-REVIEW-001-PROMOTION"

PROMOTED_DECISION_SHA = {
    "sum_product_bsc_p_0_1": "05dd32573ee965ce96caf707de3541f8be74b49317ad46b7929ef7dcf3bf64fc",
    "soft_tropical_base_2": "ea2a96e3878758cd2daebd28673d943c27740a3e1c3579d8429a8a658e567393",
    "min_plus_hamming": "88a9a766b64c7e476ac5bb4da877a2b1f6d4e88cee88cde6ea7461cc74179f3f",
}
PROMOTED_SUCCESS = {
    "sum_product_bsc_p_0_1": 263,
    "soft_tropical_base_2": 262,
    "min_plus_hamming": 226,
}
PROMOTED_TIE_ENVELOPES = {
    "sum_product_bsc_p_0_1": [263, 263],
    "soft_tropical_base_2": [262, 262],
    "min_plus_hamming": [218, 263],
}

SEMIRINGS = {
    "sum_product_bsc_p_0_1": {
        "kind": "sum_product",
        "score_direction": "maximize",
        "local_bit_weights": [9, 1],
        "interpretation": "exact numerator proportional to BSC p=0.1 likelihood",
    },
    "soft_tropical_base_2": {
        "kind": "soft_tropical",
        "score_direction": "maximize",
        "local_bit_weights": [2, 1],
        "interpretation": "exact partition score equivalent in ranking to beta=ln(2) soft-min",
    },
    "min_plus_hamming": {
        "kind": "min_plus",
        "score_direction": "minimize",
        "local_bit_costs": [0, 1],
        "interpretation": "minimum Hamming-weight tropical score",
    },
}

REPRESENTATION = {
    "kind": "exact_column_transfer_factorization",
    "physical_variable_count": 18,
    "syndrome_selector_bits": 9,
    "independent_syndrome_rank": 7,
    "logical_selector_bits": 4,
    "combined_selector_bits": 13,
    "combined_constraint_rank": 11,
    "local_column_signature": "syndrome_column_concat_logical_Z_pairing_column",
    "qubit_contraction_order": list(range(18)),
    "factorized_path_full_physical_state_enumeration": False,
    "oracle_comparison_full_state_enumeration": True,
}

DECISION_RULE = {
    "winning_class": "exact_semiring_optimum",
    "class_tie_break": "lowest_canonical_stabilizer_coset_key",
    "representative_within_class": "lowest_hamming_weight_then_integer",
}

CLAIM_BOUNDARY = {
    "exact_factorized_equivalence_only": True,
    "frozen_tcm_qdec_001_semantics_only": True,
    "primary_factorized_path_avoids_full_physical_state_enumeration": True,
    "oracle_full_enumeration_verification_only": True,
    "scalable_tensor_contraction_claim": False,
    "asymptotic_or_practical_complexity_advantage_claim": False,
    "larger_code_performance_claim": False,
    "general_qldpc_decoder_claim": False,
    "bp_osd_performance_claim": False,
    "circuit_level_noise_claim": False,
    "hardware_validation_claim": False,
    "threshold_claim": False,
    "portable_latency_or_memory_claim": False,
    "learned_decoder_authorized": False,
    "adaptive_contraction_order_authorized": False,
    "tcm_qdec_003_authorized": False,
    "qldpc_forge_authorized": False,
    "autonomous_search_authorized": False,
}

EXPECTED_PREDECESSOR = {
    "experiment_id": "TCM-QDEC-001",
    "registry_path": "registry/tcm-qdec.json",
    "evidence_path": "evidence/TCM-QDEC-001-report.json",
    "evidence_payload_sha256": PREDECESSOR_PAYLOAD,
    "scientific_merge_commit": PREDECESSOR_SCIENTIFIC_MERGE,
    "promotion_main_commit": PREDECESSOR_PROMOTION_MAIN,
    "promotion_record_path": "reviews/QTR-TCM-QDEC-REVIEW-001/promotion-record.json",
}

digest = T1.digest
syndrome = T1.syndrome
i2b = T1.i2b


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
        raise ValueError("invalid TCM-QDEC-002 registry")
    matches = [x for x in data["experiments"] if x.get("experiment_id") == "TCM-QDEC-002"]
    if len(matches) != 1:
        raise ValueError("TCM-QDEC-002 must appear exactly once")
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
        raise ValueError("TCM-QDEC-002 identity/status changed")
    for name, observed, expected in (
        ("predecessor", e["predecessor"], EXPECTED_PREDECESSOR),
        ("representation", e["representation"], REPRESENTATION),
        ("semirings", e["semirings"], SEMIRINGS),
        ("decision_rule", e["decision_rule"], DECISION_RULE),
        ("claim_boundary", e["claim_boundary"], CLAIM_BOUNDARY),
    ):
        if observed != expected:
            raise ValueError(f"{name} unexpectedly changed")
    return e


def little_bitstring_to_int(bits: str) -> int:
    value = 0
    for index, bit in enumerate(bits):
        if bit not in "01":
            raise ValueError("non-binary bitstring")
        if bit == "1":
            value |= 1 << index
    return value


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


def logical_label(error: int, logical_z: list[int]) -> int:
    out = 0
    for index, z in enumerate(logical_z):
        out |= (((error & z).bit_count() & 1) << index)
    return out


def validate_predecessor(
    tcm1_registry: dict[str, Any],
    tcm1_evidence: dict[str, Any],
    tcm1_promotion: dict[str, Any],
    fixture1: dict[str, Any],
    fixture2: dict[str, Any],
    fixture2_promotion: dict[str, Any],
) -> tuple[list[int], set[int], int, list[int]]:
    keys(tcm1_registry, {"registry_version", "experiments"}, "TCM-QDEC-001 registry")
    if tcm1_registry["registry_version"] != "0.1.0" or not isinstance(tcm1_registry["experiments"], list):
        raise ValueError("TCM-QDEC-001 registry version/shape mismatch")
    matches = [x for x in tcm1_registry["experiments"] if x.get("experiment_id") == "TCM-QDEC-001"]
    if len(matches) != 1:
        raise ValueError("TCM-QDEC-001 registry identity mismatch")
    predecessor_experiment = matches[0]
    keys(
        predecessor_experiment,
        {
            "experiment_id", "programme", "status", "predecessor", "state_space",
            "semirings", "quotient_treatments", "claim_boundary",
        },
        "TCM-QDEC-001 experiment",
    )
    if predecessor_experiment["programme"] != "QTR" or predecessor_experiment["status"] != "candidate_executable_not_promoted":
        raise ValueError("TCM-QDEC-001 registry status changed")
    expected_t1_predecessor = {
        "fixture_id": "QLDPC-FIXTURE-002",
        "evidence_path": "evidence/QLDPC-FIXTURE-002-report.json",
        "evidence_payload_sha256": T1.FIXTURE_002_PAYLOAD,
        "corpus_sha256": T1.FIXTURE_002_CORPUS,
        "scientific_merge_commit": T1.FIXTURE_002_SCIENTIFIC_MERGE,
        "promotion_merge_commit": T1.FIXTURE_002_PROMOTION_MERGE,
        "promotion_record_path": "reviews/QTR-QLDPC-REVIEW-002/promotion-record.json",
    }
    expected_t1_state = {
        "sector_model": "code_capacity_single_css_sector",
        "corpus_kind": "fixture_002_frozen_hamming_weight_0_through_4",
        "corpus_size": 4048,
        "corpus_sha256": T1.FIXTURE_002_CORPUS,
        "full_physical_error_states": 262144,
        "reachable_syndromes": 128,
        "states_per_syndrome": 2048,
        "stabilizer_span_size": 128,
        "logical_cosets_per_syndrome": 16,
    }
    for name, observed, expected in (
        ("TCM-QDEC-001 predecessor", predecessor_experiment["predecessor"], expected_t1_predecessor),
        ("TCM-QDEC-001 state space", predecessor_experiment["state_space"], expected_t1_state),
        ("TCM-QDEC-001 semirings", predecessor_experiment["semirings"], T1.SEMIRINGS),
        ("TCM-QDEC-001 treatments", predecessor_experiment["quotient_treatments"], T1.TREATMENTS),
        ("TCM-QDEC-001 claim boundary", predecessor_experiment["claim_boundary"], T1.CLAIM_BOUNDARY),
    ):
        if observed != expected:
            raise ValueError(f"{name} changed")

    if tcm1_evidence.get("experiment_id") != "TCM-QDEC-001":
        raise ValueError("TCM-QDEC-001 evidence identity mismatch")
    if tcm1_evidence.get("status") != "candidate_executable_not_promoted":
        raise ValueError("TCM-QDEC-001 immutable evidence status changed")
    if tcm1_evidence.get("payload_sha256") != PREDECESSOR_PAYLOAD:
        raise ValueError("TCM-QDEC-001 evidence payload mismatch")
    unsigned = dict(tcm1_evidence)
    unsigned.pop("payload_sha256", None)
    if digest(unsigned) != PREDECESSOR_PAYLOAD:
        raise ValueError("TCM-QDEC-001 evidence payload does not self-verify")
    if tcm1_evidence.get("claim_boundary") != T1.CLAIM_BOUNDARY:
        raise ValueError("TCM-QDEC-001 evidence claim boundary changed")
    for algebra, expected_sha in PROMOTED_DECISION_SHA.items():
        cell = tcm1_evidence.get("inference_matrix", {}).get("stabilizer_coset_aggregate", {}).get(algebra, {})
        if cell.get("success_total") != PROMOTED_SUCCESS[algebra]:
            raise ValueError(f"TCM-QDEC-001 success total changed: {algebra}")
        if cell.get("decision_diagnostics", {}).get("decision_table_sha256") != expected_sha:
            raise ValueError(f"TCM-QDEC-001 decision identity changed: {algebra}")
        env = tcm1_evidence.get("tie_sensitivity", {}).get(algebra, {}).get(
            "frozen_corpus_success_count_envelope_over_winning_class_ties"
        )
        if env != {"min": PROMOTED_TIE_ENVELOPES[algebra][0], "max": PROMOTED_TIE_ENVELOPES[algebra][1]}:
            raise ValueError(f"TCM-QDEC-001 tie envelope changed: {algebra}")

    if tcm1_promotion.get("record_id") != PREDECESSOR_PROMOTION_RECORD:
        raise ValueError("TCM-QDEC-001 promotion identity mismatch")
    if tcm1_promotion.get("status") != "referee_promoted_bounded":
        raise ValueError("TCM-QDEC-001 is not bounded promoted")
    if tcm1_promotion.get("scientific_merge_commit") != PREDECESSOR_SCIENTIFIC_MERGE:
        raise ValueError("TCM-QDEC-001 scientific merge mismatch")
    snap = tcm1_promotion.get("reviewed_snapshot", {})
    if (
        snap.get("evidence_payload_sha256") != PREDECESSOR_PAYLOAD
        or snap.get("snapshot_preserved_byte_for_byte") is not True
    ):
        raise ValueError("TCM-QDEC-001 reviewed snapshot mismatch")
    if "TCM-QDEC-002" not in tcm1_promotion.get("excluded_scope", []):
        raise ValueError("TCM-QDEC-001 downstream exclusion changed")

    rows, stabilizers, n = T1.validate_predecessors(fixture1, fixture2, fixture2_promotion)
    logical_bits = fixture1.get("logical_basis", {}).get("z_bitstrings")
    if not isinstance(logical_bits, list) or len(logical_bits) != 4:
        raise ValueError("Fixture 001 logical-Z basis missing")
    logical_z = [little_bitstring_to_int(bits) for bits in logical_bits]
    if gf2_rank(rows) != 7 or gf2_rank(rows + logical_z) != 11:
        raise ValueError("combined check/logical rank mismatch")
    if any(logical_label(s, logical_z) != 0 for s in stabilizers):
        raise ValueError("stabilizer carries nonzero logical label")
    return rows, stabilizers, n, logical_z


def transfer_columns(rows: list[int], logical_z: list[int], n: int) -> list[int]:
    return [
        syndrome(1 << q, rows) | (logical_label(1 << q, logical_z) << len(rows))
        for q in range(n)
    ]


def prefix_geometry(columns: list[int]) -> tuple[list[int], list[int], list[int]]:
    ranks = [0]
    active_counts = [1]
    transition_counts: list[int] = []
    active = {0}
    for index, column in enumerate(columns):
        transition_counts.append(2 * len(active))
        active |= {state ^ column for state in tuple(active)}
        ranks.append(gf2_rank(columns[: index + 1]))
        active_counts.append(len(active))
    return ranks, active_counts, transition_counts


def transfer_mass(columns: list[int], zero_weight: int) -> dict[int, int]:
    dp = {0: 1}
    for column in columns:
        next_dp: dict[int, int] = {}
        for label, value in dp.items():
            next_dp[label] = next_dp.get(label, 0) + value * zero_weight
            toggled = label ^ column
            next_dp[toggled] = next_dp.get(toggled, 0) + value
        dp = next_dp
    return dp


def transfer_minimum_representatives(columns: list[int]) -> dict[int, tuple[int, int]]:
    dp = {0: (0, 0)}
    for q, column in enumerate(columns):
        next_dp: dict[int, tuple[int, int]] = {}
        for label, (weight, representative) in dp.items():
            zero = (weight, representative)
            if label not in next_dp or zero < next_dp[label]:
                next_dp[label] = zero
            toggled = label ^ column
            one = (weight + 1, representative | (1 << q))
            if toggled not in next_dp or one < next_dp[toggled]:
                next_dp[toggled] = one
        dp = next_dp
    return dp


def canonical_key(representative: int, stabilizers: set[int]) -> int:
    return min(representative ^ stabilizer for stabilizer in stabilizers)


def factorized_tables(
    rows: list[int], stabilizers: set[int], n: int, logical_z: list[int]
) -> tuple[dict[str, dict[int, int]], dict[str, dict[int, list[int]]], dict[str, Any]]:
    columns = transfer_columns(rows, logical_z, n)
    prefix_ranks, active_counts, transition_counts = prefix_geometry(columns)
    mass9 = transfer_mass(columns, 9)
    mass2 = transfer_mass(columns, 2)
    minimum = transfer_minimum_representatives(columns)
    if set(mass9) != set(mass2) or set(mass9) != set(minimum):
        raise AssertionError("factorized semiring supports disagree")
    if len(minimum) != 2048:
        raise AssertionError("unexpected reachable combined-label count")

    selector_width = len(rows) + len(logical_z)
    syndrome_mask = (1 << len(rows)) - 1
    by_syndrome: dict[int, list[int]] = {}
    mapping_records: list[dict[str, Any]] = []
    class_keys: dict[int, int] = {}
    representatives: dict[int, int] = {}
    min_weights: dict[int, int] = {}
    for selector in sorted(minimum):
        weight, representative = minimum[selector]
        syn = selector & syndrome_mask
        by_syndrome.setdefault(syn, []).append(selector)
        key = canonical_key(representative, stabilizers)
        class_keys[selector] = key
        representatives[selector] = representative
        min_weights[selector] = weight
        mapping_records.append(
            {
                "selector": i2b(selector, selector_width),
                "syndrome": i2b(syn, len(rows)),
                "logical_label": i2b(selector >> len(rows), len(logical_z)),
                "canonical_coset_key": i2b(key, n),
                "minimum_representative": i2b(representative, n),
                "minimum_weight": weight,
            }
        )
    if len(by_syndrome) != 128 or set(map(len, by_syndrome.values())) != {16}:
        raise AssertionError("unexpected syndrome/logical class geometry")
    if len(set(class_keys.values())) != 2048:
        raise AssertionError("logical labels do not distinguish stabilizer cosets")

    scores = {
        "sum_product_bsc_p_0_1": mass9,
        "soft_tropical_base_2": mass2,
        "min_plus_hamming": min_weights,
    }
    tables: dict[str, dict[int, int]] = {a: {} for a in SEMIRINGS}
    ties: dict[str, dict[int, list[int]]] = {a: {} for a in SEMIRINGS}
    tie_records: dict[str, list[dict[str, Any]]] = {a: [] for a in SEMIRINGS}

    for algebra in SEMIRINGS:
        maximize = SEMIRINGS[algebra]["score_direction"] == "maximize"
        for syn in sorted(by_syndrome):
            selectors = by_syndrome[syn]
            values = [scores[algebra][selector] for selector in selectors]
            best = max(values) if maximize else min(values)
            tied_selectors = [selector for selector in selectors if scores[algebra][selector] == best]
            tied_selectors.sort(key=lambda selector: class_keys[selector])
            tied_keys = [class_keys[selector] for selector in tied_selectors]
            ties[algebra][syn] = tied_keys
            tables[algebra][syn] = representatives[tied_selectors[0]]
            tie_records[algebra].append(
                {
                    "syndrome": i2b(syn, len(rows)),
                    "canonical_coset_keys": [i2b(key, n) for key in tied_keys],
                }
            )

    score_digests: dict[str, str] = {}
    for algebra in SEMIRINGS:
        records = [
            {"selector": i2b(selector, selector_width), "score": scores[algebra][selector]}
            for selector in sorted(scores[algebra])
        ]
        score_digests[algebra] = digest(records)

    decision_digests: dict[str, str] = {}
    for algebra in SEMIRINGS:
        records = [
            {"syndrome": i2b(syn, len(rows)), "correction": i2b(correction, n)}
            for syn, correction in sorted(tables[algebra].items())
        ]
        decision_digests[algebra] = digest(records)

    column_records = [
        {
            "qubit": q,
            "selector_toggle": i2b(column, selector_width),
            "syndrome_toggle": i2b(column & syndrome_mask, len(rows)),
            "logical_toggle": i2b(column >> len(rows), len(logical_z)),
        }
        for q, column in enumerate(columns)
    ]

    diagnostics = {
        "columns": columns,
        "prefix_combined_ranks": prefix_ranks,
        "prefix_active_state_counts": active_counts,
        "transition_counts_by_qubit": transition_counts,
        "column_signature_sha256": digest(column_records),
        "canonical_class_mapping_sha256": digest(mapping_records),
        "score_table_sha256": score_digests,
        "decision_table_sha256": decision_digests,
        "winning_class_tie_sets_sha256": {
            algebra: digest(tie_records[algebra]) for algebra in SEMIRINGS
        },
        "sum_product_total_partition_mass": sum(mass9.values()),
        "soft_tropical_total_partition_mass": sum(mass2.values()),
        "minimum_weight_histogram_over_combined_labels": {
            str(weight): count
            for weight, count in sorted(Counter(min_weights.values()).items())
        },
    }
    return tables, ties, diagnostics


def factorized_tie_sensitivity(
    corpus: list[int], rows: list[int], stabilizers: set[int],
    ties: dict[str, dict[int, list[int]]],
) -> dict[str, Any]:
    counts: dict[int, dict[int, int]] = {}
    for error in corpus:
        syn = syndrome(error, rows)
        key = canonical_key(error, stabilizers)
        counts.setdefault(syn, {})
        counts[syn][key] = counts[syn].get(key, 0) + 1

    out: dict[str, Any] = {}
    for algebra in SEMIRINGS:
        lower = upper = default = 0
        histogram: dict[str, int] = {}
        for syn, tied_keys in ties[algebra].items():
            histogram[str(len(tied_keys))] = histogram.get(str(len(tied_keys)), 0) + 1
            values = [counts.get(syn, {}).get(key, 0) for key in tied_keys]
            default += values[0]
            lower += min(values)
            upper += max(values)
        out[algebra] = {
            "winning_class_count_histogram": histogram,
            "default_lowest_key_success_count": default,
            "frozen_corpus_success_count_envelope_over_winning_class_ties": {
                "min": lower,
                "max": upper,
            },
            "success_count_invariant_under_winning_class_tie_break": lower == upper,
        }
    return out


def evaluate(
    experiment: dict[str, Any],
    tcm1_registry: dict[str, Any],
    tcm1_evidence: dict[str, Any],
    tcm1_promotion: dict[str, Any],
    fixture1: dict[str, Any],
    fixture2: dict[str, Any],
    fixture2_promotion: dict[str, Any],
) -> dict[str, Any]:
    rows, stabilizers, n, logical_z = validate_predecessor(
        tcm1_registry, tcm1_evidence, tcm1_promotion,
        fixture1, fixture2, fixture2_promotion,
    )
    tables, ties, diagnostics = factorized_tables(rows, stabilizers, n, logical_z)

    oracle_tables, oracle_diagnostics, oracle_ties, _ = T1.infer_tables(rows, stabilizers, n)
    oracle_quotient = oracle_tables["stabilizer_coset_aggregate"]
    for algebra in SEMIRINGS:
        if tables[algebra] != oracle_quotient[algebra]:
            raise AssertionError(f"factorized decision table disagrees with oracle: {algebra}")
        if ties[algebra] != oracle_ties[algebra]:
            raise AssertionError(f"factorized winning-class ties disagree with oracle: {algebra}")
        if diagnostics["decision_table_sha256"][algebra] != PROMOTED_DECISION_SHA[algebra]:
            raise AssertionError(f"factorized decision digest changed: {algebra}")
        if oracle_diagnostics["stabilizer_coset_aggregate"][algebra]["decision_table_sha256"] != PROMOTED_DECISION_SHA[algebra]:
            raise AssertionError(f"oracle decision digest changed: {algebra}")

    corpus = T1.F2.make_corpus(n, 4)
    if len(corpus) != 4048:
        raise AssertionError("Fixture 002 corpus size changed")
    factorized_results: dict[str, Any] = {}
    for algebra in SEMIRINGS:
        result, _ = T1.classify(corpus, rows, stabilizers, tables[algebra])
        if result["success_total"] != PROMOTED_SUCCESS[algebra]:
            raise AssertionError(f"factorized success total changed: {algebra}")
        factorized_results[algebra] = {
            **result,
            "decision_table_sha256": diagnostics["decision_table_sha256"][algebra],
        }

    tie_report = factorized_tie_sensitivity(corpus, rows, stabilizers, ties)
    for algebra, expected in PROMOTED_TIE_ENVELOPES.items():
        env = tie_report[algebra]["frozen_corpus_success_count_envelope_over_winning_class_ties"]
        if env != {"min": expected[0], "max": expected[1]}:
            raise AssertionError(f"factorized tie envelope changed: {algebra}")

    prefix_ranks = diagnostics["prefix_combined_ranks"]
    active_counts = diagnostics["prefix_active_state_counts"]
    transitions = diagnostics["transition_counts_by_qubit"]
    if prefix_ranks != [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 11, 11, 11, 11, 11, 11, 11]:
        raise AssertionError("unexpected prefix-rank profile")
    if active_counts != [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048]:
        raise AssertionError("unexpected active-state profile")
    if sum(transitions) != 32766:
        raise AssertionError("unexpected transfer transition count")

    report: dict[str, Any] = {
        "experiment_id": "TCM-QDEC-002",
        "evaluator_version": EVALUATOR_VERSION,
        "status": "candidate_executable_not_promoted",
        "predecessor": experiment["predecessor"],
        "claim_boundary": experiment["claim_boundary"],
        "representation": experiment["representation"],
        "semirings": experiment["semirings"],
        "decision_rule": experiment["decision_rule"],
        "factorization_geometry": {
            "check_rank": gf2_rank(rows),
            "combined_check_logical_rank": gf2_rank(rows + logical_z),
            "redundant_selector_bits": len(rows) + len(logical_z) - gf2_rank(rows + logical_z),
            "reachable_syndromes": len(next(iter(tables.values()))),
            "logical_classes_per_syndrome": 16,
            "reachable_combined_labels": 2048,
            "selector_space_capacity": 1 << (len(rows) + len(logical_z)),
            "stabilizer_span_size": len(stabilizers),
            "stabilizers_zero_logical_label": all(logical_label(s, logical_z) == 0 for s in stabilizers),
            "column_signature_sha256": diagnostics["column_signature_sha256"],
            "prefix_combined_ranks": prefix_ranks,
            "prefix_active_state_counts": active_counts,
            "peak_active_state_count": max(active_counts),
        },
        "factorized_contraction": {
            "primary_full_physical_state_enumeration": False,
            "transition_relaxations_per_algebra": sum(transitions),
            "algebra_contractions": 3,
            "transition_relaxations_total": 3 * sum(transitions),
            "final_score_entry_count_per_algebra": 2048,
            "sum_product_total_partition_mass": diagnostics["sum_product_total_partition_mass"],
            "soft_tropical_total_partition_mass": diagnostics["soft_tropical_total_partition_mass"],
            "minimum_weight_histogram_over_combined_labels": diagnostics["minimum_weight_histogram_over_combined_labels"],
            "canonical_class_mapping_sha256": diagnostics["canonical_class_mapping_sha256"],
            "score_table_sha256": diagnostics["score_table_sha256"],
        },
        "factorized_decisions": factorized_results,
        "winning_class_tie_sets_sha256": diagnostics["winning_class_tie_sets_sha256"],
        "tie_sensitivity": tie_report,
        "oracle_equivalence": {
            "oracle_experiment_id": "TCM-QDEC-001",
            "oracle_full_state_enumeration_count": 1 << n,
            "winning_class_tie_set_cells_checked": len(SEMIRINGS) * 128,
            "winning_class_tie_sets_exactly_equal": True,
            "decision_entries_checked": len(SEMIRINGS) * 128,
            "decision_tables_exactly_equal": True,
            "promoted_decision_table_sha256": PROMOTED_DECISION_SHA,
            "promoted_success_totals": PROMOTED_SUCCESS,
            "promoted_tie_envelopes": PROMOTED_TIE_ENVELOPES,
        },
    }
    report["payload_sha256"] = digest(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default=str(ROOT / "registry" / "tcm-qdec-002.json"))
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
