# QTR-TCM-QDEC-003 — Exact degeneracy-variable elimination-width audit

Status: `candidate_executable_not_promoted`

Programme: `GCL Quantum Technologies Research (QTR)`

Experiment identifier: `TCM-QDEC-003`

Tracking issue: `#47`

Predecessor: `TCM-QDEC-002`

## 1. Purpose

`TCM-QDEC-002` proved that the promoted quotient-aware decoder semantics can be reproduced by exact local parity transfer contraction without using the `2^18` physical-error enumeration as the primary inference path. Its fixed transfer representation nevertheless carried all `2048 = 128 × 16` reachable syndrome/logical-class labels and reached a peak active support of `2048` states.

`TCM-QDEC-003` changes one thing only: the variables over which the exact quotient score is contracted.

Its single question is:

> After syndrome/logical class is fixed, can the remaining stabilizer degeneracy be contracted directly through a smaller exact factor graph, and what is the exact minimum elimination width of that graph on the protected `[[18,4,4]]` fixture?

This is a finite representation and elimination-width audit. It is not a scaling or speed claim.

## 2. Frozen predecessor

The experiment is bound to the bounded-promoted `TCM-QDEC-002` snapshot:

- predecessor evidence payload: `efd9e76957421494897e2cc319137874b61093d66ea871f0202df3d07e6eb3c0`;
- predecessor scientific merge: `d3340c91df3aa72dc5c7ba75906128c8eef2e174`;
- predecessor bounded promotion pinned on protected main: `693756a2569e87eb6cfeaf276ccc2bc2474cd92b`;
- predecessor promotion record: `reviews/QTR-TCM-QDEC-REVIEW-002/promotion-record.json`.

The protected code, source-locked logical basis, Fixture 002 corpus, stabilizer-equivalence correctness semantics, three exact score algebras, class tie rule, representative tie rule, score tables, decision tables, tied-winning-class sets, and min-plus tie envelope are unchanged.

## 3. Degeneracy reparameterization

The nine physical X-check rows have rank seven. `TCM-QDEC-003` chooses the lexicographically first independent row subset. On the protected fixture this is exactly rows

`[0,1,2,3,4,5,6]`.

These seven rows span the exact promoted 128-element stabilizer group. They are therefore used as seven binary degeneracy variables.

For each reachable 13-bit syndrome-plus-logical selector, the evaluator independently chooses a deterministic seed representative from the lexicographically first independent selector-column basis. The seed basis is exactly qubits

`[0,1,2,3,4,5,6,7,8,9,10]`.

Because the combined selector map has rank eleven, these eleven columns generate all `2048` reachable selector classes.

Each physical qubit is now a local factor. Its scope contains only those stabilizer-generator variables whose selected check row touches that qubit. The exact scope-size distribution is:

- arity 1: `2` factors;
- arity 2: `8` factors;
- arity 3: `8` factors.

No initial local factor has arity greater than three.

Factor-scope digest:

`9b9f68ff6cf22447892c6d853defa6daf5f08c5859ffd4352500d1e11b89052d`.

## 4. Exact elimination-order audit

The factor scopes are independent of syndrome, logical class, and semiring values. The candidate therefore performs one finite exhaustive audit of all

`7! = 5040`

stabilizer-variable elimination orders.

The exact induced-width histogram is:

- width `4`: `720` orders;
- width `5`: `4320` orders.

Thus the exact minimum induced width on this finite factor graph is `4`. The lexicographically first minimum-width order is

`[2,4,0,1,3,5,6]`.

Under that order:

- peak joint scope before elimination: `5` variables;
- peak joint table: `32` assignments;
- maximum emitted factor scope: `4` variables;
- maximum emitted factor table: `16` entries;
- assignment evaluations per class contraction: `126`;
- emitted factor-table entries per class contraction: `63`.

Order-audit digest:

`76e357c69d25f552d21a114c632a322256087b0fd1036d7ee914c02e39c7aff0`.

Frozen-order trace digest:

`898704d5fa4599dd4e11b1e85765046d0b6bb41ddfedaa3d4e329cf682dc6566`.

The minimum-width result is a property of this seven-variable finite factor graph only. It does not establish bounded treewidth for any qLDPC family.

## 5. Exact class contractions

For each of the `2048` reachable syndrome/logical classes, the evaluator contracts the seven stabilizer variables under the frozen optimal order.

The two partition-score algebras reuse the exact predecessor local weights:

- `sum_product_bsc_p_0_1`: `(9,1)`;
- `soft_tropical_base_2`: `(2,1)`.

For min-plus, the exact factor values carry both:

1. minimum Hamming weight with lowest-integer representative as the secondary tie coordinate;
2. minimum physical integer independently, which is the canonical stabilizer-coset key.

This product construction allows the minimum-weight correction representative and canonical class key to be recovered by the same seven-variable factorization without enumerating all 128 stabilizer elements for each class.

## 6. Exact equivalence result

