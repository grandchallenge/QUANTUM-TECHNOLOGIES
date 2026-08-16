# GCL Quantum Technologies Research

Status: `adopted`

Authority repository: `grandchallenge/QUANTUM-TECHNOLOGIES`

Programme identifier: `QTR`

## Purpose

GCL Quantum Technologies Research develops auditable quantum algorithms, operator encodings, resource estimates, simulations, error-correction substrates, and experimental protocols. The programme separates mathematical validity, algorithmic correctness, resource claims, simulation evidence, and hardware evidence.

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

A second research lane establishes certified qLDPC/QEC substrates before any broader architecture search. Its governed sequence is

`QLDPC-FIXTURE-001 → QLDPC-FIXTURE-002 → TCM-QDEC → QLDPC-FORGE`.

Only the first node is promoted at present; all later nodes remain gated.

## Authority state

- `QTR-CHARTER-00`: adopted.
- `QTR-SIG-WP00`: Referee-promoted finite-domain substrate.
- `QTR-SIG-WP01`: Referee-promoted finite symmetry-quotient atlas.
- `QTR-SIG-WP02`: Referee-promoted finite linearization atlas.
- `QTR-SIG-WP03`: Referee-promoted only for the admitted finite OR certificate pair.
- `QTR-SIG-WP04` and later: gated.
- `QTR-QLDPC-FIXTURE-001`: Referee-promoted only for the exact finite `[[18,4,4]]` replay and its finite code-capacity reference baseline.
- `QLDPC-FIXTURE-002`, `TCM-QDEC`, and `QLDPC-FORGE`: gated.

The signal-lane downstream promotion was reviewed at `c6d3c460804bcc414226cac3700a864773ba2fdf` and merged as `f96452e3eeb1688bf8eb60c7b22e3adf500bae39`. Its exact candidate registry and evidence snapshot remain immutable; authority is recorded in `reviews/QTR-SIG-NEXT-001/promotion-record.json`.

The qLDPC fixture was reviewed at `a024afb5b3428f49c34d905625f8c56f466528e7` and merged as `b899894cfe17680d556d32ff36e51683cd9f6b32`. Its exact registry and evidence snapshot likewise remain immutable; bounded authority is recorded in `reviews/QTR-QLDPC-REVIEW-001/promotion-record.json`.

The adoption and promotion records do not certify a general theorem, prove quantum advantage, validate hardware evidence, establish practical resource superiority, certify a qLDPC threshold, or authorize later qLDPC decoder/search stages.

## Promoted executable signal package

WP01 exhaustively groups Boolean strings by permutation orbits and checks whether the predicate is constant on each orbit. WP02 exposes signed/scalar, singular-value, rank, range, and kernel semantics. Bounded WP03 verifies one explicit four-bit OR adversary matrix and one matching span program.

The package deliberately retains negative evidence. In particular, the signed Hamming scalar separates five-bit majority, while its singular value erases the sign and creates 126 opposite-label input-pair collisions.

## qLDPC/QEC fixture lane

`QLDPC-FIXTURE-001` reconstructs the protected bivariate-bicycle CSS instance from its polynomial parameters and independently verifies `H_X H_Z^T = 0`, ranks `7/7`, `[[n,k,d]]=[[18,4,4]]`, `d_X=d_Z=4`, full-check row weight `6`, data-column weight `3`, and the exact source-transcribed four-pair logical basis. Distance is decided by exhaustive finite enumeration.

The fixture also records an exhaustive minimum-weight coset-leader decoder for one code-capacity CSS sector as a deterministic finite baseline. It is deliberately noncompetitive: no claim is made about BP-OSD superiority, latency, circuit-level noise, thresholds, hardware validity, or real-time fault-tolerant control.

The reviewed registry and evidence files retain `candidate_executable_not_promoted` because they are the immutable scientific snapshot. Promotion authority is a separate documentary overlay. This prevents later governance changes from rewriting the evidence that was actually reviewed.

## Key files

- `QTR-CHARTER-00.md`: adopted programme charter.
- `work-packages/QTR-SIG-WP00.md`: promoted signal-discovery substrate.
- `work-packages/QTR-SIG-WP01.md`: promoted finite symmetry quotient contract.
- `work-packages/QTR-SIG-WP02.md`: promoted finite linearization contract.
- `work-packages/QTR-SIG-WP03.md`: promoted bounded adversary/span-program contract.
- `work-packages/QTR-QLDPC-FIXTURE-001.md`: promoted bounded qLDPC fixture contract.
- `registry/qldpc-fixtures.json`: immutable qLDPC source/candidate snapshot.
- `reference/qldpc_fixture_001.py`: exact dependency-free qLDPC evaluator.
- `evidence/QLDPC-FIXTURE-001-report.json`: immutable exact replay report.
- `reviews/QTR-QLDPC-REVIEW-001/`: qLDPC review-cycle closure and promotion authority records.
- `registry/`: governed candidate and downstream atlas records.
- `schemas/`: fail-closed record schemas.
- `reference/`: dependency-free deterministic evaluators.
- `evidence/`: committed replay reports.
- `reviews/QTR-SIG-NEXT-001/`: signal-lane intake and promotion authority records.
- `tests/`: acceptance, adversarial, and promotion-overlay fixtures.
- `ci/validate.py`: adopted WP00 validation.
- `ci/validate_downstream.py`: promoted WP01–WP03 validation.

## Validation

```bash
python ci/validate.py
python ci/validate_downstream.py
python -m unittest discover -s tests -p "test_*.py" -v
python reference/downstream_atlas.py
python reference/qldpc_fixture_001.py
```

## Foundational sources

- Low and Chuang, *Optimal Hamiltonian Simulation by Quantum Signal Processing*, arXiv:1606.02685.
- Gilyén, Su, Low, and Wiebe, *Quantum Singular Value Transformation and Beyond*, arXiv:1806.01838.
- Lee, Mittal, Reichardt, Špalek, and Szegedy, *Quantum Query Complexity of State Conversion*, arXiv:1011.3020.
- Cornelissen, Jeffery, Ozols, and Piedrafita, *Span Programs and Quantum Time Complexity*, arXiv:2005.01323.
- Wang et al., *Demonstration of low-overhead quantum error correction codes*, arXiv:2505.09684.

These sources motivate or define the bounded programme lanes. They do not discharge theorem-level source comparison, certification, novelty review, hardware validation, or downstream authorization for future claims.
