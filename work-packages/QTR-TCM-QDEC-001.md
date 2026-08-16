# QTR-TCM-QDEC-001 — Degeneracy-aware finite semiring inference audit

Status: `candidate_executable_not_promoted`

Programme: `GCL Quantum Technologies Research (QTR)`

Experiment identifier: `TCM-QDEC-001`

Tracking issue: `#37`

Predecessor: `QLDPC-FIXTURE-002`

## 1. Purpose

This work package opens the first bounded `TCM-QDEC` experiment above the two promoted qLDPC fixtures.

Its single question is:

> When the protected code, syndrome, frozen error corpus, and correctness oracle are held fixed, does explicit aggregation over stabilizer-equivalent error classes change the decisions produced by otherwise matched finite semiring inference?

The experiment is an exact finite semantic oracle. It is not a scalable decoder implementation, tensor-network benchmark, threshold study, or hardware experiment.

A favorable result is not required for admission. Tie sensitivity, regressions, and negative evidence are first-class outputs.

## 2. Protected predecessor

The experiment consumes the immutable Fixture 002 evidence and promotion overlay rather than redefining the benchmark substrate.

Bound identities are:

- Fixture 002 evidence payload: `d98c5d73f7fdf9259a35be60580dc9b6c32c5e4483cd765ed0dcba594b9299e5`;
- frozen corpus SHA-256: `260b1a43cf1d777f28c475918e91a5f7cefc5d28a2bfb556338f7e30058f58a8`;
- Fixture 002 scientific merge: `51c31bde2e0630314d3d48dceb9b92969c37c228`;
- Fixture 002 promotion merge: `074612e39e1232d1644edc487914ca571189f409`;
- Fixture 001 evidence payload: `6c2095f48762178bf0fe5c2b5fce8299261733912a1cccc7884d11f344718427`;
- exact coset-leader table SHA-256: `96ce94c378b7b1fc5fe032fbd253aa932c1ca8abcb17b3d3c89b3ecda601da29`.

The promoted predecessors remain unchanged by this package.

## 3. Exact finite state space

For the protected one-sector `[[18,4,4]]` instance, the evaluator enumerates all

\[
2^{18}=262144
\]

physical error representatives.

The exact finite geometry is:

- `128` reachable syndromes;
- `2048` physical error representatives for each syndrome;
- stabilizer span size `128`;
- `16` stabilizer-equivalence logical classes for each syndrome.

Scoring remains restricted to the Fixture 002 frozen corpus of all 18-bit errors of Hamming weight `0..4`, totalling `4048` cases.

No sampling or random seed is used.

## 4. Controlled axis A — terminal treatment

Only the terminal treatment of the syndrome-compatible error space is varied.

### 4.1 Representative-naive marginals

`representative_naive_marginals` computes exact coordinatewise semiring marginals over physical error representatives compatible with the input syndrome. Each coordinate is hard-decoded independently. Bit ties choose zero.

No syndrome repair or projection is applied after the coordinatewise decision. If the resulting physical representative does not realize the input syndrome, that failure is retained explicitly.

This construction is intentionally a diagnostic representative-space baseline. It is not claimed to be a competitive practical decoder.

### 4.2 Stabilizer-coset aggregation

`stabilizer_coset_aggregate` first quotients syndrome-compatible error representatives by the certified stabilizer span. The semiring score is aggregated over each of the `16` logical classes.

The winning class is selected by the declared semiring reduction. If several classes tie, the default rule chooses the lowest canonical coset key. The emitted correction is the lowest-Hamming-weight representative in the selected class, with integer order as the final tie break.

Because the emitted representative belongs to the selected syndrome-compatible class, this treatment realizes every input syndrome by construction.

## 5. Controlled axis B — exact semiring reduction

Three reductions are compared. All ranking arithmetic is exact integer arithmetic.

### 5.1 Sum-product

`sum_product_bsc_p_0_1` assigns an error of weight `w` the integer score

\[
9^{18-w},
\]

which is proportional to the likelihood numerator for an independent binary symmetric channel with `p=0.1`. Scores are summed within the relevant marginal or quotient class and maximized.

### 5.2 Soft tropical

`soft_tropical_base_2` assigns the exact integer score

\[
2^{18-w}.
\]

Aggregating these scores is ranking-equivalent to a soft minimum with inverse temperature `beta = ln(2)`, while avoiding floating-point exponential and logarithmic ranking.

### 5.3 Min-plus

`min_plus_hamming` uses minimum Hamming weight as the tropical class score.

No arbitrary continuous temperature scan, learned score, or optimized parameter search is permitted in this work package.

## 6. Correctness adjudication

For a true physical error `e` and emitted correction `c`, success is certified only when

\[
e\oplus c\in S,
\]

where `S` is the certified stabilizer span. Equivalently, the residual must have zero syndrome and belong to the correct stabilizer equivalence class.

