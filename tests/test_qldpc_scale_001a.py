import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("qldpc_scale_001a", ROOT / "reference" / "qldpc_scale_001a.py")
M = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(M)


class QLDPCScale001APayloadDiagnostic(unittest.TestCase):
    def test_emit_corrected_payload(self):
        registry = M.load_registry(ROOT / "registry" / "qldpc-scale-001a.json")
        predecessor_registry = json.loads((ROOT / "registry" / "tcm-qdec-004.json").read_text())
        predecessor_evidence = json.loads((ROOT / "evidence" / "TCM-QDEC-004-report.json").read_text())
        predecessor_promotion = json.loads((ROOT / M.PREDECESSOR["promotion_record_path"]).read_text())
        report = M.evaluate(registry, predecessor_registry, predecessor_evidence, predecessor_promotion, full_validation=False)
        print("QLDPC_SCALE_001A_CORRECT_SELECTOR_BASIS_SHA256", report["source_binding"]["selector_basis_sha256"])
        print("QLDPC_SCALE_001A_CORRECT_PAYLOAD_SHA256", report["payload_sha256"])
        self.fail("diagnostic payload emission only")


if __name__ == "__main__":
    unittest.main()
