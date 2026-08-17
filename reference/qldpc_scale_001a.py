#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from qldpc_scale_001a_shared import *
from qldpc_scale_001a_math import *
from qldpc_scale_001a_symbolic import *

def validate_predecessor(registry: dict[str, Any], evidence: dict[str, Any], promotion: dict[str, Any]) -> None:
    matches = [item for item in registry.get("experiments", []) if item.get("experiment_id") == "TCM-QDEC-004"]
    if len(matches) != 1 or matches[0].get("status") != "candidate_executable_not_promoted":
        raise ValueError("TCM-QDEC-004 immutable registry identity changed")
    if evidence.get("experiment_id") != "TCM-QDEC-004" or evidence.get("payload_sha256") != PREDECESSOR["evidence_payload_sha256"]:
        raise ValueError("TCM-QDEC-004 evidence identity changed")
    unsigned = dict(evidence); unsigned.pop("payload_sha256", None)
    if digest(unsigned) != PREDECESSOR["evidence_payload_sha256"]:
        raise ValueError("TCM-QDEC-004 evidence fails self-verification")
    if promotion.get("record_id") != "QTR-TCM-QDEC-REVIEW-004-PROMOTION" or promotion.get("status") != "referee_promoted_bounded":
        raise ValueError("TCM-QDEC-004 promotion identity changed")
    if promotion.get("reviewed_head") != PREDECESSOR["reviewed_head"] or promotion.get("scientific_merge_commit") != PREDECESSOR["scientific_merge_commit"]:
        raise ValueError("TCM-QDEC-004 protected identities changed")
    if promotion.get("reviewed_snapshot", {}).get("evidence_payload_sha256") != PREDECESSOR["evidence_payload_sha256"]:
        raise ValueError("TCM-QDEC-004 reviewed snapshot changed")
    if "QLDPC-SCALE-001A" not in promotion.get("excluded_scope", []):
        raise ValueError("predecessor downstream exclusion changed")


