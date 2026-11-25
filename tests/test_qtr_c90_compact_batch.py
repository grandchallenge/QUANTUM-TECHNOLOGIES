"""Quality-blind compact transport tests; synthetic provider/graph, no live lease."""
import argparse
import json
import pathlib
import struct
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import qtr_c90_compact_batch as mod

P=pathlib.Path
B=mod.batches
E=mod.external

class CompactBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.root=P(cls.tmp.name)
        cls.engine=cls.root/"compact"
        subprocess.run(["g++","-O2","-std=c++17","-o",str(cls.engine),
                        str(ROOT/"reference/qtr_c90_native_eval_compact_refs_candidate.cpp")],
                       check=True,timeout=90)
        cls.graph=cls.root/"tiny.qtrbin"
        nodes=[(0,0,0,0),(0,1,0,0),(1,0,0,1),(4,0,2,0)]
        cls.graph.write_bytes(struct.pack("<8sIQI",b"QTRC90N1",1,len(nodes),len(nodes)-1)
                              +b"".join(struct.pack("<BIII",*x) for x in nodes))
        cls.graphsha=B.h(cls.graph)

    def setUp(self):
        t=tempfile.TemporaryDirectory(dir=self.root)
        self.addCleanup(t.cleanup)
        self.d=P(t.name)
        self.alg="soft_tropical_base_2"
        self.selectors=self.d/"selectors.txt"
        self.selectors.write_text("".join(f"{i*256+1} {i%2}\n" for i in range(347)))
        self.folder=self.d/"class"
        self.mf=self.d/"external"
        # Only test fixture identities; no production provider or scientific data.
        E.materialize(argparse.Namespace(provider_class="hosted_session",adapter="fixture",
                          source_payload_sha256="a"*64,parallelism=2,output=str(self.mf)))
        self.manifest=self.mf/"MANIFEST.json"
        self.job=self.mf/"jobs/soft_tropical_base_2__class-001.json"
        self.readback=self.d/"provider.txt";self.readback.write_text("fixture-provider-id\n")
        now=int(time.time())
        self.lease=self.d/"lease.json"
        self.l={"record_type":"QTR_C90_PROVIDER_BATCH_LEASE/1","manifest_sha256":B.h(self.manifest),
                "work_unit_id":"soft_tropical_base_2/class-001","batch":0,
                "provider_class":"hosted_session","adapter":"fixture",
                "provider_execution_id":"fixture-provider-id","lease_id":"fixture-lease",
                "attempt":1,"workers_on_session":1,"repository_write_credentials":False,
                "not_before_epoch":now-5,"deadline_epoch":now+300,
                "provider_readback_sha256":B.h(self.readback)}
        self.lease.write_bytes(E.canonical_bytes(self.l))
        self.bindfile=self.d/"binding.json"
        self.returned=self.d/"return"
        self.head=mod.githead(ROOT)
        # Isolate only the provider/frozen-source and real graph identity boundary
        # in the fixture; execute the real guarded subprocess and custody code.
        orig_h=B.h
        def fixture_h(path):
            if path==self.engine:return mod.BINARY_SHA
            return orig_h(path)
        for ctx in (patch.object(B,"h",side_effect=fixture_h),
                    patch.dict(B.GRAPHS,{self.alg:("1",self.graphsha)}),
                    patch.object(mod,"current_main"),
                    patch.object(mod,"frozen_inputs",side_effect=lambda folder,*args:mod.read(folder/"manifest.json")),
                    patch.object(mod,"available",return_value=12*2**30)):
            ctx.start();self.addCleanup(ctx.stop)
        B.plan(self.selectors,self.folder,16,1,self.alg)

    def bind(self):
        # CI is clean at exact head; local development may be staged. Mock only
        # checkout cleanliness and ancestry for fixture, not custody checks.
        with patch.object(mod.subprocess,"check_output",return_value=b""),              patch.object(mod.subprocess,"run"):
            mod.bind(self.folder,0,ROOT,self.manifest,self.job,self.lease,self.readback,self.head,self.bindfile)
        return mod.digest(self.bindfile)

    def test_guarded_run_return_and_custody(self):
        sha=self.bind()
        b=mod.load_binding(self.bindfile,sha)
        self.assertEqual(b["count"],16)
        self.assertEqual(b["evaluator_sha256"],mod.BINARY_SHA)
        sel=self.folder/"batch-000.selectors.txt"
        mod.run(self.bindfile,sha,self.engine,self.graph,sel,self.returned)
        self.assertEqual(len((self.returned/"rows.jsonl").read_text().splitlines()),16)
        with patch.object(mod.subprocess,"check_output",return_value=b""):
            mod.accept(self.folder,self.bindfile,sha,self.returned,self.engine,self.graph,ROOT,self.head)
        claim=mod.read(self.folder/"batch-000.verified.json")
        self.assertEqual(claim["compact_binding_sha256"],sha)
        self.assertEqual(claim["compact_runtime_sha256"],mod.digest(self.folder/"batch-000.runtime.json"))
        mod.custody_fields(self.folder,0,sha,claim["compact_runtime_sha256"])
        with self.assertRaises((AssertionError,ValueError,FileExistsError)):
            B.verify(self.folder,0,self.engine,self.graph)
        with self.assertRaises((AssertionError,ValueError,FileExistsError)):
            with patch.object(mod.subprocess,"check_output",return_value=b""):
                mod.accept(self.folder,self.bindfile,sha,self.returned,self.engine,self.graph,ROOT,self.head)
        with self.assertRaises((AssertionError,ValueError,FileNotFoundError)):
            mod.join(self.folder,ROOT,self.d/"joined",self.d/"semantic")
        self.assertFalse((self.d/"joined").exists())
        p=self.folder/"batch-000.runtime.json"
        r=mod.read(p);r["minimum_available_bytes"]=mod.RESERVE-1;p.write_bytes(E.canonical_bytes(r))
        with self.assertRaises(ValueError):
            mod.custody_fields(self.folder,0,sha,mod.digest(p))

    def test_lease_and_memory_fail_closed(self):
        l=dict(self.l);l["deadline_epoch"]=int(time.time())-1
        self.lease.write_bytes(E.canonical_bytes(l))
        with self.assertRaisesRegex(ValueError,"stale provider lease"):
            self.bind()
        self.lease.write_bytes(E.canonical_bytes(self.l))
        sha=self.bind()
        with self.assertRaisesRegex(ValueError,"binding digest mismatch"):
            mod.load_binding(self.bindfile,"0"*64)
        with patch.object(mod,"available",return_value=mod.RESERVE+mod.CAP-1):
            with self.assertRaisesRegex(ValueError,"insufficient host memory"):
                mod.run(self.bindfile,sha,self.engine,self.graph,self.folder/"batch-000.selectors.txt",self.returned)
        self.assertFalse(self.returned.exists())

    def test_wrong_provider_or_batch_rejected(self):
        for key,value in (("provider_execution_id","other-id"),("batch",1),("attempt",3),("workers_on_session",2)):
            l=dict(self.l);l[key]=value;self.lease.write_bytes(E.canonical_bytes(l))
            with self.subTest(key=key),self.assertRaises(ValueError):
                self.bind()
            self.assertFalse(self.bindfile.exists())

if __name__=="__main__":unittest.main()
