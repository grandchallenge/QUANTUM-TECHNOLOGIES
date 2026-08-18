from __future__ import annotations

import json
import unittest
from pathlib import Path

from reference import qec_circuit_001 as B
from reference import qec_circuit_001_exact as Q
from reference import qec_circuit_001_evidence as E

ROOT = Path(__file__).resolve().parents[1]


class QECCircuit001EvidenceTests(unittest.TestCase):
    def test_committed_evidence_self_verifies(self) -> None:
        path = ROOT / "evidence/QEC-CIRCUIT-001-report.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        claimed = data.pop("payload_sha256")
        self.assertEqual(claimed, E.COMPACT_PAYLOAD)
        self.assertEqual(B.digest(data), E.COMPACT_PAYLOAD)
        data["payload_sha256"] = claimed
        self.assertEqual(data["status"], "candidate_executable_not_promoted")
        self.assertEqual(
            data["adjudication_candidate"],
            "TEMPORAL_SUBSTRATE_CERTIFIED__CONVENTIONAL_ROWS_COMPLETED__TCM_EXACT_BOUND_EXHAUSTED",
        )
        self.assertFalse(data["comparison_boundary"]["tcm_quality_defined"])
        self.assertFalse(
            data["comparison_boundary"]["conventional_vs_tcm_quality_ordering_defined"]
        )
        self.assertEqual(
            data["measurement_origin"]["bound_full_exact_report_payload_sha256"],
            E.FULL_REPORT_PAYLOAD,
        )
        self.assertEqual(
            data["manifest_package"]["amendment_payload_sha256"],
            Q.AMENDMENT_PAYLOAD,
        )
        self.assertFalse(data["manifest_package"]["quarantined_results_admitted"])

    def test_registry_binds_candidate_evidence_and_downstream_closure(self) -> None:
        registry = json.loads(
            (ROOT / "registry/qec-circuit-001.json").read_text(encoding="utf-8")
        )
        self.assertEqual(registry["registry_version"], "0.1.0")
        self.assertEqual(len(registry["experiments"]), 1)
        experiment = registry["experiments"][0]
        self.assertEqual(experiment["experiment_id"], "QEC-CIRCUIT-001")
        self.assertEqual(experiment["status"], "candidate_executable_not_promoted")
        self.assertEqual(
            experiment["evidence"]["committed_projection_payload_sha256"],
            E.COMPACT_PAYLOAD,
        )
        self.assertEqual(
            experiment["evidence"]["full_exact_report_payload_sha256"],
            E.FULL_REPORT_PAYLOAD,
        )
        self.assertEqual(
            experiment["manifest"]["amendment_payload_sha256"], Q.AMENDMENT_PAYLOAD
        )
        self.assertFalse(experiment["claim_boundary"]["tcm_quality_defined"])
        self.assertFalse(
            experiment["claim_boundary"]["tcm_vs_conventional_quality_ordering_defined"]
        )
        self.assertFalse(experiment["claim_boundary"]["gate_level_claim"])
        self.assertFalse(experiment["claim_boundary"]["hardware_claim"])
        self.assertFalse(experiment["claim_boundary"]["threshold_claim"])
        self.assertFalse(experiment["claim_boundary"]["qldpc_forge_authorized"])
        self.assertFalse(
            experiment["claim_boundary"]["later_qec_circuit_subgate_authorized"]
        )

    def test_conventional_totals_are_exactly_bound(self) -> None:
        data = json.loads(
            (ROOT / "evidence/QEC-CIRCUIT-001-report.json").read_text(encoding="utf-8")
        )
        expected = {
            "TEMP_BP_MIN_SUM": 2430,
            "TEMP_BP_OSD_CS_7": 2520,
            "TEMP_BP_SUM_PRODUCT": 1736,
        }
        for method, success in expected.items():
            cell = data["conventional_methods"][method]
            self.assertEqual(cell["oracle_success"], success)
            self.assertEqual(cell["oracle_success"] + cell["oracle_failure"], 2851)
            self.assertEqual(cell["declared_failures"], 0)
        pair = data["conventional_pairwise"]["TEMP_BP_MIN_SUM__vs__TEMP_BP_OSD_CS_7"]
        self.assertEqual(pair["left_only_success"], 0)
        self.assertEqual(pair["right_only_success"], 90)
        self.assertEqual(pair["net_left_minus_right"], -90)

    def test_tcm_bound_is_reach_status_not_quality(self) -> None:
        data = json.loads(
            (ROOT / "evidence/QEC-CIRCUIT-001-report.json").read_text(encoding="utf-8")
        )
        tcm = data["temporal_tcm"]
        self.assertEqual(tcm["status"], "TEMPORAL_TCM_EXACT_BOUND_EXHAUSTED")
        self.assertFalse(tcm["quality_defined"])
        self.assertEqual(tcm["induced_width"], 34)
        self.assertEqual(tcm["predicted_peak_joint_table_entries"], 1 << 35)
        self.assertEqual(tcm["frozen_peak_joint_table_cap"], 1 << 20)
        self.assertFalse(tcm["intrinsic_intractability_claim"])


if __name__ == "__main__":
    unittest.main()
