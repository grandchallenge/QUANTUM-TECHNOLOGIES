#!/usr/bin/env python3
"""Verify one exact, frozen, quality-blind C90 Colab class shard.

This script NEVER computes, compares, logs or publishes decoding success.
It accepts only the five immutable returned files from the first actual
Colab native C90 class-0 shard (2026-11-19).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ACTIVATION = "0c1f5591a097adc285dec4cbfc320eeebd2c65d3"
ORCHESTRATION = "675865123437c3d6c908c7a3af337fd4023c5d0b"
ALGEBRA = "min_plus_hamming"
CLASS = 0
INPUTS = 347
EXPECTED_FILES = {
    "rows-min_plus_hamming-class-0.jsonl": "d186b8392bbfb6aedf03ddb9cc1474486c7b4a4090da739a7e6f6e2c3b0250cc",
    "receipt-min_plus_hamming-class-0.json": "ee57897c39b8ea35fa9a5a3949a2ad711d888d9287c4fb34e9538eb111025f26",
    "external-shard.json": "8ecfb5b23dde0a84e56d25e7f6af8d7c07fd90211acea2c5a46f477018b30909",
    "time.txt": "29e2296cf5938a727d479597e43713b45016c29da109dee118c0f1e980cfd372",
    "worker-state.json": "a203053d178dfac76345de4428dec3ddb58c335945e872d5b217c40c8ad4c156",
}
ROW_KEYS = frozenset({
    "status", "algebra_id", "selector_index", "selector_coordinate",
    "reachable_nodes", "peak_live_values", "minimum_weight",
    "minimum_representative_hex", "canonical_hex", "quality_exposed",
})


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fail_unless(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def verify(path: Path) -> dict:
    path = path.resolve(strict=True)
    files: dict[str, Path] = {}
    for name, wanted in EXPECTED_FILES.items():
        source = path / name
        fail_unless(source.is_file() and not source.is_symlink(), "missing or linked artifact: " + name)
        fail_unless(sha256(source) == wanted, "source artifact SHA-256 drift: " + name)
        files[name] = source

    worker = json.loads(files["worker-state.json"].read_text())
    receipt = json.loads(files["receipt-min_plus_hamming-class-0.json"].read_text())
    marker = json.loads(files["external-shard.json"].read_text())

    fail_unless(
        worker.get("stage") == "SINGLE_SHARD_COMPLETE"
        and marker.get("status") == "EXTERNAL_SELECTOR_SHARD_COMPLETE"
        and receipt.get("status") == "C90_ACTIVATED_SELECTOR_SHARD_EVALUATED",
        "missing scientific terminal receipt",
    )
    fail_unless(
        worker.get("quality_exposed") is False
        and receipt.get("quality_exposed") is False
        and marker.get("quality_exposed") is False
        and receipt.get("corrections_fixed") is False
        and receipt.get("independent_scoring_performed") is False
        and receipt.get("matched_comparison_performed") is False
        and marker.get("github_hosted_selector_values_used") is False
        and receipt.get("scientific_semantics_changed") is False,
        "quality/ordering/scientific-integrity boundary violated",
    )
    fail_unless(
        worker.get("activation_head") == receipt.get("activation_head") ==
        marker.get("activation_head") == ACTIVATION
        and worker.get("source_head") == receipt.get("orchestration_head") ==
        marker.get("runner_head") == ORCHESTRATION,
        "source/activation head identity drift",
    )
    fail_unless(
        all(x.get("algebra") == ALGEBRA for x in (worker, receipt, marker))
        and all(x.get("logical_class") == CLASS for x in (worker, receipt, marker))
        and receipt.get("selector_count") == marker.get("selector_count") == INPUTS
        and worker.get("rows") == INPUTS,
        "wrong algebra, class or selector domain",
    )

    rows_path = files["rows-min_plus_hamming-class-0.jsonl"]
    count = 0
    with rows_path.open(encoding="utf-8") as f:
        for count, line in enumerate(f, 1):
            x = json.loads(line)
            fail_unless(
                isinstance(x, dict)
                and set(x) == ROW_KEYS
                and x.get("status") == "C90_COMPACT_NATIVE_SELECTOR_EVALUATED"
                and x.get("algebra_id") == 2
                and type(x.get("selector_index")) is int
                and x["selector_index"] == (count - 1) * 256
                and type(x.get("selector_coordinate")) is int
                and type(x.get("quality_exposed")) is bool
                and x["quality_exposed"] is False,
                "selector row structure, order or quality flag drift",
            )
            # Numerical native values and correction choices are not inspected.
    fail_unless(count == INPUTS, "incomplete or extra selector records")

    dig = {name: sha256(source) for name, source in files.items()}
    fail_unless(
        marker.get("rows_file_sha256") == worker.get("rows_sha256") ==
        dig["rows-min_plus_hamming-class-0.jsonl"]
        and marker.get("time_file_sha256") == dig["time.txt"]
        and worker.get("marker_sha256") == dig["external-shard.json"]
        and worker.get("semantic_receipt_sha256") ==
        dig["receipt-min_plus_hamming-class-0.json"],
        "cross-artifact receipt hash mismatch",
    )

    resource = files["time.txt"].read_text()
    rss = re.search(r"Maximum resident set size \(kbytes\): (\d+)", resource)
    wall = re.search(r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\): (\d+):(\d+):(\d+)", resource)
    fail_unless(
        rss is not None and wall is not None and
        "Exit status: 0" in resource,
        "missing successful GNU-time resource receipt",
    )
    wall_seconds = int(wall[1]) * 3600 + int(wall[2]) * 60 + int(wall[3])
    fail_unless(wall_seconds == 5807 and int(rss[1]) == 6112280, "frozen time/resource evidence drift")

    return {
        "record_type": "QTR_C90_COLAB_FIRST_SHARD_QUALITY_BLIND_VERIFICATION/1",
        "status": "EXACT_INPUT_IDENTITIES_AND_COMPLETED_RECEIPTS_VERIFIED",
        "activation_head": ACTIVATION,
        "orchestration_head": ORCHESTRATION,
        "algebra": ALGEBRA,
        "logical_class": CLASS,
        "selector_count": count,
        "wall_seconds": wall_seconds,
        "peak_rss_kib": int(rss[1]),
        "rows_sha256": dig["rows-min_plus_hamming-class-0.jsonl"],
        "scientific_quality_exposed": False,
        "claim_boundary": "Exactly one of 768 class/algebra shards. No independent scoring, per-input success, or C90 quality comparison.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--returned-dir", required=True, type=Path)
    opts = parser.parse_args()
    result = verify(opts.returned_dir)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
