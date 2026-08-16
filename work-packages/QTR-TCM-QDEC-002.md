# QTR-TCM-QDEC-002 — Exact factorized contraction equivalence audit

Status: `referee_promoted_bounded`

Programme: `GCL Quantum Technologies Research (QTR)`

Experiment identifier: `TCM-QDEC-002`

Tracking issue: `#42`

Predecessor: `TCM-QDEC-001`

Reviewed scientific head: `9123a9c6cc2c163031d8bff0c46e0a9dd4c8f8fd`

Scientific merge: `d3340c91df3aa72dc5c7ba75906128c8eef2e174`

Promotion authority: `reviews/QTR-TCM-QDEC-REVIEW-002/promotion-record.json`

The reviewed `registry/tcm-qdec-002.json` and `evidence/TCM-QDEC-002-report.json` remain immutable scientific snapshots with status `candidate_executable_not_promoted`. Bounded authority is carried only by the separate promotion overlay.

## 1. Purpose

`TCM-QDEC-001` established that explicit aggregation over stabilizer-equivalent error classes changes finite decoding decisions relative to coordinatewise physical-representative marginals on the protected `[[18,4,4]]` fixture. It did so with an exhaustive semantic oracle over all `2^18` physical errors.

`TCM-QDEC-002` changes one thing only: the computational representation of the promoted quotient-aware inference.

Its single question is:

> Can the exact quotient-aware semiring scores, winning logical classes, tie sets, corrections, and frozen-corpus outcomes promoted by `TCM-QDEC-001` be reproduced through local factorization and exact transfer contraction, without enumerating all physical errors in the primary inference path?

The promoted result is a representation-equivalence result. It is not a scalability claim.

## 2. Frozen predecessor

The experiment is bound to the promoted `TCM-QDEC-001` snapshot:

- predecessor evidence payload: `1b19addcda5e04cf78a834b2162fe0873ed5eb15f3330995d8354906944b7122`;
- predecessor scientific merge: `41524f805dce4f0c7b64b8e743b75a60b4f76773`;
- predecessor bounded promotion pinned on protected main: `be022e3d1dd8490fd3856414908c6cdcb8b06ea4`;
- predecessor promotion record: `reviews/QTR-TCM-QDEC-REVIEW-001/promotion-record.json`.

The protected `[[18,4,4]]` one-sector CSS instance, stabilizer span, source-locked logical-Z basis, Fixture 002 corpus, correctness adjudication, three semiring definitions, and all tie rules are unchanged.

## 3. Local parity factorization

Each physical qubit contributes a 13-bit local column signature consisting of nine syndrome-check parities and four commutation parities against the source-locked logical-Z basis. For an error pattern, the combined selector is the XOR accumulation of the signatures for occupied qubits.

The combined parity system has exact GF(2) rank `11`: syndrome rank `7` plus four independent logical-class coordinates. The `2048 = 128 × 16` reachable selector labels map bijectively to the exact syndrome/stabilizer-coset classes certified by the predecessor.

## 4. Frozen contraction order and finite geometry

The qubit contraction order is fixed as `0,1,2,...,17`. No adaptive order selection, min-fill heuristic, learning, or search is permitted.

The exact prefix ranks are

`0,1,2,3,4,5,6,7,8,9,10,11,11,11,11,11,11,11,11`,

with active sparse state counts

`1,2,4,8,16,32,64,128,256,512,1024,2048,2048,2048,2048,2048,2048,2048,2048`.

The finite peak active transfer support is `2048`. This does not establish bounded width or favorable scaling for any qLDPC family.

## 5. Exact semiring contractions

The three promoted algebras are represented locally without floating-point ranking:

- `sum_product_bsc_p_0_1`: local weights `(9,1)`, yielding state weight `9^(18-w)`;
- `soft_tropical_base_2`: local weights `(2,1)`, yielding `2^(18-w)`;
- `min_plus_hamming`: local costs `(0,1)`, with Hamming-weight minimization and the frozen representative tie rule.

Each algebra executes exactly `32766` binary transition relaxations under the frozen order; the three contractions record `98298` relaxations in total. These are deterministic finite operation counts, not runtime or asymptotic claims.

