#!/usr/bin/env python3
"""QTR-C72-COMMON-GRAPH-001: common-policy, source-bound C72 structural audit.

This computes two primal graphs from *one* protected 36x72 X-check matrix:
full 36 generator coefficients and protected rank-30 independent basis.
One physical qubit generates one parity-factor scope. Both graphs use the
same declared structural elimination algorithms. This does not run,
reconstruct, or certify another research team's executable decoder.

Run from a full QTR checkout:
    python3 publication/research/qtr_c72_common_graph_001.py --output /tmp/c72-graph-audit.json

This is an exact finite structural calculation, not decoder evaluation.
"""
from __future__ import annotations

import argparse
from collections import Counter
import itertools
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reference"))

from qldpc_scale_001a_math import construct_code, matrix_record, rank_rref
from qldpc_scale_001a_shared import EXPECTED_DIGESTS, digest

CODE_SOURCE_MAIN = "aa2b293545eb3248d1482728808526d247a81c29"
EXPECT_HX_SHA = "6c01bd1eceb703a1afbd9897c9ce3810d951bc0d1284588607775e9f875740f2"
EXPECTED_X_BASIS = list(range(28)) + [30,31]
ALGORITHMS = ("lexicographic","min_degree","min_fill")
EXPECTED_WIDTHS = {
    "all_36_check_coefficients": {"lexicographic":30,"min_degree":26,"min_fill":23},
    "independent_30_stabilizers": {"lexicographic":24,"min_degree":18,"min_fill":18},
}


def scopes_from_rows(rows: list[int], n_qubits: int=72) -> list[tuple[int,...]]:
    return [tuple(j for j, row in enumerate(rows) if row & (1 << q))
            for q in range(n_qubits)]


def primal(scopes: list[tuple[int,...]], nvars: int) -> dict[int,set[int]]:
    neighbors = {i: set() for i in range(nvars)}
    for scope in scopes:
        if len(scope) != len(set(scope)):
            raise ValueError("duplicate variable within one factor scope")
        for i,j in itertools.combinations(scope,2):
            if i>=nvars or j>=nvars or i<0 or j<0:
                raise ValueError("factor variable out of graph range")
            neighbors[i].add(j);neighbors[j].add(i)
    for i,s in neighbors.items():
        if i in s: raise AssertionError("self loop")
    return neighbors


def eliminate(graph:dict[int,set[int]], policy:str) -> dict:
    if policy not in ALGORITHMS: raise ValueError("unknown policy")
    g = {v:set(ns) for v,ns in graph.items()}
    width = 0
    order:list[int] = []
    fill_count = 0
    trace:list[dict] = []
    while g:
        def key(v: int) -> tuple:
            if policy == "lexicographic": return (v,)
            nb = sorted(g[v])
            if policy == "min_degree":return (len(nb),v)
            fill = sum(int(b not in g[a]) for a,b in itertools.combinations(nb,2))
            # Explicit common tie-breaking: missing edges; degree; index
            return (fill,len(nb),v)
        v = min(g,key=key)
        nb = sorted(g.pop(v))
        width = max(width,len(nb))
        local_fill = 0
        for a in nb:g[a].remove(v)
        for a,b in itertools.combinations(nb,2):
            if b not in g[a]:
                g[a].add(b);g[b].add(a);local_fill += 1
        fill_count += local_fill
        order.append(v)
        trace.append({"variable":v,"neighbors_at_elimination":len(nb),
                      "fill_edges_added":local_fill})
    if sorted(order) != sorted(graph):raise AssertionError("incomplete ordering")
    return {"policy":policy,"induced_width":width,
            "peak_joint_assignments":1 << (width+1),
            "filled_edges_added":fill_count,
            "order":order,
            "trace_sha256":digest(trace)}


