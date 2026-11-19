"""Bounded engineering tests: replay provenance cannot be silently substituted."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "reference"))
import qtr_c90_conventional_recovery_001 as Recovery
import qtr_c90_exact_decoder_001 as Base
import qtr_c90_exact_execute_001 as Execute


class TestC90ConventionalReplayRecovery(unittest.TestCase):
    def test_constants_preserve_original_and_distinct_replay(self):
        s = Recovery.RECOVERY_SPEC
        self.assertNotEqual(s["artifact_id"], Execute.HISTORICAL_COMPARE_ARTIFACT_ID)
        self.assertNotEqual(s["head_sha"], Execute.HISTORICAL_COMPARE_HEAD)
        self.assertNotEqual("sha256:" + s["archive_sha256"],
                            Execute.HISTORICAL_COMPARE_ARTIFACT_DIGEST)
        self.assertEqual(Recovery.REPLAY_HEAD_COMMON["report_payload_sha256"],
                         Execute.HISTORICAL_COMPARE_REPORT_PAYLOAD)
        self.assertEqual(set(Execute.EXPECTED_CONVENTIONAL_CELLS),
                         set(Execute.EXPECTED_CONVENTIONAL_OUTCOMES))
        self.assertEqual(set(Execute.EXPECTED_CONVENTIONAL_CELLS),
                         set(Base.EXPECTED_CONVENTIONAL))

    def test_unverified_byte_stream_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            invalid = Path(td) / "invalid.zip"
            invalid.write_bytes(b"fake historical ZIP")
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                Recovery.verified_replay_outcomes(invalid)

    def test_corrections_must_be_fixed_before_any_comparison(self):
        with tempfile.TemporaryDirectory() as td:
            fixed = Path(td) / "fixed.json"
            fixed.write_text(json.dumps({
                "status": "C90_EXACT_CORRECTIONS_FIXED",
                "quality_exposed": True,  # illegal premature exposure
                "activation_head": Recovery.Campaign.ACTIVATION_HEAD,
                "orchestration_head": "exact-head",
                "fixed_decoder_rows": [],
            }))
            with self.assertRaisesRegex(ValueError, "ordering/identity gate"):
                Recovery.score_fixed_verified_replay(fixed, Path(td), "exact-head",
                                                     Path(td) / "result.json")
            self.assertFalse((Path(td) / "result.json").exists())

    @unittest.skipUnless(os.environ.get("QTR_C90_RECOVERY_ARCHIVE"),
                         "requires byte-verified real historical replay ZIP")
    def test_pinned_real_archive_exact_replay(self):
        result = Recovery.verified_replay_outcomes(
            Path(os.environ["QTR_C90_RECOVERY_ARCHIVE"]))
        self.assertEqual(result["source"]["artifact_id"],
                         Recovery.RECOVERY_SPEC["artifact_id"])
        self.assertTrue(result["source"]["protected_original_archive_not_byte_verified"])
        self.assertEqual(
            {k: v["oracle_success"] for k, v in result["methods"].items()},
            {"BP_MIN_SUM": 200, "BP_OSD_CS_7": 211, "BP_SUM_PRODUCT": 171},
        )


if __name__ == "__main__":
    unittest.main()
