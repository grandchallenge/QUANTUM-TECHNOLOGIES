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


class QTRC90ExactOracleCheckpoint001Tests(unittest.TestCase):
    CONTEXT = {
        "code": {
            "selector_basis_qubits": [0, 2],
            "scopes": [[0], [0, 1], [1]],
        },
        "order": [0, 1],
    }

    def test_checkpointed_oracle_matches_direct_contraction(self) -> None:
        for algebra in DAG.ALGEBRAS:
            for coordinate in range(4):
                with self.subTest(algebra=algebra, coordinate=coordinate):
                    expected = DAG.direct_contract_selector(self.CONTEXT, algebra, coordinate)
                    state, partial = Oracle.advance(
                        self.CONTEXT, algebra, coordinate, state=None, stop_step=1
                    )
                    self.assertIsNone(partial)
                    with tempfile.TemporaryDirectory(prefix="qtr-c90-oracle-checkpoint-") as tmp:
                        checkpoint = Path(tmp) / "state.pkl"
                        receipt = Path(tmp) / "state.json"
                        Oracle.save_checkpoint(checkpoint, receipt, state)
                        restored = Oracle.load_checkpoint(
                            checkpoint, receipt, self.CONTEXT, algebra, coordinate
                        )
                        completed, observed = Oracle.advance(
                            self.CONTEXT,
                            algebra,
                            coordinate,
                            state=restored,
                            stop_step=len(self.CONTEXT["order"]),
                        )
                    self.assertEqual(completed["next_step"], len(self.CONTEXT["order"]))
                    self.assertEqual(observed, expected)

    def test_uninterrupted_checkpoint_orchestrator_matches_direct_contraction(self) -> None:
        for algebra in DAG.ALGEBRAS:
            for coordinate in range(4):
                with self.subTest(algebra=algebra, coordinate=coordinate):
                    _, observed = Oracle.advance(
                        self.CONTEXT,
                        algebra,
                        coordinate,
                        state=None,
                        stop_step=len(self.CONTEXT["order"]),
                    )
                    expected = DAG.direct_contract_selector(self.CONTEXT, algebra, coordinate)
                    self.assertEqual(observed, expected)

    def test_checkpoint_digest_rejects_mutation(self) -> None:
        state, _ = Oracle.advance(
            self.CONTEXT, "sum_product_bsc_p_0_1", 0, state=None, stop_step=1
        )
        with tempfile.TemporaryDirectory(prefix="qtr-c90-oracle-checkpoint-tamper-") as tmp:
            checkpoint = Path(tmp) / "state.pkl"
            receipt = Path(tmp) / "state.json"
            Oracle.save_checkpoint(checkpoint, receipt, state)
            checkpoint.write_bytes(checkpoint.read_bytes() + b"x")
            with self.assertRaisesRegex(ValueError, "binary digest drift"):
                Oracle.load_checkpoint(
                    checkpoint,
                    receipt,
                    self.CONTEXT,
                    "sum_product_bsc_p_0_1",
                    0,
                )


if __name__ == "__main__":
    unittest.main()
