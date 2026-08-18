# QTR-QEC-CIRCUIT-001 — bounded repeated-syndrome phenomenological temporal execution

## Status

`authorized_candidate_execution`

This work package implements only the first temporal/repeated-syndrome subgate of `QEC-CIRCUIT-001`.

It is not a gate-level syndrome-extraction, hardware, threshold, or fault-tolerant-circuit result.

## Authority

- Council contract: issue #76.
- Referee recommendation: #76 comment `5321884229` — `RECOMMEND_ADOPTION_WITH_AMENDMENTS__NO_EXECUTION_AUTHORITY`.
- Human Steward authorization: #76 comment `5321917311` — `ADOPT_WITH_AMENDMENTS__AUTHORIZE_QEC_CIRCUIT_001_ONLY`.
- Execution docket: issue #77.
- Protected starting `main`: `b1e6a45073842ac498b476f6c8c1d31b133e553a`.
- Scientific branch: `agent/qec-circuit-001`.

No later `QEC-CIRCUIT` subgate and no `QLDPC-FORGE` authority is inherited.

## Manifest-first lock

The canonical pre-decoder manifest was committed before any conventional temporal decoder execution:

- first manifest commit: `ce36f40cd33d665084bd3cf2f744a7cae94bc76c`;
- path: `registry/qec-circuit-001-manifest.json`;
- manifest payload SHA-256: `15962fa93eb92632e760e62a54fbd03a8322fb09b8c3b41de2f0b4225fb52dfb`.

The manifest fixes the temporal equations, coordinate ordering, protected C18 check basis, detector matrix identity, complete finite corpus, channel model, decoder package/configuration locks, TCM resource envelope, adjudication vocabulary, and downstream exclusions.

## Frozen temporal fixture

Use the protected `[[18,4,4]]` C18 X-error sector with the protected seven-dimensional independent Z-check basis.

Three noisy syndrome rounds are followed by one perfect terminal syndrome readout. The fault object is

`x=(f1,f2,f3,m1,m2,m3) ∈ F_2^75`,

with 54 data-X and 21 measurement-bit coordinates.

The detector history is the ordered 28-bit vector formed from four seven-bit syndrome differences. Terminal correction projection is fixed as

`P_data(x)=f1 XOR f2 XOR f3`.

Detector consistency is not the scientific correctness oracle. Terminal success requires the protected syndrome-consistency and stabilizer-equivalence predicate.

## Frozen finite corpus

The authoritative corpus is every elementary temporal fault history of weight 0, 1, or 2:

- weight 0: `1`;
- weight 1: `75`;
- weight 2: `2775`;
- total: `2851`.

Distinct fault histories are never deduplicated merely because they share a detector record.

Pre-decoder ordered record digest:

`137550c93359f8a9153cffa5e2ebdad926e2d07e27b203fe3aaf39a972d12eb7`.

## Certified pre-decoder substrate

The detector matrix is reconstructed both from the temporal equations and by independent unit-fault injection. The two constructions must agree exactly, and matrix evaluation must agree with direct recurrence on all 2851 authoritative histories.

Frozen detector identity:

- shape `28 × 75`;
- rank `28`;
- SHA-256 `960701757ef5c223d4ed96070508472e4f37feef92aec69d15b175bc078dbcb7`.

The pre-decoder detector fibers contain genuine ambiguity and retain it as evidence:

- `2517` distinct detector vectors;
- fiber sizes: `2320` of size 1, `60` of size 2, `137` of size 3;
- `135` detector fibers contain multiple terminal stabilizer-equivalence classes;
- those ambiguous fibers contain `405` authoritative histories.

No tie or decoder rule may be chosen after observing outcomes to erase this ambiguity.

## Exact temporal TCM preflight

The temporal detector constraints define the exact factor scopes before any TCM table materialization.

The frozen primary order is deterministic min-fill with lowest-index tie breaking.

Preflight result:

- deterministic min-fill induced width: `20`;
- peak joint arity: `21`;
- predicted peak joint table: `2^21 = 2,097,152` entries;
- frozen peak-table cap: `2^20 = 1,048,576` entries.

Therefore the exact temporal TCM path must stop before table materialization with:

`TEMPORAL_TCM_EXACT_BOUND_EXHAUSTED`.

This is a result under one frozen deterministic envelope. It is not a claim of intrinsic intractability, runtime or memory inferiority, or family scaling.

## Conventional temporal rows

The exact package identities from `TCM-QDEC-COMPARE-001` are reused unchanged:

- `ldpc==0.1.53`, sdist SHA-256 `3b2652aa993ab71672d680ac76ee2dcf3dc289fc5d11c07d060e5f838d8c3601`;
- `bposd==1.6`, wheel SHA-256 `80e439246c11ca824610f9bc7858c68eb1f8a6b7cbb71760cf6c86e03c47ff5d`.

Frozen rows:

- `TEMP_BP_MIN_SUM`;
- `TEMP_BP_OSD_CS_7`;
- `TEMP_BP_SUM_PRODUCT`, conditional on exact interface certification.

Each row decodes the frozen `28 × 75` temporal detector matrix, receives one call per authoritative history, and returns a 75-bit inferred temporal fault history whose terminal correction is fixed by `P_data`.

No retry, tuning, package substitution, per-history parameter change, or result-dependent fallback is allowed.

## Machine route

The dedicated workflow `.github/workflows/qtr-qec-circuit-001.yml` performs:

1. exact-head checkout assertion;
2. static temporal substrate replay and fail-closed tests;
3. exact PyPI artifact download and hash verification;
4. one isolated conventional row per matrix job;
5. deterministic aggregate report construction;
6. exact-head receipt generation;
7. artifact preservation.

Scientific evidence remains candidate-only until exact-head review and Referee adjudication.

## Explicit exclusions

This work package does not establish or authorize:

- a physical syndrome-extraction gate schedule;
- ancilla preparation or hook-error analysis;
- CNOT/gate propagation or gate-location Pauli faults;
- depolarizing, biased, leakage, erasure, or correlated hardware noise;
- Y/Z-sector or full-Pauli decoding;
- more than three noisy rounds;
- round-count scaling;
- error-rate sweeps;
- thresholds or pseudo-thresholds;
- hardware validation;
- runtime or memory superiority;
- family or asymptotic claims;
- learned decoding;
- adaptive or autonomous search;
- any later `QEC-CIRCUIT` subgate;
- `QLDPC-FORGE`.

## Promotion boundary

A favorable conventional result is not itself a success predicate. Because the exact temporal TCM path is already bound-exhausted under the frozen cap, no TCM-versus-conventional quality ordering is defined in this docket unless a separately authorized exact TCM interface later exists.

Any scientific merge must remain candidate-only until role-separated exact-head review, Referee disposition, expected-head merge, and a separate documentary promotion overlay if promotion is justified.
