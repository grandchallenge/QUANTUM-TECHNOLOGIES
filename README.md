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

A second research lane establishes certified qLDPC/QEC substrates before any broader architecture search. Its governed sequence is now

`QLDPC-FIXTURE-001 → QLDPC-FIXTURE-002 → TCM-QDEC-001 → TCM-QDEC-002 → QLDPC-FORGE`.

The first two qLDPC fixtures and the first bounded TCM-QDEC semantic experiment are Referee-promoted. `TCM-QDEC-002` and `QLDPC-FORGE` remain gated.

## Authority state

- `QTR-CHARTER-00`: adopted.
- `QTR-SIG-WP00`: Referee-promoted finite-domain substrate.
- `QTR-SIG-WP01`: Referee-promoted finite symmetry-quotient atlas.
- `QTR-SIG-WP02`: Referee-promoted finite linearization atlas.
- `QTR-SIG-WP03`: Referee-promoted only for the admitted finite OR certificate pair.
- `QTR-SIG-WP04` and later: gated.
- `QTR-QLDPC-FIXTURE-001`: Referee-promoted only for the exact finite `[[18,4,4]]` replay and its finite code-capacity reference baseline.
- `QTR-QLDPC-FIXTURE-002`: Referee-promoted only for the frozen one-sector weight-`0..4` corpus, two named deterministic baselines, exact correctness scoring, deterministic counters, and retained negative evidence.
- `QTR-TCM-QDEC-001`: Referee-promoted only for the exact finite representative-versus-stabilizer-coset semiring audit on the protected Fixture 002 substrate.
- `TCM-QDEC-002` and `QLDPC-FORGE`: gated.

The signal-lane downstream promotion was reviewed at `c6d3c460804bcc414226cac3700a864773ba2fdf` and merged as `f96452e3eeb1688bf8eb60c7b22e3adf500bae39`. Its exact candidate registry and evidence snapshot remain immutable; authority is recorded in `reviews/QTR-SIG-NEXT-001/promotion-record.json`.

The first qLDPC fixture was reviewed at `a024afb5b3428f49c34d905625f8c56f466528e7` and merged as `b899894cfe17680d556d32ff36e51683cd9f6b32`. Its exact registry and evidence snapshot likewise remain immutable; bounded authority is recorded in `reviews/QTR-QLDPC-REVIEW-001/promotion-record.json`.

The second qLDPC fixture was reviewed at `e7b2eb0060e51d4157a6666f2e857c1fb19aaff1` and scientifically merged as `51c31bde2e0630314d3d48dceb9b92969c37c228`. Its exact benchmark registry and evidence snapshot remain immutable; bounded authority is recorded in `reviews/QTR-QLDPC-REVIEW-002/promotion-record.json`.

`TCM-QDEC-001` was reviewed at `cba814e5e5fb6db8fba7a8afd8211189a477eecb` and scientifically merged as `41524f805dce4f0c7b64b8e743b75a60b4f76773`. Its exact experiment registry and evidence snapshot remain immutable; bounded authority is recorded in `reviews/QTR-TCM-QDEC-REVIEW-001/promotion-record.json`.

The adoption and promotion records do not certify a general theorem, prove quantum advantage, validate hardware evidence, establish practical resource superiority, certify a qLDPC threshold, or authorize later qLDPC decoder/search stages.

## Promoted executable signal package

WP01 exhaustively groups Boolean strings by permutation orbits and checks whether the predicate is constant on each orbit. WP02 exposes signed/scalar, singular-value, rank, range, and kernel semantics. Bounded WP03 verifies one explicit four-bit OR adversary matrix and one matching span program.

The package deliberately retains negative evidence. In particular, the signed Hamming scalar separates five-bit majority, while its singular value erases the sign and creates 126 opposite-label input-pair collisions.

## qLDPC/QEC fixture lane

`QLDPC-FIXTURE-001` reconstructs the protected bivariate-bicycle CSS instance from its polynomial parameters and independently verifies `H_X H_Z^T = 0`, ranks `7/7`, `[[n,k,d]]=[[18,4,4]]`, `d_X=d_Z=4`, full-check row weight `6`, data-column weight `3`, and the exact source-transcribed four-pair logical basis. Distance is decided by exhaustive finite enumeration.

Fixture 001 also records an exhaustive minimum-weight coset-leader decoder for one code-capacity CSS sector as a deterministic finite baseline. It is deliberately noncompetitive: no claim is made about BP-OSD superiority, latency, circuit-level noise, thresholds, hardware validity, or real-time fault-tolerant control.

`QLDPC-FIXTURE-002` freezes all one-sector 18-bit errors of weights `0..4` (`4048` cases) and scores two deterministic baselines against Fixture 001's exact stabilizer semantics. The exact lookup reproduces the Fixture 001 finite decoder results; a deliberately simple greedy syndrome-descent baseline retains its failures and explicit witnesses. Deterministic operation counts and canonical serialization sizes are promoted as replayable fixture evidence, while wall-clock profiling remains machine-local and non-authoritative.

