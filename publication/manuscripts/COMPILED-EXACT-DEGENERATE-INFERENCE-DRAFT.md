# Compiled Exact Degenerate Inference for Bivariate-Bicycle Quantum LDPC Codes

**Draft manuscript — QTR Paper A**

Status: `DRAFT__REFERENCE_THEOREM_PROVED__INDEPENDENT_REVIEW_PENDING`

Authors: Grand Challenge Labs Quantum Technologies Research contributors  
Correspondence: to be assigned before submission

## Abstract

Maximum-likelihood decoding of a stabilizer quantum code is naturally a problem of inference over logical equivalence classes rather than individual physical errors. Exact evaluation is difficult because each logical class contains many stabilizer-equivalent representatives, and a direct decoder may repeat nearly the same structural computation for many syndrome and logical-class queries. We study an exact compilation architecture for one-sector decoding of bivariate-bicycle CSS codes. We write each representative as

\[
e(a,z)=L a\oplus S z,
\]

where \(a\) contains independent syndrome and logical-class selector coordinates and \(z\) contains stabilizer-degeneracy variables. We eliminate \(z\) symbolically while retaining \(a\) as Boolean parameters, producing a canonical reusable expression DAG. We prove that specialization of the compiled DAG at any selector assignment equals fixed-selector exact variable elimination. The construction applies to exact sum-product, a base-2 partition objective, and a min-plus product algebra that simultaneously retains minimum weight, a deterministic minimum-weight representative, and a canonical class key.

On a protected \([[18,4,4]]\) bivariate-bicycle code, we verify the complete semantic chain from exhaustive physical-error enumeration through quotient inference, local transfer factorization, stabilizer-variable elimination, and selector-parametric compilation. The compiled path reproduces all 6,144 class scores, 2,048 class mappings, 384 winning-class tie sets, and 384 deterministic decisions. The three compiled algebra objects contain 371, 371, and 388 reachable nodes respectively. On a source-bound \([[72,12,6]]\) bivariate-bicycle instance, the corresponding exact representation has 30 stabilizer variables and selector rank 42; deterministic min-fill has induced width 18, and the reusable compiled descriptor agrees exactly with an independent fixed-selector oracle on a precommitted 300-selector validation set.

Our contribution is not the general idea of graphical-model decoding, affine stabilizer-coset parameterization, variable elimination, semiring inference, or arithmetic-circuit compilation. The closest 2026 qLDPC work uses a mathematically similar fixed-class coset parameterization. The narrower object studied here is a reusable exact compilation in which a unified syndrome-plus-logical selector remains symbolic while stabilizer degeneracy is eliminated, together with a proof of selector-specialization correctness and a controlled equivalence record preserving class scores, degeneracy, ties, and corrections rather than only aggregate logical-error totals.

## 1. Introduction

Quantum error correction introduces an inference problem with a structural feature absent from ordinary classical maximum-likelihood decoding: many physical Pauli errors are equivalent because they differ by stabilizers. A decoder that chooses the most likely individual physical error need not choose the most likely logical equivalence class. Exact degenerate maximum-likelihood decoding therefore requires aggregation over physical representatives inside each syndrome/logical class.

Tensor-network and graphical-model formulations make this aggregation explicit. Ferris and Poulin related quantum decoding to tensor-network contraction. Bravyi, Suchara and Vargo developed exact and approximate maximum-likelihood decoding for the surface code. Subsequent work generalized tensor-network decoding to broader Pauli-code and noisy-syndrome settings. Recent qLDPC work has gone further: Krishnamoorthy et al. formulate logical-class probabilities as partition functions of a positive graphical model and report exact degenerate maximum-likelihood decoding of the \([[72,12,6]]\) bivariate-bicycle code using elimination clusters.

At the fixed-class level, the resulting coset expression is closely aligned with the coset MRF of Krishnamoorthy et al.: both write a class representative plus a binary stabilizer/check combination and factor the resulting physical error over qubits. We therefore do not claim that affine class factorization as new.

