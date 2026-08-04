"""Document, check-run, ancestry, and credential validators."""
from __future__ import annotations

import base64
import json
from typing import Any

from quantum_readback_core import ReadbackError, require

def decode_content(payload: dict[str, Any], path: str) -> bytes:
    require(payload.get("type") == "file", f"expected repository file: {path}")
    require(payload.get("encoding") == "base64", f"unexpected encoding: {path}")
    content = payload.get("content")
    require(isinstance(content, str), f"missing content: {path}")
    try:
        return base64.b64decode(content, validate=False)
    except Exception as exc:
        raise ReadbackError(f"invalid base64 repository content: {path}") from exc


def validate_documents(
    documents: dict[str, dict[str, Any]],
    requirements: list[dict[str, Any]],
    *,
    kind: str,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for requirement in requirements:
        path = requirement["path"]
        require(path in documents, f"missing {kind}: {path}")
        row = documents[path]
        require(
            row.get("git_blob_sha1") == requirement["git_blob_sha1"],
            f"{kind} blob identity drift: {path}",
        )
        text = row["text"]
        for fragment in requirement["required_fragments"]:
            require(fragment in text, f"{kind} content drift: {path}: {fragment}")
        if "state" in requirement:
            require(
                row.get("state") == requirement["state"],
                f"{kind} state drift: {path}",
            )
        output.append(
            {
                "path": path,
                "git_blob_sha1": row["git_blob_sha1"],
                "size_bytes": row["size_bytes"],
                "sha256": row["sha256"],
                **({"state": row["state"]} if "state" in row else {}),
            }
        )
    return output


def validate_check_runs(
    rows: list[dict[str, Any]], expected_names: list[str]
) -> list[dict[str, Any]]:
    by_name: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get("name"), str):
            by_name.setdefault(row["name"], []).append(row)
    selected: list[dict[str, Any]] = []
    for name in expected_names:
        candidates = by_name.get(name, [])
        successful = [
            row
            for row in candidates
            if row.get("status") == "completed" and row.get("conclusion") == "success"
        ]
        require(successful, f"protected-main check is not successful: {name}")
        row = sorted(
            successful,
            key=lambda value: str(value.get("completed_at") or ""),
            reverse=True,
        )[0]
        selected.append(
            {
                "id": row.get("id"),
                "name": name,
                "status": row.get("status"),
                "conclusion": row.get("conclusion"),
                "started_at": row.get("started_at"),
                "completed_at": row.get("completed_at"),
                "details_url": row.get("details_url"),
            }
        )
    return selected


def validate_codeql_jobs(
    rows: list[dict[str, Any]], expected_names: list[str]
) -> list[dict[str, Any]]:
    mapping = {
        row.get("name"): row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("name"), str)
    }
    selected: list[dict[str, Any]] = []
    for name in expected_names:
        row = mapping.get(name)
        require(isinstance(row, dict), f"CodeQL validation job missing: {name}")
        require(
            row.get("status") == "completed" and row.get("conclusion") == "success",
            f"CodeQL validation job did not succeed: {name}",
        )
        selected.append(
            {
                "id": row.get("id"),
                "name": name,
                "status": row.get("status"),
                "conclusion": row.get("conclusion"),
                "started_at": row.get("started_at"),
                "completed_at": row.get("completed_at"),
            }
        )
    return selected


def validate_ancestry(
    comparison: dict[str, Any], base_sha: str, main_sha: str, *, label: str
) -> dict[str, Any]:
    require(
        comparison.get("base_commit", {}).get("sha") == base_sha,
        f"{label} comparison base drift",
    )
    require(
        comparison.get("merge_base_commit", {}).get("sha") == base_sha,
        f"{label} is not an ancestor of protected main",
    )
    require(
        comparison.get("status") in {"ahead", "identical"},
        f"{label} ancestry status drift",
    )
    require(comparison.get("behind_by") == 0, f"{label} is behind protected main")
    require(
        comparison.get("head_commit", {}).get("sha") == main_sha,
        f"{label} comparison head drift",
    )
    return {
        "base": base_sha,
        "head": main_sha,
        "status": comparison.get("status"),
        "ahead_by": comparison.get("ahead_by"),
        "behind_by": comparison.get("behind_by"),
        "merge_base": comparison.get("merge_base_commit", {}).get("sha"),
    }


def scan_for_credentials(value: Any) -> None:
    serialized = json.dumps(value, sort_keys=True)
    forbidden = (
        "Authorization",
        "Bearer ",
        "ghp_",
        "github_pat_",
        "-----BEGIN PRIVATE KEY-----",
    )
    for marker in forbidden:
        if marker in serialized:
            raise ReadbackError(f"receipt contains credential marker: {marker}")
