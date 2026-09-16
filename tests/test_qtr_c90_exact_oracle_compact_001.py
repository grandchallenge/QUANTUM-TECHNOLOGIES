from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "reference"
if str(REFERENCE) not in sys.path:
    sys.path.insert(0, str(REFERENCE))

import qtr_c90_exact_dag_001 as DAG
import qtr_c90_exact_oracle_checkpoint_001 as Oracle
import qtr_c90_exact_oracle_compact_001 as Compact


class QTRC90ExactOracleCompact001Tests(unittest.TestCase):
    CONTEXT = {
        "code": {
            "selector_basis_qubits": [0, 2],
            "scopes": [[0], [0, 1], [1]],
        },
        "order": [0, 1],
    }

    @staticmethod
    def _append_unreachable(state: dict) -> int:
        nodes = state["nodes"]
        before = len(nodes)
        left = len(nodes)
        nodes.append(("T", 123456789))
        right = len(nodes)
        nodes.append(("T", 987654321))
        nodes.append(("D", 0, left, right))
        return before

    def test_exact_gc_removes_only_unreachable_and_preserves_completion(self) -> None:
        for algebra in DAG.ALGEBRAS:
            for coordinate in range(4):
                with self.subTest(algebra=algebra, coordinate=coordinate):
                    expected = DAG.direct_contract_selector(self.CONTEXT, algebra, coordinate)
                    state, partial = Oracle.advance(
                        self.CONTEXT,
                        algebra,
                        coordinate,
                        state=None,
                        stop_step=1,
                    )
                    self.assertIsNone(partial)
                    original_step = state["next_step"]
                    original_scopes = [tuple(scope) for scope, _ in state["factors"]]
                    before_unreachable = self._append_unreachable(state)
                    compacted, metrics = Compact.compact_state(
                        self.CONTEXT,
                        algebra,
                        coordinate,
                        state,
                    )
                    self.assertEqual(compacted["next_step"], original_step)
                    self.assertEqual(
                        [tuple(scope) for scope, _ in compacted["factors"]],
                        original_scopes,
                    )
                    self.assertGreaterEqual(metrics["removed_node_count"], 3)
                    self.assertLess(metrics["retained_node_count"], before_unreachable + 3)
                    _, observed = Oracle.advance(
                        self.CONTEXT,
                        algebra,
                        coordinate,
                        state=compacted,
                        stop_step=len(self.CONTEXT["order"]),
                    )
                    self.assertEqual(observed, expected)

    def test_compacted_checkpoint_roundtrip_preserves_exact_result(self) -> None:
        algebra = "sum_product_bsc_p_0_1"
        coordinate = 3
        expected = DAG.direct_contract_selector(self.CONTEXT, algebra, coordinate)
        state, _ = Oracle.advance(
            self.CONTEXT,
            algebra,
            coordinate,
            state=None,
            stop_step=1,
        )
        self._append_unreachable(state)
        compacted, _ = Compact.compact_state(
            self.CONTEXT,
            algebra,
            coordinate,
            state,
        )
        with tempfile.TemporaryDirectory(prefix="qtr-c90-oracle-compact-") as tmp:
            checkpoint = Path(tmp) / "state.pkl"
            receipt = Path(tmp) / "state.json"
            Oracle.save_checkpoint(checkpoint, receipt, compacted)
            restored = Oracle.load_checkpoint(
                checkpoint,
                receipt,
                self.CONTEXT,
                algebra,
                coordinate,
            )
            _, observed = Oracle.advance(
                self.CONTEXT,
                algebra,
                coordinate,
                state=restored,
                stop_step=len(self.CONTEXT["order"]),
            )
        self.assertEqual(observed, expected)


if __name__ == "__main__":
    unittest.main()