The companion experimental BP-OSD configuration is recorded only as tag/blob-bound provenance context. Fixture 002 does not execute experimental-data reproduction, Pauli+ simulation, or BP-OSD benchmarking, and it creates no threshold, hardware, or practical decoder-performance claim.

`TCM-QDEC-001` keeps the protected Fixture 002 code and `4048`-case scoring corpus fixed while exhaustively enumerating all `2^18` one-sector physical error representatives. For each syndrome it compares coordinatewise representative-space inference with aggregation over the `16` certified stabilizer-equivalence logical classes under three exact integer reductions: a BSC `p=0.1` sum-product numerator, a fixed base-2 soft-tropical partition score, and min-plus Hamming weight.

On the frozen corpus, representative-naive success counts are `37`, `1`, and `37`, while stabilizer-coset aggregation gives `263`, `262`, and default `226`. The result is a finite mechanism statement, not a practical-decoder leaderboard. In particular, sum-product's net `+23` relative to Fixture 002's exact minimum-weight lookup decomposes into `131` repaired exact-lookup failures and `108` broken exact-lookup successes. The min-plus aggregate is materially tie-sensitive, with success-count envelope `[218,263]`; that ambiguity is retained as promoted evidence.

The reviewed registry and evidence files for all three qLDPC/QEC stages retain `candidate_executable_not_promoted` because they are immutable scientific snapshots. Promotion authority is recorded in separate documentary overlays. This prevents later governance changes from rewriting the evidence that was actually reviewed.

## Key files

- `QTR-CHARTER-00.md`: adopted programme charter.
- `work-packages/QTR-SIG-WP00.md`: promoted signal-discovery substrate.
- `work-packages/QTR-SIG-WP01.md`: promoted finite symmetry quotient contract.
- `work-packages/QTR-SIG-WP02.md`: promoted finite linearization contract.
- `work-packages/QTR-SIG-WP03.md`: promoted bounded adversary/span-program contract.
- `work-packages/QTR-QLDPC-FIXTURE-001.md`: promoted bounded qLDPC algebra fixture contract.
- `work-packages/QTR-QLDPC-FIXTURE-002.md`: promoted bounded qLDPC systems-benchmark fixture contract.
- `work-packages/QTR-TCM-QDEC-001.md`: promoted bounded finite degeneracy-aware semiring audit.
- `registry/qldpc-fixtures.json`: immutable Fixture 001 source/candidate snapshot.
- `registry/qldpc-benchmarks.json`: immutable Fixture 002 benchmark candidate snapshot.
- `registry/tcm-qdec.json`: immutable TCM-QDEC-001 experiment candidate snapshot.
- `reference/qldpc_fixture_001.py`: exact dependency-free Fixture 001 evaluator.
- `reference/qldpc_fixture_002.py`: deterministic dependency-free Fixture 002 evaluator.
- `reference/tcm_qdec_001.py`: exact dependency-free TCM-QDEC-001 finite evaluator.
- `evidence/QLDPC-FIXTURE-001-report.json`: immutable Fixture 001 exact replay report.
- `evidence/QLDPC-FIXTURE-002-report.json`: immutable Fixture 002 exact benchmark report.
- `evidence/TCM-QDEC-001-report.json`: immutable TCM-QDEC-001 exact finite report.
- `reviews/QTR-QLDPC-REVIEW-001/`: Fixture 001 review-cycle closure and promotion authority records.
- `reviews/QTR-QLDPC-REVIEW-002/`: Fixture 002 review-cycle closure and promotion authority records.
- `reviews/QTR-TCM-QDEC-REVIEW-001/`: TCM-QDEC-001 review-cycle closure and promotion authority records.
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
python reference/qldpc_fixture_002.py
python reference/tcm_qdec_001.py
```

## Foundational sources

- Low and Chuang, *Optimal Hamiltonian Simulation by Quantum Signal Processing*, arXiv:1606.02685.
- Gilyén, Su, Low, and Wiebe, *Quantum Singular Value Transformation and Beyond*, arXiv:1806.01838.
- Lee, Mittal, Reichardt, Špalek, and Szegedy, *Quantum Query Complexity of State Conversion*, arXiv:1011.3020.
- Cornelissen, Jeffery, Ozols, and Piedrafita, *Span Programs and Quantum Time Complexity*, arXiv:2005.01323.
- Wang et al., *Demonstration of low-overhead quantum error correction codes*, arXiv:2505.09684.

These sources motivate or define the bounded programme lanes. They do not discharge theorem-level source comparison, certification, novelty review, hardware validation, or downstream authorization for future claims.
