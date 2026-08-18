#!/usr/bin/env python3
"""Deterministic compact evidence projector for QEC-CIRCUIT-002."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_MANIFEST = "9ba84244f828bc0c4f9f128e54d2c89693930c2280540f9dc420ae13e964aa29"
EXPECTED_FULL = "90d73b06e3778fea7322435f1ff7db74fc3cb708038057ef338643082aa25c28"
EXPECTED_COMPACT = "cb9915e3d9bb32dc5abf1705c3dc7709082b79e3c5b91b391fb2aca0e632fcc3"


def cbytes(x: Any) -> bytes:
    return json.dumps(
        x, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def digest(x: Any) -> str:
    return hashlib.sha256(cbytes(x)).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def project(full: dict[str, Any]) -> dict[str, Any]:
    if full["experiment_id"] != "QEC-CIRCUIT-002":
        raise ValueError("QEC-CIRCUIT-002 full report identity drift")
    if full["manifest_payload_sha256"] != EXPECTED_MANIFEST:
        raise ValueError("QEC-CIRCUIT-002 manifest binding drift")
    if full["payload_sha256"] != EXPECTED_FULL:
        raise ValueError("QEC-CIRCUIT-002 full report payload drift")
    if full["status"] != "candidate_executable_not_promoted":
        raise ValueError("QEC-CIRCUIT-002 scientific status drift")
    if full["adjudication_candidate"] != "TEMPORAL_PREDECLARED_DECOMPOSITION_FAMILY_EXHAUSTED":
        raise ValueError("QEC-CIRCUIT-002 adjudication drift")

    semantic = full["semantic_equivalence"]
    compact_semantic = {
        "R1_TERMINAL_DIRECT_AUX": {
            "status": semantic["R1_TERMINAL_DIRECT_AUX"]["status"],
            "terminal_relation_receipt_sha256": semantic["R1_TERMINAL_DIRECT_AUX"]["terminal_relation"]["satisfying_truth_table_sha256"],
            "selector_receipt_sha256": semantic["R1_TERMINAL_DIRECT_AUX"]["selector_rewrite"]["receipt_sha256"],
        },
        "R2_TERMINAL_CHAIN_AUX": {
            "status": semantic["R2_TERMINAL_CHAIN_AUX"]["status"],
            "terminal_chain_receipt_sha256": semantic["R2_TERMINAL_CHAIN_AUX"]["terminal_chain"]["satisfying_truth_table_sha256"],
            "selector_receipt_sha256": semantic["R2_TERMINAL_CHAIN_AUX"]["selector_rewrite"]["receipt_sha256"],
        },
        "R3_CAUSAL_STATE_CHAIN": {
            "status": semantic["R3_CAUSAL_STATE_CHAIN"]["status"],
            "terminal_chain_receipt_sha256": semantic["R3_CAUSAL_STATE_CHAIN"]["terminal_chain"]["satisfying_truth_table_sha256"],
            "selector_receipt_sha256": semantic["R3_CAUSAL_STATE_CHAIN"]["selector_rewrite"]["receipt_sha256"],
            "syndrome_increment_relations_checked": semantic["R3_CAUSAL_STATE_CHAIN"]["syndrome_increment"]["relations_checked"],
            "syndrome_increment_receipt_sha256": semantic["R3_CAUSAL_STATE_CHAIN"]["syndrome_increment"]["receipt_sha256"],
            "detector_assignments_checked": semantic["R3_CAUSAL_STATE_CHAIN"]["detector_rewrite"]["assignments_checked"],
            "detector_rewrite_receipt_sha256": semantic["R3_CAUSAL_STATE_CHAIN"]["detector_rewrite"]["receipt_sha256"],
        },
    }

    compact = {
        "report_version": "0.1.0",
        "experiment_id": "QEC-CIRCUIT-002",
        "status": "candidate_executable_not_promoted",
        "manifest_payload_sha256": EXPECTED_MANIFEST,
        "full_exact_report_payload_sha256": EXPECTED_FULL,
        "adjudication_candidate": full["adjudication_candidate"],
        "semantic_equivalence": compact_semantic,
        "structural_rows": full["structural_rows"],
        "quality_boundary": full["quality_boundary"],
        "transported_conventional_results": full["transported_conventional_results"],
        "claim_boundary": full["claim_boundary"],
    }
    compact["payload_sha256"] = digest(compact)
    if compact["payload_sha256"] != EXPECTED_COMPACT:
        raise ValueError("QEC-CIRCUIT-002 compact evidence payload drift")
    return compact


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    compact = project(load_json(args.input))
    rendered = json.dumps(compact, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
