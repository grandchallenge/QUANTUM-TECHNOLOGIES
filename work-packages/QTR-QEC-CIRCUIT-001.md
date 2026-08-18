# QTR-QEC-CIRCUIT-001 — bounded repeated-syndrome phenomenological temporal execution

## Status

`referee_promoted_bounded__documentary_overlay`

Referee-promoted bounded temporal authority is recorded only in `reviews/QTR-QEC-CIRCUIT-REVIEW-001/promotion-record.json`. The scientific registry and evidence remain immutable candidate snapshots with status `candidate_executable_not_promoted`.

This work package implements only the first temporal/repeated-syndrome subgate of `QEC-CIRCUIT-001`. It is not a gate-level syndrome-extraction, hardware, threshold, or fault-tolerant-circuit result.

## Authority

- Council contract: issue #76.
- Referee recommendation: #76 comment `5321884229` — `RECOMMEND_ADOPTION_WITH_AMENDMENTS__NO_EXECUTION_AUTHORITY`.
- Human Steward authorization: #76 comment `5321917311` — `ADOPT_WITH_AMENDMENTS__AUTHORIZE_QEC_CIRCUIT_001_ONLY`.
- Execution docket: issue #77.
- Protected starting `main`: `b1e6a45073842ac498b476f6c8c1d31b133e553a`.
- Scientific branch: `agent/qec-circuit-001`.
- Exact-head review: issue #79.
- Reviewed scientific head: `32bbb7117670a30fad70ee9969e2699239678a09`.
- Referee scientific disposition: #79 comment `5322294699` — `APPROVE_BOUNDED_SCIENTIFIC_MERGE__QEC_CIRCUIT_001`.
- Scientific merge: `da820411b45f2e23fe961ed9fb4597a3b3d3e774`.
- Documentary promotion referral: issue #80.
- Human Steward documentary authorization: #80 comment `5322340585` — `ADOPT_WITH_AMENDMENTS__AUTHORIZE_QEC_CIRCUIT_001_DOCUMENTARY_PROMOTION_ONLY`.
- Documentary promotion record: `reviews/QTR-QEC-CIRCUIT-REVIEW-001/promotion-record.json`.

No later `QEC-CIRCUIT` subgate and no `QLDPC-FORGE` authority is inherited. Later `QEC-CIRCUIT` subgates remain unauthorized, and `QLDPC-FORGE` remains unauthorized.

## Manifest package and execution quarantine

The base pre-decoder manifest was committed before the first attempted conventional temporal execution:

- first manifest commit `ce36f40cd33d665084bd3cf2f744a7cae94bc76c`;
- base manifest payload `15962fa93eb92632e760e62a54fbd03a8322fb09b8c3b41de2f0b4225fb52dfb`.

During workflow run `32085478805` at head `5f623a086dc9657e8abc32926bc42b374862cd51`, before any decoder result payload or outcome total was inspected, the TCM preflight specification was found incomplete: it omitted unary channel factors and the four protected terminal logical-class selector constraints from the declared exact TCM representation.

That entire workflow run is quarantined. No scientific result from it is admissible.

The pre-outcome repair is committed as:

- `registry/qec-circuit-001-manifest-amendment-001.json`;
- amendment payload `8be8637ef976c9096b22259f0f849e2350a997b80038f4815302fbefa5f2ad19`.

The amendment changes no conventional measurement parameter, detector map, corpus, channel probability, or terminal correctness oracle. Every conventional row was rerun from scratch under the amended two-part manifest.

## Frozen temporal fixture

Use the protected `[[18,4,4]]` C18 X-error sector with the protected seven-dimensional independent Z-check basis.

Three noisy syndrome rounds are followed by one perfect terminal syndrome readout. The fault object is

`x=(f1,f2,f3,m1,m2,m3) ∈ F_2^75`,

with 54 data-X and 21 measurement-bit coordinates. Terminal correction projection is fixed as

`P_data(x)=f1 XOR f2 XOR f3`.

Detector consistency is not the scientific correctness oracle. Terminal success requires protected syndrome consistency and stabilizer equivalence.

## Frozen finite corpus and detector substrate

The authoritative corpus is every elementary temporal fault history of weight 0, 1, or 2: `1 + 75 + 2775 = 2851` histories. Histories are never deduplicated merely because they share a detector record.

- detector map shape `28 × 75`;
- detector rank `28`;
- detector SHA-256 `960701757ef5c223d4ed96070508472e4f37feef92aec69d15b175bc078dbcb7`;
- ordered `(fault, detector, terminal error)` digest `137550c93359f8a9153cffa5e2ebdad926e2d07e27b203fe3aaf39a972d12eb7`.

The detector fibers retain genuine ambiguity:

- `2517` distinct detector vectors;
- fiber sizes: `2320` of size 1, `60` of size 2, `137` of size 3;
- `135` fibers span multiple terminal stabilizer-equivalence classes;
- those fibers contain `405` authoritative histories.

