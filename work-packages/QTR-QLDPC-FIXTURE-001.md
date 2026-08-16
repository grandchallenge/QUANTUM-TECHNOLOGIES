# QTR-QLDPC-FIXTURE-001 — Exact `[[18,4,4]]` bivariate-bicycle replay

Status: `referee_promoted_bounded`

Programme: `GCL Quantum Technologies Research (QTR)`

Fixture identifier: `QLDPC-FIXTURE-001`

Reviewed head: `a024afb5b3428f49c34d905625f8c56f466528e7`

Scientific merge: `b899894cfe17680d556d32ff36e51683cd9f6b32`

Promotion record: `reviews/QTR-QLDPC-REVIEW-001/promotion-record.json`

## 1. Purpose

This work package establishes the first bounded proving ground for the GCL
qLDPC/QEC programme. It reconstructs one finite bivariate-bicycle CSS code from
source-declared polynomial parameters and independently recomputes its exact
finite algebraic invariants.

The fixture exists to establish reproducibility and certification mechanics.
It is not an optimization, decoder competition, hardware reproduction, or
fault-tolerant architecture claim.

The exact registry and evidence files reviewed at the bound head remain an
immutable candidate snapshot. Bounded promotion authority is recorded by a
separate documentary overlay; the reviewed registry and evidence status are not
rewritten in place.

## 2. Protected source input

The fixture transcribes the code construction in Ke Wang et al.,
*Demonstration of low-overhead quantum error correction codes*,
arXiv:2505.09684v1 / Nature Physics (2026), Supplementary theoretical details
I.1.

The source parameters are

\[
l=m=3,
\quad
A=x+y^0+y^2,
\quad
B=y+x^0+x^2,
\]

with

\[
x=S_3\otimes I_3,
\qquad
y=I_3\otimes S_3,
\]

and CSS check matrices

\[
H_X=[A\mid B],
\qquad
H_Z=[B^\top\mid A^\top].
\]

The source declares an `[[18,4,4]]` code and rank seven for each full check
matrix. It also supplies one four-pair logical Pauli basis.

The exact transcribed inputs are stored in `registry/qldpc-fixtures.json`.
They are inputs to replay, not GCL-certified facts. The fixture-specific
evaluator literal-binds the source identity, polynomial parameters, logical
operator transcription, and redundant-check record; unknown record fields are
rejected before report generation.

## 3. Exact replay obligations

`reference/qldpc_fixture_001.py` shall independently reconstruct and check:

1. fail-closed source identity, key-set, polynomial-parameter, logical-basis,
   and redundant-check binding;
2. binary matrix construction from the polynomial parameters;
3. `H_X H_Z^T = 0` over `GF(2)`;
4. exact ranks of `H_X` and `H_Z`;
5. `n = 18` and `k = n-rank(H_X)-rank(H_Z) = 4`;
6. exact CSS distances `d_X` and `d_Z` by exhaustive enumeration;
7. row and column weight distributions;
8. the source logical Pauli basis, including canonical X/Z pairing;
9. a deterministic reference decoder for all reachable code-capacity
   syndromes.

For this 18-qubit fixture, exhaustive enumeration is the authority mechanism.
No stochastic estimate is needed for the algebraic claims above.

## 4. Reference decoder boundary

The decoder is an exhaustive minimum-weight coset-leader decoder for one CSS
sector under a code-capacity model. It exists only as an exact finite baseline.

The fixture must verify correction of every weight-zero and weight-one error,
as guaranteed by distance four. It may record exact finite success counts for
higher weights as diagnostic data.

It creates no claim that this decoder is scalable, fast, competitive with
BP-OSD, suitable for circuit-level noise, or suitable for real-time control.

## 5. Evidence artifact

Running

```bash
python reference/qldpc_fixture_001.py \
  --output evidence/QLDPC-FIXTURE-001-report.json
```

must reproduce the committed report byte-for-byte after JSON normalization.
The report binds the reconstructed matrices, exact invariants, logical basis,
decoder-table digest and entry count, diagnostic counts, claim boundary, and
canonical SHA-256 payload digest.

The unit test `tests/test_qldpc_fixture_001.py` replays the committed evidence
and includes fail-closed mutations of the declared distance, logical basis,
source record, and authority boundary. It also demonstrates that an alternate
algebraically valid canonical logical basis cannot silently replace the exact
source transcription.

The separate test `tests/test_qldpc_fixture_001_promotion.py` checks that the
promotion overlay remains bound to the reviewed head, scientific merge,
workflow evidence, office records, immutable candidate snapshot, and downstream
exclusions.

## 6. Claim boundary

This work package authorizes only exact finite code-algebra replay for
`QLDPC-FIXTURE-001` and the bounded finite code-capacity reference baseline
recorded in the reviewed evidence.

It does **not** certify or authorize:

- the Kunlun hardware experiment;
- the source circuit-level noise model;
- BP-OSD performance;
- a qLDPC threshold;
- break-even or practical advantage;
- syndrome-extraction fault tolerance;
- a universal logical gate set;
- `TCM-QDEC`;
- `QLDPC-FIXTURE-002`;
- `QLDPC-FORGE`;
- autonomous code, decoder, circuit, or architecture search.

All such claims remain gated.

## 7. Promotion record

The candidate package was reviewed at
`a024afb5b3428f49c34d905625f8c56f466528e7` after the revision-1
source-lock defect was repaired and replayed at a fresh exact head. Required
QTR and GCL workflows were green, the revised adversarial boundary was accepted,
and the Referee recorded the bounded disposition
`APPROVE_BOUNDED_SCIENTIFIC_MERGE__QLDPC_FIXTURE_001_R2`.

The reviewed scientific package merged as
`b899894cfe17680d556d32ff36e51683cd9f6b32`. The machine-readable promotion
overlay is `reviews/QTR-QLDPC-REVIEW-001/promotion-record.json`.

Promotion does not alter `registry/qldpc-fixtures.json` or
`evidence/QLDPC-FIXTURE-001-report.json`: both retain the exact candidate state
and payload reviewed by the offices. Any future scientific extension requires a
new governed fixture or work package.
