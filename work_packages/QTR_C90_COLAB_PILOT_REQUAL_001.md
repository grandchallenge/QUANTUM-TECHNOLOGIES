# QTR-C90-COLAB-PILOT-REQUAL-001 — first two exact native shards and compute envelope

Status: `TWO_EXACT_REMOTE_CALIBRATION_SHARDS_COMPLETED__QUALITY_BLIND__BULK_FEASIBILITY_NOT_ESTABLISHED`

Observed: 2026-11-19 through 2026-11-20. This is an engineering resource and provenance review; it is **not a new decoder-quality result**.

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

## Second independently completed real exact C90 shard (2026-11-20)

The separate frozen `sum_product_bsc_p_0_1` / logical class `0` ran on a second Google Colab High-RAM CPU instance (`m-hm-use1c0-29f63t6nszip8`) under unchanged source `675865123437c3d6c908c7a3af337fd4023c5d0b` and activation `0c1f5591a097adc285dec4cbfc320eeebd2c65d3`. Its original compiled ZIP was artifact `10442610733`, SHA-256 `678b39b09023f0adb854a9b0cc28ce0b85c9379e149b0103cfe94a7e4ad0fece`, source-verified and whole-ZIP hash-verified before execution. All 134 input chunks were transferred with individually checked SHA-256.

The remote native executor completed **347/347** frozen records, returned the five original files to CHAD, and the custodian confirmed exact owned-session release at **2026-11-20T03:12:37Z**. Independent local readback verified every terminal receipt, frozen selector index order `0,256,...,88576`, algebra/class, row count, inter-file hashes, and all quality-blind/no-scoring flags. Files remain private at `~/.local/share/gcl-qtr-evidence/2026-11-19/colab-sumproduct-pilot-002/returned-class-0/`.

| Returned file | SHA-256 |
|---|---|
| 347-row `rows-sum_product_bsc_p_0_1-class-0.jsonl` | `170d2bd56ed19120ad4a58e9ae27cbcf671c2c1abdf013412c4a78c87737631c` |
| `receipt-sum_product_bsc_p_0_1-class-0.json` | `142b3fa01c1f61b2c0b2ff4f888510dd4c6e987bd5aea9e13f5f175131e0a5ed` |
| `external-shard.json` | `10827d545c47c05682f24ad7b5e752a7dea15b949194a4b5855bb3e6f6809fe0` |
| `time.txt` | `c2bba07af312eebb933275dc5819c2dcc4838ac5fb61f16061eab84020c488d7` |
| `worker-state.json` | `1fb87e0919cd30468981b4f53b922d3c0140ac8f3b156ee5509d1b02dfc53713` |

**Measured** elapsed wall time **3:30:16 (12,616 seconds)**, user CPU **12,585.32 seconds**, peak resident memory **6,112,264 KiB ≈5.83 GiB**, native exit status 0. No newly computed exact-decoder success rate, corrections, scoring or matched comparisons were exposed.

The two different class-0 runtimes show that **one algebra is not a safe proxy for another**. If, and only if, all 256 classes per algebra took the observed class-0 times and five workers scaled linearly without contention, **min-plus and sum-product alone** would require `(5807+12616)*256/3600 ≈ 1,310.08 CPU-worker hours`, or `262.02` Colab instance hours at five-way concurrency. At the previously observed High-RAM CPU rate `0.26 CU/hour`, that two-algebra scenario would cost **~68.12 CU before overhead**, compared with a November 20 balance around **55.5 CU**. This conditional extrapolation *excludes the third algebra*, upload costs and variability; it is **not an unconditional lower bound** or a measured parallel-throughput result. No full 765-shard fanout is budget-qualified by these two measurements.

The third original algebra `soft_tropical_base_2` remains a separate live quality-blind calibration on exact Colab instance `m-hm-euw4c0-3ehawiq2t82h9` from original ZIP `10442242798`, SHA-256 `c4fa41b35ad5e88e4e58ca9816c78dd296d170a5d86cf9087c51b4fdcce138e8`, under its separate **2026-11-20T15:00:00Z** owned-session lease. Off-path optimized arithmetic candidates may be tested for exact equivalence, but original science/receipts remain unmodified and no speedup is admitted without controlled real-graph replay.

