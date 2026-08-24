#!/usr/bin/env python3
"""TCM-C72-INTERFACE-001 exact syndrome-to-correction bridge."""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import platform
import resource
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import qldpc_fixture_002 as F2
import qldpc_scale_001a_math as A1M
import qldpc_scale_001a_shared as A1S
import tcm_qdec_003 as T3
import tcm_qdec_compare_001 as CMP

EXPERIMENT_ID = "TCM-C72-INTERFACE-001"
EVALUATOR_VERSION = "0.1.0"
MANIFEST_PATH = ROOT / "registry" / "tcm-c72-interface-001-manifest.json"
MANIFEST_PAYLOAD = "35e3715fa9b1d0d44cad63c8cafbee01a42c3426c7db21c37d3ff68073506ddf"
PROTECTED_START_MAIN = "53e2ac281eb8738e711f75b0d6be525eafab48a3"
C72_EVIDENCE_PAYLOAD = "198bb28f47844aa98efa20d8c838c48870a8aef41ccfda266b16661677e363e1"
C72_CORPUS_SHA = "23b49e39eafd70c9619f8837dfcb0046e13a1600cd7176d42a6018814f518050"
COMPARE_MANIFEST_PAYLOAD = "c68830f40733cde6957713060cec35adf317c75572cc960610c07c4d0e24d1e2"

C18_EXPECTED_DECISION = {
    "sum_product_bsc_p_0_1": "05dd32573ee965ce96caf707de3541f8be74b49317ad46b7929ef7dcf3bf64fc",
    "soft_tropical_base_2": "ea2a96e3878758cd2daebd28673d943c27740a3e1c3579d8429a8a658e567393",
    "min_plus_hamming": "88a9a766b64c7e476ac5bb4da877a2b1f6d4e88cee88cde6ea7461cc74179f3f",
}
C18_EXPECTED_TIE = {
    "sum_product_bsc_p_0_1": "3778c019c7e235d916fa27616f83a9f8251a8c2a0276e09e0ea6dc1a6125cd60",
    "soft_tropical_base_2": "bf4297273ca05b1506bde6f5305464e5affdf78ba31b40e20a0fada3e26dd982",
    "min_plus_hamming": "1991fe00aaec2f8ce1163ca7b4192054002a2ef176d4839d6883c01f4e724007",
}
C18_EXPECTED_SUCCESS = {
    "sum_product_bsc_p_0_1": 263,
    "soft_tropical_base_2": 262,
    "min_plus_hamming": 226,
}
C18_EXPECTED_TIE_ENVELOPE = {
    "sum_product_bsc_p_0_1": [263, 263],
    "soft_tropical_base_2": [262, 262],
    "min_plus_hamming": [218, 263],
}
CHANNEL_METADATA = {"kind": "BSC", "p": "0.1"}


def cbytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(cbytes(value)).hexdigest()


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
        raise ValueError("TCM-C72-INTERFACE-001 manifest digest mismatch")
    if data["authority"]["protected_start_main"] != PROTECTED_START_MAIN:
        raise ValueError("protected starting main drift")
    if data["c72_protected"]["qldpc_scale_001a"]["evidence_payload_sha256"] != C72_EVIDENCE_PAYLOAD:
        raise ValueError("C72 predecessor payload drift")
    if data["c72_corpus"]["sha256"] != C72_CORPUS_SHA:
        raise ValueError("C72 corpus digest drift")
    if data["c72_corpus"]["source_manifest_payload_sha256"] != COMPARE_MANIFEST_PAYLOAD:
        raise ValueError("comparison manifest binding drift")
    if data["resource_policy"]["historical_deterministic_caps_are_scientific_stop_rules"] is not False:
        raise ValueError("historical experimental caps were revived as scientific gates")
    if data["decoder_interface"]["injected_error_available_to_decoder"] is not False:
        raise ValueError("decoder leakage policy drift")
    if data["claim_boundary"]["c90_execution_authorized"] is not False:
        raise ValueError("C90 authority drift")
    return data


