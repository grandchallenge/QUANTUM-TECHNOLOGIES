# GCL Quantum Technologies Research

Status: `adopted`

Authority repository: `grandchallenge/QUANTUM-TECHNOLOGIES`

Programme identifier: `QTR`

## Purpose

GCL Quantum Technologies Research develops auditable quantum algorithms, operator encodings, resource estimates, simulations, error-correction substrates, and experimental protocols. The programme separates mathematical validity, algorithmic correctness, resource claims, simulation evidence, and hardware evidence.

The first research lane studies the governed chain

\[
\text{Boolean predicate}
\rightarrow
\text{coherently accessible signal}
\rightarrow
\text{polynomial separator}
\rightarrow
\text{QSP synthesis}
\rightarrow
\text{QSVT execution}.
\]

A smaller signal is useful only when semantic sufficiency, access cost, spectral separation, polynomial degree, and end-to-end resources are all controlled.

A second research lane establishes certified qLDPC/QEC substrates before any broader architecture search. Its governed sequence is now

`QLDPC-FIXTURE-001 → QLDPC-FIXTURE-002 → TCM-QDEC-001 → TCM-QDEC-002 → TCM-QDEC-003 → TCM-QDEC-004 → QLDPC-SCALE-001A → QLDPC-SCALE-001B → TCM-QDEC-COMPARE-001 → QEC-CIRCUIT-001 → QEC-CIRCUIT-002 → QLDPC-FORGE`.

The first two qLDPC fixtures, the first four bounded TCM-QDEC experiments, the bounded single-instance `QLDPC-SCALE-001A` feasibility result, the bounded finite-ladder `QLDPC-SCALE-001B` structural/cap-exhaustion result, the bounded `TCM-QDEC-COMPARE-001` finite shared-interface comparison, the bounded `QEC-CIRCUIT-001` three-round phenomenological temporal result, the bounded `QEC-CIRCUIT-002` predeclared exact representation-family exhaustion result, and the bounded `QTR-C90-EXACT-REQUAL-001` deterministic pre-calibration resource-ledger result are Referee-promoted. `QEC-CIRCUIT-003`, `QLDPC-FORGE`, and every later node remain separately gated.

## Authority state

- `QTR-CHARTER-00`: adopted.
- `QTR-SIG-WP00`: Referee-promoted finite-domain substrate.
- `QTR-SIG-WP01`: Referee-promoted finite symmetry-quotient atlas.
- `QTR-SIG-WP02`: Referee-promoted finite linearization atlas.
- `QTR-SIG-WP03`: Referee-promoted only for the admitted finite OR certificate pair.
- `QTR-SIG-WP04` and later: gated.
- `QTR-QLDPC-FIXTURE-001`: Referee-promoted only for the exact finite `[[18,4,4]]` replay and its finite code-capacity reference baseline.
- `QTR-QLDPC-FIXTURE-002`: Referee-promoted only for the frozen one-sector weight-`0..4` corpus, two named deterministic baselines, exact correctness scoring, deterministic counters, and retained negative evidence.
- `QTR-TCM-QDEC-001`: Referee-promoted only for the exact finite representative-versus-stabilizer-coset semiring audit on the protected Fixture 002 substrate.
- `QTR-TCM-QDEC-002`: Referee-promoted only for exact finite equivalence between the frozen quotient semantics and a fixed-order local parity transfer factorization on the protected `[[18,4,4]]` fixture.
- `QTR-TCM-QDEC-003`: Referee-promoted only for the exact seven-variable stabilizer-degeneracy factorization, the exact minimum induced width `4` over all `5040` elimination orders of that frozen finite factor graph, complete predecessor score/mapping/tie/decision equivalence, and the retained unfavorable deterministic operation-count comparison.
- `QTR-TCM-QDEC-004`: Referee-promoted only for exact shared selector-parametric compilation on the same protected finite fixture, complete predecessor semantic equivalence, and the exact reduction in duplicated abstract work under the declared AOP ledger. This is not a runtime, memory, asymptotic, or scaling result.
- `QTR-QLDPC-SCALE-001A`: Referee-promoted only for the source-bound `[[72,12,6]]` single-instance feasibility result: exact reconstruction of `n=72,k=12`, exact deterministic min-fill width `18` for the named order, exact compilation inside every frozen resource cap, and exact compiled-versus-independent-oracle equality on the frozen `300`-selector validation set. Distance `6` remains source-reported; the width is not a certified global treewidth; the validation is not exhaustive over `2^42` selectors.
- `QTR-QLDPC-SCALE-001B`: Referee-promoted only for the fixed finite ladder `{72,90,108,144,288,784}`: exact source reconstruction and named-order structural audit on all five post-anchor rungs, exact Level-S structural-budget compliance, and deterministic Level-C primary peak-table exhaustion beginning at `n=90`. No post-anchor compiled object or selector semantic validation was reached. The result does not certify global treewidth, an asymptotic/family scaling law, intrinsic intractability, runtime/memory behavior, or conventional-decoder comparison.
- `QTR-TCM-QDEC-COMPARE-001`: Referee-promoted only for the frozen C18 matched shared-interface comparison, its finite exact totals and pairwise outcome relations, and the explicit C72/C90 reach/status and undefined-TCM-quality boundaries. The deterministic/default min-plus result retains its certified tie envelope `[218,263]`. No cross-surface winner, decoder-family ordering, runtime/memory, family-scaling, threshold, circuit, hardware, learned-decoder, or autonomous-search claim follows.
- `QTR-QEC-CIRCUIT-001`: Referee-promoted only for the frozen three-round phenomenological repeated-syndrome C18 X-error temporal substrate, the exact 2851-history weight-`0..2` corpus, retained detector-fiber ambiguity, the three frozen conventional outcome rows and pairwise relations, and the exact temporal TCM reach/status `TEMPORAL_TCM_EXACT_BOUND_EXHAUSTED` under the frozen resource envelope. TCM quality remains undefined; no TCM-vs-conventional quality ordering, gate-level, hardware, threshold, runtime/memory, family-scaling, learned-decoder, autonomous-search, or later-circuit claim follows.
- `QTR-QEC-CIRCUIT-002`: Referee-promoted only for exact semantic equivalence of the three predeclared auxiliary-state rewrites and exhaustion of the finite `R0/R1/R2/R3` representation family under the unchanged deterministic min-fill policy and `2^20` peak-table cap. Primary widths are `34/36/36/36`; no successor representation compiles. TCM quality remains undefined. This is not global-treewidth, intrinsic-intractability, runtime/memory, scaling, physics-model, downstream-circuit, or Forge authority.
- `QTR-C90-EXACT-REQUAL-001`: Referee-promoted only for the finite C90 deterministic pre-calibration resource-ledger result under the single C90 peak-joint amendment from `2^20` to `100 * 2^20`. The `2^26 = 67,108,864` peak-joint gate passes, but exact factor-table evaluations `201,384,562 > 2^27` and the mandatory compilation-AOP lower bound `3,410,023,338 > 2^31` fail. The first exact crossing is elimination step `15`, variable `0`, with `2^26` joint assignments. Host-memory calibration was not performed; the physical-memory question was not reached; Phase X and frozen-307 validation were not reached. This is not a physical-memory, runtime, hardware, global-complexity, scaling, accelerator, circuit, or Forge result.
- `QLDPC-FORGE`: gated.