The present work asks a narrower question. Once that local coset structure has been fixed, can the syndrome and logical selector themselves remain symbolic while the stabilizer variables are eliminated, so that one exact compiled object can later answer multiple selector queries without rebuilding the structural elimination?

We separate two kinds of binary variables. The first are **selector coordinates**, which encode independent syndrome and logical-class functionals. The second are **stabilizer-degeneracy variables**, which enumerate representatives inside one fixed class. The physical error takes the affine form

\[
e(a,z)=L a\oplus S z.
\]

Instead of assigning \(a\) and running a complete variable-elimination computation for every logical class, we keep \(a\) symbolic and eliminate only \(z\). The result is an exact directed acyclic expression graph whose leaves and selector-choice nodes retain the dependence on \(a\). A later query supplies \(a\) and evaluates the already-compiled object.

This architecture resembles arithmetic-circuit and probabilistic knowledge compilation, where a variable-elimination trace is compiled into a reusable circuit. We therefore do not claim the generic compile-once/query-many principle as new. The contribution here is the quantum-code-specific selector construction and the exact semantic boundary carried through the compilation: syndrome, logical class, stabilizer degeneracy, class probability, minimum representative, canonical class key, winning-class ties, and deterministic correction.

The paper makes four principal contributions.

1. We give an explicit selector/stabilizer factorization for the protected CSS one-sector decoding objects and prove that selector specialization commutes with exact symbolic elimination of stabilizer variables.
2. We extend the proof to the product tropical payload used to recover both the minimum-weight representative and the canonical class key, including tie semantics.
3. On a \([[18,4,4]]\) bivariate-bicycle fixture, we validate the complete semantic object across five representations, not merely final corpus success counts.
4. On the source-bound \([[72,12,6]]\) bivariate-bicycle instance, we demonstrate a larger exact compiled case and validate the reusable descriptor against an independent oracle on a frozen 300-selector set.

We deliberately do not infer an asymptotic scaling law from these two finite codes. We also do not claim practical runtime superiority from abstract operation counts. A separate \([[90,8,10]]\) exact-decoder campaign is ongoing and is excluded from the scientific results of this manuscript until its authoritative external execution completes.

## 2. Degenerate CSS decoding as class inference

### 2.1 One-sector CSS model

Consider a CSS code with binary check matrices \(H_X,H_Z\) satisfying

\[
H_XH_Z^T=0.
\]

We focus on one X-error sector. A physical X error is represented by

\[
e\in\mathbb F_2^n.
\]

Its Z-check syndrome is

\[
s=H_Ze.
\]

Two X errors are stabilizer-equivalent when their difference lies in

\[
\operatorname{rowspace}(H_X).
\]

For a true error \(e\) and correction \(c\), the exact success predicate is

\[
e\oplus c\in\operatorname{rowspace}(H_X).
\]

Syndrome consistency is necessary but not sufficient for logical success.

### 2.2 Logical classes

Fix a basis of independent Z-check syndrome functionals and a logical-Z basis. Their parities define a linear map

\[
\Phi:\mathbb F_2^n\rightarrow\mathbb F_2^m,
\]

where \(m=r_Z+k\) in the one-sector construction, with \(r_Z\) the independent syndrome rank and \(k\) the logical dimension.

Because every X stabilizer commutes with both Z checks and logical-Z operators,

\[
\operatorname{rowspace}(H_X)\subseteq\ker\Phi.
\]

A fixed value

\[
f=\Phi(e)
\]

therefore labels one syndrome/logical class.

### 2.3 Class objectives

For an independent binary symmetric channel with \(p=0.1\), the probability of an error of weight \(h\) is proportional to

\[
9^{n-h}.
\]

The exact logical-class likelihood numerator is consequently

\[
Z_f
=
\sum_{\substack{e\in\mathbb F_2^n\\\Phi(e)=f}}
9^{n-\operatorname{wt}(e)}.
\]

We also use two exact diagnostic objectives:

\[
Z^{(2)}_f
=
\sum_{\Phi(e)=f}
2^{n-\operatorname{wt}(e)},
\]

and

\[
d_f
=
\min_{\Phi(e)=f}\operatorname{wt}(e).
\]

The first is an exact base-2 partition score. The second is a min-plus objective. For deterministic decoding we additionally retain a minimum-weight physical representative and a canonical integer key for the class.

## 3. Selector and stabilizer coordinates

### 3.1 Independent stabilizer variables

Choose independent X-stabilizer generators

\[
S_1,\ldots,S_r\in\mathbb F_2^n.
\]

For

\[
z\in\mathbb F_2^r,
\]

write

\[
S(z)=\bigoplus_{j=1}^rz_jS_j.
\]

These variables enumerate the stabilizer degeneracy inside a fixed class.

### 3.2 Selector basis

Choose physical basis coordinates

\[
b_1,\ldots,b_m
\]

such that the functional columns

\[
\Phi(e_{b_1}),\ldots,\Phi(e_{b_m})
\]

are linearly independent. The resulting \(m\times m\) map is invertible.

For a coordinate vector

\[
a\in\mathbb F_2^m,
\]

define the selector lift

\[
L(a)=\bigoplus_{i=1}^m a_ie_{b_i}.
\]

For any desired functional \(f\), invert the column map to obtain \(a\) satisfying

\[
\Phi(L(a))=f.
\]

Every representative in the class can then be written

\[
e(a,z)=L(a)\oplus S(z).
\]

The stabilizer-kernel property gives

\[
\Phi(e(a,z))=\Phi(L(a))
\]

for all \(z\).

### 3.3 Local factorization

At physical coordinate \(q\),

\[
e_q(a,z)
=
\ell_q(a)\oplus
\bigoplus_{j\in J_q}z_j,
\]

where

\[
J_q=\{j:(S_j)_q=1\}.
\]

Thus each physical bit becomes one local factor involving only the stabilizer variables touching that qubit and, when \(q\) is a selector-basis qubit, one selector parameter.

The structural graph used for eliminating \(z\) is therefore independent of the numerical selector assignment.

## 4. Exact semiring formulations

### 4.1 Sum-product

For the BSC numerator, each local factor contributes

\[
w_q(0)=9,\qquad w_q(1)=1
\]

in the semiring

\[
(\mathbb N,+,\times,0,1).
\]

The contraction

\[
F_9(a)
=
\sum_z\prod_qw_q(e_q(a,z))
\]

is exactly the class likelihood numerator.

### 4.2 Base-2 partition objective

Replacing the local weights by

\[
w_q(0)=2,\qquad w_q(1)=1
\]

gives the exact class score

\[
F_2(a)=\sum_z2^{n-\operatorname{wt}(e(a,z))}.
\]

### 4.3 Min-plus product payload

To recover deterministic representatives as well as minimum weight, define the direct product of two tropical semirings.

The first component minimizes lexicographically

\[
(\operatorname{wt}(e),\operatorname{int}(e)).
\]

The second independently minimizes

\[
\operatorname{int}(e).
\]

A physical bit \(b\) at coordinate \(q\) contributes

\[
\bigl((b,b2^q),b2^q\bigr).
\]

Because the local physical-factor provenance sets remain disjoint throughout exact elimination, integer addition of the powers \(2^q\) equals support union. The first component therefore returns the minimum Hamming weight and the lowest-integer minimum-weight representative. The second returns the canonical minimum integer in the class. These representatives need not coincide.

The direct-product construction is a commutative semiring, so the same exact variable-elimination proof applies.

## 5. Selector-parametric compilation

### 5.1 Symbolic local factors

For a qubit whose selector contribution is parameter \(a_i\), the local factor table stores

\[
\operatorname{ITE}
\left(
i,
w_q(p),
w_q(p\oplus1)
\right),
\]

where

\[
p=\bigoplus_{j\in J_q}z_j.
\]

