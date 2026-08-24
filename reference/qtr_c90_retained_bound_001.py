#!/usr/bin/env python3
from __future__ import annotations
import argparse,gc,json,subprocess,sys
from pathlib import Path
from typing import Any
HERE=Path(__file__).resolve().parent
if str(HERE) not in sys.path: sys.path.insert(0,str(HERE))
import qldpc_scale_001a_math as m
import qldpc_scale_001a_symbolic as sym
import qtr_c90_resource_envelope_001 as env
import qtr_c90_structure_001 as st
from qldpc_scale_001a_shared import digest
ROOT=Path(__file__).resolve().parents[1]
EXP="QTR-C90-RETAINED-BOUND-001"
MP=ROOT/"registry/qtr-c90-retained-bound-001-manifest.json"
MD="d9072de9631901a0b97df61c14b8c5dc9d5de7d21ad9d7e181765c69fad223c2"
BASE="b7e5127fed532a8bc6dc6703bfcac3f58882477f"
RP="0ea802c6ce9c584c52bbc5608ac4a94abec5f29c2939e5c226386c4581205195"; SP="ade245552af2f88d5ecb8c0b7f8eb363510ed678908fb80462b911255dd63d67"; CP="198bb28f47844aa98efa20d8c838c48870a8aef41ccfda266b16661677e363e1"
RB="88bff95dda86b7f26c8aaff4e42ec9a8d2fda33c"; SB="b40ccb272da93afd5d43b00501fbd6be2bed0d7c"; CB="268a5bfa9ed35ad3cd5984031de20487835643d0"
REFS=["B0_ATTEMPT_UPPER_CONTROL","B1_TYPED_CANONICAL_KEY_BOUND","B2_STAGE_OPERAND_DOMAIN_BOUND","B3_PROVENANCE_PARTITION_BOUND"]
METHODS=["S0_BASELINE","S1_GF2_CONSTRAINT_ELIMINATION","S2_SEPARATOR_INTERFACE_COMPILATION","S3_GF2_PLUS_SEPARATOR"]
ALGS=["sum_product_bsc_p_0_1","soft_tropical_base_2","min_plus_hamming"]

def head():
    try:return subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    except Exception:return "UNKNOWN"
def canon(d,k="payload_sha256"):
    x=dict(d);x.pop(k,None);return digest(x)
def gitblob(p):return subprocess.check_output(["git","hash-object",str(p)],cwd=ROOT,text=True).strip()
def loadj(p,sha,blob):
    d=json.loads(p.read_text());assert d.get("payload_sha256")==sha;assert gitblob(p)==blob;return d
def manifest():
    d=json.loads(MP.read_text());x=dict(d);x.pop("manifest_payload_sha256")
    assert d["manifest_payload_sha256"]==MD and digest(x)==MD
    assert d["authority"]=={"council_issue":105,"council_referee_comment":5390019257,"execution_issue":106,"human_steward_comment":5391086069,"protected_predecessor_merge":BASE}
    assert d["refinements"]==REFS and d["frozen_methods"]==METHODS and d["abstract_state"]["max_abstract_state_records"]==8192
    return d
def preds():
    r=loadj(ROOT/"evidence/QTR-C90-RESOURCE-ENVELOPE-001-report.json",RP,RB)
    s=loadj(ROOT/"evidence/QTR-C90-STRUCTURE-001-report.json",SP,SB)
    c=loadj(ROOT/"evidence/QLDPC-SCALE-001A-report.json",CP,CB)
    assert r["overall_outcome"]=="C90_REPRESENTATION_BOUND_DOMINATES_AFTER_WORK_CAP_RELAXATION" and r["materialization_performed"] is False
    assert s["overall_outcome"]=="C90_PREDECLARED_EXACT_STRUCTURAL_FAMILY_EXHAUSTED" and not s["phase_d_reached"] and not s["phase_e_reached"]
    return r,s,c
