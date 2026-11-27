#!/usr/bin/env python3
"""Read a protected Solve return as bounded candidate data, never execute its content."""
import argparse, base64, datetime as dt, hashlib, json, os, pathlib as pl
import subprocess as sp, sys, re
P=pl.Path
def require(ok,msg):
    if not ok:raise ValueError(msg)
def sha(b):return hashlib.sha256(b).hexdigest()
def api(path):return json.loads(sp.check_output(["gh","api",path],timeout=60))
def git(root,*args):return sp.check_output(["git","-C",str(root),*args])
def parse_time(t):return dt.datetime.fromisoformat(t.replace("Z","+00:00"))
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--solve",type=P,required=True);p.add_argument("--qtr",type=P,required=True)
    p.add_argument("--dispatch",required=True);p.add_argument("--comment-id",type=int,required=True)
    p.add_argument("--key-home",type=P,required=True);p.add_argument("--output",type=P,required=True)
    a=p.parse_args()
    require(re.fullmatch(r"QTR-C90-(SP|ST|MP)-C\d{3}-B\d{3}-IA-001",a.dispatch),"dispatch ID")
    solve=a.solve.resolve();qtr=a.qtr.resolve()
    head=git(solve,"rev-parse","HEAD").decode().strip()
    require(git(solve,"ls-remote","origin","refs/heads/main").decode().split()==[head,"refs/heads/main"],"Solve checkout not exact protected main")
    for root in (solve,qtr):require(not git(root,"status","--porcelain","--untracked-files=no").strip(),"modified verifier checkout")
    require(git(qtr,"rev-parse","HEAD").decode().strip()=="cd35fd801dc6573a03f53e46f5b1ba02ea430f47","QTR verification source mismatch")
    sys.path.insert(0,str(solve));from ci import ns_ci_github_contribution_intake as intake
    from ci.gcl_worker_queue_contract import active_reservation
    profile,dispatch=intake.load_dispatch(solve,a.dispatch)
    require(profile.campaign=="QTR-C90-SWARM-001","wrong campaign")
    base=solve/"contributions/QTR-C90-SWARM-001"
    raw=base/"raw"/a.dispatch/f"github-comment-{a.comment_id}.md"
    rp=base/"receipts"/a.dispatch/f"github-comment-{a.comment_id}.json"
    r=json.loads(rp.read_text());body=raw.read_text()
    require(r["raw_sha256"]==sha(body.encode()) and r["github_comment_id"]==a.comment_id and r["dispatch_id"]==a.dispatch and r["worker_reservation_enforced"] is True and r["handling_state"]=="received_unadjudicated","protected return receipt mismatch")
    parsed=intake.parse_result_comment(body,solve)
    require(parsed["preamble"]["disposition"]=="FINITE_CERTIFICATE","not a computed candidate")
    issue=dispatch["github_issue_number"]
    observed=api(f"repos/grandchallenge/MATHSOLVE/issues/comments/{a.comment_id}")
    require(observed["body"]==body and observed["user"]["login"]==r["authenticated_github_actor"]==r["worker_reservation_owner"] and observed["issue_url"].endswith(f"/issues/{issue}"),"return comment mismatch")
    at=parse_time(observed["created_at"]);comments=[]
    for page in range(1,101):
        batch=api(f"repos/grandchallenge/MATHSOLVE/issues/{issue}/comments?per_page=100&page={page}")
        comments.extend(c for c in batch if parse_time(c["created_at"])<=at and c["id"]<a.comment_id)
        if len(batch)<100:break
    else:raise ValueError("incomplete comment census")
    lease=active_reservation(comments,a.dispatch,at,{"github-actions[bot]"})
    require(lease is not None and lease["worker"]==r["authenticated_github_actor"],"return not covered by authenticated lease")
    rel=f"handoffs/QTR-C90-SWARM-001/packet/{a.dispatch}"
    job=json.loads(git(solve,"show",f"{dispatch['task_commit']}:{rel}.json"))
    selectors=git(solve,"show",f"{dispatch['task_commit']}:{rel}.selectors.txt")
    require(sha(selectors)==job["selectors_sha256"],"protected selector drift")
    armor=parsed["sections"]["Derivation"]
    plaintext=sp.check_output(["gpg","--homedir",str(a.key_home),"--batch","--max-output","40000","--decrypt"],input=armor.encode(),timeout=30,stderr=sp.DEVNULL)
    require(len(plaintext)<=40000,"payload size")
    x=json.loads(plaintext)
    require(x["record_type"]=="QTR_C90_EXTERNAL_AGENT_CANDIDATE/1" and x["job"]==job and x["worker"]==lease["worker"] and x["reservation_comment_id"]==lease["_comment_id"] and x["claimed_at"]==lease["claimed_at"] and x["expires_at"]==lease["expires_at"],"candidate/lease mismatch")
    require(x["quality_exposed"] is False and x["campaign_admission"] is False and x["independent_execution_attested"] is False,"candidate authority mismatch")
    require(x["evaluator_sha256"]=="e9c63b0d329e165cf96a1de37ee324f52ed35a95201dae347c4c6a4a3f35384c","binary mismatch")
    start,finish=x["started_epoch"],x["finished_epoch"]
    require(type(start) is int and type(finish) is int and int(parse_time(lease["claimed_at"]).timestamp())<=start<=finish<=int(at.timestamp())<int(parse_time(lease["expires_at"]).timestamp()),"run time outside lease")
    sys.path.insert(0,str(qtr/"scripts"));import qtr_c90_compact_batch as compact
    compact.profile()
    pre,minimum,peak=x["preflight_available_bytes"],x["minimum_available_bytes"],x["peak_rss_bytes"]
    require(all(type(z) is int for z in (pre,minimum,peak)) and pre>=compact.CAP+compact.RESERVE and compact.RESERVE<=minimum<=pre and 0<peak<=compact.CAP,"candidate resource envelope")
    require(set(x["artifacts"])=={"rows.jsonl","time.txt","stderr.txt"},"artifact domain")
    data={}
    for n,record in x["artifacts"].items():
        b=base64.b64decode(record["base64"],validate=True)
        require(len(b)==record["bytes"]<=30000 and sha(b)==record["sha256"],"artifact identity")
        data[n]=b
    require("Rows SHA256: "+sha(data["rows.jsonl"]) in parsed["sections"]["Verification / falsification hooks"],"public digest mismatch")
    require(data["stderr.txt"]==b"","nonempty evaluator stderr")
    output=a.output.resolve();output.mkdir(mode=0o700,exist_ok=False)
    for n,b in {**data,"selectors.txt":selectors}.items():
        with (output/n).open("xb") as f:f.write(b)
    compact.verify_rows(job,output/"selectors.txt",output/"rows.jsonl")
    require(compact.peak_from_time(output/"time.txt")<=peak,"terminal peak inconsistent")
    receipt={"record_type":"QTR_C90_EXTERNAL_AGENT_CANDIDATE_VERIFICATION/1","dispatch_id":a.dispatch,"comment_id":a.comment_id,"solve_protected_head":head,"task_commit":dispatch["task_commit"],"raw_sha256":r["raw_sha256"],"lease_comment_id":lease["_comment_id"],"rows_sha256":sha(data["rows.jsonl"]),"selector_count":job["count"],"status":"CANDIDATE_BYTES_AND_LEASE_VERIFIED__INDEPENDENT_EXECUTION_NOT_ATTESTED","quality_exposed":False,"campaign_admission":False}
    with (output/"candidate-verification.json").open("x") as f:json.dump(receipt,f,indent=2,sort_keys=True);f.write("\n")
    print(receipt["status"],receipt["selector_count"],receipt["rows_sha256"])
if __name__=="__main__":main()
