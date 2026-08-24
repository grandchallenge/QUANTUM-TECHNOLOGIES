from __future__ import annotations

import inspect
import os
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "reference"
if str(REFERENCE) not in sys.path:
    sys.path.insert(0, str(REFERENCE))

import tcm_c72_interface_001 as C72
import tcm_c72_interface_001_parallel as P


def fake_context() -> dict:
    return {"code": {"hz": [0]}, "fake": True}


def fake_record(_context: dict, _syndrome: int, logical_class: int) -> dict:
    logical_class = int(logical_class)
    return {
        "logical_class": logical_class,
        "selector_coordinate": logical_class,
        "score_sum_product": 4096 - logical_class,
        "score_soft_tropical": logical_class,
        "minimum_weight": logical_class & 7,
        "minimum_representative": logical_class,
        "canonical_key": logical_class,
    }


def test_parallel_decoder_signature_leaks_no_injected_error() -> None:
    names = set(inspect.signature(P.parallel_decode_c72_syndrome).parameters)
    assert names == {"full_hz_syndrome", "channel_metadata", "context"}
    assert "error" not in names
    assert "injected_error" not in names


def test_parallel_fallback_preserves_exact_4096_class_order_and_decision() -> None:
    with patch.object(C72, "c72_class_record", side_effect=fake_record), patch.dict(
        os.environ, {"TCM_C72_WORKERS": "1"}, clear=False
    ):
        observed = P.parallel_decode_c72_syndrome(
            0, C72.CHANNEL_METADATA, context=fake_context()
        )
    records = [fake_record(fake_context(), 0, logical) for logical in range(4096)]
    expected = C72.decision_from_class_records(records, 72)
    assert observed["status"] == "CORRECTION_VALUED"
    assert observed["logical_classes_evaluated"] == 4096
    assert observed["decisions"] == expected


def test_parallel_wrapper_rejects_channel_drift_before_work() -> None:
    try:
        P.parallel_decode_c72_syndrome(
            0, {"kind": "BSC", "p": "0.2"}, context=fake_context()
        )
    except ValueError as exc:
        assert "channel metadata drift" in str(exc)
    else:
        raise AssertionError("channel drift was accepted")


def test_parallel_wrapper_source_contains_no_outcome_tuning() -> None:
    source = inspect.getsource(P.parallel_decode_c72_syndrome)
    assert "range(1 << 12)" in source
    assert "pool.map" in source
    for forbidden in ("prune", "beam", "approx", "threshold", "topk", "top_k"):
        assert forbidden not in source.lower()
