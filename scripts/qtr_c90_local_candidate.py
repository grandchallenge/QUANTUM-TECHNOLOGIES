#!/usr/bin/env python3
"""Bounded six-batch CHAD-only candidate execution; no provider attestation."""
import argparse, fcntl, json, os, pathlib, re
import shutil, signal, subprocess as sp, tempfile, time, zipfile
import qtr_c90_compact_batch as compact
P=pathlib.Path
ROOT=compact.ROOT
AUTH="grandchallenge/QUANTUM-TECHNOLOGIES#114 comment 7238964763"
TASK="817c596573df21422b49c7ffd6a9069066c802e1"
VOLUME="04a50e22-627b-4c9f-bcd1-3c25fc7af43e"
HOLD={
 "1347":"QTR-C90-SP-C002-B001-IA-001","1348":"QTR-C90-SP-C002-B002-IA-001",
 "1349":"QTR-C90-ST-C001-B001-IA-001","1350":"QTR-C90-ST-C001-B002-IA-001",
 "1351":"QTR-C90-MP-C001-B001-IA-001","1352":"QTR-C90-MP-C001-B002-IA-001"}
ROSTER={
 1347:("sum_product_bsc_p_0_1",2,1),1348:("sum_product_bsc_p_0_1",2,2),
 1349:("soft_tropical_base_2",1,1),1350:("soft_tropical_base_2",1,2),
 1351:("min_plus_hamming",1,1),1352:("min_plus_hamming",1,2)}
GIB=2**30
def check(ok,msg):compact.check(ok,msg)
def git(repo,*args):return sp.check_output(["git","-C",str(repo),*args],timeout=60)
def live(repo):
    h=git(repo,"ls-remote","origin","refs/heads/main").decode().split()
    check(len(h)==2 and h[1]=="refs/heads/main","protected head unavailable")
    return h[0]
def show(repo,head,path):return git(repo,"show",head+":"+path)
def api(path):return json.loads(sp.check_output(["gh","api",path],timeout=60))
def validate_hold(cfg):
    check(cfg.get("qtr_local_candidate_hold")=={"authority":AUTH,"dispatches":HOLD},
          "exact protected local custody hold missing")
def job_scope(j,n):
    check(n in ROSTER and j.get("issue")==n and j.get("dispatch_id")==HOLD[str(n)]
          and (j.get("algebra"),j.get("logical_class"),j.get("batch"))==ROSTER[n]
          and j.get("count")==16 and j.get("scientific_head")==compact.batches.HEAD
          and j.get("activation_head")==compact.batches.ACTIVATION
          and j.get("graph_sha256")==compact.batches.GRAPHS[j["algebra"]][1]
          and j.get("quality_exposed") is False and j.get("campaign_admission") is False,
          "local job outside exact authorized domain")
def custody(solve,n):
    h=live(solve)
    cfg=json.loads(show(solve,h,".gcl/worker_queue/CONFIG.json"));validate_hold(cfg)
    did=HOLD[str(n)]
    jobs=json.loads(show(solve,h,".gcl/worker_queue/JOBS.json"))["jobs"]
    matches=[j for j in jobs if j["issue_number"]==n]
    check(len(matches)==1 and matches[0]["dispatch_id"]==did and matches[0]["task_commit"]==TASK,
          "live registry drift")
    issue=api(f"repos/grandchallenge/MATHSOLVE/issues/{n}")
    check(issue["state"]=="open" and not any(x["name"] in (
        "gcl-state:reserved","gcl-state:returned","gcl-state:available") for x in issue["labels"]),
        "issue not held locally")
    comments=api(f"repos/grandchallenge/MATHSOLVE/issues/{n}/comments?per_page=100")
    check(len(comments)<100 and not any(c["body"].strip()=="/claim"
        or c["body"].startswith("GCL-CONTRIBUTION-RESULT/1")
        or c["body"].startswith("GCL-WORKER-RESERVATION/1") for c in comments),
        "claim/return history requires separate reconciliation")
    return h