The signal-lane downstream promotion was reviewed at `c6d3c460804bcc414226cac3700a864773ba2fdf` and merged as `f96452e3eeb1688bf8eb60c7b22e3adf500bae39`. Its exact candidate registry and evidence snapshot remain immutable; authority is recorded in `reviews/QTR-SIG-NEXT-001/promotion-record.json`.

The first qLDPC fixture was reviewed at `a024afb5b3428f49c34d905625f8c56f466528e7` and merged as `b899894cfe17680d556d32ff36e51683cd9f6b32`. Its exact registry and evidence snapshot likewise remain immutable; bounded authority is recorded in `reviews/QTR-QLDPC-REVIEW-001/promotion-record.json`.

The second qLDPC fixture was reviewed at `e7b2eb0060e51d4157a6666f2e857c1fb19aaff1` and scientifically merged as `51c31bde2e0630314d3d48dceb9b92969c37c228`. Its exact benchmark registry and evidence snapshot remain immutable; bounded authority is recorded in `reviews/QTR-QLDPC-REVIEW-002/promotion-record.json`.

`TCM-QDEC-001` was reviewed at `cba814e5e5fb6db8fba7a8afd8211189a477eecb` and scientifically merged as `41524f805dce4f0c7b64b8e743b75a60b4f76773`. Its exact experiment registry and evidence snapshot remain immutable; bounded authority is recorded in `reviews/QTR-TCM-QDEC-REVIEW-001/promotion-record.json`.

`TCM-QDEC-002` was reviewed at `9123a9c6cc2c163031d8bff0c46e0a9dd4c8f8fd` and scientifically merged as `d3340c91df3aa72dc5c7ba75906128c8eef2e174`. Its exact factorization registry and evidence snapshot remain immutable; bounded authority is recorded in `reviews/QTR-TCM-QDEC-REVIEW-002/promotion-record.json`.

`TCM-QDEC-003` was reviewed at `968029c156a3d668a0adc9adce850b62cd249671` and scientifically merged as `2925a41343c8e4592c1bf558d86ea461e0e1c7d4`. Its exact degeneracy-factor registry and evidence snapshot remain immutable; bounded authority is recorded in `reviews/QTR-TCM-QDEC-REVIEW-003/promotion-record.json`.

`TCM-QDEC-004` was reviewed at `8177a57b63e3f2c953a028691d305563f298b572` and scientifically merged as `7eff1025e97ff962a6fed81e6f2fa0f4d14653a3`. Its exact selector-parametric registry and evidence snapshot remain immutable; bounded authority is recorded in `reviews/QTR-TCM-QDEC-REVIEW-004/promotion-record.json`.

