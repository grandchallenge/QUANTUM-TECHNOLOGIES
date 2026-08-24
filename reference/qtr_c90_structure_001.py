#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import deque
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import qldpc_scale_001a_math as math001a
import qldpc_scale_001a_symbolic as symbolic001a
import qtr_c90_exact_requal_001 as predecessor
from qldpc_scale_001a_shared import SEMIRINGS, digest

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "QTR-C90-STRUCTURE-001"
MANIFEST_PATH = ROOT / "registry/qtr-c90-structure-001-manifest.json"
MANIFEST_PAYLOAD = "205ecca612ae366694d4c17b6ce518727abf80114b6e52598073b238946f2a6a"
PROTECTED_START_MAIN = "4182946ec5bdfda9de1443124624bd084a5acfda"
PREDECESSOR_EVIDENCE_PATH = ROOT / "evidence/QTR-C90-EXACT-REQUAL-001-report.json"
PREDECESSOR_EVIDENCE_PAYLOAD = "5b7740eef2d5b9e8f95cbf487c3841223b7e1350d7b0f9558c9629c78357dc0c"
C72_EVIDENCE_PATH = ROOT / "evidence/QLDPC-SCALE-001A-report.json"
C72_EVIDENCE_PAYLOAD = "198bb28f47844aa98efa20d8c838c48870a8aef41ccfda266b16661677e363e1"
C72_VALIDATION_OUTPUTS = "b5e168d3c8f4b420c8f2c1129ea23a3a4c5d6be946053aac7f1650cc4dd79189"
C72_VALIDATION_SET = "2eabc60f4ea2d64be6e4fea5ee33e527de46b115e727a8607b5332b19ba1e1bf"
ALGEBRAS = ["sum_product_bsc_p_0_1", "soft_tropical_base_2", "min_plus_hamming"]


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "UNKNOWN"


def load_manifest() -> dict[str, Any]:
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    claimed = data.get("manifest_payload_sha256")
    unsigned = dict(data)
    unsigned.pop("manifest_payload_sha256", None)
    if claimed != MANIFEST_PAYLOAD or digest(unsigned) != MANIFEST_PAYLOAD:
        raise ValueError("structure manifest self-digest mismatch")
    expected_authority = {
        "council_issue": 97,
        "execution_issue": 98,
        "human_steward_comment": 5383415686,
        "protected_start_main": PROTECTED_START_MAIN,
        "referee_comment": 5383330531,
    }
    if data["authority"] != expected_authority:
        raise ValueError("structure authority drift")
    if list(data["methods"]) != [
        "S0_BASELINE",
        "S1_GF2_CONSTRAINT_ELIMINATION",
        "S2_SEPARATOR_INTERFACE_COMPILATION",
        "S3_GF2_PLUS_SEPARATOR",
    ]:
        raise ValueError("predeclared method family drift")
    return data


def load_self_verified(path: Path, payload: str) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("payload_sha256") != payload:
        raise ValueError(f"payload identity drift: {path}")
    unsigned = dict(data)
    unsigned.pop("payload_sha256", None)
    if digest(unsigned) != payload:
        raise ValueError(f"payload self-verification failed: {path}")
    return data


def no_hard_affine_constraints() -> dict[str, Any]:
    checks: dict[str, bool] = {}
    for name, definition in SEMIRINGS.items():
        if definition["kind"] in {"sum_product", "soft_tropical"}:
            values = list(definition["local_bit_weights"])
            checks[name] = len(values) == 2 and all(int(v) > 0 for v in values)
        elif definition["kind"] == "min_plus":
            values = list(definition["local_bit_costs"])
            checks[name] = len(values) == 2 and all(isinstance(v, int) for v in values)
        else:
            checks[name] = False
    if not all(checks.values()):
        raise ValueError("cannot certify full-support weighted factor schema")
    return {
        "hard_affine_factor_count": 0,
        "per_algebra_full_support": checks,
        "s1_action": "IDENTITY_NO_ELIGIBLE_HARD_AFFINE_FACTORS",
    }


def primal_graph(scopes: list[tuple[int, ...]], variable_count: int) -> list[set[int]]:
    adjacency = [set() for _ in range(variable_count)]
    for scope in scopes:
        for pos, left in enumerate(scope):
            for right in scope[pos + 1:]:
                adjacency[left].add(right)
                adjacency[right].add(left)
    return adjacency