def term_u(a,n): return (2 if n else 0) if a!="min_plus_hamming" else (1+n if n else 0)
def init_u(scope): return min(2,1<<len(scope))
def guard(n): assert n<=manifest()["abstract_state"]["max_abstract_state_records"],f"abstract-state overflow {n}"

def attempts(scopes,sel,order):
    ss=set(sel);fs=[tuple(x) for x in scopes]
    local=sum((1<<len(x))+(2*(1<<len(x)) if q in ss else 0) for q,x in enumerate(fs))
    mul=mar=0; stages=[]
    for t,v in enumerate(order):
        inv=[x for x in fs if v in x];rest=[x for x in fs if v not in x]
        if not inv: stages.append((t,v,0,0,0));continue
        u=tuple(sorted(set().union(*(set(x) for x in inv))));o=tuple(x for x in u if x!=v)
        j=1<<len(u);z=1<<len(o);mul+=j*max(0,len(inv)-1);mar+=z
        stages.append((t,v,len(inv),j,z));rest.append(o);fs=rest
    root=max(0,len(fs)-1)
    return {"node_intern_attempts":local+mul+mar+root,"local":local,"mul":mul,"marginal":mar,"root":root,"stages":stages}
def b1(scopes,sel,order,a,b0):
    q=attempts(scopes,sel,order); raw=term_u(a,len(scopes))+2*len(sel)+q["mul"]+q["marginal"]+q["root"];v=min(b0,raw)
    p={"rule":"typed-key domains; binary buckets capped by attempts","terminal":term_u(a,len(scopes)),"ite":2*len(sel),"binary":q["mul"]+q["marginal"]+q["root"],"b0":b0,"bound":v}
    return v,4,digest(p)
