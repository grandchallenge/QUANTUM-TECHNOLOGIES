# QTR-C72-COSET-MRF-COMPARISON-PLAN-001

Status: DOCUMENTARY_COMPARISON_PLAN__NO_NEW_SCIENTIFIC_EXECUTION_AUTHORITY

Audit basis date: 2026-10-02

Closest paper: Ragavi Krishnamoorthy et al., “Certified decoding of quantum LDPC codes,” arXiv:2608.25545v1 (26 August 2026).

## 1. Core finding

The coset-MRF construction is mathematically close to the QTR class factorization.

Krishnamoorthy et al. use a fixed syndrome solution and logical representative,

\[
e_\lambda=e_0\oplus\lambda^T L_X,
\]

then enumerate its stabilizer coset as

\[
e=e_\lambda\oplus u^T H_X,
\]

with class partition function

\[
Z_\lambda(s)=\sum_u w^{|e_\lambda\oplus u^T H_X|}.
\]

They introduce one binary variable per X-check and one local qubit potential whose parity is the class-representative bit XOR the incident check variables.

QTR writes the corresponding affine object as

\[
e(a,z)=L a\oplus S z,
\]

where a combines independent syndrome/logical functionals and z parameterizes an independent stabilizer basis.

Therefore the following are overlapping structure, not safe QTR novelty claims:

- absorption of syndrome constraints into an affine class representative;
- binary stabilizer/check variables;
- one local factor per physical qubit;
- exact class probability as a partition function;
- variable elimination over the stabilizer/check variables.

## 2. Conceptual mapping

| Krishnamoorthy et al. | QTR | Relation |
|---|---|---|
| particular syndrome solution e0 | syndrome portion of selector lift | same affine role |
| logical coordinate lambda | logical portion of selector a | same class-selection role |
| class representative e_lambda | L a | class seed |
| X-check variables u_c | independent stabilizer variables z_j | degeneracy coordinates |
| u^T H_X | S z | stabilizer displacement |
| qubit clique N(v) | local stabilizer scope J_q | same locality origin |
| class partition function Z_lambda | exact class score F(a) | same sum-product object |
| junction tree / bucket elimination | exact variable elimination | same generic inference principle |

## 3. Material differences worth auditing

### 3.1 Independent stabilizer coordinates

Krishnamoorthy et al. formulate one binary variable per X-check and note that redundant X-check rows multiply every class partition function by the same constant.

QTR first chooses an independent stabilizer basis.

This is a representation choice, not by itself a novelty claim. It can alter graph width, so width numbers must not be compared without reconstruction.

### 3.2 Unified syndrome-plus-logical selector coordinates

The comparator fixes a syndrome solution e0 and then varies the logical label lambda.

QTR builds one full-rank Boolean selector interface containing independent syndrome coordinates followed by logical coordinates and maps that interface to selected physical unit vectors.

This makes both syndrome and logical-class dependence explicit parameters of one structural object.

### 3.3 Selector-parametric compilation

QTR does not assign the selector before symbolic elimination. It retains the selector bits in choice nodes and eliminates only stabilizer-degeneracy variables, giving one canonical exact DAG D(a) whose later specialization evaluates fixed-selector inference.

The current paper clearly reuses one coset-MRF form and evaluates many logical classes; it also computes global exact C72 optima over all 2^12 logical classes on a subsample after mini-bucket screening. The inspected text does not describe one arithmetic/expression DAG retaining syndrome/logical representative bits symbolically through elimination.

That absence is only a working differentiation hypothesis. Source and supplementary inspection are required before submission.

### 3.4 Exact decoder-level payload

QTR validates the compiled construction under:

- BSC sum-product;
- an exact base-2 partition algebra;
- min-plus weight;
- deterministic minimum-weight representative;
- canonical class key;
- winning-class tie sets;
- deterministic corrections.

General semiring knowledge compilation is prior art. The possible contribution is the exact QEC semantic package and its controlled end-to-end equivalence record.

## 4. Width numbers are not directly comparable

Krishnamoorthy et al. report approximately 36 coset variables and induced width about 23 for C72.

QTR records 30 independent stabilizer variables and deterministic min-fill width 18 for its C72 graph.

The present report must not say “18 beats 23.”

Possible sources of the difference include:

- all X-check rows versus an independent stabilizer basis;
- different primal/coset graph definitions;
- preprocessing and sparsification;
- elimination-order implementation;
- factor representation.

Current admissible wording:

> Both constructions find exact C72 class inference structurally feasible under their respective representations; their reported widths are representation-specific and are not directly comparable.

## 5. Controlled reconstruction experiment

If separately authorized as new scientific work, reconstruct both C72 graphs from the same frozen upstream matrices.

For the comparator graph:

- follow Proposition 1 literally;
- one variable per declared X-check row;
- one qubit factor per support N(v);
- class representative supplied as the local parity offset;
- retain redundant rows unless a separately labelled rank-reduced variant is defined.

For the QTR graph:

- use the protected independent X-stabilizer basis;
- use the protected selector-functional inverse;
- use the protected local scopes.

Under one common structural-audit implementation, record:

- latent-variable count;
- factor count;
- factor-arity histogram;
- primal edge count;
- lexicographic, deterministic min-fill and deterministic min-degree widths;
- peak joint arity;
- order identities.

Then use a precommitted finite selector set and require exact class-score equality after explicitly accounting for any constant redundancy factor.

Semantic identity must be established before structural comparison.

## 6. Publication consequences

A defensible Paper A contribution now requires at least one of:

1. a genuinely different selector-parametric compilation object spanning the syndrome/logical query family;
2. a controlled representation reduction after common-definition reconstruction;
3. a useful exact multi-object semantic compilation result even if the underlying coset factorization is shared.

If source inspection shows that the 2026 work already compiles an equivalent symbolic parameterized object, Paper A must narrow further.

C90 remains a separate potentially stronger novelty route if exact external execution closes and a renewed literature audit remains negative for that exact instance and scope.

## 7. Current disposition

DIRECT_MATHEMATICAL_OVERLAP_CONFIRMED__PARAMETRIC_COMPILATION_DIFFERENTIATION_REQUIRES_CONTROLLED_AUDIT

This document authorizes no new scientific execution.