def triangulated_bags(scopes: list[tuple[int, ...]], order: list[int]) -> list[tuple[int, ...]]:
    adjacency = primal_graph(scopes, len(order))
    active = set(range(len(order)))
    bags: list[tuple[int, ...]] = []
    for variable in order:
        neighbors = sorted(adjacency[variable] & active)
        bags.append(tuple(sorted([variable, *neighbors])))
        for pos, left in enumerate(neighbors):
            for right in neighbors[pos + 1:]:
                adjacency[left].add(right)
                adjacency[right].add(left)
        for neighbor in neighbors:
            adjacency[neighbor].discard(variable)
        active.remove(variable)
    return bags


def maximal_bags(raw_bags: list[tuple[int, ...]]) -> list[tuple[int, ...]]:
    unique = sorted(set(raw_bags))
    sets = [set(bag) for bag in unique]
    return [
        bag for index, bag in enumerate(unique)
        if not any(sets[index] < sets[other] for other in range(len(unique)) if other != index)
    ]


class DSU:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, left: int, right: int) -> bool:
        a, b = self.find(left), self.find(right)
        if a == b:
            return False
        if a > b:
            a, b = b, a
        self.parent[b] = a
        return True


def junction_tree(scopes: list[tuple[int, ...]], baseline_order: list[int]) -> dict[str, Any]:
    raw = triangulated_bags(scopes, baseline_order)
    bags = maximal_bags(raw)
    if not bags:
        raise ValueError("no maximal bags")
    edges: list[tuple[int, int, int]] = []
    intersection_work = 0
    for left in range(len(bags)):
        lset = set(bags[left])
        for right in range(left + 1, len(bags)):
            rset = set(bags[right])
            inter = lset & rset
            intersection_work += len(bags[left]) + len(bags[right]) + len(inter) + 1
            edges.append((len(inter), left, right))
    edges.sort(key=lambda item: (-item[0], item[1], item[2]))
    dsu = DSU(len(bags))
    tree_edges: list[tuple[int, int, tuple[int, ...]]] = []
    for _, left, right in edges:
        if dsu.union(left, right):
            tree_edges.append((left, right, tuple(sorted(set(bags[left]) & set(bags[right])))))
            if len(tree_edges) == len(bags) - 1:
                break
    if len(tree_edges) != max(0, len(bags) - 1):
        raise ValueError("junction tree construction failed")
    max_size = max(map(len, bags))
    root = min(index for index, bag in enumerate(bags) if len(bag) == max_size)
    neighbors = [[] for _ in bags]
    for left, right, separator in tree_edges:
        neighbors[left].append((right, separator))
        neighbors[right].append((left, separator))
    parent = [-1] * len(bags)
    parent_sep: list[tuple[int, ...]] = [tuple() for _ in bags]
    children = [[] for _ in bags]
    queue = deque([root])
    parent[root] = root
    while queue:
        current = queue.popleft()
        for nxt, sep in sorted(neighbors[current], key=lambda item: item[0]):
            if parent[nxt] != -1:
                continue
            parent[nxt] = current
            parent_sep[nxt] = sep
            children[current].append(nxt)
            queue.append(nxt)
    factor_assignment: list[int] = []
    for scope in scopes:
        containing = [index for index, bag in enumerate(bags) if set(scope) <= set(bag)]
        if not containing:
            raise ValueError(f"factor scope not covered by junction bag: {scope}")
        factor_assignment.append(min(containing))
    postorder: list[int] = []

    def visit(node: int) -> None:
        for child in sorted(children[node]):
            visit(child)
        postorder.append(node)

    visit(root)
    emitted: set[int] = set()
    separator_order: list[int] = []
    for node in postorder:
        keep = set(parent_sep[node]) if node != root else set()
        for variable in sorted(set(bags[node]) - keep):
            if variable not in emitted:
                separator_order.append(variable)
                emitted.add(variable)
    for variable in sorted(set(range(len(baseline_order))) - emitted):
        separator_order.append(variable)
        emitted.add(variable)
    if sorted(separator_order) != list(range(len(baseline_order))):
        raise ValueError("separator-derived order is not a permutation")
    receipt = {
        "raw_bag_count": len(raw),
        "maximal_bag_count": len(bags),
        "maximal_bags": [list(bag) for bag in bags],
        "root_bag_id": root,
        "tree_edges": [
            {"left": left, "right": right, "separator": list(separator)}
            for left, right, separator in tree_edges
        ],
        "parent": parent,
        "parent_separators": [list(value) for value in parent_sep],
        "children": [sorted(value) for value in children],
        "factor_assignment": factor_assignment,
        "separator_elimination_order": separator_order,
        "max_bag_arity": max_size,
        "max_separator_arity": max((len(item[2]) for item in tree_edges), default=0),
        "intersection_preprocess_aop": intersection_work,
    }
    receipt["canonical_sha256"] = digest(receipt)
    return receipt


