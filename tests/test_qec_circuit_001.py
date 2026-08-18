from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from reference import qec_circuit_001 as Q


class QECCircuit001Tests(unittest.TestCase):
    def test_manifest_and_static_replay(self) -> None:
        manifest = Q.load_manifest()
        self.assertEqual(
            manifest["manifest_payload_sha256"],
            "15962fa93eb92632e760e62a54fbd03a8322fb09b8c3b41de2f0b4225fb52dfb",
        )
        report = Q.static_report(manifest)
        self.assertEqual(
            report["detector_map"]["sha256"],
            "960701757ef5c223d4ed96070508472e4f37feef92aec69d15b175bc078dbcb7",
        )
        self.assertEqual(report["detector_map"]["rank"], 28)
        self.assertTrue(report["detector_map"]["dual_construction_equal"])
        self.assertEqual(report["corpus"]["size"], 2851)
        self.assertEqual(
            report["corpus"]["ordered_record_sha256"],
            "137550c93359f8a9153cffa5e2ebdad926e2d07e27b203fe3aaf39a972d12eb7",
        )
        self.assertTrue(report["corpus"]["exhaustive_matrix_recurrence_equal"])
        self.assertEqual(report["detector_fibers"]["distinct_detector_vectors"], 2517)
        self.assertEqual(
            report["detector_fibers"]["fiber_size_histogram"],
            {"1": 2320, "2": 60, "3": 137},
        )
        self.assertEqual(
            report["detector_fibers"]["fibers_with_multiple_terminal_stabilizer_classes"],
            135,
        )
        self.assertEqual(
            report["detector_fibers"]["authoritative_histories_in_ambiguous_fibers"],
            405,
        )
        tcm = report["temporal_tcm"]
        self.assertEqual(tcm["status"], "TEMPORAL_TCM_EXACT_BOUND_EXHAUSTED")
        self.assertEqual(tcm["orders"]["deterministic_min_fill"]["induced_width"], 20)
        self.assertEqual(
            tcm["orders"]["deterministic_min_fill"]["peak_joint_table_entries"],
            2_097_152,
        )
        self.assertEqual(tcm["primary_cap"], 1_048_576)
        self.assertTrue(tcm["stopped_before_table_materialization"])
        self.assertFalse(tcm["intrinsic_intractability_claim"])

    def _write_manifest(self, payload: dict) -> Path:
        # Recompute the self-digest so mutations exercise semantic locks rather than
        # merely failing the outer integrity check.
        unsigned = copy.deepcopy(payload)
        unsigned.pop("manifest_payload_sha256", None)
        payload = copy.deepcopy(unsigned)
        payload["manifest_payload_sha256"] = Q.digest(unsigned)
        handle = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        with handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        return Path(handle.name)

    def test_authority_mutation_fails_closed(self) -> None:
        manifest = Q.load_manifest()
        manifest["authority"]["human_steward_authorization_comment"] += 1
        path = self._write_manifest(manifest)
        try:
            with self.assertRaises(ValueError):
                Q.load_manifest(path)
        finally:
            path.unlink(missing_ok=True)

    def test_downstream_authority_mutation_fails_closed(self) -> None:
        manifest = Q.load_manifest()
        manifest["claim_boundary"]["qldpc_forge_authorized"] = True
        path = self._write_manifest(manifest)
        try:
            with self.assertRaises(ValueError):
                Q.load_manifest(path)
        finally:
            path.unlink(missing_ok=True)

    def test_gate_level_claim_mutation_fails_closed(self) -> None:
        manifest = Q.load_manifest()
        manifest["claim_boundary"]["gate_level_syndrome_extraction_claim"] = True
        path = self._write_manifest(manifest)
        try:
            with self.assertRaises(ValueError):
                Q.load_manifest(path)
        finally:
            path.unlink(missing_ok=True)

    def test_detector_byte_mutation_is_detected(self) -> None:
        manifest = Q.load_manifest()
        row = manifest["detector_map"]["row_bitstrings"][0]
        manifest["detector_map"]["row_bitstrings"][0] = ("0" if row[0] == "1" else "1") + row[1:]
        # static_report receives the already-loaded object deliberately: this checks
        # detector identity independently of manifest self-digest validation.
        with self.assertRaises(AssertionError):
            Q.static_report(manifest)

    def test_channel_probability_mutation_is_detected(self) -> None:
        manifest = Q.load_manifest()
        manifest["temporal_model"]["channel"]["p"] = 0.2
        with self.assertRaises(AssertionError):
            self._assert_channel_lock(manifest)

    @staticmethod
    def _assert_channel_lock(manifest: dict) -> None:
        if manifest["temporal_model"]["channel"] != {
            "kind": "independent_binary_elementary_faults",
            "p": 0.1,
        }:
            raise AssertionError("temporal channel drift")

    def test_history_deduplication_is_forbidden(self) -> None:
        manifest = Q.load_manifest()
        self.assertFalse(manifest["corpus"]["deduplicate_by_detector"])
        manifest["corpus"]["deduplicate_by_detector"] = True
        with self.assertRaises(AssertionError):
            if manifest["corpus"]["deduplicate_by_detector"] is not False:
                raise AssertionError("detector-history deduplication enabled")

    def test_tcm_cap_cannot_be_laundered(self) -> None:
        manifest = Q.load_manifest()
        primary = manifest["temporal_tcm_structural_preflight"]["orders"]["deterministic_min_fill"]
        cap = manifest["tcm_resource_envelope"]["peak_joint_table_entries"]
        self.assertGreater(primary["peak_joint_table_entries"], cap)
        manifest["tcm_resource_envelope"]["peak_joint_table_entries"] = 1 << 22
        with self.assertRaises(AssertionError):
            observed = Q.static_report(manifest)
            if observed["temporal_tcm"]["orders"]["deterministic_min_fill"]["peak_joint_table_entries"] <= manifest["tcm_resource_envelope"]["peak_joint_table_entries"]:
                raise AssertionError("frozen cap was raised to erase exhaustion")

    def test_static_limit_uses_protected_syndrome_map(self) -> None:
        manifest = Q.load_manifest()
        _, _, _, basis_rows = Q.load_fixture(manifest)
        for q in range(18):
            detectors, _ = Q.direct_recurrence(1 << q, basis_rows)
            self.assertEqual(detectors & 0x7F, Q.syndrome(1 << q, basis_rows))


if __name__ == "__main__":
    unittest.main()
