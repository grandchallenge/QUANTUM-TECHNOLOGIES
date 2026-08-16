import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "reference" / "qldpc_fixture_002.py"
SPEC = importlib.util.spec_from_file_location("qldpc_fixture_002", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class QLDPCFixture002Tests(unittest.TestCase):
    def setUp(self):
        self.registry_path = ROOT / "registry" / "qldpc-benchmarks.json"
        self.predecessor_path = ROOT / "evidence" / "QLDPC-FIXTURE-001-report.json"
        self.benchmark = MODULE.load_benchmark(self.registry_path)
        self.predecessor = json.loads(self.predecessor_path.read_text(encoding="utf-8"))

    def test_committed_evidence_exactly_replays(self):
        observed = MODULE.evaluate(self.benchmark, self.predecessor)
        expected = json.loads(
            (ROOT / "evidence" / "QLDPC-FIXTURE-002-report.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(observed, expected)

    def test_frozen_corpus_and_exact_lookup_match_predecessor(self):
        report = MODULE.evaluate(self.benchmark, self.predecessor)
        self.assertEqual(report["corpus"]["actual_error_count"], 4048)
        self.assertEqual(
            report["corpus"]["shell_sizes"],
            {"0": 1, "1": 18, "2": 153, "3": 816, "4": 3060},
        )
        self.assertEqual(
            report["corpus"]["corpus_sha256"],
            "260b1a43cf1d777f28c475918e91a5f7cefc5d28a2bfb556338f7e30058f58a8",
        )
        exact = report["benchmark_results"]["exact_coset_lookup"]
        self.assertEqual(exact["success_total"], 240)
        self.assertEqual(exact["failure_total"], 3808)
        self.assertEqual(
            exact["table_sha256"],
            self.predecessor["reference_decoder"]["table_sha256"],
        )

    def test_simple_decoder_retains_negative_evidence(self):
        report = MODULE.evaluate(self.benchmark, self.predecessor)
        greedy = report["benchmark_results"]["greedy_syndrome_descent"]
        self.assertEqual(greedy["success_total"], 125)
        self.assertEqual(greedy["failure_total"], 3923)
        self.assertEqual(
            greedy["success_counts_by_error_weight"]["2"],
            {"success": 38, "failure": 115, "total": 153},
        )
        self.assertEqual(
            greedy["systems_counters"]["stalled_with_nonzero_syndrome"], 1818
        )
        self.assertTrue(greedy["failure_witnesses"])

    def test_systems_counters_are_deterministic_not_wall_clock_claims(self):
        report = MODULE.evaluate(self.benchmark, self.predecessor)
        exact = report["benchmark_results"]["exact_coset_lookup"]["systems_counters"]
        greedy = report["benchmark_results"]["greedy_syndrome_descent"][
            "systems_counters"
        ]
        self.assertEqual(exact["setup_candidate_errors_considered"], 988)
        self.assertEqual(exact["decode_table_lookups"], 4048)
        self.assertEqual(greedy["decode_iterations_total"], 6570)
        self.assertEqual(greedy["decode_candidate_comparisons"], 150984)
        self.assertFalse(report["deterministic_system_model"]["wall_clock_authoritative"])
        self.assertFalse(report["source_context"]["experiment_decoder"]["executed_by_fixture"])

    def test_predecessor_payload_tamper_fails_closed(self):
        predecessor = copy.deepcopy(self.predecessor)
        predecessor["payload_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            MODULE.evaluate(self.benchmark, predecessor)

    def test_predecessor_authority_tamper_fails_closed(self):
        predecessor = copy.deepcopy(self.predecessor)
        predecessor["claim_boundary"]["threshold_claim"] = True
        predecessor_without_digest = dict(predecessor)
        predecessor_without_digest.pop("payload_sha256")
        predecessor["payload_sha256"] = MODULE.canonical_digest(
            predecessor_without_digest
        )
        with self.assertRaises(ValueError):
            MODULE.evaluate(self.benchmark, predecessor)

    def test_registry_corpus_tamper_fails_closed(self):
        registry = json.loads(self.registry_path.read_text(encoding="utf-8"))
        registry["benchmarks"][0]["corpus"]["max_weight"] = 5
        path = ROOT / "tests" / ".tmp-qldpc-002-registry.json"
        try:
            path.write_text(json.dumps(registry), encoding="utf-8")
            with self.assertRaises(ValueError):
                MODULE.load_benchmark(path)
        finally:
            path.unlink(missing_ok=True)

    def test_registry_downstream_authority_tamper_fails_closed(self):
        registry = json.loads(self.registry_path.read_text(encoding="utf-8"))
        registry["benchmarks"][0]["claim_boundary"]["tcm_qdec_authorized"] = True
        path = ROOT / "tests" / ".tmp-qldpc-002-authority.json"
        try:
            path.write_text(json.dumps(registry), encoding="utf-8")
            with self.assertRaises(ValueError):
                MODULE.load_benchmark(path)
        finally:
            path.unlink(missing_ok=True)

    def test_source_context_tamper_fails_closed(self):
        registry = json.loads(self.registry_path.read_text(encoding="utf-8"))
        registry["benchmarks"][0]["source_context"]["experiment_decoder"][
            "osd_order"
        ] = 8
        path = ROOT / "tests" / ".tmp-qldpc-002-source.json"
        try:
            path.write_text(json.dumps(registry), encoding="utf-8")
            with self.assertRaises(ValueError):
                MODULE.load_benchmark(path)
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
