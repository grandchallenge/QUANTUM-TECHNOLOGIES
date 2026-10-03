# QTR-PUBLICATION-SPEC-001

Status: `MANUSCRIPT_SPECIFICATION__REFERENCE_THEOREM_PROVED__INDEPENDENT_REVIEW_PENDING`

Working title:

**Compiled Exact Degenerate Inference for Bivariate-Bicycle Quantum LDPC Codes**

Programme: `GCL Quantum Technologies Research (QTR)`

## 1. Scientific objective

Extract one paper from the QTR TCM sequence that is about an exact inference architecture, not about programme governance and not about a decoder leaderboard.

The central question is:

> Can stabilizer-degenerate logical-class inference for a CSS code be compiled into a reusable selector-parametric exact object, such that later syndrome/logical queries reproduce the exact fixed-selector inference semantics without re-running structural elimination?

The paper should make a narrow contribution that remains valid even where the underlying ingredients—degenerate maximum-likelihood decoding, graphical-model inference, variable elimination and knowledge compilation—are prior art.

## 2. Central thesis

For the protected one-sector BB-code constructions considered by QTR, write an error representative in affine form

\[
e(a,z)=L a\oplus S z,
\]

where (a) carries syndrome/logical selector coordinates and (z) carries stabilizer degeneracy.

Holding (a) symbolic while exactly eliminating (z) yields a reusable canonical expression DAG. Instantiating (a) later evaluates the same exact class objective as fixed-selector variable elimination.

The paper's contribution is the QEC-specific construction, exact semantic object and verification chain—not the generic idea of arithmetic-circuit compilation.

## 3. Proposed contributions

### C1 — Exact selector/stabilizer factorization

Give a mathematical construction of the selector basis and stabilizer-degeneracy basis for the frozen CSS sector.

State exactly which functionals form (a), how the inverse selector map is built, and why every admitted syndrome/logical class has a valid affine seed.

### C2 — Selector-parametric exact compilation

Describe symbolic variable elimination with selector coordinates retained as parameters.

The compiled object must be defined independently of the implementation as a finite DAG over:

- exact terminals;
- selector-conditioned choice nodes;
- exact semiring operations;
- canonical hash-consing / structural identity.

Explain that the compiled object contains no complete selector answer table.

### C3 — Exact semantics across three algebras

Use the existing QTR algebras as semantic stress tests:

- `sum_product_bsc_p_0_1`;
- `soft_tropical_base_2`;
- `min_plus_hamming` with the product payload required for representative and canonical-key recovery.

Do not claim that multi-semiring evaluation is novel in general. Use it to show that the same structural construction preserves several distinct exact decoding objectives and tie semantics.

### C4 — Complete C18 equivalence chain

Use C18 as the exhaustive proof-of-implementation fixture.

Present the sequence:

1. exhaustive physical-representative oracle;
2. exact quotient semantics;
3. local parity transfer representation;
4. seven-variable stabilizer-degeneracy factor graph;
5. selector-parametric compiled DAG.

The acceptance criterion is preservation of the complete semantic object, not merely equal final success totals.

Report:

- all 6144 class-score entries;
- all 2048 representative/canonical-class mapping entries;
- all 384 tied-winning-class sets;
- all 384 deterministic decisions;
- finite corpus totals and the retained min-plus tie envelope.

### C5 — Larger-code case study without priority over exact C72 ML decoding

Use C72 as the larger structural case.

Report the protected QTR facts:

- 30 stabilizer variables;
- selector rank 42;
- deterministic min-fill width 18 for the QTR graph;
- peak table \(2^{19}\);
- reusable descriptor identity;
- exact equality on the frozen 300-selector independent-oracle validation set.

Do not claim first exact C72 decoding. Krishnamoorthy et al. (2026) independently report exact degenerate ML decoding of the `[[72,12,6]]` BB code using a different coset-MRF/elimination-cluster construction.

