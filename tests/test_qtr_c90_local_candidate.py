import copy, pathlib, sys, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import qtr_c90_local_candidate as local
class LocalCandidateTest(unittest.TestCase):
    def test_exact_hold_only(self):
        cfg={"qtr_local_candidate_hold":{"authority":local.AUTH,"dispatches":dict(local.HOLD)}}
        local.validate_hold(cfg)
        for bad in ({}, {"qtr_local_candidate_hold":{"authority":local.AUTH,"dispatches":{}}}):
            with self.assertRaises(ValueError):local.validate_hold(bad)
    def test_job_scope_and_tamper(self):
        for n,(a,c,b) in local.ROSTER.items():
            j={"issue":n,"dispatch_id":local.HOLD[str(n)],"algebra":a,"logical_class":c,"batch":b,
               "count":16,"scientific_head":local.compact.batches.HEAD,
               "activation_head":local.compact.batches.ACTIVATION,"graph_sha256":local.compact.batches.GRAPHS[a][1],
               "quality_exposed":False,"campaign_admission":False}
            local.job_scope(j,n)
            for key,val in (("batch",3),("count",17),("graph_sha256","x"),("quality_exposed",True),
                            ("campaign_admission",True),("dispatch_id","wrong")):
                bad=copy.deepcopy(j);bad[key]=val
                with self.assertRaises(ValueError):local.job_scope(bad,n)
