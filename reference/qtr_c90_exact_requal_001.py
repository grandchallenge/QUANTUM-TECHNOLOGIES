#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import resource
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import qldpc_scale_001b as scale001b
from qldpc_scale_001a_math import compile_descriptor, run_validation_parallel
from qldpc_scale_001a_shared import digest
from qldpc_scale_001a_symbolic import compile_symbolic_metadata

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "QTR-C90-EXACT-REQUAL-001"
MANIFEST_PATH = ROOT / "registry/qtr-c90-exact-requal-001-manifest.json"
MANIFEST_PAYLOAD = "870202c16fe1d5edea69e9af845fd306964557b6edcd4e3902a203af9820cd33"
PREDECESSOR_EVIDENCE_PAYLOAD = "6b8076376eb621710d993d1cb8768c7d4c03b7fe9d67802e6ae2e77212b610fc"
DISABLED_CANDIDATE_PATH = ROOT / "configs/compute/qtr_c90_exact_candidate_matrix.json"
DISABLED_CANDIDATE_BLOB = "a438f99569173edbc3b933eb2a7797e99279983f"
PROTECTED_START_MAIN = "8b52c71c916e9eea4a4c76309846cdb2b4a7d55a"
TARGET_DIGESTS = {
    "source_record_sha256": "f99851301f0fce2970d20ef2e4d1f054b7efbfec294de8937ec4d9e2993a04ae",
    "hx_sha256": "31af739c5854bd3287b3e1319fc99e4c5f220fdd5c1486420d0cb17d6fce86af",
    "hz_sha256": "c79c2c8c3373fbc4b46b43364f403b07c1b093f98f0be1832fac0f1f571fd7ca",
    "independent_bases_sha256": "377fae0d662372aa53372deaac9e602d4a97919150bcb3b3de65ecf714c598a8",
    "logical_basis_sha256": "6cf0007ae20507fbd34163362e96c0e4741cc7ce0437debb542f565b151aeb8a",
    "selector_basis_sha256": "257809cb3c37594e5d19b6f8a79018680f84bdec06ed898be45e4d1c504fb716",
    "factor_scope_sha256": "8dd0b2849491df78376a7f7eb8940efa142737caf45df1fe2104fe4929da50da",
    "order_record_sha256": "a612ced5cb6adce4d4dab40800e48bb80b7dd1542dc5cd89d4667cb56ae6c468",
}
VALIDATION_SET_SHA256 = "c0a675e3124ed96de66a516a2d679923b8c230c7530b80d5d431df66d781a85c"
VALIDATION_SEED = b"QLDPC-SCALE-001B::90::selector-validation::v1"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "UNKNOWN"


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    claimed = data.pop("manifest_payload_sha256")
    observed = digest(data)
    data["manifest_payload_sha256"] = claimed
    if claimed != MANIFEST_PAYLOAD or observed != MANIFEST_PAYLOAD:
        raise ValueError("C90 requalification manifest self-digest mismatch")
    if data["authority"] != {
        "authorization_readback_comment": 5336718430,
        "council_issue": 91,
        "execution_issue": 92,
        "human_steward_comment": 5336703933,
        "protected_start_main": PROTECTED_START_MAIN,
        "referee_comment": 5336617970,
    }:
        raise ValueError("C90 requalification authority drift")
    if data["preparation"]["disabled_candidate_blob_sha"] != DISABLED_CANDIDATE_BLOB:
        raise ValueError("disabled candidate binding drift")
    if data["target"]["source_and_basis_digests"] != TARGET_DIGESTS:
        raise ValueError("target digest binding drift")
    return data


