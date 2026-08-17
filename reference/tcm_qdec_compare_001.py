#!/usr/bin/env python3
"""TCM-QDEC-COMPARE-001 bounded shared-interface decoder comparison."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import qldpc_fixture_002 as F2
import tcm_qdec_001 as T1
import qldpc_scale_001b as S1B

EXPERIMENT_ID = "TCM-QDEC-COMPARE-001"
EVALUATOR_VERSION = "0.1.0"
MANIFEST_PATH = ROOT / "registry/tcm-qdec-compare-001-manifest.json"
MANIFEST_PAYLOAD = "c68830f40733cde6957713060cec35adf317c75572cc960610c07c4d0e24d1e2"
MANIFEST_COMMIT = "a187bcbd52d032ab62c85d5aa9c4e5d44576b45b"

C18_TCM_EXPECTED = {
    "sum_product_bsc_p_0_1": {
        "decision_sha256": "05dd32573ee965ce96caf707de3541f8be74b49317ad46b7929ef7dcf3bf64fc",
        "success_total": 263,
        "tie_envelope": [263, 263],
    },
    "soft_tropical_base_2": {
        "decision_sha256": "ea2a96e3878758cd2daebd28673d943c27740a3e1c3579d8429a8a658e567393",
        "success_total": 262,
        "tie_envelope": [262, 262],
    },
    "min_plus_hamming": {
        "decision_sha256": "88a9a766b64c7e476ac5bb4da877a2b1f6d4e88cee88cde6ea7461cc74179f3f",
        "success_total": 226,
        "tie_envelope": [218, 263],
    },
}


def cbytes(x: Any) -> bytes:
    return json.dumps(
        x, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def digest(x: Any) -> str:
    return hashlib.sha256(cbytes(x)).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    data = load_json(path)
    claimed = data.pop("manifest_payload_sha256")
    observed = digest(data)
    data["manifest_payload_sha256"] = claimed
    if claimed != MANIFEST_PAYLOAD or observed != MANIFEST_PAYLOAD:
        raise ValueError("COMPARE-001 manifest self-digest mismatch")
    if data["authority"] != {
        "authorization_comment": 5320400759,
        "authorization_issue": 70,
        "execution_issue": 71,
        "protected_start_main": "d2cef907ee3c1ae1d56f0625c706a87d35b3c89f",
        "referee_comment": 5320307737,
    }:
        raise ValueError("COMPARE-001 authority drift")
    if data["surfaces"]["C72"]["tcm_status"] != "SHARED_DECODER_INTERFACE_NOT_CERTIFIED":
        raise ValueError("C72 TCM status drift")
    if data["surfaces"]["C90"]["tcm_status"] != "NOT_REACHED_EXACT_COMPILATION_BOUND":
        raise ValueError("C90 TCM status drift")
    if data["claim_boundary"]["qec_circuit_001_authorized"] is not False:
        raise ValueError("QEC-CIRCUIT-001 authority drift")
    return data


def generate_large_corpus_records(n: int, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    info = manifest["surfaces"][f"C{n}"]["corpus"]
    seed = info["seed"].encode("ascii")
    threshold = manifest["corpus_generator"]["threshold_uint64"]
    records: list[dict[str, Any]] = [
        {"index": 0, "role": "zero", "weight": 0, "error": "0" * n}
    ]
    for coordinate in range(n):
        chars = ["0"] * n
        chars[coordinate] = "1"
        records.append(
            {
                "index": len(records),
                "role": "unit",
                "coordinate": coordinate,
                "weight": 1,
                "error": "".join(chars),
            }
        )
    seen = {x["error"] for x in records}
    counter = 0
    accepted = 0
    while accepted < 256:
        chars = []
        for coordinate in range(n):
            h = hashlib.sha256(
                seed + counter.to_bytes(8, "big") + coordinate.to_bytes(4, "big")
            ).digest()
            u = int.from_bytes(h[:8], "big")
            chars.append("1" if u < threshold else "0")
        bitstring = "".join(chars)
        if bitstring not in seen:
            seen.add(bitstring)
            records.append(
                {
                    "index": len(records),
                    "role": "bsc_p_0_1",
                    "counter": counter,
                    "weight": bitstring.count("1"),
                    "error": bitstring,
                }
            )
            accepted += 1
        counter += 1
    if len(records) != info["size"]:
        raise AssertionError(f"C{n} corpus size mismatch")
    if digest(records) != info["sha256"]:
        raise AssertionError(f"C{n} corpus digest mismatch")
    if counter != info["candidate_counters_consumed"]:
        raise AssertionError(f"C{n} counter consumption mismatch")
    return records


def materialize_corpora(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for n in (72, 90):
        records = generate_large_corpus_records(n, manifest)
        path = ROOT / manifest["surfaces"][f"C{n}"]["corpus"]["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        out[f"C{n}"] = {
            "path": str(path.relative_to(ROOT)),
            "size": len(records),
            "sha256": digest(records),
            "canonical_serialized_bytes": len(cbytes(records)),
        }
    return out


def int_rows_to_numpy(rows: list[int], n: int):
    import numpy as np
    return np.array(
        [[(row >> q) & 1 for q in range(n)] for row in rows], dtype=np.uint8
    )


def code_from_001b(n: int) -> tuple[list[int], list[int], int]:
    manifest_001b = S1B.load_manifest(
        ROOT / "registry/qldpc-scale-001b-ladder-manifest.json"
    )
    cfg = next(x for x in manifest_001b["ladder"] if x["n"] == n)
    code = S1B.construct_rung(cfg)
    if code["n"] != n:
        raise AssertionError("001B code reconstruction mismatch")
    return code["hx"], code["hz"], n


def c18_context() -> tuple[list[int], list[int], set[int], list[int], dict[str, dict[int, int]], dict[str, Any]]:
    fixture1 = load_json(ROOT / "evidence/QLDPC-FIXTURE-001-report.json")
    fixture2 = load_json(ROOT / "evidence/QLDPC-FIXTURE-002-report.json")
    promotion2 = load_json(ROOT / "reviews/QTR-QLDPC-REVIEW-002/promotion-record.json")
    rows, stabilizers, n = T1.validate_predecessors(fixture1, fixture2, promotion2)
    if n != 18:
        raise AssertionError("C18 n drift")
    corpus = F2.make_corpus(n, 4)
    tables, diagnostics, quotient_ties, coset_keys = T1.infer_tables(rows, stabilizers, n)
    tcm_tables = tables["stabilizer_coset_aggregate"]
    tie_report = T1.tie_sensitivity(corpus, rows, coset_keys, quotient_ties)
    for algebra, expected in C18_TCM_EXPECTED.items():
        if diagnostics["stabilizer_coset_aggregate"][algebra]["decision_table_sha256"] != expected["decision_sha256"]:
            raise AssertionError(f"{algebra} decision digest drift")
        result, _ = T1.classify(corpus, rows, stabilizers, tcm_tables[algebra])
        if result["success_total"] != expected["success_total"]:
            raise AssertionError(f"{algebra} success total drift")
        envelope = tie_report[algebra]["frozen_corpus_success_count_envelope_over_winning_class_ties"]
        if [envelope["min"], envelope["max"]] != expected["tie_envelope"]:
            raise AssertionError(f"{algebra} tie envelope drift")
    hx = [F2.b2i(x) for x in fixture1["construction"]["hx"]]
    hz = [F2.b2i(x) for x in fixture1["construction"]["hz"]]
    return hx, hz, stabilizers, corpus, tcm_tables, tie_report


def package_receipt() -> dict[str, Any]:
    import ldpc
    ldpc_version = str(getattr(ldpc, "__version__", "")).strip()
    metadata_ldpc = importlib.metadata.version("ldpc")
    metadata_bposd = importlib.metadata.version("bposd")
    if ldpc_version != "0.1.53" or metadata_ldpc != "0.1.53" or metadata_bposd != "1.6":
        raise RuntimeError(
            f"pinned package mismatch: ldpc attr={ldpc_version!r}, "
            f"ldpc metadata={metadata_ldpc!r}, bposd={metadata_bposd!r}"
        )
    if not hasattr(ldpc, "bp_decoder") or not hasattr(ldpc, "bposd_decoder"):
        raise RuntimeError("pinned ldpc decoder interfaces missing")
    return {
        "ldpc_module_version": ldpc_version,
        "ldpc_metadata_version": metadata_ldpc,
        "bposd_metadata_version": metadata_bposd,
        "bp_decoder_module": ldpc.bp_decoder.__module__,
        "bp_decoder_name": ldpc.bp_decoder.__name__,
        "bposd_decoder_module": ldpc.bposd_decoder.__module__,
        "bposd_decoder_name": ldpc.bposd_decoder.__name__,
    }


def make_decoder(method: str, h_numpy, n: int):
    import ldpc
    import numpy as np
    common = {
        "channel_probs": np.full(n, 0.1, dtype=float),
        "max_iter": 10000,
        "input_vector_type": "syndrome",
    }
    if method == "BP_MIN_SUM":
        return ldpc.bp_decoder(
            h_numpy, bp_method="ms", ms_scaling_factor=0, **common
        )
    if method == "BP_SUM_PRODUCT":
        return ldpc.bp_decoder(
            h_numpy, bp_method="ps", ms_scaling_factor=0, **common
        )
    if method == "BP_OSD_CS_7":
        return ldpc.bposd_decoder(
            h_numpy,
            bp_method="ms",
            ms_scaling_factor=0,
            osd_method="osd_cs",
            osd_order=7,
            **common,
        )
    raise ValueError(method)


def certify_decoder_interface(method: str, decoder: Any) -> dict[str, Any]:
    expected_class = "bp_decoder" if method != "BP_OSD_CS_7" else "bposd_decoder"
    observed_class = decoder.__class__.__name__
    if observed_class != expected_class:
        raise RuntimeError(f"{method} class mismatch: {observed_class}")
    receipt = {
        "status": "CERTIFIED",
        "class": observed_class,
        "bp_method": str(decoder.bp_method),
        "max_iter": int(decoder.max_iter),
        "input_vector_type": "syndrome",
        "iter_property_accessible": hasattr(decoder, "iter"),
        "converge_property_accessible": hasattr(decoder, "converge"),
    }
    if int(decoder.max_iter) != 10000:
        raise RuntimeError(f"{method} max_iter drift")
    if method == "BP_MIN_SUM":
        if str(decoder.bp_method) != "minimum_sum_log":
            raise RuntimeError("BP_MIN_SUM internal method drift")
        if hasattr(decoder, "osd_order") or hasattr(decoder, "osdw_decoding"):
            raise RuntimeError("BP_MIN_SUM unexpectedly exposes OSD path")
        receipt["osd_absent_by_class"] = True
    elif method == "BP_SUM_PRODUCT":
        if str(decoder.bp_method) != "product_sum":
            raise RuntimeError("BP_SUM_PRODUCT internal method drift")
        if hasattr(decoder, "osd_order") or hasattr(decoder, "osdw_decoding"):
            raise RuntimeError("BP_SUM_PRODUCT unexpectedly exposes OSD path")
        receipt["osd_absent_by_class"] = True
    else:
        if str(decoder.bp_method) != "minimum_sum_log":
            raise RuntimeError("BP_OSD BP method drift")
        if str(decoder.osd_method) != "osd_cs" or int(decoder.osd_order) != 7:
            raise RuntimeError("BP_OSD configuration drift")
        receipt["osd_method"] = str(decoder.osd_method)
        receipt["osd_order"] = int(decoder.osd_order)
    return receipt


def decode_surface(
    method: str,
    hx: list[int],
    hz: list[int],
    corpus: list[int],
    n: int,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[bool | None]]:
    import numpy as np

    h_numpy = int_rows_to_numpy(hz, n)
    decoder = make_decoder(method, h_numpy, n)
    interface = certify_decoder_interface(method, decoder)
    stabilizers = F2.span(hx)
    rank_hz = len(F2.basis(hz))
    osd_nominal = (n - rank_hz) + math.comb(7, 2) if method == "BP_OSD_CS_7" else None

    results: list[dict[str, Any]] = []
    outcomes: list[bool | None] = []
    totals = {
        "inputs": len(corpus),
        "correction_valued": 0,
        "declared_failures": 0,
        "oracle_success": 0,
        "oracle_failure": 0,
        "syndrome_consistent": 0,
        "syndrome_inconsistent": 0,
        "bp_iterations_total": 0,
        "bp_converged_count": 0,
        "bp_nonconverged_count": 0,
        "osd_invocation_count": 0,
        "osd_nominal_candidates_total": 0,
        "correction_weight_total": 0,
    }
    shell: dict[str, dict[str, int]] = {}

    for index, error in enumerate(corpus):
        syn = F2.syndrome(error, hz)
        syn_np = np.array([(syn >> i) & 1 for i in range(len(hz))], dtype=np.uint8)
        try:
            correction_np = decoder.decode(syn_np)
            correction = sum(
                (int(bit) & 1) << i for i, bit in enumerate(correction_np.tolist())
            )
            iterations = int(decoder.iter)
            converged = bool(int(decoder.converge))
            consistent = F2.syndrome(correction, hz) == syn
            correct = consistent and ((error ^ correction) in stabilizers)
            osd_invoked = method == "BP_OSD_CS_7" and not converged
            totals["correction_valued"] += 1
            totals["oracle_success" if correct else "oracle_failure"] += 1
            totals["syndrome_consistent" if consistent else "syndrome_inconsistent"] += 1
            totals["bp_iterations_total"] += iterations
            totals["bp_converged_count" if converged else "bp_nonconverged_count"] += 1
            totals["correction_weight_total"] += correction.bit_count()
            if osd_invoked:
                totals["osd_invocation_count"] += 1
                totals["osd_nominal_candidates_total"] += int(osd_nominal)
            outcomes.append(correct)
            record = {
                "index": index,
                "status": "CORRECTION_VALUED",
                "error": F2.i2b(error, n),
                "error_weight": error.bit_count(),
                "syndrome": F2.i2b(syn, len(hz)),
                "correction": F2.i2b(correction, n),
                "correction_weight": correction.bit_count(),
                "syndrome_consistent": consistent,
                "oracle_correct": correct,
                "bp_iterations": iterations,
                "bp_converged": converged,
                "osd_invoked": osd_invoked,
                "osd_nominal_candidates": int(osd_nominal) if osd_invoked else 0,
            }
        except Exception as exc:
            totals["declared_failures"] += 1
            outcomes.append(None)
            record = {
                "index": index,
                "status": "DECLARED_FAILURE",
                "error": F2.i2b(error, n),
                "error_weight": error.bit_count(),
                "syndrome": F2.i2b(syn, len(hz)),
                "exception_class": exc.__class__.__name__,
                "exception_message": str(exc),
            }
        results.append(record)
        w = str(error.bit_count())
        b = shell.setdefault(w, {"inputs": 0, "correction_valued": 0, "oracle_success": 0})
        b["inputs"] += 1
        if record["status"] == "CORRECTION_VALUED":
            b["correction_valued"] += 1
            b["oracle_success"] += int(record["oracle_correct"])

    if totals["bp_iterations_total"] > len(corpus) * 10000:
        raise AssertionError(f"{method} BP iteration budget exceeded")

    result_digest = digest(results)
    return {
        "configuration_status": "CERTIFIED",
        "interface": interface,
        "execution_status": "COMPLETED",
        "totals": totals,
        "success_by_error_weight": shell,
        "result_records_sha256": result_digest,
        "result_record_count": len(results),
        "osd_nominal_candidates_per_invocation": osd_nominal,
        "universal_operation_count": "NOT_DEFINED",
        "timing_authoritative": False,
    }, results, outcomes


def run_surface_method(
    method: str,
    hx: list[int],
    hz: list[int],
    corpus: list[int],
    n: int,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[bool | None]]:
    try:
        return decode_surface(method, hx, hz, corpus, n)
    except (TypeError, ValueError, AttributeError, RuntimeError) as exc:
        return (
            {
                "configuration_status": "BASELINE_INTERFACE_NOT_CERTIFIED",
                "interface": {
                    "status": "BASELINE_INTERFACE_NOT_CERTIFIED",
                    "exception_class": exc.__class__.__name__,
                    "exception_message": str(exc),
                },
                "execution_status": "NOT_REACHED_INTERFACE_NOT_CERTIFIED",
                "totals": {
                    "inputs": len(corpus),
                    "correction_valued": 0,
                    "declared_failures": 0,
                    "oracle_success": 0,
                    "oracle_failure": 0,
                    "syndrome_consistent": 0,
                    "syndrome_inconsistent": 0,
                    "bp_iterations_total": 0,
                    "bp_converged_count": 0,
                    "bp_nonconverged_count": 0,
                    "osd_invocation_count": 0,
                    "osd_nominal_candidates_total": 0,
                    "correction_weight_total": 0,
                },
                "success_by_error_weight": {},
                "result_records_sha256": digest([]),
                "result_record_count": 0,
                "osd_nominal_candidates_per_invocation": None,
                "universal_operation_count": "NOT_DEFINED",
                "timing_authoritative": False,
            },
            [],
            [None] * len(corpus),
        )


def tcm_c18_rows(
    corpus: list[int],
    rows: list[int],
    stabilizers: set[int],
    tables: dict[str, dict[int, int]],
    tie_report: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, list[bool]]]:
    out: dict[str, Any] = {}
    outcomes: dict[str, list[bool]] = {}
    for algebra in ("sum_product_bsc_p_0_1", "soft_tropical_base_2", "min_plus_hamming"):
        result, bools = T1.classify(corpus, rows, stabilizers, tables[algebra])
        outcomes[algebra] = bools
        env = tie_report[algebra]["frozen_corpus_success_count_envelope_over_winning_class_ties"]
        out[algebra] = {
            "status": "CORRECTION_VALUED_PROTECTED_DECISIONS",
            "success_total": result["success_total"],
            "failure_total": result["failure_total"],
            "success_by_error_weight": result["success_by_error_weight"],
            "failure_modes": result["failure_modes"],
            "decision_sha256": C18_TCM_EXPECTED[algebra]["decision_sha256"],
            "tie_envelope": [env["min"], env["max"]],
        }
    return out, outcomes


def pairwise_quality(
    left_name: str,
    left_outcomes: list[bool | None],
    right_name: str,
    right_outcomes: list[bool | None],
) -> dict[str, Any]:
    domain = [
        i for i, (a, b) in enumerate(zip(left_outcomes, right_outcomes))
        if a is not None and b is not None
    ]
    left_success = sum(bool(left_outcomes[i]) for i in domain)
    right_success = sum(bool(right_outcomes[i]) for i in domain)
    return {
        "left": left_name,
        "right": right_name,
        "matched_correction_valued_domain_size": len(domain),
        "left_success_on_domain": left_success,
        "right_success_on_domain": right_success,
        "left_only_success": sum(
            bool(left_outcomes[i]) and not bool(right_outcomes[i]) for i in domain
        ),
        "right_only_success": sum(
            bool(right_outcomes[i]) and not bool(left_outcomes[i]) for i in domain
        ),
        "same_outcome": sum(
            bool(left_outcomes[i]) == bool(right_outcomes[i]) for i in domain
        ),
        "success_difference_left_minus_right": left_success - right_success,
        "scope": "C18_MATCHED_CELL_ONLY",
    }


def evaluate(manifest: dict[str, Any]) -> dict[str, Any]:
    package = package_receipt()
    corpus_receipts = materialize_corpora(manifest)

    hx18, hz18, stabilizers18, corpus18, tcm_tables, tie_report = c18_context()
    tcm_rows, tcm_outcomes = tcm_c18_rows(
        corpus18, hz18, stabilizers18, tcm_tables, tie_report
    )

    conventional_rows = ["BP_MIN_SUM", "BP_OSD_CS_7", "BP_SUM_PRODUCT"]
    surfaces: dict[str, Any] = {
        "C18": {
            "role": "matched_quality_head_to_head",
            "tcm": tcm_rows,
            "historical_anchors": {
                "exact_lookup_success_total": 240,
                "greedy_success_total": 125,
            },
            "conventional": {},
            "pairwise_quality": [],
        },
        "C72": {
            "role": "conventional_reach_status_only",
            "tcm": {"status": "SHARED_DECODER_INTERFACE_NOT_CERTIFIED"},
            "conventional": {},
            "quality_comparison_with_tcm": "COMPARISON_CELL_UNDEFINED",
        },
        "C90": {
            "role": "conventional_reach_status_only",
            "tcm": {"status": "NOT_REACHED_EXACT_COMPILATION_BOUND"},
            "conventional": {},
            "quality_comparison_with_tcm": "COMPARISON_CELL_UNDEFINED",
        },
    }

    conventional_outcomes_c18: dict[str, list[bool | None]] = {}
    detailed_records: dict[str, str] = {}

    for method in conventional_rows:
        summary, records, outcomes = run_surface_method(method, hx18, hz18, corpus18, 18)
        surfaces["C18"]["conventional"][method] = summary
        conventional_outcomes_c18[method] = outcomes
        detailed_records[f"C18/{method}"] = summary["result_records_sha256"]

    for n in (72, 90):
        hx, hz, _ = code_from_001b(n)
        records = generate_large_corpus_records(n, manifest)
        corpus = [F2.b2i(x["error"]) for x in records]
        for method in conventional_rows:
            summary, detail, _outcomes = run_surface_method(method, hx, hz, corpus, n)
            surfaces[f"C{n}"]["conventional"][method] = summary
            detailed_records[f"C{n}/{method}"] = summary["result_records_sha256"]

    for method, conv in conventional_outcomes_c18.items():
        for algebra, tcm in tcm_outcomes.items():
            surfaces["C18"]["pairwise_quality"].append(
                pairwise_quality(method, conv, f"TCM::{algebra}", tcm)
            )

    report: dict[str, Any] = {
        "experiment_id": EXPERIMENT_ID,
        "evaluator_version": EVALUATOR_VERSION,
        "status": "candidate_executable_not_promoted",
        "manifest": {
            "path": str(MANIFEST_PATH.relative_to(ROOT)),
            "first_commit": MANIFEST_COMMIT,
            "payload_sha256": MANIFEST_PAYLOAD,
        },
        "package_receipt": package,
        "corpus_receipts": corpus_receipts,
        "surfaces": surfaces,
        "detailed_result_record_digests": detailed_records,
        "comparison_relation": manifest["comparison_relation"],
        "claim_boundary": manifest["claim_boundary"],
        "adjudication": {
            "c18_shared_interface_completed": True,
            "c72_tcm_quality_defined": False,
            "c90_tcm_quality_defined": False,
            "cross_surface_winner_defined": False,
            "primary_outcome": "SHARED_INTERFACE_COMPARISON_COMPLETED_ON_C18",
            "secondary_outcomes": [
                "TCM_SHARED_DECODER_INTERFACE_NOT_CERTIFIED_ON_C72",
                "CONVENTIONAL_BASELINES_REACHED_C90__TCM_NOT_REACHED_EXACT_BOUND",
            ],
        },
    }
    report["payload_sha256"] = digest(report)
    return report


def validate_static(manifest: dict[str, Any]) -> dict[str, Any]:
    receipts = {}
    for n in (72, 90):
        records = generate_large_corpus_records(n, manifest)
        receipts[f"C{n}"] = {
            "size": len(records),
            "sha256": digest(records),
            "canonical_serialized_bytes": len(cbytes(records)),
        }
    return {
        "experiment_id": EXPERIMENT_ID,
        "manifest_payload_sha256": manifest["manifest_payload_sha256"],
        "corpora": receipts,
        "static_status": "PASS",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    p.add_argument("--output", type=Path)
    p.add_argument("--static-only", action="store_true")
    p.add_argument("--check-evidence", type=Path)
    args = p.parse_args()

    manifest = load_manifest(args.manifest)
    if args.static_only:
        observed = validate_static(manifest)
    else:
        observed = evaluate(manifest)

    if args.check_evidence:
        expected = load_json(args.check_evidence)
        if observed != expected:
            raise SystemExit("COMPARE-001 exact evidence replay mismatch")

    text = json.dumps(observed, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