### C6 — Controlled comparison with the closest 2026 construction

Add a dedicated section comparing:

- variable definitions;
- logical-class representation;
- treatment of hard parity constraints;
- graph/factor definitions;
- elimination semantics;
- whether selector/logical coordinates are retained symbolically;
- exact versus approximate modes;
- certification mechanism;
- intended online/offline split.

Do not compare induced widths numerically until both are recomputed under a common graph definition or explicitly labelled representation-specific.

## 4. Mathematical theorem package

The reference-level proof package is now recorded in `QTR-THEOREM-SELECTOR-PARAMETRIC-COMPILATION-001.md`. The manuscript must incorporate and independently review the following theorem chain before submission.

### Theorem 1 — selector-coordinate correctness

Given the chosen independent syndrome rows and logical functionals, the selector map has full rank on the protected selector basis and maps the generated seed to the requested syndrome/logical functional.

Required result:

\[
\Phi(L a)=a
\]

in the declared coordinate system, with stabilizer additions lying in the kernel of the selector functionals appropriate to the class.

### Theorem 2 — class partition/function equivalence

For each selector \(a\), the physical representatives in the corresponding logical class are exactly

\[
\{L a\oplus S z:z\in\mathbb F_2^r\}.
\]

Therefore the class score is the declared semiring contraction over \(z\).

For sum-product this is the exact class likelihood numerator under the frozen BSC.

### Theorem 3 — variable-elimination correctness

Exact elimination of the stabilizer variables under any fixed valid elimination order preserves the class contraction.

This can use the standard distributive-law proof, but the paper must state it in the QTR notation.

### Theorem 4 — symbolic-compilation correctness

Let \(D\) be the symbolic DAG produced by the same elimination sequence while retaining selector variables.

For every selector assignment \(a\),

\[
\operatorname{Eval}(D,a)
=
\operatorname{VE}(a).
\]

Prove this by induction over elimination/compiled-expression construction.

This is the central manuscript theorem. A complete reference proof is now present; independent mathematical review and implementation-correspondence review remain required.

### Theorem 5 — min-plus product semantics

Prove that the product payload used by QTR yields:

- minimum Hamming weight;
- deterministic minimum-weight representative under the frozen integer order;
- canonical class key under the declared canonical ordering.

The proof must account for ties explicitly.

### Corollary — decoder decision preservation

If all class records agree, the frozen class-selection/tie-breaking function produces identical tied winner sets and deterministic corrections.

## 5. Experiments and evidence

### E1 — C18 exhaustive semantic equivalence

Use existing promoted exact evidence. Re-run from exact protected identities for paper artifact generation.

Primary figure: five-column representation ladder showing what is materialized/eliminated at each stage.

Primary table: semantic equivalence counts and representation sizes.

### E2 — C18 compilation amortization

Report the protected common-ledger AOP counts:

- compilation: 10,160;
- all-selector evaluation: 12,694,528;
- complete compiled one-shot: 12,704,688;
- classwise replay: 14,115,840.

State prominently that AOPs are not wall-clock operations.

Optional new experiment: machine-local runtime profile as secondary engineering evidence only.

### E3 — C72 structural case

Reproduce:

- source reconstruction;
- primary order and width;
- resource envelope;
- compiled descriptor;
- frozen 300-selector oracle equality.

If feasible, add an independent implementation of the symbolic-compilation theorem test over a substantially larger random selector set. This strengthens implementation confidence but does not replace the proof.

### E4 — direct comparison experiment with coset-MRF construction

Implement or reconstruct the C72 coset-MRF factor graph of Krishnamoorthy et al. from the published definition.

On the same source code instance, compare:

- number/type of latent variables;
- initial factor arities;
- primary min-fill ordering under one common implementation;
- resulting induced widths;
- exact class-score equality for a small shared selector set.

This experiment is not required to prove QTR correctness, but is highly valuable for establishing what is genuinely different.

### E5 — optional C90 stress case

