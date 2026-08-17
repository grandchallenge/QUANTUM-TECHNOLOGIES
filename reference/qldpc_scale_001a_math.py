from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path
from typing import Any
import numpy as np
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from qldpc_scale_001a_shared import *

def rank_rref(matrix: np.ndarray) -> tuple[int, list[int], np.ndarray]:
    a = matrix.copy().astype(np.uint8)
    row = 0
    pivots: list[int] = []
    for col in range(a.shape[1]):
        candidates = np.flatnonzero(a[row:, col])
        if not len(candidates):
            continue
        pivot = row + int(candidates[0])
        a[[row, pivot]] = a[[pivot, row]]
        for other in range(a.shape[0]):
            if other != row and a[other, col]:
                a[other] ^= a[row]
        pivots.append(col)
        row += 1
        if row == a.shape[0]:
            break
    return row, pivots, a


def lexicographic_independent_rows(matrix: np.ndarray) -> tuple[list[int], np.ndarray]:
    chosen: list[int] = []
    current = np.zeros((0, matrix.shape[1]), dtype=np.uint8)
    rank = 0
    for index, candidate in enumerate(matrix):
        trial = np.vstack((current, candidate))
        new_rank = rank_rref(trial)[0]
        if new_rank > rank:
            chosen.append(index)
            current = trial
            rank = new_rank
    return chosen, current


def canonical_nullspace_basis(matrix: np.ndarray) -> tuple[list[int], np.ndarray]:
    _, pivots, rref = rank_rref(matrix)
    free = [col for col in range(matrix.shape[1]) if col not in pivots]
    basis: list[np.ndarray] = []
    for free_col in free:
        vector = np.zeros(matrix.shape[1], dtype=np.uint8)
        vector[free_col] = 1
        for row, pivot in enumerate(pivots):
            if rref[row, free_col]:
                vector[pivot] = 1
        basis.append(vector)
    return free, np.array(basis, dtype=np.uint8)


def construct_code() -> dict[str, Any]:
    ell = SOURCE["ell"]
    m = SOURCE["m"]
    i_ell = np.eye(ell, dtype=np.uint8)
    i_m = np.eye(m, dtype=np.uint8)
    x = {i: np.kron(np.roll(i_ell, i, axis=1), i_m) % 2 for i in range(ell)}
    y = {i: np.kron(i_ell, np.roll(i_m, i, axis=1)) % 2 for i in range(m)}
    a = (x[3] + y[1] + y[2]) % 2
    b = (y[3] + x[1] + x[2]) % 2
    hx = np.hstack((a, b)) % 2
    hz = np.hstack((b.T, a.T)) % 2
    x_indices, x_basis = lexicographic_independent_rows(hx)
    z_indices, z_basis = lexicographic_independent_rows(hz)
    free_columns, kernel_basis = canonical_nullspace_basis(hx)
    current = z_basis.copy()
    current_rank = rank_rref(current)[0]
    logical_z: list[np.ndarray] = []
    selected_free_columns: list[int] = []
    for free_col, vector in zip(free_columns, kernel_basis):
        trial = np.vstack((current, vector))
        new_rank = rank_rref(trial)[0]
        if new_rank > current_rank:
            logical_z.append(vector.copy())
            selected_free_columns.append(free_col)
            current = trial
            current_rank = new_rank
    logical_z_matrix = np.array(logical_z, dtype=np.uint8)
    selector_rows = np.vstack((z_basis, logical_z_matrix))
    selector_basis_qubits = lexicographic_independent_rows(selector_rows.T)[0]
    scopes = [tuple(index for index, row in enumerate(x_basis) if row[qubit]) for qubit in range(hx.shape[1])]
    return {"hx": hx, "hz": hz, "x_indices": x_indices, "x_basis": x_basis, "z_indices": z_indices, "z_basis": z_basis, "free_columns": free_columns, "selected_free_columns": selected_free_columns, "logical_z": logical_z_matrix, "selector_rows": selector_rows, "selector_basis_qubits": selector_basis_qubits, "scopes": scopes}


