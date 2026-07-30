#!/usr/bin/env python3
"""Verify target QTR payload bytes against the admitted source identity ledger."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def file_record(relative_path: str) -> dict[str, Any]:
    path = ROOT / relative_path
    if not path.is_file():
        raise SystemExit(f"missing target migration file: {relative_path}")
    data = path.read_bytes()
    return {
        "relative_path": relative_path,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def canonical_payload_identity(records: list[dict[str, Any]]) -> str:
    compact = json.dumps(records, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(compact).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-ledger",
        type=Path,
        default=ROOT / "evidence" / "QTR-BOOT-001-source-identity.json",
    )
    parser.add_argument("--target-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source = load_json(args.source_ledger)
    expected = {
        record["relative_path"]: {
            "bytes": record["bytes"],
            "sha256": record["sha256"],
        }
        for record in source["files"]
    }

    observed_records = [file_record(path) for path in expected]
    mismatches: list[dict[str, Any]] = []
    for record in observed_records:
        wanted = expected[record["relative_path"]]
        if record["bytes"] != wanted["bytes"] or record["sha256"] != wanted["sha256"]:
            mismatches.append(
                {
                    "relative_path": record["relative_path"],
                    "expected": wanted,
                    "observed": {
                        "bytes": record["bytes"],
                        "sha256": record["sha256"],
                    },
                }
            )

    target_payload_identity = canonical_payload_identity(observed_records)
    # Source records carry an additional source path field. Reconstruct the same
    # canonical target projection before checking the aggregate identity.
    source_projection = [
        {
            "relative_path": record["relative_path"],
            "bytes": record["bytes"],
            "sha256": record["sha256"],
        }
        for record in source["files"]
    ]
    source_projection_identity = canonical_payload_identity(source_projection)

    result = {
        "receipt_version": "0.1.0",
        "programme_id": "QTR",
        "source_repository": source["source_repository"],
        "source_commit": source["source_commit"],
        "source_payload_identity_sha256": source["payload_identity_sha256"],
        "source_projection_identity_sha256": source_projection_identity,
        "target_repository": "grandchallenge/QUANTUM-TECHNOLOGIES",
        "target_commit": args.target_commit,
        "target_payload_identity_sha256": target_payload_identity,
        "file_count": len(observed_records),
        "files": observed_records,
        "mismatches": mismatches,
        "byte_and_sha256_equal": not mismatches,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if mismatches:
        raise SystemExit(json.dumps(mismatches, indent=2, sort_keys=True))

    print(
        f"QTR migration verified: {len(observed_records)} files, "
        f"target projection {target_payload_identity}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
