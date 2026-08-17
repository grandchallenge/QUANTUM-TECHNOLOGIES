#!/usr/bin/env python3
"""Canonical committed-evidence projection for TCM-QDEC-COMPARE-001."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def cbytes(x: Any) -> bytes:
    return json.dumps(
        x, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def digest(x: Any) -> str:
    return hashlib.sha256(cbytes(x)).hexdigest()


def method_projection(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "configuration_status": data["configuration_status"],
        "execution_status": data["execution_status"],
        "interface": data["interface"],
        "totals": data["totals"],
        "result_records_sha256": data["result_records_sha256"],
        "oracle_implementation": data.get("oracle_implementation"),
        "stabilizer_basis_rank": data.get("stabilizer_basis_rank"),
        "osd_nominal_candidates_per_invocation": data.get(
            "osd_nominal_candidates_per_invocation"
        ),
        "universal_operation_count": data["universal_operation_count"],
        "timing_authoritative": data["timing_authoritative"],
    }


def project(report: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "experiment_id": report["experiment_id"],
        "evaluator_version": report["evaluator_version"],
        "status": "candidate_executable_not_promoted",
        "manifest": report["manifest"],
        "full_report_payload_sha256": report["payload_sha256"],
        "package_receipt": report["package_receipt"],
        "corpus_receipts": report["corpus_receipts"],
        "surfaces": {},
        "cell_payload_sha256": report["cell_payload_sha256"],
        "detailed_result_record_digests": report["detailed_result_record_digests"],
        "comparison_relation": report["comparison_relation"],
        "claim_boundary": report["claim_boundary"],
        "adjudication": report["adjudication"],
    }
    for surface in ("C18", "C72", "C90"):
        source = report["surfaces"][surface]
        dest: dict[str, Any] = {
            "role": source["role"],
            "conventional": {
                method: method_projection(data)
                for method, data in source["conventional"].items()
            },
        }
        if surface == "C18":
            dest["tcm"] = {
                name: {
                    "status": data["status"],
                    "success_total": data["success_total"],
                    "failure_total": data["failure_total"],
                    "decision_sha256": data["decision_sha256"],
                    "tie_envelope": data["tie_envelope"],
                    "success_by_error_weight": data["success_by_error_weight"],
                }
                for name, data in source["tcm"].items()
            }
            dest["historical_anchors"] = source["historical_anchors"]
            dest["pairwise_quality"] = source["pairwise_quality"]
        else:
            dest["tcm"] = source["tcm"]
            dest["quality_comparison_with_tcm"] = source[
                "quality_comparison_with_tcm"
            ]
        out["surfaces"][surface] = dest
    out["payload_sha256"] = digest(out)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check-evidence", type=Path)
    args = parser.parse_args()

    report = json.loads(args.report.read_text(encoding="utf-8"))
    observed = project(report)
    if args.check_evidence:
        expected = json.loads(args.check_evidence.read_text(encoding="utf-8"))
        if observed != expected:
            raise SystemExit("COMPARE-001 committed evidence projection mismatch")
    text = json.dumps(observed, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