The degeneracy-variable contraction reproduces the exact `TCM-QDEC-002` class mapping:

`0d907375404e37533a3dd182eccea7d6a3fd6637801745f8f5b39b7c4b683f8f`.

It also reproduces all three exact score-table identities:

- sum-product: `1b6bd71b9b05f169f57103ae71cd8b540f88e05dbe0302f2b4d9c2562a76a7be`;
- soft tropical: `00c4b4c7612b6d05847963c4f8d432160cb2d6ec06fa4813700220461102bad5`;
- min-plus: `178a357cd13b2b9bbab03bad09f08efafecf37f2b59080bb3a6107e552e3b524`.

The primary degeneracy contraction is computed first. The promoted `TCM-QDEC-002` transfer representation is then reconstructed separately as the equivalence oracle.

The candidate requires direct equality of:

- all `6144 = 2048 × 3` class-score entries;
- all `2048` minimum-representative/canonical-class mapping entries;
- all `384` syndrome-by-algebra tied-winning-class sets;
- all `384` deterministic corrections.

The decision-table and winning-class-tie digests remain exactly those promoted by `TCM-QDEC-002`.

## 7. Frozen-corpus readback

The frozen Fixture 002 corpus outcomes remain:

- sum-product: `263/4048`, tie envelope `[263,263]`;
- soft tropical: `262/4048`, tie envelope `[262,262]`;
- min-plus: `226/4048`, tie envelope `[218,263]`.

The min-plus ambiguity is therefore not removed by the new representation.

## 8. The retained tradeoff

The local factor width is dramatically smaller than the `2048`-state transfer support of `TCM-QDEC-002`, but this representation evaluates classes separately.

There are `2048 × 3 = 6144` exact class contractions. At `126` assignment evaluations per contraction, the deterministic total is

`774144` assignment evaluations.

`TCM-QDEC-002` recorded `98298` binary transition relaxations across its three global transfer contractions.

Those counters are not primitive-for-primitive equivalent and are not runtime measurements. The exact reduced count ratio is recorded only as `43008:5461`, with **no arithmetic-reduction claim**. In particular, this candidate does not convert smaller local factor width into a claim of lower runtime, lower memory, or better practical complexity.

This negative systems tradeoff is part of the evidence.

## 9. Interpretation

If admitted, `TCM-QDEC-003` establishes a specific structural fact:

> On the protected `[[18,4,4]]` fixture, quotient-aware class scores can be represented as exact contractions over seven stabilizer-degeneracy variables whose finite factor graph has exact minimum induced width four, while reproducing the entire promoted score/mapping/tie/decision object.

This is stronger than merely reproducing final success totals, but weaker than a scalable decoder theorem.

The experiment separates two questions that must not be conflated:

- **local structural width:** favorable on this fixture;
- **total arithmetic work under the present class-by-class construction:** larger than the predecessor counter.

That distinction is the principal scientific result of this stage.

## 10. Replay

The deterministic report is regenerated with:

```bash
python reference/tcm_qdec_003.py --output evidence/TCM-QDEC-003-report.json
```

Candidate evidence payload:

`f0ecdae04f3da4f0508454da59ce406a4e6c461f88f1784279cb6d7e360b595f`.

The replay/adversarial harness checks predecessor and promotion binding, stabilizer-basis identity, selector-seed basis, factor-scope digest, exhaustive 5040-order audit, frozen optimal order, exact mapping/score/tie/decision equality, retained min-plus ambiguity, operation-count tradeoff, and fail-closed mutations of basis, seed, order, algebra, predecessor, and downstream authority.

## 11. Context

The experiment is conceptually consonant with the tensor-network view of quantum decoding developed by Ferris and Poulin (`arXiv:1312.4578`) and with later general tensor-network decoding work such as Chubb (`arXiv:2101.04125`). Those works motivate contraction as a decoding representation; they do not certify the finite identities or width result recorded here.

## 12. Claim boundary

`TCM-QDEC-003` may seek bounded promotion only for the exact finite degeneracy-variable representation and elimination-width result described above.

It does **not** certify or authorize bounded contraction width for a qLDPC family; scalable tensor-network decoding; asymptotic or practical complexity advantage; runtime or memory superiority; larger-code performance; general qLDPC decoder performance; BP-OSD comparison; circuit-level or phenomenological noise; hardware validation; thresholds or pseudo-thresholds; learned decoding; adaptive online contraction ordering; `TCM-QDEC-004`; `QLDPC-FORGE`; or autonomous code, decoder, circuit, or architecture search.

## 13. Promotion condition

Promotion requires fresh exact-head repository replay, green adversarial tests, independent review of the stabilizer-basis quotient parameterization and elimination-width calculation, verification that the score/mapping/tie/decision objects are exactly predecessor-equivalent, explicit retention of the unfavorable arithmetic-count comparison, and a bounded Referee disposition.

Until then, `TCM-QDEC-003` remains executable candidate evidence only.