def c72_control_certificate(method: str, jt: dict[str, Any] | None) -> dict[str, Any]:
    evidence = load_self_verified(C72_EVIDENCE_PATH, C72_EVIDENCE_PAYLOAD)
    code = math001a.construct_code()
    scopes = code["scopes"]
    selector_basis = code["selector_basis_qubits"]
    baseline_order = math001a.deterministic_min_fill(scopes, len(code["x_basis"]))
    if evidence["selector_validation"]["validation_set_sha256"] != C72_VALIDATION_SET:
        raise ValueError("C72 protected validation-set drift")
    if evidence["selector_validation"]["validation_outputs_sha256"] != C72_VALIDATION_OUTPUTS:
        raise ValueError("C72 protected validation-output drift")
    if method in {"S0_BASELINE", "S1_GF2_CONSTRAINT_ELIMINATION"}:
        order = baseline_order
        receipt: dict[str, Any] = {"kind": "identity_or_protected_baseline", "order": order}
    else:
        if jt is None:
            jt = junction_tree(scopes, baseline_order)
        order = list(jt["separator_elimination_order"])
        receipt = jt
    work = math001a.scope_work(scopes, order)
    caps = {"peak": 1 << 20, "factor": 1 << 27, "retained": 1 << 22, "serialized": 512 * 1024 * 1024, "aop": 1 << 31}
    if work["peak_joint_table_entries"] > caps["peak"] or work["factor_table_entry_evaluations"] > caps["factor"]:
        return {
            "status": "CONTROL_RESOURCE_BOUND_EXHAUSTED",
            "work": work,
            "transformation_receipt_sha256": digest(receipt),
            "semantic_validation_performed": False,
        }
    symbolic: dict[str, Any] = {}
    all_caps = True
    for algebra in ALGEBRAS:
        metadata = symbolic001a.compile_symbolic_metadata(scopes, selector_basis, order, algebra)
        symbolic[algebra] = {
            key: metadata[key] for key in (
                "node_count", "compile_aop_total", "factor_table_entry_evaluations",
                "peak_joint_table_entries", "canonical_serialized_bytes", "canonical_sha256"
            )
        }
        all_caps = all_caps and (
            metadata["node_count"] <= caps["retained"]
            and metadata["compile_aop_total"] <= caps["aop"]
            and metadata["factor_table_entry_evaluations"] <= caps["factor"]
            and metadata["peak_joint_table_entries"] <= caps["peak"]
            and metadata["canonical_serialized_bytes"] <= caps["serialized"]
        )
    if not all_caps:
        return {
            "status": "CONTROL_RESOURCE_BOUND_EXHAUSTED",
            "work": work,
            "symbolic": symbolic,
            "transformation_receipt_sha256": digest(receipt),
            "semantic_validation_performed": False,
        }
    coordinates = symbolic001a.frozen_validation_coordinates(len(selector_basis))
    if len(coordinates) != 300 or digest(coordinates) != C72_VALIDATION_SET:
        raise ValueError("C72 control coordinates drift")
    descriptor, descriptor_meta = math001a.compile_descriptor(scopes, selector_basis, order)
    rows = math001a.run_validation_parallel(coordinates, scopes, selector_basis, order, descriptor)
    output_sha = digest(rows)
    status = "CONTROL_CERTIFIED" if output_sha == C72_VALIDATION_OUTPUTS else "CONTROL_SEMANTICS_REJECTED"
    return {
        "status": status,
        "work": work,
        "symbolic": symbolic,
        "validation_count": len(coordinates),
        "validation_outputs_sha256": output_sha,
        "protected_validation_outputs_sha256": C72_VALIDATION_OUTPUTS,
        "transformation_receipt_sha256": digest(receipt),
        "compiled_descriptor_sha256": descriptor_meta["canonical_sha256"],
        "semantic_validation_performed": True,
    }