def verify_disabled_candidate() -> dict[str, Any]:
    payload = json.loads(DISABLED_CANDIDATE_PATH.read_text(encoding="utf-8"))
    if payload.get("status") != "FROZEN_DISABLED_PENDING_SEPARATE_SCIENTIFIC_AUTHORITY":
        raise ValueError("protected disabled C90 candidate status changed")
    jobs = payload.get("jobs", [])
    if len(jobs) != 1:
        raise ValueError("protected disabled C90 candidate job count changed")
    job = jobs[0]
    required = {
        "enabled": False,
        "scientific_execution_authorized": False,
        "scientific_backend": "cpu_reference",
        "workload": "c90_exact_candidate",
    }
    for key, value in required.items():
        if job.get(key) != value:
            raise ValueError(f"protected disabled C90 candidate drift: {key}")
    if job.get("claim_boundary", {}).get("physical_materialization_authorized") is not False:
        raise ValueError("protected candidate materialization boundary changed")
    return payload


def load_predecessor_evidence() -> dict[str, Any]:
    path = ROOT / "evidence/QLDPC-SCALE-001B-report.json"
    evidence = json.loads(path.read_text(encoding="utf-8"))
    if evidence.get("payload_sha256") != PREDECESSOR_EVIDENCE_PAYLOAD:
        raise ValueError("001B evidence payload identity changed")
    unsigned = dict(evidence)
    unsigned.pop("payload_sha256", None)
    if digest(unsigned) != PREDECESSOR_EVIDENCE_PAYLOAD:
        raise ValueError("001B evidence self-verification failed")
    return evidence


def reconstruct_target(manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], list[int], dict[str, Any]]:
    ladder = scale001b.load_manifest(ROOT / scale001b.MANIFEST_PATH)
    cfgs = [row for row in ladder["ladder"] if int(row["n"]) == 90]
    if len(cfgs) != 1:
        raise ValueError("expected exactly one C90 rung")
    cfg = cfgs[0]
    code = scale001b.construct_rung(cfg)
    record = scale001b.rung_record(cfg, "rung")
    observed = record["source_and_basis_digests"]
    for key, value in TARGET_DIGESTS.items():
        if key == "order_record_sha256":
            continue
        if observed.get(key) != value:
            raise ValueError(f"C90 protected identity drift: {key}")
    audit = scale001b.order_audit(code["scopes"])
    order_record = {
        **audit["orders"],
        "tie_break": "lowest_original_variable_index",
        "primal_update": "clique_current_neighbors_then_remove",
    }
    if digest(order_record) != TARGET_DIGESTS["order_record_sha256"]:
        raise ValueError("C90 min-fill/order record drift")
    if audit["widths"]["min_fill"] != manifest["target"]["min_fill_induced_width"]:
        raise ValueError("C90 protected min-fill width drift")
    if (1 << (audit["widths"]["min_fill"] + 1)) != manifest["target"]["predicted_peak_joint_table_entries"]:
        raise ValueError("C90 protected peak-joint identity drift")
    if len(code["x_basis"]) != 41 or len(code["selector_basis_qubits"]) != 49:
        raise ValueError("C90 protected basis rank drift")
    return cfg, code, audit["orders"]["min_fill"], record


def frozen_validation_coordinates(selector_rank: int) -> list[int]:
    reserved = {0, (1 << selector_rank) - 1} | {1 << index for index in range(selector_rank)}
    random_values: list[int] = []
    seen = set(reserved)
    counter = 0
    while len(random_values) < 256:
        block = hashlib.sha256(VALIDATION_SEED + counter.to_bytes(8, "big")).digest()
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
    return [0] + [1 << index for index in range(selector_rank)] + [(1 << selector_rank) - 1] + random_values


