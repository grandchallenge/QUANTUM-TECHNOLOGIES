#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "execution/external/QTR-C90-EXACT-DECODER-001/PROFILE.json"
BINDING_PATH = ROOT / "governance/MP-EXTERNAL-EXECUTION-PLANE-001-BINDING.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
PROVIDER_CLASSES = {"cloud_batch", "kubernetes", "slurm", "hosted_session", "local_batch", "other_external"}


class ExternalExecutionError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ExternalExecutionError(f"expected object: {path}")
    return value


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def validate_profile(profile: dict[str, Any]) -> None:
    if profile.get("record_type") != "QTR_EXTERNAL_EXECUTION_PROFILE":
        raise ExternalExecutionError("profile record type drift")
    if profile.get("campaign") != "QTR-C90-EXACT-DECODER-001":
        raise ExternalExecutionError("campaign identity drift")
    source = profile["source"]
    if source.get("repository") != "grandchallenge/QUANTUM-TECHNOLOGIES":
        raise ExternalExecutionError("source repository drift")
    if not SHA40.fullmatch(str(source.get("orchestration_commit", ""))):
        raise ExternalExecutionError("orchestration commit is not exact")
    if not SHA40.fullmatch(str(source.get("activation_head", ""))):
        raise ExternalExecutionError("activation head is not exact")
    if not SHA64.fullmatch(str(source.get("corpus_sha256", ""))):
        raise ExternalExecutionError("corpus digest drift")
    if source.get("inputs_per_logical_class") != 347 or source.get("logical_classes") != 256:
        raise ExternalExecutionError("frozen C90 domain drift")
    algebras = source.get("algebras")
    if algebras != ["sum_product_bsc_p_0_1", "soft_tropical_base_2", "min_plus_hamming"]:
        raise ExternalExecutionError("algebra roster drift")
    compiles = profile.get("compile_identities")
    if not isinstance(compiles, dict) or set(compiles) != set(algebras):
        raise ExternalExecutionError("compile identity coverage drift")
    for algebra, row in compiles.items():
        for key in ("native_binary_sha256", "canonical_node_stream_sha256", "compile_receipt_payload_sha256"):
            if not SHA64.fullmatch(str(row.get(key, ""))):
                raise ExternalExecutionError(f"{algebra}: invalid {key}")
        if not str(row.get("artifact_digest", "")).startswith("sha256:"):
            raise ExternalExecutionError(f"{algebra}: artifact digest is not SHA-256")
    units = profile["work_units"]
    expected = len(algebras) * int(source["logical_classes"])
    if units.get("expected_total") != expected or expected != 768:
        raise ExternalExecutionError("work-unit cardinality drift")
    if units.get("selector_count_per_unit") != 347 or units.get("all_units_required_before_aggregation") is not True:
        raise ExternalExecutionError("work-unit completeness weakened")
    invariants = profile["scientific_invariants"]
    for key in ("approximation", "pruning", "post_outcome_selection", "quality_exposed_during_shard_execution", "scientific_semantics_changed"):
        if invariants.get(key) is not False:
            raise ExternalExecutionError(f"scientific invariant weakened: {key}")
    if profile["operational_defaults"].get("repository_write_credentials") is not False:
        raise ExternalExecutionError("external executor may not receive repository write credentials")
    if any(bool(v) for v in profile["claim_boundaries"].values()):
        raise ExternalExecutionError("profile may not widen claim authority")


