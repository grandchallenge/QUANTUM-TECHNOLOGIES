# QTR-C90-EXACT-DECODER-001 — exact 347-case TCM matched comparison

## Status

`AUTHORIZED_EXECUTION__PREOUTCOME_FREEZE`

Authority is Council #113 and execution docket #114. The protected starting main is
`aa53dc3c0e99c39f766f4ccb0c0d0629cd9093db`. Human Steward authorization is
#113 comment `5405533756`.

This work package has one finite scientific endpoint:

> Compile the frozen exact C90 TCM representation, validate it without using
> C90 decoder-quality outcomes, decode all 347 frozen C90 inputs, independently
> score the returned corrections, and compare them per input with the already
> protected BP / BP-OSD records.

Resource characterization is engineering evidence, not the scientific endpoint.

## Protected predecessor

`TCM-C72-INTERFACE-001` is protected at merge
`aa53dc3c0e99c39f766f4ccb0c0d0629cd9093db` with outcome
`C72_TCM_SHARED_DECODER_INTERFACE_CERTIFIED`.

Its durable receipt is `evidence/TCM-C72-INTERFACE-001-report.json`.

## Frozen C90 surface

The source-reported code is `[[90,8,10]]`; distance 10 remains provenance only.

Protected exact dimensions:

- `rank(H_X) = rank(H_Z) = 41`;
- logical dimension `8`;
- selector rank `49`;
- exactly `256` logical classes per syndrome;
- protected deterministic min-fill induced width `25`.

The canonical pre-measurement manifest is
`registry/qtr-c90-exact-decoder-001-manifest.json`, payload
`8c0fd54d9131434e17273f8c9aea407cb132c4511aad38dda8c5cb66a6441294`.

The frozen corpus has exactly 347 inputs, digest
`b053a27a9c346832d6008987e204c88162dc1797e0367b38705861049059e086`.

The conventional anchors on those same 347 inputs are reused, not rerun:

- `BP_MIN_SUM`: `200/347`;
- `BP_OSD_CS_7`: `211/347`;
- `BP_SUM_PRODUCT`: `171/347`.

## Exact decoder semantics

The decoder receives only full `H_Z` syndrome and frozen channel metadata.
Injected error is unavailable until independent scoring.

For every syndrome, all 256 logical classes are represented exactly under:

- sum-product BSC `p=0.1`;
- soft tropical base 2;
- min-plus Hamming.

Winning class, class tie, and within-class representative semantics are inherited
unchanged from the protected TCM programme and the certified C72 bridge.

## Frozen representation

Primary representation:

`EXACT_SELECTOR_PARAMETRIC_HASH_CONSED_DAG_C90`

It is the protected selector-parametric construction already established as the
TCM shared-compilation mechanism: eliminate the 41 independent X-stabilizer
variables once in the protected deterministic min-fill order while retaining
the 49 selector coordinates as Boolean parameters.

The representation may be stored in memory or in a disk-backed exact hash-cons
store. Those are storage variants only. They must preserve the same canonical
semantic node records and root digest. No approximate representation, pruning,
beam search, post-outcome order selection, or primary complete selector-answer
cache is permitted.

## Execution sequence

1. **Preflight.** Reconstruct and verify the protected C72 predecessor, C90
   code/bases/scopes/order, 49x49 selector-functional map, frozen 307 selector
   validation set, 347-input corpus, and conventional record identities.
   Preflight must expose no C90 quality.
2. **Compile.** Build one reusable exact canonical selector-parametric DAG per
   protected algebra.
3. **Validate.** Require deterministic canonical representation identities and
   the frozen quality-blind selector controls. Injected-error success is not a
   validation input.
4. **Decode.** Produce one correction-valued exact TCM result per algebra for
   every one of the 347 corpus inputs, evaluating the complete 256-class domain.
5. **Score.** After correction fixation, independently test syndrome consistency
   and `e XOR c in Row(H_X)`.
6. **Compare.** Join by frozen corpus index to the protected conventional
   records and report `both`, `TCM-only`, `conventional-only`, and `neither`
   counts for each defined pair.

Primary sharding is frozen at 347 shards, one input per shard. A retry may repeat
only the identical scientific shard. Host capacity and parallelism may change
after an operational interruption; the scientific representation, inputs,
semantics, order, and validation set may not.

## Resource rule

The historical `2^20`, `2^27`, `2^22`, `512 MiB`, `2^31`, x100 peak-entry
amendment, and small-host retained-bound target are not scientific stopping
rules in this campaign.

OOM, scheduler timeout, unavailable compute, or storage exhaustion is
`OPERATIONAL_EXECUTION_INCOMPLETE`. It is not evidence of TCM decoder failure,
physical infeasibility, intrinsic intractability, or non-scalability.

## Terminal predicates

- `C90_TCM_MATCHED_COMPARISON_COMPLETED`
- `C90_EXACT_SEMANTIC_VALIDATION_FAILED`
- `OPERATIONAL_EXECUTION_INCOMPLETE`

Only the first defines C90 TCM quality.

## Claim boundary

Any result is a finite C90 fact only. This package creates no general decoder
superiority, family/asymptotic scaling, threshold/circuit, hardware superiority,
learned-decoder, `QEC-CIRCUIT-003`, `QLDPC-FORGE`, or autonomous-search claim or
authority.