def exact_static_ledger(scopes: list[tuple[int, ...]], selector_basis: list[int], order: list[int]) -> dict[str, Any]:
    factors = [tuple(scope) for scope in scopes]
    local_entries = sum(1 << len(scope) for scope in scopes)
    local_gf2_ops = sum((1 << len(scope)) * len(scope) for scope in scopes)
    selector_set = set(selector_basis)
    selector_local_entries = sum(1 << len(scopes[q]) for q in selector_set)
    local_intern_attempts = local_entries + 2 * selector_local_entries
    cumulative_aop_lower = local_gf2_ops + 2 * local_intern_attempts + local_entries
    cumulative_factor_evaluations = local_entries
    node_intern_attempts = local_intern_attempts
    joint_total = output_total = factor_reads_total = multiplies_total = 0
    peak_joint = 0
    peak_symbolic_factor_table_slots = sum(1 << len(scope) for scope in factors)
    peak_generic_factor_scratch_slots = 0
    peak_validation_scalar_slots = 0
    peak_projection_uint32_slots = 0
    steps: list[dict[str, Any]] = []
    caps = load_manifest()["resource_envelope"]
    first_factor_cross = first_aop_cross = first_peak_cross = None

    for step_index, variable in enumerate(order):
        involved = [scope for scope in factors if variable in scope]
        rest = [scope for scope in factors if variable not in scope]
        if not involved:
            raise ValueError(f"elimination variable {variable} has no involved factors")
        union = tuple(sorted(set().union(*(set(scope) for scope in involved))))
        output_scope = tuple(item for item in union if item != variable)
        joint = 1 << len(union)
        output = 1 << len(output_scope)
        active_before = sum(1 << len(scope) for scope in factors)
        active_after = sum(1 << len(scope) for scope in rest) + output
        reads = len(involved) * joint
        multiplies = (len(involved) - 1) * joint
        binary_interns = multiplies + output
        step_aop_lower = reads + 3 * binary_interns + output
        cumulative_factor_evaluations += joint
        cumulative_aop_lower += step_aop_lower
        node_intern_attempts += binary_interns
        joint_total += joint
        output_total += output
        factor_reads_total += reads
        multiplies_total += multiplies
        peak_joint = max(peak_joint, joint)
        peak_symbolic_factor_table_slots = max(peak_symbolic_factor_table_slots, active_after)
        peak_generic_factor_scratch_slots = max(peak_generic_factor_scratch_slots, active_before + joint + output)
        peak_validation_scalar_slots = max(peak_validation_scalar_slots, 5 * (joint + output))
        projection_uint32 = len(involved) * joint + 2 * output
        peak_projection_uint32_slots = max(peak_projection_uint32_slots, projection_uint32)
        if first_factor_cross is None and cumulative_factor_evaluations > caps["max_factor_table_entry_evaluations_per_algebra"]:
            first_factor_cross = step_index
        if first_aop_cross is None and cumulative_aop_lower > caps["max_compilation_aop_events_per_algebra"]:
            first_aop_cross = step_index
        if first_peak_cross is None and joint > caps["authorized_c90_peak_joint_table_entries"]:
            first_peak_cross = step_index
        steps.append({
            "step": step_index,
            "variable": variable,
            "involved_factor_count": len(involved),
            "union_arity": len(union),
            "output_arity": len(output_scope),
            "joint_assignments": joint,
            "output_slots": output,
            "active_factor_slots_before": active_before,
            "active_factor_slots_after": active_after,
            "factor_table_reads": reads,
            "semiring_multiply_events": multiplies,
            "binary_node_intern_attempts": binary_interns,
            "mandatory_aop_lower_bound": step_aop_lower,
            "cumulative_factor_table_entry_evaluations": cumulative_factor_evaluations,
            "cumulative_mandatory_aop_lower_bound": cumulative_aop_lower,
        })
        rest.append(output_scope)
        factors = rest

    aop_upper = cumulative_aop_lower + node_intern_attempts
    exact = {
        "local_factor_entries": local_entries,
        "local_factor_gf2_assignment_operations": local_gf2_ops,
        "selector_local_entries": selector_local_entries,
        "local_node_intern_attempts": local_intern_attempts,
        "elimination_joint_assignments": joint_total,
        "factor_table_entry_evaluations": cumulative_factor_evaluations,
        "output_entries": output_total,
        "factor_table_reads": factor_reads_total,
        "semiring_multiply_events": multiplies_total,
        "marginal_events": output_total,
        "table_write_events_excluding_intern_new_node_writes": local_entries + output_total,
        "node_intern_attempts": node_intern_attempts,
        "mandatory_compilation_aop_lower_bound": cumulative_aop_lower,
        "compilation_aop_upper_bound_if_every_intern_is_unique": aop_upper,
        "peak_joint_table_entries": peak_joint,
        "peak_symbolic_factor_table_slots": peak_symbolic_factor_table_slots,
        "peak_generic_factor_and_scratch_slots": peak_generic_factor_scratch_slots,
        "peak_validation_python_scalar_slots": peak_validation_scalar_slots,
        "peak_validation_projection_uint32_slots": peak_projection_uint32_slots,
        "steps": steps,
    }
    crossings = {
        "peak_joint_table_entries": first_peak_cross,
        "factor_table_entry_evaluations": first_factor_cross,
        "mandatory_compilation_aop_lower_bound": first_aop_cross,
    }
    return {"exact_structural_counts": exact, "first_crossed_step_zero_based": crossings}


