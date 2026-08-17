from __future__ import annotations

import hashlib
import json
import sys
from array import array
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from qldpc_scale_001a_shared import *


def rank_rref(rows: list[int], width: int) -> tuple[int, list[int], list[int]]:
    data = list(rows)
    row = 0
    pivots: list[int] = []
    for column in range(width):
        pivot = next((index for index in range(row, len(data)) if (data[index] >> column) & 1), None)
        if pivot is None:
            continue
        data[row], data[pivot] = data[pivot], data[row]
        pivot_row = data[row]
        for index in range(len(data)):
            if index != row and ((data[index] >> column) & 1):
                data[index] ^= pivot_row
        pivots.append(column)
        row += 1
        if row == len(data):
            break
    return row, pivots, data


def lexicographic_independent_rows(rows: list[int], width: int) -> tuple[list[int], list[int]]:
    chosen: list[int] = []
    current: list[int] = []
    rank = 0
    for index, candidate in enumerate(rows):
        new_rank = rank_rref(current + [candidate], width)[0]
        if new_rank > rank:
            chosen.append(index)
            current.append(candidate)
            rank = new_rank
    return chosen, current


def canonical_nullspace_basis(rows: list[int], width: int) -> tuple[list[int], list[int]]:
    _, pivots, rref = rank_rref(rows, width)
    free = [column for column in range(width) if column not in pivots]
    basis: list[int] = []
    for free_column in free:
        vector = 1 << free_column
        for row, pivot in enumerate(pivots):
            if (rref[row] >> free_column) & 1:
                vector |= 1 << pivot
        basis.append(vector)
    return free, basis


def shift_term_rows(kind: str, exponent: int, ell: int = 6, m: int = 6) -> list[int]:
    rows = [0] * (ell * m)
    for left in range(ell):
        for right in range(m):
            row = left * m + right
            if kind == "x":
                column = ((left + exponent) % ell) * m + right
            elif kind == "y":
                column = left * m + ((right + exponent) % m)
            else:
                raise ValueError(f"unknown shift kind: {kind}")
            rows[row] |= 1 << column
    return rows


def transpose_rows(rows: list[int], width: int) -> list[int]:
    out = [0] * width
    for row_index, row in enumerate(rows):
        value = row
        while value:
            low = value & -value
            column = low.bit_length() - 1
            out[column] |= 1 << row_index
            value -= low
    return out


def construct_code() -> dict[str, Any]:
    ell = SOURCE["ell"]
    m = SOURCE["m"]
    x3 = shift_term_rows("x", 3, ell, m)
    y1 = shift_term_rows("y", 1, ell, m)
    y2 = shift_term_rows("y", 2, ell, m)
    y3 = shift_term_rows("y", 3, ell, m)
    x1 = shift_term_rows("x", 1, ell, m)
    x2 = shift_term_rows("x", 2, ell, m)
    a = [left ^ middle ^ right for left, middle, right in zip(x3, y1, y2)]
    b = [left ^ middle ^ right for left, middle, right in zip(y3, x1, x2)]
    bt = transpose_rows(b, ell * m)
    at = transpose_rows(a, ell * m)
    hx = [left | (right << (ell * m)) for left, right in zip(a, b)]
    hz = [left | (right << (ell * m)) for left, right in zip(bt, at)]
    x_indices, x_basis = lexicographic_independent_rows(hx, 72)
    z_indices, z_basis = lexicographic_independent_rows(hz, 72)
    free_columns, kernel_basis = canonical_nullspace_basis(hx, 72)
    current = list(z_basis)
    current_rank = rank_rref(current, 72)[0]
    logical_z: list[int] = []
    selected_free_columns: list[int] = []
    for free_column, vector in zip(free_columns, kernel_basis):
        new_rank = rank_rref(current + [vector], 72)[0]
        if new_rank > current_rank:
            logical_z.append(vector)
            selected_free_columns.append(free_column)
            current.append(vector)
            current_rank = new_rank
    selector_rows = z_basis + logical_z
    physical_columns: list[int] = []
    for qubit in range(72):
        column = 0
        for functional, row in enumerate(selector_rows):
            if (row >> qubit) & 1:
                column |= 1 << functional
        physical_columns.append(column)
    selector_basis_qubits = lexicographic_independent_rows(physical_columns, len(selector_rows))[0]
    scopes = [tuple(index for index, row in enumerate(x_basis) if (row >> qubit) & 1) for qubit in range(72)]
    return {"hx": hx, "hz": hz, "x_indices": x_indices, "x_basis": x_basis, "z_indices": z_indices, "z_basis": z_basis, "free_columns": free_columns, "selected_free_columns": selected_free_columns, "logical_z": logical_z, "selector_rows": selector_rows, "selector_basis_qubits": selector_basis_qubits, "scopes": scopes}


