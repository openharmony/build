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

import re
from typing import Any

try:
    from .validation_model import (
        SCHEMA_ALLOWED_KEYS,
        SUPPORTED_SCHEMA_TYPES,
        SUPPORTED_STRING_FORMATS,
        ValidationResult,
        is_integer_value,
        is_number_value,
        json_pointer,
    )
except ImportError:
    from validation_model import (
        SCHEMA_ALLOWED_KEYS,
        SUPPORTED_SCHEMA_TYPES,
        SUPPORTED_STRING_FORMATS,
        ValidationResult,
        is_integer_value,
        is_number_value,
        json_pointer,
    )


def validate_schema_node(
    schema: Any,
    path: str,
    result: ValidationResult,
    *,
    skip_paths: set[str] | None = None,
    restrict_array_items_simple: bool = False,
) -> None:
    if not isinstance(schema, dict):
        result.add_issue("SCH001", path, "schema node must be an object")
        return

    schema_type = _validate_schema_type(schema, path, result)
    if schema_type is None:
        return

    _validate_schema_keywords(schema, schema_type, path, result)
    _validate_description(schema, path, result)
    _validate_default(schema, schema_type, path, result)
    _validate_enum(schema, schema_type, path, result)
    _validate_type_specific_rules(
        schema,
        schema_type,
        path,
        result,
        skip_paths or set(),
        restrict_array_items_simple,
    )


def value_matches_schema_type(value: Any, schema_type: str) -> bool:
    if schema_type == "string":
        return isinstance(value, str)
    if schema_type == "number":
        return is_number_value(value)
    if schema_type == "integer":
        return is_integer_value(value)
    if schema_type == "boolean":
        return isinstance(value, bool)
    if schema_type == "array":
        return isinstance(value, list)
    if schema_type == "object":
        return isinstance(value, dict)
    return False


def validate_input_schema(schema: Any, path: str, result: ValidationResult) -> None:
    validate_schema_node(schema, path, result, restrict_array_items_simple=True)
    if not isinstance(schema, dict):
        return
    if schema.get("type") != "object":
        result.add_issue("SCH_INPUT_002", json_pointer(path, "type"), "inputSchema root type must be object")
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        result.add_issue("SCH_INPUT_003", json_pointer(path, "properties"), "inputSchema properties must be object")
        return
    for key, subschema in properties.items():
        if isinstance(subschema, dict) and subschema.get("type") == "object":
            prop_path = json_pointer(json_pointer(path, "properties"), key)
            result.add_issue(
                "SCH_INPUT_004",
                json_pointer(prop_path, "type"),
                "inputSchema parameter does not support object type",
            )


def _validate_schema_type(schema: dict[str, Any], path: str, result: ValidationResult) -> str | None:
    if "type" not in schema:
        result.add_issue("SCH002", path, "schema node must define type")
        return None
    schema_type = schema.get("type")
    if schema_type not in SUPPORTED_SCHEMA_TYPES:
        result.add_issue("SCH003", json_pointer(path, "type"), "unsupported schema type")
        return None
    return schema_type


def _validate_schema_keywords(
    schema: dict[str, Any],
    schema_type: str,
    path: str,
    result: ValidationResult,
) -> None:
    allowed_keys = SCHEMA_ALLOWED_KEYS[schema_type]
    for key in schema:
        if key in allowed_keys:
            continue
        issue_code = "SCH401" if schema_type == "boolean" else "SCH004"
        result.add_issue(issue_code, json_pointer(path, key), f"unsupported schema keyword for {schema_type}")


def _validate_description(schema: dict[str, Any], path: str, result: ValidationResult) -> None:
    if "description" in schema and not isinstance(schema.get("description"), str):
        result.add_issue("SCH005", json_pointer(path, "description"), "description must be string")


def _validate_default(
    schema: dict[str, Any],
    schema_type: str,
    path: str,
    result: ValidationResult,
) -> None:
    if "default" not in schema:
        return
    default_value = schema.get("default")
    if schema_type == "boolean":
        if not isinstance(default_value, bool):
            result.add_issue("SCH402", json_pointer(path, "default"), "default must be boolean")
        return
    if schema_type == "array":
        if not isinstance(default_value, list):
            result.add_issue("SCH506", json_pointer(path, "default"), "default must be array")
        return
    if not value_matches_schema_type(default_value, schema_type):
        result.add_issue("SCH006", json_pointer(path, "default"), "default type does not match schema type")


def _validate_enum(
    schema: dict[str, Any],
    schema_type: str,
    path: str,
    result: ValidationResult,
) -> None:
    if "enum" not in schema:
        return
    enum_value = schema.get("enum")
    enum_path = json_pointer(path, "enum")
    if not isinstance(enum_value, list) or not enum_value:
        result.add_issue("SCH007", enum_path, "enum must be a non-empty array")
        return
    for index, item in enumerate(enum_value):
        if value_matches_schema_type(item, schema_type):
            continue
        item_path = json_pointer(enum_path, str(index))
        result.add_issue("SCH007", item_path, "enum item type does not match schema type")