def adjudicate_static(manifest: dict[str, Any], ledger: dict[str, Any]) -> dict[str, Any]:
    caps = manifest["resource_envelope"]
    x = ledger["exact_structural_counts"]
    checks = {
        "amended_peak_joint_entries": {
            "value": x["peak_joint_table_entries"],
            "cap": caps["authorized_c90_peak_joint_table_entries"],
            "pass": x["peak_joint_table_entries"] <= caps["authorized_c90_peak_joint_table_entries"],
            "classification": "exact",
        },
        "factor_table_entry_evaluations": {
            "value": x["factor_table_entry_evaluations"],
            "cap": caps["max_factor_table_entry_evaluations_per_algebra"],
            "pass": x["factor_table_entry_evaluations"] <= caps["max_factor_table_entry_evaluations_per_algebra"],
            "classification": "exact",
        },
        "compilation_aop_events": {
            "value_lower_bound": x["mandatory_compilation_aop_lower_bound"],
            "cap": caps["max_compilation_aop_events_per_algebra"],
            "pass_if_lower_bound_within_cap": x["mandatory_compilation_aop_lower_bound"] <= caps["max_compilation_aop_events_per_algebra"],
            "definite_fail": x["mandatory_compilation_aop_lower_bound"] > caps["max_compilation_aop_events_per_algebra"],
            "classification": "exact_lower_bound",
        },
        "retained_nodes_entries_prequalifiable_by_intern_upper": {
            "value_upper_bound": x["node_intern_attempts"],
            "cap": caps["max_retained_canonical_structural_nodes_or_entries_per_algebra"],
            "certified_pass": x["node_intern_attempts"] <= caps["max_retained_canonical_structural_nodes_or_entries_per_algebra"],
            "classification": "exact_upper_bound",
        },
    }
    definite_fail = (
        not checks["amended_peak_joint_entries"]["pass"]
        or not checks["factor_table_entry_evaluations"]["pass"]
        or checks["compilation_aop_events"]["definite_fail"]
    )
    if definite_fail:
        status = "C90_MEMORY_STORAGE_QUALIFICATION_FAILED"
        reason = "EXACT_DETERMINISTIC_COMPILATION_CAP_CROSSED_PRECALIBRATION"
        calibration_required = False
        phase_x_reachable = False
    elif not checks["retained_nodes_entries_prequalifiable_by_intern_upper"]["certified_pass"]:
        status = "C90_MEMORY_STORAGE_QUALIFICATION_INDETERMINATE"
        reason = "RETAINED_NODE_CAP_NOT_PREQUALIFIABLE_WITHOUT_PROHIBITED_FULL_COMPILE"
        calibration_required = False
        phase_x_reachable = False
    else:
        status = "STATIC_CLEAR_FOR_BOUNDED_CALIBRATION"
        reason = None
        calibration_required = True
        phase_x_reachable = False
    return {
        "status": status,
        "reason": reason,
        "deterministic_cap_checks": checks,
        "calibration_required": calibration_required,
        "phase_x_reachable": phase_x_reachable,
    }