For a non-selector qubit it stores the exact terminal \(w_q(p)\).

The expression language contains only:

- exact terminals;
- Boolean selector-choice nodes;
- exact semiring multiplication nodes;
- exact semiring marginal/addition nodes.

### 5.2 Symbolic variable elimination

Fix an elimination order on \(z\). At each step the compiler:

1. collects all factors containing the next degeneracy variable;
2. forms their semiring product symbolically;
3. marginalizes over the two assignments of that degeneracy variable;
4. emits the resulting symbolic factor.

Selector variables are never eliminated. No complete selector answer table is produced during compilation.

Structurally identical nodes are hash-consed. For commutative operations, operand identifiers are ordered canonically before interning.

### 5.3 Correctness theorem

Let \(D\) be the resulting symbolic DAG and \(R\) its root. Let \(\operatorname{ev}_a\) specialize its selector choices at coordinate \(a\).

**Theorem 1.** For every selector assignment \(a\),

\[
\operatorname{ev}_a(R)
=
\bigoplus_z
\bigotimes_q
w_q(e_q(a,z)).
\]

**Proof.** Each symbolic local factor specializes to the corresponding fixed-selector numerical factor. Suppose this property holds for every live factor before one elimination step. Specialization commutes with exact semiring multiplication and addition, so it also holds for the factor emitted after eliminating that variable. Induction through the complete elimination order therefore shows that specialization of the final symbolic scalar equals the fixed-selector variable-elimination result. Exact variable elimination itself preserves the full contraction by distributivity. Hash-consing and canonical operand ordering preserve denotation. ∎

A full proof, including the CSS kernel lemma, the min-plus product-semiring argument, and the factor-provenance invariant, is maintained in `QTR-THEOREM-SELECTOR-PARAMETRIC-COMPILATION-001.md`.

### 5.4 Decision preservation

For each syndrome, exact class records contain the class objective, the canonical class key, and the minimum representative. The deterministic decoder chooses the exact optimum, orders ties by the canonical key, and returns the corresponding minimum representative.

Therefore equality of all class records implies equality of:

- class scores;
- tied winner sets;
- chosen class;
- emitted correction.

This is stronger than equality of aggregate corpus success counts.

## 6. C18 complete equivalence study

### 6.1 Protected code and corpus

The first fixture is a protected \([[18,4,4]]\) bivariate-bicycle CSS code. The independent X-stabilizer rank is seven. The finite one-sector benchmark contains every physical error of Hamming weight \(0\) through \(4\):

\[
\sum_{h=0}^{4}\binom{18}{h}=4048.
\]

The correctness oracle checks residual stabilizer equivalence exactly.

### 6.2 Representation chain

The QTR record contains five successive exact views of the same finite inference problem:

1. exhaustive physical representative enumeration;
2. explicit stabilizer-coset aggregation;
3. local parity transfer contraction;
4. seven-variable stabilizer-degeneracy contraction;
5. selector-parametric compiled DAG.

The point of the sequence is not that each transformation is individually novel. It is that the complete promoted semantic object is held fixed while the representation changes.

### 6.3 Degeneracy-variable geometry

The seven-variable factor graph has 18 physical local factors. The initial factor arities are:

| Arity | Number of factors |
|---:|---:|
| 1 | 2 |
| 2 | 8 |
| 3 | 8 |

All

\[
7!=5040
\]

elimination orders were audited. The induced-width histogram is:

| Induced width | Orders |
|---:|---:|
| 4 | 720 |
| 5 | 4320 |

The frozen lexicographically first minimum-width order is

\[
[2,4,0,1,3,5,6].
\]

Its peak joint scope contains five variables, or 32 assignments.

### 6.4 Complete semantic equality

Across three algebras, the compiled path preserves:

| Semantic object | Exact entries/cells checked |
|---|---:|
| Class scores | 6,144 |
| Class mapping / representative records | 2,048 |
| Winning-class tie sets | 384 |
| Deterministic decisions | 384 |

All entries are exactly equal to the promoted predecessor semantics.

