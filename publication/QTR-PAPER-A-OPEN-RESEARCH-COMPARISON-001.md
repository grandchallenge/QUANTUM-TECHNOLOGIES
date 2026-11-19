# QTR-PAPER-A-OPEN-RESEARCH-COMPARISON-001

Status: `DOCUMENTARY_REPLICATION_PROTOCOL__NO_NEW_EXECUTION_OR_PUBLICATION_AUTHORITY`

Date: 2026-11-19

Exact protected starting revision: `8637d9b7966b58f26334beaaa9630be4f65489c1`

Programme: Grand Challenge Labs Quantum Technologies Research (QTR)

## Purpose

Make Paper A scientifically accessible, faithfully credit overlapping work, and specify a reproducible route to compare complementary inference techniques. GCL publishes research openly so that others can inspect, reproduce, critique, reuse, and extend it. Public chronology is a provenance record, not evidence that another research group used GCL's work.

## Sources and bounded claims

- GCL C72 structural feasibility: [PR #60](https://github.com/grandchallenge/QUANTUM-TECHNOLOGIES/pull/60), merged 2026-08-17 11:03:17 UTC; source-bound exact compilation/validation on 300 selector assignments under three exact algebras.
- GCL C72 full interface: [PR #111](https://github.com/grandchallenge/QUANTUM-TECHNOLOGIES/pull/111), merged 2026-08-25 05:02:12 UTC; 329 frozen inputs, all 4,096 logical classes per input, three-algebra correction-valued outcomes. Scientific receipt: `evidence/TCM-C72-INTERFACE-001-report.json`.
- R. Krishnamoorthy *et al.*, "[Certified decoding of quantum LDPC codes](https://arxiv.org/abs/2608.25545)", arXiv:2608.25545v1, submitted 2026-08-26 08:57:01 UTC. Their Proposition 1 and Sections 7.6/8.5 give an exact fixed-class coset MRF, elimination/mini-bucket methods, exact C72 decoding on 240 syndromes and a global 4,096-class check on a subsample. The work also provides AIS, Bethe, and several decision-certification methods.
- General arithmetic-circuit / exact-inference compilation and semiring inference predate both works. See `QTR-NOVELTY-UTILITY-AUDIT-001.md` and the cited literature.
- GCL's reusable selector-parametric DAG is a potentially useful **specific representation**, not a certified first-of-kind claim. The comparator manuscript inspected does not specify an equivalent symbolic query DAG. The absence in prose does not establish absence in authors' source or the wider literature.

The repository merge records predate the paper's arXiv submission; they do **not** establish the competing team's internal research timeline, access, or influence. Neither a provenance disagreement nor a derivation allegation is made.

## Mechanism correspondence

For a fixed syndrome/logical class, the comparator's `e_lambda XOR (u^T H_X)` and QTR's `L(a) XOR S(z)` denote the same **type** of affine stabilizer coset, under consistent basis choices. They do not automatically denote the same numerical partition function unless they use the same code, physical noise model and counting convention.

The comparator uses all 36 C72 X checks, including redundancies; QTR uses an independent 30-dimensional X-stabilizer basis. At equal physical error weights and fixed class:

```text
Z_all_checks = 2^(36 - 30) * Z_independent_basis
             = 64 * Z_independent_basis
```

This identity follows from the linear map from check coefficients onto the rank-30 rowspace, with a kernel of dimension 6. It applies only if all check configurations are included and each physical error contributes the same weight in both formulations. For ordinary **sum-product** partition functions, this positive constant does not change logical-class orderings; it **does** change raw partition-function values. The factor of 64 is **not** a correction factor for min-plus optima: repeating each term does not change a minimum. If numerical semirings differ, normalizations and conversions must be declared explicitly. The relationship is a mathematical correspondence, not a new execution result.

## Completed source-locked common-primal-graph cell (2026-11-19)

QTR PR #131 admitted a controlled structural reconstruction based on the same protected C72 36-row X-check matrix. A common qubit-factor and primal-graph definition, with one min-fill policy (fewest missing edges, then degree, then index), yields width 23 for all 36 check variables and width 18 for 30 independent stabilizers. The graphs have 216 and 151 primal edges. Its exact code, five tests and complete report are in publication/research/qtr_c72_common_graph_001.py, publication/tests/test_qtr_c72_common_graph_001.py and publication/research/QTR-C72-COMMON-GRAPH-001-report.json (canonical SHA-256 8f09c69b0c86c797b988173f9fedd124e9a1b30cc5bcac61c4d5fb5f2bc6746f).

This is a common **mathematical graph** comparison, not an execution of the other team's source or a common-host runtime benchmark. Their approximately-23 reported width is a consistency observation only; exact preprocessing, ordering and numerical outputs still need an independent source comparison.

## Replication protocol: common C72

This protocol is proposed for a *separately authorized* comparison; it does not execute or authorize a new experiment.

1. **Lock exact inputs**: same code matrices and endianness; rank-30 independent X stabilizers; logical-Z conventions; code revision; syndrome/corpus digest; BSC physical error probability and exact class-label map. Publish hashes before inspecting outcomes.
2. **Rebuild each original model**: one model with 36 declared check variables and the paper's qubit potentials; one with 30 independent stabilizer variables and QTR's selector lift. Preserve each model's original elimination and parameter treatment.
3. **Verify mathematical equality first**: for a precommitted set of syndrome/class assignments, compare exact scores after removing the known check-redundancy factor of 64. Align BSC normalizations, fixed-class representatives, and all bit orders. Independently verify syndrome and stabilizer membership.
4. **Compare decision semantics**: expose class scores, winning ties, representative-selection rules and corrections, rather than merely a binary success rate. Align tie policy before comparing decisions.
5. **Measure computation honestly**: compile construction, reusable object size, per-query evaluation, cumulative multi-query cost, retained peak memory, physical host, integer precision, cache state, and whether approximation/pruning is permitted must all be separately labelled. Graph widths require identical definitions and deterministic ordering algorithms.
6. **Evaluate complementarity**: compare certified approximate decisions against exact oracle scores on exactly shared trials; consider a conditional protocol in which a certificate authorizes an inexpensive decision and an uncertified case is escalated to an exact oracle. This is a research hypothesis and requires predeclared validation.
7. **Release and review**: publish exact scripts, manifests and machine-checkable equivalence outputs; retain negative results, inconclusive cells, and independent reviewer dispositions. No post-outcome tuning of the frozen C90 scientific method is permitted.

## C90 boundary

The [[90,8,10]] exact campaign remains independent of Paper A. The original August conventional ZIP is unavailable, but the frozen per-input conventional outcome vectors were recovered by exact canonical-content equivalence from authenticated October replay artifacts, preserving their true replay identities. All four surviving original compilation and validation ZIPs are SHA-256 verified and preserved on CHAD. A quality-blind exact C90 Colab pilot is in progress; the complete 266,496-cell campaign is unfinished and provenance-aware comparison intake remains a draft PR #129. No C90 quality, performance, novelty or admission claim follows.

## Collegial exchange proposal (draft only; not sent)

A possible note to the authors of *Certified decoding of quantum LDPC codes*:

> We enjoyed reading your work on certified degenerate qLDPC inference, particularly the coset-MRF construction and the AIS, Bethe and mini-bucket certification strategies. Grand Challenge Labs has been developing an open exact selector-parametric compilation route for BB-code inference, with our C72 work and evidence publicly available at https://github.com/grandchallenge/QUANTUM-TECHNOLOGIES. The fixed-class coset formulation overlaps directly with yours, while our work retains syndrome/logical selectors in a reusable exact expression DAG. We would welcome an exchange of implementation details or a controlled common-C72 comparison, particularly whether our exact class-score oracle could help evaluate your certificates and whether your certified approximations could guide expensive exact queries. We are interested in reproducibility, complementary strengths and collaboration, not priority disputes.

This text is a draft, not a message from an author and not an external communication.

## Publication boundary

This is documentary work only. Protected exact results, code, evidence, scientific registry, and governance permissions are unchanged. Paper A remains under publication review; implementation conformance is not interchangeable with the mathematical theorem and neither constitutes an independent novelty certification.