def disk_guard(work,need=0):
    mount=P("/mnt/gcl-lean-work")
    check(work.resolve()==mount/"qtr-c90-local-20261128" and not work.is_symlink(),
          "unexpected SSD workspace")
    check((mount/"volume-id").read_text().strip()==VOLUME and
          sp.check_output(["findmnt","-n","-o","FSTYPE","--target",str(work)],text=True).strip()=="ext4",
          "SSD mount identity drift")
    check(shutil.disk_usage(mount).free>=GIB+need and shutil.disk_usage("/mnt/c").free>=8*GIB+need,
          "physical or workspace disk reserve")
def stage_graph(work,j,archives):
    name=f"compiled-{j['algebra']}.qtrbin";p=work/"graphs"/name
    if not p.exists():
        archive=archives/f"{j['artifact_id']}.zip"
        check(compact.digest(archive)==j["archive_sha256"],"archive digest drift")
        tmp=p.with_suffix(".partial")
        check(not tmp.exists(),"partial graph requires reconciliation")
        with zipfile.ZipFile(archive) as z:
            info=z.getinfo(name);disk_guard(work,info.file_size)
            with z.open(info) as src,tmp.open("xb") as dest:
                shutil.copyfileobj(src,dest,1024*1024);dest.flush();os.fsync(dest.fileno())
        check(compact.digest(tmp)==j["graph_sha256"],"extracted graph digest drift")
        os.chmod(tmp,0o400);os.replace(tmp,p)
    check(compact.digest(p)==j["graph_sha256"],"graph digest drift")
    return p
def check_inputs(solve,source,work,n):
    did=HOLD[str(n)];prefix="handoffs/QTR-C90-SWARM-001/packet/"+did
    raw=show(solve,TASK,prefix+".json");j=json.loads(raw);job_scope(j,n)
    packet=work/"packets"/(did+".json");sel=work/"packets"/(did+".selectors.txt")
    check(packet.read_bytes()==raw and sel.read_bytes()==show(solve,TASK,prefix+".selectors.txt"),
          "staged packet differs from immutable task")
    check(compact.githead(source)==compact.batches.HEAD and
          not git(source,"status","--porcelain","--untracked-files=no").strip(),"frozen source drift")
    with tempfile.TemporaryDirectory(dir=work) as tmp:
        full=P(tmp)/"full.txt"
        sp.run(["python3",str(source/"reference/qtr_c90_exact_native_campaign_001.py"),
                "selectors","--logical-class",str(j["logical_class"]),"--output",str(full)],
               cwd=source,check=True,timeout=90,stdout=sp.DEVNULL,
               env={"PATH":"/usr/bin:/bin","LC_ALL":"C","PYTHONDONTWRITEBYTECODE":"1"})
        lines=full.read_bytes().splitlines(keepends=True);b=j["batch"]
        check(len(lines)==347 and sel.read_bytes()==b"".join(lines[16*b:16*(b+1)])
              and compact.digest(sel)==j["selectors_sha256"],"frozen selector mismatch")
    return j,sel
def guard_loop(proc,output,binding_sha,pre,deadline):
    minimum=pre;peak=0
    try:
        while proc.poll() is None:
            current=compact.available();minimum=min(minimum,current)
            try:children=P(f"/proc/{proc.pid}/task/{proc.pid}/children").read_text().split()
            except FileNotFoundError:children=[]
            for pid in children:
                try:s=P(f"/proc/{pid}/status").read_text()
                except FileNotFoundError:continue
                m=re.search(r"^VmRSS:\s+(\d+)",s,re.M)
                if m:peak=max(peak,int(m.group(1))*1024)
            compact.check_memory_guard(output,binding_sha,"sampled",current,minimum,peak)
            check(time.monotonic()<deadline,"bounded local batch deadline")
            time.sleep(.25)
        check(proc.returncode==0,"native evaluator failed")
    except BaseException:
        try:os.killpg(proc.pid,signal.SIGTERM)
        except ProcessLookupError:pass
        try:proc.wait(timeout=3)
        except sp.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
        raise
    return min(minimum,compact.available()),peak
