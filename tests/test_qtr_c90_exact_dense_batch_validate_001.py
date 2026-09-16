from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "reference"
if str(REFERENCE) not in sys.path:
    sys.path.insert(0, str(REFERENCE))

import qtr_c90_exact_decoder_001 as Base
import qtr_c90_exact_dense_aggregate_001 as Aggregate
import qtr_c90_exact_dense_batch_validate_001 as Batch
import qtr_c90_exact_dense_oracle_001 as Dense


class DenseBatchValidationTests(unittest.TestCase):
    def test_shard_partition_exactly_covers_frozen_307(self) -> None:
        coords = Base.frozen_validation_coordinates()
        seen = []
        for shard in range(Batch.SHARD_COUNT):
            start, stop = Batch.shard_bounds(shard, len(coords))
            seen.extend(range(start, stop))
        self.assertEqual(seen, list(range(307)))
        self.assertEqual(Batch.shard_bounds(76), (304, 307))
        with self.assertRaises(ValueError):
            Batch.shard_bounds(77)

    def _fake_reports(self, subject: str):
        coords = [int(v) for v in Base.frozen_validation_coordinates()]
        reports = []
        for algebra, algebra_id in Dense.ALGEBRA_IDS.items():
            for shard in range(Batch.SHARD_COUNT):
                start, stop = Batch.shard_bounds(shard, len(coords))
                indices = list(range(start, stop))
                selected = coords[start:stop]
                report = {
                    "experiment_id": Base.EXPERIMENT_ID,
                    "phase": "QUALITY_BLIND_FROZEN_307_DENSE_SEMANTIC_VALIDATION_SHARD",
                    "status": "C90_EXACT_DENSE_VALIDATION_SHARD_PASSED",
                    "validation_subject_commit": subject,
                    "compiled_source_commit": subject,
                    "algebra": algebra,
                    "algebra_id": algebra_id,
                    "compile_receipt_payload_sha256": f"receipt-{algebra}",
                    "canonical_node_stream_sha256": Batch.EXPECTED_CANONICAL_STREAMS[algebra],
                    "native_binary_sha256": f"binary-{algebra}",
                    "reachable_nodes": 1,
                    "dense_backend": Dense.BACKEND,
                    "validation_set_sha256": Base.C90_VALIDATION_SET_SHA,
                    "frozen_selector_count": 307,
                    "shard_size": Batch.SHARD_SIZE,
                    "shard_count": Batch.SHARD_COUNT,
                    "shard_index": shard,
                    "start_index": start,
                    "stop_index_exclusive": stop,
                    "selector_indices": indices,
                    "selector_coordinates": selected,
                    "results": [
                        {
                            "selector_index": i,
                            "selector_coordinate": c,
                            "native_value_sha256": f"n-{i}",
                            "dense_certificate_sha256": f"d-{i}",
                            "exact_equal": True,
                            "native_reachable_nodes": 1,
                            "native_peak_live_values": 1,
                        }
                        for i, c in zip(indices, selected, strict=True)
                    ],
                    "exact_equal_count": len(indices),
                    "quality_exposed": False,
                    "injected_error_success_used": False,
                    "decoder_execution_performed": False,
                    "scientific_semantics_changed": False,
                }
                report["payload_sha256"] = Base.digest(report)
                reports.append(report)
        return reports

    def test_aggregate_requires_complete_same_head_exact_coverage(self) -> None:
        subject = "a" * 40
        output = Aggregate.aggregate_reports(self._fake_reports(subject), subject_sha=subject)
        self.assertEqual(output["exact_comparison_count"], 921)
        self.assertTrue(output["same_head_compile_and_validation"])
        self.assertTrue(output["activation_eligible"])
        self.assertFalse(output["quality_exposed"])

    def test_aggregate_rejects_semantic_mismatch(self) -> None:
        subject = "b" * 40
        reports = self._fake_reports(subject)
        bad = copy.deepcopy(reports[0])
        bad["results"][0]["exact_equal"] = False
        bad["payload_sha256"] = Base.digest({k: v for k, v in bad.items() if k != "payload_sha256"})
        reports[0] = bad
        with self.assertRaises(ValueError):
            Aggregate.aggregate_reports(reports, subject_sha=subject)


if __name__ == "__main__":
    unittest.main()
