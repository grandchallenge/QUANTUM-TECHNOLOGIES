#!/usr/bin/env python3
"""Exact fixed-selector projection-plan oracle for QTR-C90-EXACT-DECODER-001.

This driver ports the predecessor's frozen factor-table semantics to a compact
C++ execution backend. It receives only a selector coordinate and the protected
factor graph; injected-error data and decoder success are unavailable.

For the two nonnegative-integer semirings the backend evaluates six pairwise-
coprime pseudo-Mersenne residues. Their product is greater than the strict C90
sum-product bound 2^41 * 9^90, so equality of all residues with a bounded native
integer proves exact integer equality. Min-plus uses exact fixed-width weight,
representative and canonical-key arithmetic.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import qtr_c90_exact_decoder_001 as Base

EXPERIMENT_ID = Base.EXPERIMENT_ID
BACKEND = "EXACT_FIXED_SELECTOR_PROJECTION_PLAN_CPP_V1"
ALGEBRA_IDS = {
    "sum_product_bsc_p_0_1": 0,
    "soft_tropical_base_2": 1,
    "min_plus_hamming": 2,
}
MODULI = tuple((1 << 61) - c for c in (1, 3, 7, 9, 13, 15))
SUM_PRODUCT_BOUND_EXCLUSIVE = (1 << 41) * (9**90) + 1
SOFT_TROPICAL_BOUND_EXCLUSIVE = (1 << 41) * (2**90) + 1


def _verify_modulus_certificate() -> None:
    for i, left in enumerate(MODULI):
        for right in MODULI[:i]:
            if math.gcd(left, right) != 1:
                raise AssertionError("dense-oracle moduli lost pairwise coprimality")
    product = math.prod(MODULI)
    if product <= SUM_PRODUCT_BOUND_EXCLUSIVE:
        raise AssertionError("dense-oracle modulus product no longer proves exact C90 equality")


def _input_text(
    *,
    algebra: str,
    coordinate: int,
    order: list[int],
    selector_basis: list[int],
    scopes: list[tuple[int, ...]],
) -> str:
    if algebra not in ALGEBRA_IDS:
        raise ValueError(algebra)
    if not (0 <= coordinate < (1 << len(selector_basis))):
        raise ValueError("selector coordinate outside frozen rank")
    tokens: list[str] = [str(ALGEBRA_IDS[algebra]), str(int(coordinate)), str(len(order))]
    tokens.extend(str(int(v)) for v in order)
    tokens.append(str(len(selector_basis)))
    tokens.extend(str(int(v)) for v in selector_basis)
    tokens.append(str(len(scopes)))
    for scope in scopes:
        tokens.append(str(len(scope)))
        tokens.extend(str(int(v)) for v in scope)
    return " ".join(tokens) + "\n"


def run_raw(
    *,
    executable: Path,
    algebra: str,
    coordinate: int,
    order: list[int],
    selector_basis: list[int],
    scopes: list[tuple[int, ...]],
) -> dict[str, Any]:
    _verify_modulus_certificate()
    completed = subprocess.run(
        [str(executable)],
        input=_input_text(
            algebra=algebra,
            coordinate=coordinate,
            order=order,
            selector_basis=selector_basis,
            scopes=scopes,
        ),
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if len(lines) != 1:
        raise AssertionError("dense oracle emitted unexpected stdout framing")
    row = json.loads(lines[0])
    if row.get("coordinate") != coordinate or row.get("algebra_id") != ALGEBRA_IDS[algebra]:
        raise AssertionError("dense oracle identity drift")
    if row.get("quality_exposed") is not False:
        raise AssertionError("dense oracle crossed quality boundary")
    if algebra != "min_plus_hamming":
        if tuple(row.get("moduli", ())) != MODULI or len(row.get("residues", ())) != len(MODULI):
            raise AssertionError("dense oracle residue certificate drift")
    return row


def _native_encoding(algebra: str, row: dict[str, Any]) -> dict[str, Any]:
    if row.get("algebra_id") != ALGEBRA_IDS[algebra]:
        raise AssertionError("native algebra identity drift")
    if row.get("quality_exposed") is not False:
        raise AssertionError("native row crossed quality boundary")
    if algebra != "min_plus_hamming":
        return {"encoding": "exact_nonnegative_integer_hex", "value_hex": row["value_hex"]}
    return {
        "encoding": "exact_min_plus_hamming_v1",
        "minimum_weight": int(row["minimum_weight"]),
        "minimum_representative_hex": row["minimum_representative_hex"],
        "canonical_hex": row["canonical_hex"],
    }


def _require_exact_native_equality(
    algebra: str,
    oracle: dict[str, Any],
    native: dict[str, Any],
) -> dict[str, Any]:
    if native.get("status") != "C90_COMPACT_NATIVE_SELECTOR_EVALUATED":
        raise AssertionError("native evaluator status drift")
    if native.get("selector_coordinate") != oracle["coordinate"]:
        raise AssertionError("native selector coordinate drift")
    encoding = _native_encoding(algebra, native)
    if algebra == "min_plus_hamming":
        if int(oracle["minimum_weight"]) != encoding["minimum_weight"]:
            raise AssertionError("dense/native min-plus weight mismatch")
        if int(oracle["minimum_representative_hex"], 16) != int(
            encoding["minimum_representative_hex"], 16
        ):
            raise AssertionError("dense/native min-plus representative mismatch")
        if int(oracle["canonical_hex"], 16) != int(encoding["canonical_hex"], 16):
            raise AssertionError("dense/native min-plus canonical-key mismatch")
        return encoding

    value = int(encoding["value_hex"], 16)
    bound = (
        SUM_PRODUCT_BOUND_EXCLUSIVE
        if algebra == "sum_product_bsc_p_0_1"
        else SOFT_TROPICAL_BOUND_EXCLUSIVE
    )
    if not (0 <= value < bound):
        raise AssertionError("native exact integer exceeds certified C90 semantic bound")
    observed = tuple(value % modulus for modulus in MODULI)
    expected = tuple(int(v) for v in oracle["residues"])
    if observed != expected:
        raise AssertionError("dense/native exact residue mismatch")
    return encoding


def validate_c90(
    *,
    executable: Path,
    algebra: str,
    coordinate: int,
    native_row: Path | None,
    output: Path,
) -> dict[str, Any]:
    context = Base.load_c90_context()
    code = context["code"]
    order = [int(v) for v in context["order"]]
    selector_basis = [int(v) for v in code["selector_basis_qubits"]]
    scopes = [tuple(int(v) for v in scope) for scope in code["scopes"]]
    oracle = run_raw(
        executable=executable,
        algebra=algebra,
        coordinate=coordinate,
        order=order,
        selector_basis=selector_basis,
        scopes=scopes,
    )
    native_encoding = None
    if native_row is not None:
        native = json.loads(native_row.read_text(encoding="utf-8"))
        native_encoding = _require_exact_native_equality(algebra, oracle, native)
    report: dict[str, Any] = {
        "experiment_id": EXPERIMENT_ID,
        "phase": "QUALITY_BLIND_FIXED_SELECTOR_DENSE_ORACLE",
        "status": "C90_DENSE_EXACT_SELECTOR_ORACLE_PASS",
        "backend": BACKEND,
        "algebra": algebra,
        "selector_coordinate": int(coordinate),
        "validation_set_sha256": Base.C90_VALIDATION_SET_SHA,
        "oracle": oracle,
        "native_exact_value": native_encoding,
        "exact_equal_to_native": native_row is not None,
        "numeric_modulus_product_bit_length": math.prod(MODULI).bit_length(),
        "sum_product_strict_bound_bit_length": SUM_PRODUCT_BOUND_EXCLUSIVE.bit_length(),
        "quality_exposed": False,
        "injected_error_success_used": False,
        "scientific_semantics_changed": False,
    }
    report["payload_sha256"] = Base.digest(report)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oracle-executable", type=Path, required=True)
    parser.add_argument("--algebra", choices=tuple(ALGEBRA_IDS), required=True)
    parser.add_argument("--coordinate", type=int, required=True)
    parser.add_argument("--native-row", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = validate_c90(
        executable=args.oracle_executable,
        algebra=args.algebra,
        coordinate=args.coordinate,
        native_row=args.native_row,
        output=args.output,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "algebra": report["algebra"],
                "selector_coordinate": report["selector_coordinate"],
                "exact_equal_to_native": report["exact_equal_to_native"],
                "payload_sha256": report["payload_sha256"],
                "quality_exposed": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