def matrix_record(rows: list[int], n_cols: int) -> dict[str, Any]:
    width = (n_cols + 3) // 4
    return {"n_rows": len(rows), "n_cols": n_cols, "row_hex": [f"{row:0{width}x}" for row in rows]}


def source_and_basis_records(code: dict[str, Any]) -> dict[str, Any]:
    hx_record = matrix_record(code["hx"], 72)
    hz_record = matrix_record(code["hz"], 72)
    bases = {"x_indices": code["x_indices"], "x_rows": [hx_record["row_hex"][index] for index in code["x_indices"]], "z_indices": code["z_indices"], "z_rows": [hz_record["row_hex"][index] for index in code["z_indices"]]}
    logical = {"kernel_free_columns": code["free_columns"], "selected_free_columns": code["selected_free_columns"], "logical_z_rows": matrix_record(code["logical_z"], 72)["row_hex"], "construction": "canonical_rref_nullspace_scan_extend_z_stabilizer_rowspace"}
    selector = {"rank": len(code["selector_basis_qubits"]), "basis_qubits": code["selector_basis_qubits"], "coordinate_rule": "coordinate_bit_i_selects_physical_unit_error_at_basis_qubits[i]", "logical_dimension": len(code["logical_z"])}
    scope_record = {"stabilizer_basis_indices": code["x_indices"], "scopes": [list(scope) for scope in code["scopes"]]}
    return {"source_record": SOURCE, "hx_record": hx_record, "hz_record": hz_record, "bases": bases, "logical": logical, "selector": selector, "scope_record": scope_record}


def css_commutation_nonzero(hx: list[int], hz: list[int]) -> int:
    return sum((left & right).bit_count() & 1 for left in hx for right in hz)


def row_weight_histogram(rows: list[int]) -> dict[str, int]:
    return {str(weight): count for weight, count in sorted(Counter(row.bit_count() for row in rows).items())}


def column_weight_histogram(rows: list[int], width: int) -> dict[str, int]:
    weights = [sum((row >> column) & 1 for row in rows) for column in range(width)]
    return {str(weight): count for weight, count in sorted(Counter(weights).items())}


def primal_graph(scopes: list[tuple[int, ...]], variable_count: int) -> list[set[int]]:
    adjacency = [set() for _ in range(variable_count)]
    for scope in scopes:
        for position, left in enumerate(scope):
            for right in scope[position + 1:]:
                adjacency[left].add(right)
                adjacency[right].add(left)
    return adjacency


def deterministic_min_fill(scopes: list[tuple[int, ...]], variable_count: int) -> list[int]:
    adjacency = primal_graph(scopes, variable_count)
    active = set(range(variable_count))
    order: list[int] = []
    while active:
        candidates: list[tuple[int, int]] = []
        for variable in sorted(active):
            neighbors = sorted(adjacency[variable] & active)
            fill = sum(1 for position, left in enumerate(neighbors) for right in neighbors[position + 1:] if right not in adjacency[left])
            candidates.append((fill, variable))
        _, variable = min(candidates)
        neighbors = sorted(adjacency[variable] & active)
        for position, left in enumerate(neighbors):
            for right in neighbors[position + 1:]:
                adjacency[left].add(right)
                adjacency[right].add(left)
        for neighbor in neighbors:
            adjacency[neighbor].discard(variable)
        active.remove(variable)
        order.append(variable)
    return order


