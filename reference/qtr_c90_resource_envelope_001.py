#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import platform
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import qtr_c90_exact_requal_001 as exact_predecessor
import qtr_c90_structure_001 as structure
from qldpc_scale_001a_shared import digest
from qtr_colab_runtime_probe import detect_runtime

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "QTR-C90-RESOURCE-ENVELOPE-001"
MANIFEST_PATH = ROOT / "registry/qtr-c90-resource-envelope-001-manifest.json"
MANIFEST_PAYLOAD = "d64b770f5cc1fb4c8a0ca8e89dad6d8020a01ae38f2c6868ff3028f53c441651"
PREDECESSOR_EVIDENCE_PATH = ROOT / "evidence/QTR-C90-STRUCTURE-001-report.json"
PREDECESSOR_EVIDENCE_PAYLOAD = "ade245552af2f88d5ecb8c0b7f8eb363510ed678908fb80462b911255dd63d67"
PROTECTED_PREDECESSOR_MERGE = "c5719a623310432c4e97a5863428176ff739cbd7"
FIXED_PROCESS_OVERHEAD_BYTES = 256 * 1024 * 1024
PROBE_SAFETY_FACTOR = 2


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "UNKNOWN"


def canonical_payload(data: dict[str, Any], key: str = "payload_sha256") -> str:
    unsigned = dict(data)
    unsigned.pop(key, None)
    return digest(unsigned)


def load_manifest() -> dict[str, Any]:
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    unsigned = dict(data)
    unsigned.pop("manifest_payload_sha256", None)
    if data.get("manifest_payload_sha256") != MANIFEST_PAYLOAD or digest(unsigned) != MANIFEST_PAYLOAD:
        raise ValueError("resource-envelope manifest self-digest mismatch")
    if data["authority"]["protected_predecessor_merge"] != PROTECTED_PREDECESSOR_MERGE:
        raise ValueError("protected predecessor merge drift")
    if data["sensitivity"]["multipliers"] != [1, 2, 4, 8]:
        raise ValueError("sensitivity grid drift")
    return data


def load_predecessor() -> dict[str, Any]:
    data = json.loads(PREDECESSOR_EVIDENCE_PATH.read_text(encoding="utf-8"))
    if data.get("payload_sha256") != PREDECESSOR_EVIDENCE_PAYLOAD:
        raise ValueError("predecessor evidence payload drift")
    if canonical_payload(data) != PREDECESSOR_EVIDENCE_PAYLOAD:
        raise ValueError("predecessor evidence self-digest mismatch")
    if data.get("overall_outcome") != "C90_PREDECLARED_EXACT_STRUCTURAL_FAMILY_EXHAUSTED":
        raise ValueError("predecessor outcome drift")
    if data.get("phase_d_reached") or data.get("phase_e_reached"):
        raise ValueError("predecessor phase reach drift")
    return data


def sensitivity_record(row: dict[str, Any], manifest: dict[str, Any]) -> list[dict[str, Any]]:
    factor = int(row["factor_or_constraint_evaluations"]["value"])
    lower = int(row["aop"]["lower"])
    upper = int(row["aop"]["upper"])
    out = []
    for multiplier in manifest["sensitivity"]["multipliers"]:
        fcap = int(manifest["sensitivity"]["factor_evaluation_base"]) * multiplier
        acap = int(manifest["sensitivity"]["compilation_aop_base"]) * multiplier
        factor_pass = factor <= fcap
        aop_definite_fail = lower > acap
        aop_certified_pass = upper <= acap
        if (not factor_pass) or aop_definite_fail:
            status = "DEFINITE_FAIL"
        elif aop_certified_pass:
            status = "CERTIFIED_PASS"
        else:
            status = "INDETERMINATE"
        out.append({
            "multiplier": multiplier,
            "factor": {"value": factor, "coordinate": fcap, "exact_pass": factor_pass},
            "aop": {
                "lower": lower,
                "upper": upper,
                "coordinate": acap,
                "definite_fail": aop_definite_fail,
                "certified_pass": aop_certified_pass,
            },
            "status": status,
            "definite_historical_blockers_cleared": factor_pass and not aop_definite_fail,
        })
    return out


