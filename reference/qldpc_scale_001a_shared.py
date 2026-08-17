import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVALUATOR_VERSION = "0.1.0"
EXPERIMENT_ID = "QLDPC-SCALE-001A"
PROTECTED_START_MAIN = "54456dd1d273a115e82a77c6c429925e03e0925e"
AUTHORIZATION_ISSUE = 58
AUTHORIZATION_COMMENT = 5312914299
REFEREE_COMMENT = 5312522572
EXECUTION_ISSUE = 59
INSTRUMENTATION_COMMENT = 5314475782

PREDECESSOR = {
    "experiment_id": "TCM-QDEC-004",
    "reviewed_head": "8177a57b63e3f2c953a028691d305563f298b572",
    "scientific_merge_commit": "7eff1025e97ff962a6fed81e6f2fa0f4d14653a3",
    "promotion_record_path": "reviews/QTR-TCM-QDEC-REVIEW-004/promotion-record.json",
    "promotion_record_blob_sha": "aaeae5bb9d02f96ac7d8aba865167be04aa91d04",
    "registry_blob_sha": "616f9ca9d81123f5b04d445e1ae5ca01e9559c85",
    "evidence_blob_sha": "77b6a05ff245d0292036b7efa47a3fe775f845af",
    "evidence_payload_sha256": "a5c7e59fa849ddc37c070d78d4a4dab8b07ae5ceccfecefeb5a20f4ae0dc83a7",
}

SOURCE = {
    "source_repository": "sbravyi/BivariateBicycleCodes",
    "source_commit": "fa77e3333d3ec44c79d8f914dd24c040d1da471b",
    "source_path": "decoder_setup.py",
    "source_blob_sha": "7ec5a36732a2a6dd229ab74405dedf36139ccda4",
    "paper": "Bravyi et al., High-threshold and low-overhead fault-tolerant quantum memory, arXiv:2308.07915v2 / Nature 627 (2024)",
    "code_parameters_source_reported": [72, 12, 6],
    "ell": 6,
    "m": 6,
    "a_exponents": [3, 1, 2],
    "b_exponents": [3, 1, 2],
    "A": "x^3+y^1+y^2",
    "B": "y^3+x^1+x^2",
    "Hx": "[A|B]",
    "Hz": "[B^T|A^T]",
    "distance_status": "SOURCE_REPORTED_DISTANCE",
}

EXPECTED_DIGESTS = {
    "source_record": "6d77562cf27dc9eb8d27d4e8c5601f61c0f69cf74dd4cab1b76d6de39e2a35a3",
    "hx": "6c01bd1eceb703a1afbd9897c9ce3810d951bc0d1284588607775e9f875740f2",
    "hz": "01f8c7d756f3056faaa40cbe20e2c68091f65b582de5abb42e99d0e5b07a5c3d",
    "independent_bases": "b2292e3d8ebe4e60bf9991b75fbc51bad85a17adec083a4aba90e96ea4380bb4",
    "logical_basis": "873defa9ab063538fd406b8b0cf5a09b3a91d8b66514795435761d51d697541f",
    "selector_basis": "26a3b1ded24edbd0498eb915b7c3209db309be4a1cff8446149d2f78e0f7e524",
    "factor_scopes": "c4b54c5ed2da67753608d13777ac02ff43872ca0688598a6b6cfc74502531c47",
    "orders": "304b71f9046a7675c696b97fa7cc1cb0e7d1f14c4a6831e7d89f2f411a7fae4a",
    "compiled_descriptor": "c47e85efbad65619eea5d2be84bc63185d81bbac08a5e82ea71330a5b858dd5c",
    "validation_set": "2eabc60f4ea2d64be6e4fea5ee33e527de46b115e727a8607b5332b19ba1e1bf",
    "validation_outputs": "b5e168d3c8f4b420c8f2c1129ea23a3a4c5d6be946053aac7f1650cc4dd79189",
}

EXPECTED_SYMBOLIC = {
    "sum_product_bsc_p_0_1": {
        "node_count": 2157761,
        "canonical_serialized_bytes": 44776799,
        "canonical_sha256": "0a559a4c7349c184d5ad29491d727badd6e0d6ef32ce215e59edb7596c2be55b",
        "compile_aop_total": 20339963,
    },
    "soft_tropical_base_2": {
        "node_count": 2157761,
        "canonical_serialized_bytes": 44776798,
        "canonical_sha256": "83c64fa29b28920d12e7e7feeb59518c8bc56b4cc1856d91502dcb7c7e7c483f",
        "compile_aop_total": 20339963,
    },
    "min_plus_hamming": {
        "node_count": 2157832,
        "canonical_serialized_bytes": 49165354,
        "canonical_sha256": "b3b8ae903eef146d0d1036759fcad015c397f616eb0cd011d64540b5354129ff",
        "compile_aop_total": 20340034,
    },
}

SEMIRINGS = {
    "sum_product_bsc_p_0_1": {"kind": "sum_product", "local_bit_weights": [9, 1]},
    "soft_tropical_base_2": {"kind": "soft_tropical", "local_bit_weights": [2, 1]},
    "min_plus_hamming": {
        "kind": "min_plus",
        "local_bit_costs": [0, 1],
        "payload": "((minimum_weight,lowest_integer_representative),lowest_canonical_coset_key)",
    },
}

COMPILE_AOP_TYPES = [
    "GF2_XOR", "GF2_AND", "EXACT_INT_ADD", "EXACT_INT_MUL",
    "EXACT_COMPARE", "TABLE_READ", "TABLE_WRITE", "NODE_INTERN",
]
EXTENDED_VALIDATION_TYPES = COMPILE_AOP_TYPES + ["INDEX_PROJECT", "BITSET_OR"]
RESOURCE_ENVELOPE = {
    "max_peak_joint_table_entries": 1 << 20,
    "max_factor_table_entry_evaluations_per_algebra": 1 << 27,
    "max_retained_canonical_structural_nodes_or_entries_per_algebra": 1 << 22,
    "max_canonical_serialized_compiled_bytes_per_algebra": 512 * 1024 * 1024,
    "max_compilation_aop_events_per_algebra": 1 << 31,
}
VALIDATION_SEED = b"QLDPC-SCALE-001A::selector-validation::v1"
RANDOM_VALIDATION_COUNT = 256

CLAIM_BOUNDARY = {
    "single_larger_instance_feasibility_only": True,
    "source_reported_distance_only": True,
    "distance_independently_certified": False,
    "exact_validation_on_frozen_sample": True,
    "exhaustive_all_selector_equivalence": False,
    "family_relation_to_18_qubit_fixture_certified": False,
    "multi_size_scaling_claim": False,
    "bounded_treewidth_family_claim": False,
    "asymptotic_complexity_claim": False,
    "runtime_superiority_claim": False,
    "memory_superiority_claim": False,
    "controlled_approximation_authorized": False,
    "bp_min_sum_bp_osd_comparison_authorized": False,
    "circuit_level_noise_authorized": False,
    "repeated_syndrome_authorized": False,
    "learned_decoder_authorized": False,
    "adaptive_online_ordering_authorized": False,
    "qldpc_scale_001b_authorized": False,
    "qldpc_forge_authorized": False,
    "autonomous_search_authorized": False,
}


def digest(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def exact_keys(mapping: dict[str, Any], expected: set[str], where: str) -> None:
    if set(mapping) != expected:
        raise ValueError(f"{where} key mismatch")