def gf2_rank(columns: list[int]) -> int:
    pivots: dict[int, int] = {}
    for original in columns:
        value = int(original)
        while value:
            pivot = value.bit_length() - 1
            if pivot in pivots:
                value ^= pivots[pivot]
            else:
                pivots[pivot] = value
                break
    return len(pivots)


def gf2_solve_column_basis(columns: list[int], width: int, rhs: int) -> int:
    """Solve sum_i x_i columns[i] == rhs over GF(2), returning x as a bitmask."""
    if len(columns) != width:
        raise ValueError("column basis must be square")
    basis: dict[int, tuple[int, int]] = {}
    for index, column in enumerate(columns):
        value = int(column)
        combo = 1 << index
        while value:
            pivot = value.bit_length() - 1
            if pivot in basis:
                prior_value, prior_combo = basis[pivot]
                value ^= prior_value
                combo ^= prior_combo
            else:
                basis[pivot] = (value, combo)
                break
        if value == 0:
            raise ValueError("selector functional map is singular")
    value = int(rhs)
    combo = 0
    while value:
        pivot = value.bit_length() - 1
        if pivot not in basis:
            raise ValueError("functional target is outside selector image")
        prior_value, prior_combo = basis[pivot]
        value ^= prior_value
        combo ^= prior_combo
    return combo


def inverse_columns(columns: list[int], width: int) -> list[int]:
    if gf2_rank(columns) != width:
        raise ValueError("selector functional map rank is not full")
    inverse = [gf2_solve_column_basis(columns, width, 1 << bit) for bit in range(width)]
    for functional_bit, coordinate in enumerate(inverse):
        rebuilt = 0
        for index, column in enumerate(columns):
            if (coordinate >> index) & 1:
                rebuilt ^= column
        if rebuilt != (1 << functional_bit):
            raise AssertionError("selector functional inverse verification failed")
    return inverse


def apply_inverse(inverse: list[int], functional: int) -> int:
    coordinate = 0
    for bit, column in enumerate(inverse):
        if (functional >> bit) & 1:
            coordinate ^= column
    return coordinate


def functional_columns(selector_rows: list[int], basis_qubits: list[int]) -> list[int]:
    columns: list[int] = []
    for qubit in basis_qubits:
        value = 0
        for functional, row in enumerate(selector_rows):
            if (row >> qubit) & 1:
                value |= 1 << functional
        columns.append(value)
    return columns


def selector_functional_value(seed: int, selector_rows: list[int]) -> int:
    out = 0
    for index, row in enumerate(selector_rows):
        if (seed & row).bit_count() & 1:
            out |= 1 << index
    return out


def independent_syndrome_from_full(full_syndrome: int, z_indices: list[int]) -> int:
    out = 0
    for basis_index, full_row_index in enumerate(z_indices):
        if (full_syndrome >> full_row_index) & 1:
            out |= 1 << basis_index
    return out


def runtime_environment() -> dict[str, Any]:
    rss_kib = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "max_rss_kib": rss_kib,
        "scientific_resource_stop_rule": False,
    }


def decision_from_class_records(records: list[dict[str, Any]], n: int) -> dict[str, Any]:
    if not records:
        raise ValueError("empty logical-class record set")
    if len(records) != len({record["logical_class"] for record in records}):
        raise ValueError("duplicate logical class")
    result: dict[str, Any] = {}
    specifications = {
        "sum_product_bsc_p_0_1": ("score_sum_product", True),
        "soft_tropical_base_2": ("score_soft_tropical", True),
        "min_plus_hamming": ("minimum_weight", False),
    }
    for algebra, (field, maximize) in specifications.items():
        values = [int(record[field]) for record in records]
        optimum = max(values) if maximize else min(values)
        tied = [record for record in records if int(record[field]) == optimum]
        tied.sort(key=lambda record: int(record["canonical_key"]))
        chosen = tied[0]
        correction = int(chosen["minimum_representative"])
        if correction >= (1 << n):
            raise ValueError("correction width overflow")
        result[algebra] = {
            "status": "CORRECTION_VALUED",
            "correction": correction,
            "logical_class": int(chosen["logical_class"]),
            "canonical_key": int(chosen["canonical_key"]),
            "minimum_weight": int(chosen["minimum_weight"]),
            "tied_winning_class_count": len(tied),
            "tied_canonical_keys": [int(record["canonical_key"]) for record in tied],
            "optimum_score": optimum,
        }
    return result


