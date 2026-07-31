#!/usr/bin/env python3
"""Dependency-free validator for the JSON Schema subset used by QTR-SIG-WP00."""

from __future__ import annotations

import json
import math
import re
from typing import Any


class SchemaValidationError(ValueError):
    """Raised when an instance violates the governed schema."""


def _fail(path: str, message: str) -> None:
    raise SchemaValidationError(f"{path}: {message}")


def _matches_type(instance: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(instance, dict)
    if expected == "array":
        return isinstance(instance, list)
    if expected == "string":
        return isinstance(instance, str)
    if expected == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if expected == "number":
        return (
            isinstance(instance, (int, float))
            and not isinstance(instance, bool)
            and math.isfinite(float(instance))
        )
    if expected == "boolean":
        return isinstance(instance, bool)
    if expected == "null":
        return instance is None
    _fail("$schema", f"unsupported type keyword {expected!r}")


def validate_instance(instance: Any, schema: dict[str, Any], path: str = "$") -> None:
    """Validate an instance against the exact keyword subset used by QTR."""

    if "const" in schema and instance != schema["const"]:
        _fail(path, f"expected const {schema['const']!r}, observed {instance!r}")

    if "enum" in schema and instance not in schema["enum"]:
        _fail(path, f"value {instance!r} is not in enum {schema['enum']!r}")

    if "type" in schema:
        expected = schema["type"]
        allowed = [expected] if isinstance(expected, str) else list(expected)
        if not any(_matches_type(instance, kind) for kind in allowed):
            _fail(path, f"expected type {allowed!r}, observed {type(instance).__name__}")

    if isinstance(instance, dict):
        required = schema.get("required", [])
        missing = [name for name in required if name not in instance]
        if missing:
            _fail(path, f"missing required properties {missing!r}")

        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        if additional is False:
            extras = sorted(set(instance) - set(properties))
            if extras:
                _fail(path, f"unknown properties {extras!r}")

        for name, value in instance.items():
            subschema = properties.get(name)
            if subschema is not None:
                validate_instance(value, subschema, f"{path}.{name}")

    if isinstance(instance, list):
        if schema.get("uniqueItems"):
            canonical = [
                json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
                for value in instance
            ]
            if len(canonical) != len(set(canonical)):
                _fail(path, "array items are not unique")
        if "items" in schema:
            for index, value in enumerate(instance):
                validate_instance(value, schema["items"], f"{path}[{index}]")

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            _fail(path, f"string length is below {schema['minLength']}")
        if "pattern" in schema and re.fullmatch(schema["pattern"], instance) is None:
            _fail(path, f"value does not match pattern {schema['pattern']!r}")

    if (
        isinstance(instance, (int, float))
        and not isinstance(instance, bool)
        and "minimum" in schema
        and instance < schema["minimum"]
    ):
        _fail(path, f"value {instance!r} is below minimum {schema['minimum']!r}")
