#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ALLOWED_GPU = {"T4", "L4", "A100", "H100", "G4"}
ALLOWED_TPU = {"v5e1", "v6e1", "V5E1", "V6E1"}


def optional_import(name: str):
    try:
        return __import__(name)
    except Exception:
        return None


def proc_meminfo() -> dict[str, int]:
    path = Path("/proc/meminfo")
    out: dict[str, int] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields = value.strip().split()
        if fields and fields[0].isdigit():
            amount = int(fields[0])
            if len(fields) > 1 and fields[1].lower() == "kb":
                amount *= 1024
            out[key] = amount
    return out


def nvidia_info() -> list[dict[str, str]]:
    if shutil.which("nvidia-smi") is None:
        return []
    proc = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,driver_version",
            "--format=csv,noheader,nounits",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if proc.returncode:
        return []
    rows = []
    for line in proc.stdout.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) >= 3:
            rows.append({"name": parts[0], "memory_total_mib": parts[1], "driver": parts[2]})
    return rows


def jax_info() -> tuple[str | None, list[dict[str, str]]]:
    jax = optional_import("jax")
    if jax is None:
        return None, []
    rows = []
    try:
        for device in jax.devices():
            rows.append({
                "platform": str(getattr(device, "platform", "")),
                "device_kind": str(getattr(device, "device_kind", "")),
                "id": str(getattr(device, "id", "")),
            })
    except Exception as exc:
        rows.append({"platform": "ERROR", "device_kind": type(exc).__name__, "id": ""})
    return str(getattr(jax, "__version__", "unknown")), rows


def torch_info() -> dict[str, Any]:
    torch = optional_import("torch")
    if torch is None:
        return {"available": False}
    out: dict[str, Any] = {
        "available": True,
        "version": str(getattr(torch, "__version__", "unknown")),
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_version": str(getattr(torch.version, "cuda", None)),
    }
    if torch.cuda.is_available():
        out["device_count"] = torch.cuda.device_count()
        out["device_names"] = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
    return out


def detect_runtime() -> dict[str, Any]:
    mem = proc_meminfo()
    disk = shutil.disk_usage("/content" if Path("/content").exists() else "/")
    gpu = nvidia_info()
    torch = torch_info()
    jax_version, jax_devices = jax_info()
    tpu_devices = [row for row in jax_devices if row.get("platform") == "tpu"]
    if tpu_devices:
        variant = "TPU"
        accelerator = "; ".join(row.get("device_kind", "") for row in tpu_devices)
    elif gpu or torch.get("cuda_available"):
        variant = "GPU"
        names = [row["name"] for row in gpu] or list(torch.get("device_names", []))
        accelerator = "; ".join(names)
    else:
        variant = "CPU"
        accelerator = None
    return {
        "observed_variant": variant,
        "observed_accelerator": accelerator,
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
        "memory_total_bytes": mem.get("MemTotal"),
        "memory_available_bytes": mem.get("MemAvailable"),
        "disk_total_bytes": disk.total,
        "disk_free_bytes": disk.free,
        "nvidia": gpu,
        "torch": torch,
        "jax_version": jax_version,
        "jax_devices": jax_devices,
    }


def normalize(text: str | None) -> str:
    return "".join(ch for ch in (text or "").lower() if ch.isalnum())


def validate_requested_runtime(job: dict[str, Any], runtime: dict[str, Any]) -> None:
    requested = job["resource"]
    variant = str(requested["variant"]).upper()
    observed = runtime["observed_variant"]
    accelerator = requested.get("accelerator")
    if variant == "DEFAULT":
        variant = "CPU"
    if observed != variant:
        raise RuntimeError(f"requested {variant}, observed {observed}")
    if variant == "GPU":
        if accelerator not in ALLOWED_GPU:
            raise RuntimeError(f"unsupported requested GPU {accelerator}")
        if normalize(str(accelerator)) not in normalize(runtime.get("observed_accelerator")):
            raise RuntimeError(
                f"requested GPU {accelerator}, observed {runtime.get('observed_accelerator')}"
            )
    if variant == "TPU":
        if accelerator not in ALLOWED_TPU:
            raise RuntimeError(f"unsupported requested TPU {accelerator}")
        observed_text = normalize(runtime.get("observed_accelerator"))
        required_family = "v5" if "5" in str(accelerator) else "v6"
        if required_family not in observed_text:
            raise RuntimeError(
                f"requested TPU {accelerator}, observed {runtime.get('observed_accelerator')}"
            )