def load_c18_context() -> dict[str, Any]:
    rows, stabilizers, n, logical_z = T3.validate_predecessor(
        load_json(ROOT / "registry" / "tcm-qdec-002.json"),
        load_json(ROOT / "evidence" / "TCM-QDEC-002-report.json"),
        load_json(ROOT / "reviews" / "QTR-TCM-QDEC-REVIEW-002" / "promotion-record.json"),
        load_json(ROOT / "registry" / "tcm-qdec.json"),
        load_json(ROOT / "evidence" / "TCM-QDEC-001-report.json"),
        load_json(ROOT / "reviews" / "QTR-TCM-QDEC-REVIEW-001" / "promotion-record.json"),
        load_json(ROOT / "evidence" / "QLDPC-FIXTURE-001-report.json"),
        load_json(ROOT / "evidence" / "QLDPC-FIXTURE-002-report.json"),
        load_json(ROOT / "reviews" / "QTR-QLDPC-REVIEW-002" / "promotion-record.json"),
    )
    _, _, scopes, _ = T3.stabilizer_basis_and_scopes(rows, stabilizers, n)
    _, seed_map = T3.selector_seed_map(rows, logical_z, n)
    order = T3.audit_orders(scopes)["frozen_lexicographically_first_optimal_order"]
    return {
        "rows": rows,
        "stabilizers": stabilizers,
        "n": n,
        "logical_z": logical_z,
        "scopes": scopes,
        "seed_map": seed_map,
        "order": order,
    }


def c18_class_record(context: dict[str, Any], syndrome: int, logical_class: int) -> dict[str, Any]:
    selector = int(syndrome) | (int(logical_class) << len(context["rows"]))
    seed = context["seed_map"][selector]
    sum9 = T3.contract_class(seed, context["scopes"], context["order"], "sum9", context["n"])
    sum2 = T3.contract_class(seed, context["scopes"], context["order"], "sum2", context["n"])
    min_product = T3.contract_class(seed, context["scopes"], context["order"], "min_product", context["n"])
    (minimum_weight, representative), canonical_key = min_product
    return {
        "logical_class": logical_class,
        "score_sum_product": int(sum9),
        "score_soft_tropical": int(sum2),
        "minimum_weight": int(minimum_weight),
        "minimum_representative": int(representative),
        "canonical_key": int(canonical_key),
    }


def decode_c18_syndrome(context: dict[str, Any], syndrome: int) -> dict[str, Any]:
    records = [c18_class_record(context, syndrome, logical) for logical in range(16)]
    return decision_from_class_records(records, context["n"])


