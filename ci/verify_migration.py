#!/usr/bin/env python3
"""Verify exact subject checkout and the immutable QTR migration pair."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_COMMIT = "33b87f2f15f3af6c6e3b9e38ed3d0d3ba6244835"
TARGET_PAYLOAD_COMMIT = "871da6e9c1953b7dcbbf84a20121995b98d6c366"
SOURCE_REPOSITORY = "grandchallenge/.github"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_bytes(command: list[str], cwd: Path | None = None) -> bytes:
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout


def runtime_head() -> str:
    return run_bytes(["git", "rev-parse", "HEAD"], ROOT).decode().strip()


def assert_runtime_head(expected: str, observed: str | None = None) -> str:
    actual = observed if observed is not None else runtime_head()
    if actual != expected:
        raise SystemExit(
            f"exact-head mismatch: expected {expected}, observed {actual}"
        )
    print(f"exact subject checkout verified: {actual}")
    return actual


def git_object_bytes(repository: Path, commit: str, path: str) -> bytes:
    return run_bytes(["git", "show", f"{commit}:{path}"], repository)


def file_record(relative_path: str, data: bytes) -> dict[str, Any]:
    return {
        "relative_path": relative_path,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def canonical_payload_identity(records: list[dict[str, Any]]) -> str:
    compact = json.dumps(records, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(compact).hexdigest()


def fetch_source_repository(commit: str, destination: Path) -> None:
    subprocess.run(["git", "init", "-q", str(destination)], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(destination),
            "fetch",
            "--quiet",
            "--depth=1",
            f"https://github.com/{SOURCE_REPOSITORY}.git",
            commit,
        ],
        check=True,
    )


def verify_history(evaluated_commit: str, output: Path) -> dict[str, Any]:
    actual_head = assert_runtime_head(evaluated_commit)
    ledger = load_json(ROOT / "evidence" / "QTR-BOOT-001-source-identity.json")

    if ledger["source_commit"] != SOURCE_COMMIT:
        raise SystemExit("source ledger commit does not match governed source commit")
    if ledger["source_repository"] != SOURCE_REPOSITORY:
        raise SystemExit("source ledger repository does not match governed source repository")

    subprocess.run(
        ["git", "cat-file", "-e", f"{TARGET_PAYLOAD_COMMIT}^{{commit}}"],
        cwd=ROOT,
        check=True,
    )

    source_records: list[dict[str, Any]] = []
    target_records: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="qtr-source-") as tmp:
        source_repo = Path(tmp)
        fetch_source_repository(SOURCE_COMMIT, source_repo)

        for expected in ledger["files"]:
            source_data = git_object_bytes(source_repo, "FETCH_HEAD", expected["path"])
            target_data = git_object_bytes(
                ROOT, TARGET_PAYLOAD_COMMIT, expected["relative_path"]
            )
            source_record = file_record(expected["relative_path"], source_data)
            target_record = file_record(expected["relative_path"], target_data)
            source_records.append(source_record)
            target_records.append(target_record)

            expected_projection = {
                "relative_path": expected["relative_path"],
                "bytes": expected["bytes"],
                "sha256": expected["sha256"],
            }
            if (
                source_record != expected_projection
                or target_record != expected_projection
                or source_data != target_data
            ):
                mismatches.append(
                    {
                        "relative_path": expected["relative_path"],
                        "expected": expected_projection,
                        "source": source_record,
                        "target": target_record,
                        "source_target_bytes_equal": source_data == target_data,
                    }
                )

    source_identity = canonical_payload_identity(source_records)
    target_identity = canonical_payload_identity(target_records)
    receipt = {
        "receipt_version": "0.2.0",
        "docket_id": "QTR-ADOPT-CORR-001",
        "evaluated_commit": evaluated_commit,
        "runtime_head": actual_head,
        "exact_head_equal": evaluated_commit == actual_head,
        "source_repository": SOURCE_REPOSITORY,
        "source_commit": SOURCE_COMMIT,
        "target_repository": "grandchallenge/QUANTUM-TECHNOLOGIES",
        "target_payload_commit": TARGET_PAYLOAD_COMMIT,
        "source_ledger_identity_sha256": ledger["payload_identity_sha256"],
        "source_projection_identity_sha256": source_identity,
        "target_projection_identity_sha256": target_identity,
        "file_count": len(source_records),
        "source_target_byte_and_sha256_equal": not mismatches,
        "mismatches": mismatches,
        "files": target_records,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if mismatches:
        raise SystemExit(json.dumps(mismatches, indent=2, sort_keys=True))
    if source_identity != target_identity:
        raise SystemExit("historical source and target projection identities differ")

    print(
        f"historical QTR migration verified: {len(source_records)} files, "
        f"projection {target_identity}"
    )
    return receipt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assert-head")
    parser.add_argument("--verify-history", action="store_true")
    parser.add_argument("--evaluated-commit")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.assert_head:
        assert_runtime_head(args.assert_head)

    if args.verify_history:
        if not args.evaluated_commit or not args.output:
            raise SystemExit("--verify-history requires --evaluated-commit and --output")
        verify_history(args.evaluated_commit, args.output)

    if not args.assert_head and not args.verify_history:
        raise SystemExit("select --assert-head and/or --verify-history")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