`QLDPC-SCALE-001A` was reviewed at `1bf76b536d9cd59d8a4b6b3518764df8e526986e` and scientifically merged as `e30e64adcbd67ab015b04415135bb167b3132a02`. Its exact larger-instance registry and evidence snapshot remain immutable; bounded single-instance promotion authority is recorded in `reviews/QTR-QLDPC-SCALE-REVIEW-001A/promotion-record.json`.

`QLDPC-SCALE-001B` was reviewed at `e4ba3cddc2440c868584ee675362f7d883855c73` and scientifically merged as `c6a7c7b3f7b49d52e22f5a79866c479aad326aa0`. Its exact ladder manifest, registry, and evidence snapshot remain immutable; bounded finite-ladder structural/cap-exhaustion promotion authority is recorded in `reviews/QTR-QLDPC-SCALE-REVIEW-001B/promotion-record.json`.

`TCM-QDEC-COMPARE-001` was reviewed at `3ebe409c60e7907b8251d44ee822141159d2879c` and scientifically merged as `18f04d4af18582bbd00ae2769927408dce9b04ee`. Its exact manifest, registry, and evidence snapshot remain immutable; bounded finite comparison authority is recorded in `reviews/QTR-TCM-QDEC-COMPARE-REVIEW-001/promotion-record.json`. C72 and C90 TCM quality comparisons remain undefined.

`QEC-CIRCUIT-001` was reviewed at `32bbb7117670a30fad70ee9969e2699239678a09` and scientifically merged as `da820411b45f2e23fe961ed9fb4597a3b3d3e774`. Its exact manifest, pre-outcome amendment, registry, and evidence snapshot remain immutable; bounded three-round phenomenological temporal authority is recorded in `reviews/QTR-QEC-CIRCUIT-REVIEW-001/promotion-record.json`. The quarantined workflow run `32085478805` contributes no admitted result. TCM quality remains undefined, and `QLDPC-FORGE` remains separately gated.

`QEC-CIRCUIT-002` was reviewed at `695ea1da951cd2b4f9d5a6a07c30b090cfd37709` and scientifically merged as `e85d67619a0d739fe039cca8f271f9a32ae2f3db`. Its exact pre-outcome manifest, registry, compact evidence, evaluator, evidence projector, and exact-replay workflow remain immutable; bounded representation-family promotion authority is recorded only in `reviews/QTR-QEC-CIRCUIT-REVIEW-002/promotion-record.json`. The earlier QTR timeout attempts remain diagnostic/non-authoritative provenance. TCM quality remains undefined, and no TCM-vs-conventional quality ordering is defined. `QEC-CIRCUIT-003` and `QLDPC-FORGE` remain separately gated.

`QTR-C90-EXACT-REQUAL-001` was reviewed at `d3215db1b22a95ba90c8e8901cc78dec83716e82` and scientifically merged as `42e644571172f895025a819d9e91cd8fcd78cbb8`. Its exact manifest, scientific registry, evidence, evaluator, and exact-replay workflow remain immutable; bounded documentary promotion authority is recorded only in `reviews/QTR-C90-EXACT-REQUAL-REVIEW-001/promotion-record.json`. The protected scientific status remains `candidate_executable_not_promoted`. The durable interpretation is that ×100 clears the historical peak-joint gate but remains insufficient under the unchanged cumulative exact-compilation ledger; the physical-memory question was not reached. `QEC-CIRCUIT-003` and `QLDPC-FORGE` remain separately gated.

The adoption and promotion records do not certify a general theorem, prove quantum advantage, validate hardware evidence, establish practical resource superiority, certify a qLDPC threshold, establish bounded tensor width for a code family, or authorize later qLDPC decoder/search stages.

## Promoted executable signal package

WP01 exhaustively groups Boolean strings by permutation orbits and checks whether the predicate is constant on each orbit. WP02 exposes signed/scalar, singular-value, rank, range, and kernel semantics. Bounded WP03 verifies one explicit four-bit OR adversary matrix and one matching span program.

The package deliberately retains negative evidence. In particular, the signed Hamming scalar separates five-bit majority, while its singular value erases the sign and creates 126 opposite-label input-pair collisions.

## qLDPC/QEC fixture lane

`QLDPC-FIXTURE-001` reconstructs the protected bivariate-bicycle CSS instance from its polynomial parameters and independently verifies `H_X H_Z^T = 0`, ranks `7/7`, `[[n,k,d]]=[[18,4,4]]`, `d_X=d_Z=4`, full-check row weight `6`, data-column weight `3`, and the exact source-transcribed four-pair logical basis. Distance is decided by exhaustive finite enumeration.