def static_method_record(
    method: str,
    manifest: dict[str, Any],
    scopes: list[tuple[int, ...]],
    selector_basis: list[int],
    baseline_order: list[int],
    control: dict[str, Any],
    s1: dict[str, Any],
    jt: dict[str, Any] | None,
) -> dict[str, Any]:
    if method == "S0_BASELINE":
        order = baseline_order
        preprocessing = 0
        transform: dict[str, Any] = {"kind": "protected_baseline"}
    elif method == "S1_GF2_CONSTRAINT_ELIMINATION":
        order = baseline_order
        preprocessing = 0
        transform = s1
    else:
        if jt is None:
            raise ValueError("junction tree missing")
        order = list(jt["separator_elimination_order"])
        preprocessing = int(jt["intersection_preprocess_aop"])
        transform = jt
    if control["status"] != "CONTROL_CERTIFIED" and method != "S0_BASELINE":
        return {
            "method": method,
            "control_status": control["status"],
            "c90_status": "NOT_ADJUDICATED_CONTROL_NOT_CERTIFIED",
            "transformation_receipt_sha256": digest(transform),
        }
    ledger = predecessor.exact_static_ledger(scopes, selector_basis, order)
    exact = ledger["exact_structural_counts"]
    caps = manifest["resource_envelope"]
    normalized_aop_lower = exact["mandatory_compilation_aop_lower_bound"] + preprocessing
    normalized_aop_upper = exact["compilation_aop_upper_bound_if_every_intern_is_unique"] + preprocessing
    intern_upper = exact["node_intern_attempts"]
    peak_pass = exact["peak_joint_table_entries"] <= caps["max_peak_joint_or_interface_entries"]
    factor_pass = exact["factor_table_entry_evaluations"] <= caps["max_factor_or_constraint_entry_evaluations_per_algebra"]
    aop_fail = normalized_aop_lower > caps["max_compilation_aop_events_per_algebra"]
    aop_pass = normalized_aop_upper <= caps["max_compilation_aop_events_per_algebra"]
    retained_pass = intern_upper <= caps["max_retained_canonical_structural_nodes_or_entries_per_algebra"]
    definite_fail = (not peak_pass) or (not factor_pass) or aop_fail
    unknown = (not aop_fail and not aop_pass) or (not retained_pass)
    if definite_fail:
        status = "C90_STATIC_CAP_EXHAUSTED"
    elif unknown:
        status = "C90_STATIC_RESOURCE_INDETERMINATE"
    else:
        serialized_upper = intern_upper * 32
        status = "C90_STATIC_ALL_CAPS_PASS" if serialized_upper <= caps["max_canonical_serialized_compiled_bytes_per_algebra"] else "C90_STATIC_RESOURCE_INDETERMINATE"
    return {
        "method": method,
        "control_status": control["status"],
        "c90_status": status,
        "native_ledger": exact,
        "normalized_ledger": {
            "separator_or_gf2_preprocess_aop": preprocessing,
            "mandatory_compilation_aop_lower_bound": normalized_aop_lower,
            "compilation_aop_upper_bound_if_every_intern_is_unique": normalized_aop_upper,
            "factor_or_constraint_entry_evaluations": exact["factor_table_entry_evaluations"],
            "retained_node_or_entry_upper_bound": intern_upper,
            "conservative_serialized_upper_bound_bytes_if_32_bytes_per_retained_entry": intern_upper * 32,
        },
        "cap_checks": {
            "peak_joint_or_interface": {"pass": peak_pass, "value": exact["peak_joint_table_entries"], "cap": caps["max_peak_joint_or_interface_entries"]},
            "factor_or_constraint_evaluations": {"pass": factor_pass, "value": exact["factor_table_entry_evaluations"], "cap": caps["max_factor_or_constraint_entry_evaluations_per_algebra"]},
            "aop": {"certified_pass": aop_pass, "definite_fail": aop_fail, "lower": normalized_aop_lower, "upper": normalized_aop_upper, "cap": caps["max_compilation_aop_events_per_algebra"]},
            "retained": {"certified_pass": retained_pass, "upper": intern_upper, "cap": caps["max_retained_canonical_structural_nodes_or_entries_per_algebra"]},
        },
        "first_crossed_step_zero_based": ledger["first_crossed_step_zero_based"],
        "transformation_receipt_sha256": digest(transform),
        "order_sha256": digest(order),
    }


