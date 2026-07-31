from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ci"))

from schema_validation import SchemaValidationError, validate_instance  # noqa: E402
from verify_migration import assert_runtime_head  # noqa: E402


class CompleteSchemaValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(
            (ROOT / "schemas" / "signal-candidate.schema.json").read_text()
        )
        registry = json.loads(
            (ROOT / "registry" / "signal-candidates.json").read_text()
        )
        cls.good = registry["candidates"][0]

    def assert_invalid(self, mutate):
        candidate = copy.deepcopy(self.good)
        mutate(candidate)
        with self.assertRaises(SchemaValidationError):
            validate_instance(candidate, self.schema)

    def test_nested_unknown_field_fails_closed(self):
        self.assert_invalid(lambda c: c["readout"].__setitem__("unknown", True))

    def test_wrong_schema_version_fails_closed(self):
        self.assert_invalid(lambda c: c.__setitem__("schema_version", "0.1.0"))

    def test_invalid_candidate_id_pattern_fails_closed(self):
        self.assert_invalid(lambda c: c.__setitem__("candidate_id", "Bad ID"))

    def test_wrong_query_unit_fails_closed(self):
        self.assert_invalid(
            lambda c: c["oracle_model"].__setitem__("query_unit", "free_qram")
        )

    def test_missing_nested_readout_field_fails_closed(self):
        self.assert_invalid(lambda c: c["readout"].pop("one_region"))

    def test_invalid_array_item_type_fails_closed(self):
        self.assert_invalid(lambda c: c["limitations"].append(17))

    def test_unique_array_constraint_fails_closed(self):
        candidate = copy.deepcopy(self.good)
        candidate["promise_domain"] = {
            "kind": "hamming_weights",
            "weights": [0, 0],
            "description": "Duplicate weights must fail.",
        }
        with self.assertRaises(SchemaValidationError):
            validate_instance(candidate, self.schema)

    def test_exact_head_receipt_mismatch_fails_closed(self):
        with self.assertRaises(SystemExit):
            assert_runtime_head("expected", observed="different")


if __name__ == "__main__":
    unittest.main()
