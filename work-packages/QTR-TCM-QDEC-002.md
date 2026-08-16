# QTR-TCM-QDEC-002 — Exact factorized contraction equivalence audit

Status: `candidate_executable_not_promoted`

Programme: `GCL Quantum Technologies Research (QTR)`

Experiment identifier: `TCM-QDEC-002`

Tracking issue: `#42`

Predecessor: `TCM-QDEC-001`

## 1. Purpose

`TCM-QDEC-001` established that explicit aggregation over stabilizer-equivalent error classes changes finite decoding decisions relative to coordinatewise physical-representative marginals on the protected `[[18,4,4]]` fixture. It did so with an exhaustive semantic oracle over all `2^18` physical errors.

`TCM-QDEC-002` changes one thing only: the computational representation of the promoted quotient-aware inference.

Its single question is:

> Can the exact quotient-aware semiring scores, winning logical classes, tie sets, corrections, and frozen-corpus outcomes promoted by `TCM-QDEC-001` be reproduced through local factorization and exact transfer contraction, without enumerating all physical errors in the primary inference path?

This is a representation-equivalence audit. It is not a scalability claim.

## 2. Frozen predecessor

The experiment is bound to the promoted `TCM-QDEC-001` snapshot:

- predecessor evidence payload: `1b19addcda5e04cf78a834b2162fe0873ed5eb15f3330995d8354906944b7122`;
- predecessor scientific merge: `41524f805dce4f0c7b64b8e743b75a60b4f76773`;
- predecessor bounded promotion pinned on protected main: `be022e3d1dd8490fd3856414908c6cdcb8b06ea4`;
- predecessor promotion record: `reviews/QTR-TCM-QDEC-REVIEW-001/promotion-record.json`.

The following semantics remain unchanged:

- protected `[[18,4,4]]` one-sector CSS instance;
- nine physical syndrome-check rows of rank seven;
- 128-element stabilizer span;
- four source-locked logical-Z operators;
- Fixture 002 frozen weight-`0..4` corpus of 4048 errors;
- stabilizer-equivalence success adjudication;
- the three exact semiring definitions;
- lowest-canonical-coset-key class tie rule;
- lowest-Hamming-weight-then-integer representative rule.

## 3. Local parity factorization

For each physical qubit `q`, define a 13-bit local column signature `c_q=(h_q,ell_q)`, where `h_q` is the nine-bit syndrome toggle caused by a unit error and `ell_q` is the four-bit commutation label against the source-locked logical-Z basis.

For an error pattern `e`, the combined selector is the XOR accumulation of the local signatures for qubits with `e_q=1`. The lower nine selector bits are the syndrome. The upper four bits identify the stabilizer-equivalence logical class within that syndrome fiber.

The combined 13-row parity system has exact GF(2) rank `11`: syndrome rank `7` plus four independent logical-class coordinates. Consequently there are exactly `2^11=2048=128×16` reachable combined labels.

## 4. Frozen contraction order

The qubit contraction order is fixed as `0,1,2,...,17`.

No min-fill heuristic, adaptive order selection, search, learning, or machine-dependent optimization is permitted.

After processing a prefix of qubits, the transfer state records only the accumulated 13-bit parity selector. Under the frozen order the exact prefix ranks are

`0,1,2,3,4,5,6,7,8,9,10,11,11,11,11,11,11,11,11`,

and the active sparse state counts are

`1,2,4,8,16,32,64,128,256,512,1024,2048,2048,2048,2048,2048,2048,2048,2048`.

The peak active transfer support on this finite fixture is therefore `2048` states. This bounded observation does not establish favorable scaling for a code family.

## 5. Exact semiring contractions

The three promoted algebras are represented locally without floating-point ranking.

- `sum_product_bsc_p_0_1`: local weights `(9,1)`, giving physical-state weight `9^(18-w)`.
- `soft_tropical_base_2`: local weights `(2,1)`, giving physical-state weight `2^(18-w)`.
- `min_plus_hamming`: local costs `(0,1)`, with path addition and minimum over paths; equal minima retain the lowest integer representative.

No temperature scan, learned score, or optimized parameter search is permitted.

## 6. Exact transfer recurrence

For each active selector state, a contracted qubit contributes exactly two branches: bit zero leaves the selector unchanged and bit one XORs the local column signature. Values are combined with the declared semiring operations.

For the frozen order, each algebra executes exactly `32766` binary transition relaxations. Three contractions therefore record `98298` transition relaxations in total.

These are deterministic operation counts, not runtime or complexity claims.

## 7. Class identity and deterministic correction

The factorized transfer table is indexed by `(syndrome, logical label)`. For every reachable label, the evaluator independently computes the minimum-weight representative by the min-plus transfer recurrence.

Its canonical stabilizer-coset key is `min_{s in S}(e xor s)` under integer order. The 2048 reachable selector labels map bijectively to 2048 canonical stabilizer cosets. This binds the factorized logical labels to the exact quotient semantics used by `TCM-QDEC-001` rather than introducing a new equivalence relation.

## 8. Candidate exact factorized evidence

The bounded factorization produces:

- check rank: `7`;
- combined check-plus-logical rank: `11`;
- selector capacity: `8192` formal 13-bit states;
- reachable combined labels: `2048`;
- logical classes per reachable syndrome: `16`;
- peak active transfer support: `2048`;
- transition relaxations per algebra: `32766`;
- total transition relaxations: `98298`.

The exact local-column signature digest is `2010b2f40048062203e8ee7607989ee30797e5ec37b0e94d5a5fd4eac8bfd023`.

The canonical class/minimum-representative mapping digest is `0d907375404e37533a3dd182eccea7d6a3fd6637801745f8f5b39b7c4b683f8f`.

Exact score-table digests are:

- sum-product: `1b6bd71b9b05f169f57103ae71cd8b540f88e05dbe0302f2b4d9c2562a76a7be`;
- soft tropical: `00c4b4c7612b6d05847963c4f8d432160cb2d6ec06fa4813700220461102bad5`;
- min-plus: `178a357cd13b2b9bbab03bad09f08efafecf37f2b59080bb3a6107e552e3b524`.

Global partition sanity checks are exact: sum-product mass `10^18`, soft-tropical mass `3^18 = 387420489`.

The minimum-weight distribution over the 2048 combined labels is: weight 0 `1`, weight 1 `18`, weight 2 `153`, weight 3 `636`, weight 4 `870`, weight 5 `370`.

## 9. Oracle equivalence

The primary factorized path is computed first. The already-promoted `TCM-QDEC-001` exhaustive implementation is then run separately as the verification oracle.

The candidate requires exact equality for all `128 × 3 = 384` syndrome/algebra cells at two levels: the complete set of tied winning canonical logical classes, and the deterministic correction selected after the frozen class and representative tie rules.

The factorized decision-table digests exactly reproduce the promoted identities:

- sum-product: `05dd32573ee965ce96caf707de3541f8be74b49317ad46b7929ef7dcf3bf64fc`;
- soft tropical: `ea2a96e3878758cd2daebd28673d943c27740a3e1c3579d8429a8a658e567393`;
- min-plus: `88a9a766b64c7e476ac5bb4da877a2b1f6d4e88cee88cde6ea7461cc74179f3f`.

The tied-winning-class-set digests are:

- sum-product: `3778c019c7e235d916fa27616f83a9f8251a8c2a0276e09e0ea6dc1a6125cd60`;
- soft tropical: `bf4297273ca05b1506bde6f5305464e5affdf78ba31b40e20a0fada3e26dd982`;
- min-plus: `1991fe00aaec2f8ce1163ca7b4192054002a2ef176d4839d6883c01f4e724007`.

## 10. Frozen-corpus readback

Because the decision tables are exactly equal, the factorized path reproduces the promoted quotient-aware frozen-corpus outcomes:

- sum-product: `263/4048`;
- soft tropical: `262/4048`;
- min-plus: `226/4048`.

All factorized corrections realize the input syndrome; remaining failures are zero-syndrome wrong-logical-class failures.

Tie envelopes are also preserved exactly: sum-product `[263,263]`, soft tropical `[262,262]`, min-plus `[218,263]` with default `226`. Thus the representation change does not erase the min-plus ambiguity identified in `TCM-QDEC-001`.

## 11. Interpretation

The positive result, if admitted, is narrowly structural: on this exact finite fixture and these exact three algebras, the promoted stabilizer-coset inference can be expressed as a local parity transfer contraction and reproduces the exhaustive quotient oracle exactly.

It does not follow that the representation remains tractable as code size grows. The observed rank-11 boundary state is a property of this instance and chosen factorization. The experiment closes a representation gap, not a scaling theorem.

## 12. Evidence and replay

The deterministic report is regenerated with:

```bash
python reference/tcm_qdec_002.py --output evidence/TCM-QDEC-002-report.json
```

Candidate evidence payload: `efd9e76957421494897e2cc319137874b61093d66ea871f0202df3d07e6eb3c0`.

The replay/adversarial harness must verify immutable predecessor evidence and promotion binding; exact local-column construction from protected checks and logical-Z operators; combined rank and stabilizer-zero-logical-label properties; prefix rank/support profiles; exact class mapping and score-table digests; exact winning-class tie-set equality with the exhaustive predecessor oracle; exact decision-table equality; exact frozen-corpus success counts and tie envelopes; deterministic transition counters; and fail-closed mutations of predecessor identity, logical basis, algebra, contraction order, tie rule, and downstream authority.

## 13. Claim boundary

`TCM-QDEC-002` may seek bounded promotion only for the exact finite factorized-equivalence result described above.

It does **not** certify or authorize scalable tensor-network or transfer decoding; asymptotic complexity improvement; practical runtime or memory advantage; larger-code decoder performance; general qLDPC decoder performance; BP-OSD comparison; circuit-level or phenomenological noise; hardware validation; thresholds or pseudo-thresholds; learned decoder parameters; adaptive contraction-order optimization; `TCM-QDEC-003`; `QLDPC-FORGE`; or autonomous code, decoder, circuit, or architecture search.

## 14. Promotion condition

Promotion requires fresh exact-head replay, green adversarial tests, independent review of the parity/logical-label construction, verification that oracle enumeration is used only as a comparator rather than as the primary factorized inference path, and a bounded Referee disposition.

Until then, `TCM-QDEC-002` remains executable candidate evidence only.
