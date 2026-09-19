# QTR-C90-EXACT-DECODER-001 — External Compute Handoff

Status: `EXTERNAL_COMPUTE_REQUIRED__GITHUB_ACTIONS_NOT_EXECUTION_SUBSTRATE`

## Purpose

This handoff preserves the authorized QTR-C90 exact-decoder campaign while moving bulk scientific execution off GitHub-hosted Actions.

GitHub is used only for:

- source and provenance;
- bounded CI and semantic-validation checks;
- compact receipt validation;
- durable issue / PR records;
- storage and retrieval of already-produced artifacts.

GitHub Actions is not used to generate the remaining C90 scientific outcome.

## Frozen scientific authority

- activation head: `0c1f5591a097adc285dec4cbfc320eeebd2c65d3`
- activation issue comment: `5737017921`
- semantic-validation run: `35084118529`
- semantic-validation artifact: `10443207511`
- semantic-validation artifact digest: `sha256:b91dd81d795822bd0f889a32b44f01b716d5b7ae097d83be5f43de95c9964bf8`
- semantic-validation payload: `3a46e8006a75bcd4eacdd421410da50809b71018b77a2dbbb930cfe44b4f80a0`
- orchestration adapter blob: `4b5ba1b5819a3ffdee294fb4cb2ab03734793a5d`
- native evaluator blob: `92022fa89ceff9cf4ac0c9b6ce8613617664e1a6`
- decoder blob: `7a275cd40b7ee8861ac1675791490b50d0266c50`
- scoring / matched-comparison blob: `f683e2af6671ef7f7908c09514d7fcab993755bc`
- C72 decision / tie-breaker blob: `164761a236ca53c919d810f0832cbcf3c1fb8989`
- exact DAG blob: `bb2576ea17beb43f1a188eb4a77a280869d0c954`

## Exact compiled inputs

### sum_product_bsc_p_0_1

- artifact: `10442610733`
- artifact digest: `sha256:678b39b09023f0adb854a9b0cc28ce0b85c9379e149b0103cfe94a7e4ad0fece`
- native binary SHA-256: `2efe52e17c6d66920b23738987818184657caf479c60c78712dff6db4a306bde`
- canonical stream: `e6d34ddfdadb19af9bda02c36997a8c2dd767f4610b178f4cf3d74407445ebb4`

### soft_tropical_base_2

- artifact: `10442242798`
- artifact digest: `sha256:c4fa41b35ad5e88e4e58ca9816c78dd296d170a5d86cf9087c51b4fdcce138e8`
- native binary SHA-256: `9647b3e7fb2ee7f6f87d7e3fe6ce6779bd756e100f86f3dc13e7dc5385b5df9a`
- canonical stream: `4d8859535f7a3ce814eb6ea459a80870fd645f57af487e5b8a9f99de3d5dccb0`

### min_plus_hamming

- artifact: `10442143252`
- artifact digest: `sha256:6b9c94bd62cd4b3818396bc2c48b66cfe63958d37ce8d5ab2b846d0fb701d38f`
- native binary SHA-256: `dd58a7e0c59626032d8714827d9f1097a33a78fd426c7d972407b32340890bb0`
- canonical stream: `3aa3f0c1d97f7428623a034b6baa20e9c7f113e830b715040dc9e1e62967b4e8`

## Authoritative evidence rule

The final C90 scientific outcome must be computed entirely on an external compute substrate.

The GitHub-hosted campaign runs are non-authoritative historical cross-check evidence only:

- min-plus run `35402858866`: completed before the substrate boundary was tightened;
- sum-product run `35402858883`: force-cancelled, terminal `completed/cancelled`;
- soft-tropical run `35402858934`: cancelled, terminal `completed/cancelled`.

No selector value, correction, score, success/failure bit, or matched-comparison cell produced by those GitHub-hosted runs may be used as an authoritative input to the final campaign receipt.

The external execution must recompute all three full algebra surfaces from the frozen validated binaries:

- 256 logical-class shards per algebra;
- exactly 347 frozen selector coordinates per shard;
- exactly 88,832 selector evaluations per algebra;
- exactly 266,496 selector evaluations across the three algebras.

The historical GitHub-hosted outputs may be compared against the external outputs after the external results are fixed. Any mismatch is a diagnostic requiring investigation. Agreement is corroboration only; it does not substitute for the external computation.

## External execution rule

Run the exact native evaluator outside GitHub Actions.

