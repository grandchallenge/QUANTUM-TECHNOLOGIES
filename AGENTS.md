# Agent instructions

**Engineering architecture and reliability:** Adopt [GCL-ENGINEERING-001 v1.0.0](https://github.com/grandchallenge/gcl-standards/blob/2a3cfed9419ba9b74eeaaee70b9db8c3f47f3c9b/standards/GCL-ENGINEERING-001.md), pinned at protected `gcl-standards` commit `2a3cfed9419ba9b74eeaaee70b9db8c3f47f3c9b`. Engineering agents own architecture, necessity, integration, tests, deploy/readback and retirement; reuse GitHub and existing components before inventing infrastructure. Do not duplicate workflow authority or mistake CI/merge for live completion. Preserve this repository's superior, reserved, and domain-specific policies. Cross-repository adoption requires explicit readback, never assumption.

QUANTUM-TECHNOLOGIES follows `GCL-AGENT-STAFFING-001` version `1.0.0` at
gcl-standards commit `94e94ddf2d4158494c084d0acaff04009971c16c`.
One Codex system may implement, staff distinct non-reserved logical audit
passes, merge through satisfied protected controls, and read back the result.
Authoring-system Adversary and Referee passes are `non_authoring_read_only`.

## Compute routing — existing GCL Colab runner by default

For every substantial QTR experiment, use Colab as the **first actual execution substrate**, not CHAD, GitHub Actions, or a merely documentary external-compute handoff. This applies automatically: the Human Steward does not need to repeat the runner choice.

The CHAD host owns source preparation, data/receipt transfer, the installed `colab` CLI and `gcl_commander.colab_supervisor`; use the existing QTR Colab scripts and governed frozen workloads rather than inventing another runner. Commit to exact job/source/input identities, preflight observed hardware, compute-unit and lease budget, incremental durable shards/checkpoints, host-side SHA-256 validation, and owned-session stop/readback. Keep local execution for small tests and infrastructure checks.

CPU-bound native C90 inference **does not become a GPU workload just by requesting a GPU**. Size an actual Colab CPU/high-RAM host for the frozen 7 GiB-per-worker plus reserve envelope, or use a compatible explicitly governed external provider if Colab capacity/lease cannot meet it. Verify quota and high-RAM availability before the first bulk shard. The original evaluator retains that envelope. The separately qualified compact storage route, once its activation contract is protected, may use the exact qualified compact binary with a 3 GiB sampled/terminal worker ceiling and unchanged 8 GiB available-host reserve (at least 11 GiB available at launch), one worker per owned provider session. Try Colab high-RAM CPU first; following a recorded unavailability, Standard CPU is eligible only when actual post-stage preflight and runtime guards pass. This is a bounded operational envelope, not a scientific limit or authorization for unqualified builds, relaxed reserves, new providers, or prolonged CHAD bulk execution. See `docs/QTR_C90_COMPACT_BATCH_ACTIVATION.md`. The frozen C90 campaign remains governed by [issue #114](https://github.com/grandchallenge/QUANTUM-TECHNOLOGIES/issues/114), its original activation head, verified compile artifacts, the exact 347-input corpus and 3 × 256 logical-class shards. Do not consume historical GitHub-hosted selector outcomes as final scientific results, change the frozen decoder, or expose quality before all corrections are fixed.

An unavailable Colab runtime triggers evidence-driven recovery or a correctly approved external-provider fallback, **not** automatic prolonged CHAD CPU or a massive Actions fan-out. Colab availability, job submission, exact source execution, checkpoint return, receipt validation, and release are different evidence stages; report them separately. This operational default conveys no new scientific or certification authority.

This repository has no mathematical-certification authority. Automation may
not write directly to protected branches, manufacture reserved authority, or
infer claim promotion, certification, safety, or deployment authority from CI
or integration.
