#!/usr/bin/env python3
"""Deterministic systems benchmark for QLDPC-FIXTURE-002.

Consumes the immutable QLDPC-FIXTURE-001 report, exhausts every single-sector
error of weight 0..4, and compares an exact coset-leader lookup with a simple
greedy syndrome-descent baseline. Wall-clock profiling is diagnostic only.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import platform
import sys
import time
from pathlib import Path
from typing import Any

EVALUATOR_VERSION = "0.1.0"
PREDECESSOR = {
    "fixture_id": "QLDPC-FIXTURE-001",
    "evidence_path": "evidence/QLDPC-FIXTURE-001-report.json",
    "evidence_payload_sha256": "6c2095f48762178bf0fe5c2b5fce8299261733912a1cccc7884d11f344718427",
    "scientific_merge_commit": "b899894cfe17680d556d32ff36e51683cd9f6b32",
    "promotion_merge_commit": "ab9a24a08d4e31b4d8cd18edb0ab1e5a7a0b3950",
}
CORPUS = {
    "kind": "exhaustive_hamming_weight_shells",
    "max_weight": 4,
    "expected_error_count": 4048,
    "sector_model": "code_capacity_single_css_sector",
    "randomness": "none",
}
DECODERS = {
    "exact_coset_lookup": {
        "kind": "minimum_weight_coset_leader_table",
        "expected_table_sha256": "96ce94c378b7b1fc5fe032fbd253aa932c1ca8abcb17b3d3c89b3ecda601da29",
        "role": "exact_reference",
    },
    "greedy_syndrome_descent": {
        "kind": "deterministic_best_syndrome_weight_reduction",
        "max_iterations": 18,
        "tie_break": "lowest_qubit_index",
        "accept_only_strict_reduction": True,
        "role": "simple_negative_capable_baseline",
    },
}
SOURCE_CONTEXT = {
    "archive": {
        "doi": "10.5281/zenodo.17706106",
        "version": "v1.1.3",
        "filename": "ZhideLu/Exp_BivariateBicycleCode-v1.1.3.zip",
        "md5": "95c3421c0301e07266357652f0179d2b",
    },
    "software": {
        "python": "3.10.14",
        "stim": "1.13.0",
        "ldpc": "0.1.53",
        "bposd": "1.6",
        "leaky": "0.2.2",
    },
    "experiment_decoder": {
        "file": "18_4_4/ErrorCorrection_for_experiment_18_4_4.py",
        "git_ref": "v1.1.3",
        "git_blob_sha": "df82b3a6aa17b969a50b1b143cc10136cb24547f",
        "bp_method": "ms",
        "max_iter": 10000,
        "osd_method": "osd_cs",
        "osd_order": 7,
        "ms_scaling_factor": 0,
        "executed_by_fixture": False,
    },
}
CLAIM_BOUNDARY = {
    "systems_benchmark_only": True,
    "experimental_data_reproduction_claim": False,
    "circuit_level_noise_claim": False,
    "bp_osd_performance_claim": False,
    "hardware_validation_claim": False,
    "threshold_claim": False,
    "cross_machine_latency_claim": False,
    "tcm_qdec_authorized": False,
    "qldpc_forge_authorized": False,
    "autonomous_search_authorized": False,
}


def cbytes(x: Any) -> bytes:
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode("utf-8")


def digest(x: Any) -> str:
    return hashlib.sha256(cbytes(x)).hexdigest()


canonical_digest = digest


def keys(d: dict[str, Any], expected: set[str], where: str) -> None:
    if set(d) != expected:
        raise ValueError(
            f"{where} key mismatch: missing={sorted(expected-set(d))}, "
            f"extra={sorted(set(d)-expected)}"
        )


def b2i(s: str) -> int:
    out = 0
    for i, ch in enumerate(s):
        if ch not in "01":
            raise ValueError("non-binary bitstring")
        if ch == "1":
            out |= 1 << i
    return out


def i2b(v: int, w: int) -> str:
    return "".join("1" if v & (1 << i) else "0" for i in range(w))


def basis(vectors: list[int]) -> list[int]:
    pivots: dict[int, int] = {}
    for original in vectors:
        v = original
        while v:
            p = v.bit_length() - 1
            if p in pivots:
                v ^= pivots[p]
            else:
                pivots[p] = v
                break
    return [pivots[p] for p in sorted(pivots, reverse=True)]


def span(vectors: list[int]) -> set[int]:
    out = {0}
    for v in basis(vectors):
        out |= {x ^ v for x in tuple(out)}
    return out


def syndrome(error: int, rows: list[int]) -> int:
    out = 0
    for i, row in enumerate(rows):
        if (error & row).bit_count() & 1:
            out |= 1 << i
    return out


def min_table(rows: list[int], n: int) -> tuple[dict[int, int], int]:
    target = 1 << len(basis(rows))
    table: dict[int, int] = {}
    considered = 0
    for weight in range(n + 1):
        for support in itertools.combinations(range(n), weight):
            error = sum(1 << q for q in support)
            considered += 1
            table.setdefault(syndrome(error, rows), error)
        if len(table) == target:
            break
    if len(table) != target:
        raise AssertionError("unreachable syndrome table target")
    return table, considered


def greedy(syn: int, columns: list[int], limit: int) -> tuple[int, int, int, int]:
    correction = 0
    residual = syn
    iterations = comparisons = 0
    while residual and iterations < limit:
        current = residual.bit_count()
        best_q = best_residual = None
        best_reduction = 0
        for q, column in enumerate(columns):
            candidate = residual ^ column
            comparisons += 1
            reduction = current - candidate.bit_count()
            if reduction > best_reduction:
                best_reduction = reduction
                best_q, best_residual = q, candidate
        if best_q is None:
            break
        correction ^= 1 << best_q
        residual = int(best_residual)
        iterations += 1
    return correction, residual, iterations, comparisons


def root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_benchmark(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    keys(data, {"registry_version", "benchmarks"}, "registry")
    if data["registry_version"] != "0.1.0" or not isinstance(data["benchmarks"], list):
        raise ValueError("invalid benchmark registry")
    matches = [x for x in data["benchmarks"] if x.get("fixture_id") == "QLDPC-FIXTURE-002"]
    if len(matches) != 1:
        raise ValueError("QLDPC-FIXTURE-002 must appear exactly once")
    b = matches[0]
    keys(b, {"claim_boundary", "corpus", "decoders", "fixture_id", "predecessor",
             "programme", "source_context", "status"}, "benchmark")
    if b["programme"] != "QTR" or b["status"] != "candidate_executable_not_promoted":
        raise ValueError("benchmark identity/status changed")
    for name, observed, expected in (
        ("predecessor", b["predecessor"], PREDECESSOR),
        ("corpus", b["corpus"], CORPUS),
        ("decoders", b["decoders"], DECODERS),
        ("source_context", b["source_context"], SOURCE_CONTEXT),
        ("claim_boundary", b["claim_boundary"], CLAIM_BOUNDARY),
    ):
        if observed != expected:
            raise ValueError(f"{name} unexpectedly changed")
    return b


def validate_predecessor(r: dict[str, Any]) -> tuple[list[int], list[int], set[int], int]:
    keys(r, {"claim_boundary", "construction", "evaluator_version", "exact_invariants",
             "fixture_id", "logical_basis", "payload_sha256", "reference_decoder",
             "removed_checks_source_record", "source", "status"}, "predecessor report")
    if r["fixture_id"] != PREDECESSOR["fixture_id"]:
        raise ValueError("predecessor fixture mismatch")
    if r["payload_sha256"] != PREDECESSOR["evidence_payload_sha256"]:
        raise ValueError("predecessor payload mismatch")
    unsigned = dict(r)
    unsigned.pop("payload_sha256")
    if digest(unsigned) != r["payload_sha256"]:
        raise ValueError("predecessor payload does not self-verify")
    if r["status"] != "candidate_executable_not_promoted":
        raise ValueError("immutable predecessor status changed")
    boundary = r["claim_boundary"]
    if boundary.get("exact_code_algebra_only") is not True:
        raise ValueError("predecessor exact algebra authority missing")
    for name in ("decoder_performance_claim", "circuit_level_noise_claim",
                 "hardware_validation_claim", "threshold_claim",
                 "fault_tolerant_architecture_claim", "qldpc_forge_authorized",
                 "tcm_qdec_authorized"):
        if boundary.get(name) is not False:
            raise ValueError(f"predecessor forbidden authority enabled: {name}")
    c, inv, ref = r["construction"], r["exact_invariants"], r["reference_decoder"]
    if c.get("family") != "bivariate_bicycle_css" or c.get("hx_equals_hz") is not True:
        raise ValueError("predecessor construction changed")
    if (inv.get("n"), inv.get("k"), inv.get("d"), inv.get("rank_hx"),
        inv.get("rank_hz")) != (18, 4, 4, 7, 7) or inv.get("css_commutes") is not True:
        raise ValueError("predecessor core invariants changed")
    if ref.get("table_sha256") != DECODERS["exact_coset_lookup"]["expected_table_sha256"]:
        raise ValueError("predecessor table identity changed")
    hx_bits, hz_bits = c.get("hx"), c.get("hz")
    if hx_bits != hz_bits or not isinstance(hx_bits, list) or len(hx_bits) != 9:
        raise ValueError("predecessor matrices changed")
    if any(not isinstance(row, str) or len(row) != 18 for row in hx_bits):
        raise ValueError("predecessor matrix width changed")
    hx, hz = [b2i(x) for x in hx_bits], [b2i(x) for x in hz_bits]
    stabilizers = span(hx)
    if len(basis(hx)) != 7 or len(basis(hz)) != 7 or len(stabilizers) != 128:
        raise ValueError("predecessor rank/span changed")
    return hx, hz, stabilizers, 18


def make_corpus(n: int, max_weight: int) -> list[int]:
    return [sum(1 << q for q in support)
            for weight in range(max_weight + 1)
            for support in itertools.combinations(range(n), weight)]


def score(corpus: list[int], corrections: list[int], residuals: list[int],
          stabilizers: set[int]) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for error, correction, residual in zip(corpus, corrections, residuals):
        bucket = out.setdefault(str(error.bit_count()), {"success": 0, "failure": 0, "total": 0})
        ok = residual == 0 and (error ^ correction) in stabilizers
        bucket["total"] += 1
        bucket["success" if ok else "failure"] += 1
    return out


def evaluate(b: dict[str, Any], predecessor: dict[str, Any]) -> dict[str, Any]:
    hx, hz, stabilizers, n = validate_predecessor(predecessor)
    corpus = make_corpus(n, b["corpus"]["max_weight"])
    if len(corpus) != b["corpus"]["expected_error_count"]:
        raise AssertionError("corpus size mismatch")
    corpus_records = [{"weight": e.bit_count(), "error": i2b(e, n)} for e in corpus]

    table, considered = min_table(hz, n)
    table_records = [{"syndrome": i2b(s, len(hz)), "correction": i2b(e, n),
                      "weight": e.bit_count()} for s, e in sorted(table.items())]
    table_sha = digest(table_records)
    if table_sha != b["decoders"]["exact_coset_lookup"]["expected_table_sha256"]:
        raise AssertionError("lookup table digest mismatch")

    input_syndromes = [syndrome(e, hz) for e in corpus]
    lookup_corrections = [table[s] for s in input_syndromes]
    lookup_residuals = [syndrome(e ^ c, hz) for e, c in zip(corpus, lookup_corrections)]
    lookup_counts = score(corpus, lookup_corrections, lookup_residuals, stabilizers)
    predecessor_counts = {
        w: {"success": v["success"], "failure": v["total"] - v["success"], "total": v["total"]}
        for w, v in predecessor["reference_decoder"]["exact_success_counts_by_error_weight"].items()
        if int(w) <= b["corpus"]["max_weight"]
    }
    if lookup_counts != predecessor_counts:
        raise AssertionError("lookup results diverge from Fixture 001")

    columns = [syndrome(1 << q, hz) for q in range(n)]
    gcorr, gres = [], []
    iterations = comparisons = stalled = 0
    hist: dict[str, int] = {}
    witnesses: list[dict[str, Any]] = []
    for error, syn in zip(corpus, input_syndromes):
        correction, residual, iters, comps = greedy(
            syn, columns, b["decoders"]["greedy_syndrome_descent"]["max_iterations"]
        )
        gcorr.append(correction); gres.append(residual)
        iterations += iters; comparisons += comps
        hist[str(iters)] = hist.get(str(iters), 0) + 1
        stalled += int(residual != 0)
        ok = residual == 0 and (error ^ correction) in stabilizers
        if not ok and len(witnesses) < 12:
            witnesses.append({
                "error_weight": error.bit_count(),
                "error": i2b(error, n),
                "input_syndrome": i2b(syn, len(hz)),
                "correction": i2b(correction, n),
                "residual_syndrome": i2b(residual, len(hz)),
                "residual_error_weight": (error ^ correction).bit_count(),
            })
    greedy_counts = score(corpus, gcorr, gres, stabilizers)

    same_correction = sum(a == b_ for a, b_ in zip(lookup_corrections, gcorr))
    same_outcome = 0
    for e, lc, lr, gc, gr in zip(corpus, lookup_corrections, lookup_residuals, gcorr, gres):
        same_outcome += (
            (lr == 0 and (e ^ lc) in stabilizers)
            == (gr == 0 and (e ^ gc) in stabilizers)
        )
    column_bits = [i2b(x, len(hz)) for x in columns]
    report: dict[str, Any] = {
        "fixture_id": b["fixture_id"],
        "evaluator_version": EVALUATOR_VERSION,
        "status": b["status"],
        "predecessor": b["predecessor"],
        "corpus": {
            **b["corpus"],
            "actual_error_count": len(corpus),
            "shell_sizes": {str(w): sum(e.bit_count() == w for e in corpus)
                            for w in range(b["corpus"]["max_weight"] + 1)},
            "corpus_sha256": digest(corpus_records),
            "canonical_serialized_bytes": len(cbytes(corpus_records)),
        },
        "benchmark_results": {
            "exact_coset_lookup": {
                "success_counts_by_error_weight": lookup_counts,
                "success_total": sum(x["success"] for x in lookup_counts.values()),
                "failure_total": sum(x["failure"] for x in lookup_counts.values()),
                "systems_counters": {
                    "setup_candidate_errors_considered": considered,
                    "setup_syndrome_evaluations": considered,
                    "decode_input_syndrome_evaluations": len(corpus),
                    "decode_table_lookups": len(corpus),
                    "table_entries": len(table),
                    "table_canonical_serialized_bytes": len(cbytes(table_records)),
                },
                "table_sha256": table_sha,
            },
            "greedy_syndrome_descent": {
                "success_counts_by_error_weight": greedy_counts,
                "success_total": sum(x["success"] for x in greedy_counts.values()),
                "failure_total": sum(x["failure"] for x in greedy_counts.values()),
                "systems_counters": {
                    "setup_column_syndrome_evaluations": len(columns),
                    "decode_input_syndrome_evaluations": len(corpus),
                    "decode_iterations_total": iterations,
                    "decode_candidate_comparisons": comparisons,
                    "stalled_with_nonzero_syndrome": stalled,
                    "iteration_histogram": dict(sorted(hist.items(), key=lambda x: int(x[0]))),
                    "column_syndrome_table_canonical_serialized_bytes": len(cbytes(column_bits)),
                    "column_syndrome_table_sha256": digest(column_bits),
                },
                "failure_witnesses": witnesses,
            },
            "agreement": {
                "same_correction_count": same_correction,
                "same_success_outcome_count": same_outcome,
                "corpus_size": len(corpus),
            },
        },
        "deterministic_system_model": {
            "data_bits": n,
            "full_syndrome_bits": len(hz),
            "independent_syndrome_bits": len(basis(hz)),
            "stabilizer_span_size": len(stabilizers),
            "wall_clock_authoritative": False,
            "memory_metric": "canonical_serialized_bytes_not_runtime_object_size",
        },
        "source_context": b["source_context"],
        "claim_boundary": b["claim_boundary"],
    }
    report["payload_sha256"] = digest(report)
    return report


def profile(b: dict[str, Any], predecessor: dict[str, Any], repeats: int) -> dict[str, Any]:
    if repeats <= 0:
        raise ValueError("profile repeats must be positive")
    samples = []
    for _ in range(repeats):
        start = time.perf_counter_ns()
        evaluate(b, predecessor)
        samples.append(time.perf_counter_ns() - start)
    return {
        "fixture_id": "QLDPC-FIXTURE-002",
        "diagnostic_only": True,
        "authoritative": False,
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "repeats": repeats,
        "elapsed_ns": samples,
        "min_elapsed_ns": min(samples),
        "max_elapsed_ns": max(samples),
        "median_elapsed_ns": sorted(samples)[len(samples) // 2],
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--registry", type=Path, default=root() / "registry/qldpc-benchmarks.json")
    p.add_argument("--predecessor", type=Path, default=root() / PREDECESSOR["evidence_path"])
    p.add_argument("--output", type=Path)
    p.add_argument("--profile-output", type=Path)
    p.add_argument("--profile-repeats", type=int, default=3)
    args = p.parse_args()
    b = load_benchmark(args.registry)
    predecessor = json.loads(args.predecessor.read_text())
    report = evaluate(b, predecessor)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(rendered, end="")
    if args.profile_output:
        args.profile_output.write_text(
            json.dumps(profile(b, predecessor, args.profile_repeats), indent=2, sort_keys=True) + "\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
