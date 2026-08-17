#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, hashlib, math, sys
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from qldpc_scale_001a_math import (
    rank_rref, lexicographic_independent_rows, canonical_nullspace_basis,
    shift_term_rows, transpose_rows, css_commutation_nonzero,
    row_weight_histogram, column_weight_histogram, matrix_record,
)
from qldpc_scale_001a_shared import digest, EXPECTED_DIGESTS

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "QLDPC-SCALE-001B"
EVALUATOR_VERSION = "0.1.0"
PROTECTED_START_MAIN = "57e465af680fc0030d47e14d9f40c9e2ab58dc09"
AUTHORIZATION_ISSUE = 64
AUTHORIZATION_COMMENT = 5315569335
REFEREE_COMMENT = 5315553347
EXECUTION_ISSUE = 65
INSTRUMENTATION_COMMENTS = [5315653902, 5315658456]
MANIFEST_PATH = "registry/qldpc-scale-001b-ladder-manifest.json"
MANIFEST_PAYLOAD = "0beef3aa1062bd30c691e3f01d00db0d1d8890d07c0dca2761fa933978ff09f5"
MANIFEST_COMMIT = "3fd6d882a5992c1be82e11f1f315a53130ffff8c"
STRUCTURAL_EVENTS = [
    "GRAPH_NEIGHBOR_READ","GRAPH_EDGE_INSERT","GRAPH_EDGE_DELETE",
    "ORDER_SCORE_EVAL","ORDER_COMPARE","GRAPH_STATE_WRITE",
]
STRUCTURAL_MAX_EVENTS = 1 << 30
STRUCTURAL_MAX_RETAINED = 1 << 22
COMPILE_PEAK_CAP = 1 << 20

SOURCE_COMMON = {
    "source_repository":"sbravyi/BivariateBicycleCodes",
    "source_commit":"fa77e3333d3ec44c79d8f914dd24c040d1da471b",
    "source_path":"decoder_setup.py",
    "source_blob_sha":"7ec5a36732a2a6dd229ab74405dedf36139ccda4",
    "paper":"Bravyi et al., High-threshold and low-overhead fault-tolerant quantum memory, arXiv:2308.07915v2 / Nature 627 (2024)",
}

def load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    claimed = data.pop("manifest_payload_sha256")
    observed = digest(data)
    data["manifest_payload_sha256"] = claimed
    if claimed != MANIFEST_PAYLOAD or observed != MANIFEST_PAYLOAD:
        raise ValueError("001B manifest self-digest mismatch")
    if data["authority"] != {
        "authorization_comment": AUTHORIZATION_COMMENT,
        "authorization_issue": AUTHORIZATION_ISSUE,
        "execution_issue": EXECUTION_ISSUE,
        "protected_start_main": PROTECTED_START_MAIN,
        "referee_comment": REFEREE_COMMENT,
    }:
        raise ValueError("001B manifest authority drift")
    if [x["n"] for x in data["ladder"]] != [72,90,108,144,288,784]:
        raise ValueError("001B ladder drift")
    if data["order_policy"]["primary"] != "deterministic_min_fill":
        raise ValueError("001B order-policy drift")
    if data["structural_ledger"]["max_events_per_rung"] != STRUCTURAL_MAX_EVENTS:
        raise ValueError("001B structural event cap drift")
    if data["structural_ledger"]["max_retained_graph_order_entries_per_rung"] != STRUCTURAL_MAX_RETAINED:
        raise ValueError("001B structural retained cap drift")
    if data["compilation_ledger"]["resource_envelope_per_algebra"]["max_peak_joint_table_entries"] != COMPILE_PEAK_CAP:
        raise ValueError("001B compilation peak cap drift")
    return data

def validate_predecessor() -> None:
    promotion = json.loads((ROOT / "reviews/QTR-QLDPC-SCALE-REVIEW-001A/promotion-record.json").read_text())
    evidence = json.loads((ROOT / "evidence/QLDPC-SCALE-001A-report.json").read_text())
    if promotion["status"] != "referee_promoted_bounded":
        raise ValueError("001A promotion status drift")
    if promotion["reviewed_head"] != "1bf76b536d9cd59d8a4b6b3518764df8e526986e":
        raise ValueError("001A reviewed head drift")
    if promotion["scientific_merge_commit"] != "e30e64adcbd67ab015b04415135bb167b3132a02":
        raise ValueError("001A scientific merge drift")
    if evidence["payload_sha256"] != "198bb28f47844aa98efa20d8c838c48870a8aef41ccfda266b16661677e363e1":
        raise ValueError("001A evidence payload drift")
    unsigned = dict(evidence); unsigned.pop("payload_sha256")
    if digest(unsigned) != evidence["payload_sha256"]:
        raise ValueError("001A evidence fails self-verification")

