from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_documentary_promotion_preserves_scientific_candidate_statuses():
    reg = load("registry/qtr-c90-exact-requal-001.json")
    ev = load("evidence/QTR-C90-EXACT-REQUAL-001-report.json")
    assert reg["experiments"][0]["status"] == "candidate_executable_not_promoted"
    assert ev["status"] == "candidate_executable_not_promoted"
    assert reg["experiments"][0]["outcome"] == "C90_MEMORY_STORAGE_QUALIFICATION_FAILED"
    assert ev["adjudication"]["primary_outcome"] == "C90_MEMORY_STORAGE_QUALIFICATION_FAILED"


def test_promotion_record_binds_exact_scientific_snapshot_and_authority():
    intake = load("reviews/QTR-C90-EXACT-REQUAL-REVIEW-001/intake.json")
    promo = load("reviews/QTR-C90-EXACT-REQUAL-REVIEW-001/promotion-record.json")
    assert intake["documentary_base_at_creation"] == "42e644571172f895025a819d9e91cd8fcd78cbb8"
    assert intake["reviewed_head"] == "d3215db1b22a95ba90c8e8901cc78dec83716e82"
    assert intake["promotion_authorization_comment"] == 5337464530
    assert promo["status"] == "referee_promoted_bounded"
    assert promo["scientific_status_strings_intentionally_unchanged"] is True
    snap = promo["reviewed_snapshot"]
    assert snap["manifest_blob_sha"] == "ca70abb3424e111d22282872b8bc9483e4cdf6ed"
    assert snap["registry_blob_sha"] == "b9a4866f6239634b973dfd22bda86e7ff87772bf"
    assert snap["evidence_blob_sha"] == "064b7ab32147f329a3893fd603cda501c7db641d"
    assert snap["evaluator_blob_sha"] == "70050138adca79468bb4b21920c3ef68b3145c39"
    assert snap["workflow_blob_sha"] == "3fe30828f74e11fad037ca185bfa216b1f52fbfb"
    assert snap["snapshot_preserved_byte_for_byte"] is True


def test_promoted_result_is_precalibration_ledger_failure_not_ram_claim():
    promo = load("reviews/QTR-C90-EXACT-REQUAL-REVIEW-001/promotion-record.json")
    scope = promo["promoted_scope"]
    assert scope["primary_outcome"] == "C90_MEMORY_STORAGE_QUALIFICATION_FAILED"
    assert scope["mandatory_reason"] == "EXACT_DETERMINISTIC_COMPILATION_CAP_CROSSED_PRECALIBRATION"
    assert scope["amended_peak_joint_table"]["pass"] is True
    assert scope["unchanged_factor_table_entry_evaluations"]["pass"] is False
    assert scope["unchanged_compilation_aop"]["definite_fail"] is True
    assert scope["host_memory_calibration_performed"] is False
    assert scope["physical_memory_question_reached"] is False
    assert scope["phase_x_reached"] is False
    assert scope["frozen_307_validation_reached"] is False


def test_documentary_text_preserves_wording_and_downstream_gates():
    wp = (ROOT / "work-packages/QTR-C90-EXACT-REQUAL-001.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    required = [
        "C90_X100_PEAK_ENTRY_REQUALIFICATION_INSUFFICIENT_UNDER_UNCHANGED_COMPILATION_LEDGER",
        "physical-memory question was not reached",
        "QEC-CIRCUIT-003",
        "QLDPC-FORGE",
    ]
    for phrase in required:
        assert phrase in wp or phrase in readme
    forbidden = "C90 does not fit in RAM"
    assert forbidden not in readme


def test_no_documentary_authority_for_accelerator_or_larger_rungs():
    promo = load("reviews/QTR-C90-EXACT-REQUAL-REVIEW-001/promotion-record.json")
    text = "\n".join(promo["excluded_scope"])
    assert "accelerator-native QEC" in text
    assert "C108/C144/C288/C784" in text
    assert "QEC-CIRCUIT-003" in text
    assert "QLDPC-FORGE" in text
