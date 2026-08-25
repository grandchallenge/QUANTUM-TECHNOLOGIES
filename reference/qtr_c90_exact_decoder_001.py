#!/usr/bin/env python3
"""QTR-C90-EXACT-DECODER-001 pre-outcome verifier and exact execution scaffold.

Preflight is quality-blind: it reconstructs and verifies the frozen C90
scientific surface but never compiles the full C90 DAG and never scores an
injected C90 error. Full compilation/decoding is a separately invoked execution
mode after the exact package head is frozen on execution docket #114.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import qldpc_fixture_002 as F2
import qldpc_scale_001b as S1B
import tcm_c72_interface_001 as C72
import tcm_qdec_compare_001 as CMP
from qldpc_scale_001a_math import rank_rref
from qldpc_scale_001a_shared import digest

EXPERIMENT_ID = "QTR-C90-EXACT-DECODER-001"
EVALUATOR_VERSION = "0.1.0"
MANIFEST_PATH = ROOT / "registry" / "qtr-c90-exact-decoder-001-manifest.json"
MANIFEST_PAYLOAD = "8c0fd54d9131434e17273f8c9aea407cb132c4511aad38dda8c5cb66a6441294"
PROTECTED_START_MAIN = "aa53dc3c0e99c39f766f4ccb0c0d0629cd9093db"
C72_OUTCOME = "C72_TCM_SHARED_DECODER_INTERFACE_CERTIFIED"
C90_CORPUS_SHA = "b053a27a9c346832d6008987e204c88162dc1797e0367b38705861049059e086"
C90_VALIDATION_SET_SHA = "c0a675e3124ed96de66a516a2d679923b8c230c7530b80d5d431df66d781a85c"
C90_VALIDATION_SEED = b"QLDPC-SCALE-001B::90::selector-validation::v1"
CHANNEL_METADATA = {"kind": "BSC", "p": "0.1"}

EXPECTED_C90_DIGESTS = {
    "source_record": "f99851301f0fce2970d20ef2e4d1f054b7efbfec294de8937ec4d9e2993a04ae",
    "hx_record": "31af739c5854bd3287b3e1319fc99e4c5f220fdd5c1486420d0cb17d6fce86af",
    "hz_record": "c79c2c8c3373fbc4b46b43364f403b07c1b093f98f0be1832fac0f1f571fd7ca",
    "bases": "377fae0d662372aa53372deaac9e602d4a97919150bcb3b3de65ecf714c598a8",
    "logical": "6cf0007ae20507fbd34163362e96c0e4741cc7ce0437debb542f565b151aeb8a",
    "selector": "257809cb3c37594e5d19b6f8a79018680f84bdec06ed898be45e4d1c504fb716",
    "scope_record": "8dd0b2849491df78376a7f7eb8940efa142737caf45df1fe2104fe4929da50da",
}
EXPECTED_FULL_ORDER_RECORD_SHA = "a612ced5cb6adce4d4dab40800e48bb80b7dd1542dc5cd89d4667cb56ae6c468"
EXPECTED_MIN_FILL_ORDER_SHA = "579c83be655d3b90c15d79bcedde8ba629b240e88ae76a910093006a69691db4"
EXPECTED_CONVENTIONAL = {
    "BP_MIN_SUM": {
        "inputs": 347,
        "oracle_success": 200,
        "result_records_sha256": "8d06d07779a61d8ec305e46bd7479f30dc773b84e2d3fe76da054500fc7f6bff",
    },
    "BP_OSD_CS_7": {
        "inputs": 347,
        "oracle_success": 211,
        "result_records_sha256": "2195de2fe9af00cc340a551ec0a01f9f54ffaca8c5f01100cf9fc05649a1db58",
    },
    "BP_SUM_PRODUCT": {
        "inputs": 347,
        "oracle_success": 171,
        "result_records_sha256": "9b5c120d8e5170a5694dd016c1f2502df216f91e72024a02cbf37e3d5a27b7ac",
    },
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_manifest() -> dict[str, Any]:
    data = load_json(MANIFEST_PATH)
    claimed = data.get("manifest_payload_sha256")
    unsigned = dict(data)
    unsigned.pop("manifest_payload_sha256", None)
    if claimed != MANIFEST_PAYLOAD or digest(unsigned) != MANIFEST_PAYLOAD:
        raise ValueError("C90 exact-decoder manifest self-digest mismatch")
    if data["authority"] != {
        "council_issue": 113,
        "execution_issue": 114,
        "human_steward_authorization_comment": 5405533756,
        "protected_start_main": PROTECTED_START_MAIN,
        "referee_comment": 5405192097,
    }:
        raise ValueError("C90 authority drift")
    if data["resource_policy"]["historical_deterministic_caps_are_scientific_stop_rules"] is not False:
        raise ValueError("historical experimental caps revived as scientific gates")
    if data["decoder_interface"]["injected_error_available_to_decoder"] is not False:
        raise ValueError("decoder leakage policy drift")
    if data["execution_method"]["post_outcome_tuning"] is not False:
        raise ValueError("post-outcome tuning policy drift")
    if data["representation"]["approximation_or_pruning"] is not False:
        raise ValueError("approximation/pruning policy drift")
    return data


def c90_configuration() -> dict[str, Any]:
    ladder = S1B.load_manifest(ROOT / "registry" / "qldpc-scale-001b-ladder-manifest.json")
    matches = [cfg for cfg in ladder["ladder"] if int(cfg["n"]) == 90]
    if len(matches) != 1:
        raise ValueError("protected C90 rung is not unique")
    return matches[0]


def _order_record(audit: dict[str, Any]) -> dict[str, Any]:
    return {
        **audit["orders"],
        "tie_break": "lowest_original_variable_index",
        "primal_update": "clique_current_neighbors_then_remove",
    }


def load_c90_context() -> dict[str, Any]:
    cfg = c90_configuration()
    code = S1B.construct_rung(cfg)
    if int(code["n"]) != 90:
        raise AssertionError("C90 reconstruction width drift")
    records = S1B.source_records(cfg, code)
    observed = {name: digest(value) for name, value in records.items()}
    if observed != EXPECTED_C90_DIGESTS:
        raise ValueError(f"C90 protected digest drift: {observed}")
    hx_rank = rank_rref(code["hx"], 90)[0]
    hz_rank = rank_rref(code["hz"], 90)[0]
    if (hx_rank, hz_rank, len(code["logical_z"]), len(code["selector_basis_qubits"])) != (41, 41, 8, 49):
        raise ValueError("C90 rank/quotient dimensions drift")
    audit = S1B.order_audit(code["scopes"])
    full_order_sha = digest(_order_record(audit))
    min_fill_order = list(audit["orders"]["min_fill"])
    min_fill_order_sha = digest(min_fill_order)
    if full_order_sha != EXPECTED_FULL_ORDER_RECORD_SHA:
        raise ValueError("C90 protected full order record drift")
    if min_fill_order_sha != EXPECTED_MIN_FILL_ORDER_SHA:
        raise ValueError("C90 protected min-fill order drift")
    if int(audit["widths"]["min_fill"]) != 25:
        raise ValueError("C90 protected min-fill width drift")

    selector_rows = list(code["z_basis"]) + list(code["logical_z"])
    columns = C72.functional_columns(selector_rows, code["selector_basis_qubits"])
    if len(columns) != 49 or C72.gf2_rank(columns) != 49:
        raise ValueError("C90 selector-functional map is not invertible")
    inverse = C72.inverse_columns(columns, 49)
    for target in range(49):
        coordinate = inverse[target]
        rebuilt = 0
        for index, column in enumerate(columns):
            if (coordinate >> index) & 1:
                rebuilt ^= column
        if rebuilt != (1 << target):
            raise AssertionError("C90 selector inverse roundtrip failed")
    selector_receipt = {
        "columns": [str(value) for value in columns],
        "inverse_unit_functionals": [str(value) for value in inverse],
        "rank": 49,
        "functional_order": "41 independent Z-check rows followed by 8 protected logical-Z rows",
    }
    return {
        "cfg": cfg,
        "code": code,
        "records": records,
        "hx_rank": hx_rank,
        "hz_rank": hz_rank,
        "order": min_fill_order,
        "full_order_record_sha256": full_order_sha,
        "min_fill_order_sha256": min_fill_order_sha,
        "selector_rows": selector_rows,
        "functional_columns": columns,
        "inverse": inverse,
        "selector_map_receipt": selector_receipt,
        "selector_map_sha256": digest(selector_receipt),
    }


def frozen_validation_coordinates() -> list[int]:
    selector_rank = 49
    reserved = {0, (1 << selector_rank) - 1} | {1 << index for index in range(selector_rank)}
    random_values: list[int] = []
    seen = set(reserved)
    counter = 0
    while len(random_values) < 256:
        block = hashlib.sha256(C90_VALIDATION_SEED + counter.to_bytes(8, "big")).digest()
        coordinate = 0
        position = 0
        for byte in block:
            for shift in range(7, -1, -1):
                if position >= selector_rank:
                    break
                if (byte >> shift) & 1:
                    coordinate |= 1 << position
                position += 1
            if position >= selector_rank:
                break
        if coordinate not in seen:
            seen.add(coordinate)
            random_values.append(coordinate)
        counter += 1
    coordinates = [0] + [1 << index for index in range(selector_rank)] + [(1 << selector_rank) - 1] + random_values
    if len(coordinates) != 307 or digest(coordinates) != C90_VALIDATION_SET_SHA:
        raise AssertionError("protected frozen C90 validation set drift")
    return coordinates


def c90_corpus_records() -> list[dict[str, Any]]:
    compare_manifest = CMP.load_manifest(ROOT / "registry" / "tcm-qdec-compare-001-manifest.json")
    generated = CMP.generate_large_corpus_records(90, compare_manifest)
    stored = load_json(ROOT / "evidence" / "corpora" / "TCM-QDEC-COMPARE-001-C90-corpus.json")
    if generated != stored:
        raise ValueError("stored C90 corpus differs from deterministic regeneration")
    if len(stored) != 347 or digest(stored) != C90_CORPUS_SHA:
        raise ValueError("frozen C90 corpus drift")
    return stored


def verify_c72_predecessor() -> dict[str, Any]:
    receipt = load_json(ROOT / "evidence" / "TCM-C72-INTERFACE-001-report.json")
    expected = load_manifest()["protected_c72_predecessor"]
    if receipt.get("adjudication", {}).get("outcome") != C72_OUTCOME:
        raise ValueError("protected C72 interface outcome drift")
    aggregate = receipt.get("aggregate_evidence", {})
    checks = {
        "aggregate_artifact_digest": aggregate.get("artifact_digest"),
        "aggregate_payload_sha256": aggregate.get("canonical_aggregate_payload_sha256"),
        "scored_rows_sha256": aggregate.get("canonical_scored_rows_sha256"),
        "selector_map_sha256": aggregate.get("selector_map_sha256"),
    }
    for key, observed in checks.items():
        if observed != expected[key]:
            raise ValueError(f"protected C72 predecessor identity drift: {key}")
    if receipt.get("adjudication", {}).get("c90_exact_decoder_campaign_eligible") is not True:
        raise ValueError("protected C72 did not make C90 eligible")
    return {"outcome": C72_OUTCOME, **checks}


def verify_conventional_anchors() -> dict[str, Any]:
    evidence = load_json(ROOT / "evidence" / "TCM-QDEC-COMPARE-001-report.json")
    c90 = evidence.get("surfaces", {}).get("C90", {}).get("conventional", {})
    receipt: dict[str, Any] = {}
    for method, expected in EXPECTED_CONVENTIONAL.items():
        cell = c90.get(method, {})
        totals = cell.get("totals", {})
        observed = {
            "inputs": int(totals.get("inputs", -1)),
            "oracle_success": int(totals.get("oracle_success", -1)),
            "result_records_sha256": cell.get("result_records_sha256"),
        }
        if observed != expected:
            raise ValueError(f"protected conventional C90 anchor drift: {method}: {observed}")
        receipt[method] = observed
    return receipt


def selector_seed_for(context: dict[str, Any], full_hz_syndrome: int, logical_class: int) -> tuple[int, int, int]:
    """Map one full C90 syndrome + logical class into the protected selector seed."""
    code = context["code"]
    independent = C72.independent_syndrome_from_full(full_hz_syndrome, code["z_indices"])
    functional = independent | (int(logical_class) << 41)
    coordinate = C72.apply_inverse(context["inverse"], functional)
    seed = 0
    for bit, qubit in enumerate(code["selector_basis_qubits"]):
        if (coordinate >> bit) & 1:
            seed ^= 1 << qubit
    if C72.selector_functional_value(seed, context["selector_rows"]) != functional:
        raise AssertionError("C90 selector coordinate inversion failed")
    if F2.syndrome(seed, code["hz"]) != full_hz_syndrome:
        raise AssertionError("C90 selector seed does not reproduce requested syndrome")
    return seed, coordinate, functional


def decode_c90_syndrome(
    full_hz_syndrome: int,
    channel_metadata: dict[str, str],
    *,
    compiled: Any,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Exact C90 decoder entry point. Injected physical error is deliberately absent."""
    if channel_metadata != CHANNEL_METADATA:
        raise ValueError("channel metadata drift")
    if compiled is None:
        raise ValueError("validated compiled C90 representation required")
    context = context or load_c90_context()
    if not (0 <= int(full_hz_syndrome) < (1 << len(context["code"]["hz"]))):
        raise ValueError("syndrome width overflow")
    records: list[dict[str, Any]] = []
    for logical_class in range(256):
        _, coordinate, functional = selector_seed_for(context, int(full_hz_syndrome), logical_class)
        record = compiled.evaluate_class(
            selector_coordinate=coordinate,
            functional_value=functional,
            logical_class=logical_class,
        )
        records.append(record)
    if len(records) != 256:
        raise AssertionError("C90 logical-class enumeration incomplete")
    return {
        "status": "CORRECTION_VALUED",
        "logical_classes_evaluated": 256,
        "decisions": C72.decision_from_class_records(records, 90),
    }