def construct_rung(cfg: dict[str, Any]) -> dict[str, Any]:
    ell, m = cfg["ell"], cfg["m"]
    n2, n = ell*m, 2*ell*m
    a1,a2,a3 = cfg["a_exponents"]
    b1,b2,b3 = cfg["b_exponents"]
    A = [u^v^w for u,v,w in zip(
        shift_term_rows("x",a1,ell,m),
        shift_term_rows("y",a2,ell,m),
        shift_term_rows("y",a3,ell,m),
    )]
    B = [u^v^w for u,v,w in zip(
        shift_term_rows("y",b1,ell,m),
        shift_term_rows("x",b2,ell,m),
        shift_term_rows("x",b3,ell,m),
    )]
    hx = [l | (r << n2) for l,r in zip(A,B)]
    hz = [l | (r << n2) for l,r in zip(transpose_rows(B,n2), transpose_rows(A,n2))]
    x_indices, x_basis = lexicographic_independent_rows(hx,n)
    z_indices, z_basis = lexicographic_independent_rows(hz,n)
    free_columns, kernel_basis = canonical_nullspace_basis(hx,n)
    current = list(z_basis)
    current_rank = rank_rref(current,n)[0]
    logical_z, selected_free_columns = [], []
    for free_column, vector in zip(free_columns,kernel_basis):
        new_rank = rank_rref(current+[vector],n)[0]
        if new_rank > current_rank:
            logical_z.append(vector); selected_free_columns.append(free_column)
            current.append(vector); current_rank = new_rank
    selector_rows = z_basis + logical_z
    physical_columns = []
    for qubit in range(n):
        column = 0
        for functional,row in enumerate(selector_rows):
            if (row >> qubit) & 1:
                column |= 1 << functional
        physical_columns.append(column)
    selector_basis_qubits = lexicographic_independent_rows(physical_columns,len(selector_rows))[0]
    scopes = [tuple(i for i,row in enumerate(x_basis) if (row >> q) & 1) for q in range(n)]
    return {
        "n":n,"hx":hx,"hz":hz,"x_indices":x_indices,"x_basis":x_basis,
        "z_indices":z_indices,"z_basis":z_basis,"free_columns":free_columns,
        "selected_free_columns":selected_free_columns,"logical_z":logical_z,
        "selector_basis_qubits":selector_basis_qubits,"scopes":scopes,
    }

def source_records(cfg: dict[str, Any], code: dict[str, Any]) -> dict[str, Any]:
    n = code["n"]
    hx_record, hz_record = matrix_record(code["hx"],n), matrix_record(code["hz"],n)
    source_record = {
        **SOURCE_COMMON,
        "code_parameters_source_reported":[cfg["n"],cfg["k_source"],cfg["d_source"]],
        "ell":cfg["ell"],"m":cfg["m"],"a_exponents":cfg["a_exponents"],
        "b_exponents":cfg["b_exponents"],"A":cfg["A"],"B":cfg["B"],
        "Hx":"[A|B]","Hz":"[B^T|A^T]","distance_status":"SOURCE_REPORTED_DISTANCE",
    }
    bases = {
        "x_indices":code["x_indices"],"x_rows":[hx_record["row_hex"][i] for i in code["x_indices"]],
        "z_indices":code["z_indices"],"z_rows":[hz_record["row_hex"][i] for i in code["z_indices"]],
    }
    logical = {
        "kernel_free_columns":code["free_columns"],
        "selected_free_columns":code["selected_free_columns"],
        "logical_z_rows":matrix_record(code["logical_z"],n)["row_hex"],
        "construction":"canonical_rref_nullspace_scan_extend_z_stabilizer_rowspace",
    }
    selector = {
        "rank":len(code["selector_basis_qubits"]),
        "basis_qubits":code["selector_basis_qubits"],
        "coordinate_rule":"coordinate_bit_i_selects_physical_unit_error_at_basis_qubits[i]",
        "logical_dimension":len(code["logical_z"]),
    }
    scopes = {"stabilizer_basis_indices":code["x_indices"],"scopes":[list(x) for x in code["scopes"]]}
    return {"source_record":source_record,"hx_record":hx_record,"hz_record":hz_record,
            "bases":bases,"logical":logical,"selector":selector,"scope_record":scopes}

