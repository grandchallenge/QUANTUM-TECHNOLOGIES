#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

JOB="${1:-}"
[[ -n "$JOB" && -f "$JOB" ]] || {
  echo "usage: $0 <job.json>" >&2
  exit 2
}

COLAB_AUTH="${COLAB_AUTH:-oauth2}"

readarray -t META < <(python - "$JOB" <<'PY'
import json, sys
job=json.load(open(sys.argv[1], encoding="utf-8"))
required={"schema_version","experiment_id","workload","resource","remote_timeout_seconds",
          "scientific_backend","scientific_execution_authorized","claim_boundary"}
missing=required-set(job)
if missing:
    raise SystemExit(f"missing job keys: {sorted(missing)}")
r=job["resource"]
variant=str(r["variant"]).upper()
accelerator=r.get("accelerator") or ""
print(job["experiment_id"])
print(variant)
print(accelerator)
print(int(job["remote_timeout_seconds"]))
PY
)

EXPERIMENT_ID="${META[0]}"
VARIANT="${META[1]}"
ACCELERATOR="${META[2]}"
REMOTE_TIMEOUT="${META[3]}"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-$$"
SESSION="gcl-qtr-$(printf '%s' "$EXPERIMENT_ID" | tr '[:upper:]_' '[:lower:]-' | tr -cd 'a-z0-9.-' | cut -c1-42)-$$"
LOCAL_RUN="$ROOT/runs/hosted/$EXPERIMENT_ID/$RUN_ID"
mkdir -p "$LOCAL_RUN"

PAYLOAD="$LOCAL_RUN/gcl_source.tar.gz"
MANIFEST="$LOCAL_RUN/gcl_manifest.json"
cp "$JOB" "$LOCAL_RUN/gcl_job.json"

python scripts/build_colab_payload.py --output "$PAYLOAD" --manifest "$MANIFEST"

ALLOCATED=0
cleanup() {
  rc=$?
  set +e
  if [[ "$ALLOCATED" -eq 1 ]]; then
    colab --auth="$COLAB_AUTH" log -s "$SESSION" -o "$LOCAL_RUN/colab-execution.md" \
      > "$LOCAL_RUN/colab-log-command.txt" 2>&1 || true
    colab --auth="$COLAB_AUTH" stop -s "$SESSION" \
      > "$LOCAL_RUN/colab-stop.txt" 2>&1 || true
  fi
  colab --auth="$COLAB_AUTH" sessions > "$LOCAL_RUN/colab-sessions-after.txt" 2>&1 || true
  exit "$rc"
}
trap cleanup EXIT INT TERM

echo "[QTR] allocating session=$SESSION variant=$VARIANT accelerator=${ACCELERATOR:-none}"
case "$VARIANT" in
  CPU|DEFAULT)
    colab --auth="$COLAB_AUTH" new -s "$SESSION"
    ;;
  GPU)
    [[ -n "$ACCELERATOR" ]] || { echo "GPU accelerator missing" >&2; exit 3; }
    colab --auth="$COLAB_AUTH" new -s "$SESSION" --gpu "$ACCELERATOR"
    ;;
  TPU)
    [[ -n "$ACCELERATOR" ]] || { echo "TPU accelerator missing" >&2; exit 3; }
    colab --auth="$COLAB_AUTH" new -s "$SESSION" --tpu "$ACCELERATOR"
    ;;
  *)
    echo "unsupported resource variant: $VARIANT" >&2
    exit 3
    ;;
esac
ALLOCATED=1

colab --auth="$COLAB_AUTH" status -s "$SESSION" > "$LOCAL_RUN/colab-status.txt"

colab --auth="$COLAB_AUTH" upload -s "$SESSION" "$PAYLOAD" /content/gcl_source.tar.gz
colab --auth="$COLAB_AUTH" upload -s "$SESSION" "$LOCAL_RUN/gcl_job.json" /content/gcl_job.json
colab --auth="$COLAB_AUTH" upload -s "$SESSION" "$MANIFEST" /content/gcl_manifest.json

set +e
colab --auth="$COLAB_AUTH" exec -s "$SESSION" -f "$ROOT/colab/qtr_remote_job.py" \
  --timeout "$REMOTE_TIMEOUT" \
  > >(tee "$LOCAL_RUN/remote-stdout.txt") \
  2> >(tee "$LOCAL_RUN/remote-stderr.txt" >&2)
REMOTE_RC=$?
set -e

colab --auth="$COLAB_AUTH" download -s "$SESSION" \
  /content/experiment_receipt.json "$LOCAL_RUN/experiment_receipt.json" \
  > "$LOCAL_RUN/download-receipt.txt" 2>&1 || true
colab --auth="$COLAB_AUTH" download -s "$SESSION" \
  /content/gcl_output_bundle.tar.gz "$LOCAL_RUN/gcl_output_bundle.tar.gz" \
  > "$LOCAL_RUN/download-bundle.txt" 2>&1 || true

if [[ -f "$LOCAL_RUN/experiment_receipt.json" ]]; then
  python - "$LOCAL_RUN/experiment_receipt.json" <<'PY'
import json, sys
r=json.load(open(sys.argv[1], encoding="utf-8"))
print("[QTR] remote receipt status:", r.get("status"))
print("[QTR] observed runtime:", r.get("runtime",{}).get("observed_variant"),
      r.get("runtime",{}).get("observed_accelerator"))
if r.get("status") != "GREEN_ENGINEERING":
    raise SystemExit(10)
PY
fi

if [[ "$REMOTE_RC" -ne 0 ]]; then
  echo "[QTR] remote execution failed rc=$REMOTE_RC; evidence retained at $LOCAL_RUN" >&2
  exit "$REMOTE_RC"
fi

echo "[QTR] hosted engineering job GREEN: $LOCAL_RUN"