def validate_programme_binding(*, require_effective: bool) -> dict[str, Any]:
    binding = load_json(BINDING_PATH)
    if binding.get("record_type") != "PROGRAMME_EXECUTION_PROFILE_BINDING":
        raise ExternalExecutionError("Programme binding record type drift")
    if binding.get("repository") != "grandchallenge/QUANTUM-TECHNOLOGIES":
        raise ExternalExecutionError("Programme binding repository drift")
    if binding.get("programme_profile") != "MP-EXTERNAL-EXECUTION-PLANE-001":
        raise ExternalExecutionError("Programme execution profile drift")
    if binding.get("programme_repository") != "grandchallenge/MATH-PROGRAMME":
        raise ExternalExecutionError("Programme binding provider repository drift")
    if not SHA40.fullmatch(str(binding.get("programme_candidate_head", ""))):
        raise ExternalExecutionError("Programme candidate head is not exact")
    status = binding.get("status")
    if status not in {"CANDIDATE_DEPENDENCY_PENDING_PROTECTED_MERGE", "EFFECTIVE"}:
        raise ExternalExecutionError("Programme binding status drift")
    if require_effective and status != "EFFECTIVE":
        raise ExternalExecutionError("Programme external-execution profile is not protected/effective")
    if status == "EFFECTIVE":
        if not SHA40.fullmatch(str(binding.get("programme_protected_head", ""))):
            raise ExternalExecutionError("effective Programme binding lacks exact protected head")
        if not SHA40.fullmatch(str(binding.get("programme_profile_blob_sha1", ""))):
            raise ExternalExecutionError("effective Programme binding lacks exact profile blob")
    if any(bool(v) for v in binding.get("claim_boundaries", {}).values()):
        raise ExternalExecutionError("Programme binding may not widen authority")
    return binding


def work_unit_id(algebra: str, logical_class: int) -> str:
    return f"{algebra}/class-{logical_class:03d}"


def expected_units(profile: dict[str, Any]) -> dict[str, tuple[str, int]]:
    result: dict[str, tuple[str, int]] = {}
    for algebra in profile["source"]["algebras"]:
        for logical_class in range(profile["source"]["logical_classes"]):
            unit_id = work_unit_id(algebra, logical_class)
            result[unit_id] = (algebra, logical_class)
    return result