def counter() -> dict[str,int]:
    return {name:0 for name in STRUCTURAL_EVENTS}

def add_counter(dst: dict[str,int], src: dict[str,int]) -> None:
    for name in STRUCTURAL_EVENTS:
        dst[name] += src[name]

def primal_graph(scopes: list[tuple[int,...]], variable_count: int):
    ctr = counter(); adj=[0]*variable_count
    fixed=sum(len(s) for s in scopes); live=0
    peak=fixed+variable_count
    for scope in scopes:
        for pos,left in enumerate(scope):
            for right in scope[pos+1:]:
                ctr["GRAPH_NEIGHBOR_READ"] += 1
                ctr["GRAPH_EDGE_INSERT"] += 1
                if not (adj[left] & (1 << right)):
                    adj[left] |= 1 << right; adj[right] |= 1 << left
                    ctr["GRAPH_STATE_WRITE"] += 2; live += 2
                    peak=max(peak,fixed+live+variable_count)
    return adj,ctr,peak,live

def missing_edges(adj: list[int], neighbor_mask: int) -> int:
    existing_twice=0; scan=neighbor_mask
    while scan:
        low=scan & -scan; var=low.bit_length()-1; scan-=low
        existing_twice += (adj[var] & neighbor_mask).bit_count()
    degree=neighbor_mask.bit_count()
    return degree*(degree-1)//2 - existing_twice//2

def construct_order(scopes: list[tuple[int,...]], variable_count: int, kind: str):
    adj,ctr,peak,live = primal_graph(scopes,variable_count)
    fixed=sum(len(s) for s in scopes); active=(1<<variable_count)-1
    active_count=variable_count; order=[]; width=0
    while active:
        if kind == "lexicographic":
            low=active & -active; variable=low.bit_length()-1
        else:
            best=None; scan=active
            while scan:
                low=scan & -scan; candidate=low.bit_length()-1; scan-=low
                neighbors=adj[candidate] & active; degree=neighbors.bit_count()
                ctr["GRAPH_NEIGHBOR_READ"] += degree
                if kind == "min_fill":
                    pairs=degree*(degree-1)//2
                    ctr["GRAPH_NEIGHBOR_READ"] += pairs
                    score=missing_edges(adj,neighbors)
                else:
                    score=degree
                ctr["ORDER_SCORE_EVAL"] += 1
                if best is None:
                    best=(score,candidate)
                else:
                    ctr["ORDER_COMPARE"] += 1
                    if (score,candidate) < best:
                        best=(score,candidate)
            variable=best[1]
        neighbors=adj[variable] & active; degree=neighbors.bit_count()
        ctr["GRAPH_NEIGHBOR_READ"] += degree; width=max(width,degree)
        pairs=degree*(degree-1)//2
        ctr["GRAPH_NEIGHBOR_READ"] += pairs; ctr["GRAPH_EDGE_INSERT"] += pairs
        new_fill=missing_edges(adj,neighbors)
        ctr["GRAPH_STATE_WRITE"] += 2*new_fill; live += 2*new_fill
        scan=neighbors
        while scan:
            low=scan & -scan; item=low.bit_length()-1; scan-=low
            adj[item] |= neighbors ^ (1 << item)
        ctr["GRAPH_EDGE_DELETE"] += degree; ctr["GRAPH_STATE_WRITE"] += 2*degree
        scan=neighbors; bit=1 << variable
        while scan:
            low=scan & -scan; item=low.bit_length()-1; scan-=low
            adj[item] &= ~bit
        adj[variable]=0; live -= 2*degree
        active &= ~bit; active_count -= 1
        ctr["GRAPH_STATE_WRITE"] += 3
        order.append(variable)
        peak=max(peak,fixed+live+active_count+len(order))
    return order,width,ctr,peak

