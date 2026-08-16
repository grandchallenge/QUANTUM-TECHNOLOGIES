# QTR-QLDPC-FIXTURE-001 — Exact `[[18,4,4]]` bivariate-bicycle replay

Status: `candidate_executable_not_promoted`

Programme: `GCL Quantum Technologies Research (QTR)`

Fixture identifier: `QLDPC-FIXTURE-001`

## 1. Purpose

This work package establishes the first bounded proving ground for the GCL
qLDPC/QEC programme. It reconstructs one finite bivariate-bicycle CSS code from
source-declared polynomial parameters and independently recomputes its exact
finite algebraic invariants.

The fixture exists to establish reproducibility and certification mechanics.
It is not an optimization, decoder competition, hardware reproduction, or
fault-tolerant architecture claim.

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
They are inputs to replay, not GCL-certified facts.

## 3. Exact replay obligations

`reference/qldpc_fixture_001.py` shall independently reconstruct and check:

1. binary matrix construction from the polynomial parameters;
2. `H_X H_Z^T = 0` over `GF(2)`;
3. exact ranks of `H_X` and `H_Z`;
4. `n = 18` and `k = n-rank(H_X)-rank(H_Z) = 4`;
5. exact CSS distances `d_X` and `d_Z` by exhaustive enumeration;
6. row and column weight distributions;
7. the source logical Pauli basis, including canonical X/Z pairing;
8. a deterministic reference decoder for all reachable code-capacity
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
and authority boundary.

## 6. Claim boundary

This work package authorizes only exact finite code-algebra replay for
`QLDPC-FIXTURE-001`.

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

## 7. Promotion condition

This package may advance beyond `candidate_executable_not_promoted` only after:

1. exact replay is green on the protected head;
2. committed evidence matches deterministic regeneration;
3. adversarial mutation tests are green;
4. source transcription is independently reviewed;
5. the Referee records a bounded disposition.

Until then, the fixture is executable evidence with no promoted scientific
authority.