## 6. Exact admitted evidence

The promoted finite identities include:

- combined check-plus-logical rank: `11`;
- reachable combined labels: `2048`;
- peak active transfer support: `2048`;
- local-column signature SHA-256: `2010b2f40048062203e8ee7607989ee30797e5ec37b0e94d5a5fd4eac8bfd023`;
- canonical class/minimum-representative mapping SHA-256: `0d907375404e37533a3dd182eccea7d6a3fd6637801745f8f5b39b7c4b683f8f`.

Exact score-table digests are:

- sum-product: `1b6bd71b9b05f169f57103ae71cd8b540f88e05dbe0302f2b4d9c2562a76a7be`;
- soft tropical: `00c4b4c7612b6d05847963c4f8d432160cb2d6ec06fa4813700220461102bad5`;
- min-plus: `178a357cd13b2b9bbab03bad09f08efafecf37f2b59080bb3a6107e552e3b524`.

Global partition checks are exact: sum-product mass `10^18` and soft-tropical mass `3^18 = 387420489`.

## 7. Oracle equivalence

The primary factorized path is computed before the promoted `TCM-QDEC-001` exhaustive implementation is invoked as an independent verification oracle.

For all `128 × 3 = 384` syndrome/algebra cells, the complete tied winning canonical-class sets and deterministic corrections exactly equal the predecessor oracle.

The reproduced decision-table digests are:

- sum-product: `05dd32573ee965ce96caf707de3541f8be74b49317ad46b7929ef7dcf3bf64fc`;
- soft tropical: `ea2a96e3878758cd2daebd28673d943c27740a3e1c3579d8429a8a658e567393`;
- min-plus: `88a9a766b64c7e476ac5bb4da877a2b1f6d4e88cee88cde6ea7461cc74179f3f`.

The tied-winning-class-set digests are:

- sum-product: `3778c019c7e235d916fa27616f83a9f8251a8c2a0276e09e0ea6dc1a6125cd60`;
- soft tropical: `bf4297273ca05b1506bde6f5305464e5affdf78ba31b40e20a0fada3e26dd982`;
- min-plus: `1991fe00aaec2f8ce1163ca7b4192054002a2ef176d4839d6883c01f4e724007`.

## 8. Frozen-corpus readback

The factorized path reproduces the promoted quotient-aware success totals:

- sum-product: `263/4048`;
- soft tropical: `262/4048`;
- min-plus: `226/4048`.

Tie envelopes remain sum-product `[263,263]`, soft tropical `[262,262]`, and min-plus `[218,263]` with default `226`. The representation change therefore preserves the predecessor's min-plus ambiguity rather than suppressing it.

## 9. Evidence and replay

The immutable reviewed evidence payload is:

`efd9e76957421494897e2cc319137874b61093d66ea871f0202df3d07e6eb3c0`.

The exact-head scientific replay passed `110/110` repository tests, including `13` TCM-QDEC-002 replay/adversarial tests, before Referee disposition. QTR validation, GCL conformance, security/action-policy, and CodeQL were successful on the reviewed head.

## 10. Claim boundary

The bounded promotion admits only the exact finite factorized-equivalence result described above.

It does **not** certify or authorize scalable tensor-network or transfer decoding; bounded contraction width for a qLDPC family; asymptotic complexity improvement; practical runtime or memory advantage; larger-code decoder performance; general qLDPC decoder performance; BP-OSD comparison; circuit-level or phenomenological noise; hardware validation; thresholds or pseudo-thresholds; learned decoder parameters; adaptive contraction-order optimization; `TCM-QDEC-003`; `QLDPC-FORGE`; or autonomous code, decoder, circuit, or architecture search.

## 11. Promotion disposition

The bounded scientific review completed at exact head `9123a9c6cc2c163031d8bff0c46e0a9dd4c8f8fd`. Referee record `5310199674` approved only the finite representation-equivalence substrate described here. The scientific snapshot merged as `d3340c91df3aa72dc5c7ba75906128c8eef2e174`.

Promotion authority is documentary and does not rewrite the registry or evidence that were reviewed. Any later scaling, larger-instance, performance, adaptive-order, or architecture stage requires a separately governed successor.
