# QTR-THEOREM-SELECTOR-PARAMETRIC-COMPILATION-001

Status: \`THEOREM_CANDIDATE__REFERENCE_PROOF_COMPLETE__NATIVE_REFINEMENT_SEPARATE\`

Programme: \`GCL Quantum Technologies Research (QTR)\`

Applies directly to the mathematical construction implemented by:

- \`reference/tcm_qdec_004.py\`;
- the generalized symbolic construction in \`reference/qldpc_scale_001a_symbolic.py\`.

This note proves the mathematical compile/evaluate identity. It does not by itself certify that every software implementation is bug-free. Executable equivalence tests and native C90 refinement remain separate obligations.

## 1. Setting

Let there be \(n\) physical binary error coordinates and \(r\) independent X-stabilizer degeneracy variables.

Let

\[
S_1,\ldots,S_r\in\mathbb F_2^n
\]

be the selected independent X-stabilizer basis. For physical coordinate \(q\), define

\[
J_q=\{j:(S_j)_q=1\}.
\]

Let \(b_1,\ldots,b_m\) be distinct selector-basis physical coordinates. Define

\[
L(a)=\bigoplus_{i=1}^{m} a_i e_{b_i},
\qquad
a\in\mathbb F_2^m,
\]

where \(e_q\) is the physical unit vector at \(q\).

For

\[
z=(z_1,\ldots,z_r)\in\mathbb F_2^r,
\]

define

\[
S(z)=\bigoplus_{j=1}^{r} z_jS_j.
\]

The represented physical error is

\[
e(a,z)=L(a)\oplus S(z).
\]

Coordinatewise,

\[
e_q(a,z)
=
\ell_q(a)\oplus
\bigoplus_{j\in J_q}z_j,
\]

where

\[
\ell_q(a)=
\begin{cases}
a_i,&q=b_i,\\
0,&q\notin\{b_1,\ldots,b_m\}.
\end{cases}
\]

This is the structural form used by the QTR symbolic compiler.

## 2. Selector functionals and class invariance

Let

\[
\Phi:\mathbb F_2^n\to\mathbb F_2^m
\]

collect the independent syndrome and logical-class functionals.

For the CSS one-sector construction used by QTR, \(\Phi\) consists of:

1. independent Z-check syndrome parities; and
2. commutation parities against a chosen logical-Z basis.

### Lemma 1 — stabilizer kernel

For every X-stabilizer \(s\in\operatorname{rowspace}(H_X)\),

\[
\Phi(s)=0.
\]

#### Proof

For every Z-check row \(h\) of \(H_Z\),

\[
h\cdot s=0
\]

by CSS commutation,

\[
H_XH_Z^{T}=0.
\]

For every logical-Z operator \(\bar Z_\ell\), an X-stabilizer commutes with \(\bar Z_\ell\), so its binary symplectic parity with \(\bar Z_\ell\) is also zero.

Thus every syndrome and logical functional used by \(\Phi\) vanishes on the selected X-stabilizer span. QED.

### Selector-basis condition

The selector basis is required to satisfy

\[
\operatorname{rank}
\left[
\Phi(e_{b_1})\ \cdots\ \Phi(e_{b_m})
\right]
=m.
\]

Therefore the column map is invertible over \(\mathbb F_2\). For every requested functional \(f\in\mathbb F_2^m\), QTR computes a unique coordinate \(a\) in the chosen basis such that

\[
\Phi(L(a))=f.
\]

The C72/C90 interface verifies this explicitly through \`functional_columns\`, \`inverse_columns\`, \`apply_inverse\`, and \`selector_lift\`.

By Lemma 1,

\[
\Phi(e(a,z))
=
\Phi(L(a))+\Phi(S(z))
=
f
\]

for every \(z\). Thus varying \(z\) enumerates representatives inside one fixed syndrome/logical class.

## 3. Exact local objectives

For every physical coordinate \(q\), let

\[
w_q:\mathbb F_2\to\mathcal A
\]

take values in a commutative semiring

\[
\mathcal S=(\mathcal A,\oplus,\otimes,0_{\mathcal S},1_{\mathcal S}).
\]

### Sum-product BSC numerator

Use

\[
(\mathbb N,+,\times,0,1)
\]

with

\[
w_q(0)=9,\qquad w_q(1)=1.
\]

For an error of Hamming weight \(h\), the product is \(9^{n-h}\), proportional to its BSC \(p=0.1\) likelihood.

### Soft-tropical base 2

Use the same semiring with

\[
w_q(0)=2,\qquad w_q(1)=1.
\]

### Min-plus product payload

Let \(\overline{\mathbb N}=\mathbb N\cup\{\infty\}\).

Define the lexicographic tropical semiring

\[
\mathcal T_{\mathrm{lex}}
=
(\overline{\mathbb N}^{\,2},
\min_{\mathrm{lex}},
+,
(\infty,\infty),
(0,0)).
\]

Define the ordinary tropical semiring

\[
\mathcal T
=
(\overline{\mathbb N},
\min,
+,
\infty,
0).
\]

The QTR min-plus payload lives in the direct product

\[
\mathcal M=\mathcal T_{\mathrm{lex}}\times\mathcal T.
\]

A local physical bit \(b\in\{0,1\}\) at qubit \(q\) contributes

\[
w_q(b)
=
\bigl((b,b2^q),\,b2^q\bigr).
\]

### Lemma 2 — the min-plus payload is a commutative semiring

\(\mathcal M\) is a commutative semiring under componentwise tropical addition and multiplication.

#### Proof

Integer addition is associative and commutative. Lexicographic order on \(\overline{\mathbb N}^{\,2}\) is translation invariant:

\[
x\le_{\mathrm{lex}}y
\Longrightarrow
x+c\le_{\mathrm{lex}}y+c.
\]

Hence addition distributes over lexicographic minimum, so \(\mathcal T_{\mathrm{lex}}\) is a commutative idempotent semiring. The same standard argument gives the ordinary min-plus semiring \(\mathcal T\). A direct product of commutative semirings is a commutative semiring under componentwise operations. QED.

## 4. Factor provenance

The representative payload uses integer addition to combine physical-bit masks. This is exact only if no original physical-qubit factor is counted twice.

### Lemma 3 — factor provenance remains a partition

Associate each initial local factor at qubit \(q\) with provenance set

\[
P_q=\{q\}.
\]

At every variable-elimination step, replace the involved factors by one output factor whose provenance is the union of their provenance sets.

Then at every stage the live factor provenance sets are pairwise disjoint and their union is \(\{0,\ldots,n-1\}\).

#### Proof

Initially the singleton sets form a partition.

Assume the live provenance sets form a partition. An elimination step selects some live factors, removes all of them, and replaces them by one factor whose provenance is their union. Because the selected sets were pairwise disjoint, their union is disjoint from every unselected live provenance set. The total union remains unchanged.

The invariant follows by induction. QED.

### Corollary — integer addition equals support union

Within any semiring product, every physical qubit contributes at most one power \(2^q\). Therefore

\[
\sum_{q:e_q=1}2^q
=
\bigvee_{q:e_q=1}2^q.
\]

Thus the first tropical component tracks

\[
(\operatorname{wt}(e),\operatorname{int}(e))
\]

and returns the minimum-weight representative with lowest integer tie break.

The second tropical component independently returns

\[
\min_{e\text{ in class}}\operatorname{int}(e),
\]

the canonical class key.

The two minimizers need not be the same representative; the product payload intentionally computes two exact summaries of the same class.

## 5. Fixed-selector class contraction

For a fixed selector coordinate \(a\), define

\[
F(a)
=
\bigoplus_{z\in\mathbb F_2^r}
\bigotimes_{q=1}^{n}
w_q(e_q(a,z)).
\]

For sum-product, \(F(a)\) is the exact class likelihood numerator under the frozen BSC.

For soft-tropical, it is the exact base-2 partition score.

For the min-plus product algebra, it is the exact pair consisting of:

1. minimum Hamming weight and lowest-integer minimum-weight representative;
2. minimum physical integer in the class.

Standard exact variable elimination over \(z\) evaluates \(F(a)\).

## 6. Symbolic expression language

The compiler replaces numerical table entries by expressions generated from:

- exact terminals;
- selector-choice nodes
  \[
  \operatorname{ITE}(i,x_0,x_1);
  \]
- semiring multiplication nodes;
- semiring marginal/addition nodes.

For selector assignment \(a\), define \(\operatorname{ev}_a\) recursively:

\[
\operatorname{ev}_a(c)=c,
\]

\[
\operatorname{ev}_a(\operatorname{ITE}(i,x_0,x_1))
=
\begin{cases}
\operatorname{ev}_a(x_0),&a_i=0,\\
\operatorname{ev}_a(x_1),&a_i=1,
\end{cases}
\]

and

\[
\operatorname{ev}_a(x\otimes y)
=
\operatorname{ev}_a(x)\otimes\operatorname{ev}_a(y),
\]

\[
\operatorname{ev}_a(x\oplus y)
=
\operatorname{ev}_a(x)\oplus\operatorname{ev}_a(y).
\]

Thus specialization commutes with every semiring operation represented in the DAG.

## 7. Lemma 4 — local specialization

For every qubit \(q\), local stabilizer assignment \(u\in\mathbb F_2^{J_q}\), and selector assignment \(a\),

\[
\operatorname{ev}_a(\Psi_q(u))
=
w_q
\left(
\ell_q(a)\oplus
\bigoplus_{j\in J_q}u_j
\right).
\]

### Proof

Let

\[
p(u)=\bigoplus_{j\in J_q}u_j.
\]

If \(q\) is not a selector-basis qubit, the compiler emits the terminal \(w_q(p(u))\).

If \(q=b_i\), it emits

\[
\operatorname{ITE}
\left(
i,
w_q(p(u)),
w_q(p(u)\oplus1)
\right).
\]

Specialization at \(a_i\) therefore yields

\[
w_q(p(u)\oplus a_i),
\]

which is exactly the claimed local value. QED.

## 8. Lemma 5 — elimination commutes with selector specialization

Suppose symbolic live factors \(\{\Psi_k\}\) specialize under \(a\) to fixed-selector numerical factors \(\{\psi_k^{(a)}\}\).

Eliminate degeneracy variable \(z_j\). Let \(I\) be the factors containing \(z_j\).

The symbolic output is

\[
\Psi'(u)
=
\bigoplus_{b\in\{0,1\}}
\bigotimes_{k\in I}
\Psi_k(u,z_j=b).
\]

The numerical fixed-selector output is

\[
\psi'^{(a)}(u)
=
\bigoplus_{b\in\{0,1\}}
\bigotimes_{k\in I}
\psi_k^{(a)}(u,z_j=b).
\]

Then

\[
\operatorname{ev}_a(\Psi'(u))
=
\psi'^{(a)}(u).
\]

### Proof

By the recursive semantics of specialization,

\[
\begin{aligned}
\operatorname{ev}_a(\Psi'(u))
&=
\operatorname{ev}_a
\left(
\bigoplus_b
\bigotimes_{k\in I}\Psi_k(u,b)
\right)\\
&=
\bigoplus_b
\bigotimes_{k\in I}
\operatorname{ev}_a(\Psi_k(u,b))\\
&=
\bigoplus_b
\bigotimes_{k\in I}
\psi_k^{(a)}(u,b)\\
&=
\psi'^{(a)}(u).
\end{aligned}
\]

QED.

## 9. Theorem — selector-parametric compilation correctness

Let \(D\) be the symbolic DAG obtained by:

1. constructing the symbolic local factors above;
2. eliminating all \(r\) stabilizer variables in any fixed complete order using exact semiring multiplication and marginalization;
3. multiplying any remaining scalar factors.

Let \(R\) be its root.

Then for every selector assignment \(a\in\mathbb F_2^m\),

\[
\boxed{
\operatorname{ev}_a(R)=F(a)
}.
\]

### Proof

By Lemma 4, before elimination every symbolic local factor specializes to its fixed-selector numerical counterpart.

Apply Lemma 5 inductively after each of the \(r\) elimination steps. After the final step, all remaining factors are scalar, and specialization commutes with their final semiring product.

Exact variable elimination preserves the complete contraction by distributivity. Therefore the specialized root equals

\[
\bigoplus_z\bigotimes_qw_q(e_q(a,z))
=
F(a).
\]

QED.

## 10. Lemma 6 — canonical DAG construction preserves denotation

The implementation:

- hash-conses structurally identical nodes;
- canonicalizes child order for commutative binary operations;
- simplifies \(\operatorname{ITE}(i,x,x)\) to \(x\).

None changes \(\operatorname{ev}_a\).

### Proof

Hash-consing shares an existing subexpression without changing its recursive value.

For a commutative operation \(\star\),

\[
x\star y=y\star x,
\]

so child reordering preserves value.

Finally,

\[
\operatorname{ITE}(i,x,x)=x
\]

under both selector values. QED.

## 11. Corollary — decoder decision preservation

Suppose the compiled object is evaluated for every logical class compatible with a syndrome and produces the same class records as fixed-selector exact inference.

If the decoder's deterministic decision function depends only on:

- class objective value;
- canonical class key;
- minimum representative;
- the frozen class tie rule,

then compiled and fixed-selector execution have identical:

- class-score table;
- tied winner set;
- deterministic chosen class;
- deterministic emitted correction.

## 12. C18 complete executable witness

\`TCM-QDEC-004\` evaluates its compiled DAG over the full 2048-selector domain for all three exact algebras.

It separately replays the classwise \`TCM-QDEC-003\` contraction.

Protected evidence records exact equality of:

- 6144 class-score entries;
- 2048 class-mapping entries;
- 384 winning-class tie sets;
- 384 deterministic decisions.

The reachable compiled DAG sizes are:

- sum-product: 371 nodes;
- soft-tropical: 371 nodes;
- min-plus product: 388 nodes.

This is exhaustive finite implementation evidence for C18. It is not substituted for the theorem.

## 13. C72 generalization

The generalized compiler uses

\`selector_parameter = {qubit: index for index, qubit in enumerate(selector_basis)}\`

and otherwise the same local selector choices and exact elimination construction.

Therefore the theorem applies mathematically whenever:

1. the selector basis is distinct;
2. its functional-column map has full rank;
3. stabilizer scopes are generated from an independent stabilizer basis;
4. the declared algebra is one of the semirings above.

The C72 package separately records compiled-versus-independent-oracle equality on the frozen 300-selector set.

The theorem establishes the mathematical all-selector identity of the construction. The 300-selector replay remains implementation-conformance evidence.

## 14. C90 native refinement boundary

The native C90 compiler/evaluator is a separate implementation of the reference semantics.

A paper that uses native C90 results must additionally establish a refinement statement:

> The native serialized DAG implements the same terminals, selector choices, binary operations, exact integer semantics and root evaluation as the reference selector-parametric construction.

Current executable support includes:

- exact source/hash binding;
- canonical compile identities;
- same-head native compilation;
- quality-blind 307-selector × three-algebra validation;
- 921/921 exact semantic comparisons.

Those checks strongly support refinement but do not replace a written implementation correspondence argument.

## 15. Relationship to prior knowledge-compilation theory

The main theorem is a specialization of a known general principle: exact variable-elimination traces can be compiled into arithmetic circuits, and later evidence assignments can be evaluated on the compiled representation.

Therefore this theorem is not presented as a new theorem of probabilistic inference.

Its role is to prove that the QTR qLDPC construction satisfies that principle while preserving the specific syndrome/logical selector semantics, stabilizer degeneracy, min-plus representative/canonical-key payload and deterministic quantum-decoder tie rules.

The publication claim must concern the QEC construction and verified application, not distributivity itself.

## 16. Remaining obligations

Before Paper A submission:

- express this proof in the manuscript's notation;
- provide a concise implementation-correspondence table for C18 and C72;
- write the native C90 refinement argument if C90 is included as theorem-backed evidence;
- obtain independent mathematical review.

## 17. Disposition

\`REFERENCE_THEOREM_PROOF_COMPLETE__READY_FOR_INDEPENDENT_REVIEW\`

No mathematical gap remains in the reference selector-parametric compile/evaluate identity identified by this audit.

The open proof boundary is implementation refinement for the native C90 realization, not the reference construction itself.
