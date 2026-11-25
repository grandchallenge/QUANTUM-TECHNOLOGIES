"""Quality-blind engineering qualification; never activates the C90 evaluator."""
import hashlib
import json
import pathlib
import random
import struct
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
FROZEN = "675865123437c3d6c908c7a3af337fd4023c5d0b"
ORIGINAL_BLOB = "92022fa89ceff9cf4ac0c9b6ce8613617664e1a6"
CANDIDATE_SHA = "696cfc28bb6ef56993d84c31465d04ea041460ac5c7886df1a5b7f758e939a68"
CANDIDATE = ROOT / "reference/qtr_c90_native_eval_compact_refs_candidate.cpp"

def fixture(algebra):
    nodes = []
    def node(k, a=0, b=0, c=0):
        i = len(nodes)
        nodes.append((k,a,b,c))
        return i
    if algebra < 2:
        t = [node(0,0),node(0,1)]
        mul, add = 3,4
    else:
        t = [node(0,0)] + [node(0,i) for i in range(1,91)]
        mul, add = 5,6
    terms = []
    for j in range(1200):
        if algebra < 2:
            a,b = t[j%2],t[(j+1)%2]
            x,y = node(1,j%49,a,b),node(1,(j+13)%49,b,a)
        else:
            a,b = t[1+j%45],t[46+j%45]
            x,y = node(1,j%49,0,a),node(1,(j+13)%49,0,b)
        terms.append(node(mul,x,y))
    stop = len(nodes)
    root = terms[0]
    for term in terms[1:]:
        root = node(add,root,term)
    data = struct.pack("<8sIQI",b"QTRC90N1",algebra,len(nodes),root)
    return data + b"".join(struct.pack("<BIII",*n) for n in nodes),stop

def oracle(algebra, coordinate):
    if algebra < 2:
        v = [9 if algebra == 0 else 2,1]
        return sum(v[(j%2)^((coordinate>>(j%49))&1)] *
                   v[((j+1)%2)^((coordinate>>((j+13)%49))&1)]
                   for j in range(1200))
    vals = []
    for j in range(1200):
        a = (1<<(j%45)) if (coordinate>>(j%49))&1 else 0
        b = (1<<(45+j%45)) if (coordinate>>((j+13)%49))&1 else 0
        vals.append((int(bool(a))+int(bool(b)),a+b))
    return (*min(vals), min(x[1] for x in vals))

class CompactReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.path = pathlib.Path(cls.tmp.name)
        original = subprocess.check_output(
            ["git","show",FROZEN+":reference/qtr_c90_exact_native_eval_001.cpp"],
            cwd=ROOT)
        blob = subprocess.check_output(["git","hash-object","--stdin"], input=original, cwd=ROOT).decode().strip()
        if blob != ORIGINAL_BLOB:
            raise AssertionError("frozen source identity drift")
        raw = CANDIDATE.read_bytes()
        if hashlib.sha256(raw).hexdigest() != CANDIDATE_SHA:
            raise AssertionError("candidate bytes drift; require new qualification")
        source = raw.decode()
        if source.count("REGION_BITS = 24;") != 1 or source.count("REGION_CAP = 32;") != 1:
            raise AssertionError("window test transform drift")
        forced = source.replace("REGION_BITS = 24;","REGION_BITS = 12;").replace("REGION_CAP = 32;","REGION_CAP = 2;").encode()
        cls.engines = []
        for tag, data in (("original",original),("candidate",raw),("forced",forced)):
            src = cls.path / (tag+".cpp")
            src.write_bytes(data)
            engine = cls.path / tag
            subprocess.run(["g++","-O3","-std=c++17","-o",str(engine),str(src)],check=True,timeout=90)
            cls.engines.append(engine)
        rng = random.Random(20261124)
        cls.coords = [0,(1<<49)-1]+[rng.getrandbits(49) for _ in range(30)]

    def invoke(self,engine,graph,selectors,*args,check=True):
        return subprocess.run([str(engine),"--native",str(graph),"--selectors",str(selectors),*map(str,args)],capture_output=True,check=check,timeout=30)

    def test_three_algebras_oracle_and_checkpoints(self):
        for algebra in range(3):
            with self.subTest(algebra=algebra):
                folder = self.path / str(algebra)
                folder.mkdir()
                graph = folder / "graph.qtrbin"
                raw,stop = fixture(algebra)
                graph.write_bytes(raw)
                selectors = folder / "selectors.txt"
                selectors.write_text("".join(f"{i} {c}\n" for i,c in enumerate(self.coords)))
                one = folder / "one.txt"
                one.write_text("0 0\n")
                outputs = [self.invoke(x,graph,selectors).stdout for x in self.engines]
                self.assertEqual(outputs[0],outputs[1])
                self.assertEqual(outputs[0],outputs[2])
                rows = [json.loads(x) for x in outputs[0].splitlines()]
                self.assertEqual(len(rows),32)
                for i,(coordinate,row) in enumerate(zip(self.coords,rows)):
                    self.assertEqual((row["selector_index"],row["selector_coordinate"]),(i,coordinate))
                    self.assertEqual(row["algebra_id"],algebra)
                    self.assertIs(row["quality_exposed"],False)
                    self.assertGreater(row["peak_live_values"],1200)
                    expected = oracle(algebra,coordinate)
                    if algebra < 2:
                        self.assertEqual(int(row["value_hex"],16),expected)
                    else:
                        self.assertEqual((row["minimum_weight"],int(row["minimum_representative_hex"],16),int(row["canonical_hex"],16)),expected)
                checkpoints = []
                for i,engine in enumerate(self.engines):
                    cp = folder / f"checkpoint-{i}.bin"
                    result = self.invoke(engine,graph,one,"--stop-node",stop,"--checkpoint-out",cp,"--checkpoint-binding","b"*64)
                    self.assertEqual(json.loads(result.stdout)["status"],"C90_COMPACT_NATIVE_SELECTOR_CHECKPOINTED")
                    checkpoints.append(cp)
                self.assertEqual(len({cp.read_bytes() for cp in checkpoints}),1)
                for engine in self.engines:
                    for cp in checkpoints:
                        got = self.invoke(engine,graph,one,"--checkpoint-in",cp,"--checkpoint-binding","b"*64)
                        self.assertEqual(got.stdout,outputs[0].splitlines(keepends=True)[0])
                    bad = self.invoke(engine,graph,one,"--checkpoint-in",checkpoints[0],"--checkpoint-binding","c"*64,check=False)
                    self.assertNotEqual(bad.returncode,0)
                    self.assertEqual(bad.stdout,b"")

if __name__ == "__main__":
    unittest.main()