Fixture 001 also records an exhaustive minimum-weight coset-leader decoder for one code-capacity CSS sector as a deterministic finite baseline. It is deliberately noncompetitive: no claim is made about BP-OSD superiority, latency, circuit-level noise, thresholds, hardware validity, or real-time fault-tolerant control.

`QLDPC-FIXTURE-002` freezes all one-sector 18-bit errors of weights `0..4` (`4048` cases) and scores two deterministic baselines against Fixture 001's exact stabilizer semantics. The exact lookup reproduces the Fixture 001 finite decoder results; a deliberately simple greedy syndrome-descent baseline retains its failures and explicit witnesses. Deterministic operation counts and canonical serialization sizes are promoted as replayable fixture evidence, while wall-clock profiling remains machine-local and non-authoritative.

The companion experimental BP-OSD configuration is recorded only as tag/blob-bound provenance context. Fixture 002 does not execute experimental-data reproduction, Pauli+ simulation, or BP-OSD benchmarking, and it creates no threshold, hardware, or practical decoder-performance claim.

`TCM-QDEC-001` keeps the protected Fixture 002 code and `4048`-case scoring corpus fixed while exhaustively enumerating all `2^18` one-sector physical error representatives. For each syndrome it compares coordinatewise representative-space inference with aggregation over the `16` certified stabilizer-equivalence logical classes under three exact integer reductions: a BSC `p=0.1` sum-product numerator, a fixed base-2 soft-tropical partition score, and min-plus Hamming weight.

On the frozen corpus, representative-naive success counts are `37`, `1`, and `37`, while stabilizer-coset aggregation gives `263`, `262`, and default `226`. The result is a finite mechanism statement, not a practical-decoder leaderboard. In particular, sum-product's net `+23` relative to Fixture 002's exact minimum-weight lookup decomposes into `131` repaired exact-lookup failures and `108` broken exact-lookup successes. The min-plus aggregate is materially tie-sensitive, with success-count envelope `[218,263]`; that ambiguity is retained as promoted evidence.

`TCM-QDEC-002` changes only the representation of the already-promoted quotient inference. It combines the nine syndrome parities with four source-locked logical-Z commutation parities into a local 13-bit selector system of rank `11`, then contracts one binary factor per qubit in the fixed order `0..17`. The primary factorized path reaches exactly `2048 = 128 × 16` syndrome/logical-class states and does not enumerate all `2^18` physical errors; the TCM-QDEC-001 enumerator is used afterward only as the verification oracle.

For all `384` syndrome-by-algebra cells, the factorized tied winning class sets and deterministic corrections exactly equal the exhaustive predecessor oracle. The frozen-corpus totals and tie envelopes therefore remain `263/[263,263]`, `262/[262,262]`, and `226/[218,263]`. The observed peak support of `2048` and `32766` transition relaxations per algebra are promoted only as deterministic diagnostics of this finite instance and fixed contraction order. They do not establish favorable asymptotics, practical speed, or bounded contraction width for a qLDPC family.

`TCM-QDEC-003` fixes each already-certified syndrome/logical class and reparameterizes only its 128-element stabilizer degeneracy through seven independent stabilizer-generator bits. The 18 physical qubits become local factors of arity at most three. Exhaustive audit of all `7! = 5040` elimination orders gives exact minimum induced width `4`; `720` orders attain that width, and the frozen lexicographically first optimum is `[2,4,0,1,3,5,6]`, with peak joint table `32`.

The seven-variable contractions reproduce exactly all `6144` TCM-QDEC-002 score entries, all `2048` class mapping/minimum-representative entries, all `384` winning-class tie sets, and all `384` deterministic decisions. The frozen corpus totals and min-plus ambiguity remain unchanged. The smaller local elimination boundary is deliberately not converted into a systems claim: the present class-by-class construction records `774144` assignment evaluations versus TCM-QDEC-002's `98298` transition relaxations under non-equivalent primitive counters. No arithmetic, runtime, memory, asymptotic, or practical superiority follows.

`TCM-QDEC-004` keeps all TCM-QDEC-003 semantics fixed and compiles the same seven-variable contraction while retaining the eleven reachable selector coordinates as explicit parameters. Exact symbolic elimination produces canonical hash-consed expression DAGs with `371`, `371`, and `388` reachable nodes for the three promoted algebras. Compilation materializes zero selector answers; the compiled objects are reusable structural representations rather than complete 2048-answer caches.

The compiled path reproduces exactly all `6144` scores, `2048` mapping/minimum-representative entries, `384` tied-winning-class sets, and `384` deterministic decisions, including the success totals `263`, `262`, `226` and min-plus envelope `[218,263]`. Under the predeclared common AOP event ledger, compilation plus one complete 2048-selector sweep records `12,704,688` events versus `14,115,840` for an independently re-instrumented classwise TCM-QDEC-003 replay, a difference of `1,411,152`. The AOP total is an abstract deterministic event count, not a runtime model; this finite result does not establish speed, memory, asymptotic, or scaling superiority.