def materialize(args: argparse.Namespace) -> None:
    profile = load_json(PROFILE_PATH)
    validate_profile(profile)
    validate_programme_binding(require_effective=True)
    if args.provider_class not in PROVIDER_CLASSES:
        raise ExternalExecutionError(f"unsupported provider class: {args.provider_class}")
    if not args.adapter.strip():
        raise ExternalExecutionError("provider adapter is required")
    if not SHA64.fullmatch(args.source_payload_sha256):
        raise ExternalExecutionError("source payload SHA-256 must be exact")
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)

    manifest = {
        "schema_version": "1.0.0",
        "record_type": "GCL_EXTERNAL_EXECUTION_MANIFEST",
        "campaign": profile["campaign"],
        "operation": profile["operation"],
        "source": {
            "repository": profile["source"]["repository"],
            "commit": profile["source"]["orchestration_commit"],
            "source_payload_sha256": args.source_payload_sha256,
        },
        "authority": {
            "operation_ref": profile["authority"]["execution_docket"],
            "scientific_execution_authorized": True,
        },
        "provider": {
            "class": args.provider_class,
            "adapter": args.adapter,
            "provider_selection_locked_before_execution": True,
            "repository_write_credentials": False,
        },
        "work_units": {
            "enumeration": "cartesian_product",
            "axes": [
                {"name": "algebra", "values": profile["source"]["algebras"]},
                {"name": "logical_class", "integer_range": {"start": 0, "stop_exclusive": 256, "step": 1}},
            ],
            "expected_total": 768,
            "work_unit_id_template": "{algebra}/class-{logical_class:03d}",
        },
        "scientific_invariants": {
            **profile["scientific_invariants"],
            "activation_head": profile["source"]["activation_head"],
            "orchestration_commit": profile["source"]["orchestration_commit"],
            "corpus_sha256": profile["source"]["corpus_sha256"],
            "inputs_per_work_unit": 347,
            "logical_classes": 256,
            "compile_identities": profile["compile_identities"],
        },
        "operational_parameters": {
            "parallelism_ceiling": min(
                int(args.parallelism),
                int(profile["operational_defaults"]["external_parallelism_ceiling"]),
            ),
            "github_hosted_scientific_execution": False,
        },
        "retry_policy": {
            "max_attempts": profile["operational_defaults"]["max_attempts_per_work_unit"],
            "same_work_unit_identity": True,
            "same_scientific_inputs": True,
        },
        "output_contract": {
            "receipt_record_type": "GCL_EXTERNAL_EXECUTION_RECEIPT",
            "required_artifacts": ["native_rows_jsonl", "semantic_shard_receipt", "runtime_receipt"],
            "all_work_units_required_before_aggregation": True,
        },
        "claim_boundaries": profile["claim_boundaries"],
    }
    if int(args.parallelism) < 1:
        raise ExternalExecutionError("parallelism must be positive")

    manifest_raw = canonical_bytes(manifest)
    manifest_path = out / "MANIFEST.json"
    manifest_path.write_bytes(manifest_raw)
    manifest_sha = sha256_bytes(manifest_raw)

    jobs = out / "jobs"
    jobs.mkdir()
    for unit_id, (algebra, logical_class) in expected_units(profile).items():
        compile_identity = profile["compile_identities"][algebra]
        job = {
            "schema_version": "1.0.0",
            "record_type": "QTR_EXTERNAL_WORK_UNIT",
            "campaign": profile["campaign"],
            "operation": profile["operation"],
            "manifest_sha256": manifest_sha,
            "work_unit_id": unit_id,
            "source_commit": profile["source"]["orchestration_commit"],
            "source_payload_sha256": args.source_payload_sha256,
            "activation_head": profile["source"]["activation_head"],
            "algebra": algebra,
            "logical_class": logical_class,
            "selector_count": 347,
            "corpus_sha256": profile["source"]["corpus_sha256"],
            "compile_identity": compile_identity,
            "command_contract": {
                "selector_generator": "reference/qtr_c90_exact_native_campaign_001.py selectors",
                "native_evaluator_source": "reference/qtr_c90_exact_native_eval_001.cpp",
                "semantic_validator": "reference/qtr_c90_exact_native_campaign_001.py validate-shard",
                "expected_semantic_status": "C90_ACTIVATED_SELECTOR_SHARD_EVALUATED",
            },
            "expected_outputs": {
                "rows": f"rows-{algebra}-class-{logical_class}.jsonl",
                "semantic_receipt": f"receipt-{algebra}-class-{logical_class}.json",
                "runtime_receipt": f"runtime-{algebra}-class-{logical_class}.json",
            },
            "scientific_semantics_changed": False,
            "promotion_claim": False,
            "repository_mutation_performed": False,
        }
        safe_name = unit_id.replace("/", "__")
        (jobs / f"{safe_name}.json").write_bytes(canonical_bytes(job))

    index = {
        "schema_version": "1.0.0",
        "campaign": profile["campaign"],
        "manifest_sha256": manifest_sha,
        "job_count": 768,
        "jobs_directory": "jobs",
        "provider": manifest["provider"],
        "parallelism_ceiling": manifest["operational_parameters"]["parallelism_ceiling"],
    }
    (out / "INDEX.json").write_bytes(canonical_bytes(index))
    print(json.dumps(index, sort_keys=True))


