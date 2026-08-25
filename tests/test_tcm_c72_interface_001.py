from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "reference"
if str(REFERENCE) not in sys.path:
    sys.path.insert(0, str(REFERENCE))

import tcm_c72_interface_001 as C72


class TCMC72Interface001Tests(unittest.TestCase):
    def test_manifest_self_verifies_and_c90_remains_closed(self) -> None:
        manifest = C72.load_manifest()
        self.assertEqual(manifest["manifest_payload_sha256"], C72.MANIFEST_PAYLOAD)
        self.assertIs(manifest["claim_boundary"]["c90_execution_authorized"], False)
        self.assertIs(manifest["claim_boundary"]["new_c90_bound_refinement_authorized"], False)
        self.assertIs(
            manifest["resource_policy"]["historical_deterministic_caps_are_scientific_stop_rules"],
            False,
        )

    def test_decoder_signature_has_no_injected_error(self) -> None:
        signature = inspect.signature(C72.decode_c72_syndrome)
        names = set(signature.parameters)
        self.assertEqual(names, {"full_hz_syndrome", "channel_metadata", "context"})
        self.assertNotIn("error", names)
        self.assertNotIn("injected_error", names)

    def test_gf2_inverse_roundtrip_on_nontrivial_basis(self) -> None:
        columns = [0b101, 0b110, 0b111]
        self.assertEqual(C72.gf2_rank(columns), 3)
        inverse = C72.inverse_columns(columns, 3)
        for target in range(8):
            coordinate = C72.apply_inverse(inverse, target)
            rebuilt = 0
            for index, column in enumerate(columns):
                if (coordinate >> index) & 1:
                    rebuilt ^= column
            self.assertEqual(rebuilt, target)

    def test_decision_rule_uses_score_then_canonical_class_tie(self) -> None:
        records = [
            {
                "logical_class": 0,
                "score_sum_product": 10,
                "score_soft_tropical": 5,
                "minimum_weight": 2,
                "minimum_representative": 8,
                "canonical_key": 7,
            },
            {
                "logical_class": 1,
                "score_sum_product": 10,
                "score_soft_tropical": 7,
                "minimum_weight": 1,
                "minimum_representative": 4,
                "canonical_key": 3,
            },
        ]
        out = C72.decision_from_class_records(records, 4)
        self.assertEqual(out["sum_product_bsc_p_0_1"]["logical_class"], 1)
        self.assertEqual(out["sum_product_bsc_p_0_1"]["tied_canonical_keys"], [3, 7])
        self.assertEqual(out["soft_tropical_base_2"]["logical_class"], 1)
        self.assertEqual(out["min_plus_hamming"]["logical_class"], 1)

    def test_shard_assignment_is_complete_and_disjoint(self) -> None:
        indices = list(range(329))
        for count in (1, 2, 7, 32, 64):
            shards = [
                [index for index in indices if index % count == shard]
                for shard in range(count)
            ]
            flattened = [index for shard in shards for index in shard]
            self.assertEqual(sorted(flattened), indices)
            self.assertEqual(len(flattened), len(set(flattened)))

    def test_c72_static_selector_map_is_invertible_without_decoder_output(self) -> None:
        context = C72.load_c72_context()
        self.assertEqual(C72.gf2_rank(context["functional_columns"]), 42)
        self.assertEqual(
            context["descriptor_meta"]["canonical_sha256"],
            C72.A1S.EXPECTED_DIGESTS["compiled_descriptor"],
        )
        self.assertEqual(len(context["inverse"]), 42)

    def test_frozen_c72_corpus_replays_without_decoder_output(self) -> None:
        records = C72.c72_corpus_records()
        self.assertEqual(len(records), 329)
        self.assertEqual(C72.digest(records), C72.C72_CORPUS_SHA)


if __name__ == "__main__":
    unittest.main()
