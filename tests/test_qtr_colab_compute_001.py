from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


matrix_mod = load_module("qtr_colab_run_matrix", ROOT / "scripts/colab_run_matrix.py")
probe_mod = load_module("qtr_colab_runtime_probe", ROOT / "reference/qtr_colab_runtime_probe.py")
requal_mod = load_module("qtr_compute_requal_001", ROOT / "reference/qtr_compute_requal_001.py")


def test_runtime_matrix_is_preparation_only_and_no_silent_substitution():
    matrix = matrix_mod.load_matrix(ROOT / "configs/compute/qtr_colab_runtime_probe_matrix.json")
    assert len(matrix["jobs"]) == 6
    assert {job["resource"]["variant"] for job in matrix["jobs"]} == {"CPU", "GPU", "TPU"}
    assert all(job["scientific_execution_authorized"] is False for job in matrix["jobs"])
    gpu = next(job for job in matrix["jobs"] if job["resource"]["accelerator"] == "T4")
    fake = {"observed_variant": "GPU", "observed_accelerator": "NVIDIA L4"}
    try:
        probe_mod.validate_requested_runtime(gpu, fake)
    except RuntimeError:
        pass
    else:
        raise AssertionError("T4 request accepted silent L4 substitution")


def test_c90_candidate_is_frozen_disabled():
    matrix = matrix_mod.load_matrix(ROOT / "configs/compute/qtr_c90_exact_candidate_matrix.json")
    assert matrix["status"] == "FROZEN_DISABLED_PENDING_SEPARATE_SCIENTIFIC_AUTHORITY"
    assert len(matrix["jobs"]) == 1
    job = matrix["jobs"][0]
    assert job["enabled"] is False
    assert job["scientific_execution_authorized"] is False
    assert job["required_authorization"]["status"] == "UNSATISFIED"


def test_x100_entry_count_arithmetic_preserves_temporal_boundary():
    assert requal_mod.peak_entries(18) == 1 << 19
    assert requal_mod.peak_entries(25) == 1 << 26
    assert requal_mod.multiplier_needed(25) == 64
    assert requal_mod.multiplier_needed(34) == 32768
    assert requal_mod.multiplier_needed(36) == 131072
    nominal = 100 * requal_mod.ORIGINAL_PEAK_CAP
    assert requal_mod.peak_entries(25) <= nominal
    assert requal_mod.peak_entries(34) > nominal


def test_payload_builder_excludes_hosted_outputs():
    payload = load_module("qtr_build_colab_payload", ROOT / "scripts/build_colab_payload.py")
    for rel in (
        "runs/hosted/x/result.json",
        ".artifacts/bootstrap/a.json",
        ".venv/bin/python",
        ".git/config",
        "__pycache__/x.pyc",
    ):
        path = ROOT / rel
        assert payload.include_path(path) is False


def test_work_package_keeps_accelerator_and_scientific_backend_distinct():
    text = (ROOT / "work-packages/QTR-COLAB-COMPUTE-001.md").read_text(encoding="utf-8")
    assert "Allocating a GPU or TPU does not cause them to execute on that accelerator." in text
    assert "separate exact-equivalence" in text
    assert "QEC-CIRCUIT-003" in text


def test_resume_requires_exact_job_digest_and_source_commit(tmp_path):
    old_root = matrix_mod.ROOT
    matrix_mod.ROOT = tmp_path
    try:
        job_path = tmp_path / "job.json"
        job_path.write_text('{"a":1}\n', encoding="utf-8")
        receipt_dir = tmp_path / "runs" / "hosted" / "X" / "001"
        receipt_dir.mkdir(parents=True)
        receipt_path = receipt_dir / "experiment_receipt.json"
        receipt_path.write_text(json.dumps({
            "status": "GREEN_ENGINEERING",
            "job_sha256": "stale",
            "source_commit": "HEAD",
        }), encoding="utf-8")
        assert matrix_mod.latest_green_receipt("X", job_path, "HEAD") is None
        receipt_path.write_text(json.dumps({
            "status": "GREEN_ENGINEERING",
            "job_sha256": matrix_mod.sha256_file(job_path),
            "source_commit": "OLD",
        }), encoding="utf-8")
        assert matrix_mod.latest_green_receipt("X", job_path, "HEAD") is None
        receipt_path.write_text(json.dumps({
            "status": "GREEN_ENGINEERING",
            "job_sha256": matrix_mod.sha256_file(job_path),
            "source_commit": "HEAD",
        }), encoding="utf-8")
        assert matrix_mod.latest_green_receipt("X", job_path, "HEAD") == receipt_path
    finally:
        matrix_mod.ROOT = old_root


def test_host_runner_requires_receipt_and_bundle_before_green():
    text = (ROOT / "scripts/colab_run_job.sh").read_text(encoding="utf-8")
    assert "missing experiment receipt" in text
    assert "missing output bundle" in text
    assert "receipt source commit mismatch" in text
    assert "receipt job digest mismatch" in text