Include only if authoritative external C90 execution completes before manuscript freeze.

Do not make the method paper dependent on C90.

## 6. Figures

1. **Semantic object diagram:** syndrome + logical selector → affine seed → stabilizer-degeneracy factor graph → class score.
2. **Representation ladder:** exhaustive representatives → transfer state → degeneracy variables → selector-parametric DAG.
3. **Compile/evaluate split:** structural compilation offline, selector assignment online.
4. **C18 factor graph:** seven stabilizer variables and local qubit factors; mark width-4 elimination order.
5. **C18 compiled DAG:** representative reduced example, not the full unreadable graph.
6. **C72 structural comparison:** QTR graph versus coset-MRF graph with a warning that graph-dependent width values are not directly comparable.
7. Optional: finite ladder context panel, explicitly not a scaling fit.

## 7. Tables

1. Prior-art positioning table.
2. C18 semantic-equivalence identities.
3. C18 representation/resource comparison.
4. C72 source/structure/validation data.
5. QTR versus Krishnamoorthy et al. construction comparison.
6. Claim-boundary table: what the paper proves and does not prove.

## 8. Manuscript architecture

### Abstract

State:

- problem: degeneracy-aware qLDPC inference requires class sums;
- method: exact selector-parametric compilation;
- C18: complete equivalence across the representation chain;
- C72: larger exact compiled case with independent frozen validation;
- contribution: reusable exact QEC inference representation, not a general decoder-speed claim.

Do not say “first exact qLDPC decoder”.

### 1. Introduction

Motivate the distinction between repeated inference and structural compilation.

Position tensor-network decoding, BP+OSD, certified qLDPC inference and knowledge compilation.

End with explicit contributions C1–C6.

### 2. Degenerate CSS decoding

Define syndrome classes, stabilizer equivalence, logical classes and exact class probability.

### 3. Affine selector–degeneracy parametrization

State Theorems 1–2.

### 4. Exact factorization and variable elimination

State Theorem 3.

### 5. Selector-parametric compilation

State Theorem 4 and canonical DAG construction.

### 6. Exact decision semantics and ties

State Theorem 5 and decision corollary.

### 7. C18 complete equivalence study

Use promoted evidence.

### 8. C72 case study

Use the exact protected C72 package and validation.

### 9. Relation to coset-MRF and knowledge compilation

This section is mandatory. It prevents overclaiming and clarifies the actual contribution.

### 10. Limits and open directions

No family-scaling theorem, runtime-superiority theorem, or circuit-level C72/C90 result.

### 11. Reproducibility

List protected commits, evidence payloads, executable routes and public artifact package.

## 9. Required related work

At minimum cite:

- Ferris & Poulin (2014);
- Bravyi, Suchara & Vargo (2014);
- Chubb (2021);
- Piveteau, Chubb & Renes (2024);
- Roffe et al. (2020);
- Panteleev & Kalachev (2021);
- Bravyi et al. (2024);
- Krishnamoorthy et al. (2026), arXiv:2608.25545;
- Chavira & Darwiche (2007);
- Darwiche (2003);
- Kimmig, Van den Broeck & De Raedt (2017).

## 10. Publication gate

The manuscript may move from specification to submission candidate only when:

- Theorems 1–5 have complete proofs;
- a fresh exact-head replay reproduces the C18 and C72 evidence used in the manuscript;
- the C72 comparison with the 2026 coset-MRF work is technically explicit;
- every “novel” or “first” sentence has an attached prior-art audit entry;
- the public reproduction package contains no governance-dependent private state;
- the paper distinguishes formal exactness, implementation validation, AOP accounting and wall-clock performance.

## 11. Current disposition

`READY_FOR_THEOREM_AND_MANUSCRIPT_DEVELOPMENT`

The next substantive paper task is to write and verify Theorem 4, the selector-parametric compilation correctness theorem. Everything else in Paper A should be organized around that result.