def static_report(manifest: dict[str, Any]) -> dict[str, Any]:
    verify_disabled_candidate()
    load_predecessor_evidence()
    _, code, order, record = reconstruct_target(manifest)
    coordinates = frozen_validation_coordinates(len(code["selector_basis_qubits"]))
    if len(coordinates) != manifest["validation"]["total_frozen_selectors"]:
        raise ValueError("frozen C90 validation count drift")
    if digest(coordinates) != manifest["validation"]["validation_set_sha256"]:
        raise ValueError("frozen C90 validation set digest drift")
    ledger = exact_static_ledger(code["scopes"], code["selector_basis_qubits"], order)
    adjudication = adjudicate_static(manifest, ledger)
    report = {
        "schema_version": 1,
        "experiment_id": EXPERIMENT_ID,
        "status": "candidate_executable_not_promoted",
        "source_commit": git_head(),
        "manifest_payload_sha256": MANIFEST_PAYLOAD,
        "phase": "M_STATIC",
        "protected_identity_replay": {
            "c90_source_and_basis_digests": record["source_and_basis_digests"],
            "order_record_sha256": TARGET_DIGESTS["order_record_sha256"],
            "min_fill_induced_width": 25,
            "predicted_peak_joint_table_entries": 67108864,
            "validation_set_sha256": digest(coordinates),
            "validation_selector_count": len(coordinates),
        },
        "resource_ledger": ledger,
        "phase_m_static_adjudication": adjudication,
        "engineering_resource_qualification": {
            "static_structural_phase_completed": True,
            "host_memory_calibration_performed": False,
            "host_memory_measurement_used": False,
        },
        "scientific_exact_compilation": {
            "performed": False,
            "phase_x_reachable_from_this_receipt": adjudication["phase_x_reachable"],
        },
        "scientific_semantic_validation": {"performed": False},
        "claim_boundary": manifest["claim_boundary"],
    }
    report["payload_sha256"] = digest(report)
    return report


def read_meminfo() -> dict[str, int]:
    values: dict[str, int] = {}
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        parts = value.strip().split()
        if not parts or not parts[0].isdigit():
            continue
        amount = int(parts[0])
        if len(parts) > 1 and parts[1].lower() == "kb":
            amount *= 1024
        values[key] = amount
    return values