def deterministic_min_degree(scopes: list[tuple[int, ...]], variable_count: int) -> list[int]:
    adjacency = primal_graph(scopes, variable_count)
    active = set(range(variable_count))
    order: list[int] = []
    while active:
        variable = min(active, key=lambda item: (len(adjacency[item] & active), item))
        neighbors = sorted(adjacency[variable] & active)
        for position, left in enumerate(neighbors):
            for right in neighbors[position + 1:]:
                adjacency[left].add(right)
                adjacency[right].add(left)
        for neighbor in neighbors:
            adjacency[neighbor].discard(variable)
        active.remove(variable)
        order.append(variable)
    return order


def elimination_trace(scopes: list[tuple[int, ...]], order: list[int]) -> tuple[int, list[dict[str, Any]]]:
    adjacency = primal_graph(scopes, len(order))
    width = 0
    trace: list[dict[str, Any]] = []
    for variable in order:
        neighbors = sorted(adjacency[variable])
        width = max(width, len(neighbors))
        trace.append({"variable": variable, "neighbor_count": len(neighbors), "neighbors": neighbors})
        for position, left in enumerate(neighbors):
            for right in neighbors[position + 1:]:
                adjacency[left].add(right)
                adjacency[right].add(left)
        for neighbor in neighbors:
            adjacency[neighbor].discard(variable)
        adjacency[variable].clear()
    return width, trace


def order_audit(scopes: list[tuple[int, ...]]) -> dict[str, Any]:
    orders = {"lexicographic": list(range(30)), "min_fill": deterministic_min_fill(scopes, 30), "min_degree": deterministic_min_degree(scopes, 30)}
    order_record = {**orders, "tie_break": "lowest_original_variable_index", "primal_update": "clique_current_neighbors_then_remove"}
    widths: dict[str, int] = {}
    traces: dict[str, Any] = {}
    for name, order in orders.items():
        widths[name], traces[name] = elimination_trace(scopes, order)
    return {"orders": orders, "order_record": order_record, "widths": widths, "traces": traces}


def scope_work(scopes: list[tuple[int, ...]], order: list[int]) -> dict[str, int]:
    factors = [tuple(scope) for scope in scopes]
    joint_total = output_total = reads = multiplies = peak_joint = peak_state = 0
    for variable in order:
        involved = [scope for scope in factors if variable in scope]
        rest = [scope for scope in factors if variable not in scope]
        union = tuple(sorted(set().union(*(set(scope) for scope in involved))))
        output_scope = tuple(item for item in union if item != variable)
        joint = 1 << len(union)
        output = 1 << len(output_scope)
        active = sum(1 << len(scope) for scope in factors)
        peak_joint = max(peak_joint, joint)
        peak_state = max(peak_state, active + joint + output)
        joint_total += joint
        output_total += output
        reads += len(involved) * joint
        multiplies += (len(involved) - 1) * joint
        rest.append(output_scope)
        factors = rest
    local_entries = sum(1 << len(scope) for scope in scopes)
    local_gf2_xor = sum((1 << len(scope)) * len(scope) for scope in scopes)
    return {"local_factor_entries": local_entries, "local_factor_gf2_xor_events": local_gf2_xor, "elimination_joint_assignments": joint_total, "factor_table_entry_evaluations": local_entries + joint_total, "output_entries": output_total, "factor_table_reads": reads, "index_project_events": reads, "semiring_multiply_events": multiplies, "marginal_events": output_total, "table_write_events": local_entries + output_total, "peak_joint_table_entries": peak_joint, "peak_retained_exact_factor_and_scratch_entries": peak_state}


