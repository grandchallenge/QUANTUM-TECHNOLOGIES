#!/usr/bin/env python3
"""Exact finite replay for QLDPC-FIXTURE-001.

The evaluator reconstructs the source-declared [[18,4,4]] bivariate-bicycle
CSS code from its polynomial parameters and independently checks finite
algebraic properties by exhaustive GF(2) computation.

It does NOT certify the Kunlun hardware experiment, circuit-level noise model,
BP-OSD performance, a threshold, fault-tolerant logical gates, TCM-QDEC, or
QLDPC-FORGE.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
from typing import Any

EVALUATOR_VERSION = "0.1.0"


def canonical_digest(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def identity(n: int) -> list[list[int]]:
    return [[int(i == j) for j in range(n)] for i in range(n)]


def cyclic_shift(n: int) -> list[list[int]]:
    return [[int(j == (i + 1) % n) for j in range(n)] for i in range(n)]


def transpose(matrix: list[list[int]]) -> list[list[int]]:
    return [list(column) for column in zip(*matrix)]


def matmul_mod2(left: list[list[int]], right: list[list[int]]) -> list[list[int]]:
    right_t = transpose(right)
    return [
        [sum(a * b for a, b in zip(row, column)) % 2 for column in right_t]
        for row in left
    ]


def matrix_add_mod2(*matrices: list[list[int]]) -> list[list[int]]:
    rows = len(matrices[0])
    cols = len(matrices[0][0])
    if any(len(matrix) != rows or len(matrix[0]) != cols for matrix in matrices):
        raise ValueError("matrix shape mismatch")
    return [
        [sum(matrix[i][j] for matrix in matrices) % 2 for j in range(cols)]
        for i in range(rows)
    ]


def matrix_power_mod2(matrix: list[list[int]], exponent: int) -> list[list[int]]:
    result = identity(len(matrix))
    base = matrix
    power = exponent
    while power:
        if power & 1:
            result = matmul_mod2(result, base)
        base = matmul_mod2(base, base)
        power >>= 1
    return result


def kron(left: list[list[int]], right: list[list[int]]) -> list[list[int]]:
    return [
        [
            left[i][j] * right[r][c]
            for j in range(len(left[0]))
            for c in range(len(right[0]))
        ]
        for i in range(len(left))
        for r in range(len(right))
    ]


def row_to_int(row: list[int]) -> int:
    value = 0
    for index, bit in enumerate(row):
        if bit not in (0, 1):
            raise ValueError("non-binary matrix entry")
        if bit:
            value |= 1 << index
    return value


def int_to_bitstring(value: int, width: int) -> str:
    return "".join("1" if value & (1 << index) else "0" for index in range(width))


def matrix_bitstrings(matrix: list[list[int]]) -> list[str]:
    return ["".join(str(bit) for bit in row) for row in matrix]


def gf2_basis(vectors: list[int]) -> list[int]:
    pivots: dict[int, int] = {}
    for original in vectors:
        value = original
        while value:
            pivot = value.bit_length() - 1
            if pivot in pivots:
                value ^= pivots[pivot]
            else:
                pivots[pivot] = value
                break
    return [pivots[pivot] for pivot in sorted(pivots, reverse=True)]


def gf2_rank(matrix: list[list[int]]) -> int:
    return len(gf2_basis([row_to_int(row) for row in matrix]))


def span(vectors: list[int]) -> set[int]:
    values = {0}
    for vector in gf2_basis(vectors):
        values |= {value ^ vector for value in tuple(values)}
    return values


def syndrome(error: int, check_rows: list[int]) -> int:
    result = 0
    for index, row in enumerate(check_rows):
        if (error & row).bit_count() % 2:
            result |= 1 << index
    return result


def parse_operator(labels: list[str], lm: int) -> int:
    value = 0
    seen: set[int] = set()
    for label in labels:
        if len(label) < 2 or label[0] not in {"L", "R"} or not label[1:].isdigit():
            raise ValueError(f"invalid logical-operator label: {label}")
        local = int(label[1:])
        if not 0 <= local < lm:
            raise ValueError(f"logical-operator index out of range: {label}")
        index = local if label[0] == "L" else lm + local
        if index in seen:
            raise ValueError(f"duplicate logical-operator site: {label}")
        seen.add(index)
        value |= 1 << index
    return value


def construct_checks(parameters: dict[str, int]) -> tuple[list[list[int]], list[list[int]]]:
    l = parameters["l"]
    m = parameters["m"]
    x = kron(cyclic_shift(l), identity(m))
    y = kron(identity(l), cyclic_shift(m))
    lm = l * m
    A = matrix_add_mod2(
        matrix_power_mod2(x, parameters["a1"]),
        matrix_power_mod2(y, parameters["a2"]),
        matrix_power_mod2(y, parameters["a3"]),
    )
    B = matrix_add_mod2(
        matrix_power_mod2(y, parameters["b1"]),
        matrix_power_mod2(x, parameters["b2"]),
        matrix_power_mod2(x, parameters["b3"]),
    )
    hx = [left + right for left, right in zip(A, B)]
    hz = [left + right for left, right in zip(transpose(B), transpose(A))]
    if len(hx) != lm or len(hx[0]) != 2 * lm:
        raise AssertionError("constructed check shape mismatch")
    return hx, hz


def exact_distance(
    kernel_checks: list[int],
    stabilizer_rows: set[int],
    n: int,
) -> tuple[int, int]:
    minimum = n + 1
    witnesses = 0
    for vector in range(1, 1 << n):
        if syndrome(vector, kernel_checks) == 0 and vector not in stabilizer_rows:
            weight = vector.bit_count()
            if weight < minimum:
                minimum = weight
                witnesses = 1
            elif weight == minimum:
                witnesses += 1
    if minimum == n + 1:
        raise AssertionError("no nontrivial logical operator found")
    return minimum, witnesses


def build_minimum_weight_decoder(check_rows: list[int], n: int) -> dict[int, int]:
    rank = len(gf2_basis(check_rows))
    target = 1 << rank
    table: dict[int, int] = {}
    for weight in range(n + 1):
        for support in itertools.combinations(range(n), weight):
            error = sum(1 << index for index in support)
            syn = syndrome(error, check_rows)
            if syn not in table:
                table[syn] = error
        if len(table) == target:
            break
    if len(table) != target:
        raise AssertionError("decoder did not cover all reachable syndromes")
    return table


def decoder_success_counts(
    decoder: dict[int, int],
    check_rows: list[int],
    stabilizer_rows: set[int],
    n: int,
    max_weight: int,
) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for weight in range(max_weight + 1):
        total = 0
        success = 0
        for support in itertools.combinations(range(n), weight):
            error = sum(1 << index for index in support)
            correction = decoder[syndrome(error, check_rows)]
            total += 1
            success += int((error ^ correction) in stabilizer_rows)
        counts[str(weight)] = {"success": success, "total": total}
    return counts


def validate_logicals(
    fixture: dict[str, Any],
    hx_rows: list[int],
    hz_rows: list[int],
    hx_span: set[int],
    hz_span: set[int],
    n: int,
) -> dict[str, Any]:
    lm = n // 2
    logical_x = [parse_operator(labels, lm) for labels in fixture["logical_operators"]["x"]]
    logical_z = [parse_operator(labels, lm) for labels in fixture["logical_operators"]["z"]]
    if len(logical_x) != len(logical_z):
        raise ValueError("logical X/Z basis sizes differ")

    x_checks = [syndrome(vector, hz_rows) == 0 and vector not in hx_span for vector in logical_x]
    z_checks = [syndrome(vector, hx_rows) == 0 and vector not in hz_span for vector in logical_z]
    pairing = [
        [(x & z).bit_count() % 2 for z in logical_z]
        for x in logical_x
    ]
    expected = [
        [int(i == j) for j in range(len(logical_z))]
        for i in range(len(logical_x))
    ]
    valid = all(x_checks) and all(z_checks) and pairing == expected
    if not valid:
        raise ValueError("source logical operators fail canonical CSS logical-basis checks")

    return {
        "basis_size": len(logical_x),
        "canonical_pairing": pairing,
        "all_x_in_kernel_hz_not_x_stabilizer": all(x_checks),
        "all_z_in_kernel_hx_not_z_stabilizer": all(z_checks),
        "x_bitstrings": [int_to_bitstring(vector, n) for vector in logical_x],
        "z_bitstrings": [int_to_bitstring(vector, n) for vector in logical_z],
    }


def evaluate_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    if fixture["fixture_id"] != "QLDPC-FIXTURE-001":
        raise ValueError("this evaluator is restricted to QLDPC-FIXTURE-001")
    if fixture["status"] != "candidate_executable_not_promoted":
        raise ValueError("fixture status unexpectedly changed")
    if fixture["claim_boundary"] != {
        "exact_code_algebra_only": True,
        "decoder_performance_claim": False,
        "circuit_level_noise_claim": False,
        "hardware_validation_claim": False,
        "threshold_claim": False,
        "fault_tolerant_architecture_claim": False,
        "qldpc_forge_authorized": False,
        "tcm_qdec_authorized": False,
    }:
        raise ValueError("claim boundary unexpectedly changed")

    hx, hz = construct_checks(fixture["parameters"])
    n = len(hx[0])
    hx_rows = [row_to_int(row) for row in hx]
    hz_rows = [row_to_int(row) for row in hz]
    rank_hx = gf2_rank(hx)
    rank_hz = gf2_rank(hz)
    k = n - rank_hx - rank_hz

    commutation = matmul_mod2(hx, transpose(hz))
    css_commutes = all(bit == 0 for row in commutation for bit in row)
    if not css_commutes:
        raise AssertionError("CSS commutation failed")

    hx_span = span(hx_rows)
    hz_span = span(hz_rows)
    dx, dx_witnesses = exact_distance(hz_rows, hx_span, n)
    dz, dz_witnesses = exact_distance(hx_rows, hz_span, n)
    distance = min(dx, dz)

    declared = fixture["source_declared_code"]
    declared_rank = fixture["source_declared_rank"]
    if (n, k, distance) != (declared["n"], declared["k"], declared["d"]):
        raise ValueError(
            f"source-declared [[n,k,d]] mismatch: computed {(n, k, distance)}, "
            f"declared {(declared['n'], declared['k'], declared['d'])}"
        )
    if (rank_hx, rank_hz) != (declared_rank["hx"], declared_rank["hz"]):
        raise ValueError("source-declared rank mismatch")

    logicals = validate_logicals(fixture, hx_rows, hz_rows, hx_span, hz_span, n)

    decoder_x = build_minimum_weight_decoder(hz_rows, n)
    decoder_z = build_minimum_weight_decoder(hx_rows, n)
    if decoder_x != decoder_z:
        raise AssertionError("expected identical decoder tables because Hx = Hz")

    decoder_entries = [
        {
            "syndrome": int_to_bitstring(syn, len(hz_rows)),
            "correction": int_to_bitstring(error, n),
            "weight": error.bit_count(),
        }
        for syn, error in sorted(decoder_x.items())
    ]
    decoder_counts = decoder_success_counts(decoder_x, hz_rows, hx_span, n, 4)
    if decoder_counts["1"]["success"] != decoder_counts["1"]["total"]:
        raise AssertionError("distance-4 fixture failed guaranteed single-error correction")

    report: dict[str, Any] = {
        "fixture_id": fixture["fixture_id"],
        "evaluator_version": EVALUATOR_VERSION,
        "status": fixture["status"],
        "source": fixture["source"],
        "construction": {
            "family": fixture["construction"],
            "parameters": fixture["parameters"],
            "hx": matrix_bitstrings(hx),
            "hz": matrix_bitstrings(hz),
            "hx_equals_hz": hx == hz,
        },
        "exact_invariants": {
            "n": n,
            "k": k,
            "d": distance,
            "dx": dx,
            "dz": dz,
            "rank_hx": rank_hx,
            "rank_hz": rank_hz,
            "css_commutes": css_commutes,
            "check_count_full": {"x": len(hx), "z": len(hz)},
            "independent_check_count": {"x": rank_hx, "z": rank_hz},
            "row_weights_hx": [sum(row) for row in hx],
            "row_weights_hz": [sum(row) for row in hz],
            "column_weights_hx": [sum(row[j] for row in hx) for j in range(n)],
            "column_weights_hz": [sum(row[j] for row in hz) for j in range(n)],
            "kernel_size_hx": 1 << (n - rank_hx),
            "kernel_size_hz": 1 << (n - rank_hz),
            "stabilizer_span_size_x": len(hx_span),
            "stabilizer_span_size_z": len(hz_span),
            "minimum_weight_logical_witness_count_x": dx_witnesses,
            "minimum_weight_logical_witness_count_z": dz_witnesses,
        },
        "logical_basis": logicals,
        "reference_decoder": {
            "kind": "exhaustive_minimum_weight_coset_leader",
            "noise_scope": "code_capacity_single_css_sector",
            "reachable_syndromes": len(decoder_entries),
            "max_coset_leader_weight": max(entry["weight"] for entry in decoder_entries),
            "guaranteed_correctable_weight": (distance - 1) // 2,
            "exact_success_counts_by_error_weight": decoder_counts,
            "table_sha256": canonical_digest(decoder_entries),
            "table_entry_count": len(decoder_entries),
            "performance_comparison_authorized": False,
        },
        "removed_checks_source_record": fixture["source_removed_checks"],
        "claim_boundary": fixture["claim_boundary"],
    }
    report["payload_sha256"] = canonical_digest(report)
    return report


def load_fixture(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    fixtures = payload.get("fixtures")
    if payload.get("registry_version") != "0.1.0" or not isinstance(fixtures, list):
        raise ValueError("invalid qLDPC fixture registry")
    matches = [fixture for fixture in fixtures if fixture.get("fixture_id") == "QLDPC-FIXTURE-001"]
    if len(matches) != 1:
        raise ValueError("QLDPC-FIXTURE-001 must appear exactly once")
    return matches[0]


def default_registry_path() -> Path:
    return Path(__file__).resolve().parents[1] / "registry" / "qldpc-fixtures.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=default_registry_path())
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = evaluate_fixture(load_fixture(args.registry))
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
