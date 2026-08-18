from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from reference import qec_circuit_001 as B
from reference import qec_circuit_001_exact as Q


class QECCircuit001Tests(unittest.TestCase):
    def test_amended_manifest_and_static_replay(self) -> None:
        manifest = B.load_manifest()
        amendment = Q.load_amendment()
        self.assertEqual(
            manifest["manifest_payload_sha256"],
            "15962fa93eb92632e760e62a54fbd03a8322fb09b8c3b41de2f0b4225fb52dfb",
        )
        self.assertEqual(
            amendment["amendment_payload_sha256"],
            "8be8637ef976c9096b22259f0f849e2350a997b80038f4815302fbefa5f2ad19",
        )
        report = Q.static_report(manifest, amendment)
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
        self.assertEqual(report["quarantined_execution"]["workflow_run"], 32085478805)
        self.assertFalse(report["quarantined_execution"]["scientific_results_admitted"])

        tcm = report["temporal_tcm"]
        self.assertEqual(tcm["status"], "TEMPORAL_TCM_EXACT_BOUND_EXHAUSTED")
        self.assertEqual(tcm["factor_representation"]["factor_count"], 107)
        self.assertEqual(
            tcm["factor_representation"]["factor_scope_arity_histogram"],
            {"1": 82, "7": 7, "8": 14, "12": 2, "18": 2},
        )
        self.assertEqual(tcm["orders"]["deterministic_min_fill"]["induced_width"], 34)
        self.assertEqual(
            tcm["orders"]["deterministic_min_fill"]["peak_joint_table_entries"],
            34_359_738_368,
        )
        self.assertEqual(tcm["primary_cap"], 1_048_576)
        self.assertTrue(tcm["stopped_before_table_materialization"])
        self.assertFalse(tcm["intrinsic_intractability_claim"])
        self.assertEqual(
            tcm["correction_representative"]["table_sha256"],
            "bb3b6e56891c6858684e6f61eace6d56bbbd4f26b026636197c2b8031cbafce7",
        )

    def _write_base_manifest(self, payload: dict) -> Path:
        unsigned = copy.deepcopy(payload)
        unsigned.pop("manifest_payload_sha256", None)
        payload = copy.deepcopy(unsigned)
        payload["manifest_payload_sha256"] = B.digest(unsigned)
        handle = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        with handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        return Path(handle.name)

    def _write_amendment(self, payload: dict) -> Path:
        unsigned = copy.deepcopy(payload)
        unsigned.pop("amendment_payload_sha256", None)
        payload = copy.deepcopy(unsigned)
        payload["amendment_payload_sha256"] = B.digest(unsigned)
        handle = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        with handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        return Path(handle.name)

    def test_authority_mutation_fails_closed(self) -> None:
        manifest = B.load_manifest()
        manifest["authority"]["human_steward_authorization_comment"] += 1
        path = self._write_base_manifest(manifest)
        try:
            with self.assertRaises(ValueError):
                B.load_manifest(path)
        finally:
            path.unlink(missing_ok=True)

    def test_downstream_authority_mutation_fails_closed(self) -> None:
        manifest = B.load_manifest()
        manifest["claim_boundary"]["qldpc_forge_authorized"] = True
        path = self._write_base_manifest(manifest)
        try:
            with self.assertRaises(ValueError):
                B.load_manifest(path)
        finally:
            path.unlink(missing_ok=True)

    def test_quarantine_mutation_fails_closed(self) -> None:
        amendment = Q.load_amendment()
        amendment["quarantined_execution"]["scientific_results_admitted"] = True
        path = self._write_amendment(amendment)
        try:
            with self.assertRaises(ValueError):
                Q.load_amendment(path)
        finally:
            path.unlink(missing_ok=True)

    def test_outcome_driven_repair_flag_fails_closed(self) -> None:
        amendment = Q.load_amendment()
        amendment["repair"]["outcome_driven"] = True
        path = self._write_amendment(amendment)
        try:
            with self.assertRaises(ValueError):
                Q.load_amendment(path)
        finally:
            path.unlink(missing_ok=True)

    def test_detector_byte_mutation_is_detected(self) -> None:
        manifest = B.load_manifest()
        amendment = Q.load_amendment()
        row = manifest["detector_map"]["row_bitstrings"][0]
        manifest["detector_map"]["row_bitstrings"][0] = ("0" if row[0] == "1" else "1") + row[1:]
        with self.assertRaises(AssertionError):
            Q.static_report(manifest, amendment)

    def test_logical_selector_mutation_is_detected(self) -> None:
        manifest = B.load_manifest()
        amendment = Q.load_amendment()
        row = amendment["temporal_tcm"]["logical_selector"]["basis_bitstrings"][0]
        amendment["temporal_tcm"]["logical_selector"]["basis_bitstrings"][0] = (
            ("0" if row[0] == "1" else "1") + row[1:]
        )
        with self.assertRaises(ValueError):
            Q.static_report(manifest, amendment)

    def test_tcm_cap_cannot_be_laundered(self) -> None:
        manifest = B.load_manifest()
        amendment = Q.load_amendment()
        manifest["tcm_resource_envelope"]["peak_joint_table_entries"] = 1 << 40
        with self.assertRaises(AssertionError):
            Q.static_report(manifest, amendment)

    def test_static_limit_uses_protected_syndrome_map(self) -> None:
        manifest = B.load_manifest()
        _, _, _, basis_rows = B.load_fixture(manifest)
        for q in range(18):
            detectors, _ = B.direct_recurrence(1 << q, basis_rows)
            self.assertEqual(detectors & 0x7F, B.syndrome(1 << q, basis_rows))


if __name__ == "__main__":
    unittest.main()
