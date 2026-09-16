#!/usr/bin/env python3
"""Checkpointable exact NumericDD oracle for QTR-C90 selector validation.

This module preserves the exact semantics of qtr_c90_exact_dag_001.direct_contract_selector.
It only makes the 41-variable elimination sequence resumable at existing variable-boundary
cache-clear points. No approximation, pruning, reordering, decoder outcome, or injected-error
success information is used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pickle
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import qtr_c90_exact_decoder_001 as Base
import qtr_c90_exact_dag_001 as DAG

EXPERIMENT_ID = Base.EXPERIMENT_ID
ORACLE_CHECKPOINT_VERSION = "0.1.0"
SCHEMA_VERSION = 1


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(8 << 20)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _binding(context: dict[str, Any], algebra: str, coordinate: int) -> str:
    code = context["code"]
    return Base.digest(
        {
            "experiment_id": EXPERIMENT_ID,
            "manifest_payload_sha256": Base.MANIFEST_PAYLOAD,
            "representation": DAG.REPRESENTATION,
            "algebra": algebra,
            "coordinate": int(coordinate),
            "order": [int(v) for v in context["order"]],
            "selector_basis_qubits": [int(v) for v in code["selector_basis_qubits"]],
            "scopes": [[int(v) for v in scope] for scope in code["scopes"]],
        }
    )


def _initialize(context: dict[str, Any], algebra: str, coordinate: int) -> dict[str, Any]:
    if algebra not in DAG.ALGEBRAS:
        raise ValueError(algebra)
    code = context["code"]
    order = [int(v) for v in context["order"]]
    dd = DAG.NumericDD(order, algebra)
    selector_parameter = {int(q): i for i, q in enumerate(code["selector_basis_qubits"])}
    factors: list[tuple[tuple[int, ...], int]] = []
    for qubit, raw_scope in enumerate(code["scopes"]):
        scope = tuple(int(v) for v in raw_scope)
        seed_bit = 1 if qubit in selector_parameter and coordinate & (1 << selector_parameter[qubit]) else 0
        ordered = sorted(scope, key=dd.rank.__getitem__)
        memo: dict[tuple[int, int], int] = {}

        def build(pos: int, parity: int) -> int:
            key = (pos, parity)
            if key in memo:
                return memo[key]
            if pos == len(ordered):
                out = dd.terminal(DAG._terminal_value(algebra, qubit, parity ^ seed_bit))
            else:
                out = dd.mk(ordered[pos], build(pos + 1, parity), build(pos + 1, parity ^ 1))
            memo[key] = out
            return out

        factors.append((scope, build(0, 0)))
    return {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": EXPERIMENT_ID,
        "oracle_checkpoint_version": ORACLE_CHECKPOINT_VERSION,
        "binding": _binding(context, algebra, coordinate),
        "algebra": algebra,
        "coordinate": int(coordinate),
        "next_step": 0,
        "nodes": dd.nodes,
        "factors": factors,
    }


def _restore_dd(context: dict[str, Any], state: dict[str, Any]) -> DAG.NumericDD:
    order = [int(v) for v in context["order"]]
    dd = DAG.NumericDD(order, str(state["algebra"]))
    dd.nodes = list(state["nodes"])
    dd.interned = {node: index for index, node in enumerate(dd.nodes)}
    dd.cache.clear()
    dd.rcache.clear()
    return dd


def _validate_state(context: dict[str, Any], algebra: str, coordinate: int, state: dict[str, Any]) -> None:
    if state.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("oracle checkpoint schema drift")
    if state.get("experiment_id") != EXPERIMENT_ID:
        raise ValueError("oracle checkpoint experiment drift")
    if state.get("oracle_checkpoint_version") != ORACLE_CHECKPOINT_VERSION:
        raise ValueError("oracle checkpoint implementation drift")
    if state.get("algebra") != algebra or int(state.get("coordinate", -1)) != int(coordinate):
        raise ValueError("oracle checkpoint subject drift")
    if state.get("binding") != _binding(context, algebra, coordinate):
        raise ValueError("oracle checkpoint binding drift")
    next_step = int(state.get("next_step", -1))
    if not 0 <= next_step <= len(context["order"]):
        raise ValueError("oracle checkpoint step drift")
    if not isinstance(state.get("nodes"), list) or not isinstance(state.get("factors"), list):
        raise ValueError("oracle checkpoint payload drift")


def advance(
    context: dict[str, Any],
    algebra: str,
    coordinate: int,
    *,
    state: dict[str, Any] | None = None,
    stop_step: int,
) -> tuple[dict[str, Any], Any | None]:
    order = [int(v) for v in context["order"]]
    if not 0 <= stop_step <= len(order):
        raise ValueError("invalid oracle stop step")
    if state is None:
        state = _initialize(context, algebra, coordinate)
    _validate_state(context, algebra, coordinate, state)
    start_step = int(state["next_step"])
    if stop_step < start_step:
        raise ValueError("oracle stop step precedes checkpoint")

    dd = _restore_dd(context, state)
    factors = [(tuple(scope), int(root)) for scope, root in state["factors"]]
    for step_index in range(start_step, stop_step):
        var = order[step_index]
        involved = [factor for factor in factors if var in factor[0]]
        rest = [factor for factor in factors if var not in factor[0]]
        if not involved:
            raise AssertionError(f"oracle elimination variable absent: {var}")
        joint = involved[0][1]
        for _, root in involved[1:]:
            joint = dd.apply("mul", joint, root)
        out = dd.apply("marg", dd.restrict(joint, var, 0), dd.restrict(joint, var, 1))
        union = tuple(sorted(set().union(*(set(scope) for scope, _ in involved))))
        rest.append((tuple(item for item in union if item != var), out))
        factors = rest
        dd.cache.clear()
        dd.rcache.clear()

    state = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": EXPERIMENT_ID,
        "oracle_checkpoint_version": ORACLE_CHECKPOINT_VERSION,
        "binding": _binding(context, algebra, coordinate),
        "algebra": algebra,
        "coordinate": int(coordinate),
        "next_step": int(stop_step),
        "nodes": dd.nodes,
        "factors": factors,
    }
    result: Any | None = None
    if stop_step == len(order):
        root = factors[0][1]
        for _, other in factors[1:]:
            root = dd.apply("mul", root, other)
        node = dd.nodes[root]
        if node[0] != "T":
            raise AssertionError("checkpointed numeric control did not contract to scalar")
        result = node[1]
    return state, result


def save_checkpoint(path: Path, receipt_path: Path, state: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("wb") as handle:
        pickle.dump(state, handle, protocol=5)
        handle.flush()
        os.fsync(handle.fileno())
    temp.replace(path)
    receipt = {
        "experiment_id": EXPERIMENT_ID,
        "oracle_checkpoint_version": ORACLE_CHECKPOINT_VERSION,
        "phase": "QUALITY_BLIND_NUMERIC_ORACLE_CHECKPOINT",
        "status": "C90_NUMERIC_ORACLE_CHECKPOINT_PRESERVED",
        "binding": state["binding"],
        "algebra": state["algebra"],
        "coordinate": int(state["coordinate"]),
        "next_step": int(state["next_step"]),
        "node_count": len(state["nodes"]),
        "factor_count": len(state["factors"]),
        "checkpoint_sha256": _file_sha256(path),
        "quality_exposed": False,
        "injected_error_success_used": False,
    }
    unsigned = dict(receipt)
    receipt["payload_sha256"] = Base.digest(unsigned)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def load_checkpoint(
    path: Path,
    receipt_path: Path,
    context: dict[str, Any],
    algebra: str,
    coordinate: int,
) -> dict[str, Any]:
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    unsigned = dict(receipt)
    payload_sha = unsigned.pop("payload_sha256", None)
    if Base.digest(unsigned) != payload_sha:
        raise ValueError("oracle checkpoint receipt digest drift")
    if receipt.get("status") != "C90_NUMERIC_ORACLE_CHECKPOINT_PRESERVED":
        raise ValueError("oracle checkpoint receipt status drift")
    if receipt.get("quality_exposed") is not False:
        raise ValueError("oracle checkpoint quality boundary drift")
    if receipt.get("checkpoint_sha256") != _file_sha256(path):
        raise ValueError("oracle checkpoint binary digest drift")
    if receipt.get("binding") != _binding(context, algebra, coordinate):
        raise ValueError("oracle checkpoint receipt binding drift")
    with path.open("rb") as handle:
        state = pickle.load(handle)
    _validate_state(context, algebra, coordinate, state)
    if int(receipt.get("next_step", -1)) != int(state["next_step"]):
        raise ValueError("oracle checkpoint receipt step drift")
    if int(receipt.get("node_count", -1)) != len(state["nodes"]):
        raise ValueError("oracle checkpoint receipt node-count drift")
    if int(receipt.get("factor_count", -1)) != len(state["factors"]):
        raise ValueError("oracle checkpoint receipt factor-count drift")
    return state


def _encode_value(algebra: str, value: Any) -> dict[str, Any]:
    if algebra != "min_plus_hamming":
        return {"encoding": "exact_nonnegative_integer_hex", "value_hex": hex(int(value))}
    ((weight, representative), canonical) = value
    return {
        "encoding": "exact_min_plus_hamming_v1",
        "minimum_weight": int(weight),
        "minimum_representative_hex": hex(int(representative)),
        "canonical_hex": hex(int(canonical)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--algebra", choices=DAG.ALGEBRAS, required=True)
    parser.add_argument("--coordinate", type=int, required=True)
    parser.add_argument("--stop-step", type=int, required=True)
    parser.add_argument("--checkpoint-in", type=Path)
    parser.add_argument("--checkpoint-receipt-in", type=Path)
    parser.add_argument("--checkpoint-out", type=Path)
    parser.add_argument("--checkpoint-receipt-out", type=Path)
    parser.add_argument("--result-out", type=Path)
    args = parser.parse_args()

    context = Base.load_c90_context()
    state = None
    if args.checkpoint_in is not None or args.checkpoint_receipt_in is not None:
        if args.checkpoint_in is None or args.checkpoint_receipt_in is None:
            raise ValueError("checkpoint binary and receipt must be supplied together")
        state = load_checkpoint(args.checkpoint_in, args.checkpoint_receipt_in, context, args.algebra, args.coordinate)
    state, result = advance(context, args.algebra, args.coordinate, state=state, stop_step=args.stop_step)

    checkpoint_receipt = None
    if args.checkpoint_out is not None or args.checkpoint_receipt_out is not None:
        if args.checkpoint_out is None or args.checkpoint_receipt_out is None:
            raise ValueError("checkpoint output binary and receipt must be supplied together")
        checkpoint_receipt = save_checkpoint(args.checkpoint_out, args.checkpoint_receipt_out, state)

    if result is not None:
        if args.result_out is None:
            raise ValueError("complete oracle execution requires --result-out")
        output = {
            "experiment_id": EXPERIMENT_ID,
            "oracle_checkpoint_version": ORACLE_CHECKPOINT_VERSION,
            "phase": "QUALITY_BLIND_NUMERIC_ORACLE_RESULT",
            "status": "C90_NUMERIC_ORACLE_EXACT_RESULT_PRESERVED",
            "binding": state["binding"],
            "algebra": args.algebra,
            "coordinate": int(args.coordinate),
            "completed_steps": int(state["next_step"]),
            "value_encoding": _encode_value(args.algebra, result),
            "value_sha256": Base.digest({"value": result}),
            "node_count": len(state["nodes"]),
            "factor_count": len(state["factors"]),
            "quality_exposed": False,
            "injected_error_success_used": False,
        }
        unsigned = dict(output)
        output["payload_sha256"] = Base.digest(unsigned)
        args.result_out.parent.mkdir(parents=True, exist_ok=True)
        args.result_out.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "C90_NUMERIC_ORACLE_SEGMENT_COMPLETE" if result is None else "C90_NUMERIC_ORACLE_EXACT_RESULT_PRESERVED",
                "algebra": args.algebra,
                "coordinate": int(args.coordinate),
                "next_step": int(state["next_step"]),
                "node_count": len(state["nodes"]),
                "factor_count": len(state["factors"]),
                "checkpoint_payload_sha256": None if checkpoint_receipt is None else checkpoint_receipt["payload_sha256"],
                "quality_exposed": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
