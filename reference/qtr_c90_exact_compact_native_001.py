#!/usr/bin/env python3
"""Quality-blind driver for the compact-native exact C90 compiler.

The native engine is only a storage/execution backend for the frozen shared-
symbolic compiler. This driver writes the protected factor graph to the native
engine, runs the exact compile, and streams the resulting compact binary to
compute the same canonical semantic-node receipt used by ExpressionDAG.

It does not enumerate selectors, score injected errors, rewrite algebraic
expressions, change the protected elimination order, or expose C90 quality.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, BinaryIO

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import qtr_c90_exact_decoder_001 as Base
import qtr_c90_exact_dag_001 as DAG
import qtr_c90_exact_execute_001 as Execute

EXPERIMENT_ID = Base.EXPERIMENT_ID
EVALUATOR_VERSION = "0.1.0"
BACKEND = "EXACT_COMPACT_NATIVE_HASH_CONS"
STORAGE_BACKEND = "memory_hash_cons"
MAGIC = b"QTRC90N1"
HEADER = struct.Struct("<8sIQI")
NODE = struct.Struct("<BIII")
KIND_NAMES = {
    1: "I",
    2: "S",
    3: "MUL",
    4: "ADD",
    5: "MPMUL",
    6: "MPMIN",
}
ALGEBRA_IDS = {
    "sum_product_bsc_p_0_1": 0,
    "soft_tropical_base_2": 1,
    "min_plus_hamming": 2,
}
ID_ALGEBRAS = {value: key for key, value in ALGEBRA_IDS.items()}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    unsigned = dict(payload)
    payload = dict(payload)
    payload["payload_sha256"] = Base.digest(unsigned)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _terminal_value(algebra: str, code: int) -> Any:
    if algebra == "sum_product_bsc_p_0_1":
        if code not in (0, 1):
            raise ValueError(f"sum-product terminal code drift: {code}")
        return 9 if code == 0 else 1
    if algebra == "soft_tropical_base_2":
        if code not in (0, 1):
            raise ValueError(f"soft-tropical terminal code drift: {code}")
        return 2 if code == 0 else 1
    if code == 0:
        return ((0, 0), 0)
    qubit = code - 1
    if not 0 <= qubit < 90:
        raise ValueError(f"min-plus terminal code drift: {code}")
    integer = 1 << qubit
    return ((1, integer), integer)


def _write_native_input(path: Path, algebra: str, context: dict[str, Any]) -> None:
    code = context["code"]
    order = [int(v) for v in context["order"]]
    selector_qubits = [int(q) for q in code["selector_basis_qubits"]]
    scopes = [tuple(int(v) for v in scope) for scope in code["scopes"]]
    tokens: list[str] = [str(ALGEBRA_IDS[algebra]), str(len(order))]
    tokens.extend(str(v) for v in order)
    tokens.append(str(len(selector_qubits)))
    tokens.extend(str(q) for q in selector_qubits)
    tokens.append(str(len(scopes)))
    for scope in scopes:
        tokens.append(str(len(scope)))
        tokens.extend(str(v) for v in scope)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(" ".join(tokens) + "\n", encoding="utf-8")


def _read_header(handle: BinaryIO) -> tuple[str, int, int]:
    raw = handle.read(HEADER.size)
    if len(raw) != HEADER.size:
        raise ValueError("compact-native output header truncated")
    magic, algebra_id, count, root = HEADER.unpack(raw)
    if magic != MAGIC:
        raise ValueError(f"compact-native output magic drift: {magic!r}")
    algebra = ID_ALGEBRAS.get(algebra_id)
    if algebra is None:
        raise ValueError(f"compact-native output algebra id drift: {algebra_id}")
    if count == 0 or root >= count:
        raise ValueError("compact-native output root/count drift")
    return algebra, int(count), int(root)


def canonical_receipt_from_binary(path: Path, expected_algebra: str) -> dict[str, Any]:
    """Stream the exact frozen semantic node records without Python DAG expansion."""
    h = hashlib.sha256()
    kinds: Counter[str] = Counter()
    serialized_bytes = 0
    with path.open("rb") as handle:
        algebra, count, root = _read_header(handle)
        if algebra != expected_algebra:
            raise ValueError(f"compact-native algebra drift: {algebra} != {expected_algebra}")
        header = {
            "format": "QTR-C90-EXACT-DECODER-001-DAG-v1",
            "algebra": algebra,
            "root": root,
        }
        h.update(
            json.dumps(header, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
            + b"\n"
        )
        for node_id in range(count):
            raw = handle.read(NODE.size)
            if len(raw) != NODE.size:
                raise ValueError(f"compact-native node stream truncated at {node_id}")
            kind, a, b, c = NODE.unpack(raw)
            if kind == 0:
                name = "T"
                record: Any = ["T", _terminal_value(algebra, int(a))]
            elif kind == 1:
                name = "I"
                if b >= node_id or c >= node_id:
                    raise ValueError(f"compact-native selector child order drift at {node_id}")
                record = ["I", int(a), int(b), int(c)]
            elif kind == 2:
                raise ValueError(f"temporary stabilizer node retained at final node {node_id}")
            elif kind in KIND_NAMES:
                name = KIND_NAMES[kind]
                if a >= node_id or b >= node_id:
                    raise ValueError(f"compact-native binary child order drift at {node_id}")
                if a > b:
                    raise ValueError(f"compact-native commutative operand order drift at {node_id}")
                record = [name, int(a), int(b)]
            else:
                raise ValueError(f"compact-native node kind drift at {node_id}: {kind}")
            kinds[name] += 1
            encoded = (
                json.dumps(record, separators=(",", ":"), ensure_ascii=True).encode() + b"\n"
            )
            h.update(encoded)
            serialized_bytes += len(encoded)
        if handle.read(1):
            raise ValueError("compact-native output has trailing bytes")
    return {
        "canonical_node_stream_sha256": h.hexdigest(),
        "root": root,
        "reachable_nodes": count,
        "node_kind_counts": dict(sorted(kinds.items())),
        "canonical_node_stream_bytes_excluding_header": serialized_bytes,
    }


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(8 << 20)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def compile_c90_algebra(
    algebra: str,
    native_executable: Path,
    native_output: Path,
    receipt_output: Path,
) -> dict[str, Any]:
    if algebra not in DAG.ALGEBRAS:
        raise ValueError(algebra)
    preflight = Execute.preflight()
    if preflight.get("quality_exposed") is not False:
        raise AssertionError("quality-blind preflight exposed C90 quality")
    context = Base.load_c90_context()
    input_path = native_output.with_suffix(native_output.suffix + ".input.txt")
    _write_native_input(input_path, algebra, context)
    native_output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [str(native_executable), "--input", str(input_path), "--output", str(native_output)],
        check=True,
    )
    compiled = canonical_receipt_from_binary(native_output, algebra)
    compiled.update(
        {
            "algebra": algebra,
            "representation": DAG.REPRESENTATION,
            "backend": BACKEND,
            "storage_backend": STORAGE_BACKEND,
            "native_binary_sha256": file_sha256(native_output),
            "native_binary_bytes": native_output.stat().st_size,
            "temporary_stabilizer_nodes_final": 0,
        }
    )
    report = {
        "experiment_id": EXPERIMENT_ID,
        "evaluator_version": EVALUATOR_VERSION,
        "phase": "QUALITY_BLIND_COMPILE_ALGEBRA",
        "status": "C90_EXACT_ALGEBRA_COMPILED_QUALITY_BLIND",
        "source_commit": DAG.git_head(),
        "manifest_payload_sha256": Base.MANIFEST_PAYLOAD,
        "algebra": algebra,
        "compiled": compiled,
        "quality_exposed": False,
        "scientific_semantics_changed": False,
        "selector_enumeration_performed": False,
        "injected_error_success_used": False,
    }
    write_json(receipt_output, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--algebra", choices=DAG.ALGEBRAS, required=True)
    parser.add_argument("--native-executable", type=Path, required=True)
    parser.add_argument("--native-output", type=Path, required=True)
    parser.add_argument("--receipt-output", type=Path, required=True)
    args = parser.parse_args()
    report = compile_c90_algebra(
        args.algebra,
        args.native_executable,
        args.native_output,
        args.receipt_output,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "algebra": report["algebra"],
                "canonical_node_stream_sha256": report["compiled"]["canonical_node_stream_sha256"],
                "reachable_nodes": report["compiled"]["reachable_nodes"],
                "native_binary_bytes": report["compiled"]["native_binary_bytes"],
                "quality_exposed": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
