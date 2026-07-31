# QTR-SIG-WP03 — Finite Adversary and Span-Program Extraction

Status: `candidate`

Parent: `QTR-SIG-WP00` (`referee_promoted`)

Issues: `#9`

Scope: `finite_instance_only`

## 1. Objective

Extract one explicit finite adversary certificate and one matching span program from the governed OR quotient and marked-row linearization.

## 2. First admitted certificate

For four-bit OR:

- the adversary matrix is the unweighted star between `0000` and the four Hamming-weight-one inputs;
- its spectral norm is `sqrt(4)=2`;
- filtering by any input coordinate leaves one edge of norm `1`;
- the executable adversary objective is therefore `2`;
- the span program has target `1` in a one-dimensional vector space and one unit input vector per bit;
- its worst positive witness size is `1`;
- its zero-input negative witness size is `4`;
- its witness-size complexity is `sqrt(1*4)=2`.

The evaluator verifies these finite objects and their matching objective values.

## 3. Gates

- `WP03-G0 Interface lock`: source WP01 and WP02 record identities are explicit.
- `WP03-G1 Adversary support`: nonzero matrix entries connect opposite labels only.
- `WP03-G2 Filter replay`: every per-coordinate filtered norm is reproduced.
- `WP03-G3 Span replay`: target, availability, and witness sizes are reproduced.
- `WP03-G4 Equality check`: the two finite certificate objectives agree.
- `WP03-G5 Review`: exact-head role review and Referee disposition.

## 4. Claim boundary

This package does not solve a general adversary SDP, prove asymptotic optimality, compile a quantum circuit, establish time efficiency, construct a QSP/QSVT implementation, or prove quantum advantage. WP04 remains gated.

## 5. Sources

- `arXiv:1011.3020` for the general adversary characterization of quantum query complexity.
- `arXiv:2005.01323` for the constructive span-program and quantum-computation relationship.
