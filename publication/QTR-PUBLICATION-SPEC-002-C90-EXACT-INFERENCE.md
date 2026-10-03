# QTR-PUBLICATION-SPEC-002

Status: `CONDITIONAL_MANUSCRIPT_SPECIFICATION__RESULT_PENDING`

Working title:

**Exact Degenerate Logical-Class Inference on the `[[90,8,10]]` Bivariate-Bicycle Code**

Programme: `GCL Quantum Technologies Research (QTR)`

Scientific campaign: `QTR-C90-EXACT-DECODER-001`

## 1. Publication condition

This paper is conditional.

No results section, abstract success claim, “first” claim, decoder-quality claim, or conventional-decoder comparison may be finalized until the authoritative external execution of `QTR-C90-EXACT-DECODER-001` completes.

The retired GitHub-hosted selector outputs are non-authoritative historical cross-check evidence and may not supply the paper's scientific result.

## 2. Scientific question

For the protected one-sector `[[90,8,10]]` bivariate-bicycle CSS instance, can the already validated exact selector-parametric representation be used to compute all 256 logical-class objectives for each input in the frozen 347-input corpus, fix the resulting corrections before quality exposure, and then perform a matched exact comparison with the protected conventional decoder outcomes?

The paper studies a finite exact problem. It is not a threshold study, an exhaustive syndrome-domain performance study, or a family-scaling result.

## 3. Frozen scientific object

The manuscript must bind exactly:

- activation head: `0c1f5591a097adc285dec4cbfc320eeebd2c65d3`;
- C90 corpus digest: `b053a27a9c346832d6008987e204c88162dc1797e0367b38705861049059e086`;
- corpus size: 347;
- logical dimension: 8;
- logical classes per syndrome: 256;
- selector rank: 49;
- algebras:
  - `sum_product_bsc_p_0_1`;
  - `soft_tropical_base_2`;
  - `min_plus_hamming`;
- exact selector evaluations required:
  [
  347	imes256	imes3=266,496.
  ]

The conventional comparison anchors remain:

- BP min-sum: `200/347`;
- BP-OSD CS-7: `211/347`;
- BP sum-product: `171/347`.

Those totals are historical protected records, not predictors of the TCM outcome.

## 4. Pre-result exactness evidence

The paper may report the already completed quality-blind implementation qualification independently of the final quality result.

At the activation head:

- same-head exact compilation completed for all three algebras;
- canonical compile identities were reproduced;
- the frozen semantic-validation matrix contained 307 selectors × 3 algebras;
- all 921 exact comparisons passed;
- validation explicitly recorded `quality_exposed: false`;
- decoder-quality execution had not yet occurred.

Aggregate semantic-validation artifact:

- run: `35084118529`;
- artifact: `10443207511`;
- artifact digest:
  `sha256:b91dd81d795822bd0f889a32b44f01b716d5b7ae097d83be5f43de95c9964bf8`.

This establishes implementation qualification on the frozen semantic-validation set. It must not be described as exhaustive validation over the complete selector domain.

## 5. Exact compile identities

### Sum-product

- canonical stream:
  `e6d34ddfdadb19af9bda02c36997a8c2dd767f4610b178f4cf3d74407445ebb4`;
- native binary SHA-256:
  `2efe52e17c6d66920b23738987818184657caf479c60c78712dff6db4a306bde`.

### Soft-tropical

- canonical stream:
  `4d8859535f7a3ce814eb6ea459a80870fd645f57af487e5b8a9f99de3d5dccb0`;
- native binary SHA-256:
  `9647b3e7fb2ee7f6f87d7e3fe6ce6779bd756e100f86f3dc13e7dc5385b5df9a`.

### Min-plus

- canonical stream:
  `3aa3f0c1d97f7428623a034b6baa20e9c7f113e830b715040dc9e1e62967b4e8`;