def row_to_int(row: np.ndarray) -> int:
    return sum(int(bit) << index for index, bit in enumerate(row.tolist()))


def matrix_record(matrix: np.ndarray) -> dict[str, Any]:
    width = (matrix.shape[1] + 3) // 4
    return {"n_rows": int(matrix.shape[0]), "n_cols": int(matrix.shape[1]), "row_hex": [f"{row_to_int(row):0{width}x}" for row in matrix]}


def source_and_basis_records(code: dict[str, Any]) -> dict[str, Any]:
    hx_record = matrix_record(code["hx"])
    hz_record = matrix_record(code["hz"])
    bases = {"x_indices": code["x_indices"], "x_rows": [hx_record["row_hex"][i] for i in code["x_indices"]], "z_indices": code["z_indices"], "z_rows": [hz_record["row_hex"][i] for i in code["z_indices"]]}
    logical = {"kernel_free_columns": code["free_columns"], "selected_free_columns": code["selected_free_columns"], "logical_z_rows": matrix_record(code["logical_z"])["row_hex"], "construction": "canonical_rref_nullspace_scan_extend_z_stabilizer_rowspace"}
    selector = {"rank": len(code["selector_basis_qubits"]), "basis_qubits": code["selector_basis_qubits"], "coordinate_rule": "coordinate_bit_i_selects_physical_unit_error_at_basis_qubits[i]", "logical_dimension": len(code["logical_z"])}
    scope_record = {"stabilizer_basis_indices": code["x_indices"], "scopes": [list(scope) for scope in code["scopes"]]}
    return {"source_record": SOURCE, "hx_record": hx_record, "hz_record": hz_record, "bases": bases, "logical": logical, "selector": selector, "scope_record": scope_record}