`QLDPC-SCALE-001A` applies the exact selector-parametric construction to the source-selected `[[72,12,6]]` BB instance. Exact reconstruction gives 30 independent stabilizer generators, selector rank 42, and local factor arity at most three. The predeclared deterministic min-fill order has induced width `18` and peak joint table `2^19`; this is an exact property of that named order on this finite factor graph, not a globally optimal treewidth certificate.

The selector-independent compiled descriptor materializes zero selector answers and fits every frozen deterministic compilation cap. On the frozen validation set—zero, all 42 units, all-ones, and 256 precommitted pseudorandom selectors—the compiled evaluator and an independently constructed fixed-selector elimination oracle agree exactly for all `300/300` selectors across sum-product, soft-tropical, and the full min-plus representative/key payload. This is sampled exact equality only, not exhaustive equivalence over the `2^42` selector space. Source-reported distance `d=6` is not independently recertified. The 18-qubit and 72-qubit measurements remain finite instance descriptors only; no family scaling law, bounded-treewidth theorem, runtime/memory claim, or `QLDPC-SCALE-001B` authority follows.

`QLDPC-SCALE-001B` freezes the finite source-bound ladder `{72,90,108,144,288,784}` before 001B measurement and applies the same source/basis semantics and three named deterministic order rules at each rung. All five post-anchor source reconstructions and Level-S structural audits pass. Exact induced widths for the frozen min-fill order are `[18,25,30,34,79,201]` across the six named instances; lexicographic widths are `[24,28,33,31,71,253]`, retaining the exact finite non-monotonic witness `33 -> 31` from `108 -> 144`. These are named-order finite-instance facts, not global treewidth or an asymptotic scaling law.

The unchanged Level-C primary peak-table cap is `2^20`. The first post-anchor rung, `n=90`, has min-fill width `25`, hence predicted peak joint table `2^26`, and compilation stops before materialization. Every later post-anchor rung also exceeds that same frozen primary cap. No post-anchor 001B compiled object or selector semantic validation is therefore reached. The promoted result is the exact structural/cap-exhaustion boundary itself; it does not imply intrinsic intractability, runtime or memory behavior, practical decoder performance, or conventional-baseline superiority or inferiority. The Council maturity criterion for considering a future `TCM-QDEC-COMPARE-001` referral is met.

`QTR-C90-EXACT-REQUAL-001` reopens only the finite C90 resource envelope after the hosted-compute preparation, without changing the protected C90 representation or min-fill order. Its single deterministic-cap amendment raises only the peak-joint allowance from `2^20` to `100 * 2^20 = 104,857,600`; the existing C90 `2^26` peak therefore passes. Exact non-materializing ledger replay nevertheless gives `201,384,562` factor-table entry evaluations against the unchanged `2^27` cap and a mandatory compilation-AOP lower bound of `3,410,023,338` against the unchanged `2^31` cap. Both cross first at elimination step `15`, variable `0`, on the `2^26` joint step.

The promoted outcome is therefore a deterministic pre-calibration cap failure under the unchanged compilation ledger. Host-memory calibration was not performed, the physical-memory question was not reached, Phase X was mechanically unreachable, and frozen-307 semantic validation was not reached. This finite result says that the ×100 peak-entry amendment alone is insufficient under the complete inherited exact-compilation ledger; it does not establish physical-memory insufficiency, intrinsic intractability, performance ordering, family scaling, or accelerator behavior.

`TCM-QDEC-COMPARE-001` freezes one shared X-error code-capacity interface, exact stabilizer-equivalence correctness oracle, precommitted C18/C72/C90 corpora, and source/configuration-pinned historical BP/min-sum/BP-OSD implementations. C18 is the only matched TCM-versus-conventional quality surface. On its 4048 protected inputs, conventional exact-oracle totals are `145`, `244`, and `19` for min-sum, BP-OSD-CS-7, and product-sum, while the protected TCM rows remain `263`, `262`, and deterministic/default `226`. The default BP-OSD-versus-min-plus difference is `+18`, but the promoted min-plus tie envelope remains `[218,263]`; no unconditional ordering follows.

On C72 the conventional rows record `161`, `161`, and `144` successes over 329 frozen inputs, while TCM quality remains undefined because the shared decoder interface was not certified. On C90 they record `200`, `211`, and `171` over 347 inputs, while the inherited exact TCM path remains `NOT_REACHED_EXACT_COMPILATION_BOUND`. These larger surfaces are reach/status evidence only. The promotion does not create a cross-surface winner, decoder-family ordering, runtime/memory result, asymptotic scaling law, intrinsic-intractability claim, threshold, circuit/hardware claim, learned-decoder authority, autonomous-search authority, or `QLDPC-FORGE` authority.