The frozen corpus success totals are:

| Objective | Successes / 4048 | Tie envelope |
|---|---:|---:|
| Sum-product \(p=0.1\) | 263 | [263, 263] |
| Base-2 partition | 262 | [262, 262] |
| Min-plus default | 226 | [218, 263] |

The min-plus ambiguity is retained rather than suppressed by compilation.

### 6.5 Compiled objects

The selector-parametric compiled objects are:

| Algebra | Reachable nodes |
|---|---:|
| Sum-product | 371 |
| Base-2 partition | 371 |
| Min-plus product | 388 |
| **Total** | **1,130** |

Their combined canonical serialized size is 65,506 bytes.

These objects contain no complete table of the 2,048 selector outputs.

### 6.6 Abstract operation accounting

QTR uses a common typed abstract-operation ledger for the compiled path and a re-instrumented classwise predecessor:

| Quantity | AOP count |
|---|---:|
| Compilation | 10,160 |
| Evaluate all 2,048 selectors, three algebras | 12,694,528 |
| Compiled one-shot total | 12,704,688 |
| Re-instrumented classwise replay | 14,115,840 |
| Difference | 1,411,152 |

The complete-sweep break-even is one sweep under this ledger.

These AOPs are deterministic abstract events, not CPU instructions and not a wall-clock model. We make no runtime or memory superiority claim from this table.

## 7. C72 case study

### 7.1 Source-bound instance

The larger case is the source-defined \([[72,12,6]]\) bivariate-bicycle code. QTR independently reconstructs:

\[
n=72,\qquad
\operatorname{rank}(H_X)=\operatorname{rank}(H_Z)=30,\qquad
k=12.
\]

The published distance \(6\) is retained as source-reported in this work; it is not independently recertified here.

The one-sector representation contains:

- 30 stabilizer variables;
- 42 selector coordinates.

### 7.2 Named-order structural result

For the QTR factor graph:

| Order | Induced width | Peak joint table |
|---|---:|---:|
| Lexicographic | 24 | \(2^{25}\) |
| Deterministic min-fill | 18 | \(2^{19}\) |
| Deterministic min-degree | 18 | \(2^{19}\) |

Min-fill is frozen as the primary order.

These widths are properties of this specific representation and order policy. They are not global treewidth certificates.

### 7.3 Reusable exact representation

The reusable structural descriptor has:

- 30 elimination steps;
- 1,772 structural scalar entries;
- 14,912 serialized bytes.

The inherited symbolic representation is independently reconstructed as a resource certificate. The exact symbolic node counts are approximately 2.16 million per algebra and remain inside the predeclared finite resource envelope.

### 7.4 Frozen independent validation

The validation set is fixed before execution:

- selector zero;
- every one of 42 unit selectors;
- all-ones;
- 256 deterministic SHA-derived non-reserved selectors.

Total:

\[
300
\]

selectors.

For every selector, the reusable compiled descriptor is compared with an independent direct fixed-selector variable-elimination oracle.

Result:

\[
300/300
\]

selectors match exactly for all three algebras, including the minimum-weight representative and canonical-key payload.

This finite validation is implementation-conformance evidence. The all-selector mathematical equality follows from the selector-parametric compilation theorem for the reference construction.

## 8. Relation to prior work

### 8.1 Tensor-network and graphical-model decoding

Quantum decoding has long been connected to tensor-network contraction. Ferris and Poulin established the formal relationship between tensor networks and quantum error correction. Bravyi, Suchara and Vargo developed maximum-likelihood surface-code decoding based on related contraction ideas. Chubb generalized tensor-network decoding for two-dimensional Pauli codes, and Piveteau, Chubb and Renes developed tensor-network decoding beyond two dimensions and for noisy-syndrome settings.

Our work does not claim priority over these formulations.

### 8.2 qLDPC decoding

BP and BP+OSD methods are established qLDPC baselines, including the work of Roffe et al. and Panteleev and Kalachev. Bivariate-bicycle codes were developed as part of the modern qLDPC memory programme of Bravyi et al.

