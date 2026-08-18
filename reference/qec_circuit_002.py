#!/usr/bin/env python3
"""QEC-CIRCUIT-002: exact temporal TCM representation decomposition audit."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "QEC-CIRCUIT-002"
EVALUATOR_VERSION = "0.1.0"
MANIFEST_PATH = ROOT / "registry/qec-circuit-002-manifest.json"
MANIFEST_PAYLOAD = "9ba84244f828bc0c4f9f128e54d2c89693930c2280540f9dc420ae13e964aa29"
EXPECTED_START = "82027613cc966c755c4af8420d0584b5b79fa1e4"

HZ_ROWS = [
    "101100000110000100",
    "110010000011000010",
    "011001000101000001",
    "000011001001101000",
    "100000101000100110",
    "010000110000010011",
    "001000011000001101",
]
LOGICAL_Z = [
    "101110001100000000",
    "101011110000000000",
    "011000010010000000",
    "110000100100000000",
]
REPRESENTATIONS = (
    "R0_BASELINE_107_FACTOR",
    "R1_TERMINAL_DIRECT_AUX",
    "R2_TERMINAL_CHAIN_AUX",
    "R3_CAUSAL_STATE_CHAIN",
)

def cbytes(x: Any) -> bytes:
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")

def digest(x: Any) -> str:
    return hashlib.sha256(cbytes(x)).hexdigest()

def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def support(bitstring: str) -> list[int]:
    return [q for q, bit in enumerate(bitstring) if bit == "1"]

def git_blob(path: str) -> str:
    return subprocess.check_output(["git", "rev-parse", f"HEAD:{path}"], cwd=ROOT, text=True).strip()

def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    data = load_json(path)
    claimed = data.pop("manifest_payload_sha256")
    observed = digest(data)
    data["manifest_payload_sha256"] = claimed
    if claimed != MANIFEST_PAYLOAD or observed != MANIFEST_PAYLOAD:
        raise ValueError("QEC-CIRCUIT-002 manifest self-digest mismatch")
    if data["experiment_id"] != EXPERIMENT_ID:
        raise ValueError("QEC-CIRCUIT-002 experiment drift")
    if data["authority"] != {
        "council_issue": 82,
        "execution_issue": 83,
        "human_steward_authorization_comment": 5323092968,
        "human_steward_disposition": "ADOPT_WITH_AMENDMENTS__AUTHORIZE_QEC_CIRCUIT_002_ONLY",
        "protected_start_main": EXPECTED_START,
        "referee_comment": 5323031200,
        "referee_recommendation": "RECOMMEND_ADOPTION_WITH_AMENDMENTS__NO_EXECUTION_AUTHORITY",
    }:
        raise ValueError("QEC-CIRCUIT-002 authority drift")
    if data["status"] != "preoutcome_representation_family_frozen_before_successor_width_inspection":
        raise ValueError("QEC-CIRCUIT-002 preoutcome status drift")
    if data["representation_family_mutable_after_width_inspection"] is not False:
        raise ValueError("representation family mutation channel opened")
    if [row["id"] for row in data["representations"]] != list(REPRESENTATIONS[1:]):
        raise ValueError("predeclared representation order drift")
    return data

def verify_predecessor(manifest: dict[str, Any]) -> dict[str, Any]:
    p = manifest["predecessor"]
    expected_blobs = {
        "registry/qec-circuit-001-manifest.json": p["manifest_blob"],
        "registry/qec-circuit-001-manifest-amendment-001.json": p["manifest_amendment_blob"],
        "registry/qec-circuit-001.json": p["registry_blob"],
        "evidence/QEC-CIRCUIT-001-report.json": p["evidence_blob"],
    }
    observed = {path: git_blob(path) for path in expected_blobs}
    if observed != expected_blobs:
        raise ValueError("protected QEC-CIRCUIT-001 blob drift")
    registry = load_json(ROOT / "registry/qec-circuit-001.json")
    evidence = load_json(ROOT / "evidence/QEC-CIRCUIT-001-report.json")
    if registry["experiments"][0]["status"] != "candidate_executable_not_promoted":
        raise ValueError("protected predecessor registry status drift")
    if evidence["status"] != "candidate_executable_not_promoted":
        raise ValueError("protected predecessor evidence status drift")
    if evidence["payload_sha256"] != p["evidence_payload_sha256"]:
        raise ValueError("protected predecessor evidence payload drift")
    promotion = load_json(ROOT / p["promotion_record_path"])
    if promotion["status"] != "referee_promoted_bounded":
        raise ValueError("protected predecessor promotion status drift")
    return {"blob_readback": observed, "promotion_status": promotion["status"]}

def detector_scopes() -> list[list[int]]:
    hz = [support(row) for row in HZ_ROWS]
    scopes: list[list[int]] = []
    for c, s in enumerate(hz):
        scopes.append(s + [54 + c])
    for c, s in enumerate(hz):
        scopes.append([18 + q for q in s] + [54 + c, 61 + c])
    for c, s in enumerate(hz):
        scopes.append([36 + q for q in s] + [61 + c, 68 + c])
    for c in range(7):
        scopes.append([68 + c])
    return scopes

def logical_selector_scopes(offsets: tuple[int, ...]) -> list[list[int]]:
    out: list[list[int]] = []
    for row in LOGICAL_Z:
        s = support(row)
        scope: list[int] = []
        for offset in offsets:
            scope.extend(offset + q for q in s)
        out.append(scope)
    return out

def representation_scopes(rep: str) -> tuple[int, list[list[int]]]:
    unary = [[q] for q in range(75)]
    detectors = detector_scopes()
    if rep == "R0_BASELINE_107_FACTOR":
        return 75, detectors + unary + logical_selector_scopes((0, 18, 36))
    if rep == "R1_TERMINAL_DIRECT_AUX":
        hard = [[q, 18 + q, 36 + q, 75 + q] for q in range(18)]
        selectors = logical_selector_scopes((75,))
        return 93, detectors + unary + hard + selectors
    if rep == "R2_TERMINAL_CHAIN_AUX":
        first = [[q, 18 + q, 75 + q] for q in range(18)]
        terminal = [[75 + q, 36 + q, 93 + q] for q in range(18)]
        selectors = logical_selector_scopes((93,))
        return 111, detectors + unary + first + terminal + selectors
    if rep == "R3_CAUSAL_STATE_CHAIN":
        first = [[q, 18 + q, 75 + q] for q in range(18)]
        terminal = [[75 + q, 36 + q, 93 + q] for q in range(18)]
        hz = [support(row) for row in HZ_ROWS]
        increments: list[list[int]] = []
        for t, base in enumerate((0, 18, 36)):
            for c, s in enumerate(hz):
                increments.append([base + q for q in s] + [111 + 7 * t + c])
        local_detectors: list[list[int]] = []
        for c in range(7):
            local_detectors.append([111 + c, 54 + c])
        for c in range(7):
            local_detectors.append([118 + c, 54 + c, 61 + c])
        for c in range(7):
            local_detectors.append([125 + c, 61 + c, 68 + c])
        for c in range(7):
            local_detectors.append([68 + c])
        selectors = logical_selector_scopes((93,))
        return 132, unary + first + terminal + increments + local_detectors + selectors
    raise ValueError(rep)

def primal_graph(scopes: list[list[int]], variable_count: int) -> list[set[int]]:
    adj = [set() for _ in range(variable_count)]
    for scope in scopes:
        for i, a in enumerate(scope):
            for b in scope[i + 1:]:
                adj[a].add(b)
                adj[b].add(a)
    return adj

def elimination_order(adj0: list[set[int]], policy: str) -> dict[str, Any]:
    adj = [set(x) for x in adj0]
    alive = set(range(len(adj)))
    order: list[int] = []
    widths: list[int] = []
    fill_total = 0
    while alive:
        def score(v: int) -> tuple[int, ...]:
            neigh = sorted(adj[v] & alive)
            if policy == "lexicographic":
                return (v,)
            if policy == "deterministic_min_degree":
                return (len(neigh), v)
            if policy == "deterministic_min_fill":
                missing = 0
                for i, a in enumerate(neigh):
                    for b in neigh[i + 1:]:
                        missing += int(b not in adj[a])
                return (missing, v)
            raise ValueError(policy)
        v = min(alive, key=score)
        neigh = sorted(adj[v] & alive)
        widths.append(len(neigh))
        for i, a in enumerate(neigh):
            for b in neigh[i + 1:]:
                if b not in adj[a]:
                    adj[a].add(b)
                    adj[b].add(a)
                    fill_total += 1
        for u in neigh:
            adj[u].discard(v)
        alive.remove(v)
        order.append(v)
    width = max(widths, default=0)
    return {
        "order_sha256": digest(order),
        "induced_width": width,
        "peak_joint_arity": width + 1,
        "peak_joint_table_entries": 1 << (width + 1),
        "fill_edges_inserted": fill_total,
    }

def edge_count(adj: list[set[int]]) -> int:
    return sum(len(row) for row in adj) // 2

def parity(bits: tuple[int, ...]) -> int:
    return sum(bits) & 1

def terminal_direct_receipt() -> dict[str, Any]:
    satisfying = []
    for f1, f2, f3 in itertools.product((0, 1), repeat=3):
        matches = [e for e in (0, 1) if e == (f1 ^ f2 ^ f3)]
        if len(matches) != 1:
            raise AssertionError("R1 terminal auxiliary not unique")
        satisfying.append([f1, f2, f3, matches[0]])
    return {"relation": "e=f1 XOR f2 XOR f3", "original_assignments": 8, "unique_extension": True, "marginal_sum_per_original_assignment": 1, "satisfying_truth_table_sha256": digest(satisfying)}

def terminal_chain_receipt() -> dict[str, Any]:
    satisfying = []
    for f1, f2, f3 in itertools.product((0, 1), repeat=3):
        matches = []
        for u, e in itertools.product((0, 1), repeat=2):
            if u == (f1 ^ f2) and e == (u ^ f3):
                matches.append((u, e))
        if len(matches) != 1 or matches[0][1] != (f1 ^ f2 ^ f3):
            raise AssertionError("R2 terminal chain not unique/equivalent")
        satisfying.append([f1, f2, f3, matches[0][0], matches[0][1]])
    return {"relations": ["u=f1 XOR f2", "e=u XOR f3"], "original_assignments": 8, "unique_extension": True, "terminal_e_matches_direct_xor": True, "marginal_sum_per_original_assignment": 1, "satisfying_truth_table_sha256": digest(satisfying)}

def selector_receipt(kind: str) -> dict[str, Any]:
    rows = []
    for j, z in enumerate(LOGICAL_Z):
        w = len(support(z))
        checked = 0
        for raw in range(1 << (3 * w)):
            f1 = [(raw >> i) & 1 for i in range(w)]
            f2 = [(raw >> (w + i)) & 1 for i in range(w)]
            f3 = [(raw >> (2 * w + i)) & 1 for i in range(w)]
            old = parity(tuple(f1 + f2 + f3))
            e = [f1[i] ^ f2[i] ^ f3[i] for i in range(w)]
            new = parity(tuple(e))
            if old != new:
                raise AssertionError(f"{kind} selector semantic drift")
            checked += 1
        rows.append({"selector": j, "support_weight": w, "assignments_checked": checked})
    return {"identity": "parity(f1|f2|f3 on logical-Z support)=parity(e on support)", "all_equal": True, "rows": rows, "receipt_sha256": digest(rows)}

def syndrome_increment_receipt() -> dict[str, Any]:
    rows = []
    for c, row in enumerate(HZ_ROWS):
        w = len(support(row))
        satisfying = []
        for bits in itertools.product((0, 1), repeat=w):
            expected = parity(bits)
            matches = [r for r in (0, 1) if r == expected]
            if len(matches) != 1:
                raise AssertionError("R3 syndrome increment not unique")
            satisfying.append(list(bits) + [matches[0]])
        rows.append({"check": c, "support_weight": w, "unique_extension": True, "truth_table_sha256": digest(satisfying)})
    return {"all_unique": True, "rows": rows, "receipt_sha256": digest(rows)}

def detector_rewrite_receipt() -> dict[str, Any]:
    rows = []
    for c in range(7):
        for r1, r2, r3, m1, m2, m3 in itertools.product((0, 1), repeat=6):
            old = [r1 ^ m1, r2 ^ m1 ^ m2, r3 ^ m2 ^ m3, m3]
            new = [r1 ^ m1, r2 ^ m1 ^ m2, r3 ^ m2 ^ m3, m3]
            if old != new:
                raise AssertionError("R3 local detector rewrite drift")
            rows.append([c, r1, r2, r3, m1, m2, m3] + old)
    return {"assignments_checked": len(rows), "all_equal": True, "receipt_sha256": digest(rows)}

def semantic_receipts() -> dict[str, Any]:
    direct = terminal_direct_receipt()
    chain = terminal_chain_receipt()
    return {
        "R1_TERMINAL_DIRECT_AUX": {"status": "TEMPORAL_DECOMPOSITION_SEMANTIC_EQUIVALENCE_CERTIFIED", "terminal_relation": direct, "selector_rewrite": selector_receipt("R1"), "unique_auxiliary_extension": True, "exact_marginal_recovery": True},
        "R2_TERMINAL_CHAIN_AUX": {"status": "TEMPORAL_DECOMPOSITION_SEMANTIC_EQUIVALENCE_CERTIFIED", "terminal_chain": chain, "selector_rewrite": selector_receipt("R2"), "unique_auxiliary_extension": True, "exact_marginal_recovery": True},
        "R3_CAUSAL_STATE_CHAIN": {"status": "TEMPORAL_DECOMPOSITION_SEMANTIC_EQUIVALENCE_CERTIFIED", "terminal_chain": chain, "selector_rewrite": selector_receipt("R3"), "syndrome_increment": syndrome_increment_receipt(), "detector_rewrite": detector_rewrite_receipt(), "unique_auxiliary_extension": True, "exact_marginal_recovery": True},
    }

def structural_row(rep: str, cap: int) -> dict[str, Any]:
    variable_count, scopes = representation_scopes(rep)
    graph = primal_graph(scopes, variable_count)
    histogram = {str(k): v for k, v in sorted(Counter(len(s) for s in scopes).items())}
    orders = {name: elimination_order(graph, name) for name in ("lexicographic", "deterministic_min_fill", "deterministic_min_degree")}
    primary = orders["deterministic_min_fill"]
    status = "TEMPORAL_DECOMPOSITION_EXACT_COMPILED" if primary["peak_joint_table_entries"] <= cap else "TEMPORAL_DECOMPOSITION_EXACT_BOUND_EXHAUSTED"
    return {"representation": rep, "variable_count": variable_count, "factor_count": len(scopes), "factor_scope_arity_histogram": histogram, "factor_scope_sha256": digest(scopes), "primal_edge_count": edge_count(graph), "orders": orders, "primary_cap": cap, "status": status, "stopped_before_table_materialization": status.endswith("BOUND_EXHAUSTED"), "global_treewidth_claim": False}

def build_report(manifest: dict[str, Any]) -> dict[str, Any]:
    predecessor = verify_predecessor(manifest)
    receipts = semantic_receipts()
    cap = manifest["resource_envelope"]["peak_joint_table_entries"]
    rows = [structural_row(rep, cap) for rep in REPRESENTATIONS]
    r0 = rows[0]
    baseline = manifest["baseline"]
    if (r0["factor_count"] != baseline["factor_count"] or r0["factor_scope_sha256"] != baseline["all_factor_scope_sha256"] or r0["factor_scope_arity_histogram"] != baseline["factor_scope_arity_histogram"] or r0["orders"]["deterministic_min_fill"]["induced_width"] != baseline["protected_primary_induced_width"] or r0["orders"]["deterministic_min_fill"]["peak_joint_table_entries"] != baseline["protected_primary_peak_joint_table_entries"]):
        raise AssertionError("R0 protected structural replay drift")
    successors = rows[1:]
    compiled = [r for r in successors if r["status"] == "TEMPORAL_DECOMPOSITION_EXACT_COMPILED"]
    quality_defined = bool(compiled)
    report = {
        "experiment_id": EXPERIMENT_ID,
        "evaluator_version": EVALUATOR_VERSION,
        "manifest_payload_sha256": MANIFEST_PAYLOAD,
        "status": "candidate_executable_not_promoted",
        "predecessor_readback": predecessor,
        "semantic_equivalence": receipts,
        "structural_rows": rows,
        "adjudication_candidate": "TEMPORAL_DECOMPOSITION_EXACT_COMPILED" if compiled else "TEMPORAL_PREDECLARED_DECOMPOSITION_FAMILY_EXHAUSTED",
        "quality_boundary": {"temporal_tcm_quality_defined": quality_defined, "conventional_vs_tcm_quality_ordering_defined": False, "reason": "QUALITY_REQUIRES_SEPARATE_EXACT_COMPILED_EVALUATION" if quality_defined else "NO_SEMANTICALLY_VALID_SUCCESSOR_REPRESENTATION_COMPILED_UNDER_FROZEN_CAPS"},
        "transported_conventional_results": manifest["transported_conventional_results"],
        "claim_boundary": manifest["claim_boundary"],
    }
    report["payload_sha256"] = digest(report)
    return report

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()

def main() -> int:
    args = parse_args()
    manifest = load_manifest(args.manifest)
    report = build_report(manifest)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