## Corrected exact temporal TCM definition

The amended `TEMP_TCM_EXACT` row is exact degeneracy-aware sum-product inference at elementary-fault probability `p=0.1`.

For each detector input it aggregates likelihood mass over all compatible 75-bit fault histories, grouped by four terminal logical-selector parities defined by the protected logical-Z basis. It retains all maximizing logical selectors; the deterministic default is the lowest integer four-bit selector. The returned correction is the frozen lowest-Hamming-weight-then-integer representative matching the terminal syndrome and winning logical selector.

The correction-representative table has `2048` entries and SHA-256:

`bb3b6e56891c6858684e6f61eace6d56bbbd4f26b026636197c2b8031cbafce7`.

The complete factor representation contains:

- 75 unary channel factors;
- 28 detector parity factors;
- 4 terminal logical-selector factors;
- 107 factors total.

Factor-scope arities are `{1:82, 7:7, 8:14, 12:2, 18:2}` with complete scope digest:

`cfa139dc874a162d6ad23c3ab9b48d3830b42c9ee2221676d73d0ebf8fa4f733`.

## Exact temporal TCM structural result

The frozen primary order remains deterministic min-fill with lowest-index tie breaking.

Corrected preflight:

- min-fill induced width `34`;
- peak joint arity `35`;
- predicted peak joint table `2^35 = 34,359,738,368` entries;
- frozen peak-table cap `2^20 = 1,048,576` entries.

Therefore exact temporal TCM stops before table materialization as:

`TEMPORAL_TCM_EXACT_BOUND_EXHAUSTED`.

This is only a result under the frozen deterministic envelope. It is not intrinsic-intractability, runtime, memory, or family-scaling evidence. TCM quality remains undefined.

## Conventional temporal rows

The exact COMPARE-001 package identities remain unchanged:

- `ldpc==0.1.53`, sdist SHA-256 `3b2652aa993ab71672d680ac76ee2dcf3dc289fc5d11c07d060e5f838d8c3601`;
- `bposd==1.6`, wheel SHA-256 `80e439246c11ca824610f9bc7858c68eb1f8a6b7cbb71760cf6c86e03c47ff5d`.

Rows are `TEMP_BP_MIN_SUM`, `TEMP_BP_OSD_CS_7`, and conditionally certified `TEMP_BP_SUM_PRODUCT`. Each decodes the frozen `28 × 75` detector matrix exactly once per authoritative history. No retries, tuning, package substitution, per-history parameter changes, or outcome-dependent fallback are allowed.

The frozen exact finite success totals are:

- `TEMP_BP_OSD_CS_7`: `2520/2851`;
- `TEMP_BP_MIN_SUM`: `2430/2851`;
- `TEMP_BP_SUM_PRODUCT`: `1736/2851`.

These conventional totals and their pairwise relations are promoted only on this exact finite corpus. Because exact temporal TCM stops at the frozen compilation bound, no TCM-vs-conventional quality ordering is defined.

The authoritative execution route is `reference/qec_circuit_001_exact.py`, which composes the base manifest and amendment. `reference/qec_circuit_001.py` is retained only as the frozen substrate/conventional engine.

## Machine route

`.github/workflows/qtr-qec-circuit-001.yml` requires exact-head checkout, amended static replay, fail-closed tests, exact package verification, fresh execution of all three conventional rows, deterministic report assembly, quarantine binding, and an exact-head receipt.

The reviewed scientific registry and compact evidence remain `candidate_executable_not_promoted` byte-for-byte. Referee-promoted bounded temporal authority resides only in `reviews/QTR-QEC-CIRCUIT-REVIEW-001/promotion-record.json`.

## Explicit exclusions

No authority or claim is created for physical gate schedules, ancilla/hook errors, CNOT/gate propagation, gate-location Pauli models, hardware noise, full-Pauli decoding, more than three noisy rounds, round-count or error-rate sweeps, thresholds, hardware validation, runtime/memory superiority, family/asymptotic claims, learned decoding, adaptive/autonomous search, later `QEC-CIRCUIT` subgates, or `QLDPC-FORGE`.

## Promotion boundary

The bounded documentary promotion memorializes only the already reviewed finite temporal substrate, the three frozen conventional outcome rows and pairwise relations, detector-fiber ambiguity, and the exact temporal TCM reach/status result under the frozen resource envelope.

A favorable conventional result is not itself a general success predicate. Exact temporal TCM is bound-exhausted under the frozen cap, so no TCM-versus-conventional quality ordering is defined in this docket. Promotion does not convert that reach boundary into intrinsic-intractability, runtime, memory, threshold, scaling, gate-level, hardware, or general decoder-family evidence.

Promotion authority is documentary only. The immutable scientific manifest, amendment, registry, evidence, reference implementations, and exact replay workflow remain unchanged from scientific merge `da820411b45f2e23fe961ed9fb4597a3b3d3e774`.
