import copy,json,math,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"reference"));sys.path.insert(0,str(ROOT/"ci"))
import downstream_atlas as da
import validate_downstream as vd
class DownstreamAtlasTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.registry=json.loads((ROOT/"registry/downstream-atlas.json").read_text())
 def reports(self):
  p=da.evaluate_registry(self.registry);return {k:{x["record_id"]:x for x in p[k]} for k in ("WP01","WP02","WP03")}
 def test_binomial_orbits(self):
  for r in self.reports()["WP01"].values():self.assertTrue(r["orbit_sizes_match_binomial"])
 def test_parity_four_boundaries(self):self.assertEqual(self.reports()["WP01"]["sym_parity_n4"]["boundary_count"],4)
 def test_exact_weight_two_boundaries(self):self.assertEqual(self.reports()["WP01"]["sym_exact_weight_2_n4"]["boundary_count"],2)
 def test_or_rank_kernel(self):
  rows=self.reports()["WP02"]["lin_or_marked_row_n4"]["by_hamming_weight"];self.assertEqual((rows[0]["rank"],rows[0]["kernel_dimension"]),(0,4));self.assertTrue(all((r["rank"],r["kernel_dimension"])==(1,3) for r in rows[1:]))
 def test_majority_singular_sign_loss(self):
  r=self.reports()["WP02"]["lin_majority_signed_scalar_n5"];self.assertTrue(r["signed_channel"]["semantically_sufficient"]);self.assertFalse(r["singular_value_channel"]["semantically_sufficient"]);self.assertEqual(r["singular_value_channel"]["cross_label_collision_pairs"],126)
 def test_or_certificate_pair(self):
  r=self.reports()["WP03"]["or_n4_star_span"];self.assertTrue(r["certificate_objectives_match"]);self.assertTrue(math.isclose(r["adversary_certificate"]["objective"],2.0))
 def test_bad_star_fails_closed(self):
  bad=copy.deepcopy(self.registry["WP03"][0]);bad["adversary_certificate"]["one_inputs"][0]="1100"
  with self.assertRaises(ValueError):da.evaluate_wp03(bad)
 def test_unknown_record_field_fails_closed(self):
  bad=copy.deepcopy(self.registry["WP02"][0]);bad["hidden_preprocessing"]="answer"
  with self.assertRaises(vd.ValidationError):vd.validate_wp02(bad)
if __name__=="__main__":unittest.main()
