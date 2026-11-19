"""Self-contained and adversarial checks of the C90 quality-blind pilot verifier.

Synthetic fixtures exercise the generic validation logic. Production CLI use
remains pinned to the five immutable original Colab file digests.
"""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "qtr_c90_colab_pilot_verifier", ROOT / "scripts/verify_qtr_c90_colab_pilot_001.py"
)
assert SPEC and SPEC.loader
Pilot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(Pilot)


class TestColabPilotVerifier(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.expected_original = Pilot.EXPECTED_FILES
        rows = [{
            "status": "C90_COMPACT_NATIVE_SELECTOR_EVALUATED",
            "algebra_id": 2,
            "selector_index": i * 256,
            "selector_coordinate": i,
            "reachable_nodes": 1,
            "peak_live_values": 1,
            "minimum_weight": 0,
            "minimum_representative_hex": "0",
            "canonical_hex": "0",
            "quality_exposed": False,
        } for i in range(Pilot.INPUTS)]
        self.write("rows-min_plus_hamming-class-0.jsonl",
                   "".join(json.dumps(x) + "\n" for x in rows))
        rowsha = Pilot.sha256(self.root / "rows-min_plus_hamming-class-0.jsonl")
        self.write("time.txt",
                   "Elapsed (wall clock) time (h:mm:ss or m:ss): 1:36:47\n"
                   "Maximum resident set size (kbytes): 6112280\nExit status: 0\n")
        receipt = {
            "status": "C90_ACTIVATED_SELECTOR_SHARD_EVALUATED",
            "activation_head": Pilot.ACTIVATION,
            "orchestration_head": Pilot.ORCHESTRATION,
            "algebra": Pilot.ALGEBRA, "logical_class": Pilot.CLASS,
            "selector_count": Pilot.INPUTS,
            "quality_exposed": False, "corrections_fixed": False,
            "independent_scoring_performed": False,
            "matched_comparison_performed": False,
            "scientific_semantics_changed": False,
        }
        self.write("receipt-min_plus_hamming-class-0.json", json.dumps(receipt))
        receiptsha = Pilot.sha256(self.root / "receipt-min_plus_hamming-class-0.json")
        marker = {
            "status": "EXTERNAL_SELECTOR_SHARD_COMPLETE",
            "activation_head": Pilot.ACTIVATION,
            "runner_head": Pilot.ORCHESTRATION,
            "algebra": Pilot.ALGEBRA, "logical_class": Pilot.CLASS,
            "selector_count": Pilot.INPUTS, "quality_exposed": False,
            "github_hosted_selector_values_used": False,
            "rows_file_sha256": rowsha,
            "time_file_sha256": Pilot.sha256(self.root / "time.txt"),
        }
        self.write("external-shard.json", json.dumps(marker))
        worker = {
            "stage": "SINGLE_SHARD_COMPLETE",
            "activation_head": Pilot.ACTIVATION,
            "source_head": Pilot.ORCHESTRATION,
            "algebra": Pilot.ALGEBRA, "logical_class": Pilot.CLASS,
            "quality_exposed": False, "rows": Pilot.INPUTS,
            "rows_sha256": rowsha, "marker_sha256": Pilot.sha256(self.root / "external-shard.json"),
            "semantic_receipt_sha256": receiptsha,
        }
        self.write("worker-state.json", json.dumps(worker))
        Pilot.EXPECTED_FILES = {
            name: Pilot.sha256(self.root / name) for name in self.expected_original
        }

    def tearDown(self):
        Pilot.EXPECTED_FILES = self.expected_original
        self.tmp.cleanup()

    def write(self, name, content):
        (self.root / name).write_text(content, encoding="utf-8")

    def repin(self, name):
        Pilot.EXPECTED_FILES[name] = Pilot.sha256(self.root / name)

    def test_valid_quality_blind_fixture(self):
        result = Pilot.verify(self.root)
        self.assertEqual(result["selector_count"], 347)
        self.assertFalse(result["scientific_quality_exposed"])
        self.assertEqual(result["wall_seconds"], 5807)

    def test_corrupted_file_is_rejected_by_digest(self):
        p = self.root / "rows-min_plus_hamming-class-0.jsonl"
        p.write_bytes(p.read_bytes() + b"x")
        with self.assertRaisesRegex(ValueError, "SHA-256 drift"):
            Pilot.verify(self.root)

    def test_even_rehashed_premature_quality_fails_closed(self):
        name = "receipt-min_plus_hamming-class-0.json"
        receipt = json.loads((self.root / name).read_text())
        receipt["quality_exposed"] = True
        self.write(name, json.dumps(receipt))
        self.repin(name)
        with self.assertRaisesRegex(ValueError, "quality/ordering"):
            Pilot.verify(self.root)

    def test_even_rehashed_wrong_selector_order_fails_closed(self):
        name = "rows-min_plus_hamming-class-0.jsonl"
        lines = (self.root / name).read_text().splitlines()
        row = json.loads(lines[1])
        row["selector_index"] = 99
        lines[1] = json.dumps(row)
        self.write(name, "\n".join(lines) + "\n")
        self.repin(name)
        with self.assertRaisesRegex(ValueError, "selector row structure"):
            Pilot.verify(self.root)


if __name__ == "__main__":
    unittest.main()