def run_c18_control() -> dict[str, Any]:
    context = load_c18_context()
    decisions: dict[str, dict[int, int]] = {algebra: {} for algebra in C18_EXPECTED_DECISION}
    ties: dict[str, dict[int, list[int]]] = {algebra: {} for algebra in C18_EXPECTED_DECISION}
    syndrome_mask = (1 << len(context["rows"])) - 1
    reachable_syndromes = sorted(
        {int(selector) & syndrome_mask for selector in context["seed_map"]}
    )
    if len(reachable_syndromes) != 128:
        raise AssertionError("unexpected C18 reachable-syndrome count")
    for syndrome in reachable_syndromes:
        result = decode_c18_syndrome(context, syndrome)
        for algebra, cell in result.items():
            decisions[algebra][syndrome] = int(cell["correction"])
            ties[algebra][syndrome] = [int(value) for value in cell["tied_canonical_keys"]]
    decision_sha: dict[str, str] = {}
    tie_sha: dict[str, str] = {}
    for algebra in decisions:
        decision_records = [
            {
                "syndrome": F2.i2b(syndrome, len(context["rows"])),
                "correction": F2.i2b(correction, context["n"]),
            }
            for syndrome, correction in sorted(decisions[algebra].items())
        ]
        tie_records = [
            {
                "syndrome": F2.i2b(syndrome, len(context["rows"])),
                "canonical_coset_keys": [F2.i2b(key, context["n"]) for key in keys],
            }
            for syndrome, keys in sorted(ties[algebra].items())
        ]
        decision_sha[algebra] = digest(decision_records)
        tie_sha[algebra] = digest(tie_records)
    if decision_sha != C18_EXPECTED_DECISION:
        raise AssertionError("generic bridge does not reproduce C18 decision tables")
    if tie_sha != C18_EXPECTED_TIE:
        raise AssertionError("generic bridge does not reproduce C18 tie sets")
    corpus = F2.make_corpus(context["n"], 4)
    success: dict[str, int] = {}
    for algebra, table in decisions.items():
        result, _ = T3.T2.T1.classify(corpus, context["rows"], context["stabilizers"], table)
        success[algebra] = int(result["success_total"])
    if success != C18_EXPECTED_SUCCESS:
        raise AssertionError("generic bridge does not reproduce C18 success totals")
    tie_report = T3.T2.factorized_tie_sensitivity(corpus, context["rows"], context["stabilizers"], ties)
    envelopes = {
        algebra: [
            int(cell["frozen_corpus_success_count_envelope_over_winning_class_ties"]["min"]),
            int(cell["frozen_corpus_success_count_envelope_over_winning_class_ties"]["max"]),
        ]
        for algebra, cell in tie_report.items()
    }
    if envelopes != C18_EXPECTED_TIE_ENVELOPE:
        raise AssertionError("generic bridge does not reproduce C18 tie envelopes")
    return {
        "status": "PASS",
        "decision_table_sha256": decision_sha,
        "winning_class_tie_sets_sha256": tie_sha,
        "success_totals": success,
        "tie_envelopes": envelopes,
    }


def load_c72_context() -> dict[str, Any]:
    manifest = load_manifest()
    evidence = load_json(ROOT / "evidence" / "QLDPC-SCALE-001A-report.json")
    if evidence.get("payload_sha256") != C72_EVIDENCE_PAYLOAD:
        raise ValueError("C72 evidence payload mismatch")
    code = A1M.construct_code()
    records = A1M.source_and_basis_records(code)
    if digest(records["hx_record"]) != A1S.EXPECTED_DIGESTS["hx"]:
        raise ValueError("C72 H_X digest drift")
    if digest(records["hz_record"]) != A1S.EXPECTED_DIGESTS["hz"]:
        raise ValueError("C72 H_Z digest drift")
    if digest(records["selector"]) != A1S.EXPECTED_DIGESTS["selector_basis"]:
        raise ValueError("C72 selector-basis digest drift")
    if digest(records["scope_record"]) != A1S.EXPECTED_DIGESTS["factor_scopes"]:
        raise ValueError("C72 factor-scope digest drift")
    order_audit = A1M.order_audit(code["scopes"])
    if digest(order_audit["order_record"]) != A1S.EXPECTED_DIGESTS["orders"]:
        raise ValueError("C72 elimination-order digest drift")
    order = order_audit["orders"]["min_fill"]
    if order_audit["widths"]["min_fill"] != 18:
        raise ValueError("C72 min-fill width drift")
    descriptor, descriptor_meta = A1M.compile_descriptor(code["scopes"], code["selector_basis_qubits"], order)
    if descriptor_meta["canonical_sha256"] != A1S.EXPECTED_DIGESTS["compiled_descriptor"]:
        raise ValueError("C72 descriptor digest drift")
    plan, final_ids = A1M.runtime_plan_from_descriptor(descriptor)
    columns = functional_columns(code["selector_rows"], code["selector_basis_qubits"])
    if len(columns) != 42 or gf2_rank(columns) != 42:
        raise ValueError("C72 selector functional map is not invertible")
    inverse = inverse_columns(columns, 42)
    map_receipt = {
        "columns": [str(value) for value in columns],
        "inverse_unit_functionals": [str(value) for value in inverse],
        "rank": 42,
        "functional_order": "30 independent Z-check rows followed by 12 protected logical-Z rows",
    }
    return {
        "manifest": manifest,
        "code": code,
        "order": order,
        "descriptor": descriptor,
        "descriptor_meta": descriptor_meta,
        "plan": plan,
        "final_ids": final_ids,
        "functional_columns": columns,
        "inverse": inverse,
        "selector_map_sha256": digest(map_receipt),
        "selector_map_receipt": map_receipt,
        "hx_rank": A1M.rank_rref(code["hx"], 72)[0],
    }