def validate_manifest_against_profile(manifest: dict[str, Any], profile: dict[str, Any]) -> None:
    if manifest.get("record_type") != "GCL_EXTERNAL_EXECUTION_MANIFEST":
        raise ExternalExecutionError("manifest record type drift")
    if manifest.get("campaign") != profile["campaign"] or manifest.get("operation") != profile["operation"]:
        raise ExternalExecutionError("manifest campaign/operation drift")
    source = manifest.get("source", {})
    if source.get("repository") != profile["source"]["repository"]:
        raise ExternalExecutionError("manifest source repository drift")
    if source.get("commit") != profile["source"]["orchestration_commit"]:
        raise ExternalExecutionError("manifest source commit drift")
    if not SHA64.fullmatch(str(source.get("source_payload_sha256", ""))):
        raise ExternalExecutionError("manifest source payload identity drift")
    authority = manifest.get("authority", {})
    if authority.get("operation_ref") != profile["authority"]["execution_docket"]:
        raise ExternalExecutionError("manifest authority reference drift")
    if authority.get("scientific_execution_authorized") is not True:
        raise ExternalExecutionError("manifest is not authorized for scientific execution")
    provider = manifest.get("provider", {})
    if provider.get("class") not in PROVIDER_CLASSES or not str(provider.get("adapter", "")).strip():
        raise ExternalExecutionError("manifest provider identity incomplete")
    if provider.get("provider_selection_locked_before_execution") is not True:
        raise ExternalExecutionError("manifest provider selection is not frozen")
    if provider.get("repository_write_credentials") is not False:
        raise ExternalExecutionError("manifest grants repository write credentials")

    units = manifest.get("work_units", {})
    expected_axes = [
        {"name": "algebra", "values": profile["source"]["algebras"]},
        {"name": "logical_class", "integer_range": {"start": 0, "stop_exclusive": 256, "step": 1}},
    ]
    if units.get("enumeration") != "cartesian_product" or units.get("axes") != expected_axes:
        raise ExternalExecutionError("manifest work-unit domain drift")
    if units.get("expected_total") != 768 or units.get("work_unit_id_template") != "{algebra}/class-{logical_class:03d}":
        raise ExternalExecutionError("manifest work-unit cardinality/identity drift")

    invariants = manifest.get("scientific_invariants", {})
    for key, value in profile["scientific_invariants"].items():
        if invariants.get(key) != value:
            raise ExternalExecutionError(f"manifest scientific invariant drift: {key}")
    exact_invariants = {
        "activation_head": profile["source"]["activation_head"],
        "orchestration_commit": profile["source"]["orchestration_commit"],
        "corpus_sha256": profile["source"]["corpus_sha256"],
        "inputs_per_work_unit": 347,
        "logical_classes": 256,
        "compile_identities": profile["compile_identities"],
    }
    for key, value in exact_invariants.items():
        if invariants.get(key) != value:
            raise ExternalExecutionError(f"manifest frozen identity drift: {key}")

    operational = manifest.get("operational_parameters", {})
    parallelism = int(operational.get("parallelism_ceiling", 0))
    if not 1 <= parallelism <= int(profile["operational_defaults"]["external_parallelism_ceiling"]):
        raise ExternalExecutionError("manifest external parallelism outside profile")
    if operational.get("github_hosted_scientific_execution") is not False:
        raise ExternalExecutionError("manifest routes scientific batch back through GitHub")

    retry = manifest.get("retry_policy", {})
    if retry != {
        "max_attempts": profile["operational_defaults"]["max_attempts_per_work_unit"],
        "same_work_unit_identity": True,
        "same_scientific_inputs": True,
    }:
        raise ExternalExecutionError("manifest retry policy drift")
    outputs = manifest.get("output_contract", {})
    if outputs.get("receipt_record_type") != "GCL_EXTERNAL_EXECUTION_RECEIPT":
        raise ExternalExecutionError("manifest receipt contract drift")
    if outputs.get("required_artifacts") != ["native_rows_jsonl", "semantic_shard_receipt", "runtime_receipt"]:
        raise ExternalExecutionError("manifest required artifact contract drift")
    if outputs.get("all_work_units_required_before_aggregation") is not True:
        raise ExternalExecutionError("manifest permits partial aggregation")
    if manifest.get("claim_boundaries") != profile["claim_boundaries"] or any(
        bool(v) for v in manifest.get("claim_boundaries", {}).values()
    ):
        raise ExternalExecutionError("manifest claim firewall drift")


def _parse_timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ExternalExecutionError(f"receipt missing {label}")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ExternalExecutionError(f"receipt {label} must be timezone-aware")
        return parsed
    except ValueError as exc:
        raise ExternalExecutionError(f"receipt invalid {label}") from exc