def preflight() -> dict[str, Any]:
    manifest = load_manifest()
    c72 = verify_c72_predecessor()
    context = load_c90_context()
    corpus = c90_corpus_records()
    conventional = verify_conventional_anchors()
    controls = frozen_validation_coordinates()
    signature = str(inspect.signature(decode_c90_syndrome))
    if "error" in signature or "injected" in signature:
        raise AssertionError("C90 decoder signature leaks injected error")
    if manifest["representation"]["historical_retained_node_cap_is_scientific_stop_rule"] is not False:
        raise AssertionError("historical retained-node cap revived")
    return {
        "experiment_id": EXPERIMENT_ID,
        "evaluator_version": EVALUATOR_VERSION,
        "status": "PREFLIGHT_PASS__NO_C90_DECODER_QUALITY",
        "manifest_payload_sha256": manifest["manifest_payload_sha256"],
        "protected_start_main": PROTECTED_START_MAIN,
        "c72_predecessor": c72,
        "c90_static": {
            "hx_rank": context["hx_rank"],
            "hz_rank": context["hz_rank"],
            "logical_dimension": len(context["code"]["logical_z"]),
            "selector_rank": len(context["code"]["selector_basis_qubits"]),
            "logical_classes_per_syndrome": 256,
            "min_fill_width": 25,
            "min_fill_order_sha256": context["min_fill_order_sha256"],
            "full_order_record_sha256": context["full_order_record_sha256"],
            "selector_map_rank": C72.gf2_rank(context["functional_columns"]),
            "selector_map_sha256": context["selector_map_sha256"],
            "validation_selector_count": len(controls),
            "validation_set_sha256": digest(controls),
            "corpus_size": len(corpus),
            "corpus_sha256": digest(corpus),
            "decoder_signature": signature,
            "injected_error_available_to_decoder": False,
        },
        "conventional_anchors": conventional,
        "representation_contract": manifest["representation"],
        "resource_policy": manifest["resource_policy"],
        "quality_exposed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["preflight"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = preflight()
    write_json(args.output, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
