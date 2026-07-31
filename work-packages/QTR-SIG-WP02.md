# QTR-SIG-WP02 — Witness, Range, Kernel, and Singular-Value Linearization Atlas

Status: `referee_promoted`

Reviewed head: `c6d3c460804bcc414226cac3700a864773ba2fdf`

Promotion merge: `f96452e3eeb1688bf8eb60c7b22e3adf500bae39`

Referee record: `QTR-SIG-NEXT-001 issue #11 comment 5141826042`

Parent: `QTR-SIG-WP00` (`referee_promoted`)

Issue: `#8`

## 1. Objective

Build finite operator-valued linearizations from governed invariant records. Report what is retained by the signed operator, its range and kernel, and its singular values.

## 2. Contract

Each record shall declare:

- its source WP01 invariant record;
- the operator shape and construction formula;
- signed values and singular values on every orbit;
- rank, range dimension, and kernel dimension;
- cross-label collisions in the signed channel;
- cross-label collisions after singular-value projection;
- whether each channel is semantically sufficient on the finite domain.

Information erased by absolute singular values must be recorded as negative evidence.

## 3. Initial fixtures

- a normalized marked row for OR;
- a signed Hamming scalar for majority;
- a signed Hamming scalar for parity;
- a centered-weight scalar for exact-weight-two.

The majority fixture is an explicit sign-loss control: the signed scalar separates the classes, but the singular value identifies opposite-label orbits.

## 4. Gates

- `WP02-G0 Source lock`: every construction references an admitted WP01 record.
- `WP02-G1 Operator replay`: dimensions, values, ranks, ranges, and kernels replay exactly.
- `WP02-G2 Channel comparison`: signed and singular-value collision ledgers are emitted separately.
- `WP02-G3 Negative retention`: sign-loss and other semantic failures fail closed and remain in evidence.
- `WP02-G4 Review`: exact-head role review and Referee disposition.

## 5. Claim boundary

The classical finite matrix formula is not a physical block encoding. The package does not provide a unitary dilation, state-preparation circuit, QSVT phase sequence, complexity theorem, or advantage claim.

## 6. Sources

The singular-value transformation context is `arXiv:1806.01838`. This package does not claim to implement that construction.
