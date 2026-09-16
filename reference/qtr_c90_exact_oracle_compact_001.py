#!/usr/bin/env python3
"""Exact reachability compaction for QTR-C90 NumericDD oracle checkpoints.

The compactor changes only node identifiers and removes nodes that are not
reachable from any live factor root. It preserves factor scopes, terminal
values, DD variable labels, branch structure, checkpoint binding, elimination
position, and quality-blindness. No approximation, pruning of reachable state,
reordering, decoder outcome, or injected-error information is used.
"""
from __future__ import annotations

import argparse
import json
import sys
from array import array
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import qtr_c90_exact_decoder_001 as Base
import qtr_c90_exact_oracle_checkpoint_001 as Oracle

EXPERIMENT_ID = Base.EXPERIMENT_ID
COMPACTOR_VERSION = "0.1.0"
_UINT32_MAX = (1 << 32) - 1


def compact_state(
    context: dict[str, Any],
    algebra: str,
    coordinate: int,
    state: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, int]]:
    """Compact a validated checkpoint in place and return exact metrics."""
    Oracle._validate_state(context, algebra, coordinate, state)
    nodes = state["nodes"]
    factors = [(tuple(scope), int(root)) for scope, root in state["factors"]]
    source_count = len(nodes)
    if source_count >= _UINT32_MAX:
        raise ValueError("oracle checkpoint exceeds uint32 compaction index capacity")

    reachable = bytearray(source_count)
    for _, root in factors:
        if not 0 <= root < source_count:
            raise ValueError("oracle factor root outside node table")
        reachable[root] = 1

    # NumericDD nodes are append-only and every D-node is created after its
    # children. Reverse propagation therefore marks the exact transitive
    # closure without recursion or a second large work stack.
    for old_id in range(source_count - 1, -1, -1):
        if reachable[old_id] == 0:
            continue
        node = nodes[old_id]
        kind = node[0]
        if kind == "T":
            continue
        if kind != "D" or len(node) != 4:
            raise ValueError("oracle checkpoint contains unknown DD node")
        low = int(node[2])
        high = int(node[3])
        if not (0 <= low < old_id and 0 <= high < old_id):
            raise ValueError("oracle checkpoint violates DD topological order")
        reachable[low] = 1
        reachable[high] = 1

    remap = array("I", [_UINT32_MAX]) * source_count
    write_id = 0
    for old_id in range(source_count):
        if reachable[old_id] == 0:
            continue
        node = nodes[old_id]
        if node[0] == "T":
            rebuilt = node
        else:
            low = int(remap[int(node[2])])
            high = int(remap[int(node[3])])
            if low == _UINT32_MAX or high == _UINT32_MAX:
                raise AssertionError("reachable child was not remapped")
            rebuilt = ("D", int(node[1]), low, high)
        nodes[write_id] = rebuilt
        remap[old_id] = write_id
        write_id += 1

    compacted_factors: list[tuple[tuple[int, ...], int]] = []
    for scope, old_root in factors:
        new_root = int(remap[old_root])
        if new_root == _UINT32_MAX:
            raise AssertionError("live factor root was removed by compaction")
        compacted_factors.append((scope, new_root))

    del nodes[write_id:]
    state["nodes"] = nodes
    state["factors"] = compacted_factors
    Oracle._validate_state(context, algebra, coordinate, state)

    metrics = {
        "source_node_count": int(source_count),
        "retained_node_count": int(write_id),
        "removed_node_count": int(source_count - write_id),
        "factor_count": len(compacted_factors),
        "next_step": int(state["next_step"]),
    }
    return state, metrics


def _write_result(path: Path, payload: dict[str, Any]) -> None:
    unsigned = dict(payload)
    payload = dict(payload)
    payload["payload_sha256"] = Base.digest(unsigned)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--algebra", required=True)
    parser.add_argument("--coordinate", type=int, required=True)
    parser.add_argument("--checkpoint-in", type=Path, required=True)
    parser.add_argument("--checkpoint-receipt-in", type=Path, required=True)
    parser.add_argument("--checkpoint-out", type=Path, required=True)
    parser.add_argument("--checkpoint-receipt-out", type=Path, required=True)
    parser.add_argument("--report-out", type=Path, required=True)
    parser.add_argument("--advance-to", type=int)
    args = parser.parse_args()

    context = Base.load_c90_context()
    source_receipt = json.loads(args.checkpoint_receipt_in.read_text(encoding="utf-8"))
    state = Oracle.load_checkpoint(
        args.checkpoint_in,
        args.checkpoint_receipt_in,
        context,
        args.algebra,
        args.coordinate,
    )
    start_step = int(state["next_step"])
    if args.advance_to is not None:
        if args.advance_to <= start_step:
            raise ValueError("advance-to must move beyond the input checkpoint")
        state, result = Oracle.advance(
            context,
            args.algebra,
            args.coordinate,
            state=state,
            stop_step=args.advance_to,
        )
        if result is not None:
            raise ValueError("compaction recovery does not admit final-result execution")

    state, metrics = compact_state(context, args.algebra, args.coordinate, state)
    target_receipt = Oracle.save_checkpoint(
        args.checkpoint_out,
        args.checkpoint_receipt_out,
        state,
    )
    report = {
        "experiment_id": EXPERIMENT_ID,
        "compactor_version": COMPACTOR_VERSION,
        "phase": "QUALITY_BLIND_NUMERIC_ORACLE_EXACT_GC",
        "status": "C90_NUMERIC_ORACLE_EXACT_GC_PASS",
        "binding": state["binding"],
        "algebra": args.algebra,
        "coordinate": int(args.coordinate),
        "input_next_step": start_step,
        "output_next_step": int(state["next_step"]),
        "source_checkpoint_sha256": source_receipt["checkpoint_sha256"],
        "source_checkpoint_payload_sha256": source_receipt["payload_sha256"],
        "target_checkpoint_sha256": target_receipt["checkpoint_sha256"],
        "target_checkpoint_payload_sha256": target_receipt["payload_sha256"],
        **metrics,
        "reachable_semantics_changed": False,
        "quality_exposed": False,
        "injected_error_success_used": False,
    }
    _write_result(args.report_out, report)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
