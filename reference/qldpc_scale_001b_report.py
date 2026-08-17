#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import qldpc_scale_001b as core

ROOT = Path(__file__).resolve().parents[1]

def project_report(full: dict[str, Any]) -> dict[str, Any]:
    projected = json.loads(json.dumps(full))
    projected.pop("payload_sha256", None)
    for rung in projected["rungs"]:
        rung["order_audit"].pop("orders", None)
    projected["payload_sha256"] = core.digest(projected)
    return projected

def evaluate(manifest: dict[str, Any]) -> dict[str, Any]:
    return project_report(core.evaluate(manifest))

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / core.MANIFEST_PATH)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = core.load_manifest(args.manifest)
    report = evaluate(manifest)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "experiment_id": core.EXPERIMENT_ID,
        "payload_sha256": report["payload_sha256"],
        "outcome": report["adjudication"]["primary_outcome"],
    }, sort_keys=True))

if __name__ == "__main__":
    main()