Most directly relevant is the 2026 work of Krishnamoorthy et al., which formulates degenerate qLDPC decoding as partition-function inference in a coset Markov random field and reports exact degenerate maximum-likelihood decoding of the \([[72,12,6]]\) bivariate-bicycle code using elimination clusters.

Consequently, exact C72 degenerate decoding is not a novelty claim of the present work.

At the class-partition level the two constructions are mathematically close. Krishnamoorthy et al. use (e_lambdaoplus u^T H_X), one variable per X-check, and one qubit potential over the incident checks. QTR uses (L aoplus S z), with an independent stabilizer basis and a full-rank selector interface spanning syndrome and logical coordinates.

The reported C72 structures are nevertheless not numerically comparable without reconstruction: the published coset MRF has 36 check variables and induced width approximately 23, whereas the protected QTR graph has 30 independent stabilizer variables and deterministic min-fill width 18. Different redundancy handling, graph definitions, preprocessing, and ordering implementations can change width.

The working differentiation is therefore not the affine coset MRF itself. It is QTR's retention of the syndrome/logical selector as symbolic parameters in one compiled exact object, plus the larger decoder-level semantic payload. A controlled source-level comparison is required before submission.

### 8.3 Probabilistic knowledge compilation

Arithmetic-circuit compilation of probabilistic inference is established. Work by Darwiche, Chavira and Darwiche, and later probabilistic knowledge-compilation research shows that variable-elimination structure can be compiled once and reused under different evidence assignments. Algebraic model counting extends compiled inference to general semiring settings.

Our contribution is consequently not the abstract fact that compilation and later specialization can commute. The theorem in Section 5 instantiates that known principle for the particular selector/stabilizer structure required by degenerate CSS decoding, including the quantum logical-class and tie/correction semantics that the implementation must preserve.

## 9. Discussion

### 9.1 What compilation buys

The selector-parametric representation separates the part of exact decoding that depends only on code structure from the part that depends on one requested syndrome/logical class.

On C18 this produces a visibly small reusable DAG. On C72 the exact symbolic object is much larger, but the same structural decomposition remains valid and the compiled descriptor can be evaluated repeatedly without rebuilding the elimination plan.

This distinction is useful even when exact decoding ultimately becomes expensive. It exposes where the cost lies: structural elimination, retained symbolic representation, or repeated selector evaluation.

### 9.2 Why full semantic preservation matters

A decoder benchmark can hide substantial mechanism changes behind one scalar logical-error count. QTR instead tracks:

- class scores;
- canonical class identities;
- minimum representatives;
- tied winners;
- deterministic choices;
- final correctness.

This revealed, for example, that the min-plus objective on C18 is materially tie-sensitive even though the representation changes preserve it exactly.

For approximate-decoder research, such exact objects can serve as stronger ground truth than a binary success/failure label. One can ask not only whether an approximate decoder fails, but whether it chose the wrong logical class, mis-estimated a class likelihood, or encountered a near-degenerate tie.

### 9.3 Limits of the finite evidence

C18 and C72 do not establish a qLDPC-family scaling law. In later QTR structural audits, the same named-order representation becomes substantially wider on larger BB instances, beginning with the \([[90,8,10]]\) code. Those later results motivate the current exact C90 campaign but are not evidence that exact inference is intrinsically intractable.

Similarly, the AOP reduction on C18 is not a runtime theorem. Different representations can change cache behavior, integer sizes, memory allocation, and parallelism. Performance must be measured separately.

### 9.4 Current C90 frontier

A separate QTR campaign has compiled and quality-blind validated an exact native representation for the \([[90,8,10]]\) BB instance. Its authoritative large-scale evaluation is being moved to an external compute substrate.

No C90 decoder-quality result from that campaign is used in this manuscript.

If completed, C90 may become a separate result paper. It should not be allowed to block or distort the present method paper.

## 10. Reproducibility and evidence separation

