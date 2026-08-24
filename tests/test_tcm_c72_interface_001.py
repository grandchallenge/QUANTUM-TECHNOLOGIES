from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "reference"
if str(REFERENCE) not in sys.path:
    sys.path.insert(0, str(REFERENCE))

import tcm_c72_interface_001 as C72


def test_manifest_self_verifies_and_c90_remains_closed() -> None:
    manifest = C72.load_manifest()
    assert manifest["manifest_payload_sha256"] == C72.MANIFEST_PAYLOAD
    assert manifest["claim_boundary"]["c90_execution_authorized"] is False
    assert manifest["claim_boundary"]["new_c90_bound_refinement_authorized"] is False
    assert manifest["resource_policy"]["historical_deterministic_caps_are_scientific_stop_rules"] is False


def test_decoder_signature_has_no_injected_error() -> None:
    signature = inspect.signature(C72.decode_c72_syndrome)
    names = set(signature.parameters)
    assert names == {"full_hz_syndrome", "channel_metadata", "context"}
    assert "error" not in names
    assert "injected_error" not in names


def test_gf2_inverse_roundtrip_on_nontrivial_basis() -> None:
    columns = [0b101, 0b110, 0b111]
    assert C72.gf2_rank(columns) == 3
    inverse = C72.inverse_columns(columns, 3)
    for target in range(8):
        coordinate = C72.apply_inverse(inverse, target)
        rebuilt = 0
        for index, column in enumerate(columns):
            if (coordinate >> index) & 1:
                rebuilt ^= column
        assert rebuilt == target


def test_decision_rule_uses_score_then_canonical_class_tie() -> None:
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
    assert out["sum_product_bsc_p_0_1"]["logical_class"] == 1
    assert out["sum_product_bsc_p_0_1"]["tied_canonical_keys"] == [3, 7]
    assert out["soft_tropical_base_2"]["logical_class"] == 1
    assert out["min_plus_hamming"]["logical_class"] == 1


def test_shard_assignment_is_complete_and_disjoint() -> None:
    indices = list(range(329))
    for count in (1, 2, 7, 32, 64):
        shards = [[index for index in indices if index % count == shard] for shard in range(count)]
        flattened = [index for shard in shards for index in shard]
        assert sorted(flattened) == indices
        assert len(flattened) == len(set(flattened))


def test_c72_static_selector_map_is_invertible_without_decoder_output() -> None:
    context = C72.load_c72_context()
    assert C72.gf2_rank(context["functional_columns"]) == 42
    assert context["descriptor_meta"]["canonical_sha256"] == C72.A1S.EXPECTED_DIGESTS["compiled_descriptor"]
    assert len(context["inverse"]) == 42


def test_frozen_c72_corpus_replays_without_decoder_output() -> None:
    records = C72.c72_corpus_records()
    assert len(records) == 329
    assert C72.digest(records) == C72.C72_CORPUS_SHA
