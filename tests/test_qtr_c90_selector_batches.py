"""Source-locked C90 transport tests; no scientific scoring or native evaluation."""
import hashlib
import importlib.util
import json
import pathlib
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts/qtr_c90_selector_batches.py"
spec = importlib.util.spec_from_file_location("qtr_batch_transport", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class BatchTransportTests(unittest.TestCase):
    def test_original_class0_two_algebras_and_tamper(self):
        root = pathlib.Path.home() / ".local/share/gcl-qtr-evidence/2026-11-19"
        records = (
            root / "colab-sumproduct-pilot-002/returned-class-0/rows-sum_product_bsc_p_0_1-class-0.jsonl",
            root / "colab-preflight/returned-class-0/rows-min_plus_hamming-class-0.jsonl",
        )
        if not all(f.exists() for f in records):
            self.skipTest("private original-native fixture not present on runner")
        for original in records:
            with self.subTest(original=original.name), tempfile.TemporaryDirectory() as tmp:
                tmp = pathlib.Path(tmp)
                old = original.read_bytes()
                lines = old.splitlines(keepends=True)
                assert len(lines) == 347
                inp = tmp / "selectors.txt"
                inp.write_text("".join(
                    f"{json.loads(line)['selector_index']} {json.loads(line)['selector_coordinate']}\n"
                    for line in lines
                ))
                folder = tmp / "class-0"
                mod.plan(inp, folder, 16, 0, "min_plus_hamming" if "min_plus" in original.name else "sum_product_bsc_p_0_1")
                manifest = json.loads((folder / "manifest.json").read_text())
                self.assertEqual([e["count"] for e in manifest["entries"]], [16]*21+[11])
                for e in manifest["entries"]:
                    (folder / f"batch-{e['number']:03d}.rows.jsonl").write_bytes(
                        b"".join(lines[e["start"]:e["start"]+e["count"]])
                    )
                alg = manifest["algebra"]
                for e in manifest["entries"]:
                    chunk = folder / f"batch-{e['number']:03d}.rows.jsonl"
                    claim = {
                        "record_type":"QTR_C90_FROZEN_NATIVE_BATCH_CUSTODY/1",
                        "source_head":mod.HEAD,"activation_head":mod.ACTIVATION,
                        "logical_class":0,"algebra":alg,
                        "native_graph_sha256":mod.GRAPHS[alg][1],
                        "batch":e["number"],"start":e["start"],"count":e["count"],
                        "selectors_sha256":e["selector_sha256"],
                        "rows_sha256":hashlib.sha256(chunk.read_bytes()).hexdigest(),
                        "evaluator_sha256":"a"*64,"quality_exposed":False,
                        "status":"NATIVE_BATCH_VERIFIED__NO_SCIENTIFIC_PROMOTION"}
                    (folder / f"batch-{e['number']:03d}.verified.json").write_text(json.dumps(claim))
                out = tmp / "joined.jsonl"
                mod.join(folder, out)
                self.assertEqual(out.read_bytes(), old)
                b = folder / "batch-010.rows.jsonl"
                r = b.read_bytes()
                obj = json.loads(r.splitlines()[0])
                obj["selector_coordinate"] += 1
                b.write_bytes(json.dumps(obj).encode()+b"\n"+b"".join(r.splitlines(keepends=True)[1:]))
                with self.assertRaises(AssertionError):
                    mod.join(folder, tmp / "rejected.jsonl")
                self.assertFalse((tmp / "rejected.jsonl").exists())

    def test_complete_synthetic_transport_and_receipt_integrity(self):
        with tempfile.TemporaryDirectory() as directory:
            base = pathlib.Path(directory)
            cls = 17
            inp = base / "selectors.txt"
            inp.write_text("".join(f"{i*256+cls} {i+1}\n" for i in range(347)))
            folder = base / "class-17"
            mod.plan(inp, folder, 16, cls, "soft_tropical_base_2")
            m = json.loads((folder / "manifest.json").read_text())
            for e in m["entries"]:
                selectors = (folder / e["selector_file"]).read_text().splitlines()
                content = "".join(
                    json.dumps({
                        "selector_index": int(s.split()[0]),
                        "selector_coordinate": int(s.split()[1]),
                        "algebra_id": 1,
                        "status": "C90_COMPACT_NATIVE_SELECTOR_EVALUATED",
                        "quality_exposed": False,
                    }, sort_keys=True) + "\n"
                    for s in selectors
                ).encode()
                part = folder / f"batch-{e['number']:03d}.rows.jsonl"
                part.write_bytes(content)
                record = {
                    "record_type": "QTR_C90_FROZEN_NATIVE_BATCH_CUSTODY/1",
                    "source_head": mod.HEAD, "activation_head": mod.ACTIVATION,
                    "logical_class": cls, "algebra": "soft_tropical_base_2",
                    "native_graph_sha256": mod.GRAPHS["soft_tropical_base_2"][1],
                    "batch": e["number"], "start": e["start"], "count": e["count"],
                    "selectors_sha256": e["selector_sha256"],
                    "rows_sha256": hashlib.sha256(content).hexdigest(),
                    "evaluator_sha256": "a"*64, "quality_exposed": False,
                    "status": "NATIVE_BATCH_VERIFIED__NO_SCIENTIFIC_PROMOTION",
                }
                (folder / f"batch-{e['number']:03d}.verified.json").write_text(json.dumps(record))
            out = base / "complete.jsonl"
            mod.join(folder, out)
            self.assertEqual(len(out.read_bytes().splitlines()), 347)
            forged = folder / "batch-011.verified.json"
            record = json.loads(forged.read_text())
            record["count"] += 1
            forged.write_text(json.dumps(record))
            with self.assertRaises(AssertionError):
                mod.join(folder, base / "rejected.jsonl")
            self.assertFalse((base / "rejected.jsonl").exists())

    def test_all_classes_frozen_index_formula(self):
        for cls in (0, 1, 5, 127, 255):
            with self.subTest(cls=cls), tempfile.TemporaryDirectory() as tmp:
                path = pathlib.Path(tmp)
                inp = path / "input.txt"
                inp.write_text("".join(f"{i*256+cls} {i+1}\n" for i in range(347)))
                folder = path / f"class-{cls}"
                mod.plan(inp, folder, 16, cls, "soft_tropical_base_2")
                manifest = json.loads((folder / "manifest.json").read_text())
                self.assertEqual(len(manifest["entries"]),22)
                self.assertEqual(manifest["logical_class"],cls)
                if cls:
                    with self.assertRaises(AssertionError):
                        mod.plan(inp, path / "wrong", 16, cls - 1, "soft_tropical_base_2")


if __name__ == "__main__":
    unittest.main()