def current_rss_bytes() -> int:
    status = Path("/proc/self/status")
    if status.exists():
        for line in status.read_text(encoding="utf-8").splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) * 1024
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def calibrate(manifest: dict[str, Any], static_path: Path, output: Path, session_id: str) -> dict[str, Any]:
    static = json.loads(static_path.read_text(encoding="utf-8"))
    if static.get("payload_sha256") != digest({k: v for k, v in static.items() if k != "payload_sha256"}):
        raise ValueError("static receipt self-digest mismatch")
    if static["phase_m_static_adjudication"]["status"] != "STATIC_CLEAR_FOR_BOUNDED_CALIBRATION":
        raise ValueError("calibration is mechanically forbidden by terminal static Phase-M outcome")
    mem = read_meminfo()
    total = mem["MemTotal"]
    policy = manifest["resource_envelope"]["physical_memory"]
    max_probe = min(
        int(policy["calibration_probe_max_bytes"]),
        total * int(policy["calibration_probe_max_fraction_of_total_ram"]["numerator"])
        // int(policy["calibration_probe_max_fraction_of_total_ram"]["denominator"]),
    )
    pointer_bytes = struct.calcsize("P")
    object_sizes = {
        "pointer_bytes": pointer_bytes,
        "int_0": sys.getsizeof(0),
        "int_2pow90": sys.getsizeof(1 << 90),
        "tuple_2_ints": sys.getsizeof((1, 2)),
        "tuple_4_ints": sys.getsizeof((1, 2, 3, 4)),
        "list_empty": sys.getsizeof([]),
        "list_one": sys.getsizeof([None]),
        "dict_empty": sys.getsizeof({}),
        "dict_one_tuple_int": sys.getsizeof({(1, 2): 3}),
    }
    n = min(200_000, max(1_000, max_probe // 512))
    probes = []
    for name, maker in [
        ("list_none", lambda: [None] * n),
        ("list_int", lambda: list(range(n))),
        ("dict_tuple_int", lambda: {(i, i ^ 1): i for i in range(n)}),
    ]:
        before = current_rss_bytes()
        obj = maker()
        after = current_rss_bytes()
        probes.append({
            "name": name,
            "items": n,
            "rss_before": before,
            "rss_after": after,
            "rss_delta_nonnegative": max(0, after - before),
            "container_shallow_bytes": sys.getsizeof(obj),
        })
        del obj
        gc.collect()
    report = {
        "schema_version": 1,
        "experiment_id": EXPERIMENT_ID,
        "phase": "M_CALIBRATION",
        "status": "GREEN_ENGINEERING_CALIBRATION",
        "source_commit": git_head(),
        "manifest_payload_sha256": MANIFEST_PAYLOAD,
        "hosted_session_identity": session_id,
        "meminfo_before": {k: mem.get(k) for k in ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree")},
        "python": {"implementation": sys.implementation.name, "version": sys.version, "pointer_bits": pointer_bytes * 8},
        "object_sizes": object_sizes,
        "probe_limit_bytes": max_probe,
        "probes": probes,
        "device_memory_counted": False,
        "claim_boundary": manifest["claim_boundary"],
    }
    report["payload_sha256"] = digest(report)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def phase_m_adjudicate(manifest: dict[str, Any], static_path: Path, calibration_path: Path | None, output: Path, session_id: str) -> dict[str, Any]:
    static = json.loads(static_path.read_text(encoding="utf-8"))
    static_status = static["phase_m_static_adjudication"]["status"]
    if static_status in {"C90_MEMORY_STORAGE_QUALIFICATION_FAILED", "C90_MEMORY_STORAGE_QUALIFICATION_INDETERMINATE"}:
        outcome = static_status
        predicted = None
        observed = None
    elif static_status != "STATIC_CLEAR_FOR_BOUNDED_CALIBRATION":
        raise ValueError(f"unexpected static status: {static_status}")
    else:
        if calibration_path is None or not calibration_path.exists():
            raise ValueError("calibration receipt required after static clearance")
        calibration = json.loads(calibration_path.read_text(encoding="utf-8"))
        if calibration["manifest_payload_sha256"] != MANIFEST_PAYLOAD:
            raise ValueError("calibration manifest binding mismatch")
        x = static["resource_ledger"]["exact_structural_counts"]
        sizes = calibration["object_sizes"]
        safety = int(manifest["resource_envelope"]["physical_memory"]["engineering_upper_bound_safety_multiplier"])
        pointer_slot_upper = max(sizes["pointer_bytes"], sizes["list_one"] - sizes["list_empty"]) * safety
        int_upper = max(sizes["int_0"], sizes["int_2pow90"]) * safety
        compile_table_bytes = x["peak_symbolic_factor_table_slots"] * pointer_slot_upper
        validation_value_bytes = x["peak_validation_python_scalar_slots"] * (pointer_slot_upper + int_upper)
        projection_bytes = x["peak_validation_projection_uint32_slots"] * 4
        predicted = max(compile_table_bytes, validation_value_bytes + projection_bytes)
        total = calibration["meminfo_before"]["MemTotal"]
        available = calibration["meminfo_before"]["MemAvailable"]
        policy = manifest["resource_envelope"]["physical_memory"]
        fraction_cap = total * int(policy["max_predicted_fraction_of_total_ram"]["numerator"]) // int(policy["max_predicted_fraction_of_total_ram"]["denominator"])
        reserve = int(policy["minimum_absolute_reserve_bytes"])
        pass_memory = predicted <= fraction_cap and total - predicted >= reserve and available >= predicted + reserve
        observed = {"MemTotal": total, "MemAvailable": available, "fraction_cap": fraction_cap, "minimum_reserve_bytes": reserve}
        outcome = "C90_MEMORY_STORAGE_QUALIFIED_WITHIN_BOUND" if pass_memory else "C90_MEMORY_STORAGE_QUALIFICATION_FAILED"
    report = {
        "schema_version": 1,
        "experiment_id": EXPERIMENT_ID,
        "phase": "M_ADJUDICATION",
        "status": outcome,
        "source_commit": git_head(),
        "manifest_payload_sha256": MANIFEST_PAYLOAD,
        "hosted_session_identity": session_id,
        "static_report_sha256": sha256_file(static_path),
        "calibration_report_sha256": sha256_file(calibration_path) if calibration_path else None,
        "conservative_predicted_peak_resident_bytes": predicted,
        "observed_host_memory": observed,
        "phase_x_authorized_by_receipt": outcome == "C90_MEMORY_STORAGE_QUALIFIED_WITHIN_BOUND",
        "claim_boundary": manifest["claim_boundary"],
    }
    report["payload_sha256"] = digest(report)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def require_phase_m_pass(manifest: dict[str, Any], phase_m_path: Path, session_id: str) -> dict[str, Any]:
    receipt = json.loads(phase_m_path.read_text(encoding="utf-8"))
    if receipt.get("payload_sha256") != digest({k: v for k, v in receipt.items() if k != "payload_sha256"}):
        raise ValueError("Phase-M receipt self-digest mismatch")
    if receipt.get("status") != "C90_MEMORY_STORAGE_QUALIFIED_WITHIN_BOUND":
        raise ValueError("Phase X forbidden without exact Phase-M pass")
    if receipt.get("manifest_payload_sha256") != MANIFEST_PAYLOAD:
        raise ValueError("Phase-M manifest binding mismatch")
    if receipt.get("hosted_session_identity") != session_id:
        raise ValueError("Phase-M hosted session mismatch")
    return receipt


def compile_algebra(manifest: dict[str, Any], algebra: str, phase_m_path: Path, session_id: str, output: Path) -> dict[str, Any]:
    if algebra not in manifest["phase_x"]["algebra_order"]:
        raise ValueError("algebra not in frozen order")
    mem = read_meminfo()
    phase_m = require_phase_m_pass(manifest, phase_m_path, session_id)
    predicted = phase_m.get("conservative_predicted_peak_resident_bytes")
    reserve = int(manifest["resource_envelope"]["physical_memory"]["minimum_absolute_reserve_bytes"])
    if not isinstance(predicted, int) or predicted < 0:
        raise ValueError("Phase-M receipt lacks conservative predicted resident bytes")
    if mem.get("MemAvailable", 0) < predicted + reserve:
        report = {
            "schema_version": 1,
            "experiment_id": EXPERIMENT_ID,
            "phase": "X_COMPILE",
            "algebra": algebra,
            "status": "C90_EXACT_COMPILATION_RESOURCE_BOUND_EXHAUSTED",
            "source_commit": git_head(),
            "manifest_payload_sha256": MANIFEST_PAYLOAD,
            "hosted_session_identity": session_id,
            "pre_run_memavailable_bytes": mem.get("MemAvailable"),
            "metadata": None,
            "cap_checks": {"physical_memavailable_gate": False},
            "first_crossed_resource_witness": {"cap": "fresh_MemAvailable", "required_bytes": predicted + reserve, "observed_bytes": mem.get("MemAvailable", 0)},
            "claim_boundary": manifest["claim_boundary"],
        }
        report["payload_sha256"] = digest(report)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report
    _, code, order, _ = reconstruct_target(manifest)
    metadata = compile_symbolic_metadata(code["scopes"], code["selector_basis_qubits"], order, algebra)
    caps = manifest["resource_envelope"]
    checks = {
        "peak_joint": metadata["peak_joint_table_entries"] <= caps["authorized_c90_peak_joint_table_entries"],
        "factor_evaluations": metadata["factor_table_entry_evaluations"] <= caps["max_factor_table_entry_evaluations_per_algebra"],
        "retained_nodes": metadata["node_count"] <= caps["max_retained_canonical_structural_nodes_or_entries_per_algebra"],
        "serialized_bytes": metadata["canonical_serialized_bytes"] <= caps["max_canonical_serialized_compiled_bytes_per_algebra"],
        "aop": metadata["compile_aop_total"] <= caps["max_compilation_aop_events_per_algebra"],
    }
    status = "C90_EXACT_COMPILATION_COMPLETED" if all(checks.values()) else "C90_EXACT_COMPILATION_RESOURCE_BOUND_EXHAUSTED"
    report = {
        "schema_version": 1,
        "experiment_id": EXPERIMENT_ID,
        "phase": "X_COMPILE",
        "algebra": algebra,
        "status": status,
        "source_commit": git_head(),
        "manifest_payload_sha256": MANIFEST_PAYLOAD,
        "hosted_session_identity": session_id,
        "pre_run_memavailable_bytes": mem.get("MemAvailable"),
        "metadata": metadata,
        "cap_checks": checks,
        "claim_boundary": manifest["claim_boundary"],
    }
    report["payload_sha256"] = digest(report)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def validate_307(manifest: dict[str, Any], compile_paths: list[Path], output: Path) -> dict[str, Any]:
    expected = manifest["phase_x"]["algebra_order"]
    if len(compile_paths) != 3:
        raise ValueError("all three compilation receipts required")
    seen = []
    for path in compile_paths:
        row = json.loads(path.read_text(encoding="utf-8"))
        if row.get("status") != "C90_EXACT_COMPILATION_COMPLETED":
            raise ValueError("validation forbidden unless all three compiles are green")
        seen.append(row.get("algebra"))
    if seen != expected:
        raise ValueError("compilation receipt order drift")
    _, code, order, _ = reconstruct_target(manifest)
    descriptor, _ = compile_descriptor(code["scopes"], code["selector_basis_qubits"], order)
    coords = frozen_validation_coordinates(49)
    rows = run_validation_parallel(coords, code["scopes"], code["selector_basis_qubits"], order, descriptor, processes=1)
    report = {
        "schema_version": 1,
        "experiment_id": EXPERIMENT_ID,
        "phase": "VALIDATE_307",
        "status": "C90_EXACT_SEMANTIC_VALIDATION_COMPLETED_ON_FROZEN_307",
        "source_commit": git_head(),
        "manifest_payload_sha256": MANIFEST_PAYLOAD,
        "selector_count": len(coords),
        "validation_set_sha256": digest(coords),
        "validation_outputs_sha256": digest(rows),
        "all_exact_equal": True,
        "exhaustive_all_selector_equivalence": False,
        "claim_boundary": manifest["claim_boundary"],
    }
    report["payload_sha256"] = digest(report)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("static"); p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("calibrate"); p.add_argument("--static", type=Path, required=True); p.add_argument("--session-id", required=True); p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("adjudicate"); p.add_argument("--static", type=Path, required=True); p.add_argument("--calibration", type=Path); p.add_argument("--session-id", required=True); p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("compile-algebra"); p.add_argument("--algebra", required=True); p.add_argument("--phase-m", type=Path, required=True); p.add_argument("--session-id", required=True); p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("validate"); p.add_argument("--compile", type=Path, action="append", required=True); p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = load_manifest()
    if args.command == "static":
        result = static_report(manifest); args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    elif args.command == "calibrate":
        result = calibrate(manifest, args.static, args.output, args.session_id)
    elif args.command == "adjudicate":
        result = phase_m_adjudicate(manifest, args.static, args.calibration, args.output, args.session_id)
    elif args.command == "compile-algebra":
        result = compile_algebra(manifest, args.algebra, args.phase_m, args.session_id, args.output)
    else:
        result = validate_307(manifest, args.compile, args.output)
    print(json.dumps({"experiment_id": EXPERIMENT_ID, "phase": result.get("phase"), "status": result.get("status"), "payload_sha256": result.get("payload_sha256")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
