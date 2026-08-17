#!/usr/bin/env python3
"""Exact one-cell scorer for TCM-QDEC-COMPARE-001.

This adapter preserves the frozen decoder calls and comparison schema but tests
stabilizer-row-space membership by deterministic GF(2) basis reduction instead
of materializing the full row span. The two predicates are exactly equivalent.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import qldpc_fixture_002 as F2
import tcm_qdec_compare_001 as C

SURFACES = ("C18", "C72", "C90")
METHODS = ("BP_MIN_SUM", "BP_OSD_CS_7", "BP_SUM_PRODUCT")


def in_row_span(value: int, rows_or_basis: list[int], *, already_basis: bool = False) -> bool:
    """Return exact GF(2) row-space membership by echelon reduction."""
    v = int(value)
    basis = rows_or_basis if already_basis else F2.basis(rows_or_basis)
    for row in basis:
        pivot = row.bit_length() - 1
        if pivot >= 0 and ((v >> pivot) & 1):
            v ^= row
    return v == 0


def surface_context(surface: str, manifest: dict[str, Any]):
    if surface == "C18":
        hx, hz, _stabilizers, corpus, _tables, _ties = C.c18_context()
        return hx, hz, corpus, 18
    n = int(surface[1:])
    hx, hz, _ = C.code_from_001b(n)
    corpus_records = C.generate_large_corpus_records(n, manifest)
    corpus = [F2.b2i(x["error"]) for x in corpus_records]
    return hx, hz, corpus, n


def decode_exact_cell(method: str, hx: list[int], hz: list[int], corpus: list[int], n: int):
    import numpy as np

    h_numpy = C.int_rows_to_numpy(hz, n)
    decoder = C.make_decoder(method, h_numpy, n)
    interface = C.certify_decoder_interface(method, decoder)
    stabilizer_basis = F2.basis(hx)
    rank_hz = len(F2.basis(hz))
    osd_nominal = (n - rank_hz) + math.comb(7, 2) if method == "BP_OSD_CS_7" else None

    results: list[dict[str, Any]] = []
    outcomes: list[bool | None] = []
    totals = {
        "inputs": len(corpus),
        "correction_valued": 0,
        "declared_failures": 0,
        "oracle_success": 0,
        "oracle_failure": 0,
        "syndrome_consistent": 0,
        "syndrome_inconsistent": 0,
        "bp_iterations_total": 0,
        "bp_converged_count": 0,
        "bp_nonconverged_count": 0,
        "osd_invocation_count": 0,
        "osd_nominal_candidates_total": 0,
        "correction_weight_total": 0,
    }
    shell: dict[str, dict[str, int]] = {}

    for index, error in enumerate(corpus):
        syn = F2.syndrome(error, hz)
        syn_np = np.array([(syn >> i) & 1 for i in range(len(hz))], dtype=np.uint8)
        try:
            correction_np = decoder.decode(syn_np)
            correction = sum(
                (int(bit) & 1) << i for i, bit in enumerate(correction_np.tolist())
            )
            iterations = int(decoder.iter)
            converged = bool(int(decoder.converge))
            consistent = F2.syndrome(correction, hz) == syn
            correct = consistent and in_row_span(
                error ^ correction, stabilizer_basis, already_basis=True
            )
            osd_invoked = method == "BP_OSD_CS_7" and not converged
            totals["correction_valued"] += 1
            totals["oracle_success" if correct else "oracle_failure"] += 1
            totals["syndrome_consistent" if consistent else "syndrome_inconsistent"] += 1
            totals["bp_iterations_total"] += iterations
            totals["bp_converged_count" if converged else "bp_nonconverged_count"] += 1
            totals["correction_weight_total"] += correction.bit_count()
            if osd_invoked:
                totals["osd_invocation_count"] += 1
                totals["osd_nominal_candidates_total"] += int(osd_nominal)
            outcomes.append(correct)
            record = {
                "index": index,
                "status": "CORRECTION_VALUED",
                "error": F2.i2b(error, n),
                "error_weight": error.bit_count(),
                "syndrome": F2.i2b(syn, len(hz)),
                "correction": F2.i2b(correction, n),
                "correction_weight": correction.bit_count(),
                "syndrome_consistent": consistent,
                "oracle_correct": correct,
                "bp_iterations": iterations,
                "bp_converged": converged,
                "osd_invoked": osd_invoked,
                "osd_nominal_candidates": int(osd_nominal) if osd_invoked else 0,
            }
        except Exception as exc:
            totals["declared_failures"] += 1
            outcomes.append(None)
            record = {
                "index": index,
                "status": "DECLARED_FAILURE",
                "error": F2.i2b(error, n),
                "error_weight": error.bit_count(),
                "syndrome": F2.i2b(syn, len(hz)),
                "exception_class": exc.__class__.__name__,
                "exception_message": str(exc),
            }
        results.append(record)
        w = str(error.bit_count())
        bucket = shell.setdefault(
            w, {"inputs": 0, "correction_valued": 0, "oracle_success": 0}
        )
        bucket["inputs"] += 1
        if record["status"] == "CORRECTION_VALUED":
            bucket["correction_valued"] += 1
            bucket["oracle_success"] += int(record["oracle_correct"])

    if totals["bp_iterations_total"] > len(corpus) * 10000:
        raise AssertionError(f"{method} BP iteration budget exceeded")

    return (
        {
            "configuration_status": "CERTIFIED",
            "interface": interface,
            "execution_status": "COMPLETED",
            "totals": totals,
            "success_by_error_weight": shell,
            "result_records_sha256": C.digest(results),
            "result_record_count": len(results),
            "osd_nominal_candidates_per_invocation": osd_nominal,
            "oracle_implementation": "GF2_BASIS_REDUCTION_EQUIVALENT_TO_ROWSPAN_MEMBERSHIP",
            "stabilizer_basis_rank": len(stabilizer_basis),
            "universal_operation_count": "NOT_DEFINED",
            "timing_authoritative": False,
        },
        results,
        outcomes,
    )


def execute_cell(surface: str, method: str) -> dict[str, Any]:
    if surface not in SURFACES or method not in METHODS:
        raise ValueError("unauthorized COMPARE-001 cell")
    manifest = C.load_manifest()
    package = C.package_receipt()
    hx, hz, corpus, n = surface_context(surface, manifest)
    try:
        summary, records, outcomes = decode_exact_cell(method, hx, hz, corpus, n)
    except (TypeError, ValueError, AttributeError, RuntimeError) as exc:
        summary = {
            "configuration_status": "BASELINE_INTERFACE_NOT_CERTIFIED",
            "interface": {
                "status": "BASELINE_INTERFACE_NOT_CERTIFIED",
                "exception_class": exc.__class__.__name__,
                "exception_message": str(exc),
            },
            "execution_status": "NOT_REACHED_INTERFACE_NOT_CERTIFIED",
            "totals": {
                "inputs": len(corpus),
                "correction_valued": 0,
                "declared_failures": 0,
                "oracle_success": 0,
                "oracle_failure": 0,
                "syndrome_consistent": 0,
                "syndrome_inconsistent": 0,
                "bp_iterations_total": 0,
                "bp_converged_count": 0,
                "bp_nonconverged_count": 0,
                "osd_invocation_count": 0,
                "osd_nominal_candidates_total": 0,
                "correction_weight_total": 0,
            },
            "success_by_error_weight": {},
            "result_records_sha256": C.digest([]),
            "result_record_count": 0,
            "osd_nominal_candidates_per_invocation": None,
            "oracle_implementation": "GF2_BASIS_REDUCTION_EQUIVALENT_TO_ROWSPAN_MEMBERSHIP",
            "stabilizer_basis_rank": len(F2.basis(hx)),
            "universal_operation_count": "NOT_DEFINED",
            "timing_authoritative": False,
        }
        records = []
        outcomes = [None] * len(corpus)

    record_digest = C.digest(records)
    payload_subject = {
        "surface": surface,
        "method": method,
        "package_receipt": package,
        "corpus_size": len(corpus),
        "summary": summary,
        "outcomes": outcomes,
        "result_records_sha256": record_digest,
    }
    return {
        "experiment_id": C.EXPERIMENT_ID,
        "manifest_payload_sha256": C.MANIFEST_PAYLOAD,
        **payload_subject,
        "cell_payload_sha256": C.digest(payload_subject),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--surface", required=True, choices=SURFACES)
    p.add_argument("--method", required=True, choices=METHODS)
    p.add_argument("--cell-output", required=True, type=Path)
    args = p.parse_args()
    result = execute_cell(args.surface, args.method)
    args.cell_output.parent.mkdir(parents=True, exist_ok=True)
    args.cell_output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
