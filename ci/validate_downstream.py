#!/usr/bin/env python3
"""Fail-closed validation for QTR-SIG-WP01, WP02, and bounded WP03."""
from __future__ import annotations
import json, math, sys
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"reference"));sys.path.insert(0,str(ROOT/"ci"))
import downstream_atlas as da
from schema_validation import SchemaValidationError, validate_instance
class ValidationError(RuntimeError):pass
def require(x:bool,m:str)->None:
    if not x:raise ValidationError(m)
def load(path:Path)->Any:
    try:return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:raise ValidationError(f"cannot load {path.relative_to(ROOT)}: {exc}") from exc
def exact_keys(record:dict[str,Any],required:set[str],optional:set[str]=set())->None:
    missing=required-set(record);extra=set(record)-required-optional
    require(not missing,f"missing keys {sorted(missing)}");require(not extra,f"unknown keys {sorted(extra)}")
def validate_wp01(r:dict[str,Any])->None:
    exact_keys(r,{"record_id","predicate_id","predicate_parameters","input_width","group_action","invariant_coordinates","source_candidates","claim_status","expected"})
    require(r["group_action"]=="S_n_coordinate_permutations","WP01 action is not locked");require(r["invariant_coordinates"]==["hamming_weight"],"WP01 invariant is not locked")
    require(r["claim_status"]=="finite_exhaustive_evidence","WP01 claim status invalid");exact_keys(r["expected"],{"orbit_count","orbit_sizes","labels_by_orbit","boundary_count"})
def validate_wp02(r:dict[str,Any])->None:
    exact_keys(r,{"record_id","predicate_id","predicate_parameters","input_width","source_invariant_record","construction","claim_status","expected"})
    exact_keys(r["construction"],{"kind","operator_shape","definition"},{"target_weight","scale"});exact_keys(r["expected"],{"signed_collision_pairs","singular_collision_pairs","singular_semantically_sufficient"})
    require(r["claim_status"] in {"finite_exhaustive_evidence","finite_negative_result"},"WP02 claim status invalid")
def validate_wp03(r:dict[str,Any])->None:
    exact_keys(r,{"record_id","predicate_id","input_width","certificate_family","source_linearization_record","adversary_certificate","span_program","claim_status","limitations","sources"})
    exact_keys(r["adversary_certificate"],{"zero_input","one_inputs","definition"});exact_keys(r["span_program"],{"vector_space_dimension","target","input_vectors","availability_rule"})
    require(r["certificate_family"]=="or_star_and_unit_span_program","WP03 family invalid");require(r["claim_status"]=="finite_certificate","WP03 claim status invalid")
def validate_all()->dict[str,Any]:
    schema=load(ROOT/"schemas/downstream-atlas.schema.json");registry=load(ROOT/"registry/downstream-atlas.json")
    try:validate_instance(registry,schema)
    except SchemaValidationError as exc:raise ValidationError(str(exc)) from exc
    require(registry["authority"]["charter_adoption_merge"]=="0743ac9947cc835de817d50d92cf3df444132449","wrong adoption authority")
    require(registry["authority"]["adoption_pin_merge"]=="468f22e694c569969602ec68812c57b9109dc8ad","wrong adoption pin")
    for r in registry["WP01"]:validate_wp01(r)
    for r in registry["WP02"]:validate_wp02(r)
    for r in registry["WP03"]:validate_wp03(r)
    report=da.evaluate_registry(registry);expected=load(ROOT/"evidence/downstream-atlas-report.json");require(report==expected,"downstream evidence mismatch")
    w1={r["record_id"] for r in registry["WP01"]};w2={r["record_id"] for r in registry["WP02"]}
    for r,o in zip(registry["WP01"],report["WP01"]):
        e=r["expected"];require(o["orbit_count"]==e["orbit_count"] and o["orbit_sizes"]==e["orbit_sizes"] and o["labels_by_orbit"]==e["labels_by_orbit"] and o["boundary_count"]==e["boundary_count"],f"{r['record_id']}: WP01 expected mismatch");require(o["quotient_semantically_sufficient"],f"{r['record_id']}: quotient collision")
    for r,o in zip(registry["WP02"],report["WP02"]):
        require(r["source_invariant_record"] in w1,f"{r['record_id']}: missing WP01 source");e=r["expected"];require(o["signed_channel"]["cross_label_collision_pairs"]==e["signed_collision_pairs"],f"{r['record_id']}: signed mismatch");require(o["singular_value_channel"]["cross_label_collision_pairs"]==e["singular_collision_pairs"],f"{r['record_id']}: singular mismatch");require(o["singular_value_channel"]["semantically_sufficient"]==e["singular_semantically_sufficient"],f"{r['record_id']}: singular status mismatch")
    for r,o in zip(registry["WP03"],report["WP03"]):
        require(r["source_linearization_record"] in w2,f"{r['record_id']}: missing WP02 source");require(math.isclose(o["adversary_certificate"]["objective"],2.0),"WP03 objective mismatch");require(math.isclose(o["span_program"]["witness_size_complexity"],2.0),"WP03 span mismatch");require(o["certificate_objectives_match"],"WP03 objectives disagree")
    return report
def main()->int:
    r=validate_all();print(f"QTR-SIG-NEXT-001 validation passed: {r['payload_sha256']}");return 0
if __name__=="__main__":
    try:raise SystemExit(main())
    except ValidationError as exc:print(f"QTR downstream validation failed: {exc}",file=sys.stderr);raise SystemExit(1)