def b2(scopes,sel,order,a,b0):
    fs=[{"s":tuple(x),"u":init_u(tuple(x))} for x in scopes];total=0;rec=[];state=len(fs)
    for t,v in enumerate(order):
        inv=[f for f in fs if v in f["s"]];rest=[f for f in fs if v not in f["s"]]
        if not inv: rec.append((t,v,0));state+=1;guard(state);continue
        un=tuple(sorted(set().union(*(set(f["s"]) for f in inv))));out=tuple(x for x in un if x!=v);j=1<<len(un);z=1<<len(out)
        acc=inv[0]["u"]; ms=[]
        for f in inv[1:]:
            x=min(j,acc*f["u"]);ms.append(x);total+=x;acc=x
        marg=min(z,acc*(acc+1)//2);total+=marg
        rec.append((t,v,tuple(f["u"] for f in inv),tuple(ms),acc,marg));rest.append({"s":out,"u":marg});fs=rest;state+=len(inv)+2;guard(state)
    if fs:
        acc=fs[0]["u"]
        for f in fs[1:]: x=min(1,acc*f["u"]);total+=x;acc=x
    raw=term_u(a,len(scopes))+2*len(sel)+total; val=min(b0,raw)
    return val,state,digest({"rule":"stage operand-domain induction","records":rec,"raw":raw,"b0":b0,"bound":val})
def b3(scopes,sel,order,a,b0,b2v):
    fs=[{"s":tuple(x),"u":init_u(tuple(x)),"p":("source",i)} for i,x in enumerate(scopes)];total=0;rec=[];state=len(fs)
    for t,v in enumerate(order):
        inv=[f for f in fs if v in f["s"]];rest=[f for f in fs if v not in f["s"]]
        if not inv: rec.append((t,v,0));state+=1;guard(state);continue
        un=tuple(sorted(set().union(*(set(f["s"]) for f in inv))));out=tuple(x for x in un if x!=v);z=1<<len(out);br=[]
        for bit in (0,1):
            cs=[min(f["u"],1<<max(0,len(f["s"])-1)) for f in inv];acc=cs[0];mb=[]
            for r in cs[1:]: x=min(z,acc*r);mb.append(x);total+=x;acc=x
            br.append(acc);state+=len(cs)+1;guard(state)
        marg=min(z,br[0]*br[1]);total+=marg
        rec.append((t,v,tuple(br),marg,tuple(f["p"] for f in inv)));rest.append({"s":out,"u":marg,"p":("stage",t)});fs=rest;state+=2;guard(state)
    if fs:
        acc=fs[0]["u"]
        for f in fs[1:]: x=min(1,acc*f["u"]);total+=x;acc=x
    raw=term_u(a,len(scopes))+2*len(sel)+total; pv=min(b0,raw);val=min(b2v,pv)
    return val,state,digest({"rule":"B2 plus frozen branch/provenance partitions; cross-bucket duplicates overcounted","records":rec,"raw":raw,"partition":pv,"b2":b2v,"bound":val,"different_signatures_imply_distinct":False})
def bounds(scopes,sel,order,a,b0=None):
    q=attempts(scopes,sel,order); b0a=q["node_intern_attempts"]; b0=b0a if b0 is None else b0
    assert b0a==b0,f"B0 mismatch {b0a} != {b0}"
    v1,n1,r1=b1(scopes,sel,order,a,b0);v2,n2,r2=b2(scopes,sel,order,a,b0);v3,n3,r3=b3(scopes,sel,order,a,b0,v2)
    vs={REFS[0]:b0,REFS[1]:v1,REFS[2]:v2,REFS[3]:v3};assert v3<=v2<=b0 and v1<=b0
    return vs,{REFS[0]:(len(q["stages"])+4,digest({"rule":"unique<=attempts","b0":b0})),REFS[1]:(n1,r1),REFS[2]:(n2,r2),REFS[3]:(n3,r3)}
def c72():
    c=m.construct_code();sc=[tuple(x) for x in c["scopes"]];sel=list(c["selector_basis_qubits"]);base=list(m.deterministic_min_fill(sc,len(c["x_basis"])));sep=list(st.junction_tree(sc,base)["separator_elimination_order"])
    return sc,sel,{METHODS[0]:base,METHODS[1]:base,METHODS[2]:sep,METHODS[3]:sep}
def c90():
    sc,orders=env.method_orders();pm=env.exact_predecessor.load_manifest();_,c,_,_=env.exact_predecessor.reconstruct_target(pm)
    return [tuple(x) for x in sc],list(c["selector_basis_qubits"]),orders

def controls():
    man=manifest();_,_,ce=preds();sc,sel,orders=c72();rows={};cache={}
    for method in METHODS:
        o=orders[method];osh=digest(o);rows[method]={}
        for a in ALGS:
            k=(osh,a)
            if k not in cache: cache[k]=sym.compile_symbolic_metadata(sc,sel,o,a);gc.collect()
            ex=cache[k];vs,pr=bounds(sc,sel,o,a,int(ex["compile_aop"]["NODE_INTERN"]));n=int(ex["node_count"])
            rows[method][a]={"exact_node_count":n,"exact_node_intern_attempts":int(ex["compile_aop"]["NODE_INTERN"]),"bounds":vs,"checks":{r:{"sound":n<=vs[r],"within_b0":vs[r]<=vs[REFS[0]]} for r in REFS},"receipts":{r:pr[r][1] for r in REFS}}
    adm={r:all(x["checks"][r]["sound"] and x["checks"][r]["within_b0"] for mm in rows.values() for x in mm.values()) for r in REFS};adm[REFS[0]]=True
    if not adm[REFS[2]]:adm[REFS[3]]=False
    z={"schema_version":1,"experiment_id":EXP,"phase":"CONTROL_CERTIFICATION","status":"CONTROL_CERTIFICATION_COMPLETE","source_commit":head(),"manifest_payload_sha256":MD,"control_source":{"experiment_id":"QLDPC-SCALE-001A","evidence_payload_sha256":CP,"validation_outputs_sha256":ce["selector_validation"]["validation_outputs_sha256"]},"methods":rows,"refinement_admitted_for_c90":adm,"c90_bound_computation_performed":False,"c90_materialization_performed":False,"claim_boundary":man["claim_boundary"]};z["payload_sha256"]=digest(z);return z
def ceiling(live):
    p=manifest()["physical_model"];total=p["memory_total_bytes"];avail=p["memory_available_bytes"];res=p["absolute_reserve_bytes"];nb=p["node_store_bytes_per_retained_node_engineering_upper_proxy"];tb=p["table_slot_bytes_per_live_entry_engineering_upper_proxy"];ov=p["fixed_process_overhead_bytes"]
    budgets=[total*70//100,total-res,avail-res];peak=min(budgets);non=live*tb+ov;n=(peak-non)//nb
    x={"live_entries":live,"fraction_budget_bytes":budgets[0],"reserve_budget_bytes":budgets[1],"available_budget_bytes":budgets[2],"binding_peak_budget_bytes":peak,"non_node_bytes":non,"node_bytes_per_retained_node":nb,"gate_compatible_node_ceiling":n};x["derivation_receipt_sha256"]=digest(x);return x
def physical(n,live):
    p=manifest()["physical_model"];pred=n*p["node_store_bytes_per_retained_node_engineering_upper_proxy"]+live*p["table_slot_bytes_per_live_entry_engineering_upper_proxy"]+p["fixed_process_overhead_bytes"];res=p["absolute_reserve_bytes"];total=p["memory_total_bytes"];avail=p["memory_available_bytes"]
    g={"predicted_peak_le_70pct_total":pred*100<=total*70,"absolute_2gib_reserve":pred+res<=total,"fresh_memavailable_covers_peak_plus_reserve":avail>=pred+res,"runtime_index_support":True,"serialized_storage_bounded":True}
    return pred,g
def ser(n):return 256+n*env.max_serialized_node_line_bytes(n)
def c90run(ctrl):
    man=manifest();_,s,_=preds();assert ctrl["phase"]=="CONTROL_CERTIFICATION" and ctrl["manifest_payload_sha256"]==MD;adm=ctrl["refinement_admitted_for_c90"];sc,sel,orders=c90();rows={};tight=False;cand=False;ind=False
    for method in METHODS:
        prot=s["c90_methods"][method];b0=int(prot["retained"]["upper"]);o=orders[method];assert digest(o)==prot["order_sha256"];live=int(env.planned_table_liveness(sc,o)["peak_live_factor_table_entries_exact_planned"]);ce=ceiling(live);assert ce["gate_compatible_node_ceiling"]==man["gate_compatible_node_targets"][method]
        algs={};worst={r:0 for r in REFS};rcpt={r:[] for r in REFS};states={r:0 for r in REFS}
        for a in ALGS:
            vs,pr=bounds(sc,sel,o,a,b0);algs[a]={}
            for r in REFS:
                if r!=REFS[0] and not adm.get(r,False): algs[a][r]={"bound_type":"unknown","bound_value":None,"status":"CONTROL_REJECTED","c90_materialization_performed":False};ind=True;continue
                v=vs[r];worst[r]=max(worst[r],v);states[r]=max(states[r],pr[r][0]);rcpt[r].append(pr[r][1]);guard(pr[r][0]);algs[a][r]={"bound_type":"upper_bound","bound_value":v,"protected_b0_value":b0,"soundness_receipt_sha256":pr[r][1],"abstract_state_count":pr[r][0],"abstract_state_schema_id":man["abstract_state"]["schema_id"],"c90_materialization_performed":False}
        rr={}
        for r in REFS:
            if r!=REFS[0] and not adm.get(r,False):rr[r]={"bound_type":"unknown","bound_value":None,"status":"CONTROL_REJECTED","control_certification":False,"c90_materialization_performed":False};continue
            v=worst[r];pred,g=physical(v,live);strict=v<b0;tight|=strict;cand|=all(g.values());receipt=digest({"method":method,"refinement":r,"algebra_receipts":rcpt[r],"worst":v,"order":digest(o),"schema":man["abstract_state"]["schema_id"]})
            rr[r]={"bound_type":"upper_bound","bound_value":v,"protected_b0_value":b0,"tightening_factor_numerator":b0,"tightening_factor_denominator":v,"strict_tightening":strict,"soundness_receipt_sha256":receipt,"control_certification":True,"abstract_state_count":states[r],"abstract_state_schema_id":man["abstract_state"]["schema_id"],"c90_materialization_performed":False,"gate_compatible_node_ceiling":ce["gate_compatible_node_ceiling"],"gate_target_certified":v<=ce["gate_compatible_node_ceiling"],"canonical_serialized_size_upper_bound_bytes":ser(v),"physical_model_components":{"retained_node_store_bytes":v*338,"live_factor_table_slot_bytes":live*18,"fixed_process_overhead_bytes":268435456},"physical_gate_booleans":g,"predicted_peak_resident_upper_proxy_bytes":pred,"physical_envelope_candidate":all(g.values()),"historical_cap_comparisons_diagnostic_only":{"retained_2pow22_pass":v<=4194304,"serialized_512mib_pass":ser(v)<=536870912,"diagnostic_only":True}}
        rows[method]={"protected_order_sha256":digest(o),"protected_transformation_receipt_sha256":prot["transformation_receipt_sha256"],"protected_b0_value":b0,"exact_live_factor_table_entries":live,"gate_ceiling_derivation":ce,"per_algebra":algs,"refinements":rr}
    outcome="C90_CANONICAL_NODE_BOUND_CERTIFIES_PHYSICAL_ENVELOPE_CANDIDATE" if cand else ("C90_CANONICAL_NODE_BOUND_TIGHTENED__PHYSICAL_GATE_STILL_UNCERTIFIED" if tight else ("C90_CANONICAL_NODE_BOUND_AUDIT_INDETERMINATE" if ind else "C90_CANONICAL_NODE_BOUND_NO_MATERIAL_TIGHTENING"))
    z={"schema_version":1,"experiment_id":EXP,"status":"candidate_executable_not_promoted","source_commit":head(),"manifest_payload_sha256":MD,"source_facts":{"protected_predecessor_merge":BASE,"resource_evidence_payload_sha256":RP,"structure_evidence_payload_sha256":SP,"frozen_methods":METHODS,"refinements":REFS,"abstract_state_schema_id":man["abstract_state"]["schema_id"]},"control_certification":{"payload_sha256":ctrl["payload_sha256"],"refinement_admitted_for_c90":adm},"proof_objects":{"invariant":man["bound_invariant"]["formula"],"abstract_state_max_records":8192,"c90_soundness_source":man["bound_invariant"]["c90_soundness_source"]},"derived_targets":man["gate_compatible_node_targets"],"c90_bounds":rows,"adjudication":{"overall_outcome":outcome,"actual_physical_infeasibility_established":False,"intrinsic_intractability_established":False,"full_c90_materialization_authorized":False,"separate_exact_execution_successor_required_for_materialization":True},"c90_materialization_performed":False,"frozen_307_validation_performed":False,"claim_boundary":man["claim_boundary"]};z["payload_sha256"]=digest(z);return z
def write(p,d):Path(p).write_text(json.dumps(d,indent=2,sort_keys=True)+"\n")
def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest="cmd",required=True);a=sp.add_parser("control");a.add_argument("--output",required=True);b=sp.add_parser("c90");b.add_argument("--control",required=True);b.add_argument("--output",required=True);x=ap.parse_args()
    if x.cmd=="control":z=controls();write(x.output,z);print("CONTROL:",z["payload_sha256"]);print("ADMITTED:",json.dumps(z["refinement_admitted_for_c90"],sort_keys=True));return
    c=json.loads(Path(x.control).read_text());assert canon(c)==c["payload_sha256"];z=c90run(c);write(x.output,z);print("OUTCOME:",z["adjudication"]["overall_outcome"]);print("PAYLOAD:",z["payload_sha256"]);[print(k,json.dumps({r:d.get("bound_value") for r,d in v["refinements"].items()},sort_keys=True)) for k,v in z["c90_bounds"].items()]
if __name__=="__main__":main()