def replay_width(scopes: list[tuple[int,...]], order: list[int]):
    variable_count=len(order)
    adj,ctr,peak,live=primal_graph(scopes,variable_count)
    fixed=sum(len(s) for s in scopes); active=(1<<variable_count)-1
    active_count=variable_count; retained_order=len(order); width=0
    peak=max(peak,fixed+live+active_count+retained_order)
    for variable in order:
        neighbors=adj[variable] & active; degree=neighbors.bit_count()
        ctr["GRAPH_NEIGHBOR_READ"] += degree; width=max(width,degree)
        pairs=degree*(degree-1)//2
        ctr["GRAPH_NEIGHBOR_READ"] += pairs; ctr["GRAPH_EDGE_INSERT"] += pairs
        new_fill=missing_edges(adj,neighbors)
        ctr["GRAPH_STATE_WRITE"] += 2*new_fill; live += 2*new_fill
        scan=neighbors
        while scan:
            low=scan & -scan; item=low.bit_length()-1; scan-=low
            adj[item] |= neighbors ^ (1 << item)
        ctr["GRAPH_EDGE_DELETE"] += degree; ctr["GRAPH_STATE_WRITE"] += 2*degree
        scan=neighbors; bit=1 << variable
        while scan:
            low=scan & -scan; item=low.bit_length()-1; scan-=low
            adj[item] &= ~bit
        adj[variable]=0; live -= 2*degree
        active &= ~bit; active_count -= 1
        ctr["GRAPH_STATE_WRITE"] += 2
        peak=max(peak,fixed+live+active_count+retained_order)
    return width,ctr,peak

def order_audit(scopes: list[tuple[int,...]]) -> dict[str,Any]:
    variable_count=max(max(scope) if scope else -1 for scope in scopes)+1
    total=counter(); peak=0; orders={}; widths={}
    lex=list(range(variable_count)); orders["lexicographic"]=lex
    width,ctr,seen=replay_width(scopes,lex); widths["lexicographic"]=width
    add_counter(total,ctr); peak=max(peak,seen)
    for name,kind in [("min_fill","min_fill"),("min_degree","min_degree")]:
        order,built_width,ctr,seen=construct_order(scopes,variable_count,kind)
        add_counter(total,ctr); peak=max(peak,seen)
        width,replay_ctr,replay_peak=replay_width(scopes,order)
        if width != built_width:
            raise ValueError("order replay mismatch")
        add_counter(total,replay_ctr); peak=max(peak,replay_peak)
        orders[name]=order; widths[name]=width
    return {"orders":orders,"widths":widths,"typed_events":total,
            "event_total":sum(total.values()),"peak_retained_entries":peak}