The scientific objects used here are tied to immutable repository evidence and separate promotion records.

For C18:

- the exact fixture and 4,048-case corpus are frozen;
- the TCM-QDEC-001 through 004 sequence preserves the same semantic target;
- the TCM-QDEC-004 evidence payload is
  `a5c7e59fa849ddc37c070d78d4a4dab8b07ae5ceccfecefeb5a20f4ae0dc83a7`.

For C72:

- the source code construction is pinned to the upstream source revision used by QTR;
- the QLDPC-SCALE-001A evidence payload is
  `198bb28f47844aa98efa20d8c838c48870a8aef41ccfda266b16661677e363e1`;
- the frozen selector-validation set and output digests are retained in the evidence package.

The theorem proof is maintained separately from executable replay so that a passing implementation test is not presented as the mathematical proof itself.

Before submission, the public artifact package should include:

1. immutable code and environment identities;
2. C18 semantic records;
3. the C72 frozen validation selector set;
4. independent verification scripts;
5. a compact manifest connecting manuscript tables to evidence digests.

## 11. Conclusion

Degenerate qLDPC decoding can be viewed not only as repeated numerical inference but as an exact compilable function of syndrome/logical selector coordinates.

For the protected bivariate-bicycle instances studied here, stabilizer degeneracy can be eliminated symbolically while selector coordinates remain explicit. The resulting reusable DAG has the same exact denotation as fixed-selector variable elimination. On C18 the construction reproduces the complete promoted semantic object across the full selector domain; on C72 the larger compiled representation agrees with an independent oracle on a precommitted finite validation set.

The main value of the construction is structural. It cleanly separates code-dependent inference from query-dependent selector assignment and retains more exact information than final success counts alone. This creates both a reusable exact decoder representation and a ground-truth object for studying approximate decoders, ties, degeneracy, and the boundary at which exact computation becomes difficult.

## References

1. A. J. Ferris and D. Poulin, “Tensor Networks and Quantum Error Correction,” *Physical Review Letters* 113, 030501 (2014).
2. S. Bravyi, M. Suchara, and A. Vargo, “Efficient Algorithms for Maximum Likelihood Decoding in the Surface Code,” *Physical Review A* 90, 032326 (2014).
3. C. T. Chubb, “General tensor network decoding of 2D Pauli codes,” arXiv:2101.04125 (2021).
4. C. Piveteau, C. T. Chubb, and J. M. Renes, “Tensor-Network Decoding Beyond 2D,” *PRX Quantum* 5, 040303 (2024).
5. J. Roffe, D. R. White, S. Burton, and E. Campbell, “Decoding across the quantum low-density parity-check code landscape,” *Physical Review Research* 2, 043423 (2020).
6. P. Panteleev and G. Kalachev, “Degenerate Quantum LDPC Codes With Good Finite Length Performance,” *Quantum* 5, 585 (2021).
7. S. Bravyi et al., “High-threshold and low-overhead fault-tolerant quantum memory,” *Nature* 627, 778–782 (2024).
8. R. Krishnamoorthy et al., “Certified decoding of quantum LDPC codes,” arXiv:2608.25545 (2026).
9. A. Darwiche, “A Differential Approach to Inference in Bayesian Networks,” *Journal of the ACM* 50(3) (2003).
10. M. Chavira and A. Darwiche, “Compiling Bayesian Networks Using Variable Elimination,” *IJCAI* (2007).
11. A. Kimmig, G. Van den Broeck, and L. De Raedt, “Algebraic model counting,” *Journal of Applied Logic* 22, 46–62 (2017).

## Submission-blocking items

This draft is intentionally not yet a submission candidate.

Required before submission:

- independent mathematical review of Theorem 1 and its supporting lemmas;
- common-definition technical comparison against the 2026 coset-MRF construction;
- refreshed literature search;
- verified bibliography metadata;
- manuscript figures;
- exact table-to-evidence manifest;
- author list, affiliations, acknowledgments, and data/code availability statement.
