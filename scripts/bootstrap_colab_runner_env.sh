#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

REBUILD=0
VERIFY_ONLY=0
CHECK_AUTH=1
COLAB_AUTH="${COLAB_AUTH:-oauth2}"
PYTHON_SERIES="3.12"
COLAB_CLI_VERSION="0.6.0"
JUPYTER_KERNEL_CLIENT_VERSION="0.9.0"
VENV_DIR="$ROOT/.venv"
ARTIFACT_DIR="$ROOT/.artifacts/bootstrap"

say() { printf '[QTR] %s\n' "$*"; }
die() { printf '[QTR] ERROR: %s\n' "$*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --rebuild) REBUILD=1 ;;
    --verify-only) VERIFY_ONLY=1 ;;
    --skip-auth-check) CHECK_AUTH=0 ;;
    *) die "unknown option: $1" ;;
  esac
  shift
done

command -v uv >/dev/null 2>&1 || die "uv is required"
UV_BIN="$(command -v uv)"
mkdir -p "$ARTIFACT_DIR"

if [[ "$VERIFY_ONLY" -eq 0 ]]; then
  say "ensuring Python $PYTHON_SERIES is available under uv"
  "$UV_BIN" python install "$PYTHON_SERIES"
fi

if [[ "$REBUILD" -eq 1 && "$VERIFY_ONLY" -eq 0 ]]; then
  rm -rf "$VENV_DIR"
fi

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  [[ "$VERIFY_ONLY" -eq 0 ]] || die ".venv missing in --verify-only mode"
  say "creating Python $PYTHON_SERIES runner environment"
  "$UV_BIN" venv --python "$PYTHON_SERIES" --seed "$VENV_DIR"
fi

VENV_PY="$VENV_DIR/bin/python"
ACTUAL_SERIES="$($VENV_PY -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
[[ "$ACTUAL_SERIES" == "$PYTHON_SERIES" ]] || die "expected Python $PYTHON_SERIES, found $ACTUAL_SERIES"

if [[ "$VERIFY_ONLY" -eq 0 ]]; then
  say "installing local runner test dependencies"
  "$UV_BIN" pip install --python "$VENV_PY" "pytest>=8,<9"
  say "installing isolated Colab CLI toolchain"
  "$UV_BIN" tool install --force --python "$PYTHON_SERIES" \
    --with "jupyter-kernel-client==$JUPYTER_KERNEL_CLIENT_VERSION" \
    "google-colab-cli==$COLAB_CLI_VERSION"
fi

TOOL_BIN_DIR="$($UV_BIN tool dir --bin)"
COLAB_BIN="$TOOL_BIN_DIR/colab"
[[ -x "$COLAB_BIN" ]] || die "Colab CLI executable not found at $COLAB_BIN"
ln -sfn "$COLAB_BIN" "$VENV_DIR/bin/colab"
export PATH="$VENV_DIR/bin:$TOOL_BIN_DIR:$PATH"
command -v colab >/dev/null 2>&1 || die "colab CLI is not visible on PATH"
colab --help >/dev/null 2>&1 || die "colab CLI exists but cannot start"

say "checking Colab CLI provenance"
"$UV_BIN" tool list > "$ARTIFACT_DIR/uv-tool-list.txt"
grep -q "google-colab-cli v$COLAB_CLI_VERSION" "$ARTIFACT_DIR/uv-tool-list.txt" \
  || die "uv tool list does not report google-colab-cli v$COLAB_CLI_VERSION"
colab version > "$ARTIFACT_DIR/colab-version.txt" 2>&1

if [[ "$CHECK_AUTH" -eq 1 ]]; then
  say "checking Colab access (auth=$COLAB_AUTH)"
  if command -v timeout >/dev/null 2>&1; then
    timeout 45 colab --auth="$COLAB_AUTH" sessions \
      > "$ARTIFACT_DIR/colab-sessions.txt" 2>&1 \
      || die "Colab auth/session check failed"
  else
    colab --auth="$COLAB_AUTH" sessions \
      > "$ARTIFACT_DIR/colab-sessions.txt" 2>&1 \
      || die "Colab auth/session check failed"
  fi
else
  printf 'SKIPPED\n' > "$ARTIFACT_DIR/colab-sessions.txt"
fi

say "compiling runner entrypoints"
"$VENV_PY" -m py_compile \
  scripts/build_colab_payload.py \
  scripts/colab_run_matrix.py \
  colab/qtr_remote_job.py \
  reference/qtr_colab_runtime_probe.py \
  reference/qtr_compute_requal_001.py

bash -n scripts/colab_run_job.sh
bash -n scripts/bootstrap_colab_runner_env.sh

say "running bounded runner tests"
"$VENV_PY" -m pytest -q tests/test_qtr_colab_compute_001.py --import-mode=importlib

say "checking deterministic source payload"
"$VENV_PY" scripts/build_colab_payload.py --check

say "writing environment receipt"
"$VENV_PY" - "$ARTIFACT_DIR" "$COLAB_BIN" "$COLAB_AUTH" "$CHECK_AUTH" <<'PY'
from __future__ import annotations
import hashlib, json, platform, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

artifact = Path(sys.argv[1])
colab_bin = sys.argv[2]
auth = sys.argv[3]
auth_checked = bool(int(sys.argv[4]))
root = Path.cwd()

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

receipt = {
    "schema_version": 1,
    "audit_id": "QTR-COLAB-RUNNER-ENVIRONMENT-001",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "python": sys.version,
    "platform": platform.platform(),
    "colab_cli": subprocess.check_output([colab_bin, "version"], text=True).strip(),
    "colab_auth_provider": auth,
    "colab_auth_checked": auth_checked,
    "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    "entrypoint_sha256": {
        "scripts/build_colab_payload.py": sha(root / "scripts/build_colab_payload.py"),
        "scripts/colab_run_job.sh": sha(root / "scripts/colab_run_job.sh"),
        "scripts/colab_run_matrix.py": sha(root / "scripts/colab_run_matrix.py"),
        "colab/qtr_remote_job.py": sha(root / "colab/qtr_remote_job.py"),
    },
    "claim_boundary": {
        "engineering_environment_only": True,
        "scientific_execution_authorized": False,
        "promotion_authorized": False,
    },
}
(artifact / "QTR_COLAB_RUNNER_ENVIRONMENT_RECEIPT.json").write_text(
    json.dumps(receipt, indent=2, sort_keys=True) + "\n"
)
PY

say "runner environment GREEN"