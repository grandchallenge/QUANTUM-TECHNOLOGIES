# QTR-TCM-C72-INTERFACE-001 — exact syndrome-to-correction bridge

## Status

Authorized execution under Council #109 and execution docket #110. This work package is part of the existing TCM-QDEC/C72/C90 lineage; it is not a new research track.

Protected starting main:

`53e2ac281eb8738e711f75b0d6be525eafab48a3`

Human Steward authorization:

#109 comment `5392408266` — `ADOPT_WITH_AMENDMENTS__AUTHORIZE_TCM_C72_INTERFACE_001_ONLY`.

## Purpose

The protected `QLDPC-SCALE-001A` result already establishes an exact C72 selector-parametric contraction object on the source-bound `[[72,12,6]]` BB instance, with exact arithmetic in three algebras and compiled-versus-independent equality on the frozen 300-selector validation set.

`TCM-QDEC-COMPARE-001` deliberately left the C72 TCM quality cell undefined because no shared syndrome-to-correction interface had been certified.

This operation closes only that missing interface.

The scientific question is:

> Can the protected C72 exact TCM class scorer be exposed as a deterministic correction-valued decoder without changing its score, logical-class choice, tie, representative, channel, or correctness semantics?

## Decoder boundary

The decoder signature is:

`decode(full_HZ_syndrome, channel_metadata) -> correction | declared_failure`

The injected error is not a decoder input. It is available only to the independent scorer after the decoder has returned a correction.

For every syndrome and each of the three protected algebras, the decoder evaluates all `2^12 = 4096` logical classes exactly. There is no logical-class pruning, beam search, approximation, early stopping, learned score, post-outcome restriction, or adaptive order search.

The decision rule remains:

- winning class: exact semiring optimum;
- class tie: lowest canonical stabilizer-coset key;
- representative within winning class: lowest Hamming weight, then lowest integer.

## Selector-coordinate bridge

C72 uses 42 protected selector coordinates, but those coordinates are not assumed to be numerically identical to the desired 30 independent syndrome bits plus 12 logical bits.

The implementation constructs the exact `42 x 42` GF(2) map from protected selector-basis coordinates to the protected functional basis:

1. the 30 independent Z-check functionals;
2. the 12 canonical logical-Z functionals.

The map must have rank 42. Its exact inverse is constructed and verified on every unit functional. Each requested syndrome/logical class is converted through that inverse before the existing selector lift is used.

## C18 control

Before any C72 decoder output is admitted, the same outer syndrome/logical-class decision bridge is instantiated on the protected C18 TCM-QDEC-003 class contraction.

It must reproduce exactly:

- all three protected decision-table digests;
- all three protected winning-class tie-set digests;
- frozen-corpus totals `263`, `262`, `226`;
- tie envelopes `[263,263]`, `[262,262]`, `[218,263]`.

Failure stops the operation before C72 quality evidence.

## C72 corpus

Use only the already-frozen COMPARE-001 C72 corpus:

- zero error;
- every one of the 72 unit errors;
- 256 deterministic SHA-derived BSC `p=0.1` errors;
- total `329` inputs;
- digest `23b49e39eafd70c9619f8837dfcb0046e13a1600cd7176d42a6018814f518050`.

The channel remains BSC `p=0.1`.

## Exact execution and sharding

The full run is intentionally not a GitHub Actions benchmark. CI performs only the C18 control and C72 static/interface preflight.

The complete C72 decoder run is executed on suitable available hardware through deterministic input-level sharding. A shard owns complete corpus inputs according to:

`input_index mod shard_count == shard_index`.

Every owned input still evaluates all 4096 logical classes. Sharding changes only scheduling, never mathematics. Worker count is therefore operational rather than scientific.

All shards are required for aggregation. The aggregate scorer regenerates the frozen corpus independently, checks syndrome consistency, and applies the exact residual row-space oracle.

## Resource-policy correction

The historical `2^20`, `2^27`, `2^22`, `512 MiB`, and `2^31` values are not scientific stopping rules in this operation. They remain historical experimental limits only.

The hosted run records actual CPU, RAM, storage, elapsed time and process diagnostics. OOM, timeout, storage exhaustion, unavailable compute, or an unsuitable host yields:

`OPERATIONAL_EXECUTION_INCOMPLETE`.

It does not establish mathematical infeasibility, physical infeasibility, or intrinsic intractability.

## Admissible outcomes

- `C72_TCM_SHARED_DECODER_INTERFACE_CERTIFIED`
- `C72_TCM_INTERFACE_SEMANTIC_EQUIVALENCE_FAILED`
- `C72_TCM_INTERFACE_CONSTRUCTION_NOT_CERTIFIED`
- `OPERATIONAL_EXECUTION_INCOMPLETE`

Decoder-quality failures on individual injected errors are valid finite C72 scientific data. They do not by themselves invalidate the decoder interface. Interface certification requires complete correction-valued execution and syndrome-consistent outputs under the frozen exact semantics.

## Downstream boundary

Only `C72_TCM_SHARED_DECODER_INTERFACE_CERTIFIED` makes a separately governed C90 exact decoder campaign eligible.

That later C90 campaign, if authorized, is intended to:

`compile -> validate -> decode frozen 347-input corpus -> matched BP/BP-OSD comparison`.

This C72 operation does not authorize C90 execution.

## Explicit exclusions

No authority is created for:

- C90 materialization or decoding;
- another C90 retained-bound refinement ladder;
- changed code, order, semiring, channel or corpus;
- approximation or pruning;
- family/asymptotic claims;
- threshold or circuit-level claims;
- hardware superiority claims;
- learned decoding;
- `QEC-CIRCUIT-003`;
- `QLDPC-FORGE`;
- autonomous search.
