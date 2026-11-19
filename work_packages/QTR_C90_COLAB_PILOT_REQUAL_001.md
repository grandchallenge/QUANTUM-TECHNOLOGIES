# QTR-C90-COLAB-PILOT-REQUAL-001 — first exact native shard and compute envelope

Status: `EXACT_REMOTE_PILOT_COMPLETED__QUALITY_BLIND__BULK_FEASIBILITY_NOT_ESTABLISHED`

Observed: 2026-11-19. This is an engineering resource and provenance review; it is **not a new decoder-quality result**.

## Scope and exact identities

- Experiment `QTR-C90-EXACT-DECODER-001`, frozen activation `0c1f5591a097adc285dec4cbfc320eeebd2c65d3`.
- Original unchanged scientific/external runner `675865123437c3d6c908c7a3af337fd4023c5d0b`.
- First preselected algebra `min_plus_hamming`, logical class `0`, all 347 frozen C90 selectors.
- Original compile ZIP artifact `10442143252`, SHA-256 `6b9c94bd62cd4b3818396bc2c48b66cfe63958d37ce8d5ab2b846d0fb701d38f`; exact native binary SHA-256 `dd58a7e0c59626032d8714827d9f1097a33a78fd426c7d972407b32340890bb0`.
- Actual Google Colab High-RAM CPU session `gcl-qtr-c90-highmem-preflight-20261119`, provider instance `m-hm-usc1c0-2ipa4z37zl6i0`, with 8 logical CPUs, approximately 51 GiB RAM. The experiment was not executed on CHAD or GitHub Actions.
- Input upload was chunked and independently checked against the whole ZIP SHA-256. The native compiled object and original source blob hashes were checked on Colab **before** execution.

## Verified remote outcome (quality blind)

The native evaluator finished with exit status 0, and the custodian read back the five finished artifacts (returned host storage only):

| Immutable file | SHA-256 |
|---|---|
| 347-row `rows-min_plus_hamming-class-0.jsonl` | `d186b8392bbfb6aedf03ddb9cc1474486c7b4a4090da739a7e6f6e2c3b0250cc` |
| `receipt-min_plus_hamming-class-0.json` | `ee57897c39b8ea35fa9a5a3949a2ad711d888d9287c4fb34e9538eb111025f26` |
| `external-shard.json` | `8ecfb5b23dde0a84e56d25e7f6af8d7c07fd90211acea2c5a46f477018b30909` |
| `time.txt` | `29e2296cf5938a727d479597e43713b45016c29da109dee118c0f1e980cfd372` |
| `worker-state.json` | `a203053d178dfac76345de4428dec3ddb58c335945e872d5b217c40c8ad4c156` |

The native JSONL parses as **347 distinct ordered input-selector records**, with frozen global selector indices `0, 256, ..., 88576`. Every row and each terminal receipt says `quality_exposed=false`. The receipt specifically records `corrections_fixed=false`, `independent_scoring_performed=false`, and `matched_comparison_performed=false`. Neither decoder success nor corrections were evaluated by the quality-blind receipt verifier.

Exact verification command (requires the five returned private files):

```bash
python3 scripts/verify_qtr_c90_colab_pilot_001.py \
  --returned-dir "$HOME/.local/share/gcl-qtr-evidence/2026-11-19/colab-preflight/returned-class-0"
```

The verification was executed on CHAD. Two negative tests deliberately corrupted the rows and marker, and both were rejected by immutable SHA-256 gates. The immutable original five-file set passed.

The Colab session ended after the result download. The owner-bound custodian's final log reads `OWNED_SESSION_RELEASE_CONFIRMED` and `CUSTODIAN_COMPLETED` at **2026-11-19T14:03:42Z**, with no original-session assignment surviving in the subsequent Colab readback.

## Empirical resource measurement

The GNU-time record says:

| Metric | Observed |
|---|---:|
| Native evaluation elapsed wall time | **1:36:47 (5,807 s)** |
| User CPU time | **5,802.92 s** |
| CPU utilization | **99% of one CPU core** |
| Maximum resident memory | **6,112,280 KiB ≈ 5.83 GiB** |
| Complete selector records | **347** |
| Average records per hour, this shard | **215.1** |

One class/algebra shard is exactly 347 selector evaluations. Under the strictly counterfactual assumption that the other **767 shards** consume the same time as this first min-plus shard:

- full 768-shard campaign would consume approximately **1,238.8 native worker CPU-hours**;
- with five independent workers and sufficient CPU throughput this is approximately **247.8 wall-hours**, before data transfer, resumption, scheduling, host contention and cleanup;
- at the **pilot-observed** 0.26 Colab compute units/hour for a High-RAM CPU session, the counterfactual costs approximately **64.4 CU**, before overhead.

The Colab account balance readback later on November 19 was **63.11 CU**, with one unrelated L4 assignment consuming additional balance. Thus the full work is **not safely budget-qualified** on this one-shard extrapolation. Class-specific/algebra-specific costs may be significantly different. The five-worker figure is a memory-envelope **upper bound**, not measured simultaneous scaling or a guaranteed 8-core efficiency figure.

## Mandatory next executable work

1. Preserve all three exact native compile ZIPs and the validation ZIP beyond their announced December 15 expiration; on CHAD the three large original archives and the validation ZIP have already been SHA-256 verified locally. Off-host durable preservation remains open.
2. Perform bounded quality-blind *cross-algebra* and *parallel-throughput* calibration using Colab as first substrate; report full resource/cost evidence and refuse unauthorized batch fan-out when it cannot fit quota/lease.
3. Requalify 768-shard host/runtime/lease/cost plan, including external compute if Colab's capacity is inadequate. Any future performance optimization must preserve frozen semiring exactness and undergo fresh source/head validation.
4. Independently review provenance-aware conventional replay recovery [PR #129](https://github.com/grandchallenge/QUANTUM-TECHNOLOGIES/pull/129); its four recovery tests pass on the actual authenticated October ZIP but historical workflow-routing CI on its **old execution base** is not green. The protected original August ZIP has not been recovered.
5. After **all 768** source-bound external class/algebra shards finish, fix all 347 corrections per algebra, then and only then independently score, complete all nine matched comparisons and consider C90 quality claims.

## Explicit nonclaims

No C90 decoder success count, correction validity, matched comparison, threshold, runtime-speedup over alternatives, globally optimal induced width, scaling law, Paper B submission authority or scientific certification follows from the completed first pilot.

The scientific state is exactly **1 of 768 shards**, **347 of 266,496 selector evaluations**, with quality concealed. This is a successful native-execution-path validation and one measured resource sample.