The GCL default is the established host-orchestrated disposable-compute pattern. A Colab CPU runtime or another explicitly provisioned GCL compute host is suitable because the current native evaluator is CPU-bound. GPU allocation is not required unless a separately qualified accelerator-native evaluator is introduced.

The external host must:

1. checkout the orchestration branch and verify all frozen blob identities above;
2. obtain the exact compiled input artifact for each algebra and verify artifact, receipt, canonical-stream, and native-binary identities;
3. execute all 256 logical-class shards for each algebra, with exactly 347 frozen selector coordinates in every shard;
4. preserve each JSONL selector-result stream plus its fail-closed shard receipt;
5. assemble all 88,832 selector results per algebra into the 347 fixed correction records using `reference/qtr_c90_exact_native_campaign_001.py aggregate`;
6. only after the fixed-correction receipt exists, run `score` against the protected conventional artifact;
7. retain raw external execution logs and resource measurements with the final result package;
8. return only compact receipts and evidence inventories to GitHub for bounded CI verification and governed review.

Host parallelism, worker count, checkpointing, and restart policy are engineering parameters only. They may be changed after operational interruption provided selector coordinates, exact evaluator semantics, compiled binaries, fixed decision rule, independent scoring rule, and comparison rule remain unchanged.

## GitHub Actions boundary

The bulk campaign workflows were removed from branch `execution/qtr-c90-exact-decoder-001-0c1f5591`.

Do not recreate a GitHub-hosted matrix for bulk selector evaluation.

Permitted GitHub Actions work for this campaign is limited to bounded software-lifecycle checks such as:

- unit tests;
- source / blob identity checks;
- semantic equivalence tests on the frozen validation set;
- compact artifact / receipt schema validation;
- digest and provenance verification;
- deterministic recomputation of small receipt predicates.

The scientific outcome is not complete until the external exact run produces the full fixed-correction surface and independent matched-comparison receipt.

## External runner

Runner:

`scripts/run_qtr_c90_exact_decoder_external.py`

The runner uses the host's authenticated `gh` session only to retrieve and verify the frozen compile artifacts and the protected conventional comparison artifact. It does not submit scientific work to GitHub Actions.

It verifies the frozen scientific blob identities before every scientific operation and refuses a source drift.

Inspect the host before launch:

```bash
python scripts/run_qtr_c90_exact_decoder_external.py plan
```

The memory guard assumes 7 GiB per active native evaluator plus an 8 GiB host reserve. The runner will refuse a requested worker count above the conservative RAM/CPU limit.

Run one complete algebra surface:

```bash
python scripts/run_qtr_c90_exact_decoder_external.py evaluate \
  --algebra min_plus_hamming \
  --workers 16 \
  --work-root /data/qtr-c90

python scripts/run_qtr_c90_exact_decoder_external.py evaluate \
  --algebra soft_tropical_base_2 \
  --workers 16 \
  --work-root /data/qtr-c90

python scripts/run_qtr_c90_exact_decoder_external.py evaluate \
  --algebra sum_product_bsc_p_0_1 \
  --workers 16 \
  --work-root /data/qtr-c90
```

The three algebra surfaces may be run on separate external hosts. Before final aggregation, collect their `external-shards/<algebra>/` trees under one common work root. Every accepted shard has an `external-shard.json` marker with `execution_substrate: external`; the runner will not treat a GitHub-hosted shard artifact as resumable authoritative evidence.

After all three external surfaces are complete:

```bash
python scripts/run_qtr_c90_exact_decoder_external.py aggregate-score \
  --work-root /data/qtr-c90
```

The aggregate step first fixes all 347 corrections with quality still closed. Only then does the separate score step load the protected conventional artifact and expose the authorized matched comparison.

Representative class-0 engineering timings from the retired hosted-runner attempt were:

- `min_plus_hamming`: 4,000 seconds;
- `soft_tropical_base_2`: 7,038 seconds;
- `sum_product_bsc_p_0_1`: 7,588 seconds.

These are planning diagnostics only. Assuming similar external CPU throughput, estimated per-algebra wall time is:

| Workers | Conservative RAM floor | min-plus | soft-tropical | sum-product |
|---:|---:|---:|---:|---:|
| 8 | 64 GiB | 35.56 h | 62.56 h | 67.45 h |
| 16 | 120 GiB | 17.78 h | 31.28 h | 33.72 h |
| 32 | 232 GiB | 8.89 h | 15.64 h | 16.86 h |

The timings are not scientific claims. They only size the external host.