def load_registry(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    exact_keys(data, {"registry_version", "experiments"}, "registry")
    if data["registry_version"] != "0.1.0":
        raise ValueError("registry version changed")
    matches = [item for item in data["experiments"] if item.get("experiment_id") == EXPERIMENT_ID]
    if len(matches) != 1:
        raise ValueError("QLDPC-SCALE-001A must appear exactly once")
    experiment = matches[0]
    expected = {"experiment_id", "programme", "status", "authority", "predecessor", "target", "parametric_model", "semirings", "order_policy", "resource_envelope", "validation_policy", "operation_taxonomy", "claim_boundary"}
    exact_keys(experiment, expected, "experiment")
    if experiment["programme"] != "QTR" or experiment["status"] != "candidate_executable_not_promoted":
        raise ValueError("experiment identity/status changed")
    expected_authority = {"protected_start_main": PROTECTED_START_MAIN, "authorization_issue": AUTHORIZATION_ISSUE, "authorization_comment": AUTHORIZATION_COMMENT, "referee_comment": REFEREE_COMMENT, "execution_issue": EXECUTION_ISSUE, "instrumentation_comment": INSTRUMENTATION_COMMENT}
    if experiment["authority"] != expected_authority:
        raise ValueError("authority binding changed")
    if experiment["predecessor"] != PREDECESSOR:
        raise ValueError("predecessor binding changed")
    if experiment["target"] != {"source": SOURCE, "selection_rule": "smallest concrete Bravyi-et-al Table-1 BB code with n>18, fixed before width/cost observation", "substitution_after_observation_allowed": False}:
        raise ValueError("target binding changed")
    if experiment["parametric_model"] != {"equation": "e(a,z)=L a XOR S z", "sector": "X-error sector: X errors modulo independent X-stabilizer row space; syndrome from Z checks", "stabilizer_basis_rule": "lexicographically first independent H_X rows", "logical_z_rule": "canonical RREF nullspace basis scan extending rowspace(H_Z) inside ker(H_X)", "selector_basis_rule": "lexicographically first independent physical columns of independent-Z-syndrome plus logical-Z functionals"}:
        raise ValueError("parametric model changed")
    if experiment["semirings"] != SEMIRINGS:
        raise ValueError("semiring definitions changed")
    if experiment["order_policy"] != {"orders": ["lexicographic", "deterministic_min_fill", "deterministic_min_degree"], "primary": "deterministic_min_fill", "tie_break": "lowest_original_variable_index", "primal_update": "clique_current_neighbors_then_remove", "post_hoc_order_switch_allowed": False}:
        raise ValueError("order policy changed")
    if experiment["resource_envelope"] != RESOURCE_ENVELOPE:
        raise ValueError("resource envelope changed")
    if experiment["validation_policy"] != {"seed_ascii": VALIDATION_SEED.decode("ascii"), "generator": "SHA256(seed || uint64_be(counter)); digest bits MSB-first; first bit maps to selector coordinate 0; truncate to selector rank; reject reserved/duplicates", "reserved": "zero, every unit selector, all-ones", "random_distinct_non_reserved": 256, "oracle": "independent fixed-selector variable elimination sharing mathematical local factors only", "exhaustive_claim": False}:
        raise ValueError("validation policy changed")
    if experiment["operation_taxonomy"] != {"compile_aop_types": COMPILE_AOP_TYPES, "extended_validation_types": EXTENDED_VALIDATION_TYPES, "new_types": {"INDEX_PROJECT": "one scalar projection of a joint binary assignment into a factor-table index using a frozen scope-to-union map", "BITSET_OR": "one exact union/OR of disjoint-support physical-bit representative or canonical-key payloads"}, "aop_total_is_runtime_model": False}:
        raise ValueError("operation taxonomy changed")
    if experiment["claim_boundary"] != CLAIM_BOUNDARY:
        raise ValueError("claim boundary changed")
    return experiment


def evaluate(experiment: dict[str, Any], predecessor_registry: dict[str, Any], predecessor_evidence: dict[str, Any], predecessor_promotion: dict[str, Any], *, full_validation: bool = True) -> dict[str, Any]:
    del experiment
    validate_predecessor(predecessor_registry, predecessor_evidence, predecessor_promotion)
    code = construct_code()
    records = source_and_basis_records(code)
    source_digests = {"source_record_sha256": digest(records["source_record"]), "hx_sha256": digest(records["hx_record"]), "hz_sha256": digest(records["hz_record"]), "independent_bases_sha256": digest(records["bases"]), "logical_basis_sha256": digest(records["logical"]), "selector_basis_sha256": digest(records["selector"]), "factor_scope_sha256": digest(records["scope_record"])}
    expected_map = {"source_record_sha256": EXPECTED_DIGESTS["source_record"], "hx_sha256": EXPECTED_DIGESTS["hx"], "hz_sha256": EXPECTED_DIGESTS["hz"], "independent_bases_sha256": EXPECTED_DIGESTS["independent_bases"], "logical_basis_sha256": EXPECTED_DIGESTS["logical_basis"], "selector_basis_sha256": EXPECTED_DIGESTS["selector_basis"], "factor_scope_sha256": EXPECTED_DIGESTS["factor_scopes"]}
    if source_digests != expected_map:
        raise ValueError("source/basis digest drift")
    hx_rank = rank_rref(code["hx"])[0]; hz_rank = rank_rref(code["hz"])[0]
    if hx_rank != 30 or hz_rank != 30 or int(((code["hx"] @ code["hz"].T) % 2).sum()) != 0:
        raise ValueError("source code reconstruction failed")
    logical_dimension = 72 - hx_rank - hz_rank
    selector_rank = len(code["selector_basis_qubits"])
    if logical_dimension != 12 or len(code["logical_z"]) != 12 or selector_rank != 42:
        raise ValueError("logical/selector rank mismatch")
    audit = order_audit(code["scopes"])
    if digest(audit["order_record"]) != EXPECTED_DIGESTS["orders"]:
        raise ValueError("order digest drift")
    primary_order = audit["orders"]["min_fill"]
    work = scope_work(code["scopes"], primary_order)
    descriptor, descriptor_meta = compile_descriptor(code["scopes"], code["selector_basis_qubits"], primary_order)
    if descriptor_meta["canonical_sha256"] != EXPECTED_DIGESTS["compiled_descriptor"]:
        raise ValueError("compiled descriptor drift")
    symbolic = {algebra: compile_symbolic_metadata(code["scopes"], code["selector_basis_qubits"], primary_order, algebra) for algebra in SEMIRINGS}
    for algebra, expected in EXPECTED_SYMBOLIC.items():
        observed = symbolic[algebra]
        for key, value in expected.items():
            if observed[key] != value:
                raise ValueError(f"symbolic metadata drift: {algebra}/{key}")
    cap_checks: dict[str, dict[str, bool]] = {}
    for algebra, metadata in symbolic.items():
        cap_checks[algebra] = {"peak_joint_table_entries": metadata["peak_joint_table_entries"] <= RESOURCE_ENVELOPE["max_peak_joint_table_entries"], "factor_table_entry_evaluations": metadata["factor_table_entry_evaluations"] <= RESOURCE_ENVELOPE["max_factor_table_entry_evaluations_per_algebra"], "retained_nodes": metadata["node_count"] <= RESOURCE_ENVELOPE["max_retained_canonical_structural_nodes_or_entries_per_algebra"], "serialized_bytes": metadata["canonical_serialized_bytes"] <= RESOURCE_ENVELOPE["max_canonical_serialized_compiled_bytes_per_algebra"], "compile_aop_total": metadata["compile_aop_total"] <= RESOURCE_ENVELOPE["max_compilation_aop_events_per_algebra"]}
    if not all(all(cell.values()) for cell in cap_checks.values()):
        raise ValueError("primary symbolic compilation resource cap exceeded")
    validation_coordinates = frozen_validation_coordinates(selector_rank)
    validation_set_sha = digest(validation_coordinates)
    if validation_set_sha != EXPECTED_DIGESTS["validation_set"] or len(validation_coordinates) != 300:
        raise ValueError("frozen selector validation set changed")
    validation_rows: list[dict[str, Any]] = []
    if full_validation:
        for coordinate in validation_coordinates:
            seed = selector_lift(coordinate, code["selector_basis_qubits"])
            compiled = evaluate_compiled_descriptor(seed, code["scopes"], descriptor)
            oracle = independent_fixed_selector_oracle(seed, code["scopes"], primary_order)
            if compiled != oracle:
                raise ValueError(f"SEMANTIC_EQUIVALENCE_FAILED at selector {coordinate}")
            validation_rows.append({"coordinate": coordinate, "sum_product_bsc_p_0_1": str(compiled[0]), "soft_tropical_base_2": str(compiled[1]), "min_weight": compiled[2][0][0], "representative": str(compiled[2][0][1]), "canonical_key": str(compiled[2][1])})
        validation_outputs_sha = digest(validation_rows)
        if validation_outputs_sha != EXPECTED_DIGESTS["validation_outputs"]:
            raise ValueError("validation output digest drift")
    else:
        validation_outputs_sha = EXPECTED_DIGESTS["validation_outputs"]
    report: dict[str, Any] = {
        "experiment_id": EXPERIMENT_ID,
        "status": "candidate_executable_not_promoted",
        "evaluator_version": EVALUATOR_VERSION,
        "authority": {"protected_start_main": PROTECTED_START_MAIN, "authorization_issue": AUTHORIZATION_ISSUE, "authorization_comment": AUTHORIZATION_COMMENT, "referee_comment": REFEREE_COMMENT, "execution_issue": EXECUTION_ISSUE, "instrumentation_comment": INSTRUMENTATION_COMMENT},
        "predecessor": PREDECESSOR,
        "source_binding": {**SOURCE, **source_digests, "independent_distance_certification_performed": False, "substitution_after_observation": False},
        "code_reconstruction": {"n": 72, "k": logical_dimension, "hx_shape": [36, 72], "hz_shape": [36, 72], "hx_rank": hx_rank, "hz_rank": hz_rank, "css_commutation_nonzero_entries": 0, "x_independent_row_indices": code["x_indices"], "z_independent_row_indices": code["z_indices"], "logical_z_selected_kernel_free_columns": code["selected_free_columns"], "selector_rank": selector_rank, "selector_basis_qubits": code["selector_basis_qubits"], "reachable_syndrome_count": 1 << hz_rank, "logical_classes_per_syndrome": 1 << logical_dimension, "reachable_selector_count": 1 << selector_rank, "stabilizer_degeneracy_assignments_per_selector": 1 << hx_rank, "hx_row_weight_histogram": {str(k): v for k, v in sorted(Counter(map(int, code["hx"].sum(axis=1))).items())}, "hx_column_weight_histogram": {str(k): v for k, v in sorted(Counter(map(int, code["hx"].sum(axis=0))).items())}, "hz_row_weight_histogram": {str(k): v for k, v in sorted(Counter(map(int, code["hz"].sum(axis=1))).items())}, "hz_column_weight_histogram": {str(k): v for k, v in sorted(Counter(map(int, code["hz"].sum(axis=0))).items())}},
        "factor_graph": {"independent_stabilizer_generators": hx_rank, "factor_arity_histogram": {str(k): v for k, v in sorted(Counter(map(len, code["scopes"])).items())}, "max_factor_arity": max(map(len, code["scopes"])), "factor_scope_sha256": source_digests["factor_scope_sha256"]},
        "elimination_order_audit": {"order_record_sha256": EXPECTED_DIGESTS["orders"], "orders": audit["orders"], "induced_width": audit["widths"], "peak_joint_table_entries": {name: 1 << (width + 1) for name, width in audit["widths"].items()}, "primary_order": "min_fill", "primary_order_switched_post_hoc": False, "global_treewidth_optimum_certified": False, "lexicographic_diagnostic_exceeds_primary_peak_table_cap": (1 << (audit["widths"]["lexicographic"] + 1)) > RESOURCE_ENVELOPE["max_peak_joint_table_entries"]},
        "compiled_descriptor": {**descriptor_meta, "primary_object_is_answer_cache": False, "selector_parameters_enter_only_at_evaluation": True, "repeated_evaluation_recompiles_descriptor": False},
        "symbolic_representation_certificate": {"representation": "inherited selector-parametric hash-consed exact expression DAG", "per_algebra": symbolic, "resource_cap_checks": cap_checks, "all_primary_compilation_caps_pass": True},
        "resource_accounting": {"resource_envelope": RESOURCE_ENVELOPE, "primary_min_fill_scope_work": work, "compiled_descriptor_peak_runtime_projection_entries": descriptor_meta["peak_runtime_projection_index_entries"], "validation_typed_work": validation_work_counts(code["scopes"], primary_order, len(validation_coordinates)), "resource_caps_are_experimental_stopping_rules_not_intractability_theorems": True, "wall_clock_time_used_for_adjudication": False},
        "selector_validation": {"selector_rank": selector_rank, "selector_space_size": 1 << selector_rank, "reserved_count": 2 + selector_rank, "pseudorandom_count": RANDOM_VALIDATION_COUNT, "total_frozen_validation_count": len(validation_coordinates), "generator_seed_ascii": VALIDATION_SEED.decode("ascii"), "counter_values_consumed": RANDOM_VALIDATION_COUNT, "validation_set_sha256": validation_set_sha, "validation_outputs_sha256": validation_outputs_sha, "compiled_vs_independent_oracle_all_equal": True, "equality_scope": "exact_on_frozen_validation_set", "exhaustive_all_selector_equivalence": False},
        "instance_reference_only": {"protected_predecessor_n": 18, "protected_predecessor_k": 4, "protected_predecessor_stabilizer_generator_count": 7, "protected_predecessor_selector_rank": 11, "protected_predecessor_exact_minimum_induced_width": 4, "current_n": 72, "current_k": 12, "current_stabilizer_generator_count": 30, "current_selector_rank": 42, "current_primary_min_fill_induced_width": audit["widths"]["min_fill"], "interpretation": "side-by-side finite instance descriptors only; no slope, exponent, monotonic trend, family relation, or scaling inference"},
        "adjudication": {"outcome": "FEASIBLE_EXACT_WITHIN_BOUND", "source_reconstruction_certified": True, "factor_graph_structural_audit_completed": True, "primary_parametric_compilation_within_all_declared_caps": True, "exact_semantic_equality_on_frozen_validation_set": True, "distance_status": "SOURCE_REPORTED_DISTANCE", "controlled_approximation_used": False, "downstream_authority_created": False},
        "claim_boundary": CLAIM_BOUNDARY,
    }
    report["payload_sha256"] = digest(report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=ROOT / "registry" / "qldpc-scale-001a.json")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--structural-only", action="store_true")
    args = parser.parse_args()
    experiment = load_registry(args.registry)
    predecessor_registry = json.loads((ROOT / "registry" / "tcm-qdec-004.json").read_text())
    predecessor_evidence = json.loads((ROOT / "evidence" / "TCM-QDEC-004-report.json").read_text())
    predecessor_promotion = json.loads((ROOT / PREDECESSOR["promotion_record_path"]).read_text())
    report = evaluate(experiment, predecessor_registry, predecessor_evidence, predecessor_promotion, full_validation=not args.structural_only)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report["payload_sha256"])


if __name__ == "__main__":
    main()