def _validate_receipt_common(receipt: dict[str, Any], manifest: dict[str, Any], manifest_sha: str) -> None:
    if receipt.get("record_type") != "GCL_EXTERNAL_EXECUTION_RECEIPT":
        raise ExternalExecutionError("receipt record type drift")
    if receipt.get("manifest_sha256") != manifest_sha:
        raise ExternalExecutionError("receipt manifest identity mismatch")
    if receipt.get("source_commit") != manifest["source"]["commit"]:
        raise ExternalExecutionError("receipt source commit mismatch")
    if receipt.get("source_payload_sha256") != manifest["source"]["source_payload_sha256"]:
        raise ExternalExecutionError("receipt source payload mismatch")
    provider = receipt.get("provider", {})
    if provider.get("class") != manifest["provider"]["class"] or provider.get("adapter") != manifest["provider"]["adapter"]:
        raise ExternalExecutionError("receipt provider identity mismatch")
    if not str(provider.get("execution_id", "")).strip():
        raise ExternalExecutionError("receipt provider execution identity missing")
    attempt = int(provider.get("attempt", 0))
    if not 1 <= attempt <= int(manifest["retry_policy"]["max_attempts"]):
        raise ExternalExecutionError("receipt attempt outside frozen retry policy")
    started = _parse_timestamp(receipt.get("started_at"), "started_at")
    finished = _parse_timestamp(receipt.get("finished_at"), "finished_at")
    if finished < started:
        raise ExternalExecutionError("receipt finish precedes start")
    if receipt.get("scientific_semantics_changed") is not False:
        raise ExternalExecutionError("receipt claims scientific semantic change")
    if receipt.get("promotion_claim") is not False:
        raise ExternalExecutionError("external execution may not claim promotion")
    if receipt.get("repository_mutation_performed") is not False:
        raise ExternalExecutionError("external executor may not mutate repository state")
    if receipt.get("status") != "SUCCESS" or int(receipt.get("returncode", 1)) != 0:
        raise ExternalExecutionError("operationally unsuccessful work unit cannot enter complete aggregate")


