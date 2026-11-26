#!/usr/bin/env python3
"""Compact storage route within existing C90 external jobs and batch custody.

Controller binds a live provider lease before launch, and independently accepts
returned bytes. No scheduler, credentials, scoring, or admission authority.
"""
import argparse
import fcntl
import json
import os
import pathlib
import re
import signal
import subprocess
import tempfile
import time

import qtr_c90_selector_batches as batches
import qtr_c90_external_execution as external

P = pathlib.Path
ROOT = P(__file__).resolve().parents[1]
PROFILE = ROOT / "execution/external/QTR-C90-EXACT-DECODER-001/COMPACT.json"
SOURCE_SHA = "696cfc28bb6ef56993d84c31465d04ea041460ac5c7886df1a5b7f758e939a68"
BINARY_SHA = "e9c63b0d329e165cf96a1de37ee324f52ed35a95201dae347c4c6a4a3f35384c"
QUAL_HEAD = "9422215904e9efffbf9c1d6aed16480b91fc5d35"
RESERVE = 8 * 2**30
CAP = 3 * 2**30
HEX = re.compile(r"^[0-9a-f]{64}$")
HEAD = re.compile(r"^[0-9a-f]{40}$")

def check(ok, message):
    if not ok:
        raise ValueError(message)

def read(path):
    check(path.is_file() and not path.is_symlink(), "missing or linked input")
    return external.load_json(path)

def digest(path):
    check(path.is_file() and not path.is_symlink(), "missing or linked artifact")
    return batches.h(path)

def write(path, value):
    batches.commit(path, external.canonical_bytes(value))

def profile():
    p = read(PROFILE)
    check(p.get("source_path")=="reference/qtr_c90_native_eval_compact_refs_candidate.cpp","candidate source path drift")
    for k, v in {
        "record_type": "QTR_C90_COMPACT_STORAGE_ROUTE/1",
        "qualification_protected_head": QUAL_HEAD,
        "frozen_source_head": batches.HEAD,
        "activation_head": batches.ACTIVATION,
        "source_sha256": SOURCE_SHA, "binary_sha256": BINARY_SHA,
        "worker_ceiling_bytes": CAP, "host_reserve_bytes": RESERVE,
        "maximum_workers_per_provider_session": 1,
        "external_parallelism_ceiling": 48, "max_attempts_per_work_unit": 2,
        "batch_size": 16, "quality_exposed": False,
        "scientific_semantics_changed": False, "campaign_admission": False,
    }.items():
        check(p.get(k) == v, "compact profile drift: " + k)
    check(digest(ROOT / p["source_path"]) == SOURCE_SHA, "compact source drift")
    check(digest(ROOT / "evidence/QTR-C90-COMPACT-CLASS1-BATCH000-DIFFERENTIAL-001.json")
          == "6ff968f30d999cf8560ca1af42cc9f8b97360348fc63d66a1023b363ea8fa450",
          "qualification evidence drift")
    return p

def githead(path):
    return subprocess.check_output(["git","-C",str(path),"rev-parse","HEAD"], text=True).strip()

