# QTR-SIG-WP01 — Symmetry Quotient and Invariant-Coordinate Atlas

Status: `referee_promoted`

Reviewed head: `c6d3c460804bcc414226cac3700a864773ba2fdf`

Promotion merge: `f96452e3eeb1688bf8eb60c7b22e3adf500bae39`

Referee record: `QTR-SIG-NEXT-001 issue #11 comment 5141826042`

Parent: `QTR-SIG-WP00` (`referee_promoted`)

Issue: `#7`

## 1. Objective

Build an executable atlas of finite symmetry quotients for signal discovery. The first governed action is the coordinate-permutation action of the symmetric group `S_n` on Boolean strings. The first admitted invariant coordinate is Hamming weight.

## 2. Contract

For each record, the package shall declare:

- the predicate and promise domain;
- the acting group;
- the invariant coordinates;
- the orbit partition;
- the label set on every orbit;
- whether the predicate is constant on each orbit;
- the number of label boundaries in ordered invariant coordinates;
- source-candidate and replay identities.

A quotient is semantically sufficient on the finite domain only when every orbit contains one label.

## 3. Initial fixtures

- four-bit OR;
- five-bit majority;
- four-bit parity;
- four-bit exact-weight-two.

These fixtures distinguish monotone one-boundary profiles from oscillatory and isolated-orbit profiles.

## 4. Gates

- `WP01-G0 Action lock`: the group action and domain are explicit.
- `WP01-G1 Orbit replay`: exhaustive enumeration reproduces every orbit size.
- `WP01-G2 Label constancy`: every admitted quotient is checked for cross-label orbit collisions.
- `WP01-G3 Boundary report`: ordered quotient labels and boundary counts are emitted.
- `WP01-G4 Review`: exact-head role review and Referee disposition.

## 5. Claim boundary

Finite orbit compression does not establish coherent accessibility, low polynomial degree, query advantage, time advantage, practical resources, or hardware relevance. Hamming weight is admitted as an invariant coordinate, not as a free input primitive.

## 6. Sources

The package uses standard permutation-orbit and finite enumeration facts. QSP/QSVT motivation is bounded by `arXiv:1806.01838`. No external theorem is promoted by this work package.