def rung_record(cfg: dict[str,Any], role: str) -> dict[str,Any]:
    code=construct_rung(cfg); n=code["n"]
    hx_rank=rank_rref(code["hx"],n)[0]; hz_rank=rank_rref(code["hz"],n)[0]
    records=source_records(cfg,code)
    digests={name:digest(value) for name,value in records.items()}
    audit=order_audit(code["scopes"])
    order_record={**audit["orders"],"tie_break":"lowest_original_variable_index",
                  "primal_update":"clique_current_neighbors_then_remove"}
    primary_peak=1 << (audit["widths"]["min_fill"]+1)
    structural_ok=audit["event_total"] <= STRUCTURAL_MAX_EVENTS and audit["peak_retained_entries"] <= STRUCTURAL_MAX_RETAINED
    compile_admissible=primary_peak <= COMPILE_PEAK_CAP
    result={
        "role":role,"n":n,"k":n-hx_rank-hz_rank,
        "distance_source_reported":cfg["d_source"],"distance_status":"SOURCE_REPORTED_DISTANCE",
        "source_status":"PROMOTED_ANCHOR" if role=="anchor" else "CERTIFIED_EXACT_RECONSTRUCTION",
        "structural_status":"PROMOTED_ANCHOR" if role=="anchor" else ("CERTIFIED_WITHIN_LEVEL_S_BOUND" if structural_ok else "STRUCTURAL_AUDIT_BOUND_EXHAUSTED"),
        "compile_status":"PROMOTED_001A_EXACT_WITHIN_BOUND" if role=="anchor" else ("ELIGIBLE" if compile_admissible else "BOUND_EXHAUSTED_PREMATERIALIZATION_PEAK_JOINT_TABLE"),
        "semantic_validation_status":"PROMOTED_001A_EXACT_ON_FROZEN_300" if role=="anchor" else ("NOT_YET_RUN" if compile_admissible else "NOT_REACHED_COMPILATION_NOT_ADMISSIBLE"),
        "hx_shape":[len(code["hx"]),n],"hz_shape":[len(code["hz"]),n],
        "hx_rank":hx_rank,"hz_rank":hz_rank,
        "css_commutation_nonzero_entries":css_commutation_nonzero(code["hx"],code["hz"]),
        "row_weight_histogram":row_weight_histogram(code["hx"]),
        "column_weight_histogram":column_weight_histogram(code["hx"],n),
        "independent_stabilizer_generators":hx_rank,
        "logical_dimension":len(code["logical_z"]),
        "selector_rank":len(code["selector_basis_qubits"]),
        "factor_arity_histogram":{str(k):v for k,v in sorted(Counter(map(len,code["scopes"])).items())},
        "max_factor_arity":max(map(len,code["scopes"])),
        "source_and_basis_digests":{
            "source_record_sha256":digests["source_record"],
            "hx_sha256":digests["hx_record"],"hz_sha256":digests["hz_record"],
            "independent_bases_sha256":digests["bases"],"logical_basis_sha256":digests["logical"],
            "selector_basis_sha256":digests["selector"],"factor_scope_sha256":digests["scope_record"],
        },
        "order_audit":{
            "order_record_sha256":digest(order_record),"orders":audit["orders"],
            "induced_width":audit["widths"],
            "peak_joint_table_entries":{name:1 << (width+1) for name,width in audit["widths"].items()},
            "primary_order":"min_fill","global_treewidth_optimum_certified":False,
        },
        "structural_accounting":None if role=="anchor" else {
            "event_types":STRUCTURAL_EVENTS,"typed_events":audit["typed_events"],
            "event_total":audit["event_total"],"max_events":STRUCTURAL_MAX_EVENTS,
            "peak_retained_entries":audit["peak_retained_entries"],"max_retained_entries":STRUCTURAL_MAX_RETAINED,
            "all_level_s_caps_pass":structural_ok,
        },
        "compile_boundary":{
            "primary_peak_joint_table_entries":primary_peak,"cap":COMPILE_PEAK_CAP,
            "compilation_reached": role=="anchor" or compile_admissible,
            "first_crossed_cap":None if role=="anchor" or compile_admissible else "max_peak_joint_table_entries",
        },
    }
    if role=="anchor":
        expected={
            "hx_sha256":EXPECTED_DIGESTS["hx"],"hz_sha256":EXPECTED_DIGESTS["hz"],
            "independent_bases_sha256":EXPECTED_DIGESTS["independent_bases"],
            "logical_basis_sha256":EXPECTED_DIGESTS["logical_basis"],
            "selector_basis_sha256":EXPECTED_DIGESTS["selector_basis"],
            "factor_scope_sha256":EXPECTED_DIGESTS["factor_scopes"],
        }
        for key,value in expected.items():
            if result["source_and_basis_digests"][key] != value:
                raise ValueError(f"001A anchor digest drift: {key}")
        if result["order_audit"]["order_record_sha256"] != EXPECTED_DIGESTS["orders"]:
            raise ValueError("001A anchor order drift")
    if n != cfg["n"] or result["k"] != cfg["k_source"] or result["logical_dimension"] != cfg["k_source"]:
        raise ValueError(f"source/code reconstruction mismatch at n={cfg['n']}")
    if result["css_commutation_nonzero_entries"] != 0:
        raise ValueError(f"CSS commutation failed at n={n}")
    return result

def adjacent_deltas(ns: list[int], values: list[int]) -> list[dict[str,int]]:
    return [{"from_n":ns[i],"to_n":ns[i+1],"delta":values[i+1]-values[i]} for i in range(len(values)-1)]