def compute() -> dict:
    code = construct_code()
    hx = code["hx"]
    if len(hx) != 36 or rank_rref(hx,72)[0]!=30:
        raise ValueError("protected C72 HX rank drift")
    if code["x_indices"] != EXPECTED_X_BASIS:
        raise ValueError("protected independent basis indices drift")
    hx_sha = digest(matrix_record(hx,72))
    if hx_sha != EXPECT_HX_SHA or hx_sha != EXPECTED_DIGESTS["hx"]:
        raise ValueError("source-bound HX digest drift")
    independent = [hx[index] for index in code["x_indices"]]
    if rank_rref(independent,72)[0] != 30:
        raise AssertionError("independent rowspace basis invalid")
    if any(rank_rref(independent+[v],72)[0] != 30 for v in hx):
        raise AssertionError("full check rowspace not spanned")

    groups = {
        "all_36_check_coefficients":(hx,36),
        "independent_30_stabilizers":(independent,30),
    }
    outputs={}
    for key,(rows,n) in groups.items():
        scopes = scopes_from_rows(rows)
        g = primal(scopes,n)
        report={
            "variables":n,
            "physical_factors":len(scopes),
            "factor_scope_arity_histogram":{str(k):v for k,v in sorted(Counter(map(len,scopes)).items())},
            "factor_scopes_sha256":digest([list(scope) for scope in scopes]),
            "primal_edges":sum(len(x) for x in g.values())//2,
            "initial_max_factor_arity":max(map(len,scopes)),
            "orders":{a:eliminate(g,a) for a in ALGORITHMS},
        }
        actual={a:report["orders"][a]["induced_width"] for a in ALGORITHMS}
        if actual != EXPECTED_WIDTHS[key]:
            raise ValueError("unexpected structural widths "+str((key,actual)))
        outputs[key]=report

    # This known protected conclusion is cross-checked, but its reported
    # min-fill tie ordering need not equal our explicitly declared policy.
    protected = json.loads((ROOT/"evidence/QLDPC-SCALE-001A-report.json").read_text())
    if protected["payload_sha256"]!="198bb28f47844aa98efa20d8c838c48870a8aef41ccfda266b16661677e363e1":
        raise ValueError("protected QLDPC report payload drift")
    if protected["elimination_order_audit"]["induced_width"] != EXPECTED_WIDTHS["independent_30_stabilizers"]:
        raise ValueError("protected QLDPC independent widths drift")

    report={
        "record_type":"QTR_C72_COMMON_GRAPH_AUDIT/1",
        "status":"SOURCE_BOUND_BOUNDED_STRUCTURAL_RECONSTRUCTION__NO_COMPARATOR_IMPLEMENTATION_AUDIT",
        "source_qtr_protected_main":CODE_SOURCE_MAIN,
        "code_hx_sha256":hx_sha,
        "declarations":{
            "physical_qubits":72,
            "graphs":"one binary latent per declared X check vs one per independent X stabilizer",
            "qubit_factors":"one parity-factor per physical qubit; latent variable scope is row support at that qubit",
            "primal_graph":"join distinct latent variables co-occurring in a factor",
            "induced_width":"maximum live-neighbor count before elimination",
            "lexicographic":"lowest live index",
            "min_degree":"lowest live degree, then index",
            "min_fill":"fewest missing edges among live neighbors, then degree, then index",
        },
        "full_check_kernel_dimension":6,
        "full_check_coefficient_multiplicity":64,
        "independent_row_indices":code["x_indices"],
        "graphs":outputs,
        "qualification":[
            "Same source matrix and deterministic algorithms are applied to both reconstructions.",
            "The independently selected 30-variable primal graph matches the protected width summary, but a different tie-break policy can change the exact elimination order.",
            "This is structural information only. It does not establish a direct shared-runtime benchmark, globally minimal treewidth, or superiority of one decoder implementation.",
            "The 36-variable graph models the paper's described one-check-variable-per-row coset factorization, but does not inspect or execute the comparator's source code.",
            "The ordinary sum-product class score of the redundant 36-variable model must be divided by 64 before comparing with a rank-30 independent-basis class partition; min-plus minima are unchanged.",
        ],
    }
    report["canonical_report_sha256"] = digest({k:v for k,v in report.items()})
    return report


def main() -> int:
    cli = argparse.ArgumentParser()
    cli.add_argument("--output",type=Path,required=True)
    args = cli.parse_args()
    data = compute()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,sort_keys=True,indent=2)+"\n")
    print("C72_COMMON_POLICY_GRAPH_AUDIT_PASS")
    for key,v in data["graphs"].items():
        print(key,"edges",v["primal_edges"],"widths",
              {k:v["orders"][k]["induced_width"] for k in ALGORITHMS})
    print("CANONICAL_REPORT_SHA256",data["canonical_report_sha256"])
    return 0


if __name__=="__main__":
    raise SystemExit(main())