def run(args):
    n=args.issue;work=args.work.resolve();solve=args.solve.resolve();source=args.source.resolve()
    check(n in ROSTER,"only six authorized batches")
    check(not git(ROOT,"status","--porcelain","--untracked-files=no").strip(),"transport modified")
    qhead=compact.githead(ROOT);compact.current_main(qhead);compact.profile()
    disk_guard(work)
    fd=os.open("/tmp/gcl-qtr-c90-compact-"+str(os.getuid())+".lock",os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,"r+") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        sh=custody(solve,n)
        j,sel=check_inputs(solve,source,work,n)
        evaluator=work/"eval-compact"
        check(compact.digest(evaluator)==compact.BINARY_SHA and os.access(evaluator,os.X_OK),"evaluator drift")
        graph=stage_graph(work,j,args.archives)
        prior=sorted((work/"receipts").glob(f"{n}-attempt-*"))
        check(not any((x/"local-candidate.json").exists() for x in prior),"already completed local candidate")
        check(len(prior)<2,"local attempts exhausted")
        check(compact.available()>=compact.CAP+compact.RESERVE,"post-stage memory preflight")
        disk_guard(work)
        out=work/"receipts"/f"{n}-attempt-{len(prior)+1}";out.mkdir(mode=0o700)
        identity=[compact.file_identity(x) for x in (evaluator,graph,sel)]
        binding={"record_type":"QTR_C90_CHAD_LOCAL_CANDIDATE_BINDING/1","authority":AUTH,
                 "qtr_head":qhead,"solve_head":sh,"task_commit":TASK,"job":j,
                 "evaluator_sha256":compact.BINARY_SHA,"worker_ceiling_bytes":compact.CAP,
                 "host_reserve_bytes":compact.RESERVE,"attempt":len(prior)+1,
                 "execution_origin":"CHAD_LOCAL_OS_ONLY","independent_execution_attested":False,
                 "campaign_admission":False,"quality_exposed":False}
        compact.write(out/"binding.json",binding);bs=compact.digest(out/"binding.json")
        pre=compact.available();check(pre>=compact.CAP+compact.RESERVE,"post-stage memory preflight")
        disk_guard(work);started=int(time.time());partial=out/"rows.partial"
        with partial.open("xb") as rows,(out/"stderr.txt").open("xb") as err:
            proc=sp.Popen(["/usr/bin/time","-v","-o",str(out/"time.txt"),"/usr/bin/nice","-n","10",
                          str(evaluator),"--native",str(graph),"--selectors",str(sel)],
                          cwd=out,stdout=rows,stderr=err,start_new_session=True,
                          env={"PATH":"/usr/bin:/bin","LC_ALL":"C"})
            minimum,peak=guard_loop(proc,out,bs,pre,time.monotonic()+1200)
            rows.flush();os.fsync(rows.fileno())
        peak=max(peak,compact.peak_from_time(out/"time.txt"))
        current=compact.available();minimum=min(minimum,current)
        compact.check_memory_guard(out,bs,"terminal",current,minimum,peak)
        check(0<peak<=compact.CAP and (out/"stderr.txt").stat().st_size==0,"terminal guard or stderr")
        check(identity==[compact.file_identity(x) for x in (evaluator,graph,sel)],"staged artifact changed")
        compact.verify_rows(j,sel,partial)
        compact.current_main(qhead);check(custody(solve,n)==sh,"custody changed during computation")
        os.replace(partial,out/"rows.jsonl")
        receipt={"record_type":"QTR_C90_CHAD_LOCAL_CANDIDATE/1","binding_sha256":bs,
                 "issue":n,"dispatch_id":j["dispatch_id"],"selector_count":16,
                 "started_epoch":started,"finished_epoch":int(time.time()),"returncode":0,
                 "minimum_available_bytes":minimum,"preflight_available_bytes":pre,"peak_rss_bytes":peak,
                 "rows_sha256":compact.digest(out/"rows.jsonl"),"time_sha256":compact.digest(out/"time.txt"),
                 "stderr_sha256":compact.digest(out/"stderr.txt"),"execution_origin":"CHAD_LOCAL_OS_ONLY",
                 "independent_execution_attested":False,"campaign_admission":False,"quality_exposed":False}
        compact.write(out/"local-candidate.json",receipt)
        print("LOCAL_CANDIDATE_VERIFIED",n,16,compact.digest(out/"local-candidate.json"),flush=True)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("work","solve","source","archives"):p.add_argument("--"+key,type=P,required=True)
    p.add_argument("--issue",type=int,choices=sorted(ROSTER),required=True)
    run(p.parse_args())
if __name__=="__main__":main()
