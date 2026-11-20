#!/usr/bin/env python3
"""Source-locked, quality-blind intake of C90 conventional October replay evidence.

This is a portable *data intake* validator on current QTR main. It does not
import the unmerged historical C90 scientific decoder, select corrections,
score a new decoder, or claim that the missing August ZIP was recovered.

The constants below are transcribed exactly from frozen reference code at
675865123437c3d6c908c7a3af337fd4023c5d0b and PR #129's verified replay.
Every conventional outcome vector is checked independently against its
protected digest, but the CLI never emits the per-input vectors.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path
from typing import Any

SOURCE_HEAD = "675865123437c3d6c908c7a3af337fd4023c5d0b"
RECOVERY_ARCHIVE = {
    "artifact_id": 12738710046,
    "run_id": 40511661627,
    "head_sha": "c588cbbc635fe477c8496fd69e6145f62b768b2e",
    "name": "TCM-QDEC-COMPARE-001-exact-head",
    "sha256": "dd59ab416d41b1e9025d82319e28bd0ab622e0cdc6e10b097ca470a879dd3a46",
}
ORIGINAL_ARCHIVE = {
    "artifact_id": 9304727792,
    "run_id": 32079738866,
    "head_sha": "3ebe409c60e7907b8251d44ee822141159d2879c",
    "sha256": "34f37ec1a351a42e08c7143b359ca40191db4cd92ceeab2881930a67e3942182",
    "byte_verified": False,
}
CORPUS_SHA = "b053a27a9c346832d6008987e204c88162dc1797e0367b38705861049059e086"
MANIFEST_SHA = "c68830f40733cde6957713060cec35adf317c75572cc960610c07c4d0e24d1e2"
REPORT_SHA = "6385c2da742e14ecf2bc41336c78c2a8ff42b1cdd897fb5e7cfac056e2214146"
REPLAY_RECEIPT_COMMON = {
    "bposd_wheel_sha256": "80e439246c11ca824610f9bc7858c68eb1f8a6b7cbb71760cf6c86e03c47ff5d",
    "exact_head_equal": True,
    "execution_mode": "deterministic_3x3_cell_shard_with_exact_basis_oracle",
    "experiment_id": "TCM-QDEC-COMPARE-001",
    "ldpc_sdist_sha256": "3b2652aa993ab71672d680ac76ee2dcf3dc289fc5d11c07d060e5f838d8c3601",
    "manifest_payload_sha256": MANIFEST_SHA,
    "qec_circuit_001_authorized": False,
    "receipt_version": "0.3.0",
    "report_payload_sha256": REPORT_SHA,
    "timing_authoritative": False,
}
CONVENTIONAL = {
    "BP_MIN_SUM": {
        "success": 200,
        "cell_sha256": "3c46d32686fcf4c821c9e9e973f107837c56f63abc69e71175cf555cde4979e5",
        "outcomes_sha256": "9652133baf36b83605c2f394067bd25938b47eb9595435b72470256ca1fe5bae",
        "results_sha256": "8d06d07779a61d8ec305e46bd7479f30dc773b84e2d3fe76da054500fc7f6bff",
    },
    "BP_OSD_CS_7": {
        "success": 211,
        "cell_sha256": "f86b3764780328a67c7cb84dc92920ebbd499b8c2eeef7cb2c9cf3b9edfbe240",
        "outcomes_sha256": "bd2141809336ae41db0a5e471be74603e780f6b7beba72a541bdc00132ab50ea",
        "results_sha256": "2195de2fe9af00cc340a551ec0a01f9f54ffaca8c5f01100cf9fc05649a1db58",
    },
    "BP_SUM_PRODUCT": {
        "success": 171,
        "cell_sha256": "26237bdf051a15b20dc3a0cc2fcc2b02b264a0f7c037d601af21c1fd9fac2ab0",
        "outcomes_sha256": "d943dcfbf110e8c1e57558bddec270da374d6ea0abc9be9923d848e30eac3f48",
        "results_sha256": "9b5c120d8e5170a5694dd016c1f2502df216f91e72024a02cbf37e3d5a27b7ac",
    },
}
CELL_SUBJECT_KEYS = (
    "surface", "method", "package_receipt", "corpus_size",
    "summary", "outcomes", "result_records_sha256",
)
CELL_ALL_KEYS = set(CELL_SUBJECT_KEYS) | {
    "experiment_id", "manifest_payload_sha256", "cell_payload_sha256",
}


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=True, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_github_metadata() -> None:
    """Optional online verification. Never fabricates an earlier ZIP receipt."""
    i = RECOVERY_ARCHIVE["artifact_id"]
    response = subprocess.run(
        ["gh", "api", f"repos/grandchallenge/QUANTUM-TECHNOLOGIES/actions/artifacts/{i}"],
        check=True, capture_output=True, text=True)
    m = json.loads(response.stdout)
    run = m.get("workflow_run") or {}
    if not (
        m.get("id") == i
        and m.get("name") == RECOVERY_ARCHIVE["name"]
        and m.get("digest") == "sha256:" + RECOVERY_ARCHIVE["sha256"]
        and m.get("expired") is False
        and run.get("id") == RECOVERY_ARCHIVE["run_id"]
        and run.get("head_sha") == RECOVERY_ARCHIVE["head_sha"]
    ):
        raise ValueError("authenticated GitHub archive provenance drift")


def verify_archive(path: Path, protected_report: Path | None = None) -> dict[str, Any]:
    if not path.is_file() or file_sha(path) != RECOVERY_ARCHIVE["sha256"]:
        raise ValueError("actual October replay ZIP SHA-256 mismatch")

    with zipfile.ZipFile(path) as z:
        members = z.namelist()
        if len(members) != len(set(members)):
            raise ValueError("duplicate ZIP entry names")

        def only_one(suffix: str) -> str:
            found = [n for n in members if n.endswith(suffix)]
            if len(found) != 1:
                raise ValueError("missing or ambiguous ZIP member " + suffix)
            return found[0]

        def load(name: str) -> Any:
            if name not in members:
                raise ValueError("missing ZIP member " + name)
            return json.loads(z.read(name).decode("utf-8"))

        receipt = load("tmp/TCM-QDEC-COMPARE-001-exact-head.json")
        expected_receipt = {
            **REPLAY_RECEIPT_COMMON,
            "evaluated_commit": RECOVERY_ARCHIVE["head_sha"],
            "runtime_head": RECOVERY_ARCHIVE["head_sha"],
        }
        if receipt != expected_receipt:
            raise ValueError("true October replay receipt identity drift")

        report = load("tmp/TCM-QDEC-COMPARE-001-report.json")
        unsigned = dict(report)
        if unsigned.pop("payload_sha256", None) != REPORT_SHA or canonical_sha(unsigned) != REPORT_SHA:
            raise ValueError("protected full report payload drift")
        if report.get("manifest", {}).get("payload_sha256") != MANIFEST_SHA:
            raise ValueError("protected compared-manifest identity drift")
        if protected_report is not None:
            baseline = json.loads(protected_report.read_text(encoding="utf-8"))
            if baseline != report:
                raise ValueError("recovered report differs from current protected public report")

        corpus = json.loads(z.read(only_one("/TCM-QDEC-COMPARE-001-C90-corpus.json")))
        if not isinstance(corpus, list) or len(corpus) != 347 or canonical_sha(corpus) != CORPUS_SHA:
            raise ValueError("frozen C90 input corpus coverage/hash drift")

        methods: dict[str, Any] = {}
        for method, expected in CONVENTIONAL.items():
            cell = load(f"tmp/compare-cells/C90-{method}.json")
            if not isinstance(cell, dict) or set(cell) != CELL_ALL_KEYS:
                raise ValueError("conventional cell structure/key drift: " + method)
            subject = {k: cell[k] for k in CELL_SUBJECT_KEYS}
            outcomes = cell.get("outcomes")
            if not (
                cell["cell_payload_sha256"] == expected["cell_sha256"]
                and canonical_sha(subject) == expected["cell_sha256"]
                and cell["experiment_id"] == "TCM-QDEC-COMPARE-001"
                and cell["manifest_payload_sha256"] == MANIFEST_SHA
                and cell["surface"] == "C90"
                and cell["method"] == method
                and cell["corpus_size"] == 347
                and isinstance(outcomes, list)
                and len(outcomes) == 347
                and all(type(x) is bool for x in outcomes)
                and canonical_sha(outcomes) == expected["outcomes_sha256"]
                and sum(outcomes) == expected["success"]
                and cell["result_records_sha256"] == expected["results_sha256"]
                and report.get("cell_payload_sha256", {}).get("C90/" + method)
                    == expected["cell_sha256"]
                and report.get("detailed_result_record_digests", {}).get("C90/" + method)
                    == expected["results_sha256"]
            ):
                raise ValueError("C90 per-input conventional outcomes digest/record drift: " + method)
            methods[method] = {
                "success": expected["success"],
                "outcomes_sha256": expected["outcomes_sha256"],
                "cell_sha256": expected["cell_sha256"],
                "result_records_sha256": expected["results_sha256"],
            }
    return {
        "record_type": "QTR_C90_CONVENTIONAL_REPLAY_INTAKE/1",
        "status": "OCTOBER_REPLAY_CONTENT_EQUIVALENCE_VERIFIED__ORIGINAL_AUGUST_ZIP_NOT_VERIFIED",
        "frozen_reference_head": SOURCE_HEAD,
        "actual_october_source": {
            "artifact_id": RECOVERY_ARCHIVE["artifact_id"],
            "run_id": RECOVERY_ARCHIVE["run_id"],
            "head_sha": RECOVERY_ARCHIVE["head_sha"],
            "archive_sha256": RECOVERY_ARCHIVE["sha256"],
        },
        "original_august_source": ORIGINAL_ARCHIVE,
        "frozen_corpus_sha256": CORPUS_SHA,
        "protected_report_sha256": REPORT_SHA,
        "methods": methods,
        "scoring_performed": False,
        "new_decoder_quality_exposed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--protected-report", type=Path)
    parser.add_argument("--check-github-metadata", action="store_true")
    args = parser.parse_args()
    if args.check_github_metadata:
        check_github_metadata()
    result = verify_archive(args.archive, args.protected_report)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
