# QTR-C90-RESOURCE-ENVELOPE-001

Status: **AUTHORIZED CALIBRATION — PRE-OUTCOME FREEZE**

Protected base: `c5719a623310432c4e97a5863428176ff739cbd7`

Authority:
- Council: #100
- execution docket: #102
- Human Steward authorization: #100 comment `5389645111`
- Council Referee recommendation: #100 comment `5389473992`
- protected predecessor readback: #101 comment `5389715147`

Manifest payload:

`d64b770f5cc1fb4c8a0ca8e89dad6d8020a01ae38f2c6868ff3028f53c441651`

## Scientific question

For the same frozen finite C90 inference problem and exact CPU-reference semantics, determine whether the historical deterministic compilation stopping rules are materially conservative, approximately aligned with, or non-decisive relative to a conservatively calibrated physical execution envelope.

This is a calibration audit. It does not reopen or amend the predecessor result `C90_PREDECLARED_EXACT_STRUCTURAL_FAMILY_EXHAUSTED`.

## Frozen sensitivity grid

Exactly `{1x,2x,4x,8x}` for:
- factor/constraint evaluations from base `2^27`;
- compilation AOP from base `2^31`.

A coordinate is:
- `CERTIFIED_PASS` only when the exact factor count and conservative AOP upper bound both clear it;
- `DEFINITE_FAIL` when the exact factor count or mandatory AOP lower bound crosses it;
- otherwise `INDETERMINATE`.

Clearing a historical *definite blocker* is not the same as obtaining a certified pass. In particular, the predeclared arithmetic is expected to distinguish S2/S3 at the `2x` AOP coordinate when lower and upper bounds straddle that coordinate.

## Representation audit

No C90 value table or symbolic node set may be materialized.

The static phase computes:
- exact planned factor-table liveness from frozen scopes/order;
- exact maximum planned individual output-table cardinality;
- protected intern-attempt / retained-node upper bounds without relabeling them as exact retained counts;
- a conservative canonical-serialization upper bound derived from frozen node schemas and index/integer ranges.

Every representation quantity carries an explicit type: `exact`, `lower_bound`, `upper_bound`, or `unknown`.

## Hosted CPU-reference probe

A fresh CPU-only hosted session may measure direct-host `MemTotal` / `MemAvailable`, Python implementation/version, pointer width, object sizes, and bounded representative node-store/table allocations.

The probe allocation ceiling is `min(512 MiB, 5% MemTotal)`. GPU/TPU memory is excluded.

The probe is calibration only. It may not compile C90 or run frozen-307 validation.

## Candidate physical-envelope gate

A method can receive a physical-envelope candidate only if:
1. it has a certified cumulative-work sensitivity coordinate;
2. the predicted resident upper proxy is at most 70% of total RAM;
3. at least 2 GiB total-RAM reserve remains;
4. fresh `MemAvailable` covers predicted peak plus 2 GiB;
5. runtime index support is sufficient;
6. serialized storage is conservatively bounded.

Failure of an upper bound to fit does **not** prove physical impossibility. It leaves physical feasibility indeterminate and may support only representation-bound dominance.

## Explicit exclusions

No full C90 materialization, frozen-307 validation, cap adoption, new structural method, adaptive order search, approximation, learned decoding, accelerator-native QEC, runtime/memory superiority claim, family/asymptotic result, intrinsic-intractability result, `QEC-CIRCUIT-003`, or `QLDPC-FORGE` authority is created here.

No new calibration outcome has been inspected at this freeze point.
