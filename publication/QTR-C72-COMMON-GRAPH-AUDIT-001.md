# QTR-C72-COMMON-GRAPH-001 — common-policy structural comparison

Status: \`BOUNDED_SOURCE_LOCKED_RECONSTRUCTION__SCIENTIFIC_REVIEW_PENDING\`

Date: 2026-11-19

Protected code source: QTR main \`aa2b293545eb3248d1482728808526d247a81c29\`; C72 X-check matrix canonical SHA-256 \`6c01bd1eceb703a1afbd9897c9ce3810d951bc0d1284588607775e9f875740f2\`.

## Research question

After accounting for the X-check linear dependencies, how does the structural graph of the *same* bivariate-bicycle [[72,12,6]] code change between two exact affine-coset representations?

The two definitions use the identical physical qubit coordinates, full 36-row X-check matrix and qubit-local parity factors:

1. **Full-check formulation:** one binary latent variable per all 36 X-check rows.
2. **Independent-basis formulation:** one binary latent variable per the protected independent X-stabilizer subset of rank 30.

For each of the 72 physical qubits, the factor scope comprises every latent variable corresponding to a generator incident on that qubit. The primal graph joins two latent variables whenever they occur in the same qubit factor. **The same** graph construction and three deterministic elimination algorithms are applied to both models. These are static structural analyses, not full decoder evaluations.

## Reconstructed results

| Statistic | 36-check graph | 30-independent graph |
|---|---:|---:|
| Latent binary variables | 36 | 30 |
| Qubit-local factors | 72 | 72 |
| Factor scope arities | 72 of arity 3 | 7 of arity 1, 22 of arity 2, 43 of arity 3 |
| Primal graph edges | 216 | 151 |
| Lexicographic induced width | 30 | 24 |
| Min-degree induced width | 26 | 18 |
| Min-fill induced width | **23** | **18** |
| Min-fill peak joint assignments (structural) | \`2^24\` | \`2^19\` |

The common tie policy is explicitly specified: min-fill chooses the fewest missing edges among active neighbors, followed by current degree, then original variable index. Min-degree chooses current degree, then index. Lexicographic chooses the smallest live index.

The protected QTR report independently confirms widths 24/18/18 for the rank-30 graph. Its recorded min-fill *elimination order* is not identical to our new common-policy order because the tie-break differs, although the induced width agrees.

The reconstructed 36-check min-fill width **23** happens to agree with the approximately-23 C72 value reported by Krishnamoorthy et al. However, the comparator's implementation, pruning, graph preprocessing, memory layout and exact ordering rules were not inspected or executed. Numerical agreement is a useful consistency check, **not a certified common-implementation comparison** or a runtime result.

## Exact mathematical normalization

The declared 36 X-check rows have rank 30. The full-check coefficient map has a six-dimensional kernel and precisely \(2^6=64\) coefficient vectors for each independent stabilizer displacement. With identical physical weights and syndrome/logical class:

\[
Z_{\mathrm{full\ checks}}=64 Z_{\mathrm{independent}}.
\]

The factor is for **ordinary sum-product partition functions**; min-plus minima are unchanged by repeated representatives. The six explicit kernel generators and a separate three-test algebraic certificate are in Paper A PR #128 at \`publication/QTR-C72-COSET-COORDINATE-CERTIFICATE-001.json\`. This structural comparison independently reconstructs the matrix rank and rowspace.

## Exact machine-readable evidence

- \`publication/research/qtr_c72_common_graph_001.py\`: pure Python source-locked reconstruction and named-order graph algorithm.
- \`publication/tests/test_qtr_c72_common_graph_001.py\`: five independent finite structural and hostile tests.
- \`publication/research/QTR-C72-COMMON-GRAPH-001-report.json\`: canonical machine-readable output; expected SHA-256 (excluding its own \`canonical_report_sha256\` key) \`8f09c69b0c86c797b988173f9fedd124e9a1b30cc5bcac61c4d5fb5f2bc6746f\`.

Reproduction:

\`\`\`bash
python3 publication/tests/test_qtr_c72_common_graph_001.py -v
python3 publication/research/qtr_c72_common_graph_001.py \
  --output /tmp/QTR-C72-COMMON-GRAPH-001-report.json
\`\`\`

The five local tests passed at source head \`ca7ead4a641b2da1171441a3cae3aa3a480db9d5\`. No GPU is required; this is bounded structural verification, so CHAD's local CPU is appropriate.

## Claim boundary and next decision

- We have **not** shown the globally optimal treewidth for either graph.
- We have **not** shown a lower runtime or memory footprint for a complete decoder; redundant-check coordinate sums and independent-basis coordinate sums have different multiplicities and numerical normalizations.
- We have **not** accessed or executed the comparator's source code, and do not claim their intellectual work was derived from GCL's.
- We have **not** added a new C72 accuracy/decoding-quality result, multi-code scaling law or novel semiring theorem.
- Paper A's earlier 300 frozen selector checks and distinct 329-input interface campaign remain untouched.
- The corresponding publication claim may be added to Paper A only after this **separate** structural audit has passed exact-head protected review. The careful headline is *a reproducible contrast of two coset parameterizations under common graph and elimination policies*, not decoder superiority.
