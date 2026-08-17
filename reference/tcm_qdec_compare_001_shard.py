#!/usr/bin/env python3
"""Deterministic sharded execution/assembly for TCM-QDEC-COMPARE-001."""

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

import qldpc_fixture_002 as F2
import tcm_qdec_compare_001 as C

SURFACES = ("C18", "C72", "C90")
METHODS = ("BP_MIN_SUM", "BP_OSD_CS_7", "BP_SUM_PRODUCT")


def c18_code_and_corpus():
    hx, hz, _stabilizers, corpus, _tables, _ties = C.c18_context()
    return hx, hz, corpus, 18


def large_code_and_corpus(surface: str, manifest: dict[str, Any]):
    n = int(surface[1:])
    hx, hz, _ = C.code_from_001b(n)
    records = C.generate_large_corpus_records(n, manifest)
    corpus = [F2.b2i(x["error"]) for x in records]
    return hx, hz, corpus, n


def execute_cell(surface: str, method: str) -> dict[str, Any]:
    """Execute a cell only through the exact basis-reduction scorer."""
    import tcm_qdec_compare_001_exact_cell as exact_cell

    return exact_cell.execute_cell(surface, method)


def load_cells(root: Path) -> dict[tuple[str, str], dict[str, Any]]:
    found: dict[tuple[str, str], dict[str, Any]] = {}
    for path in sorted(root.rglob("*.json")):
        try:
            cell = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if cell.get("experiment_id") != C.EXPERIMENT_ID:
            continue
        surface = cell.get("surface")
        method = cell.get("method")
        if surface not in SURFACES or method not in METHODS:
            continue
        key = (surface, method)
        if key in found:
            raise ValueError(f"duplicate cell artifact: {key}")
        if cell.get("manifest_payload_sha256") != C.MANIFEST_PAYLOAD:
            raise ValueError(f"manifest drift in cell {key}")
        if len(cell.get("outcomes", [])) != int(cell.get("corpus_size", -1)):
            raise ValueError(f"outcome count mismatch in cell {key}")
        found[key] = cell
    expected = {(s, m) for s in SURFACES for m in METHODS}
    missing = sorted(expected - set(found))
    if missing:
        raise ValueError(f"missing COMPARE-001 cell artifacts: {missing}")
    return found


def assemble(root: Path) -> dict[str, Any]:
    manifest = C.load_manifest()
    cells = load_cells(root)
    package_receipts = {C.digest(cell["package_receipt"]) for cell in cells.values()}
    if len(package_receipts) != 1:
        raise ValueError("historical package receipt differs across shards")
    package = next(iter(cells.values()))["package_receipt"]
    corpus_receipts = C.materialize_corpora(manifest)

    hx18, hz18, stabilizers18, corpus18, tcm_tables, tie_report = C.c18_context()
    tcm_rows, tcm_outcomes = C.tcm_c18_rows(
        corpus18, hz18, stabilizers18, tcm_tables, tie_report
    )

    surfaces: dict[str, Any] = {
        "C18": {
            "role": "matched_quality_head_to_head",
            "tcm": tcm_rows,
            "historical_anchors": {
                "exact_lookup_success_total": 240,
                "greedy_success_total": 125,
            },
            "conventional": {},
            "pairwise_quality": [],
        },
        "C72": {
            "role": "conventional_reach_status_only",
            "tcm": {"status": "SHARED_DECODER_INTERFACE_NOT_CERTIFIED"},
            "conventional": {},
            "quality_comparison_with_tcm": "COMPARISON_CELL_UNDEFINED",
        },
        "C90": {
            "role": "conventional_reach_status_only",
            "tcm": {"status": "NOT_REACHED_EXACT_COMPILATION_BOUND"},
            "conventional": {},
            "quality_comparison_with_tcm": "COMPARISON_CELL_UNDEFINED",
        },
    }
    detail_digests: dict[str, str] = {}
    for surface in SURFACES:
        for method in METHODS:
            cell = cells[(surface, method)]
            surfaces[surface]["conventional"][method] = cell["summary"]
            detail_digests[f"{surface}/{method}"] = cell["result_records_sha256"]

    for method in METHODS:
        conv = cells[("C18", method)]["outcomes"]
        for algebra, tcm in tcm_outcomes.items():
            surfaces["C18"]["pairwise_quality"].append(
                C.pairwise_quality(method, conv, f"TCM::{algebra}", tcm)
            )

    mandatory = ("BP_MIN_SUM", "BP_OSD_CS_7")
    c18_mandatory_complete = all(
        cells[("C18", method)]["summary"]["execution_status"] == "COMPLETED"
        for method in mandatory
    )
    c90_reached = [
        method
        for method in METHODS
        if cells[("C90", method)]["summary"]["execution_status"] == "COMPLETED"
    ]
    secondary = ["TCM_SHARED_DECODER_INTERFACE_NOT_CERTIFIED_ON_C72"]
    if c90_reached:
        secondary.append("CONVENTIONAL_BASELINES_REACHED_C90__TCM_NOT_REACHED_EXACT_BOUND")
    else:
        secondary.append("CONVENTIONAL_BASELINE_NOT_REACHED_ON_C90")

    report: dict[str, Any] = {
        "experiment_id": C.EXPERIMENT_ID,
        "evaluator_version": C.EVALUATOR_VERSION,
        "execution_mode": "deterministic_3x3_cell_shard",
        "status": "candidate_executable_not_promoted",
        "manifest": {
            "path": str(C.MANIFEST_PATH.relative_to(ROOT)),
            "first_commit": C.MANIFEST_COMMIT,
            "payload_sha256": C.MANIFEST_PAYLOAD,
        },
        "package_receipt": package,
        "corpus_receipts": corpus_receipts,
        "surfaces": surfaces,
        "detailed_result_record_digests": detail_digests,
        "cell_payload_sha256": {
            f"{s}/{m}": cells[(s, m)]["cell_payload_sha256"]
            for s in SURFACES for m in METHODS
        },
        "comparison_relation": manifest["comparison_relation"],
        "claim_boundary": manifest["claim_boundary"],
        "adjudication": {
            "c18_shared_interface_completed": c18_mandatory_complete,
            "c72_tcm_quality_defined": False,
            "c90_tcm_quality_defined": False,
            "c90_conventional_reached_rows": c90_reached,
            "cross_surface_winner_defined": False,
            "primary_outcome": (
                "SHARED_INTERFACE_COMPARISON_COMPLETED_ON_C18"
                if c18_mandatory_complete
                else "CONVENTIONAL_BASELINE_INTERFACE_NOT_CERTIFIED"
            ),
            "secondary_outcomes": secondary,
        },
    }
    report["payload_sha256"] = C.digest(report)
    return report


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--surface", choices=SURFACES)
    p.add_argument("--method", choices=METHODS)
    p.add_argument("--cell-output", type=Path)
    p.add_argument("--assemble", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--check-evidence", type=Path)
    args = p.parse_args()

    if args.assemble:
        result = assemble(args.assemble)
    else:
        if not args.surface or not args.method or not args.cell_output:
            p.error("cell mode requires --surface --method --cell-output")
        result = execute_cell(args.surface, args.method)
        args.cell_output.parent.mkdir(parents=True, exist_ok=True)
        args.cell_output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.check_evidence:
        expected = json.loads(args.check_evidence.read_text(encoding="utf-8"))
        if result != expected:
            raise SystemExit("COMPARE-001 exact evidence replay mismatch")

    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
