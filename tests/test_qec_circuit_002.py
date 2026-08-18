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

    def test_local_terminal_auxiliary_relations(self) -> None:
        direct = Q2.terminal_direct_receipt()
        chain = Q2.terminal_chain_receipt()
        self.assertTrue(direct["unique_extension"])
        self.assertTrue(chain["unique_extension"])
        self.assertTrue(chain["terminal_e_matches_direct_xor"])
        self.assertEqual(
            direct["satisfying_truth_table_sha256"],
            "ee26e328e893db21dbd860887541edc44545515ca583e77d257fce3d82f175bc",
        )
        self.assertEqual(
            chain["satisfying_truth_table_sha256"],
            "58a2480b08b25bb23ad3643ce7c9c799f8ac7c2990490ddfe98f022fb2feb4de",
        )

    def test_committed_evidence_is_bound_and_exhausted(self) -> None:
        evidence = json.loads(
            (ROOT / "evidence/QEC-CIRCUIT-002-report.json").read_text(encoding="utf-8")
        )
        claimed = evidence.pop("payload_sha256")
        self.assertEqual(
            claimed,
            "cb9915e3d9bb32dc5abf1705c3dc7709082b79e3c5b91b391fb2aca0e632fcc3",
        )
        self.assertEqual(Q2.digest(evidence), claimed)
        self.assertEqual(
            evidence["full_exact_report_payload_sha256"], E2.EXPECTED_FULL
        )
        self.assertEqual(
            evidence["adjudication_candidate"],
            "TEMPORAL_PREDECLARED_DECOMPOSITION_FAMILY_EXHAUSTED",
        )
        rows = evidence["structural_rows"]
        self.assertEqual(
            [row["orders"]["deterministic_min_fill"]["induced_width"] for row in rows],
            [34, 36, 36, 36],
        )
        self.assertEqual(
            [row["status"] for row in rows],
            ["TEMPORAL_DECOMPOSITION_EXACT_BOUND_EXHAUSTED"] * 4,
        )
        self.assertFalse(evidence["quality_boundary"]["temporal_tcm_quality_defined"])
        self.assertFalse(
            evidence["quality_boundary"]["conventional_vs_tcm_quality_ordering_defined"]
        )

    def test_semantic_receipt_identities_are_committed(self) -> None:
        evidence = json.loads(
            (ROOT / "evidence/QEC-CIRCUIT-002-report.json").read_text(encoding="utf-8")
        )
        semantic = evidence["semantic_equivalence"]
        for row in semantic.values():
            self.assertEqual(
                row["status"],
                "TEMPORAL_DECOMPOSITION_SEMANTIC_EQUIVALENCE_CERTIFIED",
            )
        self.assertEqual(
            semantic["R1_TERMINAL_DIRECT_AUX"]["selector_receipt_sha256"],
            "2a7c7aabf03c645ba3028d7989c551d82b7ebfb001c9f17cc902bc803dd8e2d9",
        )
        self.assertEqual(
            semantic["R3_CAUSAL_STATE_CHAIN"]["syndrome_increment_relations_checked"],
            21,
        )
        self.assertEqual(
            semantic["R3_CAUSAL_STATE_CHAIN"]["syndrome_increment_receipt_sha256"],
            "a072cb066a3f7a780b491dc7c5bb771b5fe914506ef3cf5585bcd28504f3e1e8",
        )
        self.assertEqual(
            semantic["R3_CAUSAL_STATE_CHAIN"]["detector_assignments_checked"],
            4494,
        )
        self.assertEqual(
            semantic["R3_CAUSAL_STATE_CHAIN"]["detector_rewrite_receipt_sha256"],
            "0ef88c6ac026714ad9132ce38759268c969f4557595c728e3d990b9e5962497d",
        )

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