`QEC-CIRCUIT-001` adds a three-round phenomenological repeated-syndrome temporal substrate on the protected C18 X-error sector, with one perfect terminal readout. The exact temporal fault object has 75 coordinates—54 data-X and 21 measurement-bit coordinates—and the authoritative corpus is the complete weight-`0..2` set of 2,851 histories. The 28-bit detector map has rank 28. Detector ambiguity is deliberately retained: 2,517 distinct detector vectors occur, 135 detector fibers span multiple terminal stabilizer-equivalence classes, and those fibers contain 405 authoritative histories.

All three frozen conventional rows return corrections on all 2,851 histories. Exact terminal-oracle success totals are `2520`, `2430`, and `1736` for BP-OSD-CS-7, min-sum, and product-sum respectively; pairwise relations are promoted only on this finite corpus. Exact temporal TCM is not assigned a quality score: the complete 107-factor representation has deterministic min-fill induced width `34`, predicts peak joint table `2^35`, exceeds the frozen `2^20` peak-table cap, and stops before materialization as `TEMPORAL_TCM_EXACT_BOUND_EXHAUSTED`. TCM quality remains undefined. This reach boundary is not intrinsic-intractability, runtime, memory, threshold, scaling, hardware, or conventional-superiority evidence.

`QEC-CIRCUIT-002` freezes the `QEC-CIRCUIT-001` scientific object and changes representation only. Before any successor width was inspected, the full family `R0_BASELINE_107_FACTOR`, `R1_TERMINAL_DIRECT_AUX`, `R2_TERMINAL_CHAIN_AUX`, and `R3_CAUSAL_STATE_CHAIN` was committed. Exact local truth-table and rewrite receipts certify all three successor constructions as conservative extensions of the same temporal sum-product objective.

Under the unchanged deterministic min-fill rule, primary induced widths are `34`, `36`, `36`, and `36`, with predicted peak tables `2^35`, `2^37`, `2^37`, and `2^37` against the unchanged `2^20` cap. Every row stops before inadmissible materialization and no successor representation compiles. The promoted classification is therefore only `TEMPORAL_PREDECLARED_DECOMPOSITION_FAMILY_EXHAUSTED`. TCM quality remains undefined. This result does not establish global treewidth, intrinsic intractability, runtime or memory behavior, scaling, a changed physics model, or any downstream circuit claim.

The reviewed registry and evidence files for all twelve qLDPC/QEC stages retain `candidate_executable_not_promoted` because they are immutable scientific snapshots. Promotion authority is recorded in separate documentary overlays. This prevents later governance changes from rewriting the evidence that was actually reviewed.

## Key files

