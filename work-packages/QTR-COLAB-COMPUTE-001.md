# QTR-COLAB-COMPUTE-001 — Hosted CPU/GPU/TPU preparation

Status: `ENGINEERING_PREPARATION_ONLY__NO_NEW_SCIENTIFIC_EXECUTION_AUTHORITY`

Tracking issue: `#88`

Protected preparation base:

`2a53fa9ba6d18220a8469e2d5d667e003d1cdd37`

## 1. Purpose

This package prepares the qLDPC/QEC programme to use Google Colab CPU, GPU, and
TPU instances without changing any protected scientific result. It adopts the
K-DIAGNOSTICS host-orchestrated lifecycle: deterministic payload, fresh runtime,
explicit upload/execute/download/log/stop steps, fail-closed hardware validation,
durable receipts, and host-side cleanup.

The runner is engineering infrastructure. A green hosted receipt does not itself
create scientific evidence or promotion authority.

## 2. Host contract

Use Linux or WSL. The preparation pins:

- Python 3.12 for the local runner environment;
- `google-colab-cli==0.6.0`;
- `jupyter-kernel-client==0.9.0`;
- `COLAB_AUTH=oauth2` by default.

Credentials remain in the CLI/user environment and are never included in source
payloads or receipts.

Bootstrap:

```bash
bash scripts/bootstrap_colab_runner_env.sh --rebuild
source .venv/bin/activate
```

One-command hosted engineering preflight:

```bash
bash scripts/run_qtr_colab_compute_preflight.sh --rebuild
```

This command runs the independent resource-discovery matrix first and the CPU-reference
compute-envelope prequalification second. It still returns nonzero if any requested
accelerator is unavailable or fails validation; those failures are retained rather
than being silently substituted.

## 3. Runtime probe matrix

The first matrix characterizes requested Colab resources and rejects silent
substitution:

```bash
python scripts/colab_run_matrix.py \
  configs/compute/qtr_colab_runtime_probe_matrix.json \
  --dry-run
```

Hosted execution:

```bash
python scripts/colab_run_matrix.py \
  configs/compute/qtr_colab_runtime_probe_matrix.json \
  --continue-on-error
```

The `--continue-on-error` flag is appropriate for this resource-discovery matrix
because accelerator quota/availability failures are independent cells. The matrix
runner remains fail-fast by default for scientific or coupled workloads.

Predeclared cells:

1. CPU/default;
2. GPU T4;
3. GPU L4;
4. GPU A100;
5. TPU v5e1;
6. TPU v6e1.

Each cell records requested and observed hardware, host RAM/disk/CPU information,
optional Torch/JAX device metadata, and a deterministic functional probe. Timing
fields are engineering diagnostics only.

## 4. Compute-envelope requalification preflight

The second matrix runs only the protected CPU reference structural logic:

```bash
python scripts/colab_run_matrix.py \
  configs/compute/qtr_compute_requal_001_matrix.json
```

It reproduces:

- C72 deterministic min-fill width 18;
- C90 deterministic min-fill width 25;
- temporal C18 widths `34/36/36/36` for `R0/R1/R2/R3`.

It then evaluates the nominal `x100` peak-entry envelope without materializing a
new compiled object. With original peak cap `2^20`, the required multipliers are:

- C72: `0.5x`;
- C90: `64x`;
- temporal R0: `32768x`;
- temporal R1/R2/R3: `131072x`.

Therefore C90 crosses the nominal `x100` entry-count preflight, while the current
temporal representations do not. This is not yet a physical-memory clearance:
Colab RAM and representation-specific bytes per retained entry must be checked
before any exact C90 materialization.

## 5. Frozen C90 candidate

`configs/compute/qtr_c90_exact_candidate_matrix.json` is intentionally disabled.

The runner rejects any attempt to enable its `c90_exact_candidate` cell under
this preparation contract. A later scientific contract must define:

- the exact enlarged resource envelope;
- observed runtime and memory prerequisites;
- exact algebra(s) to compile;
- materialization stopping rules;
- selector validation corpus;
- evidence/receipt schema;
- review and promotion path.

No code path in this preparation package permits the disabled candidate to run.

## 6. Accelerator semantics

The existing qLDPC/QEC reference algorithms are Python/CPU implementations.
Allocating a GPU or TPU does not cause them to execute on that accelerator.

Accordingly:

- runtime probes may use GPU/TPU functional kernels;
- protected QEC structural replay remains `cpu_reference`;
- any future GPU/TPU scientific kernel requires a separate exact-equivalence
  certificate against the CPU reference before accelerator results are admissible.

This distinction is written into every job and receipt.

## 7. Artifacts

Each hosted job writes local evidence under:

`runs/hosted/<experiment-id>/<run-id>/`

including, when available:

- deterministic source archive;
- source manifest;
- exact job configuration;
- Colab status;
- remote stdout/stderr;
- `experiment_receipt.json`;
- `gcl_output_bundle.tar.gz`;
- Colab execution log;
- cleanup/session readback.

Failed jobs retain the local directory.

## 8. Claim boundary

This package creates no authority for new C90 scientific evidence, mutation of
`QLDPC-SCALE-001B`, mutation of `QEC-CIRCUIT-002`, adaptive/stochastic order
search, gate-level `QEC-CIRCUIT-003`, thresholds, scaling laws, runtime/memory
superiority, hardware-performance claims, `QLDPC-FORGE`, or autonomous search.