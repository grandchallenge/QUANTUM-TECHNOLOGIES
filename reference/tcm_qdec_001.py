#!/usr/bin/env python3
"""TCM-QDEC-001: exact finite degeneracy-aware semiring inference audit."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
F2_PATH = ROOT / "reference" / "qldpc_fixture_002.py"
SPEC = importlib.util.spec_from_file_location("qldpc_fixture_002_for_tcm", F2_PATH)
F2 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(F2)

EVALUATOR_VERSION = "0.1.0"
FIXTURE_001_PAYLOAD = "6c2095f48762178bf0fe5c2b5fce8299261733912a1cccc7884d11f344718427"
FIXTURE_002_PAYLOAD = "d98c5d73f7fdf9259a35be60580dc9b6c32c5e4483cd765ed0dcba594b9299e5"
FIXTURE_002_CORPUS = "260b1a43cf1d777f28c475918e91a5f7cefc5d28a2bfb556338f7e30058f58a8"
FIXTURE_002_SCIENTIFIC_MERGE = "51c31bde2e0630314d3d48dceb9b92969c37c228"
FIXTURE_002_PROMOTION_MERGE = "074612e39e1232d1644edc487914ca571189f409"
EXACT_TABLE_SHA = "96ce94c378b7b1fc5fe032fbd253aa932c1ca8abcb17b3d3c89b3ecda601da29"

CLAIM_BOUNDARY = {
    "finite_semiring_comparison_only": True,
    "frozen_fixture_002_corpus_only": True,
    "exact_state_space_enumeration": True,
    "scalable_tensor_contraction_claim": False,
    "general_qldpc_decoder_claim": False,
    "decoder_performance_superiority_claim": False,
    "bp_osd_performance_claim": False,
    "circuit_level_noise_claim": False,
    "hardware_validation_claim": False,
    "threshold_claim": False,
    "portable_latency_or_memory_claim": False,
    "learned_decoder_authorized": False,
    "tcm_qdec_002_authorized": False,
    "qldpc_forge_authorized": False,
    "autonomous_search_authorized": False,
}

SEMIRINGS = {
    "sum_product_bsc_p_0_1": {
        "kind": "sum_product",
        "score_direction": "maximize",
        "exact_state_weight": "9**(n-hamming_weight)",
        "interpretation": "exact numerator proportional to BSC p=0.1 likelihood",
    },
    "soft_tropical_base_2": {
        "kind": "soft_tropical",
        "score_direction": "maximize",
        "exact_state_weight": "2**(n-hamming_weight)",
        "interpretation": "exact partition score equivalent in ranking to beta=ln(2) soft-min",
    },
    "min_plus_hamming": {
        "kind": "min_plus",
        "score_direction": "minimize",
        "exact_state_weight": "hamming_weight",
        "interpretation": "minimum Hamming-weight tropical score",
    },
}

TREATMENTS = {
    "representative_naive_marginals": {
        "kind": "coordinatewise_semiring_marginal_hard_decision",
        "tie_break": "zero_bit",
        "syndrome_projection": "none",
    },
    "stabilizer_coset_aggregate": {
        "kind": "semiring_aggregate_over_stabilizer_equivalence_class",
        "class_tie_break": "lowest_canonical_coset_key",
        "representative_within_class": "lowest_hamming_weight_then_integer",
    },
}

digest = F2.canonical_digest
syndrome = F2.syndrome
i2b = F2.i2b


def keys(d: dict[str, Any], expected: set[str], where: str) -> None:
    if set(d) != expected:
        raise ValueError(
            f"{where} key mismatch: missing={sorted(expected-set(d))}, "
            f"extra={sorted(set(d)-expected)}"
        )


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_registry(path: Path) -> dict[str, Any]:
    data = load_json(path)
    keys(data, {"registry_version", "experiments"}, "registry")
    if data["registry_version"] != "0.1.0" or not isinstance(data["experiments"], list):
        raise ValueError("invalid TCM-QDEC registry")
    matches = [x for x in data["experiments"] if x.get("experiment_id") == "TCM-QDEC-001"]
    if len(matches) != 1:
        raise ValueError("TCM-QDEC-001 must appear exactly once")
    e = matches[0]
    keys(
        e,
        {
            "experiment_id", "programme", "status", "predecessor", "state_space",
            "semirings", "quotient_treatments", "claim_boundary",
        },
        "experiment",
    )
    if e["programme"] != "QTR" or e["status"] != "candidate_executable_not_promoted":
        raise ValueError("TCM-QDEC experiment identity/status changed")
    expected_predecessor = {
        "fixture_id": "QLDPC-FIXTURE-002",
        "evidence_path": "evidence/QLDPC-FIXTURE-002-report.json",
        "evidence_payload_sha256": FIXTURE_002_PAYLOAD,
        "corpus_sha256": FIXTURE_002_CORPUS,
        "scientific_merge_commit": FIXTURE_002_SCIENTIFIC_MERGE,
        "promotion_merge_commit": FIXTURE_002_PROMOTION_MERGE,
        "promotion_record_path": "reviews/QTR-QLDPC-REVIEW-002/promotion-record.json",
    }
    expected_state = {
        "sector_model": "code_capacity_single_css_sector",
        "corpus_kind": "fixture_002_frozen_hamming_weight_0_through_4",
        "corpus_size": 4048,
        "corpus_sha256": FIXTURE_002_CORPUS,
        "full_physical_error_states": 262144,
        "reachable_syndromes": 128,
        "states_per_syndrome": 2048,
        "stabilizer_span_size": 128,
        "logical_cosets_per_syndrome": 16,
    }
    for name, observed, expected in (
        ("predecessor", e["predecessor"], expected_predecessor),
        ("state_space", e["state_space"], expected_state),
        ("semirings", e["semirings"], SEMIRINGS),
        ("quotient_treatments", e["quotient_treatments"], TREATMENTS),
        ("claim_boundary", e["claim_boundary"], CLAIM_BOUNDARY),
    ):
        if observed != expected:
            raise ValueError(f"{name} unexpectedly changed")
    return e


def validate_predecessors(
    fixture1: dict[str, Any], fixture2: dict[str, Any], promotion2: dict[str, Any]
) -> tuple[list[int], set[int], int]:
    if fixture1.get("payload_sha256") != FIXTURE_001_PAYLOAD:
        raise ValueError("Fixture 001 payload mismatch")
    _, rows, stabilizers, n = F2.validate_predecessor(fixture1)

    if fixture2.get("fixture_id") != "QLDPC-FIXTURE-002":
        raise ValueError("Fixture 002 identity mismatch")
    if fixture2.get("payload_sha256") != FIXTURE_002_PAYLOAD:
        raise ValueError("Fixture 002 payload mismatch")
    unsigned2 = dict(fixture2)
    unsigned2.pop("payload_sha256", None)
    if digest(unsigned2) != FIXTURE_002_PAYLOAD:
        raise ValueError("Fixture 002 payload does not self-verify")
    corpus = fixture2.get("corpus", {})
    if (
        corpus.get("corpus_sha256") != FIXTURE_002_CORPUS
        or corpus.get("actual_error_count") != 4048
        or corpus.get("max_weight") != 4
        or corpus.get("sector_model") != "code_capacity_single_css_sector"
    ):
        raise ValueError("Fixture 002 frozen corpus changed")
    boundary = fixture2.get("claim_boundary", {})
    if boundary.get("systems_benchmark_only") is not True:
        raise ValueError("Fixture 002 authority missing")
    for name in (
        "tcm_qdec_authorized", "qldpc_forge_authorized",
        "autonomous_search_authorized", "circuit_level_noise_claim",
        "hardware_validation_claim", "threshold_claim",
    ):
        if boundary.get(name) is not False:
            raise ValueError(f"Fixture 002 forbidden inherited authority enabled: {name}")
    exact = fixture2.get("benchmark_results", {}).get("exact_coset_lookup", {})
    greedy = fixture2.get("benchmark_results", {}).get("greedy_syndrome_descent", {})
    if exact.get("table_sha256") != EXACT_TABLE_SHA or exact.get("success_total") != 240:
        raise ValueError("Fixture 002 exact baseline changed")
    if greedy.get("success_total") != 125:
        raise ValueError("Fixture 002 greedy baseline changed")

    if promotion2.get("record_id") != "QTR-QLDPC-REVIEW-002-PROMOTION":
        raise ValueError("Fixture 002 promotion record identity mismatch")
    if promotion2.get("status") != "referee_promoted_bounded":
        raise ValueError("Fixture 002 is not bounded promoted")
    if promotion2.get("scientific_merge_commit") != FIXTURE_002_SCIENTIFIC_MERGE:
        raise ValueError("Fixture 002 scientific merge mismatch")
    snap = promotion2.get("reviewed_snapshot", {})
    if (
        snap.get("evidence_payload_sha256") != FIXTURE_002_PAYLOAD
        or snap.get("corpus_sha256") != FIXTURE_002_CORPUS
        or snap.get("snapshot_preserved_byte_for_byte") is not True
    ):
        raise ValueError("Fixture 002 reviewed snapshot mismatch")
    return rows, stabilizers, n


def build_coset_keys(stabilizers: set[int], n: int) -> list[int]:
    out = [-1] * (1 << n)
    for seed in range(1 << n):
        if out[seed] != -1:
            continue
        orbit = [seed ^ s for s in stabilizers]
        key = min(orbit)
        for state in orbit:
            out[state] = key
    if any(x < 0 for x in out):
        raise AssertionError("incomplete stabilizer-coset partition")
    return out


def winning_keys(stats: dict[int, dict[str, int]], algebra: str) -> list[int]:
    if algebra == "sum_product_bsc_p_0_1":
        best = max(x["mass9"] for x in stats.values())
        return sorted(k for k, x in stats.items() if x["mass9"] == best)
    if algebra == "soft_tropical_base_2":
        best = max(x["mass2"] for x in stats.values())
        return sorted(k for k, x in stats.items() if x["mass2"] == best)
    best = min(x["min_weight"] for x in stats.values())
    return sorted(k for k, x in stats.items() if x["min_weight"] == best)


def infer_tables(
    rows: list[int], stabilizers: set[int], n: int
) -> tuple[
    dict[str, dict[str, dict[int, int]]],
    dict[str, Any],
    dict[str, dict[int, list[int]]],
    list[int],
]:
    by_syndrome: dict[int, list[int]] = {}
    for state in range(1 << n):
        by_syndrome.setdefault(syndrome(state, rows), []).append(state)
    if len(by_syndrome) != 128 or set(map(len, by_syndrome.values())) != {2048}:
        raise AssertionError("unexpected syndrome state-space geometry")

    coset_keys = build_coset_keys(stabilizers, n)
    tables = {t: {a: {} for a in SEMIRINGS} for t in TREATMENTS}
    quotient_ties = {a: {} for a in SEMIRINGS}
    diagnostics = {
        t: {
            a: {
                "unique_syndrome_decisions": 0,
                "syndrome_valid_decisions": 0,
                "syndrome_invalid_decisions": 0,
                "decision_tie_syndromes": 0,
                "decision_table_sha256": None,
            }
            for a in SEMIRINGS
        }
        for t in TREATMENTS
    }

    for syn in sorted(by_syndrome):
        states = by_syndrome[syn]
        marginal9 = [[0, 0] for _ in range(n)]
        marginal2 = [[0, 0] for _ in range(n)]
        marginal_min = [[n + 1, n + 1] for _ in range(n)]
        classes: dict[int, dict[str, int]] = {}

        for state in states:
            w = state.bit_count()
            m9 = 9 ** (n - w)
            m2 = 2 ** (n - w)
            for q in range(n):
                bit = (state >> q) & 1
                marginal9[q][bit] += m9
                marginal2[q][bit] += m2
                marginal_min[q][bit] = min(marginal_min[q][bit], w)

            key = coset_keys[state]
            item = classes.setdefault(
                key,
                {"mass9": 0, "mass2": 0, "min_weight": n + 1,
                 "representative": state, "count": 0},
            )
            item["mass9"] += m9
            item["mass2"] += m2
            item["count"] += 1
            if (w, state) < (item["min_weight"], item["representative"]):
                item["min_weight"] = w
                item["representative"] = state

        if len(classes) != 16 or set(x["count"] for x in classes.values()) != {128}:
            raise AssertionError("unexpected logical-coset geometry")

        for algebra in SEMIRINGS:
            rep = 0
            bit_ties = 0
            for q in range(n):
                if algebra == "sum_product_bsc_p_0_1":
                    zero, one = marginal9[q]
                    bit = int(one > zero)
                elif algebra == "soft_tropical_base_2":
                    zero, one = marginal2[q]
                    bit = int(one > zero)
                else:
                    zero, one = marginal_min[q]
                    bit = int(one < zero)
                bit_ties += int(one == zero)
                if bit:
                    rep |= 1 << q
            tables["representative_naive_marginals"][algebra][syn] = rep
            rd = diagnostics["representative_naive_marginals"][algebra]
            rd["unique_syndrome_decisions"] += 1
            valid = syndrome(rep, rows) == syn
            rd["syndrome_valid_decisions"] += int(valid)
            rd["syndrome_invalid_decisions"] += int(not valid)
            rd["decision_tie_syndromes"] += int(bit_ties > 0)

            tied = winning_keys(classes, algebra)
            quotient_ties[algebra][syn] = tied
            correction = classes[tied[0]]["representative"]
            tables["stabilizer_coset_aggregate"][algebra][syn] = correction
            qd = diagnostics["stabilizer_coset_aggregate"][algebra]
            qd["unique_syndrome_decisions"] += 1
            valid = syndrome(correction, rows) == syn
            qd["syndrome_valid_decisions"] += int(valid)
            qd["syndrome_invalid_decisions"] += int(not valid)
            qd["decision_tie_syndromes"] += int(len(tied) > 1)

    for treatment in TREATMENTS:
        for algebra in SEMIRINGS:
            records = [
                {"syndrome": i2b(s, len(rows)), "correction": i2b(c, n)}
                for s, c in sorted(tables[treatment][algebra].items())
            ]
            diagnostics[treatment][algebra]["decision_table_sha256"] = digest(records)
    return tables, diagnostics, quotient_ties, coset_keys


def classify(
    corpus: list[int], rows: list[int], stabilizers: set[int], table: dict[int, int]
) -> tuple[dict[str, Any], list[bool]]:
    shell: dict[str, dict[str, int]] = {}
    failures = {"nonzero_residual_syndrome": 0,
                "zero_syndrome_wrong_logical_coset": 0}
    outcomes: list[bool] = []
    for error in corpus:
        syn = syndrome(error, rows)
        correction = table[syn]
        residual = error ^ correction
        residual_syndrome = syndrome(residual, rows)
        ok = residual_syndrome == 0 and residual in stabilizers
        outcomes.append(ok)
        bucket = shell.setdefault(
            str(error.bit_count()), {"success": 0, "failure": 0, "total": 0}
        )
        bucket["total"] += 1
        bucket["success" if ok else "failure"] += 1
        if not ok:
            failures[
                "nonzero_residual_syndrome"
                if residual_syndrome
                else "zero_syndrome_wrong_logical_coset"
            ] += 1
    total = sum(outcomes)
    return {
        "success_total": total,
        "failure_total": len(outcomes) - total,
        "success_counts_by_error_weight": shell,
        "failure_modes": failures,
    }, outcomes


def delta(first: list[bool], second: list[bool]) -> dict[str, int]:
    return {
        "repaired_by_second": sum((not a) and b for a, b in zip(first, second)),
        "broken_by_second": sum(a and (not b) for a, b in zip(first, second)),
        "same_outcome": sum(a == b for a, b in zip(first, second)),
    }


def comparison_witnesses(
    corpus: list[int], rows: list[int], first: dict[int, int], second: dict[int, int],
    first_outcomes: list[bool], second_outcomes: list[bool], limit: int = 8,
) -> dict[str, list[dict[str, Any]]]:
    repaired: list[dict[str, Any]] = []
    broken: list[dict[str, Any]] = []
    for error, a_ok, b_ok in zip(corpus, first_outcomes, second_outcomes):
        if a_ok == b_ok:
            continue
        syn = syndrome(error, rows)
        record = {
            "error_weight": error.bit_count(),
            "error": i2b(error, 18),
            "syndrome": i2b(syn, len(rows)),
            "first_correction": i2b(first[syn], 18),
            "second_correction": i2b(second[syn], 18),
        }
        if not a_ok and b_ok and len(repaired) < limit:
            repaired.append(record)
        elif a_ok and not b_ok and len(broken) < limit:
            broken.append(record)
    return {"repaired_witnesses": repaired, "broken_witnesses": broken}


def tie_sensitivity(
    corpus: list[int], rows: list[int], coset_keys: list[int],
    quotient_ties: dict[str, dict[int, list[int]]],
) -> dict[str, Any]:
    counts: dict[int, dict[int, int]] = {}
    for error in corpus:
        syn = syndrome(error, rows)
        key = coset_keys[error]
        counts.setdefault(syn, {})
        counts[syn][key] = counts[syn].get(key, 0) + 1

    out: dict[str, Any] = {}
    for algebra in SEMIRINGS:
        default = lower = upper = 0
        hist: dict[str, int] = {}
        for syn, tied in quotient_ties[algebra].items():
            hist[str(len(tied))] = hist.get(str(len(tied)), 0) + 1
            values = [counts.get(syn, {}).get(key, 0) for key in tied]
            default += counts.get(syn, {}).get(tied[0], 0)
            lower += min(values)
            upper += max(values)
        out[algebra] = {
            "winning_class_count_histogram": hist,
            "default_lowest_key_success_count": default,
            "frozen_corpus_success_count_envelope_over_winning_class_ties":
                {"min": lower, "max": upper},
            "success_count_invariant_under_winning_class_tie_break": lower == upper,
        }
    return out


def evaluate(
    experiment: dict[str, Any], fixture1: dict[str, Any],
    fixture2: dict[str, Any], promotion2: dict[str, Any],
) -> dict[str, Any]:
    rows, stabilizers, n = validate_predecessors(fixture1, fixture2, promotion2)
    corpus = F2.make_corpus(n, 4)
    corpus_records = [{"weight": e.bit_count(), "error": i2b(e, n)} for e in corpus]
    corpus_sha = digest(corpus_records)
    if len(corpus) != 4048 or corpus_sha != FIXTURE_002_CORPUS:
        raise AssertionError("frozen corpus does not replay Fixture 002")

    tables, diagnostics, quotient_ties, coset_keys = infer_tables(
        rows, stabilizers, n
    )

    exact_table, considered = F2.min_table(rows, n)
    exact_records = [
        {"syndrome": i2b(s, len(rows)), "correction": i2b(e, n),
         "weight": e.bit_count()}
        for s, e in sorted(exact_table.items())
    ]
    if digest(exact_records) != EXACT_TABLE_SHA or considered != 988:
        raise AssertionError("Fixture 002 exact lookup identity changed")
    columns = [syndrome(1 << q, rows) for q in range(n)]
    greedy_table = {
        s: F2.greedy(s, columns, n)[0]
        for s in exact_table
    }
    exact_result, exact_outcomes = classify(corpus, rows, stabilizers, exact_table)
    greedy_result, greedy_outcomes = classify(corpus, rows, stabilizers, greedy_table)
    if exact_result["success_total"] != 240 or greedy_result["success_total"] != 125:
        raise AssertionError("Fixture 002 baseline outcomes changed")

    matrix: dict[str, dict[str, Any]] = {}
    outcomes: dict[tuple[str, str], list[bool]] = {}
    for treatment in TREATMENTS:
        matrix[treatment] = {}
        for algebra in SEMIRINGS:
            result, out = classify(corpus, rows, stabilizers, tables[treatment][algebra])
            outcomes[(treatment, algebra)] = out
            matrix[treatment][algebra] = {
                **result,
                "decision_diagnostics": diagnostics[treatment][algebra],
            }

    comparisons: dict[str, Any] = {}
    for algebra in SEMIRINGS:
        naive = outcomes[("representative_naive_marginals", algebra)]
        quotient = outcomes[("stabilizer_coset_aggregate", algebra)]
        comparisons[algebra] = {
            "quotient_minus_representative_success_count": sum(quotient) - sum(naive),
            "quotient_vs_representative": {
                **delta(naive, quotient),
                **comparison_witnesses(
                    corpus, rows,
                    tables["representative_naive_marginals"][algebra],
                    tables["stabilizer_coset_aggregate"][algebra],
                    naive, quotient,
                ),
            },
            "quotient_minus_fixture_002_exact_success_count":
                sum(quotient) - sum(exact_outcomes),
            "quotient_vs_fixture_002_exact": delta(exact_outcomes, quotient),
            "quotient_minus_fixture_002_greedy_success_count":
                sum(quotient) - sum(greedy_outcomes),
            "quotient_vs_fixture_002_greedy": delta(greedy_outcomes, quotient),
        }

    report: dict[str, Any] = {
        "experiment_id": "TCM-QDEC-001",
        "evaluator_version": EVALUATOR_VERSION,
        "status": "candidate_executable_not_promoted",
        "predecessor": experiment["predecessor"],
        "claim_boundary": experiment["claim_boundary"],
        "state_space": {
            **experiment["state_space"],
            "replayed_corpus_sha256": corpus_sha,
            "full_state_enumeration_count": 1 << n,
        },
        "semirings": experiment["semirings"],
        "quotient_treatments": experiment["quotient_treatments"],
        "fixture_002_baselines": {
            "exact_coset_lookup": exact_result,
            "greedy_syndrome_descent": greedy_result,
        },
        "inference_matrix": matrix,
        "tie_sensitivity": tie_sensitivity(corpus, rows, coset_keys, quotient_ties),
        "comparisons": comparisons,
    }
    report["payload_sha256"] = digest(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default=str(ROOT / "registry" / "tcm-qdec.json"))
    parser.add_argument("--fixture-001",
                        default=str(ROOT / "evidence" / "QLDPC-FIXTURE-001-report.json"))
    parser.add_argument("--fixture-002",
                        default=str(ROOT / "evidence" / "QLDPC-FIXTURE-002-report.json"))
    parser.add_argument(
        "--fixture-002-promotion",
        default=str(ROOT / "reviews" / "QTR-QLDPC-REVIEW-002" / "promotion-record.json"),
    )
    parser.add_argument("--output")
    args = parser.parse_args()
    report = evaluate(
        load_registry(Path(args.registry)),
        load_json(Path(args.fixture_001)),
        load_json(Path(args.fixture_002)),
        load_json(Path(args.fixture_002_promotion)),
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
