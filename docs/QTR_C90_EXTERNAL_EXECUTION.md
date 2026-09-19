# QTR-C90 external execution adapter

This package moves any retry or successor of the large QTR-C90 exact-decoder batch off GitHub-hosted scientific execution while preserving the frozen C90 subject.

The currently in-flight GitHub Actions runs are grandfathered and are not cancelled by this migration:

- min-plus: `35402858866`;
- sum-product: `35402858883`;
- soft-tropical: `35402858934`.

## Boundary

GitHub remains the repository authority, protected integration route, provenance surface, and returned-evidence verifier. It does not execute the 768 scientific work units in the successor route.

The external executor receives no repository write credentials and cannot merge, certify, promote, publish, or mutate protected state.

Provider selection is operational. A final execution manifest is materialized before launch and binds the selected provider class and adapter, the exact source payload digest, the frozen C90 orchestration commit, all three exact compile identities, the 347-input corpus, all 256 logical classes, retry semantics, and claim boundaries.

## Materialize an execution

Prepare a source payload from exact orchestration commit:

`e81eaf49bf92e8f4830000d4b32e6be04f64b219`

Compute its SHA-256, then run:

```bash
python scripts/qtr_c90_external_execution.py materialize \
  --provider-class slurm \
  --adapter gcl-slurm-v1 \
  --source-payload-sha256 <64-hex-digest> \
  --parallelism 48 \
  --output /path/to/qtr-c90-external-run
```

The command emits one exact `MANIFEST.json`, an `INDEX.json`, and exactly 768 immutable job envelopes.

No provider is selected by this repository package. The example provider value is illustrative; the actual provider and adapter are locked when the execution is materialized.

## Work-unit contract

Each work unit is exactly one pair:

`(algebra, logical_class)`

for three frozen algebras and logical classes `0..255`. Every unit evaluates all 347 frozen inputs for its class.

The worker uses the exact source payload and corresponding frozen native compile identity, generates the 347 selector rows, runs the exact native evaluator, then runs the frozen semantic shard validator. It returns native rows, the semantic shard receipt, and a runtime receipt.

A provider may retry an operationally failed unit under the frozen retry policy. It may not alter the algebra, class, corpus, source, compile identity, or scientific semantics.

## Verify readmission evidence

The external provider returns one generic `GCL_EXTERNAL_EXECUTION_RECEIPT` per work unit. Receipt filenames end in `.receipt.json`.

Run:

```bash
python scripts/qtr_c90_external_execution.py verify \
  --manifest /path/to/run/MANIFEST.json \
  --receipts /path/to/receipts \
  --artifact-root /path/to/materialized/artifacts
```

Verification fails closed unless all 768 unique work units are successful and bind the exact manifest, source payload, provider identity, retry policy, artifact digests, and frozen claim boundaries. When artifacts are materialized, the QTR semantic shard receipts are independently inspected for exact activation head, algebra, class, 347-row coverage, compile identity, and no quality exposure during shard execution.

Aggregation and independent scientific scoring remain downstream operations. Complete receipt verification alone does not promote a result.

## Programme dependency

The QTR binding currently points to MATH-PROGRAMME PR #1028 exact candidate `d5f9d2da3b0ace24d9116a437e097251ab4368b7`. Before this QTR package can become effective, that candidate must be admitted on protected MATH-PROGRAMME state and this binding must be replaced with the exact protected merge/readback identity and exact Programme profile blob. The materializer enforces this: while the binding is pending, executable manifest generation fails closed.

This dependency is deliberately fail-closed. It does not block the already in-flight C90 execution.