def evaluate_static(*, full_control: bool = True) -> dict[str, Any]:
    manifest = load_manifest()
    predecessor_evidence = load_self_verified(PREDECESSOR_EVIDENCE_PATH, PREDECESSOR_EVIDENCE_PAYLOAD)
    if predecessor_evidence["adjudication"]["primary_outcome"] != "C90_MEMORY_STORAGE_QUALIFICATION_FAILED":
        raise ValueError("predecessor outcome drift")
    pmanifest = predecessor.load_manifest()
    _, code90, baseline_order, _ = predecessor.reconstruct_target(pmanifest)
    s0_ledger = predecessor.exact_static_ledger(code90["scopes"], code90["selector_basis_qubits"], baseline_order)
    s0_exact = s0_ledger["exact_structural_counts"]
    if s0_exact["factor_table_entry_evaluations"] != 201384562:
        raise ValueError("S0 factor-evaluation replay drift")
    if s0_exact["peak_joint_table_entries"] != 67108864:
        raise ValueError("S0 peak replay drift")
    if s0_exact["mandatory_compilation_aop_lower_bound"] != 3410023338:
        raise ValueError("S0 AOP replay drift")
    s1 = no_hard_affine_constraints()
    code72 = math001a.construct_code()
    c72_base_order = math001a.deterministic_min_fill(code72["scopes"], len(code72["x_basis"]))
    jt72 = junction_tree(code72["scopes"], c72_base_order)
    jt90 = junction_tree(code90["scopes"], baseline_order)
    if full_control:
        c72_s2 = c72_control_certificate("S2_SEPARATOR_INTERFACE_COMPILATION", jt72)
    else:
        c72_s2 = {"status": "CONTROL_CERTIFICATION_NOT_RUN", "transformation_receipt_sha256": jt72["canonical_sha256"], "semantic_validation_performed": False}
    controls = {
        "S0_BASELINE": {"status": "CONTROL_CERTIFIED", "basis": "protected C72 exact result"},
        "S1_GF2_CONSTRAINT_ELIMINATION": {"status": "CONTROL_CERTIFIED", "basis": "machine-checked identity: no eligible hard affine factors", **s1},
        "S2_SEPARATOR_INTERFACE_COMPILATION": c72_s2,
        "S3_GF2_PLUS_SEPARATOR": {**c72_s2, "basis": "S1 is identity; S3 receipt/order exactly S2"},
    }
    records: dict[str, Any] = {}
    for method in manifest["methods"]:
        records[method] = static_method_record(
            method, manifest, code90["scopes"], code90["selector_basis_qubits"], baseline_order,
            controls[method], s1,
            jt90 if method in {"S2_SEPARATOR_INTERFACE_COMPILATION", "S3_GF2_PLUS_SEPARATOR"} else None,
        )
    nonbaseline = [records[name] for name in manifest["methods"] if name != "S0_BASELINE"]
    if any(row["c90_status"] == "C90_STATIC_ALL_CAPS_PASS" for row in nonbaseline):
        phase_c = "PHASE_D_ELIGIBLE_METHODS_PRESENT"
        overall = None
    elif any(row["c90_status"] == "C90_STATIC_RESOURCE_INDETERMINATE" for row in nonbaseline):
        phase_c = "PHASE_C_TERMINAL_INDETERMINATE"
        overall = "C90_PREDECLARED_EXACT_STRUCTURAL_FAMILY_INDETERMINATE"
    elif all(row["c90_status"] in {"C90_STATIC_CAP_EXHAUSTED", "NOT_ADJUDICATED_CONTROL_NOT_CERTIFIED"} for row in nonbaseline):
        phase_c = "PHASE_C_TERMINAL_FAMILY_EXHAUSTED"
        overall = "C90_PREDECLARED_EXACT_STRUCTURAL_FAMILY_EXHAUSTED"
    else:
        phase_c = "PHASE_C_TERMINAL_MIXED"
        overall = "C90_PREDECLARED_EXACT_STRUCTURAL_FAMILY_INDETERMINATE"
    report = {
        "schema_version": 1,
        "experiment_id": EXPERIMENT_ID,
        "status": "candidate_executable_not_promoted",
        "source_commit": git_head(),
        "manifest_payload_sha256": MANIFEST_PAYLOAD,
        "authority": manifest["authority"],
        "s0_replay": {
            "factor_table_entry_evaluations": s0_exact["factor_table_entry_evaluations"],
            "peak_joint_table_entries": s0_exact["peak_joint_table_entries"],
            "mandatory_compilation_aop_lower_bound": s0_exact["mandatory_compilation_aop_lower_bound"],
            "matches_protected_predecessor": True,
        },
        "s1_eligibility": s1,
        "control_certification": controls,
        "c90_methods": records,
        "phase_c_disposition": phase_c,
        "overall_outcome": overall,
        "phase_d_reached": False,
        "phase_e_reached": False,
        "claim_boundary": manifest["claim_boundary"],
    }
    report["payload_sha256"] = digest(report)
    return report


