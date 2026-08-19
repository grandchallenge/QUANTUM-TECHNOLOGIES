#!/usr/bin/env python3
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

import qldpc_scale_001b as scale001b
import qec_circuit_002 as circuit002

ORIGINAL_PEAK_CAP = 1 << 20
EXPECTED = {
    "C72": 18,
    "C90": 25,
    "R0_BASELINE_107_FACTOR": 34,
    "R1_TERMINAL_DIRECT_AUX": 36,
    "R2_TERMINAL_CHAIN_AUX": 36,
    "R3_CAUSAL_STATE_CHAIN": 36,
}


def peak_entries(width: int) -> int:
    return 1 << (width + 1)


def multiplier_needed(width: int) -> float:
    return peak_entries(width) / ORIGINAL_PEAK_CAP


def load_job(path: Path) -> dict[str, Any]:
    job = json.loads(path.read_text(encoding="utf-8"))
    if job.get("workload") != "compute_requal_preflight":
        raise ValueError("wrong workload")
    if job.get("scientific_execution_authorized") is not False:
        raise ValueError("preflight may not authorize scientific execution")
    multiplier = job.get("nominal_envelope_multiplier")
    if not isinstance(multiplier, int) or multiplier <= 0:
        raise ValueError("nominal_envelope_multiplier must be a positive integer")
    return job


def scale_widths() -> dict[str, int]:
    manifest = scale001b.load_manifest(ROOT / scale001b.MANIFEST_PATH)
    rungs = {int(row["n"]): row for row in manifest["ladder"]}
    out = {}
    for n in (72, 90):
        code = scale001b.construct_rung(rungs[n])
        audit = scale001b.order_audit(code["scopes"])
        out[f"C{n}"] = int(audit["widths"]["min_fill"])
    return out


def temporal_widths() -> dict[str, int]:
    circuit002.load_manifest()
    out = {}
    for rep in (
        "R0_BASELINE_107_FACTOR",
        "R1_TERMINAL_DIRECT_AUX",
        "R2_TERMINAL_CHAIN_AUX",
        "R3_CAUSAL_STATE_CHAIN",
    ):
        variable_count, scopes = circuit002.representation_scopes(rep)
        result = circuit002.elimination_order(
            circuit002.primal_graph(scopes, variable_count),
            "deterministic_min_fill",
        )
        out[rep] = int(result["induced_width"])
    return out


def evaluate(job: dict[str, Any]) -> dict[str, Any]:
    widths = {**scale_widths(), **temporal_widths()}
    if widths != EXPECTED:
        raise ValueError(f"protected structural identity drift: {widths}")
    multiplier = int(job["nominal_envelope_multiplier"])
    nominal_cap = ORIGINAL_PEAK_CAP * multiplier
    rows = []
    for name, width in widths.items():
        peak = peak_entries(width)
        rows.append({
            "target": name,
            "protected_min_fill_width": width,
            "predicted_peak_joint_table_entries": peak,
            "multiplier_needed_vs_original_peak_cap": multiplier_needed(width),
            "inside_nominal_entry_cap": peak <= nominal_cap,
            "physical_materialization_authorized": False,
        })
    return {
        "schema_version": 1,
        "experiment_id": job["experiment_id"],
        "status": "GREEN_ENGINEERING_PREQUALIFICATION",
        "original_peak_entry_cap": ORIGINAL_PEAK_CAP,
        "nominal_envelope_multiplier": multiplier,
        "nominal_peak_entry_cap": nominal_cap,
        "rows": rows,
        "c90_crosses_nominal_entry_cap": next(
            row["inside_nominal_entry_cap"] for row in rows if row["target"] == "C90"
        ),
        "temporal_r0_crosses_nominal_entry_cap": next(
            row["inside_nominal_entry_cap"]
            for row in rows
            if row["target"] == "R0_BASELINE_107_FACTOR"
        ),
        "physical_memory_eligibility_decided": False,
        "physical_memory_note": (
            "Entry-count requalification is not permission to materialize. "
            "Observed Colab RAM and representation-specific storage must be checked "
            "under a separately authorized exact-execution contract."
        ),
        "scientific_execution_performed": False,
        "scientific_disposition_authorized": False,
        "claim_boundary": job["claim_boundary"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(load_job(args.job))
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": result["status"],
        "c90_crosses_nominal_entry_cap": result["c90_crosses_nominal_entry_cap"],
        "temporal_r0_crosses_nominal_entry_cap": result["temporal_r0_crosses_nominal_entry_cap"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())