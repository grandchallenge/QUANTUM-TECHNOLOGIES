#!/usr/bin/env python3
"""Project the full QEC-CIRCUIT-001 exact report into committed candidate evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import qec_circuit_001 as B
import qec_circuit_001_exact as Q

FULL_REPORT_PAYLOAD = "6138aaf0630a5e222c8ae8688d03ce5a48015d506bfc5000e3e19b3f93fb0d6f"
COMPACT_PAYLOAD = "e7c6f3479f5f06b56df95452833e22b59a9db97a9de5d18491c040238f36fed0"
MEASUREMENT_HEAD = "64ef8fd367e5426f4cfd9839cf0ee2817fd65643"
MEASUREMENT_RUN = 32085787908
MEASUREMENT_ARTIFACT = 9306683617
MEASUREMENT_ARTIFACT_DIGEST = "sha256:f851d683b1f442ed2251579d3212f239386134aa1d034bb8c30155eee0c8498d"


def verify_full_report(report: dict[str, Any]) -> None:
    if report.get("experiment_id") != B.EXPERIMENT_ID:
        raise ValueError("QEC-CIRCUIT-001 full report identity mismatch")
    if report.get("status") != "candidate_executable_not_promoted":
        raise ValueError("QEC-CIRCUIT-001 full report status drift")
    if report.get("manifest_payload_sha256") != B.MANIFEST_PAYLOAD:
        raise ValueError("QEC-CIRCUIT-001 base manifest binding drift")
    if report.get("manifest_amendment_payload_sha256") != Q.AMENDMENT_PAYLOAD:
        raise ValueError("QEC-CIRCUIT-001 amendment binding drift")
    claimed = report.get("payload_sha256")
    unsigned = dict(report)
    unsigned.pop("payload_sha256", None)
    observed = B.digest(unsigned)
    if claimed != FULL_REPORT_PAYLOAD or observed != FULL_REPORT_PAYLOAD:
        raise ValueError(
            f"QEC-CIRCUIT-001 full report payload drift: claimed={claimed}, observed={observed}"
        )
    quarantine = report["quarantined_execution"]
    if (
        quarantine["workflow_run"] != Q.QUARANTINED_RUN
        or quarantine["scientific_results_admitted"] is not False
        or quarantine["decoder_result_payloads_inspected_before_repair"] is not False
    ):
        raise ValueError("QEC-CIRCUIT-001 quarantine boundary drift")
    if report["temporal_tcm"]["status"] != "TEMPORAL_TCM_EXACT_BOUND_EXHAUSTED":
        raise ValueError("QEC-CIRCUIT-001 TCM status drift")
    boundary = report["comparison_boundary"]
    if boundary["tcm_quality_defined"] is not False:
        raise ValueError("QEC-CIRCUIT-001 undefined TCM quality was imputed")
    if boundary["conventional_vs_tcm_quality_ordering_defined"] is not False:
        raise ValueError("QEC-CIRCUIT-001 TCM/conventional ordering was imputed")


def project(report: dict[str, Any]) -> dict[str, Any]:
    verify_full_report(report)
    substrate = report["substrate"]
    tcm = report["temporal_tcm"]
    out: dict[str, Any] = {
        "adjudication_candidate": "TEMPORAL_SUBSTRATE_CERTIFIED__CONVENTIONAL_ROWS_COMPLETED__TCM_EXACT_BOUND_EXHAUSTED",
        "authority": {
            "council_issue": 76,
            "disposition": "ADOPT_WITH_AMENDMENTS__AUTHORIZE_QEC_CIRCUIT_001_ONLY",
            "execution_issue": 77,
            "human_steward_authorization_comment": 5321917311,
            "protected_start_main": B.EXPECTED_START,
        },
        "claim_boundary": report["claim_boundary"],
        "comparison_boundary": report["comparison_boundary"],
        "conventional_methods": {},
        "conventional_pairwise": report["conventional_pairwise"],
        "experiment_id": B.EXPERIMENT_ID,
        "manifest_package": {
            "amendment_payload_sha256": Q.AMENDMENT_PAYLOAD,
            "base_manifest_payload_sha256": B.MANIFEST_PAYLOAD,
            "quarantined_results_admitted": False,
            "quarantined_workflow_run": Q.QUARANTINED_RUN,
        },
        "measurement_origin": {
            "artifact_digest": MEASUREMENT_ARTIFACT_DIGEST,
            "bound_full_exact_report_payload_sha256": FULL_REPORT_PAYLOAD,
            "exact_head_artifact": MEASUREMENT_ARTIFACT,
            "head": MEASUREMENT_HEAD,
            "workflow_run": MEASUREMENT_RUN,
        },
        "report_version": "0.1.0",
        "status": "candidate_executable_not_promoted",
        "substrate": {
            "authoritative_histories_in_ambiguous_fibers": substrate["detector_fibers"]["authoritative_histories_in_ambiguous_fibers"],
            "code": "[[18,4,4]]",
            "corpus_record_sha256": substrate["corpus"]["ordered_record_sha256"],
            "corpus_size": substrate["corpus"]["size"],
            "detector_bit_count": 28,
            "detector_map_rank": substrate["detector_map"]["rank"],
            "detector_map_sha256": substrate["detector_map"]["sha256"],
            "distinct_detector_vectors": substrate["detector_fibers"]["distinct_detector_vectors"],
            "fault_coordinate_count": 75,
            "fiber_size_histogram": substrate["detector_fibers"]["fiber_size_histogram"],
            "fibers_with_multiple_terminal_stabilizer_classes": substrate["detector_fibers"]["fibers_with_multiple_terminal_stabilizer_classes"],
            "kind": "three_round_phenomenological_repeated_syndrome_temporal_fixture",
            "sector": "X_error",
        },
        "temporal_tcm": {
            "algebra": "sum_product_bsc_p_0_1",
            "correction_representative_table_sha256": tcm["correction_representative"]["table_sha256"],
            "factor_count": tcm["factor_representation"]["factor_count"],
            "factor_scope_sha256": tcm["factor_representation"]["all_factor_scope_sha256"],
            "frozen_peak_joint_table_cap": tcm["primary_cap"],
            "induced_width": tcm["orders"]["deterministic_min_fill"]["induced_width"],
            "intrinsic_intractability_claim": False,
            "peak_joint_arity": tcm["orders"]["deterministic_min_fill"]["peak_joint_arity"],
            "predicted_peak_joint_table_entries": tcm["orders"]["deterministic_min_fill"]["peak_joint_table_entries"],
            "primary_order": "deterministic_min_fill",
            "quality_defined": False,
            "status": tcm["status"],
            "stopped_before_table_materialization": True,
        },
    }
    for method, cell in report["conventional_methods"].items():
        totals = cell["totals"]
        out["conventional_methods"][method] = {
            "by_elementary_fault_weight": cell["by_elementary_fault_weight"],
            "correction_valued": totals["correction_valued"],
            "declared_failures": totals["declared_failures"],
            "detector_consistent": totals["detector_consistent"],
            "detector_inconsistent": totals["detector_inconsistent"],
            "interface_status": cell["interface"]["status"],
            "oracle_failure": totals["oracle_failure"],
            "oracle_success": totals["oracle_success"],
            "terminal_syndrome_consistent": totals["terminal_syndrome_consistent"],
            "terminal_syndrome_inconsistent": totals["terminal_syndrome_inconsistent"],
        }
    out["payload_sha256"] = B.digest(out)
    if out["payload_sha256"] != COMPACT_PAYLOAD:
        raise AssertionError(
            f"QEC-CIRCUIT-001 compact payload drift: {out['payload_sha256']}"
        )
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check-evidence", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    projected = project(report)
    rendered = json.dumps(projected, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    if args.check_evidence:
        committed = json.loads(args.check_evidence.read_text(encoding="utf-8"))
        if committed != projected:
            raise SystemExit("QEC-CIRCUIT-001 committed evidence differs from deterministic projection")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