def planned_table_liveness(scopes: list[tuple[int, ...]], order: list[int]) -> dict[str, int]:
    factors = [(tuple(scope), 1 << len(scope)) for scope in scopes]
    initial_entries = sum(size for _, size in factors)
    peak_before = initial_entries
    peak_during_output = initial_entries
    max_individual = max((size for _, size in factors), default=0)
    total_output_entries = 0
    for variable in order:
        involved = [factor for factor in factors if variable in factor[0]]
        rest = [factor for factor in factors if variable not in factor[0]]
        if not involved:
            continue
        union = tuple(sorted(set().union(*(set(scope) for scope, _ in involved))))
        output_scope = tuple(item for item in union if item != variable)
        output_entries = 1 << len(output_scope)
        current_entries = sum(size for _, size in factors)
        peak_before = max(peak_before, current_entries)
        peak_during_output = max(peak_during_output, current_entries + output_entries)
        max_individual = max(max_individual, output_entries)
        total_output_entries += output_entries
        rest.append((output_scope, output_entries))
        factors = rest
    return {
        "initial_factor_table_entries": initial_entries,
        "peak_live_factor_table_entries_exact_planned": peak_during_output,
        "peak_live_before_output_entries": peak_before,
        "maximum_individual_table_entries_exact_planned": max_individual,
        "total_output_table_entries_planned": total_output_entries,
    }


def method_orders() -> tuple[list[tuple[int, ...]], dict[str, list[int]]]:
    pmanifest = exact_predecessor.load_manifest()
    _, code90, baseline_order, _ = exact_predecessor.reconstruct_target(pmanifest)
    jt90 = structure.junction_tree(code90["scopes"], baseline_order)
    sep_order = list(jt90["separator_elimination_order"])
    orders = {
        "S0_BASELINE": list(baseline_order),
        "S1_GF2_CONSTRAINT_ELIMINATION": list(baseline_order),
        "S2_SEPARATOR_INTERFACE_COMPILATION": sep_order,
        "S3_GF2_PLUS_SEPARATOR": sep_order,
    }
    return [tuple(scope) for scope in code90["scopes"]], orders


def max_serialized_node_line_bytes(retained_upper: int) -> int:
    max_index = max(0, retained_upper - 1)
    max_parameter = 48
    max_qubit_integer = (1 << 90) - 1
    candidates = [
        ("T", 9),
        ("T", 2),
        ("T", ((1, max_qubit_integer), max_qubit_integer)),
        ("I", max_parameter, max_index, max_index),
        ("MUL", max_index, max_index),
        ("ADD", max_index, max_index),
        ("MPMUL", max_index, max_index),
        ("MPMIN", max_index, max_index),
    ]
    return max(len(json.dumps(node, separators=(",", ":"), ensure_ascii=True).encode()) + 1 for node in candidates)


def representation_record(method: str, row: dict[str, Any], liveness: dict[str, int]) -> dict[str, Any]:
    retained_upper = int(row["retained"]["upper"])
    max_line = max_serialized_node_line_bytes(retained_upper)
    header_upper = 256
    serialized_upper = header_upper + retained_upper * max_line
    return {
        "retained_canonical_nodes_or_entries": {
            "type": "upper_bound",
            "value": retained_upper,
            "basis": "protected node-intern-attempt upper bound; not an exact retained-node count",
        },
        "intern_attempts": {
            "type": "upper_bound",
            "value": retained_upper,
            "basis": "protected static normalized ledger",
        },
        "live_factor_table_entries": {
            "type": "exact",
            "value": int(liveness["peak_live_factor_table_entries_exact_planned"]),
            "basis": "scope-only liveness simulation of the protected Python symbolic compiler schedule",
        },
        "maximum_individual_table_entries": {
            "type": "exact",
            "value": int(liveness["maximum_individual_table_entries_exact_planned"]),
            "basis": "scope-only output-table cardinality under frozen order",
        },
        "canonical_serialized_bytes": {
            "type": "upper_bound",
            "value": serialized_upper,
            "basis": "retained-node upper bound times exact maximum JSON-line length over frozen node schemas and 90-bit terminal integers, plus header allowance",
            "max_node_line_bytes": max_line,
            "header_upper_bytes": header_upper,
        },
        "legacy_32_byte_serialized_diagnostic": int(row["normalized_ledger"]["conservative_serialized_upper_bound_bytes_if_32_bytes_per_retained_entry"]),
        "method": method,
    }


def evaluate_static() -> dict[str, Any]:
    manifest = load_manifest()
    predecessor = load_predecessor()
    scopes, orders = method_orders()
    methods: dict[str, Any] = {}
    for method in manifest["frozen_methods"]:
        row = predecessor["c90_methods"][method]
        sensitivity = sensitivity_record(row, manifest)
        liveness = planned_table_liveness(scopes, orders[method])
        representation = representation_record(method, row, liveness)
        first_certified = next((item["multiplier"] for item in sensitivity if item["status"] == "CERTIFIED_PASS"), None)
        first_definite_clear = next((item["multiplier"] for item in sensitivity if item["definite_historical_blockers_cleared"]), None)
        methods[method] = {
            "control_status": row["control_status"],
            "sensitivity": sensitivity,
            "first_coordinate_clearing_definite_historical_blockers": first_definite_clear,
            "first_certified_cumulative_work_coordinate": first_certified,
            "representation": representation,
            "order_sha256": row["order_sha256"],
            "transformation_receipt_sha256": row["transformation_receipt_sha256"],
        }
    report = {
        "schema_version": 1,
        "experiment_id": EXPERIMENT_ID,
        "status": "candidate_executable_not_promoted",
        "source_commit": git_head(),
        "manifest_payload_sha256": MANIFEST_PAYLOAD,
        "protected_predecessor_merge": PROTECTED_PREDECESSOR_MERGE,
        "protected_predecessor_evidence_payload_sha256": PREDECESSOR_EVIDENCE_PAYLOAD,
        "methods": methods,
        "materialization_performed": False,
        "physical_probe_performed": False,
        "claim_boundary": manifest["claim_boundary"],
    }
    report["payload_sha256"] = digest(report)
    return report


