#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2026 Huawei Device Co., Ltd.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

try:
    from .validation_model import (
        SCHEMA_ALLOWED_KEYS,
        SUPPORTED_SCHEMA_TYPES,
        SUPPORTED_STRING_FORMATS,
        ValidationResult,
        is_integer_value,
        json_pointer,
    )
except ImportError:
    from validation_model import (
        SCHEMA_ALLOWED_KEYS,
        SUPPORTED_SCHEMA_TYPES,
        SUPPORTED_STRING_FORMATS,
        ValidationResult,
        is_integer_value,
        json_pointer,
    )


@dataclass(frozen=True)
class NumericBoundsCodes:
    min_code: str
    exclusive_code: str
    range_code: str
    exclusive_range_code: str


def validate_schema_node(schema: Any, path: str, result: ValidationResult) -> None:
    if not isinstance(schema, dict):
        result.add_issue("SCH001", path, "schema node must be an object")
        return

    _validate_reserved_schema_keywords(schema, path, result)
    if _has_unsupported_union_keyword(schema):
        return

    if "type" not in schema:
        result.add_issue("SCH002", path, "schema node must define type")
        return

    schema_type = schema["type"]
    if schema_type not in SUPPORTED_SCHEMA_TYPES:
        result.add_issue(
            "SCH003",
            json_pointer(path, "type"),
            f"unsupported schema type: {schema_type!r}",
        )
        return

    _validate_schema_keywords(schema, schema_type, path, result)
    _validate_schema_common_fields(schema, schema_type, path, result)
    _dispatch_schema_validation(schema, schema_type, path, result)


def validate_string_schema(schema: dict, path: str, result: ValidationResult) -> None:
    min_len = schema.get("minLength")
    max_len = schema.get("maxLength")
    if min_len is not None and not (is_integer_value(min_len) and min_len >= 0):
        result.add_issue("SCH101", json_pointer(path, "minLength"), "minLength must be an integer >= 0")
    if max_len is not None and not (is_integer_value(max_len) and max_len >= 0):
        result.add_issue("SCH102", json_pointer(path, "maxLength"), "maxLength must be an integer >= 0")
    if is_integer_value(min_len) and is_integer_value(max_len) and min_len > max_len:
        result.add_issue("SCH103", path, "minLength must not be greater than maxLength")
    if "pattern" in schema:
        pattern = schema["pattern"]
        if not isinstance(pattern, str):
            result.add_issue("SCH104", json_pointer(path, "pattern"), "pattern must be a string")
        else:
            try:
                re.compile(pattern)
            except re.error as exc:
                result.add_issue("SCH104", json_pointer(path, "pattern"), f"invalid regex pattern: {exc}")
    if "format" in schema and schema["format"] not in SUPPORTED_STRING_FORMATS:
        result.add_issue("SCH105", json_pointer(path, "format"), "unsupported string format")


def validate_number_schema(schema: dict, path: str, result: ValidationResult) -> None:
    codes = NumericBoundsCodes("SCH201", "SCH202", "SCH203", "SCH204")
    validate_numeric_bounds(schema, path, result, codes, allow_float=True)
    multiple = schema.get("multipleOf")
    is_valid_number = isinstance(multiple, (int, float)) and not isinstance(multiple, bool)
    if multiple is not None and not (is_valid_number and multiple > 0):
        result.add_issue("SCH205", json_pointer(path, "multipleOf"), "multipleOf must be a positive number")


def validate_integer_schema(schema: dict, path: str, result: ValidationResult) -> None:
    for key in ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf"):
        if key in schema and not is_integer_value(schema[key]):
            result.add_issue("SCH301", json_pointer(path, key), f"{key} must be an integer")
    minimum = schema.get("minimum")
    maximum = schema.get("maximum")
    if is_integer_value(minimum) and is_integer_value(maximum) and minimum > maximum:
        result.add_issue("SCH303", path, "minimum must not be greater than maximum")
    multiple = schema.get("multipleOf")
    if multiple is not None and not (is_integer_value(multiple) and multiple > 0):
        result.add_issue("SCH302", json_pointer(path, "multipleOf"), "multipleOf must be an integer > 0")


def validate_boolean_schema(schema: dict, path: str, result: ValidationResult) -> None:
    invalid_keys = set(schema.keys()) - SCHEMA_ALLOWED_KEYS["boolean"]
    for key in invalid_keys:
        result.add_issue("SCH401", json_pointer(path, key), f"{key} is not allowed for boolean schema")
    if "default" in schema and not isinstance(schema["default"], bool):
        result.add_issue("SCH402", json_pointer(path, "default"), "default must be boolean")


def validate_array_schema(schema: dict, path: str, result: ValidationResult) -> None:
    items = schema.get("items")
    _validate_array_items(schema, path, result)
    _validate_array_size_rules(schema, path, result)
    _validate_array_uniqueness_rule(schema, path, result)
    _validate_array_default(schema.get("default"), items, schema.get("uniqueItems"), path, result)


