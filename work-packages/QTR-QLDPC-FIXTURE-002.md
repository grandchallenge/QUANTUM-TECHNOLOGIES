# QTR-QLDPC-FIXTURE-002 — Frozen-corpus decoder systems benchmark

Status: `referee_promoted_bounded`

Programme: `GCL Quantum Technologies Research (QTR)`

Fixture identifier: `QLDPC-FIXTURE-002`

Predecessor: `QLDPC-FIXTURE-001`

Tracking issue: `#32`

Reviewed scientific head: `e7b2eb0060e51d4157a6666f2e857c1fb19aaff1`

Scientific merge: `51c31bde2e0630314d3d48dceb9b92969c37c228`

Promotion authority: `reviews/QTR-QLDPC-REVIEW-002/promotion-record.json`

The registry and evidence files retain their reviewed
`candidate_executable_not_promoted` status as an immutable scientific snapshot.
The status above records the separate bounded governance disposition.

## 1. Purpose

This work package establishes the first systems-measurement layer above the
promoted finite qLDPC algebra substrate.

The benchmark intentionally stays on the same protected `[[18,4,4]]`
bivariate-bicycle CSS code. Its purpose is to make decoder correctness,
negative evidence, deterministic cost counters, and benchmark provenance
machine-checkable before any broader decoder or architecture programme is
allowed to begin.

It is not a decoder competition and it is not a circuit-level or hardware
reproduction.

## 2. Predecessor binding

The evaluator consumes the immutable Fixture 001 evidence snapshot:

- evidence path: `evidence/QLDPC-FIXTURE-001-report.json`;
- evidence payload:
  `6c2095f48762178bf0fe5c2b5fce8299261733912a1cccc7884d11f344718427`;
- scientific merge:
  `b899894cfe17680d556d32ff36e51683cd9f6b32`;
- promotion pin:
  `ab9a24a08d4e31b4d8cd18edb0ab1e5a7a0b3950`.

Fixture 002 re-verifies the predecessor payload digest and core algebraic
identities before benchmarking. It does not reinterpret the documentary
promotion overlay as new mathematical evidence.

## 3. Frozen corpus

The benchmark corpus is exhaustive rather than sampled.

For one CSS sector it contains every 18-bit error of Hamming weight

\[
0\leq w\leq 4.
\]

The shell sizes are

\[
\binom{18}{0}=1,\quad
\binom{18}{1}=18,\quad
\binom{18}{2}=153,\quad
\binom{18}{3}=816,\quad
\binom{18}{4}=3060,
\]

for a total of `4048` error instances.

No random seed exists because no random sampling is performed. The complete
ordered corpus is represented by a canonical SHA-256 identity in the evidence
report.

Because Fixture 001 has `H_X = H_Z`, the same finite parity-check structure can
be reused for either code-capacity CSS sector. Fixture 002 nevertheless reports
one sector only and does not multiply this finite benchmark into a
circuit-level noise claim.

## 4. Decoder baselines

Two deliberately different baselines are included.

### 4.1 Exact coset-leader lookup

The first baseline reconstructs the exhaustive minimum-weight syndrome table
used in Fixture 001.

It is an exact finite reference object, not a scalable decoder proposal. Its
table digest must remain

`96ce94c378b7b1fc5fe032fbd253aa932c1ca8abcb17b3d3c89b3ecda601da29`.

Every benchmark result is scored by checking the residual error modulo the
certified X-stabilizer span, not by trusting the decoder's own termination
state.

### 4.2 Greedy syndrome descent

The second baseline is intentionally simple.

At each iteration it evaluates all 18 single-qubit flips and chooses the
lowest-index qubit that gives the largest strict reduction in syndrome Hamming
weight. If no strict reduction exists, it stops and retains the nonzero
residual syndrome as negative evidence.

This decoder is included because a systems fixture should be able to preserve
failures, not because the algorithm is expected to be competitive.

## 5. Deterministic systems counters

Committed evidence contains deterministic counters rather than
machine-dependent timing claims.

The report records, among other quantities:

- exact lookup-table setup candidate count;
- syndrome evaluations;
- table lookups;
- greedy iterations;
- greedy candidate comparisons;
- stalled nonzero syndromes;
- iteration histogram;
- canonical serialized byte sizes for the lookup and column-syndrome tables.

These quantities replay exactly on any conforming Python implementation.

An optional `--profile-output` mode may record wall-clock timing together with
the Python and platform identity. Such output is explicitly diagnostic,
non-authoritative, and is not included in the committed evidence payload.

## 6. Source-context record

The registry also binds the companion experimental software as provenance
context only:

- Zenodo DOI `10.5281/zenodo.17706106`;
- archive version `v1.1.3`;
- archive MD5 `95c3421c0301e07266357652f0179d2b`;
- Python `3.10.14`;
- Stim `1.13.0`;
- LDPC `0.1.53`;
- bposd `1.6`;
- leaky `0.2.2`.

The source experiment decoder
`18_4_4/ErrorCorrection_for_experiment_18_4_4.py` is bound to Git tag
`v1.1.3` and blob `df82b3a6aa17b969a50b1b143cc10136cb24547f`. It records
min-sum BP, `max_iter=10000`, `osd_cs`, OSD order `7`, and min-sum scaling
factor `0`.

Fixture 002 does **not** execute that BP-OSD pipeline. The transcription exists
to establish a future compatibility boundary, not to import the source
experiment's decoder performance into GCL authority.

## 7. Evidence and replay

The deterministic report is regenerated with

```bash
python reference/qldpc_fixture_002.py \
  --output evidence/QLDPC-FIXTURE-002-report.json
```

Optional machine-local timing diagnostics may be produced separately:

```bash
python reference/qldpc_fixture_002.py \
  --profile-output /tmp/QLDPC-FIXTURE-002-profile.json
```

The test package verifies exact committed replay and adversarially rejects
changes to the predecessor payload, predecessor claim boundary, corpus
definition, source-context record, or downstream authorization flags.

## 8. Claim boundary

Fixture 002 is promoted only for:

- this frozen finite code-capacity corpus;
- exact correctness scoring against the promoted Fixture 001 algebra;
- the two explicitly named deterministic decoder baselines;
- deterministic systems counters and preserved negative evidence;
- non-authoritative optional local profiling mechanics;
- the tag/blob-bound source BP-OSD configuration as provenance context only.

It does **not** certify or authorize:

- experimental-data reproduction;
- circuit-level or Pauli+ noise-model validation;
- BP-OSD performance or superiority;
- Kunlun hardware validation;
- thresholds or pseudo-thresholds;
- cross-machine latency comparisons;
- practical decoder/resource superiority;
- fault-tolerant logical operations;
- `TCM-QDEC`;
- `QLDPC-FORGE`;
- autonomous code, decoder, circuit, or architecture search.

## 9. Promotion record

The bounded promotion was reviewed at exact scientific head
`e7b2eb0060e51d4157a6666f2e857c1fb19aaff1` and scientifically merged as
`51c31bde2e0630314d3d48dceb9b92969c37c228`.

The immutable reviewed evidence payload remains
`d98c5d73f7fdf9259a35be60580dc9b6c32c5e4483cd765ed0dcba594b9299e5`
and the frozen corpus remains
`260b1a43cf1d777f28c475918e91a5f7cefc5d28a2bfb556338f7e30058f58a8`.

Authority is recorded separately in
`reviews/QTR-QLDPC-REVIEW-002/promotion-record.json`. `TCM-QDEC` and
`QLDPC-FORGE` remain gated.