def materialize_one(method: str, algebra: str, output: Path) -> None:
    if method not in {"S1_GF2_CONSTRAINT_ELIMINATION", "S2_SEPARATOR_INTERFACE_COMPILATION", "S3_GF2_PLUS_SEPARATOR"}:
        raise ValueError("materialization method not authorized")
    if algebra not in ALGEBRAS:
        raise ValueError("algebra not authorized")
    report = evaluate_static(full_control=True)
    row = report["c90_methods"][method]
    if row["c90_status"] != "C90_STATIC_ALL_CAPS_PASS":
        raise RuntimeError("Phase D forbidden: method lacks certified static all-cap pass")
    pmanifest = predecessor.load_manifest()
    _, code, baseline_order, _ = predecessor.reconstruct_target(pmanifest)
    order = baseline_order if method == "S1_GF2_CONSTRAINT_ELIMINATION" else junction_tree(code["scopes"], baseline_order)["separator_elimination_order"]
    metadata = symbolic001a.compile_symbolic_metadata(code["scopes"], code["selector_basis_qubits"], order, algebra)
    caps = load_manifest()["resource_envelope"]
    checks = {
        "peak": metadata["peak_joint_table_entries"] <= caps["max_peak_joint_or_interface_entries"],
        "factor": metadata["factor_table_entry_evaluations"] <= caps["max_factor_or_constraint_entry_evaluations_per_algebra"],
        "retained": metadata["node_count"] <= caps["max_retained_canonical_structural_nodes_or_entries_per_algebra"],
        "serialized": metadata["canonical_serialized_bytes"] <= caps["max_canonical_serialized_compiled_bytes_per_algebra"],
        "aop": metadata["compile_aop_total"] <= caps["max_compilation_aop_events_per_algebra"],
    }
    payload = {
        "experiment_id": EXPERIMENT_ID,
        "method": method,
        "algebra": algebra,
        "source_commit": git_head(),
        "scientific_backend": "cpu_reference",
        "metadata": metadata,
        "cap_checks": checks,
        "status": "C90_MATERIALIZATION_COMPLETED" if all(checks.values()) else "C90_MATERIALIZATION_RESOURCE_BOUND_EXHAUSTED",
    }
    payload["payload_sha256"] = digest(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not all(checks.values()):
        raise SystemExit(3)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["static", "materialize-one"], default="static")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--method")
    parser.add_argument("--algebra")
    parser.add_argument("--skip-full-control", action="store_true")
    args = parser.parse_args()
    if args.phase == "static":
        report = evaluate_static(full_control=not args.skip_full_control)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({
            "experiment_id": EXPERIMENT_ID,
            "status": report["status"],
            "phase_c_disposition": report["phase_c_disposition"],
            "overall_outcome": report["overall_outcome"],
            "payload_sha256": report["payload_sha256"],
        }, sort_keys=True))
    else:
        if not args.method or not args.algebra:
            raise SystemExit("--method and --algebra are required for materialize-one")
        materialize_one(args.method, args.algebra, args.output)


if __name__ == "__main__":
    main()