def validate_object_schema(schema: dict, path: str, result: ValidationResult) -> None:
    if "properties" not in schema:
        result.add_issue("SCH606", json_pointer(path, "properties"), "object schema must define properties")
        properties = None
    else:
        properties = schema.get("properties")
    properties = _normalize_object_properties(properties, path, result)
    _validate_object_property_schemas(properties, path, result)
    _validate_object_required(schema.get("required"), properties, path, result)


def validate_numeric_bounds(
    schema: dict,
    path: str,
    result: ValidationResult,
    codes: NumericBoundsCodes,
    allow_float: bool,
) -> None:
    numeric_types = (int, float) if allow_float else (int,)
    for key in ("minimum", "maximum"):
        value = schema.get(key)
        if key in schema and not (isinstance(value, numeric_types) and not isinstance(value, bool)):
            result.add_issue(codes.min_code, json_pointer(path, key), f"{key} must be numeric")
    for key in ("exclusiveMinimum", "exclusiveMaximum"):
        value = schema.get(key)
        if key in schema and not (isinstance(value, numeric_types) and not isinstance(value, bool)):
            result.add_issue(codes.exclusive_code, json_pointer(path, key), f"{key} must be numeric")
    minimum = schema.get("minimum")
    maximum = schema.get("maximum")
    if _is_numeric(minimum) and _is_numeric(maximum) and minimum > maximum:
        result.add_issue(codes.range_code, path, "minimum must not be greater than maximum")
    ex_min = schema.get("exclusiveMinimum")
    ex_max = schema.get("exclusiveMaximum")
    if _is_numeric(ex_min) and _is_numeric(ex_max) and ex_min >= ex_max:
        result.add_issue(
            codes.exclusive_range_code,
            path,
            "exclusiveMinimum must be less than exclusiveMaximum",
        )


def _is_numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def value_matches_schema_type(value: Any, schema_type: str) -> bool:
    if schema_type == "string":
        return isinstance(value, str)
    if schema_type == "number":
        return _is_numeric(value)
    if schema_type == "integer":
        return is_integer_value(value)
    if schema_type == "boolean":
        return isinstance(value, bool)
    if schema_type == "array":
        return isinstance(value, list)
    if schema_type == "object":
        return isinstance(value, dict)
    return False


def _validate_reserved_schema_keywords(schema: dict, path: str, result: ValidationResult) -> None:
    if "enum" in schema:
        result.add_issue(
            "SCH007",
            json_pointer(path, "enum"),
            "enum is reserved by design but not supported in the current version",
        )

    for key in ("oneOf", "anyOf", "allOf"):
        if key in schema:
            result.add_issue(
                "SCH008",
                json_pointer(path, key),
                "union schema is reserved by design but not supported in the current version",
            )


def _has_unsupported_union_keyword(schema: dict) -> bool:
    return any(key in schema for key in ("oneOf", "anyOf", "allOf"))


def resolve_schema_path_detail(input_schema: dict, path_parts: list[str]) -> tuple[str, dict | None]:
    current = input_schema
    for index, part in enumerate(path_parts):
        if not isinstance(current, dict):
            return ("invalid_node", None)
        if current.get("type") != "object":
            return ("intermediate_not_object", None)
        properties = current.get("properties")
        if not isinstance(properties, dict):
            return ("invalid_node", None)
        if part not in properties:
            return ("leaf_missing", None) if index == len(path_parts) - 1 else ("path_missing", None)
        current = properties[part]
    if isinstance(current, dict):
        return ("ok", current)
    return ("leaf_missing", None)


def _validate_schema_keywords(
    schema: dict[str, Any],
    schema_type: str,
    path: str,
    result: ValidationResult,
) -> None:
    reserved_keywords = {"enum", "oneOf", "anyOf", "allOf"}
    for key in schema.keys():
        if key in reserved_keywords:
            continue
        if key not in SCHEMA_ALLOWED_KEYS[schema_type]:
            message = f"unsupported schema keyword for {schema_type}"
            result.add_issue("SCH004", json_pointer(path, key), message)


def _validate_schema_common_fields(
    schema: dict[str, Any],
    schema_type: str,
    path: str,
    result: ValidationResult,
) -> None:
    if "description" in schema and not isinstance(schema["description"], str):
        result.add_issue("SCH005", json_pointer(path, "description"), "description must be a string")
    if "default" in schema and not value_matches_schema_type(schema["default"], schema_type):
        result.add_issue("SCH006", json_pointer(path, "default"), "default type does not match schema type")


def _dispatch_schema_validation(
    schema: dict[str, Any],
    schema_type: str,
    path: str,
    result: ValidationResult,
) -> None:
    validators = {
        "string": validate_string_schema,
        "number": validate_number_schema,
        "integer": validate_integer_schema,
        "boolean": validate_boolean_schema,
        "array": validate_array_schema,
        "object": validate_object_schema,
    }
    validators[schema_type](schema, path, result)


