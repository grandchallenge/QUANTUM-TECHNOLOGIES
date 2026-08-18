#!/usr/bin/env python3
"""Authoritative amended replay for QEC-CIRCUIT-001.

This module composes the immutable base temporal manifest with the precommitted
TCM semantic amendment. The first workflow run bound only to the base manifest
is quarantined and no result from it is scientifically admissible.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import qec_circuit_001 as B

EVALUATOR_VERSION = "0.1.1"
AMENDMENT_PATH = ROOT / "registry/qec-circuit-001-manifest-amendment-001.json"
AMENDMENT_PAYLOAD = "8be8637ef976c9096b22259f0f849e2350a997b80038f4815302fbefa5f2ad19"
QUARANTINED_RUN = 32085478805
QUARANTINED_HEAD = "5f623a086dc9657e8abc32926bc42b374862cd51"


def load_amendment(path: Path = AMENDMENT_PATH) -> dict[str, Any]:
    data = B.load_json(path)
    claimed = data.pop("amendment_payload_sha256")
    observed = B.digest(data)
    data["amendment_payload_sha256"] = claimed
    if claimed != AMENDMENT_PAYLOAD or observed != AMENDMENT_PAYLOAD:
        raise ValueError("QEC-CIRCUIT-001 amendment self-digest mismatch")
    if data["experiment_id"] != B.EXPERIMENT_ID:
        raise ValueError("QEC-CIRCUIT-001 amendment experiment drift")
    if data["base_manifest"] != {
        "first_commit": "ce36f40cd33d665084bd3cf2f744a7cae94bc76c",
        "path": "registry/qec-circuit-001-manifest.json",
        "payload_sha256": B.MANIFEST_PAYLOAD,
    }:
        raise ValueError("QEC-CIRCUIT-001 base-manifest binding drift")
    q = data["quarantined_execution"]
    if (
        q["workflow_run"] != QUARANTINED_RUN
        or q["evaluated_head"] != QUARANTINED_HEAD
        or q["scientific_results_admitted"] is not False
        or q["decoder_result_payloads_inspected_before_repair"] is not False
        or q["job_status_metadata_inspected_only"] is not True
        or q["all_rows_must_reexecute_under_amended_contract"] is not True
    ):
        raise ValueError("quarantined execution record drift")
    repair = data["repair"]
    for key in (
        "conventional_decoder_contract_changed",
        "detector_map_changed",
        "corpus_changed",
        "channel_probability_changed",
        "terminal_correctness_oracle_changed",
        "outcome_driven",
    ):
        if repair[key] is not False:
            raise ValueError(f"forbidden amendment drift: {key}")
    if repair["tcm_semantics_changed_from_incomplete_to_complete_declared_representation"] is not True:
        raise ValueError("TCM specification repair record missing")
    for key in (
        "gate_level_claim",
        "threshold_claim",
        "runtime_or_memory_superiority_claim",
        "family_or_asymptotic_claim",
        "qldpc_forge_authorized",
    ):
        if data["claim_boundary"][key] is not False:
            raise ValueError(f"amendment claim inflation: {key}")
    return data


def protected_logical_z(amendment: dict[str, Any]) -> list[int]:
    fixture = B.load_json(ROOT / "evidence/QLDPC-FIXTURE-001-report.json")
    observed = fixture["logical_basis"]["z_bitstrings"]
    expected = amendment["temporal_tcm"]["logical_selector"]["basis_bitstrings"]
    if observed != expected:
        raise ValueError("protected logical-Z basis drift")
    if B.digest(observed) != amendment["temporal_tcm"]["logical_selector"]["basis_sha256"]:
        raise ValueError("protected logical-Z basis digest drift")
    return [B.b2i(x) for x in observed]


def logical_selector(error: int, logical_z: list[int]) -> int:
    out = 0
    for i, z in enumerate(logical_z):
        if (error & z).bit_count() & 1:
            out |= 1 << i
    return out


def logical_selector_scopes(logical_z: list[int]) -> list[list[int]]:
    scopes: list[list[int]] = []
    for z in logical_z:
        support = [q for q in range(18) if (z >> q) & 1]
        scopes.append(
            support
            + [18 + q for q in support]
            + [36 + q for q in support]
        )
    return scopes


def full_tcm_scopes(detector_rows: list[int], logical_z: list[int]) -> list[list[int]]:
    return (
        B.detector_scopes(detector_rows)
        + [[q] for q in range(75)]
        + logical_selector_scopes(logical_z)
    )


def correction_representative_table(
    basis_rows: list[int], logical_z: list[int]
) -> list[dict[str, Any]]:
    best: dict[tuple[int, int], tuple[int, int]] = {}
    for error in range(1 << 18):
        key = (B.syndrome(error, basis_rows), logical_selector(error, logical_z))
        candidate = (error.bit_count(), error)
        current = best.get(key)
        if current is None or candidate < current:
            best[key] = candidate
    if len(best) != 2048:
        raise AssertionError("incomplete temporal terminal correction table")
    records: list[dict[str, Any]] = []
    for syn in range(128):
        for selector in range(16):
            weight, error = best[(syn, selector)]
            records.append(
                {
                    "syndrome": B.i2b(syn, 7),
                    "logical_selector": B.i2b(selector, 4),
                    "correction": B.i2b(error, 18),
                    "weight": weight,
                }
            )
    return records


def amended_tcm_report(
    manifest: dict[str, Any], amendment: dict[str, Any], basis_rows: list[int]
) -> dict[str, Any]:
    detector_rows = B.build_detector_formula(basis_rows)
    logical_z = protected_logical_z(amendment)
    selector_scopes = logical_selector_scopes(logical_z)
    tcm = amendment["temporal_tcm"]
    if B.digest(selector_scopes) != tcm["factor_representation"]["logical_selector_scope_sha256"]:
        raise AssertionError("logical-selector scope digest drift")
    scopes = full_tcm_scopes(detector_rows, logical_z)
    if B.digest(scopes) != tcm["factor_representation"]["all_factor_scope_sha256"]:
        raise AssertionError("complete temporal TCM factor-scope digest drift")
    histogram: dict[str, int] = {}
    for scope in scopes:
        key = str(len(scope))
        histogram[key] = histogram.get(key, 0) + 1
    if histogram != tcm["factor_representation"]["factor_scope_arity_histogram"]:
        raise AssertionError("complete temporal TCM factor arity drift")
    if len(scopes) != tcm["factor_representation"]["factor_count"]:
        raise AssertionError("complete temporal TCM factor count drift")

    graph = B.primal_graph(scopes)
    orders = {
        "lexicographic": B.elimination_order(graph, "lexicographic"),
        "deterministic_min_fill": B.elimination_order(graph, "deterministic_min_fill"),
        "deterministic_min_degree": B.elimination_order(graph, "deterministic_min_degree"),
    }
    expected = tcm["structural_preflight"]["orders"]
    if orders != expected:
        raise AssertionError("amended temporal TCM structural preflight drift")

    table = correction_representative_table(basis_rows, logical_z)
    correction = tcm["correction_representative"]
    if len(table) != correction["table_entry_count"]:
        raise AssertionError("terminal correction table size drift")
    if B.digest(table) != correction["table_sha256"]:
        raise AssertionError("terminal correction table digest drift")
    if max(row["weight"] for row in table) != correction["maximum_representative_weight"]:
        raise AssertionError("terminal correction representative weight drift")

    primary = orders[tcm["structural_preflight"]["primary_order"]]
    cap = manifest["tcm_resource_envelope"]["peak_joint_table_entries"]
    if cap != tcm["structural_preflight"]["frozen_peak_joint_table_cap"]:
        raise AssertionError("amendment/base TCM cap mismatch")
    if primary["peak_joint_table_entries"] <= cap:
        raise AssertionError("expected amended TCM cap exhaustion not reproduced")

    return {
        "status": "TEMPORAL_TCM_EXACT_BOUND_EXHAUSTED",
        "algebra": tcm["algebra"],
        "semantic_objective": tcm["semantic_objective"],
        "logical_selector": tcm["logical_selector"],
        "correction_representative": tcm["correction_representative"],
        "tie_semantics": tcm["tie_semantics"],
        "factor_representation": tcm["factor_representation"],
        "orders": orders,
        "primary_cap": cap,
        "stopped_before_table_materialization": True,
        "intrinsic_intractability_claim": False,
    }


def static_report(
    manifest: dict[str, Any], amendment: dict[str, Any]
) -> dict[str, Any]:
    substrate = B.static_report(manifest)
    _, _, _, basis_rows = B.load_fixture(manifest)
    substrate["evaluator_version"] = EVALUATOR_VERSION
    substrate["manifest_amendment_payload_sha256"] = AMENDMENT_PAYLOAD
    substrate["quarantined_execution"] = amendment["quarantined_execution"]
    substrate["temporal_tcm"] = amended_tcm_report(manifest, amendment, basis_rows)
    return substrate


def decode_method(
    method: str, manifest: dict[str, Any], amendment: dict[str, Any]
) -> dict[str, Any]:
    # Execute the unchanged conventional contract only after the amended static
    # contract has replayed successfully.
    static_report(manifest, amendment)
    cell = B.decode_method(method, manifest)
    cell["evaluator_version"] = EVALUATOR_VERSION
    cell["manifest_amendment_payload_sha256"] = AMENDMENT_PAYLOAD
    cell["quarantined_run_not_admitted"] = QUARANTINED_RUN
    return cell


def assemble(
    cell_dir: Path, manifest: dict[str, Any], amendment: dict[str, Any]
) -> dict[str, Any]:
    report = B.assemble(cell_dir, manifest)
    for method in B.METHODS:
        matches = list(cell_dir.rglob(f"{method}.json"))
        if len(matches) != 1:
            raise ValueError(f"expected one cell for {method}")
        cell = B.load_json(matches[0])
        if cell.get("manifest_amendment_payload_sha256") != AMENDMENT_PAYLOAD:
            raise ValueError(f"{method} was not executed under the amended contract")
        if cell.get("quarantined_run_not_admitted") != QUARANTINED_RUN:
            raise ValueError(f"{method} quarantine binding drift")

    amended_static = static_report(manifest, amendment)
    report["evaluator_version"] = EVALUATOR_VERSION
    report["manifest_amendment_payload_sha256"] = AMENDMENT_PAYLOAD
    report["substrate"] = amended_static
    report["temporal_tcm"] = amended_static["temporal_tcm"]
    report["quarantined_execution"] = amendment["quarantined_execution"]
    report["comparison_boundary"]["tcm_reason"] = "TEMPORAL_TCM_EXACT_BOUND_EXHAUSTED"
    report["comparison_boundary"]["tcm_quality_defined"] = False
    report["comparison_boundary"]["conventional_vs_tcm_quality_ordering_defined"] = False
    report.pop("payload_sha256", None)
    report["payload_sha256"] = B.digest(report)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=B.MANIFEST_PATH)
    parser.add_argument("--amendment", type=Path, default=AMENDMENT_PATH)
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--method", choices=B.METHODS)
    parser.add_argument("--assemble", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = B.load_manifest(args.manifest)
    amendment = load_amendment(args.amendment)
    if sum(bool(x) for x in (args.static_only, args.method, args.assemble)) != 1:
        raise SystemExit("choose exactly one of --static-only, --method, or --assemble")
    if args.static_only:
        result = static_report(manifest, amendment)
    elif args.method:
        result = decode_method(args.method, manifest, amendment)
    else:
        result = assemble(args.assemble, manifest, amendment)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
