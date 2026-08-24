#!/usr/bin/env python3
"""Hosted orchestrator for TCM-C72-INTERFACE-001.

Worker count and host size are operational choices only. Scientific semantics are
frozen in the manifest and every owned input evaluates all 4096 logical classes.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVALUATOR = ROOT / "reference" / "tcm_c72_interface_001.py"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def meminfo() -> dict[str, int]:
    path = Path("/proc/meminfo")
    if not path.exists():
        return {}
    out: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if ":" not in line:
            continue
        key, rest = line.split(":", 1)
        fields = rest.strip().split()
        if fields and fields[0].isdigit():
            value = int(fields[0])
            if len(fields) > 1 and fields[1].lower() == "kb":
                value *= 1024
            out[key] = value
    return out


def host_receipt() -> dict[str, Any]:
    disk = shutil.disk_usage(ROOT)
    memory = meminfo()
    return {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
        "mem_total_bytes": memory.get("MemTotal"),
        "mem_available_bytes": memory.get("MemAvailable"),
        "disk_total_bytes": disk.total,
        "disk_free_bytes": disk.free,
        "historical_experimental_caps_are_scientific_stop_rules": False,
    }


def run_command(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--workers", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    if args.workers < 1:
        parser.error("--workers must be at least one")

    observed_head = git_head()
    if observed_head != args.expected_head:
        raise RuntimeError(
            f"exact-head mismatch: expected {args.expected_head}, observed {observed_head}"
        )

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    preflight = output_dir / "TCM-C72-INTERFACE-001-preflight.json"
    aggregate = output_dir / "TCM-C72-INTERFACE-001-report.json"
    receipt_path = output_dir / "TCM-C72-INTERFACE-001-hosted-receipt.json"

    started = time.time()
    receipt: dict[str, Any] = {
        "experiment_id": "TCM-C72-INTERFACE-001",
        "source_commit": observed_head,
        "workers": args.workers,
        "host": host_receipt(),
        "scientific_resource_stop_rule": False,
        "status": "RUNNING",
    }

    try:
        run_command(
            [
                sys.executable,
                str(EVALUATOR),
                "--mode",
                "preflight",
                "--output",
                str(preflight),
            ]
        )

        shard_paths = [
            output_dir / f"TCM-C72-INTERFACE-001-shard-{index:04d}-of-{args.workers:04d}.json"
            for index in range(args.workers)
        ]

        def run_one(index: int) -> None:
            run_command(
                [
                    sys.executable,
                    str(EVALUATOR),
                    "--mode",
                    "shard",
                    "--shard-index",
                    str(index),
                    "--shard-count",
                    str(args.workers),
                    "--output",
                    str(shard_paths[index]),
                ]
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(run_one, index) for index in range(args.workers)]
            for future in concurrent.futures.as_completed(futures):
                future.result()

        command = [
            sys.executable,
            str(EVALUATOR),
            "--mode",
            "aggregate",
            "--output",
            str(aggregate),
        ]
        for shard_path in shard_paths:
            command.extend(["--shard", str(shard_path)])
        run_command(command)

        receipt.update(
            {
                "status": "COMPLETE",
                "elapsed_seconds": time.time() - started,
                "preflight_sha256": sha256_file(preflight),
                "aggregate_sha256": sha256_file(aggregate),
                "shard_count": len(shard_paths),
                "shard_sha256": {
                    path.name: sha256_file(path) for path in shard_paths
                },
                "host_after": host_receipt(),
            }
        )
    except Exception as exc:
        receipt.update(
            {
                "status": "OPERATIONAL_EXECUTION_INCOMPLETE",
                "elapsed_seconds": time.time() - started,
                "exception_class": exc.__class__.__name__,
                "exception_message": str(exc),
                "host_after": host_receipt(),
                "scientific_infeasibility_claim": False,
            }
        )
        receipt_path.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        raise

    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