def _safe_artifact_path(value: Any) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ExternalExecutionError("artifact path must be a non-empty POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ExternalExecutionError(f"unsafe artifact path: {value}")
    return path


def _validate_semantic_receipt(path: Path, profile: dict[str, Any], algebra: str, logical_class: int) -> None:
    row = load_json(path)
    if row.get("status") != "C90_ACTIVATED_SELECTOR_SHARD_EVALUATED":
        raise ExternalExecutionError("semantic shard status drift")
    if row.get("activation_head") != profile["source"]["activation_head"]:
        raise ExternalExecutionError("semantic shard activation-head drift")
    if row.get("algebra") != algebra or int(row.get("logical_class", -1)) != logical_class:
        raise ExternalExecutionError("semantic shard work-unit drift")
    if int(row.get("selector_count", -1)) != 347:
        raise ExternalExecutionError("semantic shard selector coverage drift")
    if row.get("quality_exposed") is not False or row.get("scientific_semantics_changed") is not False:
        raise ExternalExecutionError("semantic shard crossed frozen boundary")
    expected_compile = profile["compile_identities"][algebra]
    if row.get("compile_identity") != expected_compile:
        raise ExternalExecutionError("semantic shard compile identity drift")


def verify(args: argparse.Namespace) -> None:
    profile = load_json(PROFILE_PATH)
    validate_profile(profile)
    validate_programme_binding(require_effective=True)
    manifest_path = Path(args.manifest)
    manifest = load_json(manifest_path)
    manifest_sha = sha256_file(manifest_path)
    validate_manifest_against_profile(manifest, profile)

    expected = expected_units(profile)
    receipts_dir = Path(args.receipts)
    receipt_paths = sorted(receipts_dir.rglob("*.receipt.json"))
    if len(receipt_paths) != len(expected):
        raise ExternalExecutionError(f"receipt cardinality mismatch: expected {len(expected)}, observed {len(receipt_paths)}")

    observed: set[str] = set()
    artifact_root = Path(args.artifact_root).resolve() if args.artifact_root else None
    for path in receipt_paths:
        receipt = load_json(path)
        _validate_receipt_common(receipt, manifest, manifest_sha)
        unit_id = str(receipt.get("work_unit_id", ""))
        if unit_id not in expected:
            raise ExternalExecutionError(f"unknown work unit: {unit_id}")
        if unit_id in observed:
            raise ExternalExecutionError(f"duplicate work unit receipt: {unit_id}")
        observed.add(unit_id)
        algebra, logical_class = expected[unit_id]

        artifacts = receipt.get("output_artifacts")
        if not isinstance(artifacts, list) or len(artifacts) < 3:
            raise ExternalExecutionError(f"{unit_id}: incomplete output artifact receipt")
        artifact_map: dict[str, dict[str, Any]] = {}
        for row in artifacts:
            if not isinstance(row, dict):
                raise ExternalExecutionError(f"{unit_id}: malformed output artifact receipt")
            artifact_path = str(_safe_artifact_path(row.get("path")))
            if artifact_path in artifact_map:
                raise ExternalExecutionError(f"{unit_id}: duplicate output artifact path: {artifact_path}")
            artifact_map[artifact_path] = row
        expected_rows = f"rows-{algebra}-class-{logical_class}.jsonl"
        expected_semantic = f"receipt-{algebra}-class-{logical_class}.json"
        expected_runtime = f"runtime-{algebra}-class-{logical_class}.json"
        for required in (expected_rows, expected_semantic, expected_runtime):
            matches = [p for p in artifact_map if p.endswith("/" + required) or p == required]
            if len(matches) != 1:
                raise ExternalExecutionError(f"{unit_id}: missing or duplicate artifact {required}")
            row = artifact_map[matches[0]]
            if int(row.get("bytes", -1)) < 0 or not SHA64.fullmatch(str(row.get("sha256", ""))):
                raise ExternalExecutionError(f"{unit_id}: invalid artifact identity {required}")
            if artifact_root is not None:
                rel = _safe_artifact_path(matches[0])
                local = (artifact_root / Path(*rel.parts)).resolve()
                if not local.is_relative_to(artifact_root):
                    raise ExternalExecutionError(f"{unit_id}: artifact escapes materialized root: {matches[0]}")
                if not local.is_file():
                    raise ExternalExecutionError(f"{unit_id}: artifact not materialized: {matches[0]}")
                if local.stat().st_size != int(row["bytes"]) or sha256_file(local) != row["sha256"]:
                    raise ExternalExecutionError(f"{unit_id}: artifact digest mismatch: {matches[0]}")
                if required == expected_semantic:
                    _validate_semantic_receipt(local, profile, algebra, logical_class)

    if observed != set(expected):
        raise ExternalExecutionError("external execution coverage is incomplete")
    result = {
        "status": "QTR_EXTERNAL_EXECUTION_RECEIPTS_COMPLETE",
        "campaign": profile["campaign"],
        "manifest_sha256": manifest_sha,
        "work_units_verified": len(observed),
        "scientific_semantics_changed": False,
        "promotion_claim": False,
    }
    print(json.dumps(result, sort_keys=True))


def validate_profile_command(args: argparse.Namespace) -> None:
    validate_profile(load_json(PROFILE_PATH))
    validate_programme_binding(require_effective=False)
    print("QTR external execution profile and Programme binding: valid")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate-profile")
    p.set_defaults(func=validate_profile_command)

    p = sub.add_parser("materialize")
    p.add_argument("--provider-class", required=True, choices=sorted(PROVIDER_CLASSES))
    p.add_argument("--adapter", required=True)
    p.add_argument("--source-payload-sha256", required=True)
    p.add_argument("--parallelism", type=int, default=48)
    p.add_argument("--output", required=True)
    p.set_defaults(func=materialize)

    p = sub.add_parser("verify")
    p.add_argument("--manifest", required=True)
    p.add_argument("--receipts", required=True)
    p.add_argument("--artifact-root")
    p.set_defaults(func=verify)

    args = parser.parse_args()
    try:
        result = args.func(args)
        return 0 if result is None else int(result or 0)
    except (ExternalExecutionError, OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"QTR external execution error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
