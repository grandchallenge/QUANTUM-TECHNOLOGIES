#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "reference/tcm_qdec_compare_001.py"
SPEC = importlib.util.spec_from_file_location("tcm_qdec_compare_001_tested", PATH)
M = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(M)


class Compare001StaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = M.load_manifest()

    def test_manifest_identity_and_authority(self):
        self.assertEqual(
            self.manifest["manifest_payload_sha256"],
            "c68830f40733cde6957713060cec35adf317c75572cc960610c07c4d0e24d1e2",
        )
        self.assertEqual(self.manifest["authority"]["authorization_comment"], 5320400759)
        self.assertEqual(self.manifest["authority"]["execution_issue"], 71)

    def test_c18_protected_corpus_and_tcm_rows(self):
        c18 = self.manifest["c18_protected"]
        self.assertEqual(
            c18["fixture_002"]["corpus_sha256"],
            "260b1a43cf1d777f28c475918e91a5f7cefc5d28a2bfb556338f7e30058f58a8",
        )
        self.assertEqual(c18["fixture_002"]["corpus_size"], 4048)
        self.assertEqual(c18["tcm_qdec_001"]["decision_rows"]["sum_product_bsc_p_0_1"]["success_total"], 263)
        self.assertEqual(c18["tcm_qdec_001"]["decision_rows"]["soft_tropical_base_2"]["success_total"], 262)
        self.assertEqual(c18["tcm_qdec_001"]["decision_rows"]["min_plus_hamming"]["tie_envelope"], [218, 263])

    def test_large_corpus_digests(self):
        expected = {
            72: (329, "23b49e39eafd70c9619f8837dfcb0046e13a1600cd7176d42a6018814f518050"),
            90: (347, "b053a27a9c346832d6008987e204c88162dc1797e0367b38705861049059e086"),
        }
        for n, (count, sha) in expected.items():
            records = M.generate_large_corpus_records(n, self.manifest)
            self.assertEqual(len(records), count)
            self.assertEqual(M.digest(records), sha)
            self.assertEqual(records[0]["role"], "zero")
            self.assertTrue(all(records[i + 1]["role"] == "unit" for i in range(n)))

    def test_large_corpus_seed_or_probability_drift_fails(self):
        for field, replacement in (("seed", "drift"), ("sha256", "0" * 64)):
            mutated = copy.deepcopy(self.manifest)
            mutated["surfaces"]["C72"]["corpus"][field] = replacement
            mutated.pop("manifest_payload_sha256", None)
            mutated["manifest_payload_sha256"] = M.digest(mutated)
            with tempfile.TemporaryDirectory() as tmp:
                p = Path(tmp) / "manifest.json"
                p.write_text(json.dumps(mutated), encoding="utf-8")
                with self.assertRaises(ValueError):
                    M.load_manifest(p)

    def test_pure_bp_rows_are_separate_from_osd_row(self):
        rows = self.manifest["conventional_implementation"]["rows"]
        self.assertEqual(rows["BP_MIN_SUM"]["python_class"], "ldpc.bp_decoder")
        self.assertFalse(rows["BP_MIN_SUM"]["osd_present"])
        self.assertEqual(rows["BP_SUM_PRODUCT"]["python_class"], "ldpc.bp_decoder")
        self.assertFalse(rows["BP_SUM_PRODUCT"]["osd_present"])
        self.assertEqual(rows["BP_OSD_CS_7"]["python_class"], "ldpc.bposd_decoder")
        self.assertEqual(rows["BP_OSD_CS_7"]["osd_order"], 7)

    def test_historical_package_lock(self):
        target = self.manifest["conventional_implementation"]["initial_compatibility_target"]
        self.assertEqual(target["ldpc"]["version"], "0.1.53")
        self.assertEqual(
            target["ldpc"]["upstream_commit"],
            "8e2cba3206cf639518164d8b409f7d21b17d0738",
        )
        self.assertEqual(
            target["ldpc"]["bp_decoder_source_blob"],
            "dbee68689c795bc2417166e2e25eb495fa4be5bb",
        )
        self.assertEqual(
            target["ldpc"]["bposd_decoder_source_blob"],
            "1e588ab70dbc684f45f36bbdeed524d0c98b70d0",
        )
        self.assertEqual(target["bposd"]["version"], "1.6")

    def test_sector_orientation_is_locked(self):
        sector = self.manifest["sector_semantics"]
        self.assertEqual(sector["decoder_parity_check"], "H_Z")
        self.assertEqual(sector["oracle_success"], "e XOR c belongs to rowspace(H_X)")
        self.assertEqual(sector["channel_probability_vector"], "constant BSC p=0.1 on every data coordinate")

    def test_larger_tcm_cells_remain_undefined_for_quality(self):
        self.assertEqual(
            self.manifest["surfaces"]["C72"]["tcm_status"],
            "SHARED_DECODER_INTERFACE_NOT_CERTIFIED",
        )
        self.assertEqual(
            self.manifest["surfaces"]["C90"]["tcm_status"],
            "NOT_REACHED_EXACT_COMPILATION_BOUND",
        )
        self.assertFalse(self.manifest["comparison_relation"]["cross_surface_aggregate_winner"])
        self.assertFalse(self.manifest["comparison_relation"]["missing_value_imputation"])

    def test_execution_envelope_and_no_retries(self):
        envelope = self.manifest["execution_envelope"]
        self.assertTrue(envelope["one_decode_invocation_per_input"])
        self.assertFalse(envelope["retry_on_failure_or_bad_outcome"])
        self.assertFalse(envelope["post_outcome_tuning"])
        self.assertEqual(envelope["max_iter_per_bp_invocation"], 10000)
        self.assertEqual(envelope["max_total_bp_iterations_by_surface"]["C18"], 40480000)

    def test_downstream_authority_remains_closed(self):
        boundary = self.manifest["claim_boundary"]
        self.assertFalse(boundary["qec_circuit_001_authorized"])
        self.assertFalse(boundary["qldpc_forge_authorized"])
        self.assertFalse(boundary["approximate_tcm"])
        self.assertFalse(boundary["general_decoder_superiority"])
        self.assertFalse(boundary["runtime_or_memory_superiority"])

    def test_static_replay(self):
        receipt = M.validate_static(self.manifest)
        self.assertEqual(receipt["static_status"], "PASS")
        self.assertEqual(receipt["corpora"]["C72"]["size"], 329)
        self.assertEqual(receipt["corpora"]["C90"]["size"], 347)


if __name__ == "__main__":
    unittest.main()
