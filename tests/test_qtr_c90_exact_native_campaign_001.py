#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "reference"
if str(REF) not in sys.path:
    sys.path.insert(0, str(REF))

import qtr_c90_exact_native_campaign_001 as Campaign
import tcm_c72_interface_001 as C72


class NativeCampaignTests(unittest.TestCase):
    def test_shard_is_exactly_one_logical_class_across_all_347_inputs(self) -> None:
        for logical_class in (0, 1, 127, 255):
            rows = Campaign.selector_metadata(logical_class)
            self.assertEqual(len(rows), 347)
            self.assertEqual(
                [row["global_index"] for row in rows],
                [index * 256 + logical_class for index in range(347)],
            )
            self.assertTrue(all(0 <= row["coordinate"] < (1 << 49) for row in rows))
            self.assertTrue(
                all((row["functional"] >> 41) == logical_class for row in rows)
            )

    def test_256_shards_partition_full_frozen_decode_domain(self) -> None:
        ids = {
            input_index * 256 + logical_class
            for logical_class in range(256)
            for input_index in range(347)
        }
        self.assertEqual(len(ids), 347 * 256)
        self.assertEqual(min(ids), 0)
        self.assertEqual(max(ids), 347 * 256 - 1)

    def test_native_class_record_feeds_unchanged_c72_decision_rule(self) -> None:
        context = Campaign.frozen_context()
        corpus0 = Campaign.frozen_corpus()[0]
        error = Campaign.Base.F2.b2i(corpus0["error"])
        syndrome = Campaign.Base.F2.syndrome(error, context["code"]["hz"])
        records = []
        for logical_class in range(256):
            seed, coordinate, functional = Campaign.Base.selector_seed_for(
                context, syndrome, logical_class
            )
            meta = {
                "coordinate": coordinate,
                "functional": functional,
            }
            sum_row = {
                "selector_coordinate": coordinate,
                "value_hex": hex(1000 + logical_class),
            }
            soft_row = {
                "selector_coordinate": coordinate,
                "value_hex": hex(2000 + (255 - logical_class)),
            }
            min_row = {
                "selector_coordinate": coordinate,
                "minimum_weight": seed.bit_count(),
                "minimum_representative_hex": hex(seed),
                "canonical_hex": hex(seed),
            }
            records.append(
                Campaign.class_record_from_native(
                    logical_class=logical_class,
                    meta=meta,
                    sum_row=sum_row,
                    soft_row=soft_row,
                    min_row=min_row,
                )
            )
        decisions = C72.decision_from_class_records(records, 90)
        self.assertEqual(decisions["sum_product_bsc_p_0_1"]["logical_class"], 255)
        self.assertEqual(decisions["soft_tropical_base_2"]["logical_class"], 0)
        for cell in decisions.values():
            self.assertLess(int(cell["correction"]), 1 << 90)

    def test_selector_file_has_347_rows_and_global_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "selectors.txt"
            Campaign.write_selector_file(7, path)
            rows = [line.split() for line in path.read_text().splitlines()]
            self.assertEqual(len(rows), 347)
            self.assertEqual(int(rows[0][0]), 7)
            self.assertEqual(int(rows[-1][0]), 346 * 256 + 7)


if __name__ == "__main__":
    unittest.main()
