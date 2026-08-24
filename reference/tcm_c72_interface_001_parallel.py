#!/usr/bin/env python3
"""Execution-only exact parallel wrapper for TCM-C72-INTERFACE-001.

This module changes no decoder mathematics. It partitions the already-frozen
4096 logical classes across local CPU worker processes and returns records in
exact logical-class order before applying the frozen decision rule.
"""

from __future__ import annotations

import argparse
import hashlib
import multiprocessing
import os
from pathlib import Path
from typing import Any

import tcm_c72_interface_001 as C72

_PARENT_CONTEXT: dict[str, Any] | None = None
_WORKER_SYNDROME: int | None = None


def _worker_init(full_hz_syndrome: int) -> None:
    global _WORKER_SYNDROME
    _WORKER_SYNDROME = int(full_hz_syndrome)


def _class_worker(logical_class: int) -> dict[str, Any]:
    if _PARENT_CONTEXT is None or _WORKER_SYNDROME is None:
        raise RuntimeError("parallel C72 worker not initialized")
    return C72.c72_class_record(_PARENT_CONTEXT, _WORKER_SYNDROME, int(logical_class))


def parallel_decode_c72_syndrome(
    full_hz_syndrome: int,
    channel_metadata: dict[str, str],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Exact C72 decoder with execution-only class parallelism.

    The injected error is deliberately not an argument. The output is defined
    by the same 4096 class records and the same frozen decision rule as the
    serial implementation.
    """
    if channel_metadata != C72.CHANNEL_METADATA:
        raise ValueError("channel metadata drift")
    context = context or C72.load_c72_context()
    if not (0 <= int(full_hz_syndrome) < (1 << len(context["code"]["hz"]))):
        raise ValueError("syndrome width overflow")

    worker_count = min(max(1, int(os.environ.get("TCM_C72_WORKERS", "4"))), os.cpu_count() or 1)
    logical_classes = list(range(1 << 12))

    global _PARENT_CONTEXT
    _PARENT_CONTEXT = context
    methods = multiprocessing.get_all_start_methods()
    if worker_count > 1 and "fork" in methods:
        mp = multiprocessing.get_context("fork")
        with mp.Pool(
            processes=worker_count,
            initializer=_worker_init,
            initargs=(int(full_hz_syndrome),),
        ) as pool:
            records = pool.map(_class_worker, logical_classes, chunksize=4)
    else:
        records = [
            C72.c72_class_record(context, int(full_hz_syndrome), logical_class)
            for logical_class in logical_classes
        ]

    if [int(record["logical_class"]) for record in records] != logical_classes:
        raise AssertionError("parallel logical-class ordering drift")

    hasher = hashlib.sha256()
    for record in records:
        hasher.update(C72.cbytes(record))
        hasher.update(b"\n")

    return {
        "status": "CORRECTION_VALUED",
        "logical_classes_evaluated": 4096,
        "class_score_stream_sha256": hasher.hexdigest(),
        "decisions": C72.decision_from_class_records(records, 72),
    }


def run_parallel_shard(shard_index: int, shard_count: int) -> dict[str, Any]:
    original = C72.decode_c72_syndrome
    C72.decode_c72_syndrome = parallel_decode_c72_syndrome
    try:
        report = C72.run_shard(shard_index, shard_count)
    finally:
        C72.decode_c72_syndrome = original
    report["engineering_diagnostics"]["execution_wrapper"] = "exact_fork_parallel_logical_classes"
    report["engineering_diagnostics"]["requested_worker_count"] = int(
        os.environ.get("TCM_C72_WORKERS", "4")
    )
    report["payload_sha256"] = C72.digest({k: v for k, v in report.items() if k != "payload_sha256"})
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--shard-count", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run_parallel_shard(args.shard_index, args.shard_count)
    C72.write_json(args.output, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