The public-main conventional *baseline evidence intake*, distinct from new exact decoder quality, is now admitted via [PR #135](https://github.com/grandchallenge/QUANTUM-TECHNOLOGIES/pull/135), protected merge `4435955438ddd003e95a90657cf6259313dc524b`. The older [PR #129](https://github.com/grandchallenge/QUANTUM-TECHNOLOGIES/pull/129) retains a future historical-scoring adapter and is not a prerequisite for verifying existing conventional data; scoring is still blocked until all C90 corrections have been fixed.

## Completed six-process CPU scaling trial (2026-11-20)

This is **source-bound engineering evidence**, not completion of the scientific C90 class surface. The existing original soft-tropical class-0 evaluator and independent off-path arithmetic comparison continued unchanged. We added **four separate processes using the original frozen C90 native evaluator** for logical classes 1–4, each evaluating exactly its first eight source-generated selectors. No other Colab session was allocated, and no experiment inputs or original scientific code changed.

- Original source head: `675865123437c3d6c908c7a3af337fd4023c5d0b`; activation head: `0c1f5591a097adc285dec4cbfc320eeebd2c65d3`.
- Frozen soft-tropical compiled graph SHA-256: `9647b3e7fb2ee7f6f87d7e3fe6ce6779bd756e100f86f3dc13e7dc5385b5df9a`; frozen evaluator executable SHA-256: `a062b8a1808313e160f5604398ac5962645b5000479a3b9e4fd648e1e53e6ec3`.
- Exact existing Colab High-RAM CPU instance: `m-hm-euw4c0-3ehawiq2t82h9`; eight usable CPUs, no cgroup CPU quota, 50.99 GiB physical RAM.
- With six live C90 evaluator processes, each used approximately 99.7–99.8% of one CPU. Observed load was 5.8–6.2 and **31.54 GiB remained available**. Colab's rate was unchanged at **0.26 compute units/hour**.
- All **32/32** additional selector records were independently checked for frozen ordering, coordinates, algebra, row status, source hashes, semantic quality-blind flags, and immutable file digests.

| Additional original-evaluator job | Selectors verified | Native elapsed time | Peak RSS |
|---|---:|---:|---:|
| Logical class 1 | 8 | 253.725 s | 6,112,156 KiB |
| Logical class 2 | 8 | 273.217 s | 6,112,396 KiB |
| Logical class 3 | 8 | 283.473 s | 6,112,200 KiB |
| Logical class 4 | 8 | 260.374 s | 6,112,256 KiB |

In a count-only sample of the two incumbent processes (08:05:38–08:06:41 UTC), **6 rows / 63 s = 0.09524 rows/s** were observed. A later, loaded 160-second sample with the four additions recorded **28 rows / 160 s = 0.17500 rows/s** across all processes, an **observed 1.84× aggregate increase**. These are not matched-selector or steady-state crossover samples: inputs differ, workers started at different times, and some completed during the window. Therefore **1.84× is an observed interval result, not a guaranteed six-worker campaign speedup or efficiency bound**.

CHAD's independent receipt custodian unpacked and verified 19 files including the original short-batch selector inputs, quality-blind raw outputs, GNU-time reports, individual terminal states, source preflight and grouped manifest. Owner-local archival ZIP `~/.local/share/gcl-qtr-evidence/2026-11-20/c90-sixcore-throughput/C90_SIX_CORE_QUALITY_BLIND_2026-11-20.tar.gz` has SHA-256 `e28a21461787b40a795b8cb2cf00ba654bc278fb090e888b4b83a0731dd62d07`. Raw exact values are **not** published in this record. See [the original exact execution evidence in QTR #114](https://github.com/grandchallenge/QUANTUM-TECHNOLOGIES/issues/114#issuecomment-7034161867).

**Consequence for subsequent bounded jobs:** The existing 7-GiB-per-process guard, 8-GiB host reserve, exact-head input verification and provider lease remain mandatory. On the observed shape, **four additional original evaluator workers alongside two incumbent workers** are mechanically viable without higher-RAM hardware. A fresh session may qualify up to six total workers only after checking available CPU, RAM, output custody, actual performance under its own workload and budget. The existing full 768-shard unbounded fanout is **not authorized** by this test. These eight-selector fragments do **not** count as completed 347-selector scientific shards.

## Mandatory next executable work

1. Preserve all three exact native compile ZIPs and the validation ZIP beyond their announced December 15 expiration; on CHAD the three large original archives and the validation ZIP have already been SHA-256 verified locally. Off-host durable preservation remains open.
2. Cross-algebra single-class timings and the bounded six-process original-evaluator utilization trial are now recorded above. For the next **actual complete-shard** batch, use a separate owner-bound, source-locked lease plan with four-to-six workers only after requalifying total memory, output custody, actual matched-task throughput and available compute-unit budget. Do not extrapolate the short-run 1.84× interval blindly.
3. Requalify 768-shard host/runtime/lease/cost plan, including external compute if Colab's capacity is inadequate. Any future performance optimization must preserve frozen semiring exactness and undergo fresh source/head validation.
4. The conventional **baseline evidence intake is completed on protected main** via PR #135, including six tests and the genuine October replay ZIP. A separately governed future scoring adapter on historical PR #129 still requires admissible execution integration after exact corrections are fixed. The original August ZIP has not been recovered.
5. After **all 768** source-bound external class/algebra shards finish, fix all 347 corrections per algebra, then and only then independently score, complete all nine matched comparisons and consider C90 quality claims.

## Explicit nonclaims

No C90 decoder success count, correction validity, matched comparison, threshold, runtime-speedup over alternatives, globally optimal induced width, scaling law, Paper B submission authority or scientific certification follows from the completed first pilot.

The verified scientific state at this review is **2 of 768 shards**, **694 of 266,496 selector evaluations**, with quality concealed. This establishes the exact native-execution path across two different algebras and two measured resource samples; no full campaign performance or quality claim follows.
