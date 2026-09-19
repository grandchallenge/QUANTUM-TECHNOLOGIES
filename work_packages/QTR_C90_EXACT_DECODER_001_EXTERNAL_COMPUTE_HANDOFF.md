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
