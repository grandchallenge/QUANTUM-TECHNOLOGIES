#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

EXPECTED_PROTECTED_BASE="c5719a623310432c4e97a5863428176ff739cbd7"
COLAB_AUTH="${COLAB_AUTH:-oauth2}"
VENV_PY="$ROOT/.venv/bin/python"
COLAB_BIN="$ROOT/.venv/bin/colab"
JOB_TEMPLATE="$ROOT/configs/compute/qtr_c90_resource_envelope_001_job.json"

[[ -x "$VENV_PY" ]] || { echo "missing runner Python; run bootstrap_colab_runner_env.sh" >&2; exit 2; }
[[ -x "$COLAB_BIN" ]] || { echo "missing Colab CLI; run bootstrap_colab_runner_env.sh" >&2; exit 2; }
[[ -f "$JOB_TEMPLATE" ]] || { echo "missing resource-envelope job template" >&2; exit 2; }

HEAD="$(git rev-parse HEAD)"
test -z "$(git status --porcelain)" || { echo "working tree not clean" >&2; exit 20; }

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-$$"
SESSION="gcl-qtr-c90-env-${RUN_ID,,}"
LOCAL_RUN="$ROOT/runs/hosted/QTR-C90-RESOURCE-ENVELOPE-001/$RUN_ID"
mkdir -p "$LOCAL_RUN"

PAYLOAD="$LOCAL_RUN/gcl_source.tar.gz"
SOURCE_MANIFEST="$LOCAL_RUN/gcl_manifest.json"
JOB="$LOCAL_RUN/gcl_job.json"

"$VENV_PY" scripts/build_colab_payload.py --output "$PAYLOAD" --manifest "$SOURCE_MANIFEST"
"$VENV_PY" - "$JOB_TEMPLATE" "$JOB" "$SESSION" <<'PY'
import json,sys
src,dst,session=sys.argv[1:]
job=json.load(open(src,encoding="utf-8"))
if job.get("hosted_session_identity")!="__HOST_RENDERED__":
    raise SystemExit("job template session placeholder changed")
job["hosted_session_identity"]=session
json.dump(job,open(dst,"w",encoding="utf-8"),indent=2,sort_keys=True)
open(dst,"a",encoding="utf-8").write("\n")
PY

ALLOCATED=0
cleanup() {
  rc=$?
  set +e
  if [[ "$ALLOCATED" -eq 1 ]]; then
    "$COLAB_BIN" --auth="$COLAB_AUTH" log -s "$SESSION" -o "$LOCAL_RUN/colab-execution.md" > "$LOCAL_RUN/colab-log-command.txt" 2>&1 || true
    "$COLAB_BIN" --auth="$COLAB_AUTH" stop -s "$SESSION" > "$LOCAL_RUN/colab-stop.txt" 2>&1 || true
  fi
  "$COLAB_BIN" --auth="$COLAB_AUTH" sessions > "$LOCAL_RUN/colab-sessions-after.txt" 2>&1 || true
  exit "$rc"
}
trap cleanup EXIT INT TERM

echo "[QTR-C90-ENV] source=$HEAD"
echo "[QTR-C90-ENV] protected predecessor=$EXPECTED_PROTECTED_BASE"
echo "[QTR-C90-ENV] allocating fresh CPU session=$SESSION"
"$COLAB_BIN" --auth="$COLAB_AUTH" new -s "$SESSION"
ALLOCATED=1
"$COLAB_BIN" --auth="$COLAB_AUTH" status -s "$SESSION" > "$LOCAL_RUN/colab-status.txt"

"$COLAB_BIN" --auth="$COLAB_AUTH" upload -s "$SESSION" "$PAYLOAD" /content/gcl_source.tar.gz
"$COLAB_BIN" --auth="$COLAB_AUTH" upload -s "$SESSION" "$SOURCE_MANIFEST" /content/gcl_manifest.json
"$COLAB_BIN" --auth="$COLAB_AUTH" upload -s "$SESSION" "$JOB" /content/gcl_job.json