def primal_graph(scopes: list[tuple[int, ...]], variable_count: int) -> list[set[int]]:
    adjacency = [set() for _ in range(variable_count)]
    for scope in scopes:
        for pos, left in enumerate(scope):
            for right in scope[pos + 1:]:
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
            fill = sum(1 for pos, left in enumerate(neighbors) for right in neighbors[pos + 1:] if right not in adjacency[left])
            candidates.append((fill, variable))
        _, variable = min(candidates)
        neighbors = sorted(adjacency[variable] & active)
        for pos, left in enumerate(neighbors):
            for right in neighbors[pos + 1:]:
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
        for pos, left in enumerate(neighbors):
            for right in neighbors[pos + 1:]:
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
        for pos, left in enumerate(neighbors):
            for right in neighbors[pos + 1:]:
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
        step_record = {"step": step, "variable": variable, "input_ids": [factor_id for factor_id, _ in involved], "output_id": output_id, "union_scope": list(union), "output_scope": list(output_scope), "eliminated_union_position": union_positions[variable], "projection_maps": projection_maps}
        steps.append(step_record)
        structural_entries += len(union) + len(output_scope) + len(involved) + 5
        joint = 1 << len(union)
        output = 1 << len(output_scope)
        peak_runtime_projection_entries = max(peak_runtime_projection_entries, len(involved) * joint + 2 * output)
        rest.append((output_id, output_scope))
        factors = rest
    descriptor = {"format": "QTR-QLDPC-SCALE-001A-COMPILED-DESCRIPTOR-v1", "selector_basis_qubits": selector_basis, "selector_parameter_count": len(selector_basis), "initial_factor_scopes": [list(scope) for scope in scopes], "elimination_order": order, "steps": steps, "final_factor_ids": [factor_id for factor_id, _ in factors], "runtime_projection_policy": "generate_exact_flat_index_arrays_lazily_per_step_from_projection_maps_then_discard", "selector_values_materialized_during_compilation": 0, "answer_cache_entries": 0}
    raw = json.dumps(descriptor, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    metadata = {"canonical_sha256": hashlib.sha256(raw).hexdigest(), "canonical_serialized_bytes": len(raw), "structural_scalar_entries": structural_entries, "step_count": len(steps), "selector_values_materialized_during_compilation": 0, "answer_cache_entries": 0, "peak_runtime_projection_index_entries": peak_runtime_projection_entries}
    return descriptor, metadata


def generate_projection(scope_positions: list[int], union_arity: int) -> np.ndarray:
    assignments = np.arange(1 << union_arity, dtype=np.uint32)
    index = np.zeros(len(assignments), dtype=np.uint32)
    for factor_position, union_position in enumerate(scope_positions):
        index |= (((assignments >> union_position) & 1) << factor_position).astype(np.uint32)
    return index


def marginal_indices(union_arity: int, eliminated_position: int) -> tuple[np.ndarray, np.ndarray]:
    output = np.arange(1 << (union_arity - 1), dtype=np.uint32)
    low = (output & ((1 << eliminated_position) - 1)) | ((output >> eliminated_position) << (eliminated_position + 1))
    return low, low | (1 << eliminated_position)


def selector_lift(coordinate: int, selector_basis: list[int]) -> int:
    seed = 0
    for index, qubit in enumerate(selector_basis):
        if (coordinate >> index) & 1:
            seed |= 1 << qubit
    return seed


def local_tables(seed: int, scopes: list[tuple[int, ...]]) -> dict[int, tuple[np.ndarray, ...]]:
    tables: dict[int, tuple[np.ndarray, ...]] = {}
    for qubit, scope in enumerate(scopes):
        size = 1 << len(scope)
        base = (seed >> qubit) & 1
        sum9 = np.empty(size, dtype=object)
        sum2 = np.empty(size, dtype=object)
        weight = np.empty(size, dtype=np.uint16)
        rep_low = np.zeros(size, dtype=np.uint64)
        rep_high = np.zeros(size, dtype=np.uint8)
        key_low = np.zeros(size, dtype=np.uint64)
        key_high = np.zeros(size, dtype=np.uint8)
        for assignment in range(size):
            bit = base ^ (assignment.bit_count() & 1)
            sum9[assignment] = 9 if bit == 0 else 1
            sum2[assignment] = 2 if bit == 0 else 1
            weight[assignment] = bit
            if bit:
                if qubit < 64:
                    value = np.uint64(1) << np.uint64(qubit)
                    rep_low[assignment] = value
                    key_low[assignment] = value
                else:
                    value = np.uint8(1 << (qubit - 64))
                    rep_high[assignment] = value
                    key_high[assignment] = value
        tables[qubit] = (sum9, sum2, weight, rep_low, rep_high, key_low, key_high)
    return tables


def combine_min(parts: list[tuple[np.ndarray, ...]]) -> tuple[np.ndarray, ...]:
    weight = rep_low = rep_high = key_low = key_high = None
    for w, rl, rh, kl, kh in parts:
        if weight is None:
            weight = w.astype(np.uint16)
            rep_low = rl.copy(); rep_high = rh.copy(); key_low = kl.copy(); key_high = kh.copy()
        else:
            weight = weight + w
            rep_low = np.bitwise_or(rep_low, rl); rep_high = np.bitwise_or(rep_high, rh)
            key_low = np.bitwise_or(key_low, kl); key_high = np.bitwise_or(key_high, kh)
    assert weight is not None and rep_low is not None and rep_high is not None and key_low is not None and key_high is not None
    return weight, rep_low, rep_high, key_low, key_high


def marginal_min(values: tuple[np.ndarray, ...], low: np.ndarray, high: np.ndarray) -> tuple[np.ndarray, ...]:
    weight, rep_low, rep_high, key_low, key_high = values
    w0, w1 = weight[low], weight[high]
    rl0, rl1 = rep_low[low], rep_low[high]
    rh0, rh1 = rep_high[low], rep_high[high]
    kl0, kl1 = key_low[low], key_low[high]
    kh0, kh1 = key_high[low], key_high[high]
    choose1 = (w1 < w0) | ((w1 == w0) & ((rh1 < rh0) | ((rh1 == rh0) & (rl1 < rl0))))
    out_weight = np.where(choose1, w1, w0)
    out_rep_low = np.where(choose1, rl1, rl0)
    out_rep_high = np.where(choose1, rh1, rh0)
    choose_key1 = (kh1 < kh0) | ((kh1 == kh0) & (kl1 < kl0))
    out_key_low = np.where(choose_key1, kl1, kl0)
    out_key_high = np.where(choose_key1, kh1, kh0)
    return out_weight, out_rep_low, out_rep_high, out_key_low, out_key_high


def finish_tables(tables: dict[int, tuple[np.ndarray, ...]], final_ids: list[int]) -> tuple[int, int, tuple[tuple[int, int], int]]:
    sum9 = sum2 = 1
    weight = rep_low = rep_high = key_low = key_high = 0
    for factor_id in final_ids:
        values = tables[factor_id]
        sum9 *= int(values[0][0]); sum2 *= int(values[1][0]); weight += int(values[2][0])
        rep_low |= int(values[3][0]); rep_high |= int(values[4][0]); key_low |= int(values[5][0]); key_high |= int(values[6][0])
    representative = rep_low | (rep_high << 64)
    key = key_low | (key_high << 64)
    return sum9, sum2, ((weight, representative), key)


def evaluate_compiled_descriptor(seed: int, scopes: list[tuple[int, ...]], descriptor: dict[str, Any]) -> tuple[int, int, tuple[tuple[int, int], int]]:
    tables = local_tables(seed, scopes)
    for step in descriptor["steps"]:
        union_arity = len(step["union_scope"])
        projections = [generate_projection(mapping["union_positions"], union_arity) for mapping in step["projection_maps"]]
        low, high = marginal_indices(union_arity, step["eliminated_union_position"])
        sum9 = sum2 = None
        min_parts = []
        for factor_id, projection in zip(step["input_ids"], projections):
            values = tables[factor_id]
            part9 = values[0][projection]; part2 = values[1][projection]
            sum9 = part9 if sum9 is None else sum9 * part9
            sum2 = part2 if sum2 is None else sum2 * part2
            min_parts.append(tuple(value[projection] for value in values[2:]))
        assert sum9 is not None and sum2 is not None
        min_values = combine_min(min_parts)
        tables[step["output_id"]] = (sum9[low] + sum9[high], sum2[low] + sum2[high], *marginal_min(min_values, low, high))
        for factor_id in step["input_ids"]:
            del tables[factor_id]
    return finish_tables(tables, descriptor["final_factor_ids"])


def independent_fixed_selector_oracle(seed: int, scopes: list[tuple[int, ...]], order: list[int]) -> tuple[int, int, tuple[tuple[int, int], int]]:
    tables = local_tables(seed, scopes)
    factors = [(index, tuple(scope)) for index, scope in enumerate(scopes)]
    next_id = len(factors)
    for variable in order:
        involved = [factor for factor in factors if variable in factor[1]]
        rest = [factor for factor in factors if variable not in factor[1]]
        union = tuple(sorted(set().union(*(set(scope) for _, scope in involved))))
        union_positions = {item: position for position, item in enumerate(union)}
        projections = [generate_projection([union_positions[item] for item in scope], len(union)) for _, scope in involved]
        low, high = marginal_indices(len(union), union_positions[variable])
        sum9 = sum2 = None
        min_parts = []
        for (factor_id, _), projection in zip(involved, projections):
            values = tables[factor_id]
            part9 = values[0][projection]; part2 = values[1][projection]
            sum9 = part9 if sum9 is None else sum9 * part9
            sum2 = part2 if sum2 is None else sum2 * part2
            min_parts.append(tuple(value[projection] for value in values[2:]))
        assert sum9 is not None and sum2 is not None
        min_values = combine_min(min_parts)
        tables[next_id] = (sum9[low] + sum9[high], sum2[low] + sum2[high], *marginal_min(min_values, low, high))
        for factor_id, _ in involved:
            del tables[factor_id]
        rest.append((next_id, tuple(item for item in union if item != variable)))
        next_id += 1
        factors = rest
    return finish_tables(tables, [factor_id for factor_id, _ in factors])