def frozen_inputs(folder, source, algebra, cls):
    source=source.resolve()
    check(githead(source) == batches.HEAD, "frozen source HEAD drift")
    check(not subprocess.check_output(["git","-C",str(source),"status","--porcelain","--untracked-files=no"]).strip(),
          "frozen source modified")
    with tempfile.TemporaryDirectory() as tmp:
        expected = P(tmp)/"selectors.txt"
        subprocess.run(["python3",str(source/"reference/qtr_c90_exact_native_campaign_001.py"),
                        "selectors","--logical-class",str(cls),"--output",str(expected)],
                       cwd=source,check=True,stdout=subprocess.DEVNULL,
                       env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
        m=read(folder/"manifest.json")
        check(m["algebra"]==algebra and m["logical_class"]==cls and m["source_head"]==batches.HEAD
              and m["activation_head"]==batches.ACTIVATION and m["schema"]=="C90_BATCH_TRANSPORT/1"
              and m["native_graph_sha256"]==batches.GRAPHS[algebra][1] and m["quality_exposed"] is False
              and m["selector_count"]==347 and m["batch_size"]==16 and len(m["entries"])==22,
              "batch plan identity")
        raw=expected.read_bytes()
        check(m["input_sha256"]==batches.sha(raw),"frozen selector digest")
        rows=raw.splitlines(keepends=True)
        for i,e in enumerate(m["entries"]):
            name=f"batch-{i:03d}.selectors.txt"
            chunk=b"".join(rows[16*i:16*i+16])
            check(e["number"]==i and e["start"]==16*i and e["count"]==len(rows[16*i:16*i+16])
                  and e["selector_file"]==name and digest(folder/name)==batches.sha(chunk)==e["selector_sha256"],
                  "frozen batch input mismatch")
        return m

def lease_check(l, job, manifest, now, *, live):
    check(l.get("record_type")=="QTR_C90_PROVIDER_BATCH_LEASE/1"
          and l.get("manifest_sha256")==job["manifest_sha256"]
          and l.get("work_unit_id")==job["work_unit_id"]
          and l.get("provider_class")==manifest["provider"]["class"]
          and l.get("adapter")==manifest["provider"]["adapter"]
          and l.get("provider_class")!="local_batch"
          and l.get("repository_write_credentials") is False
          and l.get("workers_on_session")==1
          and type(l.get("attempt")) is int
          and 1<=l["attempt"]<=manifest["retry_policy"]["max_attempts"]
          and isinstance(l.get("provider_execution_id"),str) and l["provider_execution_id"].strip()
          and isinstance(l.get("lease_id"),str) and l["lease_id"].strip()
          and HEX.fullmatch(str(l.get("provider_readback_sha256",""))), "provider lease binding")
    start,end=l["not_before_epoch"],l["deadline_epoch"]
    check(type(start) is int and type(end) is int and 0<end-start<=86400, "lease interval")
    if live:check(start<=now<end,"stale provider lease")
    return l

def bind(folder, batch, source, manifest_path, job_path, lease_path, readback, protected_head, output):
    profile()
    check(HEAD.fullmatch(protected_head),"transport HEAD format")
    current_main(protected_head)
    check(not subprocess.check_output(["git","-C",str(ROOT),"status","--porcelain","--untracked-files=no"]).strip(),
          "transport checkout modified")
    subprocess.run(["git","-C",str(ROOT),"merge-base","--is-ancestor",QUAL_HEAD,protected_head],check=True)
    manifest=read(manifest_path); ep=external.load_json(external.PROFILE_PATH)
    external.validate_profile(ep);external.validate_programme_binding(require_effective=True)
    external.validate_manifest_against_profile(manifest,ep)
    job=read(job_path);a,c=job["algebra"],job["logical_class"]
    check(type(c) is int and 1<=c<256 and a in batches.GRAPHS and job["work_unit_id"]==external.work_unit_id(a,c)
          and job["record_type"]=="QTR_EXTERNAL_WORK_UNIT" and job["manifest_sha256"]==digest(manifest_path)
          and job["source_commit"]==manifest["source"]["commit"]
          and job["source_payload_sha256"]==manifest["source"]["source_payload_sha256"]
          and job["activation_head"]==batches.ACTIVATION and job["selector_count"]==347
          and job["corpus_sha256"]==ep["source"]["corpus_sha256"]
          and job["compile_identity"]==ep["compile_identities"][a]
          and job["scientific_semantics_changed"] is False
          and job["promotion_claim"] is False and job["repository_mutation_performed"] is False,
          "external work-unit identity")
    check(job.get("campaign")==manifest["campaign"] and job.get("operation")==manifest["operation"]
          and manifest["operational_parameters"]["parallelism_ceiling"]<=48, "external job campaign drift")
    l=lease_check(read(lease_path),job,manifest,int(time.time()),live=True)
    check(digest(readback)==l["provider_readback_sha256"],"provider readback mismatch")
    check(l["provider_execution_id"] in readback.read_text(),"provider identity absent from readback")
    with tempfile.TemporaryDirectory() as tmp:
        index=P(tmp)/"pending.json"
        batches.campaign_plan(index,protected_head)
        pending=read(index);pending_sha=digest(index)
        check(any(u["work_unit_id"]==job["work_unit_id"] for u in pending["work_units"]), "work unit not pending")
    m=frozen_inputs(folder,source,a,c)
    check(type(batch) is int and 0<=batch<22 and l["batch"]==batch,"lease batch mismatch")
    e=m["entries"][batch]
    b={"record_type":"QTR_C90_COMPACT_BATCH_BINDING/1","protected_head":protected_head,
       "profile_sha256":digest(PROFILE),"source_head":batches.HEAD,"activation_head":batches.ACTIVATION,
       "source_sha256":SOURCE_SHA,"evaluator_sha256":BINARY_SHA,"graph_sha256":batches.GRAPHS[a][1],
       "algebra":a,"logical_class":c,"batch":batch,"count":e["count"],
       "selectors_sha256":e["selector_sha256"],"batch_plan_sha256":digest(folder/"manifest.json"),
       "external_manifest_sha256":digest(manifest_path),"external_job_sha256":digest(job_path),
       "pending_index_sha256":pending_sha,
       "worker_script_sha256":digest(P(__file__).resolve()),
       "batch_tool_sha256":digest(P(batches.__file__).resolve()),
       "external_tool_sha256":digest(P(external.__file__).resolve()),
       "provider_lease_sha256":digest(lease_path),"lease":l,
       "worker_ceiling_bytes":CAP,"host_reserve_bytes":RESERVE,
       "quality_exposed":False,"campaign_admission":False}
    write(output,b)
    return b

def load_binding(path, expected_sha):
    profile()
    check(HEX.fullmatch(expected_sha) and digest(path)==expected_sha,"binding digest mismatch")
    b=read(path); a,c,i=b["algebra"],b["logical_class"],b["batch"]
    check(a in batches.GRAPHS and type(c) is int and 1<=c<256 and type(i) is int and 0<=i<22
          and b["count"]==min(16,347-i*16),"batch domain")
    for k,v in {"record_type":"QTR_C90_COMPACT_BATCH_BINDING/1","profile_sha256":digest(PROFILE),
                "source_head":batches.HEAD,"activation_head":batches.ACTIVATION,
                "source_sha256":SOURCE_SHA,"evaluator_sha256":BINARY_SHA,
                "graph_sha256":batches.GRAPHS[a][1],"worker_ceiling_bytes":CAP,"host_reserve_bytes":RESERVE,
                "worker_script_sha256":digest(P(__file__).resolve()),
                "batch_tool_sha256":digest(P(batches.__file__).resolve()),
                "external_tool_sha256":digest(P(external.__file__).resolve()),
                "quality_exposed":False,"campaign_admission":False}.items():
        check(b.get(k)==v,"binding identity drift: "+k)
    check(HEAD.fullmatch(b["protected_head"]),"transport head")
    for k in ("selectors_sha256","batch_plan_sha256","external_manifest_sha256","external_job_sha256","provider_lease_sha256","pending_index_sha256"):
        check(HEX.fullmatch(b[k]),"binding digest shape")
    l=b["lease"]
    check(l["batch"]==i and l["work_unit_id"]==external.work_unit_id(a,c)
          and l["manifest_sha256"]==b["external_manifest_sha256"]
          and l["workers_on_session"]==1 and l["repository_write_credentials"] is False
          and l["provider_class"]!="local_batch"
          and 0<l["deadline_epoch"]-l["not_before_epoch"]<=86400
          and type(l["attempt"]) is int and 1<=l["attempt"]<=2,"lease drift")
    return b

def available():
    return int(re.search(r"^MemAvailable:\s+(\d+)",P("/proc/meminfo").read_text(),re.M).group(1))*1024

def file_identity(path):
    x=path.stat()
    return (x.st_dev,x.st_ino,x.st_size,x.st_mtime_ns,x.st_ctime_ns)

def verify_rows(b, selectors, rows):
    check(digest(selectors)==b["selectors_sha256"],"selector digest drift")
    ss=batches.lines(selectors); rr=batches.lines(rows)
    check(len(ss)==len(rr)==b["count"],"row cardinality drift")
    for j,(s,r) in enumerate(zip(ss,rr)):
        index,coord=map(int,s.split()); row=json.loads(r)
        check(index==(16*b["batch"]+j)*256+b["logical_class"] and 0<=coord<2**49
              and row["selector_index"]==index and row["selector_coordinate"]==coord
              and row["algebra_id"]==int(batches.GRAPHS[b["algebra"]][0])
              and row["status"]=="C90_COMPACT_NATIVE_SELECTOR_EVALUATED"
              and row["quality_exposed"] is False,"row identity drift")
        if row["algebra_id"]==2:
            check(type(row["minimum_weight"]) is int and 0<=row["minimum_weight"]<=90
                  and 0<=int(row["minimum_representative_hex"],16)<2**90
                  and 0<=int(row["canonical_hex"],16)<2**90,"min-plus value domain")
        else:
            check(0<=int(row["value_hex"],16)<2**384,"numeric value domain")

def check_time(b, started, finished):
    l=b["lease"]
    check(type(started) is int and type(finished) is int
          and l["not_before_epoch"]<=started<=finished<l["deadline_epoch"],"runtime outside lease")

def peak_from_time(path):
    t=path.read_text()
    m=re.search(r"Maximum resident set size \(kbytes\): (\d+)",t)
    check(m is not None and re.search(r"^\s*Exit status: 0\s*$",t,re.M),"nonzero or missing time receipt")
    return int(m.group(1))*1024

def check_memory_guard(output, binding_sha, phase, available_bytes, minimum, peak):
    """Persist the actual violating sample before terminating; never a success receipt."""
    violations=[]
    if minimum<RESERVE:violations.append("HOST_RESERVE")
    if peak>CAP:violations.append("WORKER_RSS")
    if violations:
        r={"record_type":"QTR_C90_COMPACT_GUARD_FAILURE/1","binding_sha256":binding_sha,
           "phase":phase,"observed_epoch":int(time.time()),"violations":violations,
           "available_bytes":available_bytes,"minimum_available_bytes":minimum,
           "peak_rss_bytes":peak,"host_reserve_bytes":RESERVE,"worker_ceiling_bytes":CAP,
           "quality_exposed":False,"campaign_admission":False}
        # A flushed, quality-blind line survives loss of the provider filesystem.
        print("COMPACT_GUARD_FAILURE "+json.dumps(r,sort_keys=True),flush=True)
        write(output/"guard-failure.json",r)
        raise ValueError("memory guard violated: "+",".join(violations))

def run(binding, binding_sha, evaluator, graph, selectors, output):
    b=load_binding(binding,binding_sha)
    identity=[file_identity(x) for x in (evaluator,graph,selectors)]
    check(digest(evaluator)==BINARY_SHA and digest(graph)==b["graph_sha256"]
          and digest(selectors)==b["selectors_sha256"],"staged artifact drift")
    check(identity==[file_identity(x) for x in (evaluator,graph,selectors)],"staged artifact changed during hashing")
    check(os.access(evaluator,os.X_OK),"evaluator not executable")
    lock_path=P("/tmp")/f"gcl-qtr-c90-compact-{os.getuid()}.lock"
    fd=os.open(lock_path,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,"r+") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        started=int(time.time());check_time(b,started,started)
        pre=available();check(pre>=CAP+RESERVE,"insufficient host memory for compact worker plus reserve")
        output.mkdir(mode=0o700,parents=False,exist_ok=False)
        minimum=pre;peak=0;partial=output/"rows.partial";timing=output/"time.txt";err=output/"stderr.txt"
        with partial.open("xb") as out,err.open("xb") as log:
            proc=subprocess.Popen(["/usr/bin/time","-v","-o",str(timing),str(evaluator.resolve()),
                "--native",str(graph.resolve()),"--selectors",str(selectors.resolve())],
                stdout=out,stderr=log,start_new_session=True,env={**os.environ,"LC_ALL":"C"})
            try:
                while proc.poll() is None:
                    current=available();minimum=min(minimum,current)
                    try: children=P(f"/proc/{proc.pid}/task/{proc.pid}/children").read_text().split()
                    except FileNotFoundError: children=[]
                    for pid in children:
                        try: status=P(f"/proc/{pid}/status").read_text()
                        except FileNotFoundError: continue
                        m=re.search(r"^VmRSS:\s+(\d+)",status,re.M)
                        if m:peak=max(peak,int(m.group(1))*1024)
                    check_memory_guard(output,binding_sha,"sampled",current,minimum,peak)
                    check(int(time.time())<b["lease"]["deadline_epoch"],"provider lease expired")
                    time.sleep(.25)
                check(proc.returncode==0,"native evaluator failed")
                current=available();minimum=min(minimum,current)
            except BaseException:
                try:os.killpg(proc.pid,signal.SIGTERM)
                except ProcessLookupError:pass
                try:proc.wait(timeout=3)
                except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
                raise
            out.flush();os.fsync(out.fileno())
        peak=max(peak,peak_from_time(timing))
        finished=int(time.time());check_time(b,started,finished)
        check_memory_guard(output,binding_sha,"terminal",current,minimum,peak)
        check(identity==[file_identity(x) for x in (evaluator,graph,selectors)],"staged artifact changed during execution")
        verify_rows(b,selectors,partial)
        finished=int(time.time());check_time(b,started,finished)
        rows=output/"rows.jsonl";os.replace(partial,rows)
        receipt={"record_type":"QTR_C90_COMPACT_BATCH_RUNTIME/1","binding_sha256":binding_sha,
            "provider_execution_id":b["lease"]["provider_execution_id"],"lease_id":b["lease"]["lease_id"],
            "attempt":b["lease"]["attempt"],"started_epoch":started,"finished_epoch":finished,
            "returncode":0,"preflight_available_bytes":pre,"minimum_available_bytes":minimum,
            "peak_rss_bytes":peak,"rows_sha256":digest(rows),"time_sha256":digest(timing),
            "stderr_sha256":digest(err),"quality_exposed":False,"campaign_admission":False}
        check_time(b,started,int(time.time()))
        write(output/"runtime.json",receipt)
        print("COMPACT_BATCH_RETURN_READY",binding_sha,digest(output/"runtime.json"),flush=True)

def verify_returned(b,binding_sha,selectors,rows,timing,stderr,runtime):
    r=read(runtime)
    for k,v in {"record_type":"QTR_C90_COMPACT_BATCH_RUNTIME/1","binding_sha256":binding_sha,
                "provider_execution_id":b["lease"]["provider_execution_id"],
                "lease_id":b["lease"]["lease_id"],"attempt":b["lease"]["attempt"],"returncode":0,
                "rows_sha256":digest(rows),"time_sha256":digest(timing),"stderr_sha256":digest(stderr),
                "quality_exposed":False,"campaign_admission":False}.items():
        check(r.get(k)==v,"runtime receipt drift: "+k)
    check_time(b,r["started_epoch"],r["finished_epoch"])
    check(type(r["preflight_available_bytes"]) is int and r["preflight_available_bytes"]>=CAP+RESERVE
          and type(r["minimum_available_bytes"]) is int and RESERVE<=r["minimum_available_bytes"]<=r["preflight_available_bytes"]
          and type(r["peak_rss_bytes"]) is int and 0<peak_from_time(timing)<=r["peak_rss_bytes"]<=CAP,"runtime resource violation")
    verify_rows(b,selectors,rows)
    return r

def custody_fields(folder,batch,binding_sha,runtime_sha):
    stem=folder/f"batch-{batch:03d}"
    binding=stem.with_suffix(".binding.json");runtime=stem.with_suffix(".runtime.json")
    b=load_binding(binding,binding_sha)
    check(b["batch"]==batch and digest(folder/"manifest.json")==b["batch_plan_sha256"]
          and digest(runtime)==runtime_sha,"compact custody binding drift")
    verify_returned(b,binding_sha,stem.with_suffix(".selectors.txt"),stem.with_suffix(".rows.jsonl"),
                    stem.with_suffix(".time.txt"),stem.with_suffix(".stderr.txt"),runtime)
    return b

def current_main(protected_head):
    check(githead(ROOT)==protected_head,"transport checkout HEAD mismatch")
    observed=subprocess.check_output(["git","-C",str(ROOT),"ls-remote","origin","refs/heads/main"],text=True).split()
    check(observed==[protected_head,"refs/heads/main"],"protected main changed; reconcile before dispatch or return")

def accept(folder,binding,binding_sha,returned,evaluator,graph,source,protected_head):
    b=load_binding(binding,binding_sha);i=b["batch"]
    check(returned.is_dir() and not returned.is_symlink(),"invalid returned artifact directory")
    check(b["protected_head"]==protected_head,"stale protected head at return")
    check(not subprocess.check_output(["git","-C",str(ROOT),"status","--porcelain","--untracked-files=no"]).strip(),"transport checkout modified")
    current_main(protected_head)
    frozen_inputs(folder,source,b["algebra"],b["logical_class"])
    check(digest(folder/"manifest.json")==b["batch_plan_sha256"],"batch plan changed")
    check(digest(evaluator)==BINARY_SHA and digest(graph)==b["graph_sha256"],"host artifact drift")
    stem=folder/f"batch-{i:03d}"
    verify_returned(b,binding_sha,stem.with_suffix(".selectors.txt"),returned/"rows.jsonl",
                    returned/"time.txt",returned/"stderr.txt",returned/"runtime.json")
    files=[(binding,".binding.json"),(returned/"runtime.json",".runtime.json"),
           (returned/"time.txt",".time.txt"),(returned/"stderr.txt",".stderr.txt"),
           (returned/"rows.jsonl",".rows.jsonl")]
    check(all(not stem.with_suffix(suffix).exists() for _,suffix in files)
          and not stem.with_suffix(".verified.json").exists(),"existing or ambiguous custody; reconcile first")
    for src,suffix in files:batches.commit(stem.with_suffix(suffix),src.read_bytes())
    batches.verify(folder,i,evaluator,graph,compact_binding_sha=binding_sha,
                   compact_runtime_sha=digest(stem.with_suffix(".runtime.json")))
    print("COMPACT_BATCH_HOST_CUSTODY_VERIFIED",i,flush=True)

def join(folder,source,output,semantic):
    source=source.resolve()
    m=read(folder/"manifest.json")
    frozen_inputs(folder,source,m["algebra"],m["logical_class"])
    for i in range(22):
        claim=read(folder/f"batch-{i:03d}.verified.json")
        check(claim["evaluator_sha256"]==BINARY_SHA,"mixed engine in compact class")
        custody_fields(folder,i,claim["compact_binding_sha256"],claim["compact_runtime_sha256"])
    check(not semantic.exists(),"semantic receipt already exists")
    batches.join(folder,output)
    subprocess.run(["python3",str(source/"reference/qtr_c90_exact_native_campaign_001.py"),"validate-shard",
                    "--algebra",m["algebra"],"--logical-class",str(m["logical_class"]),
                    "--rows",str(output.resolve()),"--output",str(semantic.resolve())],
                   cwd=source,check=True,env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
    r=read(semantic)
    check(r["status"]=="C90_ACTIVATED_SELECTOR_SHARD_EVALUATED" and r["selector_count"]==347
          and r["quality_exposed"] is False and r["scientific_semantics_changed"] is False,"frozen shard validation failed")
    print("COMPACT_FULL_CLASS_VALIDATED__NO_ADMISSION",flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest="cmd",required=True)
    x=sub.add_parser("bind")
    for n in ("folder","source","manifest","job","lease","readback","output"):x.add_argument("--"+n,type=P,required=True)
    x.add_argument("--batch",type=int,required=True);x.add_argument("--protected-head",required=True)
    x=sub.add_parser("run")
    for n in ("binding","evaluator","graph","selectors","output"):x.add_argument("--"+n,type=P,required=True)
    x.add_argument("--binding-sha",required=True)
    x=sub.add_parser("accept")
    for n in ("folder","binding","returned","evaluator","graph","source"):x.add_argument("--"+n,type=P,required=True)
    x.add_argument("--binding-sha",required=True);x.add_argument("--protected-head",required=True)
    x=sub.add_parser("join")
    for n in ("folder","source","output","semantic"):x.add_argument("--"+n,type=P,required=True)
    a=p.parse_args()
    if a.cmd=="bind":
        bind(a.folder,a.batch,a.source,a.manifest,a.job,a.lease,a.readback,a.protected_head,a.output)
        print("COMPACT_BINDING_READY",digest(a.output))
    elif a.cmd=="run":run(a.binding,a.binding_sha,a.evaluator,a.graph,a.selectors,a.output)
    elif a.cmd=="accept":accept(a.folder,a.binding,a.binding_sha,a.returned,a.evaluator,a.graph,a.source,a.protected_head)
    else:join(a.folder,a.source,a.output,a.semantic)

if __name__=="__main__":main()