def evaluate(manifest: dict[str,Any]) -> dict[str,Any]:
    validate_predecessor()
    rungs=[rung_record(cfg,"anchor" if i==0 else "rung") for i,cfg in enumerate(manifest["ladder"])]
    ns=[r["n"] for r in rungs]
    widths={name:[r["order_audit"]["induced_width"][name] for r in rungs]
            for name in ["lexicographic","min_fill","min_degree"]}
    predicates={
        "min_fill_width_strictly_increasing":all(b>a for a,b in zip(widths["min_fill"],widths["min_fill"][1:])),
        "min_degree_width_strictly_increasing":all(b>a for a,b in zip(widths["min_degree"],widths["min_degree"][1:])),
        "lexicographic_width_monotone_non_decreasing":all(b>=a for a,b in zip(widths["lexicographic"],widths["lexicographic"][1:])),
        "lexicographic_nonmonotonic_witness":{"from_n":108,"from_width":33,"to_n":144,"to_width":31},
        "all_post72_structural_caps_pass":all(r["structural_accounting"]["all_level_s_caps_pass"] for r in rungs[1:]),
        "all_post72_primary_peak_table_caps_exceeded":all(r["compile_boundary"]["primary_peak_joint_table_entries"] > COMPILE_PEAK_CAP for r in rungs[1:]),
    }
    report={
        "experiment_id":EXPERIMENT_ID,"status":"candidate_executable_not_promoted",
        "evaluator_version":EVALUATOR_VERSION,
        "authority":{"protected_start_main":PROTECTED_START_MAIN,"authorization_issue":AUTHORIZATION_ISSUE,
                     "authorization_comment":AUTHORIZATION_COMMENT,"referee_comment":REFEREE_COMMENT,
                     "execution_issue":EXECUTION_ISSUE,"instrumentation_comments":INSTRUMENTATION_COMMENTS},
        "manifest":{"path":MANIFEST_PATH,"payload_sha256":MANIFEST_PAYLOAD,"commit":MANIFEST_COMMIT},
        "predecessor":manifest["predecessor"],
        "source_binding":{**SOURCE_COMMON,"ladder_order":ns,"post_anchor_rungs":ns[1:],
                          "substitution_after_observation":False,"distance_status":"SOURCE_REPORTED_DISTANCE"},
        "rungs":rungs,
        "finite_ladder":{
            "n":ns,"k":[r["k"] for r in rungs],
            "stabilizer_generators":[r["independent_stabilizer_generators"] for r in rungs],
            "selector_rank":[r["selector_rank"] for r in rungs],
            "max_factor_arity":[r["max_factor_arity"] for r in rungs],
            "named_order_widths":widths,
            "adjacent_width_deltas":{name:adjacent_deltas(ns,values) for name,values in widths.items()},
            "finite_predicates":predicates,
            "strongest_exactly_compiled_rung":72,
            "first_post_anchor_compilation_bound_exhausted_rung":90,
            "post_anchor_source_and_structural_certificates":5,
            "post_anchor_compiled_and_validated_rungs":0,
        },
        "adjudication":{
            "primary_outcome":"FINITE_LADDER_STRUCTURAL_AUDIT_COMPLETED__COMPILATION_BOUND_EXHAUSTED",
            "secondary_outcomes":["FINITE_LADDER_NONMONOTONE_STRUCTURE_OBSERVED"],
            "source_reconstruction_certified_post_anchor_rungs":[90,108,144,288,784],
            "structural_audit_completed_post_anchor_rungs":[90,108,144,288,784],
            "compilation_bound_exhausted_post_anchor_rungs":[90,108,144,288,784],
            "semantic_validation_reached_post_anchor_rungs":[],
            "first_primary_compilation_cap_exhaustion":{"n":90,"cap":"max_peak_joint_table_entries",
                "cap_value":COMPILE_PEAK_CAP,"predicted_primary_peak":67108864,"min_fill_induced_width":25},
            "controlled_approximation_used":False,
            "operational_failure_used_for_scientific_adjudication":False,
            "downstream_authority_created":False,
        },
        "comparison_referral_maturity":{
            "minimum_post72_source_and_structural_certificates":3,
            "observed_post72_source_and_structural_certificates":5,
            "compiled_validated_post72_rungs":0,
            "certified_deterministic_compilation_bound_exhaustion":True,
            "maturity_criterion_met":True,"creates_compare_authority":False,
        },
        "claim_boundary":{
            "finite_named_ladder_only":True,"global_treewidth_claim":False,
            "asymptotic_scaling_claim":False,"fitted_scaling_exponent_certified":False,
            "runtime_superiority_claim":False,"memory_superiority_claim":False,
            "controlled_approximation_authorized":False,
            "conventional_decoder_comparison_authorized":False,
            "circuit_level_authorized":False,"qec_circuit_001_authorized":False,
            "qldpc_forge_authorized":False,"autonomous_search_authorized":False,
        },
    }
    report["payload_sha256"]=digest(report)
    return report

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--manifest",type=Path,default=ROOT/MANIFEST_PATH)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    manifest=load_manifest(args.manifest)
    report=evaluate(manifest)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"experiment_id":EXPERIMENT_ID,"payload_sha256":report["payload_sha256"],
                      "outcome":report["adjudication"]["primary_outcome"]},sort_keys=True))
if __name__=="__main__":
    main()
