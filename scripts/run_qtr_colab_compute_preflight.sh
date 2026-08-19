#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

REBUILD=0
RESUME=1
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --rebuild) REBUILD=1 ;;
    --no-resume) RESUME=0 ;;
    --dry-run) DRY_RUN=1 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

BOOTSTRAP=(bash scripts/bootstrap_colab_runner_env.sh)
if [[ "$REBUILD" -eq 1 ]]; then
  BOOTSTRAP+=(--rebuild)
fi
"${BOOTSTRAP[@]}"

PY="$ROOT/.venv/bin/python"
MATRIX_ARGS=()
if [[ "$RESUME" -eq 1 ]]; then
  MATRIX_ARGS+=(--resume)
fi
if [[ "$DRY_RUN" -eq 1 ]]; then
  MATRIX_ARGS+=(--dry-run)
fi

set +e
"$PY" scripts/colab_run_matrix.py \
  configs/compute/qtr_colab_runtime_probe_matrix.json \
  --continue-on-error "${MATRIX_ARGS[@]}"
RUNTIME_RC=$?
set -e

"$PY" scripts/colab_run_matrix.py \
  configs/compute/qtr_compute_requal_001_matrix.json \
  "${MATRIX_ARGS[@]}"

echo "[QTR] runtime-probe matrix rc=$RUNTIME_RC"
if [[ "$RUNTIME_RC" -ne 0 ]]; then
  echo "[QTR] one or more requested Colab resources were unavailable or failed validation; evidence is retained" >&2
fi
exit "$RUNTIME_RC"