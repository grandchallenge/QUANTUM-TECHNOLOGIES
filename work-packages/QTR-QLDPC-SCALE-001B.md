# QTR-QLDPC-SCALE-001B — bounded finite BB ladder

Status: `candidate_executable_not_promoted`

Authority:
- protected start: `57e465af680fc0030d47e14d9f40c9e2ab58dc09`;
- Human Steward: issue #64 comment `5315569335`;
- Referee recommendation: issue #64 comment `5315553347`;
- execution docket: #65;
- pre-measurement instrumentation locks: `5315653902`, `5315658456`.

Canonical manifest:
- `registry/qldpc-scale-001b-ladder-manifest.json`;
- manifest payload `0beef3aa1062bd30c691e3f01d00db0d1d8890d07c0dca2761fa933978ff09f5`;
- first manifest commit `3fd6d882a5992c1be82e11f1f315a53130ffff8c`.

## Scientific question

Across the fixed source-bound ladder

`72(anchor) -> 90 -> 108 -> 144 -> 288 -> 784`,

how do the exact TCM factor-graph structure, named deterministic elimination widths,
compiled-representation feasibility and bounded exact semantic path change under one
unchanged protocol?

This is a finite-ladder audit only. It is not an asymptotic scaling experiment.

## Exact source/structural result

All five post-anchor source reconstructions pass exactly. The exact derived
`(n,k)` values agree with the source-reported code dimensions, CSS commutation is
zero, every check row has weight 6, every data column has weight 3, and the
canonical stabilizer/logical/selector constructions are replayable.

The exact named-order induced widths are:

| n | k | stabilizer rank | selector rank | lex | min-fill | min-degree | primary peak |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 72 | 12 | 30 | 42 | 24 | 18 | 18 | `2^19` |
| 90 | 8 | 41 | 49 | 28 | 25 | 25 | `2^26` |
| 108 | 8 | 50 | 58 | 33 | 30 | 30 | `2^31` |
| 144 | 12 | 66 | 78 | 31 | 34 | 38 | `2^35` |
| 288 | 12 | 138 | 150 | 71 | 79 | 83 | `2^80` |
| 784 | 24 | 380 | 404 | 253 | 201 | 223 | `2^202` |

`min-fill` is the frozen primary order; none of the widths above are a global
treewidth certificate.

Every post-anchor Level-S structural audit remains inside the frozen structural
budget. Rung 784 is the largest:
- total structural ledger events: `509630167 < 2^30`;
- peak retained structural entries: `69939 < 2^22`.

## Compilation boundary

The promoted 72-qubit anchor had primary min-fill width 18 and peak table `2^19`,
inside the `2^20` cap.

The first post-anchor rung, 90, has min-fill width 25 and predicted peak joint
table `2^26 = 67108864`, so the unchanged compilation cap is crossed before
table materialization. Every later post-anchor rung also exceeds that cap under
the same primary order.

No 001B post-anchor compiled object is therefore constructed and no 001B
post-anchor selector-validation set is evaluated. This is a deterministic
scientific stopping-rule result, not a wall-clock, host-memory or intractability
claim.

Primary adjudication:

`FINITE_LADDER_STRUCTURAL_AUDIT_COMPLETED__COMPILATION_BOUND_EXHAUSTED`

Secondary exact finite-ladder predicate:

`FINITE_LADDER_NONMONOTONE_STRUCTURE_OBSERVED`

because lexicographic named-order width decreases from 33 at n=108 to 31 at
n=144. This finite non-monotonicity is retained rather than converted into a
smoothed growth narrative.

## Comparison-maturity boundary

The programme now has exact source and named-order structural certificates for
all five post-72 rungs, and a certified deterministic compilation-bound
exhaustion beginning at n=90. This satisfies the Council's *maturity criterion
for considering a future referral* to `TCM-QDEC-COMPARE-001`.

It creates **no comparison authority**.

## Claim exclusions

This candidate does not establish:
- global treewidth for any rung or family;
- an asymptotic/family scaling law or fitted exponent;
- a generally scalable decoder;
- runtime or memory superiority;
- independently certified distances 10, 10, 12, 18 or 24;
- controlled approximation;
- BP/min-sum/BP-OSD comparison;
- circuit-level/repeated-syndrome behavior;
- thresholds or hardware behavior;
- learned decoding or adaptive online ordering;
- `TCM-QDEC-COMPARE-001`, `QEC-CIRCUIT-001`, `QLDPC-FORGE`, or autonomous-search authority.

Evidence payload: `6b8076376eb621710d993d1cb8768c7d4c03b7fe9d67802e6ae2e77212b610fc`.