def _validate_type_specific_rules(
    schema: dict[str, Any],
    schema_type: str,
    path: str,
    result: ValidationResult,
    skip_paths: set[str],
    restrict_array_items_simple: bool,
) -> None:
    validators = {
        "string": _validate_string_schema,
        "number": _validate_number_schema,
        "integer": _validate_integer_schema,
        "boolean": _validate_boolean_schema,
        "array": _validate_array_schema,
        "object": _validate_object_schema,
    }
    validators[schema_type](schema, path, result, skip_paths, restrict_array_items_simple)


def _validate_string_schema(
    schema: dict[str, Any],
    path: str,
    result: ValidationResult,
    _: set[str],
    __: bool,
) -> None:
    min_length = schema.get("minLength")
    max_length = schema.get("maxLength")
    if min_length is not None and not (is_integer_value(min_length) and min_length >= 0):
        result.add_issue("SCH101", json_pointer(path, "minLength"), "minLength must be integer >= 0")
    if max_length is not None and not (is_integer_value(max_length) and max_length >= 0):
        result.add_issue("SCH102", json_pointer(path, "maxLength"), "maxLength must be integer >= 0")
    if is_integer_value(min_length) and is_integer_value(max_length) and min_length > max_length:
        result.add_issue("SCH103", path, "minLength must not be greater than maxLength")
    _validate_pattern(schema.get("pattern"), path, result)
    _validate_format(schema.get("format"), path, result)


def _validate_pattern(pattern: Any, path: str, result: ValidationResult) -> None:
    if pattern is None:
        return
    if not isinstance(pattern, str):
        result.add_issue("SCH104", json_pointer(path, "pattern"), "pattern must be string")
        return
    try:
        re.compile(pattern)
    except re.error:
        result.add_issue("SCH104", json_pointer(path, "pattern"), "pattern must be a valid regex")


def _validate_format(format_value: Any, path: str, result: ValidationResult) -> None:
    if format_value is None:
        return
    if format_value not in SUPPORTED_STRING_FORMATS:
        result.add_issue("SCH105", json_pointer(path, "format"), "unsupported string format")


def _validate_number_schema(
    schema: dict[str, Any],
    path: str,
    result: ValidationResult,
    _: set[str],
    __: bool,
) -> None:
    _validate_numeric_keyword(schema, path, result, ("minimum", "maximum"), "SCH201", is_number_value)
    _validate_numeric_keyword(
        schema,
        path,
        result,
        ("exclusiveMinimum", "exclusiveMaximum"),
        "SCH202",
        is_number_value,
    )
    _validate_range_pair(schema, path, result, "minimum", "maximum", "SCH203", lambda left, right: left > right)
    _validate_range_pair(
        schema,
        path,
        result,
        "exclusiveMinimum",
        "exclusiveMaximum",
        "SCH204",
        lambda left, right: left >= right,
    )
    multiple_of = schema.get("multipleOf")
    if multiple_of is not None and not (is_number_value(multiple_of) and multiple_of > 0):
        result.add_issue("SCH205", json_pointer(path, "multipleOf"), "multipleOf must be a positive number")


def _validate_integer_schema(
    schema: dict[str, Any],
    path: str,
    result: ValidationResult,
    _: set[str],
    __: bool,
) -> None:
    keys = ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf")
    _validate_numeric_keyword(schema, path, result, keys, "SCH301", is_integer_value)
    multiple_of = schema.get("multipleOf")
    if multiple_of is not None and not (is_integer_value(multiple_of) and multiple_of > 0):
        result.add_issue("SCH302", json_pointer(path, "multipleOf"), "multipleOf must be integer > 0")
    _validate_range_pair(schema, path, result, "minimum", "maximum", "SCH303", lambda left, right: left > right)
    _validate_range_pair(
        schema,
        path,
        result,
        "exclusiveMinimum",
        "exclusiveMaximum",
        "SCH304",
        lambda left, right: left >= right,
    )


def _validate_boolean_schema(
    _: dict[str, Any],
    __: str,
    ___: ValidationResult,
    ____: set[str],
    _____: bool,
) -> None:
    return


def _validate_array_schema(
    schema: dict[str, Any],
    path: str,
    result: ValidationResult,
    _: set[str],
    restrict_array_items_simple: bool,
) -> None:
    items = schema.get("items")
    items_path = json_pointer(path, "items")
    if "items" not in schema:
        result.add_issue("SCH501", items_path, "array schema must define items")
    elif not isinstance(items, dict):
        result.add_issue("SCH502", items_path, "items must be a schema object")
    else:
        validate_schema_node(items, items_path, result, restrict_array_items_simple=restrict_array_items_simple)
        if restrict_array_items_simple and items.get("type") not in {"boolean", "integer", "number", "string"}:
            result.add_issue("SCH507", json_pointer(items_path, "type"), "array items.type is not supported")
    _validate_array_size(schema, path, result)
    if "uniqueItems" in schema and not isinstance(schema.get("uniqueItems"), bool):
        result.add_issue("SCH505", json_pointer(path, "uniqueItems"), "uniqueItems must be boolean")
    _validate_array_default(schema.get("default"), items, schema.get("uniqueItems"), path, result)


