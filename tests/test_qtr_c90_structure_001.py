from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "reference"
if str(REFERENCE) not in sys.path:
    sys.path.insert(0, str(REFERENCE))

import qldpc_scale_001a_math as math001a
import qtr_c90_structure_001 as structure


class TestQTRC90Structure001(unittest.TestCase):
    def test_manifest_freezes_exact_family_and_caps(self) -> None:
        manifest = structure.load_manifest()
        self.assertEqual(
            list(manifest["methods"]),
            [
                "S0_BASELINE",
                "S1_GF2_CONSTRAINT_ELIMINATION",
                "S2_SEPARATOR_INTERFACE_COMPILATION",
                "S3_GF2_PLUS_SEPARATOR",
            ],
        )
        caps = manifest["resource_envelope"]
        self.assertEqual(caps["max_peak_joint_or_interface_entries"], 100 * (1 << 20))
        self.assertEqual(caps["max_factor_or_constraint_entry_evaluations_per_algebra"], 1 << 27)
        self.assertEqual(caps["max_retained_canonical_structural_nodes_or_entries_per_algebra"], 1 << 22)
        self.assertEqual(caps["max_canonical_serialized_compiled_bytes_per_algebra"], 512 * 1024 * 1024)
        self.assertEqual(caps["max_compilation_aop_events_per_algebra"], 1 << 31)

    def test_s1_refuses_weighted_factors_as_gf2_equations(self) -> None:
        result = structure.no_hard_affine_constraints()
        self.assertEqual(result["hard_affine_factor_count"], 0)
        self.assertEqual(result["s1_action"], "IDENTITY_NO_ELIGIBLE_HARD_AFFINE_FACTORS")
        self.assertTrue(all(result["per_algebra_full_support"].values()))

    def test_separator_compiler_is_deterministic_and_running_intersection(self) -> None:
        code = math001a.construct_code()
        scopes = code["scopes"]
        order = math001a.deterministic_min_fill(scopes, len(code["x_basis"]))
        left = structure.junction_tree(scopes, order)
        right = structure.junction_tree(scopes, order)
        self.assertEqual(left["canonical_sha256"], right["canonical_sha256"])
        bags = [set(row) for row in left["maximal_bags"]]
        for factor_index, scope in enumerate(scopes):
            self.assertTrue(set(scope) <= bags[left["factor_assignment"][factor_index]])
        adjacency = [[] for _ in bags]
        for edge in left["tree_edges"]:
            adjacency[edge["left"]].append(edge["right"])
            adjacency[edge["right"]].append(edge["left"])
        variables = set().union(*bags)
        for variable in variables:
            nodes = [index for index, bag in enumerate(bags) if variable in bag]
            seen = {nodes[0]}
            frontier = [nodes[0]]
            allowed = set(nodes)
            while frontier:
                current = frontier.pop()
                for nxt in adjacency[current]:
                    if nxt in allowed and nxt not in seen:
                        seen.add(nxt)
                        frontier.append(nxt)
            self.assertEqual(seen, allowed, f"running intersection failed for variable {variable}")
        self.assertEqual(
            sorted(left["separator_elimination_order"]),
            list(range(len(code["x_basis"]))),
        )

    def test_protected_s0_and_identity_s1_replay_without_new_control_outcomes(self) -> None:
        report = structure.evaluate_static(full_control=False)
        self.assertTrue(report["s0_replay"]["matches_protected_predecessor"])
        self.assertEqual(report["s0_replay"]["factor_table_entry_evaluations"], 201384562)
        self.assertEqual(report["s0_replay"]["peak_joint_table_entries"], 67108864)
        self.assertEqual(report["s0_replay"]["mandatory_compilation_aop_lower_bound"], 3410023338)
        self.assertEqual(
            report["c90_methods"]["S1_GF2_CONSTRAINT_ELIMINATION"]["c90_status"],
            "C90_STATIC_CAP_EXHAUSTED",
        )
        self.assertEqual(
            report["c90_methods"]["S2_SEPARATOR_INTERFACE_COMPILATION"]["c90_status"],
            "NOT_ADJUDICATED_CONTROL_NOT_CERTIFIED",
        )
        self.assertEqual(
            report["c90_methods"]["S3_GF2_PLUS_SEPARATOR"]["c90_status"],
            "NOT_ADJUDICATED_CONTROL_NOT_CERTIFIED",
        )
        self.assertFalse(report["phase_d_reached"])
        self.assertFalse(report["phase_e_reached"])

    def test_manifest_self_digest_is_canonical(self) -> None:
        raw = json.loads((ROOT / "registry/qtr-c90-structure-001-manifest.json").read_text())
        claimed = raw.pop("manifest_payload_sha256")
        from qldpc_scale_001a_shared import digest
        self.assertEqual(claimed, structure.MANIFEST_PAYLOAD)
        self.assertEqual(digest(raw), claimed)


if __name__ == "__main__":
    unittest.main()