The evaluator therefore distinguishes:

- successful stabilizer-equivalent correction;
- nonzero residual syndrome;
- zero residual syndrome but wrong logical coset.

The following notions are deliberately not conflated:

\[
\text{syndrome satisfaction}
\neq
\text{minimum-weight correction}
\neq
\text{logical success}.
\]

## 7. Exact finite result

The candidate evaluator produces the following six-cell result on the frozen `4048`-case corpus:

| terminal treatment | sum-product | soft tropical | min-plus |
|---|---:|---:|---:|
| representative-naive marginals | `37` | `1` | `37` |
| stabilizer-coset aggregate | `263` | `262` | `226` |

Matched quotient aggregation therefore changes the number of successful frozen-corpus decisions by:

- sum-product: `+226`;
- soft tropical: `+261`;
- min-plus: `+189`.

For these matched comparisons, the default quotient treatment repairs the stated number of representative-space failures and breaks no representative-space successes.

This is a finite mechanism result only. It does not establish decoder superiority outside the declared experiment.

## 8. Relation to Fixture 002 baselines

The evaluator independently replays the promoted Fixture 002 anchors:

- exact minimum-weight coset-leader lookup: `240/4048` successful;
- greedy syndrome descent: `125/4048` successful.

Under the default class tie rule, quotient-aware sum-product records `263` successful frozen-corpus cases, which is a net `+23` relative to the exact minimum-weight lookup. That scalar difference must not be read as monotone improvement: the two decision rules disagree substantially.

Relative to the exact lookup, quotient-aware sum-product:

- repairs `131` exact-lookup failures;
- breaks `108` exact-lookup successes;
- leaves the remaining `3809` outcomes unchanged.

Soft tropical similarly repairs `130` and breaks `108`; min-plus repairs `96` and breaks `110`.

The experiment therefore does not promote a statement that TCM-QDEC has beaten the exact reference decoder. It demonstrates that the finite objective induced by stabilizer-class aggregation is genuinely different from minimum-weight representative selection.

## 9. Tie sensitivity

Winning logical classes are not always unique. The evaluator retains this degeneracy explicitly.

For the frozen corpus, the success-count envelope over all permitted choices among tied winning classes is:

- sum-product: `[263, 263]`;
- soft tropical: `[262, 262]`;
- min-plus: `[218, 263]`.

Thus the aggregate success count is tie-invariant for the selected sum-product and soft-tropical reductions on this corpus, despite non-unique winning classes. The min-plus result is materially tie-sensitive; its default lowest-coset-key result is `226`.

The interval `[218,263]` is part of the scientific evidence. It must not be replaced by the single default number when characterizing the min-plus mechanism.

## 10. Evidence and replay

The deterministic report is regenerated with:

```bash
python reference/tcm_qdec_001.py \
  --output evidence/TCM-QDEC-001-report.json
```

The committed candidate evidence payload is:

`1b19addcda5e04cf78a834b2162fe0873ed5eb15f3330995d8354906944b7122`.

The replay/adversarial harness must verify, at minimum:

- exact committed-evidence regeneration;
- predecessor payload and promotion identities;
- frozen Fixture 002 corpus identity;
- complete `2^18` state-space geometry;
- exact six-cell success matrix;
- residual-syndrome and wrong-logical-coset failure classification;
- exact decision-table identities;
- quotient-versus-representative repair/break counts;
- replay of Fixture 002 exact and greedy anchors;
- tie envelopes and tie-invariance claims;
- fail-closed rejection of semiring, predecessor, corpus, promotion, and downstream-authority drift.

## 11. Claim boundary

`TCM-QDEC-001` may seek bounded promotion only for the exact finite semantic comparison described above.

It does **not** certify or authorize:

- scalable tensor-network contraction or a scalable TCM decoder;
- general qLDPC decoder performance;
- practical decoder superiority;
- BP-OSD performance or comparison claims;
- circuit-level or phenomenological noise;
- Kunlun or other hardware validation;
- thresholds or pseudo-thresholds;
- portable latency or runtime-memory claims;
- learned decoder parameters;
- adaptive or autonomous parameter search;
- `TCM-QDEC-002`;
- `QLDPC-FORGE`;
- autonomous code, decoder, circuit, or architecture search.

## 12. Promotion condition

Promotion requires:

1. exact protected-predecessor binding;
2. byte-stable committed report regeneration;
3. complete finite state-space replay;
4. exact six-cell matrix reproduction;
5. independent verification of matched repair/break counts;
6. explicit retention of representative-space syndrome failures;
7. explicit retention of min-plus tie sensitivity;
8. green adversarial tests;
9. fresh exact-head QTR and GCL workflows;
10. a fresh bounded office review and Referee disposition.

Until then, `TCM-QDEC-001` remains executable candidate evidence only.