def compile_descriptor(scopes: list[tuple[int, ...]], selector_basis: list[int], order: list[int]) -> tuple[dict[str, Any], dict[str, int]]:
    factors = [(index, tuple(scope)) for index, scope in enumerate(scopes)]
    next_id = len(factors)
    steps: list[dict[str, Any]] = []
    structural_entries = sum(len(scope) for scope in scopes)
    peak_runtime_projection_entries = 0
    for step, variable in enumerate(order):
        involved = [factor for factor in factors if variable in factor[1]]
        rest = [factor for factor in factors if variable not in factor[1]]
        union = tuple(sorted(set().union(*(set(scope) for _, scope in involved))))
        union_positions = {item: position for position, item in enumerate(union)}
        output_scope = tuple(item for item in union if item != variable)
        projection_maps = []
        for factor_id, factor_scope in involved:
            positions = [union_positions[item] for item in factor_scope]
            projection_maps.append({"factor_id": factor_id, "factor_scope": list(factor_scope), "union_positions": positions})
            structural_entries += len(positions) + 3
        output_id = next_id
        next_id += 1
        steps.append({"step": step, "variable": variable, "input_ids": [factor_id for factor_id, _ in involved], "output_id": output_id, "union_scope": list(union), "output_scope": list(output_scope), "eliminated_union_position": union_positions[variable], "projection_maps": projection_maps})
        structural_entries += len(union) + len(output_scope) + len(involved) + 5
        joint = 1 << len(union)
        output = 1 << len(output_scope)
        peak_runtime_projection_entries = max(peak_runtime_projection_entries, len(involved) * joint + 2 * output)
        rest.append((output_id, output_scope))
        factors = rest
    descriptor = {"format": "QTR-QLDPC-SCALE-001A-COMPILED-DESCRIPTOR-v1", "selector_basis_qubits": selector_basis, "selector_parameter_count": len(selector_basis), "initial_factor_scopes": [list(scope) for scope in scopes], "elimination_order": order, "steps": steps, "final_factor_ids": [factor_id for factor_id, _ in factors], "runtime_projection_policy": "generate_exact_flat_index_arrays_lazily_per_step_from_projection_maps_then_discard", "selector_values_materialized_during_compilation": 0, "answer_cache_entries": 0}
    raw = json.dumps(descriptor, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return descriptor, {"canonical_sha256": hashlib.sha256(raw).hexdigest(), "canonical_serialized_bytes": len(raw), "structural_scalar_entries": structural_entries, "step_count": len(steps), "selector_values_materialized_during_compilation": 0, "answer_cache_entries": 0, "peak_runtime_projection_index_entries": peak_runtime_projection_entries}


def generate_projection(positions: list[int], union_arity: int) -> array:
    size = 1 << union_arity
    out = array("I", [0]) * size
    for assignment in range(size):
        index = 0
        for factor_position, union_position in enumerate(positions):
            index |= ((assignment >> union_position) & 1) << factor_position
        out[assignment] = index
    return out


def marginal_indices(union_arity: int, eliminated_position: int) -> tuple[array, array]:
    output_size = 1 << (union_arity - 1)
    low = array("I", [0]) * output_size
    high = array("I", [0]) * output_size
    mask = (1 << eliminated_position) - 1
    for output in range(output_size):
        value = (output & mask) | ((output >> eliminated_position) << (eliminated_position + 1))
        low[output] = value
        high[output] = value | (1 << eliminated_position)
    return low, high


def selector_lift(coordinate: int, selector_basis: list[int]) -> int:
    seed = 0
    for index, qubit in enumerate(selector_basis):
        if (coordinate >> index) & 1:
            seed |= 1 << qubit
    return seed


def local_tables(seed: int, scopes: list[tuple[int, ...]]) -> dict[int, tuple[list[int], ...]]:
    tables: dict[int, tuple[list[int], ...]] = {}
    for qubit, scope in enumerate(scopes):
        size = 1 << len(scope)
        base = (seed >> qubit) & 1
        sum9 = [0] * size
        sum2 = [0] * size
        weight = [0] * size
        representative = [0] * size
        key = [0] * size
        bit_value = 1 << qubit
        for assignment in range(size):
            bit = base ^ (assignment.bit_count() & 1)
            sum9[assignment] = 9 if bit == 0 else 1
            sum2[assignment] = 2 if bit == 0 else 1
            weight[assignment] = bit
            if bit:
                representative[assignment] = bit_value
                key[assignment] = bit_value
        tables[qubit] = (sum9, sum2, weight, representative, key)
    return tables


def runtime_plan_from_descriptor(descriptor: dict[str, Any]) -> tuple[list[tuple[list[int], list[array], array, array, int]], list[int]]:
    plan = []
    for step in descriptor["steps"]:
        union_arity = len(step["union_scope"])
        projections = [generate_projection(mapping["union_positions"], union_arity) for mapping in step["projection_maps"]]
        low, high = marginal_indices(union_arity, step["eliminated_union_position"])
        plan.append((list(step["input_ids"]), projections, low, high, int(step["output_id"])))
    return plan, list(descriptor["final_factor_ids"])


def independent_runtime_plan(scopes: list[tuple[int, ...]], order: list[int]) -> tuple[list[tuple[list[int], list[array], array, array, int]], list[int]]:
    factors = [(index, tuple(scope)) for index, scope in enumerate(scopes)]
    next_id = len(factors)
    plan = []
    for variable in order:
        involved = [factor for factor in factors if variable in factor[1]]
        rest = [factor for factor in factors if variable not in factor[1]]
        union = tuple(sorted(set().union(*(set(scope) for _, scope in involved))))
        positions = {item: position for position, item in enumerate(union)}
        projections = [generate_projection([positions[item] for item in scope], len(union)) for _, scope in involved]
        low, high = marginal_indices(len(union), positions[variable])
        input_ids = [factor_id for factor_id, _ in involved]
        plan.append((input_ids, projections, low, high, next_id))
        rest.append((next_id, tuple(item for item in union if item != variable)))
        next_id += 1
        factors = rest
    return plan, [factor_id for factor_id, _ in factors]


def evaluate_projection_plan(seed: int, scopes: list[tuple[int, ...]], plan: list[tuple[list[int], list[array], array, array, int]], final_ids: list[int]) -> tuple[int, int, tuple[tuple[int, int], int]]:
    tables = local_tables(seed, scopes)
    for input_ids, projections, low, high, output_id in plan:
        first = tables[input_ids[0]]
        first_projection = projections[0]
        sum9 = [first[0][index] for index in first_projection]
        sum2 = [first[1][index] for index in first_projection]
        weight = [first[2][index] for index in first_projection]
        representative = [first[3][index] for index in first_projection]
        key = [first[4][index] for index in first_projection]
        for factor_id, projection in zip(input_ids[1:], projections[1:]):
            local9, local2, local_weight, local_rep, local_key = tables[factor_id]
            sum9 = [value * local9[index] for value, index in zip(sum9, projection)]
            sum2 = [value * local2[index] for value, index in zip(sum2, projection)]
            weight = [value + local_weight[index] for value, index in zip(weight, projection)]
            representative = [value | local_rep[index] for value, index in zip(representative, projection)]
            key = [value | local_key[index] for value, index in zip(key, projection)]
        out9 = [sum9[left] + sum9[right] for left, right in zip(low, high)]
        out2 = [sum2[left] + sum2[right] for left, right in zip(low, high)]
        out_weight: list[int] = []
        out_rep: list[int] = []
        out_key: list[int] = []
        append_weight = out_weight.append
        append_rep = out_rep.append
        append_key = out_key.append
        for left, right in zip(low, high):
            left_weight = weight[left]
            right_weight = weight[right]
            left_rep = representative[left]
            right_rep = representative[right]
            if right_weight < left_weight or (right_weight == left_weight and right_rep < left_rep):
                append_weight(right_weight)
                append_rep(right_rep)
            else:
                append_weight(left_weight)
                append_rep(left_rep)
            left_key = key[left]
            right_key = key[right]
            append_key(right_key if right_key < left_key else left_key)
        tables[output_id] = (out9, out2, out_weight, out_rep, out_key)
        for factor_id in input_ids:
            del tables[factor_id]
    final9 = final2 = 1
    final_weight = final_rep = final_key = 0
    for factor_id in final_ids:
        values = tables[factor_id]
        final9 *= values[0][0]
        final2 *= values[1][0]
        final_weight += values[2][0]
        final_rep |= values[3][0]
        final_key |= values[4][0]
    return final9, final2, ((final_weight, final_rep), final_key)


def evaluate_compiled_descriptor(seed: int, scopes: list[tuple[int, ...]], descriptor: dict[str, Any]) -> tuple[int, int, tuple[tuple[int, int], int]]:
    plan, final_ids = runtime_plan_from_descriptor(descriptor)
    return evaluate_projection_plan(seed, scopes, plan, final_ids)


def independent_fixed_selector_oracle(seed: int, scopes: list[tuple[int, ...]], order: list[int]) -> tuple[int, int, tuple[tuple[int, int], int]]:
    plan, final_ids = independent_runtime_plan(scopes, order)
    return evaluate_projection_plan(seed, scopes, plan, final_ids)


_VALIDATION_SCOPES: list[tuple[int, ...]] | None = None
_VALIDATION_SELECTOR_BASIS: list[int] | None = None
_VALIDATION_COMPILED_PLAN = None
_VALIDATION_COMPILED_FINALS = None
_VALIDATION_ORACLE_PLAN = None
_VALIDATION_ORACLE_FINALS = None


def _validation_worker_init(scopes: list[tuple[int, ...]], selector_basis: list[int], order: list[int], descriptor: dict[str, Any]) -> None:
    global _VALIDATION_SCOPES, _VALIDATION_SELECTOR_BASIS
    global _VALIDATION_COMPILED_PLAN, _VALIDATION_COMPILED_FINALS
    global _VALIDATION_ORACLE_PLAN, _VALIDATION_ORACLE_FINALS
    _VALIDATION_SCOPES = scopes
    _VALIDATION_SELECTOR_BASIS = selector_basis
    _VALIDATION_COMPILED_PLAN, _VALIDATION_COMPILED_FINALS = runtime_plan_from_descriptor(descriptor)
    _VALIDATION_ORACLE_PLAN, _VALIDATION_ORACLE_FINALS = independent_runtime_plan(scopes, order)


def _validation_worker(coordinate: int) -> dict[str, Any]:
    if _VALIDATION_SCOPES is None or _VALIDATION_SELECTOR_BASIS is None or _VALIDATION_COMPILED_PLAN is None or _VALIDATION_COMPILED_FINALS is None or _VALIDATION_ORACLE_PLAN is None or _VALIDATION_ORACLE_FINALS is None:
        raise RuntimeError("validation worker not initialized")
    seed = selector_lift(coordinate, _VALIDATION_SELECTOR_BASIS)
    compiled = evaluate_projection_plan(seed, _VALIDATION_SCOPES, _VALIDATION_COMPILED_PLAN, _VALIDATION_COMPILED_FINALS)
    oracle = evaluate_projection_plan(seed, _VALIDATION_SCOPES, _VALIDATION_ORACLE_PLAN, _VALIDATION_ORACLE_FINALS)
    if compiled != oracle:
        raise ValueError(f"SEMANTIC_EQUIVALENCE_FAILED at selector {coordinate}")
    return {"coordinate": coordinate, "sum_product_bsc_p_0_1": str(compiled[0]), "soft_tropical_base_2": str(compiled[1]), "min_weight": compiled[2][0][0], "representative": str(compiled[2][0][1]), "canonical_key": str(compiled[2][1])}


def run_validation_parallel(coordinates: list[int], scopes: list[tuple[int, ...]], selector_basis: list[int], order: list[int], descriptor: dict[str, Any], *, processes: int | None = None) -> list[dict[str, Any]]:
    import multiprocessing
    import os
    worker_count = processes or min(4, os.cpu_count() or 1)
    if worker_count <= 1:
        _validation_worker_init(scopes, selector_basis, order, descriptor)
        return [_validation_worker(coordinate) for coordinate in coordinates]
    available = multiprocessing.get_all_start_methods()
    method = "fork" if "fork" in available else "spawn"
    context = multiprocessing.get_context(method)
    with context.Pool(processes=worker_count, initializer=_validation_worker_init, initargs=(scopes, selector_basis, order, descriptor)) as pool:
        return pool.map(_validation_worker, coordinates, chunksize=1)
