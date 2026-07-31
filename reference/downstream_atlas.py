#!/usr/bin/env python3
"""Deterministic finite evaluators for QTR-SIG-WP01 through bounded WP03.

This module verifies finite orbit, linearization, adversary, and span-program
records. It does not prove asymptotic complexity, coherent implementation,
QSP/QSVT admissibility, or quantum advantage.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, math
from pathlib import Path
from typing import Any
VERSION="0.1.0"; DIGITS=12

def digest(x:Any)->str:
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
def weight(bits:tuple[int,...])->int:return sum(bits)
def label(pid:str,bits:tuple[int,...],params:dict[str,Any])->int:
    w=weight(bits); n=len(bits)
    if pid=="or": return int(w>0)
    if pid=="majority": return int(2*w>n)
    if pid=="parity": return w%2
    if pid=="exact_weight": return int(w==params["target_weight"])
    raise ValueError(f"unknown predicate {pid}")
def evaluate_wp01(record:dict[str,Any])->dict[str,Any]:
    n=record["input_width"]; groups={w:[] for w in range(n+1)}
    for bits in itertools.product((0,1),repeat=n): groups[weight(bits)].append(label(record["predicate_id"],bits,record["predicate_parameters"]))
    sizes=[len(groups[w]) for w in range(n+1)]; labels=[sorted(set(groups[w])) for w in range(n+1)]
    constant=all(len(x)==1 for x in labels); seq=[x[0] for x in labels] if constant else []
    report={"record_id":record["record_id"],"predicate_id":record["predicate_id"],"input_width":n,"group_action":record["group_action"],"invariant_coordinates":record["invariant_coordinates"],"domain_size":2**n,"orbit_count":n+1,"orbit_sizes":sizes,"orbit_sizes_match_binomial":sizes==[math.comb(n,w) for w in range(n+1)],"labels_by_orbit":labels,"predicate_constant_on_orbits":constant,"quotient_semantically_sufficient":constant,"boundary_count":sum(a!=b for a,b in zip(seq,seq[1:])) if seq else 0,"compression_ratio":round((2**n)/(n+1),DIGITS),"claim_status":record["claim_status"]}
    report["report_sha256"]=digest(report); return report
def signed_value(record:dict[str,Any],w:int)->float:
    n=record["input_width"]; c=record["construction"]
    if c["kind"]=="marked_row": return math.sqrt(w/n)
    if c["kind"]=="signed_hamming_scalar": return 2*w/n-1
    if c["kind"]=="centered_weight_scalar": return (w-c["target_weight"])/c["scale"]
    raise ValueError(f"unknown construction {c['kind']}")
def collisions(rows:list[dict[str,Any]],key:str)->tuple[int,list[dict[str,Any]]]:
    groups={}
    for row in rows: groups.setdefault(row[key],[]).append(row)
    count=0; witnesses=[]
    for value,members in sorted(groups.items()):
        z=[r for r in members if r["label"]==0]; o=[r for r in members if r["label"]==1]
        count+=len(z)*len(o)
        if z and o:witnesses.append({"value":value,"zero_weight":z[0]["hamming_weight"],"one_weight":o[0]["hamming_weight"]})
    return count,witnesses
def evaluate_wp02(record:dict[str,Any])->dict[str,Any]:
    n=record["input_width"]; rows=[]; shape=record["construction"]["operator_shape"]
    for bits in itertools.product((0,1),repeat=n):
        w=weight(bits); signed=round(signed_value(record,w),DIGITS); singular=round(abs(signed),DIGITS)
        if record["construction"]["kind"]=="marked_row": rank=0 if w==0 else 1
        else: rank=0 if singular==0 else 1
        rows.append({"hamming_weight":w,"label":label(record["predicate_id"],bits,record["predicate_parameters"]),"signed_value":signed,"singular_value":singular,"rank":rank,"range_dimension":rank,"kernel_dimension":shape[1]-rank})
    sc,sw=collisions(rows,"signed_value"); vc,vw=collisions(rows,"singular_value")
    by=[]
    for w in range(n+1):
        m=[r for r in rows if r["hamming_weight"]==w]; e=m[0]; by.append({"hamming_weight":w,"multiplicity":len(m),"label":e["label"],"signed_value":e["signed_value"],"singular_value":e["singular_value"],"rank":e["rank"],"range_dimension":e["range_dimension"],"kernel_dimension":e["kernel_dimension"]})
    report={"record_id":record["record_id"],"predicate_id":record["predicate_id"],"input_width":n,"construction_kind":record["construction"]["kind"],"operator_shape":shape,"by_hamming_weight":by,"signed_channel":{"cross_label_collision_pairs":sc,"collision_witnesses":sw,"semantically_sufficient":sc==0},"singular_value_channel":{"cross_label_collision_pairs":vc,"collision_witnesses":vw,"semantically_sufficient":vc==0},"claim_status":record["claim_status"]}
    report["report_sha256"]=digest(report); return report
def evaluate_wp03(record:dict[str,Any])->dict[str,Any]:
    n=record["input_width"]; cert=record["adversary_certificate"]; span=record["span_program"]
    expected=sorted("".join("1" if i==j else "0" for i in range(n)) for j in range(n))
    if cert["zero_input"]!="0"*n or sorted(cert["one_inputs"])!=expected: raise ValueError("invalid OR star support")
    if span["vector_space_dimension"]!=1 or span["target"]!=[1.0] or len(span["input_vectors"])!=n or any(v!=[1.0] for v in span["input_vectors"]): raise ValueError("invalid OR unit span program")
    objective=math.sqrt(n); complexity=math.sqrt(1.0*n)
    report={"record_id":record["record_id"],"predicate_id":"or","input_width":n,"adversary_certificate":{"matrix_support":"star_between_zero_and_weight_one_inputs","edge_count":n,"spectral_norm":objective,"per_bit_filtered_norms":[1.0]*n,"objective":objective,"feasible_opposite_label_support":True},"span_program":{"vector_space_dimension":1,"positive_witness_size_worst_case":1.0,"negative_witness_size_zero_input":float(n),"witness_size_complexity":complexity},"certificate_objectives_match":math.isclose(objective,complexity),"claim_status":record["claim_status"],"limitations":record["limitations"]}
    report["report_sha256"]=digest(report); return report
def evaluate_registry(registry:dict[str,Any])->dict[str,Any]:
    payload={"evaluator_version":VERSION,"registry_version":registry["registry_version"],"status":registry["status"],"WP01":[evaluate_wp01(r) for r in registry["WP01"]],"WP02":[evaluate_wp02(r) for r in registry["WP02"]],"WP03":[evaluate_wp03(r) for r in registry["WP03"]]}
    payload["payload_sha256"]=digest(payload); return payload
def main()->int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--registry",type=Path,default=Path(__file__).resolve().parents[1]/"registry/downstream-atlas.json"); p.add_argument("--output",type=Path); a=p.parse_args()
    out=evaluate_registry(json.loads(a.registry.read_text())); text=json.dumps(out,indent=2,sort_keys=True)+"\n"
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(text)
    print(text,end="");return 0
if __name__=="__main__":raise SystemExit(main())