- `QTR-CHARTER-00.md`: adopted programme charter.
- `work-packages/QTR-SIG-WP00.md`: promoted signal-discovery substrate.
- `work-packages/QTR-SIG-WP01.md`: promoted finite symmetry quotient contract.
- `work-packages/QTR-SIG-WP02.md`: promoted finite linearization contract.
- `work-packages/QTR-SIG-WP03.md`: promoted bounded adversary/span-program contract.
- `work-packages/QTR-QLDPC-FIXTURE-001.md`: promoted bounded qLDPC algebra fixture contract.
- `work-packages/QTR-QLDPC-FIXTURE-002.md`: promoted bounded qLDPC systems-benchmark fixture contract.
- `work-packages/QTR-TCM-QDEC-001.md`: promoted bounded finite degeneracy-aware semiring audit.
- `work-packages/QTR-TCM-QDEC-002.md`: promoted bounded exact factorized-equivalence audit.
- `work-packages/QTR-TCM-QDEC-003.md`: promoted bounded exact degeneracy-factor and finite elimination-width audit.
- `work-packages/QTR-TCM-QDEC-004.md`: promoted bounded exact selector-parametric shared-compilation audit.
- `work-packages/QTR-QLDPC-SCALE-001A.md`: promoted bounded first-larger-BB single-instance feasibility audit.
- `work-packages/QTR-QLDPC-SCALE-001B.md`: promoted bounded finite-ladder source/structural and compilation-cap-exhaustion audit.
- `work-packages/QTR-C90-EXACT-REQUAL-001.md`: promoted bounded finite C90 deterministic resource-ledger requalification.
- `work-packages/QTR-TCM-QDEC-COMPARE-001.md`: promoted bounded finite shared-interface decoder comparison.
- `work-packages/QTR-QEC-CIRCUIT-001.md`: promoted bounded three-round phenomenological temporal decoding fixture.
- `work-packages/QTR-QEC-CIRCUIT-002.md`: promoted bounded exact temporal representation-decomposition audit.
- `registry/qldpc-fixtures.json`: immutable Fixture 001 source/candidate snapshot.
- `registry/qldpc-benchmarks.json`: immutable Fixture 002 benchmark candidate snapshot.
- `registry/tcm-qdec.json`: immutable TCM-QDEC-001 experiment candidate snapshot.
- `registry/tcm-qdec-002.json`: immutable TCM-QDEC-002 factorization candidate snapshot.
- `registry/tcm-qdec-003.json`: immutable TCM-QDEC-003 degeneracy-factor candidate snapshot.
- `registry/tcm-qdec-004.json`: immutable TCM-QDEC-004 selector-parametric compilation candidate snapshot.
- `registry/qldpc-scale-001a.json`: immutable QLDPC-SCALE-001A larger-instance candidate snapshot.
- `registry/qldpc-scale-001b-ladder-manifest.json`: immutable QLDPC-SCALE-001B pre-measurement finite-ladder manifest.
- `registry/qldpc-scale-001b.json`: immutable QLDPC-SCALE-001B candidate registry snapshot.
- `registry/qtr-c90-exact-requal-001-manifest.json`: immutable QTR-C90-EXACT-REQUAL-001 pre-outcome manifest.
- `registry/qtr-c90-exact-requal-001.json`: immutable QTR-C90-EXACT-REQUAL-001 candidate registry snapshot.
- `registry/tcm-qdec-compare-001-manifest.json`: immutable TCM-QDEC-COMPARE-001 pre-measurement manifest.
- `registry/tcm-qdec-compare-001.json`: immutable TCM-QDEC-COMPARE-001 candidate registry snapshot.
- `registry/qec-circuit-001-manifest.json`: immutable QEC-CIRCUIT-001 pre-decoder manifest.
- `registry/qec-circuit-001-manifest-amendment-001.json`: immutable pre-outcome QEC-CIRCUIT-001 semantic amendment.
- `registry/qec-circuit-001.json`: immutable QEC-CIRCUIT-001 candidate registry snapshot.
- `registry/qec-circuit-002-manifest.json`: immutable QEC-CIRCUIT-002 pre-outcome representation-family manifest.
- `registry/qec-circuit-002.json`: immutable QEC-CIRCUIT-002 candidate registry snapshot.
- `reference/qldpc_fixture_001.py`: exact dependency-free Fixture 001 evaluator.
- `reference/qldpc_fixture_002.py`: deterministic dependency-free Fixture 002 evaluator.
- `reference/tcm_qdec_001.py`: exact dependency-free TCM-QDEC-001 finite evaluator.
- `reference/tcm_qdec_002.py`: exact dependency-free TCM-QDEC-002 factorized evaluator.
- `reference/tcm_qdec_003.py`: exact dependency-free TCM-QDEC-003 degeneracy-factor evaluator.
- `reference/tcm_qdec_004.py`: exact dependency-free TCM-QDEC-004 selector-parametric compiler/evaluator.
- `reference/qldpc_scale_001a.py`: dependency-free QLDPC-SCALE-001A orchestration and exact validation entrypoint.
- `reference/qldpc_scale_001a_math.py`: exact GF(2), source reconstruction, factor-graph and elimination backend.
- `reference/qldpc_scale_001a_shared.py`: frozen source, digest, taxonomy, and resource constants.
- `reference/qldpc_scale_001a_symbolic.py`: exact symbolic compilation certificate backend.
- `reference/qldpc_scale_001b.py`: exact dependency-free finite-ladder source/structural evaluator.
- `reference/qldpc_scale_001b_report.py`: compact canonical QLDPC-SCALE-001B evidence projection.
- `reference/qtr_c90_exact_requal_001.py`: exact QTR-C90-EXACT-REQUAL-001 non-materializing resource-ledger evaluator and conditional executor.
- `reference/tcm_qdec_compare_001.py`: COMPARE-001 manifest/corpus and comparison orchestration.
- `reference/tcm_qdec_compare_001_exact_cell.py`: exact basis-reduction conventional cell evaluator.
- `reference/tcm_qdec_compare_001_evidence.py`: deterministic compact evidence projector.
- `reference/qec_circuit_001.py`: frozen QEC-CIRCUIT-001 temporal substrate/conventional engine.
- `reference/qec_circuit_001_exact.py`: authoritative amended exact QEC-CIRCUIT-001 replay.
- `reference/qec_circuit_001_evidence.py`: deterministic QEC-CIRCUIT-001 compact evidence projector.
- `reference/qec_circuit_002.py`: exact QEC-CIRCUIT-002 representation-decomposition evaluator.
- `reference/qec_circuit_002_evidence.py`: deterministic QEC-CIRCUIT-002 compact evidence projector.
- `evidence/QLDPC-FIXTURE-001-report.json`: immutable Fixture 001 exact replay report.
- `evidence/QLDPC-FIXTURE-002-report.json`: immutable Fixture 002 exact benchmark report.
- `evidence/TCM-QDEC-001-report.json`: immutable TCM-QDEC-001 exact finite report.
- `evidence/TCM-QDEC-002-report.json`: immutable TCM-QDEC-002 exact factorization report.
- `evidence/TCM-QDEC-003-report.json`: immutable TCM-QDEC-003 exact degeneracy-factor report.
- `evidence/TCM-QDEC-004-report.json`: immutable TCM-QDEC-004 exact shared-compilation report.
- `evidence/QLDPC-SCALE-001A-report.json`: immutable QLDPC-SCALE-001A exact single-instance feasibility report.
- `evidence/QLDPC-SCALE-001B-report.json`: immutable QLDPC-SCALE-001B finite-ladder structural/cap-exhaustion report.
- `evidence/QTR-C90-EXACT-REQUAL-001-report.json`: immutable QTR-C90-EXACT-REQUAL-001 candidate resource-ledger evidence.
- `evidence/TCM-QDEC-COMPARE-001-report.json`: immutable compact COMPARE-001 candidate evidence binding the full exact report payload.
- `evidence/QEC-CIRCUIT-001-report.json`: immutable compact QEC-CIRCUIT-001 candidate evidence binding the full exact report payload.
- `evidence/QEC-CIRCUIT-002-report.json`: immutable compact QEC-CIRCUIT-002 candidate evidence binding the full exact report payload.
- `reviews/QTR-QLDPC-REVIEW-001/`: Fixture 001 review-cycle closure and promotion authority records.
- `reviews/QTR-QLDPC-REVIEW-002/`: Fixture 002 review-cycle closure and promotion authority records.
- `reviews/QTR-TCM-QDEC-REVIEW-001/`: TCM-QDEC-001 review-cycle closure and promotion authority records.
- `reviews/QTR-TCM-QDEC-REVIEW-002/`: TCM-QDEC-002 review-cycle closure and promotion authority records.
- `reviews/QTR-TCM-QDEC-REVIEW-003/`: TCM-QDEC-003 review-cycle closure and promotion authority records.
- `reviews/QTR-TCM-QDEC-REVIEW-004/`: TCM-QDEC-004 review-cycle closure and promotion authority records.
- `reviews/QTR-QLDPC-SCALE-REVIEW-001A/`: QLDPC-SCALE-001A review-cycle closure and bounded promotion authority records.
- `reviews/QTR-QLDPC-SCALE-REVIEW-001B/`: QLDPC-SCALE-001B review-cycle closure and bounded promotion authority records.
- `reviews/QTR-C90-EXACT-REQUAL-REVIEW-001/`: QTR-C90-EXACT-REQUAL-001 scientific review closure and bounded promotion authority records.
- `reviews/QTR-TCM-QDEC-COMPARE-REVIEW-001/`: TCM-QDEC-COMPARE-001 review-cycle closure and bounded promotion authority records.
- `reviews/QTR-QEC-CIRCUIT-REVIEW-001/`: QEC-CIRCUIT-001 review-cycle closure and bounded promotion authority records.
- `reviews/QTR-QEC-CIRCUIT-REVIEW-002/`: QEC-CIRCUIT-002 review-cycle closure and bounded promotion authority records.
- `registry/`: governed candidate and downstream atlas records.
- `schemas/`: fail-closed record schemas.
- `reference/`: dependency-free deterministic evaluators.
- `evidence/`: committed replay reports.
- `reviews/QTR-SIG-NEXT-001/`: signal-lane intake and promotion authority records.
- `tests/`: acceptance, adversarial, and promotion-overlay fixtures.
- `ci/validate.py`: adopted WP00 validation.
- `ci/validate_downstream.py`: promoted WP01–WP03 validation.

