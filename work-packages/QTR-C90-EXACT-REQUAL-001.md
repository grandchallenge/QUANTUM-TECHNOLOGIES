# QTR-C90-EXACT-REQUAL-001 — C90 exact resource requalification

Status: `AUTHORIZED_MANIFEST_FIRST__CANDIDATE_ONLY`

Authority:
- Council contract: Issue #91.
- Referee recommendation: #91 comment `5336617970`.
- Human Steward authorization: #91 comment `5336703933`.
- Execution docket: Issue #92.
- Protected starting `main`: `8b52c71c916e9eea4a4c76309846cdb2b4a7d55a`.

## Question

On the already-protected C90 representation and deterministic min-fill order, does the existing exact CPU-reference compiler satisfy every retained deterministic resource cap and a conservative fresh-host memory/storage envelope; and, only if it does, can one exact C90 compilation and the frozen 307-selector semantic validation complete?

A negative or indeterminate Phase-M result is a valid terminal result.

## Frozen substrate

The experiment consumes the protected `QLDPC-SCALE-001B` C90 rung without changing the code, source, bases, factor scopes, selector semantics, order, or algebra.

The source-reported object remains `[[90,8,10]]`; distance 10 is provenance only. The protected deterministic min-fill width is 25, with predicted peak joint table `2^26 = 67,108,864`.

The protected disabled preparation candidate `configs/compute/qtr_c90_exact_candidate_matrix.json` is not edited. It remains an immutable provenance object. Scientific execution, if reachable, is controlled by the new manifest-first state machine.

## Resource amendment

Exactly one inherited deterministic cap is changed for this finite C90 experiment:

- historical peak joint table: `2^20`;
- authorized C90-only peak joint table: `100 * 2^20 = 104,857,600`.

The following remain unchanged:

- factor-table entry evaluations per algebra: `2^27`;
- retained canonical nodes/entries per algebra: `2^22`;
- canonical serialized compiled object per algebra: `512 MiB`;
- compilation AOP events per algebra: `2^31`.

Passing the amended peak-entry cap does not override any unchanged cap.

## Phase M

The first operation is non-materializing structural replay. It reconstructs the protected C90 object, verifies all protected source/basis/scope/order digests, verifies the frozen 307-selector set, computes exact structural counts implied by the existing compiler, computes an exact mandatory lower bound on compilation AOP events, and checks deterministic caps decidable without full compilation.

Quantities remain separated as exact structural counts, conservative engineering byte bounds, and observed runtime measurements.

If an unchanged deterministic cap is already crossed exactly, Phase M terminates as `C90_MEMORY_STORAGE_QUALIFICATION_FAILED` before host-memory calibration. This is a resource-envelope result, not a claim that the C90 representation is intrinsically intractable.

If exact structural accounting does not terminate the experiment, bounded CPython calibration runs in a child process that exits before Phase X. Any material byte term that cannot be conservatively bounded yields `C90_MEMORY_STORAGE_QUALIFICATION_INDETERMINATE`.

A memory pass additionally requires predicted peak resident bytes <= 70% of fresh total host RAM, at least 2 GiB total-RAM reserve, fresh `MemAvailable >= predicted_peak + 2 GiB`, no device memory, and no assumed swap, compression, allocator reuse, or GC timing.

## Phase X

Phase X is mechanically unreachable unless the exact Phase-M pass receipt is bound to the same source commit, manifest digest, and hosted session.

Fixed algebra order:

1. `sum_product_bsc_p_0_1`;
2. `soft_tropical_base_2`;
3. `min_plus_hamming`.

Each algebra runs in its own fresh subprocess. `MemAvailable` is reread immediately before each materializing subprocess. Failure stops the sequence. There is no order switch, representation rewrite, approximation, answer cache, backend change, retry, or post-outcome cap increase.

The scientific backend is CPU reference. T4 availability from the preparation stage does not enter the memory budget and does not authorize accelerator execution.

## Frozen validation

Validation can begin only if all three exact compilation receipts are green.

The selector set is zero, 49 unit selectors, all-ones, and 256 distinct non-reserved hash-generated selectors. The seed is exactly `QLDPC-SCALE-001B::90::selector-validation::v1`; total 307 selectors.

Equality is checked against the independent fixed-selector oracle for all three exact algebras. A success is exact only on this frozen set; it is not an all-`2^49` selector theorem.

## Hosted execution

The complete hosted path is:

```bash
bash scripts/bootstrap_colab_runner_env.sh --rebuild
bash scripts/run_qtr_c90_exact_requal_colab.sh
```

The host script uses a fresh CPU Colab session, deterministic source payload, rendered session-bound job receipt, authoritative artifact readback, and teardown.

Do not run the hosted command merely because the static artifact exists. Inspect the static Phase-M adjudication first. A terminal static failure or indeterminate result makes physical calibration and Phase X unnecessary and prohibited.

## Claim boundary

This experiment does not authorize or imply decoder-quality evidence, runtime/memory/hardware superiority, global treewidth or asymptotic/family scaling, C108/C144/C288/C784 reruns, approximation or representation search, accelerator-native QEC, conventional-decoder rebenchmarking, threshold or circuit-level work, `QEC-CIRCUIT-003`, learned/autonomous decoder or code search, or `QLDPC-FORGE`.