def deep_size(obj: Any, seen: set[int] | None = None) -> int:
    if seen is None:
        seen = set()
    oid = id(obj)
    if oid in seen:
        return 0
    seen.add(oid)
    size = sys.getsizeof(obj)
    if isinstance(obj, dict):
        for key, value in obj.items():
            size += deep_size(key, seen)
            size += deep_size(value, seen)
    elif isinstance(obj, (list, tuple, set, frozenset)):
        for item in obj:
            size += deep_size(item, seen)
    return size


def rss_bytes() -> int:
    status = Path("/proc/self/status")
    if not status.exists():
        return 0
    for line in status.read_text(encoding="utf-8").splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1]) * 1024
    return 0


def probe_object_forms(manifest: dict[str, Any]) -> dict[str, Any]:
    runtime = detect_runtime()
    if runtime.get("observed_variant") != "CPU" or runtime.get("observed_accelerator") not in {None, ""}:
        raise RuntimeError("fresh calibration probe requires CPU-reference runtime without accelerator")
    total = int(runtime.get("memory_total_bytes") or 0)
    available = int(runtime.get("memory_available_bytes") or 0)
    if total <= 0 or available <= 0:
        raise RuntimeError("direct-host MemTotal/MemAvailable unavailable")
    allocation_limit = min(512 * 1024 * 1024, total // 20)
    samples = []
    for n in manifest["physical_probe"]["probe_entry_counts"]:
        before = rss_bytes()
        nodes = []
        interned = {}
        for i in range(n):
            node = ("MPMUL", i, i + 1)
            nodes.append(node)
            interned[node] = i
        after_nodes = rss_bytes()
        combined_deep = deep_size((nodes, interned))
        table = list(range(n))
        after_table = rss_bytes()
        table_shallow = sys.getsizeof(table)
        sample_deep = deep_size((nodes, interned, table))
        if sample_deep > allocation_limit:
            raise RuntimeError("bounded physical probe exceeded predeclared allocation ceiling")
        samples.append({
            "entries": n,
            "node_store_deep_bytes": combined_deep,
            "node_store_bytes_per_entry_ceiling": (combined_deep + n - 1) // n,
            "node_store_rss_delta_bytes": max(0, after_nodes - before),
            "node_store_rss_bytes_per_entry_ceiling": (max(0, after_nodes - before) + n - 1) // n,
            "table_list_shallow_bytes": table_shallow,
            "table_slot_bytes_per_entry_ceiling": (table_shallow + n - 1) // n,
            "combined_probe_deep_bytes": sample_deep,
            "combined_rss_delta_bytes": max(0, after_table - before),
        })
        del table, interned, nodes
    node_proxy = max(max(s["node_store_bytes_per_entry_ceiling"], s["node_store_rss_bytes_per_entry_ceiling"]) for s in samples) * PROBE_SAFETY_FACTOR
    table_slot_proxy = max(s["table_slot_bytes_per_entry_ceiling"] for s in samples) * PROBE_SAFETY_FACTOR
    return {
        "runtime": runtime,
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "pointer_width_bits": struct.calcsize("P") * 8,
        "sys_getsizeof": {
            "empty_list": sys.getsizeof([]),
            "empty_dict": sys.getsizeof({}),
            "int_zero": sys.getsizeof(0),
            "node_T": sys.getsizeof(("T", 9)),
            "node_I": sys.getsizeof(("I", 48, 123456789, 987654321)),
            "node_binary": sys.getsizeof(("MPMUL", 123456789, 987654321)),
        },
        "samples": samples,
        "allocation_limit_bytes": allocation_limit,
        "node_store_bytes_per_retained_node_engineering_upper_proxy": node_proxy,
        "table_slot_bytes_per_live_entry_engineering_upper_proxy": table_slot_proxy,
        "predeclared_probe_safety_factor": PROBE_SAFETY_FACTOR,
        "probe_is_bounded_and_non_materializing": True,
    }


def adjudicate(static: dict[str, Any], probe: dict[str, Any]) -> dict[str, Any]:
    manifest = load_manifest()
    total = int(probe["runtime"]["memory_total_bytes"])
    available = int(probe["runtime"]["memory_available_bytes"])
    node_bytes = int(probe["node_store_bytes_per_retained_node_engineering_upper_proxy"])
    table_bytes = int(probe["table_slot_bytes_per_live_entry_engineering_upper_proxy"])
    reserve = int(manifest["candidate_envelope_gate"]["absolute_reserve_bytes"])
    method_rows: dict[str, Any] = {}
    any_candidate = False
    representation_dominates = False
    for method, row in static["methods"].items():
        coordinate = row["first_certified_cumulative_work_coordinate"]
        rep = row["representation"]
        if coordinate is None:
            method_rows[method] = {"status": "NO_CERTIFIED_CUMULATIVE_WORK_COORDINATE", "candidate_envelope": False}
            continue
        retained_upper = int(rep["retained_canonical_nodes_or_entries"]["value"])
        live_entries = int(rep["live_factor_table_entries"]["value"])
        predicted_peak_upper = retained_upper * node_bytes + live_entries * table_bytes + FIXED_PROCESS_OVERHEAD_BYTES
        fraction_ok = predicted_peak_upper * 100 <= total * 70
        reserve_ok = predicted_peak_upper + reserve <= total
        available_ok = available >= predicted_peak_upper + reserve
        index_ok = int(rep["maximum_individual_table_entries"]["value"]) <= sys.maxsize
        serialized_bounded = rep["canonical_serialized_bytes"]["type"] == "upper_bound"
        candidate = all([fraction_ok, reserve_ok, available_ok, index_ok, serialized_bounded])
        any_candidate = any_candidate or candidate
        if not candidate:
            representation_dominates = True
        method_rows[method] = {
            "status": "PHYSICAL_ENVELOPE_CANDIDATE" if candidate else "REPRESENTATION_UPPER_BOUND_DOES_NOT_CERTIFY_PHYSICAL_GATE",
            "candidate_envelope": candidate,
            "cumulative_work_sensitivity_coordinate": coordinate,
            "predicted_peak_resident_upper_proxy_bytes": predicted_peak_upper,
            "predicted_components": {
                "retained_node_store_bytes": retained_upper * node_bytes,
                "live_factor_table_slot_bytes": live_entries * table_bytes,
                "fixed_process_overhead_bytes": FIXED_PROCESS_OVERHEAD_BYTES,
            },
            "canonical_serialized_upper_bound_bytes": int(rep["canonical_serialized_bytes"]["value"]),
            "gates": {
                "predicted_peak_le_70pct_total": fraction_ok,
                "absolute_2gib_reserve": reserve_ok,
                "fresh_memavailable_covers_peak_plus_reserve": available_ok,
                "runtime_index_support": index_ok,
                "serialized_storage_bounded": serialized_bounded,
            },
            "physical_feasibility_if_not_candidate": "indeterminate_from_upper_bound" if not candidate else None,
        }
    if any_candidate:
        overall = "C90_HISTORICAL_CAPS_CONSERVATIVE__PHYSICAL_ENVELOPE_CANDIDATE_IDENTIFIED"
    elif representation_dominates:
        overall = "C90_REPRESENTATION_BOUND_DOMINATES_AFTER_WORK_CAP_RELAXATION"
    else:
        overall = "C90_RESOURCE_ENVELOPE_CALIBRATION_INDETERMINATE"
    result = {
        "schema_version": 1,
        "experiment_id": EXPERIMENT_ID,
        "status": "candidate_executable_not_promoted",
        "source_commit": git_head(),
        "manifest_payload_sha256": MANIFEST_PAYLOAD,
        "overall_outcome": overall,
        "methods": method_rows,
        "static_payload_sha256": static["payload_sha256"],
        "physical_probe": probe,
        "materialization_performed": False,
        "frozen_307_validation_performed": False,
        "claim_boundary": manifest["claim_boundary"],
    }
    result["payload_sha256"] = digest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p_static = sub.add_parser("static")
    p_static.add_argument("--output", type=Path, required=True)
    p_probe = sub.add_parser("probe")
    p_probe.add_argument("--session-id", required=True)
    p_probe.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "static":
        result = evaluate_static()
    else:
        static = evaluate_static()
        probe = probe_object_forms(load_manifest())
        probe["hosted_session_identity"] = args.session_id
        result = adjudicate(static, probe)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "experiment_id": EXPERIMENT_ID,
        "command": args.command,
        "payload_sha256": result["payload_sha256"],
        "overall_outcome": result.get("overall_outcome"),
        "materialization_performed": result["materialization_performed"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