REMOTE_TIMEOUT="$("$VENV_PY" - "$JOB" <<'PY'
import json,sys
print(int(json.load(open(sys.argv[1]))["remote_timeout_seconds"]))
PY
)"

set +e
"$COLAB_BIN" --auth="$COLAB_AUTH" exec -s "$SESSION" -f "$ROOT/colab/qtr_c90_resource_envelope_remote_job.py" --timeout "$REMOTE_TIMEOUT" > >(tee "$LOCAL_RUN/remote-stdout.txt") 2> >(tee "$LOCAL_RUN/remote-stderr.txt" >&2)
REMOTE_RC=$?
set -e

"$COLAB_BIN" --auth="$COLAB_AUTH" download -s "$SESSION" /content/experiment_receipt.json "$LOCAL_RUN/experiment_receipt.json" > "$LOCAL_RUN/download-receipt.txt" 2>&1 || true
"$COLAB_BIN" --auth="$COLAB_AUTH" download -s "$SESSION" /content/gcl_output_bundle.tar.gz "$LOCAL_RUN/gcl_output_bundle.tar.gz" > "$LOCAL_RUN/download-bundle.txt" 2>&1 || true
"$COLAB_BIN" --auth="$COLAB_AUTH" download -s "$SESSION" /content/gcl_result.json "$LOCAL_RUN/gcl_result.json" > "$LOCAL_RUN/download-result.txt" 2>&1 || true

for required in experiment_receipt.json gcl_output_bundle.tar.gz gcl_result.json; do
  [[ -f "$LOCAL_RUN/$required" ]] || { echo "missing hosted artifact $required; evidence retained at $LOCAL_RUN" >&2; exit 30; }
done

"$VENV_PY" - "$LOCAL_RUN/experiment_receipt.json" "$LOCAL_RUN/gcl_result.json" "$JOB" "$SOURCE_MANIFEST" "$SESSION" <<'PY'
import hashlib,json,sys
from pathlib import Path
receipt_path,result_path,job_path,manifest_path,session=sys.argv[1:]
r=json.load(open(receipt_path)); result=json.load(open(result_path)); manifest=json.load(open(manifest_path))
sha=lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
if r.get("status")!="GREEN_SCIENTIFIC_CANDIDATE": raise SystemExit(f"hosted receipt not green: {r.get('status')}")
if r.get("hosted_session_identity")!=session: raise SystemExit("session identity mismatch")
if r.get("source_commit")!=manifest.get("source_commit"): raise SystemExit("source commit mismatch")
if r.get("source_payload_sha256")!=manifest.get("payload_sha256"): raise SystemExit("source payload mismatch")
if r.get("job_sha256")!=sha(job_path): raise SystemExit("job digest mismatch")
if r.get("result_sha256")!=sha(result_path): raise SystemExit("result digest mismatch")
if result.get("status")!="candidate_executable_not_promoted": raise SystemExit("scientific result status drift")
if result.get("materialization_performed") is not False: raise SystemExit("materialization boundary violated")
if result.get("frozen_307_validation_performed") is not False: raise SystemExit("validation boundary violated")
print("[QTR-C90-ENV] outcome:",result["overall_outcome"])
for name,row in result["methods"].items():
    print("[QTR-C90-ENV]",name,row["status"],"coordinate",row.get("cumulative_work_sensitivity_coordinate"))
PY

if [[ "$REMOTE_RC" -ne 0 ]]; then
  echo "remote process rc=$REMOTE_RC; evidence retained at $LOCAL_RUN" >&2
  exit "$REMOTE_RC"
fi

echo "RESULT: QTR_C90_RESOURCE_ENVELOPE_HOSTED_CALIBRATION_COMPLETE"
echo "WORKDIR=$LOCAL_RUN"