def _validate_array_items(schema: dict[str, Any], path: str, result: ValidationResult) -> None:
    if "items" not in schema:
        result.add_issue("SCH501", path, "array schema must define items")
        return
    items = schema["items"]
    items_path = json_pointer(path, "items")
    if not isinstance(items, dict):
        result.add_issue("SCH502", items_path, "items must be a schema object")
        return
    validate_schema_node(items, items_path, result)
    item_type = items.get("type")
    simple_types = {"boolean", "integer", "number", "string"}
    if item_type in SUPPORTED_SCHEMA_TYPES and item_type not in simple_types:
        message = "array items.type must be one of boolean, integer, number, string"
        result.add_issue("SCH507", json_pointer(items_path, "type"), message)


def _validate_array_size_rules(schema: dict[str, Any], path: str, result: ValidationResult) -> None:
    min_items = schema.get("minItems")
    max_items = schema.get("maxItems")
    if min_items is not None and not (is_integer_value(min_items) and min_items >= 0):
        result.add_issue("SCH503", json_pointer(path, "minItems"), "minItems must be an integer >= 0")
    if max_items is not None and not (is_integer_value(max_items) and max_items >= 0):
        result.add_issue("SCH503", json_pointer(path, "maxItems"), "maxItems must be an integer >= 0")
    if is_integer_value(min_items) and is_integer_value(max_items) and min_items > max_items:
        result.add_issue("SCH504", path, "minItems must not be greater than maxItems")


def _validate_array_uniqueness_rule(schema: dict[str, Any], path: str, result: ValidationResult) -> None:
    if "uniqueItems" in schema and not isinstance(schema["uniqueItems"], bool):
        result.add_issue("SCH505", json_pointer(path, "uniqueItems"), "uniqueItems must be boolean")


def _validate_array_default(
    default_value: Any,
    items: Any,
    unique_items: Any,
    path: str,
    result: ValidationResult,
) -> None:
    if default_value is None:
        return
    if not isinstance(default_value, list):
        result.add_issue("SCH506", json_pointer(path, "default"), "default must be an array")
        return
    if not isinstance(items, dict):
        return
    _validate_array_default_item_types(default_value, items.get("type"), path, result)
    if unique_items is True:
        _validate_array_default_uniqueness(default_value, path, result)


def _validate_array_default_item_types(
    default_value: list[Any],
    item_type: Any,
    path: str,
    result: ValidationResult,
) -> None:
    if item_type not in SUPPORTED_SCHEMA_TYPES:
        return
    default_path = json_pointer(path, "default")
    for index, item in enumerate(default_value):
        if value_matches_schema_type(item, item_type):
            continue
        item_path = json_pointer(default_path, str(index))
        message = f"default array item type does not match items.type {item_type!r}"
        result.add_issue("SCH508", item_path, message)


def _validate_array_default_uniqueness(
    default_value: list[Any],
    path: str,
    result: ValidationResult,
) -> None:
    try:
        seen: set[str] = set()
        default_path = json_pointer(path, "default")
        for index, item in enumerate(default_value):
            marker = json.dumps(item, ensure_ascii=False, sort_keys=True)
            if marker in seen:
                item_path = json_pointer(default_path, str(index))
                message = "default array must not contain duplicates when uniqueItems is true"
                result.add_issue("SCH509", item_path, message)
            seen.add(marker)
    except TypeError:
        return


def _normalize_object_properties(
    properties: Any,
    path: str,
    result: ValidationResult,
) -> dict[str, Any] | None:
    if properties is None:
        return None
    if isinstance(properties, dict):
        return properties
    result.add_issue("SCH601", json_pointer(path, "properties"), "properties must be an object")
    return None


def _validate_object_property_schemas(
    properties: dict[str, Any] | None,
    path: str,
    result: ValidationResult,
) -> None:
    if not isinstance(properties, dict):
        return
    properties_path = json_pointer(path, "properties")
    for key, subschema in properties.items():
        subschema_path = json_pointer(properties_path, key)
        if not isinstance(subschema, dict):
            result.add_issue("SCH602", subschema_path, "property schema must be an object")
            continue
        validate_schema_node(subschema, subschema_path, result)


def _validate_object_required(
    required: Any,
    properties: dict[str, Any] | None,
    path: str,
    result: ValidationResult,
) -> None:
    if required is None:
        return
    required_path = json_pointer(path, "required")
    if not (isinstance(required, list) and all(isinstance(item, str) for item in required)):
        result.add_issue("SCH603", required_path, "required must be a string array")
        return
    seen: set[str] = set()
    for item in required:
        if item in seen:
            result.add_issue("SCH605", required_path, "required entries must be unique")
        seen.add(item)
        if not isinstance(properties, dict) or item not in properties:
            result.add_issue("SCH604", required_path, f"required field '{item}' is not defined")
