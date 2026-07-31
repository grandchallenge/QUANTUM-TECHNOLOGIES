# GCL Quantum Technologies Research

Status: `adopted`

Authority repository: `grandchallenge/QUANTUM-TECHNOLOGIES`

Programme identifier: `QTR`

## Purpose

GCL Quantum Technologies Research develops auditable quantum algorithms, operator encodings, resource estimates, simulations, and experimental protocols. The programme separates mathematical validity, algorithmic correctness, resource claims, simulation evidence, and hardware evidence.

The first research lane studies the governed chain

\[
\text{Boolean predicate}
\rightarrow
\text{coherently accessible signal}
\rightarrow
\text{polynomial separator}
\rightarrow
\text{QSP synthesis}
\rightarrow
\text{QSVT execution}.
\]

A smaller signal is useful only when semantic sufficiency, access cost, spectral separation, polynomial degree, and end-to-end resources are all controlled.

## Authority state

- `QTR-CHARTER-00`: adopted.
- `QTR-SIG-WP00`: Referee-promoted finite-domain substrate.
- `QTR-SIG-WP01`: Referee-promoted finite symmetry-quotient atlas.
- `QTR-SIG-WP02`: Referee-promoted finite linearization atlas.
- `QTR-SIG-WP03`: Referee-promoted only for the admitted finite OR certificate pair.
- `QTR-SIG-WP04` and later: gated.

The downstream promotion was reviewed at `c6d3c460804bcc414226cac3700a864773ba2fdf` and merged as `f96452e3eeb1688bf8eb60c7b22e3adf500bae39`. The exact candidate registry and evidence snapshot remain immutable; authority is recorded in `reviews/QTR-SIG-NEXT-001/promotion-record.json`.

The adoption and promotion records do not certify a general theorem, establish a new quantum algorithm, prove quantum advantage, validate a physical block encoding, establish practical resource superiority, or validate hardware evidence.

## Promoted executable package

WP01 exhaustively groups Boolean strings by permutation orbits and checks whether the predicate is constant on each orbit. WP02 exposes signed/scalar, singular-value, rank, range, and kernel semantics. Bounded WP03 verifies one explicit four-bit OR adversary matrix and one matching span program.

The package deliberately retains negative evidence. In particular, the signed Hamming scalar separates five-bit majority, while its singular value erases the sign and creates 126 opposite-label input-pair collisions.

## Key files

- `QTR-CHARTER-00.md`: adopted programme charter.
- `work-packages/QTR-SIG-WP00.md`: promoted signal-discovery substrate.
- `work-packages/QTR-SIG-WP01.md`: promoted finite symmetry quotient contract.
- `work-packages/QTR-SIG-WP02.md`: promoted finite linearization contract.
- `work-packages/QTR-SIG-WP03.md`: promoted bounded adversary/span-program contract.
- `registry/`: governed candidate and downstream atlas records.
- `schemas/`: fail-closed record schemas.
- `reference/`: dependency-free deterministic evaluators.
- `evidence/`: committed replay reports.
- `reviews/QTR-SIG-NEXT-001/`: intake and promotion authority records.
- `tests/`: acceptance and adversarial fixtures.
- `ci/validate.py`: adopted WP00 validation.
- `ci/validate_downstream.py`: promoted WP01–WP03 validation.

## Validation

```bash
python ci/validate.py
python ci/validate_downstream.py
python -m unittest discover -s tests -p "test_*.py" -v
python reference/downstream_atlas.py
```

## Foundational sources

- Low and Chuang, *Optimal Hamiltonian Simulation by Quantum Signal Processing*, arXiv:1606.02685.
- Gilyén, Su, Low, and Wiebe, *Quantum Singular Value Transformation and Beyond*, arXiv:1806.01838.
- Lee, Mittal, Reichardt, Špalek, and Szegedy, *Quantum Query Complexity of State Conversion*, arXiv:1011.3020.
- Cornelissen, Jeffery, Ozols, and Piedrafita, *Span Programs and Quantum Time Complexity*, arXiv:2005.01323.

These sources motivate the programme lanes. They do not discharge theorem-level source comparison, certification, or novelty review for future claims.