## Validation

```bash
python ci/validate.py
python ci/validate_downstream.py
python -m unittest discover -s tests -p "test_*.py" -v
python reference/downstream_atlas.py
python reference/qldpc_fixture_001.py
python reference/qldpc_fixture_002.py
python reference/tcm_qdec_001.py
python reference/tcm_qdec_002.py
python reference/tcm_qdec_003.py
python reference/tcm_qdec_004.py
python reference/qldpc_scale_001a.py
python reference/qldpc_scale_001b_report.py --output /tmp/qldpc-scale-001b.json
python reference/qtr_c90_exact_requal_001.py static --output /tmp/qtr-c90-exact-requal-001-static.json
python reference/tcm_qdec_compare_001.py --static-only --output /tmp/tcm-qdec-compare-001-static.json
python reference/qec_circuit_001_exact.py --static-only --output /tmp/qec-circuit-001-static.json
python reference/qec_circuit_002.py --output /tmp/qec-circuit-002-full.json
```

## Foundational sources

- Low and Chuang, *Optimal Hamiltonian Simulation by Quantum Signal Processing*, arXiv:1606.02685.
- Gilyén, Su, Low, and Wiebe, *Quantum Singular Value Transformation and Beyond*, arXiv:1806.01838.
- Lee, Mittal, Reichardt, Špalek, and Szegedy, *Quantum Query Complexity of State Conversion*, arXiv:1011.3020.
- Cornelissen, Jeffery, Ozols, and Piedrafita, *Span Programs and Quantum Time Complexity*, arXiv:2005.01323.
- Wang et al., *Demonstration of low-overhead quantum error correction codes*, arXiv:2505.09684.

These sources motivate or define the bounded programme lanes. They do not discharge theorem-level source comparison, certification, novelty review, hardware validation, or downstream authorization for future claims.
