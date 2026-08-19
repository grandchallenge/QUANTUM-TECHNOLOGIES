from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "reference"
if str(REF) not in sys.path:
    sys.path.insert(0, str(REF))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


c90 = load_module("qtr_c90_exact_requal_001", REF / "qtr_c90_exact_requal_001.py")


def test_manifest_self_digest_authority_and_single_cap_amendment():
    m = c90.load_manifest()
    assert m["manifest_payload_sha256"] == c90.MANIFEST_PAYLOAD
    assert m["authority"]["human_steward_comment"] == 5336703933
    e = m["resource_envelope"]
    assert e["historical_peak_joint_table_entries"] == 1 << 20
    assert e["authorized_c90_peak_joint_table_entries"] == 100 * (1 << 20)
    assert e["only_amended_deterministic_cap"] == "max_peak_joint_table_entries"
    assert e["max_factor_table_entry_evaluations_per_algebra"] == 1 << 27
    assert e["max_retained_canonical_structural_nodes_or_entries_per_algebra"] == 1 << 22
    assert e["max_canonical_serialized_compiled_bytes_per_algebra"] == 512 * 1024 * 1024
    assert e["max_compilation_aop_events_per_algebra"] == 1 << 31


def test_protected_disabled_candidate_remains_disabled():
    row = c90.verify_disabled_candidate()
    job = row["jobs"][0]
    assert row["status"] == "FROZEN_DISABLED_PENDING_SEPARATE_SCIENTIFIC_AUTHORITY"
    assert job["enabled"] is False
    assert job["scientific_execution_authorized"] is False
    assert job["claim_boundary"]["physical_materialization_authorized"] is False


def test_frozen_validation_coordinates_precommitted():
    coords = c90.frozen_validation_coordinates(49)
    assert len(coords) == 307
    assert c90.digest(coords) == c90.VALIDATION_SET_SHA256
    assert coords[0] == 0
    assert coords[1:50] == [1 << i for i in range(49)]
    assert coords[50] == (1 << 49) - 1
    assert len(set(coords)) == 307


def test_new_aop_lower_bound_matches_protected_c72_ledger_when_known_nodes_added():
    import qldpc_scale_001a_math as m72
    code = m72.construct_code()
    audit = m72.order_audit(code["scopes"])
    ledger = c90.exact_static_ledger(
        code["scopes"], code["selector_basis_qubits"], audit["orders"]["min_fill"]
    )["exact_structural_counts"]
    protected_unique_nodes = 2_157_761
    protected_compile_aop_total = 20_339_963
    assert ledger["mandatory_compilation_aop_lower_bound"] + protected_unique_nodes == protected_compile_aop_total


def test_static_adjudication_fails_closed_on_unchanged_exact_cap():
    m = c90.load_manifest()
    cap = m["resource_envelope"]["max_factor_table_entry_evaluations_per_algebra"]
    ledger = {"exact_structural_counts": {
        "peak_joint_table_entries": 1,
        "factor_table_entry_evaluations": cap + 1,
        "mandatory_compilation_aop_lower_bound": 1,
        "node_intern_attempts": 1,
    }}
    result = c90.adjudicate_static(m, ledger)
    assert result["status"] == "C90_MEMORY_STORAGE_QUALIFICATION_FAILED"
    assert result["calibration_required"] is False
    assert result["phase_x_reachable"] is False


def test_phase_x_requires_exact_pass_receipt_same_session(tmp_path):
    m = c90.load_manifest()
    fail = {
        "status": "C90_MEMORY_STORAGE_QUALIFICATION_FAILED",
        "manifest_payload_sha256": c90.MANIFEST_PAYLOAD,
        "hosted_session_identity": "SESSION-A",
    }
    fail["payload_sha256"] = c90.digest(fail)
    path = tmp_path / "phase_m.json"
    path.write_text(json.dumps(fail), encoding="utf-8")
    with pytest.raises(ValueError, match="Phase X forbidden"):
        c90.require_phase_m_pass(m, path, "SESSION-A")

    passed = {
        "status": "C90_MEMORY_STORAGE_QUALIFIED_WITHIN_BOUND",
        "manifest_payload_sha256": c90.MANIFEST_PAYLOAD,
        "hosted_session_identity": "SESSION-A",
    }
    passed["payload_sha256"] = c90.digest(passed)
    path.write_text(json.dumps(passed), encoding="utf-8")
    with pytest.raises(ValueError, match="session mismatch"):
        c90.require_phase_m_pass(m, path, "SESSION-B")
    assert c90.require_phase_m_pass(m, path, "SESSION-A")["status"].endswith("WITHIN_BOUND")


def test_state_machine_has_no_recovery_edge_after_negative_phase_m():
    m = c90.load_manifest()
    machine = m["state_machine"]
    assert "M_FAIL" in machine["terminal"]
    assert "M_INDETERMINATE" in machine["terminal"]
    assert "M_FAIL" not in machine["transitions"]
    assert "M_INDETERMINATE" not in machine["transitions"]
    assert machine["post_outcome_mutation_edge_exists"] is False


def test_hosted_job_template_is_cpu_reference_and_render_only_session():
    job = json.loads((ROOT / "configs/compute/qtr_c90_exact_requal_001_job.json").read_text())
    assert job["scientific_execution_authorized"] is True
    assert job["scientific_backend"] == "cpu_reference"
    assert job["resource"] == {"variant": "CPU", "accelerator": None}
    assert job["hosted_session_identity"] == "__HOST_RENDERED__"
    assert job["manifest_payload_sha256"] == c90.MANIFEST_PAYLOAD
