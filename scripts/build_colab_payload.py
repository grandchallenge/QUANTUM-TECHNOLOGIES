#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]

EXCLUDED_PARTS = {
    ".git",
    ".venv",
    ".pytest_cache",
    "__pycache__",
    ".artifacts",
    "runs",
    "receipts",
    "analysis",
    "dist",
    "build",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".zip"}
EXCLUDED_NAMES = {"gcl_source.tar.gz", "gcl_manifest.json", "gcl_job.json"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def include_path(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDED_PARTS for part in rel.parts):
        return False
    if path.suffix in EXCLUDED_SUFFIXES:
        return False
    if path.name in EXCLUDED_NAMES or path.name.endswith(".tar.gz"):
        return False
    return path.is_file()


def governed_files() -> list[Path]:
    return sorted(
        (path for path in ROOT.rglob("*") if include_path(path)),
        key=lambda path: path.relative_to(ROOT).as_posix(),
    )


def tar_bytes(paths: Iterable[Path]) -> bytes:
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w") as archive:
        for path in paths:
            rel = path.relative_to(ROOT).as_posix()
            data = path.read_bytes()
            info = tarfile.TarInfo(name=rel)
            info.size = len(data)
            info.mode = 0o755 if os.access(path, os.X_OK) else 0o644
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            info.mtime = 0
            archive.addfile(info, io.BytesIO(data))
    compressed = io.BytesIO()
    with gzip.GzipFile(fileobj=compressed, mode="wb", mtime=0, filename="") as gz:
        gz.write(raw.getvalue())
    return compressed.getvalue()


def build(output: Path, manifest_path: Path) -> dict[str, object]:
    paths = governed_files()
    payload = tar_bytes(paths)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)
    manifest = {
        "schema_version": 1,
        "kind": "QTR_COLAB_SOURCE_PAYLOAD",
        "source_commit": git_head(),
        "payload_sha256": sha256_bytes(payload),
        "file_count": len(paths),
        "files": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in paths
        ],
        "excluded_top_level_runtime_outputs": sorted(EXCLUDED_PARTS),
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def check_deterministic() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        a, ma = tmp / "a.tar.gz", tmp / "a.json"
        b, mb = tmp / "b.tar.gz", tmp / "b.json"
        first = build(a, ma)
        second = build(b, mb)
        if a.read_bytes() != b.read_bytes():
            raise SystemExit("deterministic payload check failed: archive bytes differ")
        if first != second:
            raise SystemExit("deterministic payload check failed: manifests differ")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        check_deterministic()
        print("[QTR] deterministic Colab payload: PASS")
        return 0
    if not args.output or not args.manifest:
        parser.error("--output and --manifest are required unless --check is used")
    manifest = build(args.output, args.manifest)
    print(
        f"[QTR] payload={args.output} sha256={manifest['payload_sha256']} "
        f"files={manifest['file_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())