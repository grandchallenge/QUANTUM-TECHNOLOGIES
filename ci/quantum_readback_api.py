"""Authenticated GitHub REST GET-only client and collection helpers."""
from __future__ import annotations

import json
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from quantum_readback_core import API_ROOT, ReadbackError, byte_sha256, require
from quantum_readback_evidence import decode_content, validate_check_runs
from quantum_readback_rules import normalize_codeql, repo_path

class GitHubAPI:
    """Minimal GitHub REST client that refuses non-GET requests."""

    def __init__(self, token: str, api_version: str) -> None:
        if not token.strip():
            raise ReadbackError("missing GitHub authentication token")
        self._token = token.strip()
        self._api_version = api_version

    def request(
        self,
        endpoint: str,
        *,
        method: str = "GET",
        accepted: tuple[int, ...] = (200,),
    ) -> tuple[int, Any]:
        if method != "GET":
            raise ReadbackError("collector transport is GET-only")
        url = endpoint if endpoint.startswith("https://") else API_ROOT + endpoint
        request = urllib.request.Request(
            url,
            method="GET",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self._token}",
                "X-GitHub-Api-Version": self._api_version,
                "User-Agent": "gcl-quantum-full-readback/1.0",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                status = response.status
                body = response.read()
        except urllib.error.HTTPError as exc:
            status = exc.code
            body = exc.read()
        if status not in accepted:
            detail = body.decode("utf-8", errors="replace")[:2000]
            raise ReadbackError(
                f"GitHub API GET {endpoint} failed with {status}: {detail}"
            )
        if not body:
            return status, None
        try:
            return status, json.loads(body)
        except json.JSONDecodeError as exc:
            raise ReadbackError(
                f"GitHub API GET {endpoint} returned malformed JSON"
            ) from exc


def gh_token() -> str:
    if not shutil_which("gh"):
        raise ReadbackError("GitHub CLI 'gh' is not available")
    status = subprocess.run(
        ["gh", "auth", "status", "--hostname", "github.com"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if status.returncode != 0:
        raise ReadbackError("GitHub CLI is not authenticated")
    completed = subprocess.run(
        ["gh", "auth", "token"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0 or not completed.stdout.strip():
        raise ReadbackError("unable to obtain GitHub CLI authentication token")
    return completed.stdout.strip()


def shutil_which(command: str) -> str | None:
    import shutil

    return shutil.which(command)


def repo_path(repository: str) -> str:
    return f"/repos/{repository}"

def collect_document(
    client: GitHubAPI,
    repository: str,
    path: str,
    ref: str,
    *,
    state: str | None = None,
) -> dict[str, Any]:
    encoded = urllib.parse.quote(path, safe="/")
    _, payload = client.request(
        f"{repo_path(repository)}/contents/{encoded}?ref={ref}"
    )
    require(isinstance(payload, dict), f"malformed content response: {path}")
    data = decode_content(payload, path)
    result = {
        "path": path,
        "git_blob_sha1": payload.get("sha"),
        "size_bytes": len(data),
        "sha256": byte_sha256(data),
        "text": data.decode("utf-8"),
    }
    if state is not None:
        result["state"] = state
    return result


def fetch_workflow_states(
    client: GitHubAPI, repository: str
) -> dict[str, str]:
    _, payload = client.request(
        f"{repo_path(repository)}/actions/workflows?per_page=100"
    )
    require(isinstance(payload, dict), "malformed workflow inventory")
    rows = payload.get("workflows")
    require(isinstance(rows, list), "workflow inventory lacks workflows")
    result: dict[str, str] = {}
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get("path"), str):
            result[row["path"]] = str(row.get("state"))
    return result


def security_readback(
    client: GitHubAPI, repository: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    base = repo_path(repository)
    alerts_status, alerts_body = client.request(
        f"{base}/vulnerability-alerts", accepted=(200, 204)
    )
    fixes_status, fixes_body = client.request(
        f"{base}/automated-security-fixes", accepted=(200, 204)
    )
    _, private_body = client.request(f"{base}/private-vulnerability-reporting")
    _, codeql_body = client.request(f"{base}/code-scanning/default-setup")
    require(isinstance(private_body, dict), "malformed private-reporting readback")
    require(isinstance(codeql_body, dict), "malformed CodeQL readback")

    if fixes_status == 204:
        fixes_enabled, fixes_paused = True, False
    else:
        require(isinstance(fixes_body, dict), "malformed Dependabot readback")
        fixes_enabled = bool(fixes_body.get("enabled", True))
        fixes_paused = bool(fixes_body.get("paused", False))

    normalized = {
        "vulnerability_alerts": alerts_status in (200, 204),
        "dependabot_security_updates_enabled": fixes_enabled,
        "dependabot_security_updates_paused": fixes_paused,
        "private_vulnerability_reporting": private_body.get("enabled"),
        "codeql": normalize_codeql(codeql_body),
    }
    raw = {
        "vulnerability_alerts_status": alerts_status,
        "vulnerability_alerts_response": alerts_body,
        "automated_security_fixes_status": fixes_status,
        "automated_security_fixes_response": fixes_body,
        "private_vulnerability_reporting": private_body,
        "codeql_default_setup": codeql_body,
    }
    return normalized, raw


def fetch_rulesets(
    client: GitHubAPI, repository: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    base = repo_path(repository)
    _, summaries = client.request(f"{base}/rulesets?includes_parents=false&per_page=100")
    require(isinstance(summaries, list), "malformed ruleset inventory")
    details: list[dict[str, Any]] = []
    for summary in summaries:
        if not isinstance(summary, dict) or summary.get("source_type") != "Repository":
            continue
        ruleset_id = summary.get("id")
        require(isinstance(ruleset_id, int), "ruleset summary lacks numeric ID")
        _, detail = client.request(
            f"{base}/rulesets/{ruleset_id}?includes_parents=false"
        )
        require(isinstance(detail, dict), "malformed ruleset detail")
        details.append(detail)
    return summaries, details


def find_ruleset(
    details: list[dict[str, Any]],
    *,
    name: str | None = None,
    ruleset_id: int | None = None,
) -> dict[str, Any]:
    rows = [
        row
        for row in details
        if (name is None or row.get("name") == name)
        and (ruleset_id is None or row.get("id") == ruleset_id)
    ]
    require(len(rows) == 1, f"expected exactly one ruleset: {name or ruleset_id}")
    return rows[0]


def fetch_check_runs(
    client: GitHubAPI, repository: str, sha: str
) -> list[dict[str, Any]]:
    _, payload = client.request(
        f"{repo_path(repository)}/commits/{sha}/check-runs?per_page=100"
    )
    require(isinstance(payload, dict), "malformed check-run response")
    rows = payload.get("check_runs")
    require(isinstance(rows, list), "check-run response lacks rows")
    return rows


def wait_for_check_runs(
    client: GitHubAPI,
    repository: str,
    sha: str,
    names: list[str],
    wait_seconds: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    deadline = time.monotonic() + max(wait_seconds, 0)
    last: list[dict[str, Any]] = []
    while True:
        last = fetch_check_runs(client, repository, sha)
        try:
            selected = validate_check_runs(last, names)
            return selected, last
        except ReadbackError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(min(15, max(1, int(deadline - time.monotonic()))))


def comparison(
    client: GitHubAPI, repository: str, base: str, head: str
) -> dict[str, Any]:
    _, payload = client.request(f"{repo_path(repository)}/compare/{base}...{head}")
    require(isinstance(payload, dict), "malformed commit comparison")
    return payload