- native binary SHA-256:
  `dd58a7e0c59626032d8714827d9f1097a33a78fd426c7d972407b32340890bb0`.

## 6. External authoritative execution

The publication result must be generated under the protected external-execution route.

Required shape:

- 3 algebras;
- 256 logical-class work units per algebra;
- 347 selector evaluations per work unit;
- 768 unique work units total;
- 88,832 selector evaluations per algebra;
- 266,496 total selector evaluations.

Every authoritative work unit must bind:

- exact source payload;
- exact activation head;
- exact compile identity;
- algebra;
- logical class;
- complete 347-selector coverage;
- external execution substrate;
- artifact digests;
- no quality exposure during selector evaluation.

Repository write credentials are not part of the worker authority.

## 7. Required execution ordering

The publication claim depends on a strict two-phase boundary.

### Phase A — inference with quality closed

For every corpus input and each algebra:

1. evaluate all 256 logical classes;
2. construct the exact class records;
3. apply the frozen C72-derived class-selection and tie rule;
4. fix one correction record;
5. preserve the fixed-correction digest.

At completion, there must be exactly 347 fixed correction rows per algebra and no use of the injected error or conventional decoder outcome to select them.

Required state:

`C90_EXACT_CORRECTIONS_FIXED`

with `quality_exposed: false`.

### Phase B — independent scoring

Only after Phase A is immutable:

1. load the frozen injected errors;
2. verify syndrome consistency;
3. adjudicate residual stabilizer equivalence;
4. load the protected conventional artifact;
5. construct exact matched contingency tables.

Required terminal state:

`C90_TCM_MATCHED_COMPARISON_COMPLETED`.

## 8. Novelty gate

Targeted literature search through 2026-10-02 found extensive use of the `[[90,8,10]]` BB code in approximate/practical decoders, including BP/BP-OSD, beam-search, message-passing ensembles and hardware-oriented decoding.

The search also found the 2026 Krishnamoorthy et al. exact degenerate-ML result for `[[72,12,6]]`, but not an exact degenerate-ML result for `[[90,8,10]]`.

This is not sufficient to claim priority.

Before submission, perform a refreshed search for at least:

- `"[[90,8,10]]" exact degenerate decoder`;
- `"[[90,8,10]]" maximum likelihood decoder`;
- `"[[90,8,10]]" partition function decoder`;
- `"[[90,8,10]]" tensor network exact decoder`;
- all works citing Bravyi et al. 2024 and Krishnamoorthy et al. 2026;
- recent qLDPC-decoder proceedings/preprints after 2026-10-02.

A “first exact C90” statement is admitted only if that audit remains negative and the exact scope is stated.

## 9. Possible principal claim if execution succeeds

The strongest admissible claim is expected to have the following form:

> We perform exact degeneracy-aware logical-class inference for all 256 logical classes on each member of a precommitted 347-input one-sector corpus for the `[[90,8,10]]` bivariate-bicycle code, using a previously quality-blind validated reusable exact representation. Corrections are fixed before outcome labels are opened, after which they are scored by an independent stabilizer-equivalence oracle and compared on the same inputs with protected BP/min-sum/BP-OSD records.

This wording deliberately does not imply exhaustive performance over all C90 syndromes.

If a renewed prior-art audit supports priority, a qualified phrase such as “to our knowledge, the first reported exact degenerate logical-class evaluation on this `[[90,8,10]]` BB instance” may be considered. It is not currently authorized.

## 10. Results tables to populate only after closure

### Table A — exact TCM finite outcomes

| Algebra | Success / 347 | Failure / 347 | Tie diagnostics |
|---|---:|---:|---|
| sum-product | TBD | TBD | TBD |
| soft-tropical | TBD | TBD | TBD |
| min-plus | TBD | TBD | TBD |

No placeholder may be replaced before the authoritative external report exists.

### Table B — matched pairwise outcomes

For every TCM × conventional pair report:

- both succeed;
- TCM only succeeds;
- conventional only succeeds;
- both fail.

Every table must sum to 347.

### Table C — exact execution evidence

Report:

- external work units;
- successful receipts;
- selector count;
- complete class coverage;
- artifact digest inventory;
- fixed-correction digest;
- scoring report digest.

### Table D — resource measurements

Engineering measurements may include:

- evaluator wall time;
- peak RSS;
- external host class;
- worker parallelism;
- total CPU-hours.

These are measurements of the implementation, not decoder-complexity theorems and not cross-method performance comparisons unless measured under a controlled common protocol.

## 11. Figures

1. **C90 exact inference pipeline:** syndrome → 256 class evaluations → fixed correction → later scoring.
2. **Quality firewall:** clearly show that injected error/conventional outcomes are unavailable during Phase A.
3. **Selector decomposition:** 41 independent syndrome coordinates + 8 logical coordinates.
4. **Compiled object identity panel:** three exact algebras and canonical/native identities.
5. **Matched-outcome mosaic:** only after final results exist.
6. **C18 → C72 → C90 representation frontier:** structural context without fitting a scaling curve.

## 12. Required interpretation

The paper should distinguish:

- exact inference semantics;
- finite-corpus decoder quality;
- implementation resource consumption;
- asymptotic decoder complexity;
- practical real-time usefulness.

Only the first two are primary scientific outcomes of this campaign.

Even a favorable C90 finite result would not establish:

- threshold;
- pseudo-threshold;
- family-level decoder superiority;
- practical real-time performance;
- circuit-level C90 performance;
- accelerator advantage;
- asymptotic tractability;
- general superiority over BP-OSD.

## 13. Closest comparison literature

Required references include:

- Bravyi et al. 2024 for the BB code family;
- Roffe et al. 2020 and Panteleev & Kalachev 2021 for BP/OSD qLDPC context;
- Ferris & Poulin 2014;
- Bravyi, Suchara & Vargo 2014;
- Chubb 2021;
- Piveteau, Chubb & Renes 2024;
- Krishnamoorthy et al. 2026, arXiv:2608.25545;
- current practical C90 decoder literature, including beam-search and correlated/message-passing approaches.

## 14. Reproducibility package

The final public package should contain:

- exact source revision;
- source-payload digest;
- compile receipts and identities;
- external execution manifest;
- 768 receipt inventory;
- raw semantic shard receipts;
- fixed-correction object;
- matched-comparison report;
- scripts that independently verify all digests and coverage;
- no repository mutation credentials;
- a one-command verification path that does not rerun the heavy computation.

Where raw selector streams are too large for the paper repository, publish them in an immutable research artifact store and retain digests/manifest in Git.

## 15. Failure outcomes remain publishable evidence

If the external campaign exposes a semantic discrepancy, the paper must not silently disappear or repair the scientific definition post outcome.

Admissible outcomes include:

- exact C90 inference completes and is scored;
- a validated representation/evaluator mismatch is discovered;
- external exact execution is operationally infeasible under the chosen resource allocation but no mathematical infeasibility is inferred.

A semantic counterexample would feed back into Paper A and is scientifically more important than preserving the planned C90 headline.

## 16. Submission gate

This manuscript may become a submission candidate only when:

- all 768 external units are verified;
- all selector coverage is exact;
- all fixed corrections are assembled before quality exposure;
- independent scoring passes;
- matched tables reconcile exactly;
- external evidence is durably archived;
- a renewed C90 prior-art audit is complete;
- the manuscript contains no result derived from the retired GitHub-hosted selector computations;
- Paper A's compilation-correctness theorem is either proved here or cited from a finalized companion manuscript.

## 17. Current disposition

`WAITING_ON_AUTHORITATIVE_EXTERNAL_C90_RESULT`

Writing may proceed for Introduction, Methods, Related Work, Exactness Protocol and Reproducibility.

Results, Discussion and priority language remain gated.