def validate_job(job: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "experiment_id",
        "workload",
        "resource",
        "remote_timeout_seconds",
        "scientific_backend",
        "scientific_execution_authorized",
        "claim_boundary",
        "enabled",
    }
    allowed = required | {"nominal_envelope_multiplier", "required_authorization"}
    missing = required - set(job)
    unknown = set(job) - allowed
    if missing or unknown:
        raise ValueError(f"job keys invalid missing={sorted(missing)} unknown={sorted(unknown)}")
    if job["schema_version"] != 1:
        raise ValueError("schema_version must be 1")
    if job["scientific_execution_authorized"] is not False:
        raise ValueError("preparation jobs may not authorize scientific execution")


def cpu_probe() -> dict[str, Any]:
    n = 1 << 20
    mask = (1 << 63) - 1
    start = time.perf_counter()
    checksum = 0
    value = 0x123456789ABCDEF
    for i in range(n):
        value = ((value * 6364136223846793005 + 1442695040888963407) & mask)
        checksum ^= value ^ i
    elapsed = time.perf_counter() - start
    return {"elements": n, "checksum": checksum, "elapsed_seconds_diagnostic": elapsed}


def gpu_probe() -> dict[str, Any] | None:
    torch = optional_import("torch")
    if torch is None or not torch.cuda.is_available():
        return None
    n = 1 << 20
    start = time.perf_counter()
    x = torch.arange(n, dtype=torch.int64, device="cuda")
    y = torch.bitwise_xor(x, 0x55AA55AA)
    checksum = int(y.sum().item())
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - start
    return {"elements": n, "checksum": checksum, "elapsed_seconds_diagnostic": elapsed}


def tpu_probe() -> dict[str, Any] | None:
    jax = optional_import("jax")
    if jax is None:
        return None
    devices = [d for d in jax.devices() if getattr(d, "platform", None) == "tpu"]
    if not devices:
        return None
    import jax.numpy as jnp
    n = 1 << 20
    start = time.perf_counter()
    x = jnp.arange(n, dtype=jnp.int32)
    y = jnp.bitwise_xor(x, jnp.int32(0x55AA55AA))
    checksum_arr = jnp.sum(y, dtype=jnp.int64)
    checksum = int(checksum_arr.block_until_ready())
    elapsed = time.perf_counter() - start
    return {"elements": n, "checksum": checksum, "elapsed_seconds_diagnostic": elapsed}


def run_probe(job: dict[str, Any]) -> dict[str, Any]:
    validate_job(job)
    runtime = detect_runtime()
    validate_requested_runtime(job, runtime)
    probes = {"cpu": cpu_probe(), "gpu": None, "tpu": None}
    if runtime["observed_variant"] == "GPU":
        probes["gpu"] = gpu_probe()
        if probes["gpu"] is None:
            raise RuntimeError("GPU requested/observed but GPU functional probe unavailable")
    elif runtime["observed_variant"] == "TPU":
        probes["tpu"] = tpu_probe()
        if probes["tpu"] is None:
            raise RuntimeError("TPU requested/observed but TPU functional probe unavailable")
    return {
        "schema_version": 1,
        "experiment_id": job["experiment_id"],
        "status": "GREEN_ENGINEERING",
        "runtime": runtime,
        "functional_probes": probes,
        "scientific_backend": job["scientific_backend"],
        "accelerator_scientifically_used": False,
        "timings_are_engineering_diagnostics_only": True,
        "claim_boundary": job["claim_boundary"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate-job", action="store_true")
    args = parser.parse_args()
    job = json.loads(args.job.read_text(encoding="utf-8"))
    validate_job(job)
    if args.validate_job:
        print("[QTR] job validation: PASS")
        return 0
    if args.output is None:
        parser.error("--output is required unless --validate-job is used")
    result = run_probe(job)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "runtime": result["runtime"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())