#!/usr/bin/env python3
"""QEC-CIRCUIT-001: bounded phenomenological repeated-syndrome temporal replay."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import itertools
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import qldpc_fixture_002 as F2

EXPERIMENT_ID = "QEC-CIRCUIT-001"
EVALUATOR_VERSION = "0.1.0"
MANIFEST_PATH = ROOT / "registry/qec-circuit-001-manifest.json"
MANIFEST_PAYLOAD = "15962fa93eb92632e760e62a54fbd03a8322fb09b8c3b41de2f0b4225fb52dfb"
FIXTURE_PAYLOAD = "6c2095f48762178bf0fe5c2b5fce8299261733912a1cccc7884d11f344718427"
EXPECTED_START = "b1e6a45073842ac498b476f6c8c1d31b133e553a"
METHODS = ("TEMP_BP_MIN_SUM", "TEMP_BP_OSD_CS_7", "TEMP_BP_SUM_PRODUCT")


def cbytes(x: Any) -> bytes:
    return json.dumps(
        x, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def digest(x: Any) -> str:
    return hashlib.sha256(cbytes(x)).hexdigest()


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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    data = load_json(path)
    claimed = data.pop("manifest_payload_sha256")
    observed = digest(data)
    data["manifest_payload_sha256"] = claimed
    if claimed != MANIFEST_PAYLOAD or observed != MANIFEST_PAYLOAD:
        raise ValueError("QEC-CIRCUIT-001 manifest self-digest mismatch")
    authority = data["authority"]
    if authority != {
        "council_issue": 76,
        "execution_issue": 77,
        "human_steward_authorization_comment": 5321917311,
        "human_steward_disposition": "ADOPT_WITH_AMENDMENTS__AUTHORIZE_QEC_CIRCUIT_001_ONLY",
        "protected_start_main": EXPECTED_START,
        "referee_comment": 5321884229,
        "referee_recommendation": "RECOMMEND_ADOPTION_WITH_AMENDMENTS__NO_EXECUTION_AUTHORITY",
    }:
        raise ValueError("QEC-CIRCUIT-001 authority drift")
    boundary = data["claim_boundary"]
    if boundary["phenomenological_repeated_syndrome_fixture_only"] is not True:
        raise ValueError("temporal fixture boundary missing")
    forbidden = (
        "gate_level_syndrome_extraction_claim",
        "ancilla_or_hook_error_claim",
        "gate_propagation_claim",
        "hardware_noise_claim",
        "full_pauli_claim",
        "round_count_scaling_claim",
        "error_rate_sweep_authorized",
        "threshold_or_pseudothreshold_claim",
        "runtime_or_memory_superiority_claim",
        "family_or_asymptotic_claim",
        "learned_decoder_authorized",
        "adaptive_order_search_authorized",
        "autonomous_search_authorized",
        "later_qec_circuit_subgate_authorized",
        "qldpc_forge_authorized",
    )
    for name in forbidden:
        if boundary[name] is not False:
            raise ValueError(f"forbidden authority enabled: {name}")
    return data


def load_fixture(manifest: dict[str, Any]) -> tuple[list[int], list[int], set[int], list[int]]:
    path = ROOT / manifest["predecessors"]["QLDPC-FIXTURE-001"]["evidence_path"]
    report = load_json(path)
    if report.get("payload_sha256") != FIXTURE_PAYLOAD:
        raise ValueError("Fixture 001 payload drift")
    unsigned = dict(report)
    unsigned.pop("payload_sha256", None)
    if digest(unsigned) != FIXTURE_PAYLOAD:
        raise ValueError("Fixture 001 payload does not self-verify")
    hx = [b2i(x) for x in report["construction"]["hx"]]
    hz = [b2i(x) for x in report["construction"]["hz"]]
    if report["removed_checks_source_record"]["z"] != [3, 4]:
        raise ValueError("protected removed Z-check record drift")
    basis_rows = [hz[i] for i in range(len(hz)) if i not in (3, 4)]
    expected_bits = manifest["fixture"]["independent_z_check_basis"]["rows"]
    if [i2b(x, 18) for x in basis_rows] != expected_bits:
        raise ValueError("independent Z-check basis drift")
    if len(F2.basis(basis_rows)) != 7 or len(F2.basis(hz)) != 7:
        raise ValueError("Z-check rank drift")
    if F2.span(basis_rows) != F2.span(hz):
        raise ValueError("independent Z-check basis does not span protected H_Z")
    stabilizers = F2.span(hx)
    if len(stabilizers) != 128:
        raise ValueError("X stabilizer span drift")
    return hx, hz, stabilizers, basis_rows


def syndrome(error: int, rows: list[int]) -> int:
    return F2.syndrome(error, rows)


def direct_recurrence(x: int, basis_rows: list[int]) -> tuple[int, int]:
    mask18 = (1 << 18) - 1
    mask7 = (1 << 7) - 1
    f1 = x & mask18
    f2 = (x >> 18) & mask18
    f3 = (x >> 36) & mask18
    m1 = (x >> 54) & mask7
    m2 = (x >> 61) & mask7
    m3 = (x >> 68) & mask7
    e1 = f1
    e2 = f1 ^ f2
    e3 = f1 ^ f2 ^ f3
    y1 = syndrome(e1, basis_rows) ^ m1
    y2 = syndrome(e2, basis_rows) ^ m2
    y3 = syndrome(e3, basis_rows) ^ m3
    y4 = syndrome(e3, basis_rows)
    d1 = y1
    d2 = y2 ^ y1
    d3 = y3 ^ y2
    d4 = y4 ^ y3
    detectors = d1 | (d2 << 7) | (d3 << 14) | (d4 << 21)
    return detectors, e3


def terminal_projection(x: int) -> int:
    mask18 = (1 << 18) - 1
    return (x & mask18) ^ ((x >> 18) & mask18) ^ ((x >> 36) & mask18)


def build_detector_formula(basis_rows: list[int]) -> list[int]:
    rows = [0] * 28
    for a, hrow in enumerate(basis_rows):
        rows[a] = hrow | (1 << (54 + a))
        rows[7 + a] = (hrow << 18) | (1 << (54 + a)) | (1 << (61 + a))
        rows[14 + a] = (hrow << 36) | (1 << (61 + a)) | (1 << (68 + a))
        rows[21 + a] = 1 << (68 + a)
    return rows


def build_detector_unit_injection(basis_rows: list[int]) -> list[int]:
    columns = [direct_recurrence(1 << q, basis_rows)[0] for q in range(75)]
    rows = []
    for r in range(28):
        rows.append(sum(((column >> r) & 1) << q for q, column in enumerate(columns)))
    return rows


def detector_apply(x: int, detector_rows: list[int]) -> int:
    out = 0
    for r, row in enumerate(detector_rows):
        if (x & row).bit_count() & 1:
            out |= 1 << r
    return out


def make_corpus() -> list[int]:
    return (
        [0]
        + [1 << q for q in range(75)]
        + [(1 << a) | (1 << b) for a in range(75) for b in range(a + 1, 75)]
    )


def canonical_class(error: int, stabilizers: set[int]) -> int:
    return min(error ^ s for s in stabilizers)


def detector_scopes(detector_rows: list[int]) -> list[list[int]]:
    return [[q for q in range(75) if (row >> q) & 1] for row in detector_rows]


def primal_graph(scopes: list[list[int]]) -> list[set[int]]:
    adj = [set() for _ in range(75)]
    for scope in scopes:
        for i, a in enumerate(scope):
            for b in scope[i + 1 :]:
                adj[a].add(b)
                adj[b].add(a)
    return adj


def elimination_order(adj0: list[set[int]], policy: str) -> dict[str, Any]:
    adj = [set(x) for x in adj0]
    alive = set(range(len(adj)))
    order: list[int] = []
    widths: list[int] = []
    fill_total = 0
    while alive:
        def score(v: int) -> tuple[int, ...]:
            neigh = sorted(adj[v] & alive)
            if policy == "lexicographic":
                return (v,)
            if policy == "deterministic_min_degree":
                return (len(neigh), v)
            if policy == "deterministic_min_fill":
                missing = 0
                for i, a in enumerate(neigh):
                    for b in neigh[i + 1 :]:
                        missing += int(b not in adj[a])
                return (missing, v)
            raise ValueError(policy)

        v = min(alive, key=score)
        neigh = sorted(adj[v] & alive)
        widths.append(len(neigh))
        for i, a in enumerate(neigh):
            for b in neigh[i + 1 :]:
                if b not in adj[a]:
                    adj[a].add(b)
                    adj[b].add(a)
                    fill_total += 1
        for u in neigh:
            adj[u].discard(v)
        alive.remove(v)
        order.append(v)
    width = max(widths, default=0)
    return {
        "order_sha256": digest(order),
        "induced_width": width,
        "peak_joint_arity": width + 1,
        "peak_joint_table_entries": 1 << (width + 1),
        "fill_edges_inserted": fill_total,
    }


def gf2_rank(rows: list[int]) -> int:
    return len(F2.basis(rows))


def static_report(manifest: dict[str, Any]) -> dict[str, Any]:
    _, _, stabilizers, basis_rows = load_fixture(manifest)
    formula = build_detector_formula(basis_rows)
    injected = build_detector_unit_injection(basis_rows)
    if formula != injected:
        raise AssertionError("detector map dual construction mismatch")
    observed_bits = [i2b(row, 75) for row in formula]
    if observed_bits != manifest["detector_map"]["row_bitstrings"]:
        raise AssertionError("detector map bytes drift")
    if digest(observed_bits) != manifest["detector_map"]["sha256"]:
        raise AssertionError("detector map digest drift")
    if gf2_rank(formula) != manifest["detector_map"]["rank"]:
        raise AssertionError("detector map rank drift")

    corpus = make_corpus()
    if len(corpus) != 2851:
        raise AssertionError("corpus size drift")
    records = []
    fibers: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for index, x in enumerate(corpus):
        d_direct, e3 = direct_recurrence(x, basis_rows)
        d_matrix = detector_apply(x, formula)
        if d_direct != d_matrix:
            raise AssertionError(f"detector recurrence mismatch at corpus index {index}")
        if terminal_projection(x) != e3:
            raise AssertionError("terminal projection drift")
        klass = canonical_class(e3, stabilizers)
        fibers[d_direct].append((e3, klass))
        records.append(
            {
                "index": index,
                "fault_weight": x.bit_count(),
                "fault_history": i2b(x, 75),
                "detector_history": i2b(d_direct, 28),
                "terminal_error": i2b(e3, 18),
            }
        )
    corpus_info = manifest["corpus"]
    if digest(records) != corpus_info["ordered_fault_detector_terminal_record_sha256"]:
        raise AssertionError("corpus record digest drift")
    if len(cbytes(records)) != corpus_info["canonical_serialized_bytes"]:
        raise AssertionError("corpus canonical-byte count drift")

    size_hist = Counter(len(v) for v in fibers.values())
    class_hist = Counter(len({klass for _, klass in v}) for v in fibers.values())
    ambiguous = [v for v in fibers.values() if len({klass for _, klass in v}) > 1]
    fiber_report = {
        "distinct_detector_vectors": len(fibers),
        "fiber_size_histogram": {str(k): v for k, v in sorted(size_hist.items())},
        "terminal_stabilizer_class_count_per_fiber_histogram": {
            str(k): v for k, v in sorted(class_hist.items())
        },
        "fibers_with_multiple_terminal_stabilizer_classes": len(ambiguous),
        "authoritative_histories_in_ambiguous_fibers": sum(len(v) for v in ambiguous),
        "ambiguity_retained": True,
    }
    if fiber_report != manifest["detector_fibers_predecoder"]:
        raise AssertionError("detector fiber statistics drift")

    scopes = detector_scopes(formula)
    graph = primal_graph(scopes)
    order_report = {
        "lexicographic": elimination_order(graph, "lexicographic"),
        "deterministic_min_fill": elimination_order(graph, "deterministic_min_fill"),
        "deterministic_min_degree": elimination_order(graph, "deterministic_min_degree"),
    }
    tcm = manifest["temporal_tcm_structural_preflight"]
    if digest(scopes) != tcm["factor_scope_sha256"]:
        raise AssertionError("temporal factor-scope digest drift")
    for name, row in order_report.items():
        if row != tcm["orders"][name]:
            raise AssertionError(f"{name} structural order drift")
    if order_report["deterministic_min_fill"]["peak_joint_table_entries"] <= manifest[
        "tcm_resource_envelope"
    ]["peak_joint_table_entries"]:
        raise AssertionError("expected frozen TCM cap exhaustion not reproduced")

    for q in range(18):
        x = 1 << q
        d, _ = direct_recurrence(x, basis_rows)
        if (d & 0x7F) != syndrome(1 << q, basis_rows):
            raise AssertionError("static-limit syndrome mismatch")

    return {
        "experiment_id": EXPERIMENT_ID,
        "evaluator_version": EVALUATOR_VERSION,
        "manifest_payload_sha256": MANIFEST_PAYLOAD,
        "detector_map": {
            "sha256": digest(observed_bits),
            "rank": gf2_rank(formula),
            "row_weights": [row.bit_count() for row in formula],
            "column_weight_histogram": manifest["detector_map"]["column_weight_histogram"],
            "dual_construction_equal": True,
        },
        "corpus": {
            "size": len(corpus),
            "ordered_record_sha256": digest(records),
            "canonical_serialized_bytes": len(cbytes(records)),
            "exhaustive_matrix_recurrence_equal": True,
        },
        "detector_fibers": fiber_report,
        "temporal_tcm": {
            "status": "TEMPORAL_TCM_EXACT_BOUND_EXHAUSTED",
            "orders": order_report,
            "primary_cap": manifest["tcm_resource_envelope"]["peak_joint_table_entries"],
            "stopped_before_table_materialization": True,
            "intrinsic_intractability_claim": False,
        },
        "claim_boundary": manifest["claim_boundary"],
    }


def int_rows_to_numpy(rows: list[int], n: int):
    import numpy as np
    return np.array([[(row >> q) & 1 for q in range(n)] for row in rows], dtype=np.uint8)


def package_receipt() -> dict[str, Any]:
    import ldpc
    ldpc_attr = str(getattr(ldpc, "__version__", "")).strip()
    ldpc_meta = importlib.metadata.version("ldpc")
    bposd_meta = importlib.metadata.version("bposd")
    if (ldpc_attr, ldpc_meta, bposd_meta) != ("0.1.53", "0.1.53", "1.6"):
        raise RuntimeError(
            f"pinned package mismatch: ldpc attr={ldpc_attr}, ldpc={ldpc_meta}, bposd={bposd_meta}"
        )
    return {
        "ldpc_module_version": ldpc_attr,
        "ldpc_metadata_version": ldpc_meta,
        "bposd_metadata_version": bposd_meta,
        "bp_decoder_class": ldpc.bp_decoder.__name__,
        "bposd_decoder_class": ldpc.bposd_decoder.__name__,
    }


def make_decoder(method: str, detector_rows: list[int]):
    import ldpc
    import numpy as np
    h = int_rows_to_numpy(detector_rows, 75)
    common = {
        "channel_probs": np.full(75, 0.1, dtype=float),
        "max_iter": 10000,
        "input_vector_type": "syndrome",
    }
    if method == "TEMP_BP_MIN_SUM":
        return ldpc.bp_decoder(h, bp_method="ms", ms_scaling_factor=0, **common)
    if method == "TEMP_BP_SUM_PRODUCT":
        return ldpc.bp_decoder(h, bp_method="ps", ms_scaling_factor=0, **common)
    if method == "TEMP_BP_OSD_CS_7":
        return ldpc.bposd_decoder(
            h,
            bp_method="ms",
            ms_scaling_factor=0,
            osd_method="osd_cs",
            osd_order=7,
            **common,
        )
    raise ValueError(method)


def certify_decoder_interface(method: str, decoder: Any) -> dict[str, Any]:
    expected_class = "bposd_decoder" if method == "TEMP_BP_OSD_CS_7" else "bp_decoder"
    observed_class = decoder.__class__.__name__
    if observed_class != expected_class:
        raise RuntimeError(f"{method} class mismatch: {observed_class}")
    receipt: dict[str, Any] = {
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
    if method == "TEMP_BP_MIN_SUM":
        if str(decoder.bp_method) != "minimum_sum_log":
            raise RuntimeError("TEMP_BP_MIN_SUM internal method drift")
        if hasattr(decoder, "osd_order") or hasattr(decoder, "osdw_decoding"):
            raise RuntimeError("TEMP_BP_MIN_SUM unexpectedly exposes OSD")
        receipt["osd_absent_by_class"] = True
    elif method == "TEMP_BP_SUM_PRODUCT":
        if str(decoder.bp_method) != "product_sum":
            raise RuntimeError("TEMP_BP_SUM_PRODUCT internal method drift")
        if hasattr(decoder, "osd_order") or hasattr(decoder, "osdw_decoding"):
            raise RuntimeError("TEMP_BP_SUM_PRODUCT unexpectedly exposes OSD")
        receipt["osd_absent_by_class"] = True
    else:
        if str(decoder.bp_method) != "minimum_sum_log":
            raise RuntimeError("TEMP_BP_OSD_CS_7 BP method drift")
        if str(decoder.osd_method) != "osd_cs" or int(decoder.osd_order) != 7:
            raise RuntimeError("TEMP_BP_OSD_CS_7 OSD configuration drift")
        receipt["osd_method"] = str(decoder.osd_method)
        receipt["osd_order"] = int(decoder.osd_order)
    return receipt


def decode_method(method: str, manifest: dict[str, Any]) -> dict[str, Any]:
    import numpy as np

    static_report(manifest)
    hx, hz, stabilizers, basis_rows = load_fixture(manifest)
    detector_rows = build_detector_formula(basis_rows)
    decoder = make_decoder(method, detector_rows)
    interface = certify_decoder_interface(method, decoder)
    corpus = make_corpus()

    shell: dict[str, dict[str, int]] = {}
    outcomes: list[bool | None] = []
    correction_valued: list[bool] = []
    per_input: list[dict[str, Any]] = []
    totals = {
        "inputs": len(corpus),
        "correction_valued": 0,
        "declared_failures": 0,
        "oracle_success": 0,
        "oracle_failure": 0,
        "detector_consistent": 0,
        "detector_inconsistent": 0,
        "terminal_syndrome_consistent": 0,
        "terminal_syndrome_inconsistent": 0,
        "bp_iterations_total": 0,
        "bp_converged_count": 0,
        "bp_nonconverged_count": 0,
        "terminal_correction_weight_total": 0,
    }

    for index, x in enumerate(corpus):
        detectors, terminal_error = direct_recurrence(x, basis_rows)
        weight = x.bit_count()
        bucket = shell.setdefault(
            str(weight),
            {"inputs": 0, "correction_valued": 0, "declared_failures": 0, "oracle_success": 0, "oracle_failure": 0},
        )
        bucket["inputs"] += 1
        detector_np = np.array([(detectors >> r) & 1 for r in range(28)], dtype=np.uint8)
        try:
            inferred_np = decoder.decode(detector_np)
            inferred = sum((int(bit) & 1) << q for q, bit in enumerate(inferred_np.tolist()))
            if inferred >> 75:
                raise RuntimeError("decoder returned oversized history")
            correction = terminal_projection(inferred)
            detector_consistent = detector_apply(inferred, detector_rows) == detectors
            terminal_syndrome_consistent = syndrome(correction, hz) == syndrome(terminal_error, hz)
            success = terminal_syndrome_consistent and ((terminal_error ^ correction) in stabilizers)
            iterations = int(decoder.iter) if hasattr(decoder, "iter") else 0
            converged = bool(int(decoder.converge)) if hasattr(decoder, "converge") else False

            totals["correction_valued"] += 1
            totals["detector_consistent" if detector_consistent else "detector_inconsistent"] += 1
            totals["terminal_syndrome_consistent" if terminal_syndrome_consistent else "terminal_syndrome_inconsistent"] += 1
            totals["oracle_success" if success else "oracle_failure"] += 1
            totals["bp_iterations_total"] += iterations
            totals["bp_converged_count" if converged else "bp_nonconverged_count"] += 1
            totals["terminal_correction_weight_total"] += correction.bit_count()
            bucket["correction_valued"] += 1
            bucket["oracle_success" if success else "oracle_failure"] += 1
            outcomes.append(success)
            correction_valued.append(True)
            per_input.append({
                "index": index,
                "fault_weight": weight,
                "detectors": i2b(detectors, 28),
                "inferred_history": i2b(inferred, 75),
                "terminal_correction": i2b(correction, 18),
                "detector_consistent": detector_consistent,
                "terminal_syndrome_consistent": terminal_syndrome_consistent,
                "oracle_success": success,
                "bp_iterations": iterations,
                "bp_converged": converged,
            })
        except Exception as exc:
            totals["declared_failures"] += 1
            bucket["declared_failures"] += 1
            outcomes.append(None)
            correction_valued.append(False)
            per_input.append({
                "index": index,
                "fault_weight": weight,
                "detectors": i2b(detectors, 28),
                "declared_failure": f"{type(exc).__name__}: {exc}",
            })

    if totals["correction_valued"] + totals["declared_failures"] != len(corpus):
        raise AssertionError("method accounting mismatch")

    return {
        "experiment_id": EXPERIMENT_ID,
        "evaluator_version": EVALUATOR_VERSION,
        "manifest_payload_sha256": MANIFEST_PAYLOAD,
        "method": method,
        "package_receipt": package_receipt(),
        "interface": interface,
        "totals": totals,
        "by_elementary_fault_weight": shell,
        "outcomes": outcomes,
        "correction_valued": correction_valued,
        "per_input": per_input,
        "timing_authoritative": False,
        "memory_authoritative": False,
    }


def assemble(cell_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    static = static_report(manifest)
    cells: dict[str, Any] = {}
    for method in METHODS:
        matches = list(cell_dir.rglob(f"{method}.json"))
        if len(matches) != 1:
            raise ValueError(f"expected one cell file for {method}, found {len(matches)}")
        cell = load_json(matches[0])
        if cell["experiment_id"] != EXPERIMENT_ID or cell["method"] != method:
            raise ValueError(f"cell identity mismatch for {method}")
        if cell["manifest_payload_sha256"] != MANIFEST_PAYLOAD:
            raise ValueError(f"cell manifest mismatch for {method}")
        cells[method] = cell

    pairwise: dict[str, Any] = {}
    for left, right in itertools.combinations(METHODS, 2):
        lo = cells[left]["outcomes"]
        ro = cells[right]["outcomes"]
        if len(lo) != len(ro):
            raise AssertionError("pairwise outcome length mismatch")
        matched = left_only = right_only = both_success = both_failure = 0
        for a, b in zip(lo, ro):
            if a is None or b is None:
                continue
            matched += 1
            if a and b:
                both_success += 1
            elif a and not b:
                left_only += 1
            elif b and not a:
                right_only += 1
            else:
                both_failure += 1
        pairwise[f"{left}__vs__{right}"] = {
            "matched_correction_valued_inputs": matched,
            "both_success": both_success,
            "left_only_success": left_only,
            "right_only_success": right_only,
            "both_failure": both_failure,
            "net_left_minus_right": left_only - right_only,
        }

    report: dict[str, Any] = {
        "experiment_id": EXPERIMENT_ID,
        "evaluator_version": EVALUATOR_VERSION,
        "status": "candidate_executable_not_promoted",
        "manifest_payload_sha256": MANIFEST_PAYLOAD,
        "substrate": static,
        "temporal_tcm": static["temporal_tcm"],
        "conventional_methods": {
            method: {
                "interface": cells[method]["interface"],
                "package_receipt": cells[method]["package_receipt"],
                "totals": cells[method]["totals"],
                "by_elementary_fault_weight": cells[method]["by_elementary_fault_weight"],
            }
            for method in METHODS
        },
        "conventional_pairwise": pairwise,
        "comparison_boundary": {
            "tcm_quality_defined": False,
            "tcm_reason": "TEMPORAL_TCM_EXACT_BOUND_EXHAUSTED",
            "conventional_vs_tcm_quality_ordering_defined": False,
            "gate_level_claim": False,
            "threshold_claim": False,
            "runtime_or_memory_superiority_claim": False,
        },
        "claim_boundary": manifest["claim_boundary"],
    }
    report["payload_sha256"] = digest(report)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--method", choices=METHODS)
    parser.add_argument("--assemble", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = load_manifest(args.manifest)
    if sum(bool(x) for x in (args.static_only, args.method, args.assemble)) != 1:
        raise SystemExit("choose exactly one of --static-only, --method, or --assemble")
    if args.static_only:
        result = static_report(manifest)
    elif args.method:
        result = decode_method(args.method, manifest)
    else:
        result = assemble(args.assemble, manifest)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
