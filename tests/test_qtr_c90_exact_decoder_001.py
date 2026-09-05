from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "reference"
if str(REFERENCE) not in sys.path:
    sys.path.insert(0, str(REFERENCE))

import qtr_c90_exact_decoder_001 as C90


class QTRC90ExactDecoder001Tests(unittest.TestCase):
    def test_manifest_self_verifies_and_resource_caps_are_not_scientific_gates(self) -> None:
        manifest = C90.load_manifest()
        self.assertEqual(manifest["manifest_payload_sha256"], C90.MANIFEST_PAYLOAD)
        self.assertIs(
            manifest["resource_policy"]["historical_deterministic_caps_are_scientific_stop_rules"],
            False,
        )
        self.assertIs(manifest["representation"]["approximation_or_pruning"], False)
        self.assertIs(manifest["execution_method"]["post_outcome_tuning"], False)

    def test_protected_c90_reconstruction_and_dimensions(self) -> None:
        context = C90.load_c90_context()
        self.assertEqual(context["hx_rank"], 41)
        self.assertEqual(context["hz_rank"], 41)
        self.assertEqual(len(context["code"]["logical_z"]), 8)
        self.assertEqual(len(context["code"]["selector_basis_qubits"]), 49)
        self.assertEqual(context["min_fill_order_sha256"], C90.EXPECTED_MIN_FILL_ORDER_SHA)
        self.assertEqual(context["full_order_record_sha256"], C90.EXPECTED_FULL_ORDER_RECORD_SHA)

    def test_selector_functional_map_is_invertible(self) -> None:
        context = C90.load_c90_context()
        self.assertEqual(C90.C72.gf2_rank(context["functional_columns"]), 49)
        for target in range(49):
            coordinate = context["inverse"][target]
            rebuilt = 0
            for index, column in enumerate(context["functional_columns"]):
                if (coordinate >> index) & 1:
                    rebuilt ^= column
            self.assertEqual(rebuilt, 1 << target)

    def test_frozen_307_selector_validation_set_replays(self) -> None:
        coordinates = C90.frozen_validation_coordinates()
        self.assertEqual(len(coordinates), 307)
        self.assertEqual(C90.digest(coordinates), C90.C90_VALIDATION_SET_SHA)

    def test_frozen_c90_corpus_replays(self) -> None:
        records = C90.c90_corpus_records()
        self.assertEqual(len(records), 347)
        self.assertEqual(C90.digest(records), C90.C90_CORPUS_SHA)

    def test_protected_conventional_anchors_replay(self) -> None:
        self.assertEqual(C90.verify_conventional_anchors(), C90.EXPECTED_CONVENTIONAL)

    def test_c72_predecessor_is_certified(self) -> None:
        receipt = C90.verify_c72_predecessor()
        self.assertEqual(receipt["outcome"], C90.C72_OUTCOME)

    def test_decoder_signature_has_no_injected_error(self) -> None:
        signature = inspect.signature(C90.decode_c90_syndrome)
        names = set(signature.parameters)
        self.assertEqual(names, {"full_hz_syndrome", "channel_metadata", "compiled", "context"})
        self.assertNotIn("error", names)
        self.assertNotIn("injected_error", names)

    def test_preflight_exposes_no_c90_quality(self) -> None:
        report = C90.preflight()
        self.assertEqual(report["status"], "PREFLIGHT_PASS__NO_C90_DECODER_QUALITY")
        self.assertIs(report["quality_exposed"], False)
        self.assertEqual(report["c90_static"]["logical_classes_per_syndrome"], 256)
        self.assertEqual(report["c90_static"]["corpus_size"], 347)


if __name__ == "__main__":
    unittest.main()