def c72_seed_for(context: dict[str, Any], full_syndrome: int, logical_class: int) -> tuple[int, int, int]:
    code = context["code"]
    independent = independent_syndrome_from_full(full_syndrome, code["z_indices"])
    functional = independent | (int(logical_class) << 30)
    coordinate = apply_inverse(context["inverse"], functional)
    seed = A1M.selector_lift(coordinate, code["selector_basis_qubits"])
    if selector_functional_value(seed, code["selector_rows"]) != functional:
        raise AssertionError("selector coordinate inversion failed")
    if F2.syndrome(seed, code["hz"]) != full_syndrome:
        raise AssertionError("selector seed does not reproduce requested full syndrome")
    return seed, coordinate, functional


def c72_class_record(context: dict[str, Any], full_syndrome: int, logical_class: int) -> dict[str, Any]:
    seed, coordinate, functional = c72_seed_for(context, full_syndrome, logical_class)
    sum9, sum2, min_product = A1M.evaluate_projection_plan(
        seed, context["code"]["scopes"], context["plan"], context["final_ids"]
    )
    (minimum_weight, representative), canonical_key = min_product
    if selector_functional_value(representative, context["code"]["selector_rows"]) != functional:
        raise AssertionError("minimum representative left requested selector class")
    if selector_functional_value(canonical_key, context["code"]["selector_rows"]) != functional:
        raise AssertionError("canonical class key left requested selector class")
    return {
        "logical_class": logical_class,
        "selector_coordinate": coordinate,
        "score_sum_product": int(sum9),
        "score_soft_tropical": int(sum2),
        "minimum_weight": int(minimum_weight),
        "minimum_representative": int(representative),
        "canonical_key": int(canonical_key),
    }