def _validate_array_size(schema: dict[str, Any], path: str, result: ValidationResult) -> None:
    min_items = schema.get("minItems")
    max_items = schema.get("maxItems")
    if min_items is not None and not (is_integer_value(min_items) and min_items >= 0):
        result.add_issue("SCH503", json_pointer(path, "minItems"), "minItems must be integer >= 0")
    if max_items is not None and not (is_integer_value(max_items) and max_items >= 0):
        result.add_issue("SCH503", json_pointer(path, "maxItems"), "maxItems must be integer >= 0")
    if is_integer_value(min_items) and is_integer_value(max_items) and min_items > max_items:
        result.add_issue("SCH504", path, "minItems must not be greater than maxItems")


def _validate_array_default(
    default_value: Any,
    items: Any,
    unique_items: Any,
    path: str,
    result: ValidationResult,
) -> None:
    if default_value is None or not isinstance(default_value, list) or not isinstance(items, dict):
        return
    item_type = items.get("type")
    if item_type in SUPPORTED_SCHEMA_TYPES:
        _validate_array_default_items(default_value, item_type, path, result)
    if unique_items is True:
        _validate_array_default_uniqueness(default_value, path, result)


def _validate_array_default_items(
    default_value: list[Any],
    item_type: str,
    path: str,
    result: ValidationResult,
) -> None:
    default_path = json_pointer(path, "default")
    for index, item in enumerate(default_value):
        if value_matches_schema_type(item, item_type):
            continue
        item_path = json_pointer(default_path, str(index))
        result.add_issue("SCH508", item_path, "default array item type does not match items.type")


def _validate_array_default_uniqueness(
    default_value: list[Any],
    path: str,
    result: ValidationResult,
) -> None:
    seen: set[Any] = set()
    default_path = json_pointer(path, "default")
    for index, item in enumerate(default_value):
        marker = _freeze_value(item)
        if marker in seen:
            item_path = json_pointer(default_path, str(index))
            result.add_issue("SCH509", item_path, "default array must not contain duplicates")
        seen.add(marker)


def _validate_object_schema(
    schema: dict[str, Any],
    path: str,
    result: ValidationResult,
    skip_paths: set[str],
    restrict_array_items_simple: bool,
) -> None:
    properties_path = json_pointer(path, "properties")
    properties = schema.get("properties")
    if "properties" not in schema:
        result.add_issue("SCH606", properties_path, "object schema must define properties")
        properties = None
    elif not isinstance(properties, dict):
        result.add_issue("SCH601", properties_path, "properties must be object")
        properties = None
    _validate_object_properties(properties, properties_path, result, skip_paths, restrict_array_items_simple)
    _validate_required(schema.get("required"), properties, path, result)


def _validate_object_properties(
    properties: Any,
    properties_path: str,
    result: ValidationResult,
    skip_paths: set[str],
    restrict_array_items_simple: bool,
) -> None:
    if not isinstance(properties, dict):
        return
    for key, subschema in properties.items():
        prop_path = json_pointer(properties_path, key)
        if prop_path in skip_paths:
            continue
        if not isinstance(subschema, dict):
            result.add_issue("SCH602", prop_path, "property schema must be an object")
            continue
        validate_schema_node(
            subschema,
            prop_path,
            result,
            skip_paths=skip_paths,
            restrict_array_items_simple=restrict_array_items_simple,
        )


def _validate_required(required: Any, properties: Any, path: str, result: ValidationResult) -> None:
    if required is None:
        return
    required_path = json_pointer(path, "required")
    if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
        result.add_issue("SCH603", required_path, "required must be a string array")
        return
    seen: set[str] = set()
    for item in required:
        if item in seen:
            result.add_issue("SCH605", required_path, "required must not contain duplicates")
        seen.add(item)
        if isinstance(properties, dict) and item in properties:
            continue
        result.add_issue("SCH604", required_path, f"required field '{item}' is not defined in properties")


def _validate_numeric_keyword(
    schema: dict[str, Any],
    path: str,
    result: ValidationResult,
    keys: tuple[str, ...],
    issue_code: str,
    matcher,
) -> None:
    for key in keys:
        value = schema.get(key)
        if key in schema and not matcher(value):
            result.add_issue(issue_code, json_pointer(path, key), f"{key} has invalid type")


def _validate_range_pair(
    schema: dict[str, Any],
    path: str,
    result: ValidationResult,
    left_key: str,
    right_key: str,
    issue_code: str,
    comparator,
) -> None:
    left_value = schema.get(left_key)
    right_value = schema.get(right_key)
    if not (is_number_value(left_value) and is_number_value(right_value)):
        return
    if comparator(left_value, right_value):
        result.add_issue(issue_code, path, f"{left_key} and {right_key} relationship is invalid")


def _freeze_value(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, dict):
        return tuple(sorted((key, _freeze_value(item)) for key, item in value.items()))
    return value
