# QTR-C90-EXACT-DECODER-001 — Protected-Conventional Data Recovery

Status: `RECOVERED_CONTENT_DIGEST_EQUIVALENT__ORCHESTRATION_REVIEW_PENDING__NO_SCIENTIFIC_QUALITY_EXPOSED`

Date: 2026-11-19

Protected original external-runner head: `675865123437c3d6c908c7a3af337fd4023c5d0b`. Frozen execution-activation head: `0c1f5591a097adc285dec4cbfc320eeebd2c65d3`. Protected conventional science: `evidence/TCM-QDEC-COMPARE-001-report.json` on main and the frozen `reference/qtr_c90_exact_execute_001.py` digest constants.

## Incident and recovery

The original Actions artifact `9304727792`, August workflow run `32079738866`, SHA-256 `34f37ec1a351a42e08c7143b359ca40191db4cd92ceeab2881930a67e3942182`, has been deleted or is no longer retrievable. The original full ZIP bytes and exact-head receipt were **not** recovered. Do not restamp an October receipt with the original August head.

Two later *actual GitHub replay* artifacts were independently downloaded and validated:

- Primary alternate `12738710046`; October workflow `40511661627`; head `c588cbbc635fe477c8496fd69e6145f62b768b2e`; ZIP SHA-256 `dd59ab416d41b1e9025d82319e28bd0ab622e0cdc6e10b097ca470a879dd3a46`.
- Corroborating alternate `12620093340`; workflow `40249646493`; head `3ca53e2aa39c14b498edb1d62bcbb45d7e09b490`; ZIP SHA-256 `c4491149fa086403d0f0738f6169dd7358d5782ddb8bd7c73b7a2689210108b1`.

These artifacts have different ZIP/execution-receipt hashes. They contain the original protected **full report payload**, canonical hash `6385c2da742e14ecf2bc41336c78c2a8ff42b1cdd897fb5e7cfac056e2214146`, the frozen 347-input C90 corpus (hash `b053a27a9c346832d6008987e204c88162dc1797e0367b38705861049059e086`), and all three identical C90 per-input 347-boolean success/failure arrays. Independently recomputed cell canonical digests, historical detailed-record digests embedded in cells, and outcome-vector SHA-256 commitments all match the protected source.

| Frozen conventional method | Success | Exact outcome-vector SHA-256 |
|---|---:|---|
| BP_MIN_SUM | 200/347 | `9652133baf36b83605c2f394067bd25938b47eb9595435b72470256ca1fe5bae` |
| BP_OSD_CS_7 | 211/347 | `bd2141809336ae41db0a5e471be74603e780f6b7beba72a541bdc00132ab50ea` |
| BP_SUM_PRODUCT | 171/347 | `d943dcfbf110e8c1e57558bddec270da374d6ea0abc9be9923d848e30eac3f48` |

No conventional decoder is rerun and no missing per-input outcomes are guessed or inferred from totals.

## Narrow engineering remedy

The original scoring route is the **default and unchanged**. After the independently computed TCM corrections have been **fixed with quality blind**, the external orchestrator optionally supports:

```bash
python scripts/run_qtr_c90_exact_decoder_external.py aggregate-score \
  --work-root /data/qtr-c90 --conventional-source verified-replay
```

That explicit opt-in verifies the newer archive's **actual** GitHub artifact identity, run, head and ZIP digest. It then verifies the report, C90 corpus, every conventional cell payload, every per-input outcome-vector digest, and protected totals. It leaves the frozen scientific methods in `reference/` unchanged. It reuses `qtr_c90_exact_execute_001.score_and_compare` for the independent correction score and nine contingencies. The final report records the **actual October replay source**, original historical digest identity, and the explicit `protected_original_archive_not_byte_verified` limitation.

The original reference loader continues to reject the October exact-head receipt, correctly; the new documented path neither bypasses nor falsifies it.

## Local verification and release boundaries

Static Python compile and the `verify-local` mode were replayed against the actual downloaded primary ZIP, with all three expected methods passing. Unit tests include invalid ZIP rejection, refusal to expose quality before corrections are fixed, and optional actual-ZIP integration.

This source repair **does not** claim full authoritative C90 execution, C90 quality, a new conventional baseline, original ZIP recovery, native code correctness, protected admission, or release. It requires exact-head CI and role-separated review before protected adoption; any later scientific outcome requires 266,496 externally recomputed selector evaluations and all nine matched comparisons.

Three large original native compile artifacts remain subject to separate byte-for-byte archival preservation before their 2026-12-15 expiry. An off-host durable backup is still required.
