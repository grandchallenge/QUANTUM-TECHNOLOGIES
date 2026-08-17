# QTR-QLDPC-SCALE-001A — first larger protected BB feasibility

## Status

Scientific candidate only. The immutable scientific registry and evidence are `candidate_executable_not_promoted`. No promotion authority exists unless a later exact-head review and separate immutable-snapshot promotion overlay justify it.

Protected starting main: `54456dd1d273a115e82a77c6c429925e03e0925e`.

Human Steward authorization: issue #58 comment `5312914299`, `AUTHORIZE_QLDPC_SCALE_001A_WITH_AMENDMENTS`.

Execution docket: #59.

Evidence payload: `198bb28f47844aa98efa20d8c838c48870a8aef41ccfda266b16661677e363e1`.

## Scientific question

On the first source-selected larger protected bivariate-bicycle fixture, does the exact TCM representation remain structurally and computationally tractable within the predeclared deterministic resource envelope, strongly enough to justify asking separately for `QLDPC-SCALE-001B`?

A negative result is admissible. This work package is a single-instance feasibility audit, not a scaling ladder.

## Source-first target

The target was fixed before width or cost inspection by the Council contract: the smallest concrete Bravyi-et-al. BB code larger than 18 data qubits, the published `[[72,12,6]]` code.

The exact construction is bound to the authors' companion repository:

- repository `sbravyi/BivariateBicycleCodes`;
- commit `fa77e3333d3ec44c79d8f914dd24c040d1da471b`;
- path `decoder_setup.py`;
- Git blob `7ec5a36732a2a6dd229ab74405dedf36139ccda4`;
- `ell=m=6`;
- `A=x^3+y+y^2`;
- `B=y^3+x+x^2`;
- `H_X=[A|B]`;
- `H_Z=[B^T|A^T]`.

The source reports `[[72,12,6]]`. This experiment independently reconstructs `n=72` and `k=12`; distance `d=6` remains `SOURCE_REPORTED_DISTANCE` and is not independently recertified here.

## Exact source/code reconstruction

The replayed matrices satisfy:

- `H_X,H_Z` shape `36 x 72`;
- `rank(H_X)=rank(H_Z)=30`;
- exact CSS commutation;
- `k=72-30-30=12`;
- every check row has weight 6;
- every data column has weight 3.

The evaluator constructs the lexicographically first independent stabilizer basis and a canonical logical-Z quotient basis by extending `rowspace(H_Z)` inside `ker(H_X)`. The combined syndrome-plus-logical selector rank is 42, so the protected one-sector affine model is

`e(a,z) = L a XOR S z`

with `a in F_2^42` and `z in F_2^30`.

The 72 local factors have arity histogram `1:7`, `2:22`, `3:43`.

## Predeclared elimination audit

Exactly three deterministic orders are audited:

- lexicographic: induced width 24, peak joint table `2^25`;
- deterministic min-fill: induced width 18, peak joint table `2^19`;
- deterministic min-degree: induced width 18, peak joint table `2^19`.

The primary order remains deterministic min-fill. The diagnostic orders may not replace it post hoc. No globally minimum treewidth value is claimed.

## Frozen deterministic resource envelope

Per algebra, the primary exact compilation path is bounded by:

- peak joint-table entries <= `2^20`;
- cumulative exact factor-table entry evaluations <= `2^27`;
- retained canonical structural nodes/entries <= `2^22`;
- canonical serialized compiled artifact <= `512 MiB`;
- symbolic compilation AOP events <= `2^31`.

These are experimental stopping rules, not a theorem of intractability.

The primary min-fill path records peak joint table `524,288`, factor-table entry evaluations `1,066,940`, and peak retained exact factor-plus-scratch state `793,442`. All declared primary structural caps pass.

## Reusable compiled representation

The canonical execution object is a selector-independent contraction descriptor containing factor scopes, the frozen min-fill order, projection descriptors, and marginalization positions. It contains zero selector answers and zero oracle outputs.

