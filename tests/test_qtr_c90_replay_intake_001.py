"""Quality-blind C90 conventional evidence intake: synthetic hostile and real-archive tests.

Synthetic fixtures verify the *verification predicates*, not scientific decoder
results. No exact C90 corrections are generated or scored.
"""
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "c90_replay_intake", ROOT / "scripts/qtr_c90_conventional_replay_intake_001.py"
)
assert SPEC is not None and SPEC.loader is not None
R = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(R)


class TestConventionalReplayIntake(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def synthetic(self, *, bad_head: bool = False, changed_outcomes: bool = False,
                  changed_public: bool = False):
        manuscript = "fixture-manifest"
        receipt = {
            **R.REPLAY_RECEIPT_COMMON,
            "manifest_payload_sha256": manuscript,
            "report_payload_sha256": "",
            "evaluated_commit": R.RECOVERY_ARCHIVE["head_sha"],
            "runtime_head": R.RECOVERY_ARCHIVE["head_sha"],
        }
        if bad_head:
            receipt["runtime_head"] = "not-the-real-october-head"
        corpus = [{"index": i, "fixture": True} for i in range(347)]
        expected_methods = {}
        cells = {}
        report = {
            "manifest": {"payload_sha256": manuscript},
            "cell_payload_sha256": {},
            "detailed_result_record_digests": {},
            "corpus_receipts": {"fixture": True},
            "surfaces": {"C90": {"fixture": "record"}},
            "experiment_id": "TCM-QDEC-COMPARE-001",
        }
        for method, existing in R.CONVENTIONAL.items():
            count = existing["success"]
            outcomes = [i < count for i in range(347)]
            record = {
                "surface": "C90",
                "method": method,
                "package_receipt": {"synthetic": True},
                "corpus_size": 347,
                "summary": {"fixture": True},
                "outcomes": outcomes,
                "result_records_sha256": existing["results_sha256"],
            }
            expected_methods[method] = {
                **existing,
                "outcomes_sha256": R.canonical_sha(outcomes),
                "cell_sha256": R.canonical_sha(record),
            }
            cells[method] = {
                **record,
                "experiment_id": "TCM-QDEC-COMPARE-001",
                "manifest_payload_sha256": manuscript,
                "cell_payload_sha256": expected_methods[method]["cell_sha256"],
            }
            report["cell_payload_sha256"]["C90/" + method] = expected_methods[method]["cell_sha256"]
            report["detailed_result_record_digests"]["C90/" + method] = existing["results_sha256"]

        report_hash = R.canonical_sha(report)
        report["payload_sha256"] = report_hash
        receipt["report_payload_sha256"] = report_hash
        public = {
            "manifest": report["manifest"],
            "cell_payload_sha256": report["cell_payload_sha256"],
            "detailed_result_record_digests": report["detailed_result_record_digests"],
            "corpus_receipts": report["corpus_receipts"],
            "surfaces": {"C90": {"fixture": report["surfaces"]["C90"]["fixture"]}},
            "experiment_id": report["experiment_id"],
            "full_report_payload_sha256": report_hash,
        }
        if changed_public:
            public["surfaces"]["C90"]["fixture"] = "ALTERED-PUBLIC-PROJECTION"
        public["payload_sha256"] = R.canonical_sha(public)

        if changed_outcomes:
            cells["BP_MIN_SUM"]["outcomes"][0] = False

        zpath = self.dir / "synthetic-replay.zip"
        with zipfile.ZipFile(zpath, "w") as z:
            def dump(name, data):
                z.writestr(name, json.dumps(data, sort_keys=True))
            dump("tmp/TCM-QDEC-COMPARE-001-exact-head.json", receipt)
            dump("tmp/TCM-QDEC-COMPARE-001-report.json", report)
            dump("root/TCM-QDEC-COMPARE-001-C90-corpus.json", corpus)
            for method, cell in cells.items():
                dump(f"tmp/compare-cells/C90-{method}.json", cell)
        pubpath = self.dir / "protected-public-report.json"
        pubpath.write_text(json.dumps(public, sort_keys=True))
        overrides = {
            "RECOVERY_ARCHIVE": {**R.RECOVERY_ARCHIVE, "sha256": R.file_sha(zpath)},
            "CONVENTIONAL": expected_methods,
            "REPORT_SHA": report_hash,
            "MANIFEST_SHA": manuscript,
            "CORPUS_SHA": R.canonical_sha(corpus),
            "REPLAY_RECEIPT_COMMON": {**R.REPLAY_RECEIPT_COMMON,
                                      "manifest_payload_sha256": manuscript,
                                      "report_payload_sha256": report_hash},
        }
        return zpath, pubpath, overrides

    def run_fixture(self, *, bad_head=False, changed_outcomes=False, changed_public=False):
        archive, public, overrides = self.synthetic(
            bad_head=bad_head, changed_outcomes=changed_outcomes,
            changed_public=changed_public)
        with patch.multiple(R, **overrides):
            return R.verify_archive(archive, public)

    def test_valid_synthetic_full_pipeline_is_quality_blind(self):
        r = self.run_fixture()
        self.assertFalse(r["scoring_performed"])
        self.assertFalse(r["new_decoder_quality_exposed"])
        self.assertEqual({k: x["success"] for k, x in r["methods"].items()},
                         {"BP_MIN_SUM": 200, "BP_OSD_CS_7": 211, "BP_SUM_PRODUCT": 171})
        self.assertTrue(r["original_august_source"]["byte_verified"] is False)

    def test_wrong_october_head_rejected_even_if_zip_hash_is_rebound(self):
        with self.assertRaisesRegex(ValueError, "October replay receipt"):
            self.run_fixture(bad_head=True)

    def test_rehashed_changed_outcomes_rejected(self):
        with self.assertRaisesRegex(ValueError, "per-input conventional outcomes"):
            self.run_fixture(changed_outcomes=True)

    def test_independently_rehashed_bad_public_projection_rejected(self):
        with self.assertRaisesRegex(ValueError, "public report projection"):
            self.run_fixture(changed_public=True)

    def test_unverified_stream_rejected_first(self):
        p = self.dir / "fake.zip"
        p.write_bytes(b"not a replay archive")
        with self.assertRaisesRegex(ValueError, "October replay ZIP SHA-256 mismatch"):
            R.verify_archive(p)

    @unittest.skipUnless(os.environ.get("QTR_C90_REPLAY_ARCHIVE") and
                         os.environ.get("QTR_C90_PUBLIC_REPORT"),
                         "requires pinned real October replay ZIP and protected main report")
    def test_real_authenticated_replay_and_protected_projection(self):
        r = R.verify_archive(Path(os.environ["QTR_C90_REPLAY_ARCHIVE"]),
                             Path(os.environ["QTR_C90_PUBLIC_REPORT"]))
        self.assertEqual(r["actual_october_source"]["run_id"], 40511661627)
        self.assertTrue(r["original_august_source"]["byte_verified"] is False)
        self.assertFalse(r["scoring_performed"])


if __name__ == "__main__":
    unittest.main()
