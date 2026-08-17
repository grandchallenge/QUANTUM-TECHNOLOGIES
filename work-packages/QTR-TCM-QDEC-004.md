# QTR-TCM-QDEC-004 — shared exact selector-parametric compilation

## Status

Referee-promoted bounded through the separate overlay in `reviews/QTR-TCM-QDEC-REVIEW-004/promotion-record.json`. The immutable scientific registry and evidence remain `candidate_executable_not_promoted` and are not rewritten by promotion.

Reviewed head: `8177a57b63e3f2c953a028691d305563f298b572`.

Scientific merge: `7eff1025e97ff962a6fed81e6f2fa0f4d14653a3`.

Evidence payload: `a5c7e59fa849ddc37c070d78d4a4dab8b07ae5ceccfecefeb5a20f4ae0dc83a7`.

Human Steward authority remains issue #52 comment `5311144666`; execution docket #53 authorized TCM-QDEC-004 only.

## Scientific question

Can the exact selector-parameterized quotient contraction be compiled once into a reusable selector-independent structural object and then evaluated across all 2048 reachable selectors with less duplicated deterministic work, while preserving the complete promoted score, mapping, tie and decision semantics?

## Frozen substrate

The experiment changes only evaluation architecture. It freezes the protected `[[18,4,4]]` one-sector code, source logical basis, stabilizer basis rows `[0,1,2,3,4,5,6]`, selector seed basis qubits `[0,1,2,3,4,5,6,7,8,9,10]`, seven-variable elimination order `[2,4,0,1,3,5,6]`, all three exact algebras, canonical-class and minimum-representative rules, class tie rule, and every protected TCM-QDEC-003 semantic digest.

## Primary mechanism

Write the promoted affine physical error as

`e(a,z) = L a XOR S z`,

with eleven selector parameters `a` and seven stabilizer-degeneracy variables `z`.

For each local qubit factor, the evaluator constructs an exact symbolic expression depending on its stabilizer scope and, for the first eleven physical unit-basis sites, at most one selector parameter. It then eliminates the seven `z` variables in the frozen TCM-QDEC-003 order while leaving all selector parameters symbolic.

The result is a canonical hash-consed expression DAG for each algebra. The DAG contains exact terminals, selector-parameter choice nodes, and exact semiring operation nodes. Compilation does not enumerate or store the 2048 evaluated selector answers. Selector coordinates enter only when the already-compiled DAG is evaluated.

A complete answer table is prohibited as the primary compiled object. Such a cache is not needed by the promoted mechanism.

## Exact semantic result

The promoted finite result preserves exact equality with TCM-QDEC-003 at the complete certified boundary:

- 6144 class-score entries;
- 2048 canonical-class/minimum-representative entries;
- 384 winning-class tie sets;
- 384 deterministic decisions;
- frozen-corpus success totals `263`, `262`, `226`;
- tie envelopes `[263,263]`, `[262,262]`, `[218,263]`.

## Predeclared abstract-operation accounting

Both the compiled path and an independently re-instrumented TCM-QDEC-003 classwise replay use the same typed AOP ledger:

`GF2_XOR`, `GF2_AND`, `EXACT_INT_ADD`, `EXACT_INT_MUL`, `EXACT_COMPARE`, `TABLE_READ`, `TABLE_WRITE`, `NODE_INTERN`.

The unweighted AOP sum is a deterministic abstract event count only. It is not a runtime model. No runtime or memory superiority may be inferred from it.

Compilation cost, canonical compiled size, all-selector evaluation cost, one-shot cost, repeated-sweep break-even, and the original predecessor-specific counters are reported separately. The original `774144` assignment evaluations and `98298` TCM-QDEC-002 transition relaxations remain non-equivalent historical counters and are not translated into AOPs.

## Promoted bounded result

The exact compilation retains:

- sum-product: 371 reachable expression nodes;
- soft-tropical: 371 reachable expression nodes;
- min-plus/product objective: 388 reachable expression nodes;
- 1130 reachable nodes total;
- 65,506 canonical serialized bytes total.

No selector answer is materialized during compilation.

The common-ledger counts are:

- compilation: 10,160 AOPs;
- evaluation of all 2048 selectors in all three algebras: 12,694,528 AOPs;
- complete one-shot compiled path: 12,704,688 AOPs;
- re-instrumented TCM-QDEC-003 classwise replay: 14,115,840 AOPs;
- one-shot reduction: 1,411,152 AOPs;
- exact complete-sweep break-even: `k = 1`.

This promotes only the classification `EXACT_SHARED_COMPILATION_WITH_REDUCED_DUPLICATION` **under the declared abstract ledger on this fixed fixture**. It does not establish runtime speedup, memory superiority, asymptotic improvement, or family-scale behavior.

## Fail-closed boundary

No authority is created for `QLDPC-SCALE-001A`, a multi-size scaling ladder, BP/min-sum/BP-OSD comparison, repeated syndrome extraction, measurement error, circuit-level noise, thresholds, learned decoding, adaptive online contraction order, `QLDPC-FORGE`, or autonomous architecture search.