Its canonical identity is:

- 30 elimination steps;
- 1,772 structural scalar entries;
- 14,912 serialized bytes;
- SHA-256 `c47e85efbad65619eea5d2be84bc63185d81bbac08a5e82ea71330a5b858dd5c`.

Projection arrays used during evaluation are generated lazily as scratch and discarded stepwise. Repeated evaluation does not recompile the descriptor.

The inherited hash-consed symbolic representation is independently reconstructed as a representation/resource certificate:

- sum-product: 2,157,761 nodes, 44,776,799 bytes, 20,339,963 compile AOPs;
- soft-tropical: 2,157,761 nodes, 44,776,798 bytes, 20,339,963 compile AOPs;
- min-plus: 2,157,832 nodes, 49,165,354 bytes, 20,340,034 compile AOPs.

All five declared per-algebra compilation caps pass.

## Operation taxonomy

The inherited symbolic compilation ledger remains `GF2_XOR`, `GF2_AND`, `EXACT_INT_ADD`, `EXACT_INT_MUL`, `EXACT_COMPARE`, `TABLE_READ`, `TABLE_WRITE`, `NODE_INTERN`.

The larger-fixture validation interpreter explicitly adds `INDEX_PROJECT` and `BITSET_OR`. These additional primitives are reported separately and are not converted into runtime claims.

## Frozen exact validation set

The validation set was fixed before execution:

- selector zero;
- every one of 42 unit selector coordinates;
- all-ones;
- 256 distinct non-reserved vectors generated by `SHA256(seed || uint64_be(counter))`, using ASCII seed `QLDPC-SCALE-001A::selector-validation::v1`, counter from zero, digest bits MSB-first, first consumed bit mapped to selector coordinate zero.

Total frozen validation selectors: 300.

For every selector, the reusable compiled descriptor is compared against an independent direct fixed-selector variable-elimination oracle. Result: **300/300 selectors match exactly** for sum-product, soft-tropical, and the full min-plus minimum-weight/representative/canonical-key payload.

Validation-set digest: `2eabc60f4ea2d64be6e4fea5ee33e527de46b115e727a8607b5332b19ba1e1bf`.

Validation-output digest: `b5e168d3c8f4b420c8f2c1129ea23a3a4c5d6be946053aac7f1650cc4dd79189`.

This is exact equality **on the frozen validation set only**. It is not exhaustive all-selector equivalence over `2^42` reachable selector coordinates.

## Candidate adjudication

Candidate outcome: `FEASIBLE_EXACT_WITHIN_BOUND`.

This means only that exact source reconstruction passed, the exact factor-graph audit passed, the primary parametric compilation fit every predeclared deterministic cap, exact equality held on the frozen validation sample, and no controlled approximation was used.

## Instance-reference boundary

The protected `[[18,4,4]]` and current `[[72,12,6]]` measurements may be shown side by side only as finite instance descriptors:

- 18-qubit fixture: 7 stabilizer variables, selector rank 11, certified minimum induced width 4;
- 72-qubit fixture: 30 stabilizer variables, selector rank 42, primary deterministic min-fill induced width 18.

These are not a slope, exponent, monotonic trend, family-growth result, or certified one-parameter sequence.

## Fail-closed boundary

No authority or claim is created for exhaustive all-selector equivalence, independently certified distance 6, `QLDPC-SCALE-001B`, multi-size/family scaling, bounded qLDPC-family treewidth, asymptotic complexity, runtime or memory superiority, BP/min-sum/BP-OSD comparison, controlled approximation, repeated-syndrome or circuit-level decoding, thresholds or hardware claims, learned decoding, adaptive online elimination-order optimization, `TCM-QDEC-COMPARE-001`, `QEC-CIRCUIT-001`, `QLDPC-FORGE`, or autonomous search.
