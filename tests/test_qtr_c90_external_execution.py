#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "qtr_external",
    ROOT / "scripts/qtr_c90_external_execution.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class QTRExternalExecutionTests(unittest.TestCase):
    def test_profile_exact_domain(self) -> None:
        profile = mod.load_json(mod.PROFILE_PATH)
        mod.validate_profile(profile)
        units = mod.expected_units(profile)
        self.assertEqual(768, len(units))
        self.assertIn("sum_product_bsc_p_0_1/class-000", units)
        self.assertIn("min_plus_hamming/class-255", units)

    def test_materialization_is_provider_bound_and_has_768_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "run"
            args = SimpleNamespace(
                provider_class="slurm",
                adapter="gcl-slurm-v1",
                source_payload_sha256="1" * 64,
                parallelism=48,
                output=str(out),
            )
            mod.materialize(args)
            manifest = mod.load_json(out / "MANIFEST.json")
            self.assertEqual("slurm", manifest["provider"]["class"])
            self.assertFalse(manifest["provider"]["repository_write_credentials"])
            self.assertFalse(manifest["operational_parameters"]["github_hosted_scientific_execution"])
            self.assertEqual(768, len(list((out / "jobs").glob("*.json"))))
            self.assertLessEqual(manifest["operational_parameters"]["parallelism_ceiling"], 48)

    def test_parallelism_is_capped_by_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "run"
            args = SimpleNamespace(
                provider_class="other_external",
                adapter="provider-neutral-v1",
                source_payload_sha256="2" * 64,
                parallelism=768,
                output=str(out),
            )
            mod.materialize(args)
            manifest = mod.load_json(out / "MANIFEST.json")
            self.assertEqual(48, manifest["operational_parameters"]["parallelism_ceiling"])

    def test_receipt_rejects_promotion_and_repository_mutation(self) -> None:
        manifest = {
            "source": {"commit": "0" * 40, "source_payload_sha256": "1" * 64},
            "provider": {"class": "slurm", "adapter": "gcl-slurm-v1"},
            "retry_policy": {"max_attempts": 2},
        }
        base = {
            "record_type": "GCL_EXTERNAL_EXECUTION_RECEIPT",
            "manifest_sha256": "a" * 64,
            "source_commit": "0" * 40,
            "source_payload_sha256": "1" * 64,
            "provider": {"class": "slurm", "adapter": "gcl-slurm-v1", "execution_id": "1", "attempt": 1},
            "status": "SUCCESS",
            "returncode": 0,
            "scientific_semantics_changed": False,
            "promotion_claim": False,
            "repository_mutation_performed": False,
        }
        bad = dict(base)
        bad["promotion_claim"] = True
        with self.assertRaises(mod.ExternalExecutionError):
            mod._validate_receipt_common(bad, manifest, "a" * 64)
        bad = dict(base)
        bad["repository_mutation_performed"] = True
        with self.assertRaises(mod.ExternalExecutionError):
            mod._validate_receipt_common(bad, manifest, "a" * 64)

    def test_grandfathered_runs_are_not_cancelled_by_profile(self) -> None:
        profile = mod.load_json(mod.PROFILE_PATH)
        self.assertTrue(profile["migration"]["current_github_execution_grandfathered"])
        self.assertFalse(profile["migration"]["cancel_current_run_for_migration"])
        self.assertEqual(
            [35402858866, 35402858883, 35402858934],
            profile["migration"]["grandfathered_workflow_runs"],
        )


if __name__ == "__main__":
    unittest.main()