def decode_c72_syndrome(
    full_hz_syndrome: int,
    channel_metadata: dict[str, str],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Exact C72 decoder. The injected error is deliberately not an argument."""
    if channel_metadata != CHANNEL_METADATA:
        raise ValueError("channel metadata drift")
    context = context or load_c72_context()
    if not (0 <= int(full_hz_syndrome) < (1 << len(context["code"]["hz"]))):
        raise ValueError("syndrome width overflow")
    records: list[dict[str, Any]] = []
    hasher = hashlib.sha256()
    for logical_class in range(1 << 12):
        record = c72_class_record(context, int(full_hz_syndrome), logical_class)
        records.append(record)
        hasher.update(cbytes(record))
        hasher.update(b"\n")
    if len(records) != 4096:
        raise AssertionError("logical class enumeration incomplete")
    return {
        "status": "CORRECTION_VALUED",
        "logical_classes_evaluated": 4096,
        "class_score_stream_sha256": hasher.hexdigest(),
        "decisions": decision_from_class_records(records, 72),
    }


def c72_corpus_records() -> list[dict[str, Any]]:
    compare_manifest = CMP.load_manifest(ROOT / "registry" / "tcm-qdec-compare-001-manifest.json")
    records = CMP.generate_large_corpus_records(72, compare_manifest)
    if len(records) != 329 or digest(records) != C72_CORPUS_SHA:
        raise AssertionError("frozen C72 corpus drift")
    return records


def preflight() -> dict[str, Any]:
    manifest = load_manifest()
    c18 = run_c18_control()
    context = load_c72_context()
    corpus = c72_corpus_records()
    signature = str(inspect.signature(decode_c72_syndrome))
    if "error" in signature or "injected" in signature:
        raise AssertionError("decoder function signature leaks injected error")
    return {
        "experiment_id": EXPERIMENT_ID,
        "evaluator_version": EVALUATOR_VERSION,
        "status": "PREFLIGHT_PASS__NO_C72_DECODER_OUTCOME",
        "manifest_payload_sha256": manifest["manifest_payload_sha256"],
        "c18_control": c18,
        "c72_static": {
            "selector_map_rank": 42,
            "selector_map_sha256": context["selector_map_sha256"],
            "compiled_descriptor_sha256": context["descriptor_meta"]["canonical_sha256"],
            "min_fill_width": 18,
            "corpus_size": len(corpus),
            "corpus_sha256": digest(corpus),
            "decoder_signature": signature,
            "injected_error_available_to_decoder": False,
        },
        "runtime_environment": runtime_environment(),
    }


def run_shard(shard_index: int, shard_count: int) -> dict[str, Any]:
    if shard_count < 1 or not (0 <= shard_index < shard_count):
        raise ValueError("invalid shard coordinates")
    manifest = load_manifest()
    c18 = run_c18_control()
    if c18["status"] != "PASS":
        raise AssertionError("C18 control not green")
    context = load_c72_context()
    corpus = c72_corpus_records()
    owned = [record for record in corpus if int(record["index"]) % shard_count == shard_index]
    started = time.time()
    rows: list[dict[str, Any]] = []
    for record in owned:
        error = F2.b2i(record["error"])
        syndrome = F2.syndrome(error, context["code"]["hz"])
        decoded = decode_c72_syndrome(syndrome, CHANNEL_METADATA, context=context)
        rows.append(
            {
                "index": int(record["index"]),
                "syndrome": F2.i2b(syndrome, len(context["code"]["hz"])),
                "decode_status": decoded["status"],
                "logical_classes_evaluated": decoded["logical_classes_evaluated"],
                "class_score_stream_sha256": decoded["class_score_stream_sha256"],
                "decisions": {
                    algebra: {
                        **cell,
                        "correction": F2.i2b(int(cell["correction"]), 72),
                        "canonical_key": F2.i2b(int(cell["canonical_key"]), 72),
                        "tied_canonical_keys": [
                            F2.i2b(int(value), 72) for value in cell["tied_canonical_keys"]
                        ],
                    }
                    for algebra, cell in decoded["decisions"].items()
                },
            }
        )
    elapsed = time.time() - started
    report = {
        "experiment_id": EXPERIMENT_ID,
        "evaluator_version": EVALUATOR_VERSION,
        "status": "C72_SHARD_COMPLETE",
        "manifest_payload_sha256": manifest["manifest_payload_sha256"],
        "shard": {
            "index": shard_index,
            "count": shard_count,
            "owned_input_count": len(owned),
            "owned_indices": [int(record["index"]) for record in owned],
        },
        "c18_control_status": c18["status"],
        "c72_selector_map_sha256": context["selector_map_sha256"],
        "rows": rows,
        "rows_sha256": digest(rows),
        "engineering_diagnostics": {
            **runtime_environment(),
            "elapsed_seconds": elapsed,
            "historical_caps_used_as_scientific_stop_rules": False,
        },
    }
    report["payload_sha256"] = digest(report)
    return report


def rowspace_contains(vector: int, rows: list[int], width: int, expected_rank: int) -> bool:
    return A1M.rank_rref(rows + [int(vector)], width)[0] == expected_rank


def aggregate_shards(paths: list[Path]) -> dict[str, Any]:
    if not paths:
        raise ValueError("no shard files supplied")
    manifest = load_manifest()
    context = load_c72_context()
    corpus = c72_corpus_records()
    shards = [load_json(path) for path in paths]
    if len({int(shard["shard"]["count"]) for shard in shards}) != 1:
        raise ValueError("shard-count mismatch")
    shard_count = int(shards[0]["shard"]["count"])
    if len(shards) != shard_count:
        raise ValueError("aggregate requires every shard exactly once")
    by_index: dict[int, dict[str, Any]] = {}
    for shard in shards:
        unsigned = dict(shard)
        claimed = unsigned.pop("payload_sha256", None)
        if claimed != digest(unsigned):
            raise ValueError("shard payload digest mismatch")
        if shard["manifest_payload_sha256"] != MANIFEST_PAYLOAD:
            raise ValueError("shard manifest drift")
        for row in shard["rows"]:
            index = int(row["index"])
            if index in by_index:
                raise ValueError("duplicate C72 input across shards")
            by_index[index] = row
    if sorted(by_index) != list(range(len(corpus))):
        raise ValueError("C72 shard coverage incomplete")
    totals = {
        algebra: {
            "inputs": 0,
            "correction_valued": 0,
            "syndrome_consistent": 0,
            "syndrome_inconsistent": 0,
            "oracle_success": 0,
            "oracle_failure": 0,
        }
        for algebra in C18_EXPECTED_DECISION
    }
    scored_rows: list[dict[str, Any]] = []
    for corpus_record in corpus:
        index = int(corpus_record["index"])
        error = F2.b2i(corpus_record["error"])
        expected_syndrome = F2.syndrome(error, context["code"]["hz"])
        row = by_index[index]
        observed_syndrome = F2.b2i(row["syndrome"])
        if observed_syndrome != expected_syndrome:
            raise AssertionError("shard syndrome drift")
        scored: dict[str, Any] = {"index": index, "algebras": {}}
        for algebra, cell in row["decisions"].items():
            correction = F2.b2i(cell["correction"])
            consistent = F2.syndrome(correction, context["code"]["hz"]) == expected_syndrome
            correct = consistent and rowspace_contains(
                error ^ correction, context["code"]["hx"], 72, context["hx_rank"]
            )
            bucket = totals[algebra]
            bucket["inputs"] += 1
            bucket["correction_valued"] += int(cell["status"] == "CORRECTION_VALUED")
            bucket["syndrome_consistent" if consistent else "syndrome_inconsistent"] += 1
            bucket["oracle_success" if correct else "oracle_failure"] += 1
            scored["algebras"][algebra] = {
                "syndrome_consistent": consistent,
                "oracle_correct": correct,
                "correction_weight": correction.bit_count(),
                "logical_class": int(cell["logical_class"]),
                "tied_winning_class_count": int(cell["tied_winning_class_count"]),
            }
        scored_rows.append(scored)
    interface_certified = all(
        cell["inputs"] == 329
        and cell["correction_valued"] == 329
        and cell["syndrome_inconsistent"] == 0
        for cell in totals.values()
    )
    outcome = (
        "C72_TCM_SHARED_DECODER_INTERFACE_CERTIFIED"
        if interface_certified
        else "C72_TCM_INTERFACE_SEMANTIC_EQUIVALENCE_FAILED"
    )
    report = {
        "experiment_id": EXPERIMENT_ID,
        "evaluator_version": EVALUATOR_VERSION,
        "status": "candidate_executable_not_promoted",
        "manifest_payload_sha256": manifest["manifest_payload_sha256"],
        "c72_corpus": {"size": len(corpus), "sha256": digest(corpus)},
        "selector_map_sha256": context["selector_map_sha256"],
        "aggregate": {
            "shard_count": shard_count,
            "input_coverage_complete": True,
            "all_4096_logical_classes_evaluated_per_input": all(
                int(row["logical_classes_evaluated"]) == 4096 for row in by_index.values()
            ),
            "totals": totals,
            "scored_rows_sha256": digest(scored_rows),
        },
        "adjudication": {
            "outcome": outcome,
            "c72_tcm_quality_defined": interface_certified,
            "c90_exact_decoder_campaign_eligible": interface_certified,
            "c90_execution_authorized_here": False,
            "resource_failure_infeasibility_claim": False,
        },
        "claim_boundary": manifest["claim_boundary"],
        "engineering_diagnostics": {
            "shards": [shard["engineering_diagnostics"] for shard in shards],
            "historical_caps_used_as_scientific_stop_rules": False,
        },
    }
    report["payload_sha256"] = digest(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["preflight", "shard", "aggregate"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--shard-index", type=int)
    parser.add_argument("--shard-count", type=int)
    parser.add_argument("--shard", action="append", type=Path, default=[])
    args = parser.parse_args()

    if args.mode == "preflight":
        result = preflight()
    elif args.mode == "shard":
        if args.shard_index is None or args.shard_count is None:
            parser.error("--shard-index and --shard-count are required for shard mode")
        result = run_shard(args.shard_index, args.shard_count)
    else:
        if not args.shard:
            parser.error("one or more --shard paths are required for aggregate mode")
        result = aggregate_shards(args.shard)
    write_json(args.output, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
