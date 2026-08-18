from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "reference"
if str(REFERENCE) not in sys.path:
    sys.path.insert(0, str(REFERENCE))

import qec_circuit_002 as Q2
import qec_circuit_002_evidence as E2


class QecCircuit002Tests(unittest.TestCase):
    def test_manifest_is_preoutcome_frozen(self) -> None:
        manifest = Q2.load_manifest()
        self.assertEqual(
            manifest["status"],
            "preoutcome_representation_family_frozen_before_successor_width_inspection",
        )
        self.assertFalse(manifest["representation_family_mutable_after_width_inspection"])
        self.assertEqual(
            [row["id"] for row in manifest["representations"]],
            list(Q2.REPRESENTATIONS[1:]),
        )
        self.assertEqual(
            manifest["resource_envelope"]["peak_joint_table_entries"], 1 << 20
        )
        self.assertFalse(manifest["structural_policy"]["stochastic_search_authorized"])
        self.assertFalse(manifest["structural_policy"]["post_outcome_order_tuning_authorized"])

    def test_semantic_receipts_are_exact(self) -> None:
        receipts = Q2.semantic_receipts()
        r1 = receipts["R1_TERMINAL_DIRECT_AUX"]
        r2 = receipts["R2_TERMINAL_CHAIN_AUX"]
        r3 = receipts["R3_CAUSAL_STATE_CHAIN"]
        for row in receipts.values():
            self.assertEqual(
                row["status"],
                "TEMPORAL_DECOMPOSITION_SEMANTIC_EQUIVALENCE_CERTIFIED",
            )
            self.assertTrue(row["unique_auxiliary_extension"])
            self.assertTrue(row["exact_marginal_recovery"])
        self.assertEqual(
            r1["terminal_relation"]["satisfying_truth_table_sha256"],
            "ee26e328e893db21dbd860887541edc44545515ca583e77d257fce3d82f175bc",
        )
        self.assertEqual(
            r2["terminal_chain"]["satisfying_truth_table_sha256"],
            "58a2480b08b25bb23ad3643ce7c9c799f8ac7c2990490ddfe98f022fb2feb4de",
        )
        self.assertEqual(
            r1["selector_rewrite"]["receipt_sha256"],
            "2a7c7aabf03c645ba3028d7989c551d82b7ebfb001c9f17cc902bc803dd8e2d9",
        )
        self.assertEqual(r3["syndrome_increment"]["relations_checked"], 21)
        self.assertEqual(
            r3["syndrome_increment"]["receipt_sha256"],
            "a072cb066a3f7a780b491dc7c5bb771b5fe914506ef3cf5585bcd28504f3e1e8",
        )
        self.assertEqual(r3["detector_rewrite"]["assignments_checked"], 4494)
        self.assertEqual(
            r3["detector_rewrite"]["receipt_sha256"],
            "0ef88c6ac026714ad9132ce38759268c969f4557595c728e3d990b9e5962497d",
        )

    def test_structural_rows_reproduce_frozen_outcome(self) -> None:
        manifest = Q2.load_manifest()
        cap = manifest["resource_envelope"]["peak_joint_table_entries"]
        rows = [Q2.structural_row(rep, cap) for rep in Q2.REPRESENTATIONS]
        self.assertEqual(
            [row["orders"]["deterministic_min_fill"]["induced_width"] for row in rows],
            [34, 36, 36, 36],
        )
        self.assertEqual(
            rows[0]["factor_scope_sha256"],
            "cfa139dc874a162d6ad23c3ab9b48d3830b42c9ee2221676d73d0ebf8fa4f733",
        )
        self.assertEqual(
            [row["status"] for row in rows],
            ["TEMPORAL_DECOMPOSITION_EXACT_BOUND_EXHAUSTED"] * 4,
        )
        self.assertTrue(all(row["stopped_before_table_materialization"] for row in rows))
        self.assertTrue(
            all(
                row["orders"]["deterministic_min_fill"]["peak_joint_table_entries"]
                > cap
                for row in rows
            )
        )

    def test_full_report_and_compact_evidence_are_bound(self) -> None:
        manifest = Q2.load_manifest()
        full = Q2.build_report(manifest)
        self.assertEqual(
            full["payload_sha256"],
            "90d73b06e3778fea7322435f1ff7db74fc3cb708038057ef338643082aa25c28",
        )
        self.assertEqual(
            full["adjudication_candidate"],
            "TEMPORAL_PREDECLARED_DECOMPOSITION_FAMILY_EXHAUSTED",
        )
        self.assertFalse(full["quality_boundary"]["temporal_tcm_quality_defined"])
        self.assertFalse(
            full["quality_boundary"]["conventional_vs_tcm_quality_ordering_defined"]
        )
        compact = E2.project(full)
        committed = json.loads(
            (ROOT / "evidence/QEC-CIRCUIT-002-report.json").read_text(encoding="utf-8")
        )
        self.assertEqual(compact, committed)
        claimed = committed.pop("payload_sha256")
        self.assertEqual(
            claimed,
            "cb9915e3d9bb32dc5abf1705c3dc7709082b79e3c5b91b391fb2aca0e632fcc3",
        )
        self.assertEqual(Q2.digest(committed), claimed)

    def test_registry_remains_candidate_and_no_downstream_authority(self) -> None:
        registry = json.loads(
            (ROOT / "registry/qec-circuit-002.json").read_text(encoding="utf-8")
        )["experiments"][0]
        self.assertEqual(registry["status"], "candidate_executable_not_promoted")
        self.assertFalse(registry["quality_boundary"]["temporal_tcm_quality_defined"])
        self.assertFalse(registry["claim_boundary"]["qec_circuit_003_authorized"])
        self.assertFalse(registry["claim_boundary"]["qldpc_forge_authorized"])
        self.assertFalse(registry["claim_boundary"]["intrinsic_intractability_claim"])


if __name__ == "__main__":
    unittest.main()
