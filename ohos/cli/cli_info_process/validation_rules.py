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

from pathlib import PurePosixPath
import re
from typing import Any

try:
    from .validation_model import (
        RESERVED_EVENT_TYPES,
        SUPPORTED_SUBCOMMAND_FIELDS,
        SUPPORTED_TOP_LEVEL_FIELDS,
        ValidationResult,
        json_pointer,
    )
    from .validation_schema import validate_input_schema, validate_schema_node
except ImportError:
    from validation_model import (
        RESERVED_EVENT_TYPES,
        SUPPORTED_SUBCOMMAND_FIELDS,
        SUPPORTED_TOP_LEVEL_FIELDS,
        ValidationResult,
        json_pointer,
    )
    from validation_schema import validate_input_schema, validate_schema_node


NAME_PATTERN = re.compile(r"^(?P<prefix>[^-]+)-(?P<tool_name>.+)$")


def validate_config(data: dict[str, Any], result: ValidationResult) -> None:
    if not isinstance(data, dict):
        return
    validate_top_level(data, result)
    validate_subcommands(data, result)


def validate_top_level(data: dict[str, Any], result: ValidationResult) -> None:
    _validate_allowed_fields(data, SUPPORTED_TOP_LEVEL_FIELDS, "/", "TOP_fields_001", result)
    _validate_name(data, result)
    _validate_required_string(data, "version", "TOP_version_001", result)
    _validate_required_string(data, "description", "TOP_description_001", result)
    _validate_executable_path(data, result)
    _validate_string_array_field(
        data,
        "requirePermissions",
        ("TOP_requirePermissions_001", "TOP_requirePermissions_002"),
        result,
        required=True,
    )
    _validate_event_types(data.get("eventTypes"), "/eventTypes", "TOP_eventTypes", result)
    _validate_event_schemas(data.get("eventSchemas"), "/eventSchemas", "TOP_eventSchemas", result)
    _validate_optional_boolean(data, "hasSubcommands", "TOP_hasSubcommands_001", result)
    _validate_input_schema_field(data, "/inputSchema", "TOP_inputSchema_001", result)
    _validate_output_schema_field(data, "/outputSchema", "TOP_outputSchema", result)
    _validate_top_level_relationships(data, result)
    _validate_event_relationships(
        data.get("eventTypes"),
        data.get("eventSchemas"),
        "/",
        "TOP_eventTypes_101",
        "TOP_eventSchemas_101",
        result,
    )


def validate_subcommands(data: dict[str, Any], result: ValidationResult) -> None:
    subcommands = data.get("subcommands")
    if "subcommands" in data and not isinstance(subcommands, dict):
        result.add_issue("TOP_subcommands_001", "/subcommands", "subcommands must be object")
        return
    if isinstance(subcommands, dict) and not subcommands:
        result.add_issue("TOP_subcommands_002", "/subcommands", "subcommands must not be empty")
    if not isinstance(subcommands, dict):
        return
    for name, definition in subcommands.items():
        sub_path = json_pointer("/subcommands", name)
        _validate_subcommand_name(name, data.get("name"), sub_path, result)
        validate_subcommand_definition(name, definition, sub_path, result)


def validate_subcommand_definition(
    name: str,
    definition: Any,
    path: str,
    result: ValidationResult,
) -> None:
    if not isinstance(definition, dict):
        result.add_issue("SUB_subcommands_001", path, "subcommand definition must be object")
        return
    _validate_allowed_fields(definition, SUPPORTED_SUBCOMMAND_FIELDS, path, "SUB_fields_001", result)
    _validate_required_string(definition, "description", "SUB_description_001", result, path)
    _validate_string_array_field(
        definition,
        "requirePermissions",
        ("SUB_requirePermissions_001", "SUB_requirePermissions_002"),
        result,
        required=True,
        base_path=path,
    )
    _validate_input_schema_field(definition, json_pointer(path, "inputSchema"), "SUB_inputSchema_001", result)
    _validate_output_schema_field(definition, json_pointer(path, "outputSchema"), "SUB_outputSchema", result)
    _validate_event_types(
        definition.get("eventTypes"),
        json_pointer(path, "eventTypes"),
        "SUB_eventTypes",
        result,
    )
    _validate_event_schemas(
        definition.get("eventSchemas"),
        json_pointer(path, "eventSchemas"),
        "SUB_eventSchemas",
        result,
    )
    _validate_event_relationships(
        definition.get("eventTypes"),
        definition.get("eventSchemas"),
        path,
        "SUB_eventTypes_101",
        "SUB_eventSchemas_101",
        result,
    )


def _validate_allowed_fields(
    data: dict[str, Any],
    allowed_fields: set[str],
    path: str,
    issue_code: str,
    result: ValidationResult,
) -> None:
    for key in data:
        if key in allowed_fields:
            continue
        result.add_issue(issue_code, json_pointer(path, key), f"unsupported field '{key}'")


def _validate_name(data: dict[str, Any], result: ValidationResult) -> None:
    name = data.get("name")
    if not isinstance(name, str) or not name:
        result.add_issue("TOP_name_001", "/name", "name must be a non-empty string")
        return
    match = NAME_PATTERN.fullmatch(name)
    if match is None:
        result.add_issue("TOP_name_002", "/name", "name must use prefix-toolName format")
        return
    prefix = match.group("prefix")
    tool_name = match.group("tool_name")
    if prefix not in {"ohos", "hms"}:
        result.add_issue("TOP_name_003", "/name", "name prefix must be ohos or hms")
    if len(tool_name) > 32:
        result.add_issue("TOP_name_004", "/name", "toolName length must be <= 32")


def _validate_required_string(
    data: dict[str, Any],
    field: str,
    issue_code: str,
    result: ValidationResult,
    base_path: str = "/",
) -> None:
    value = data.get(field)
    if isinstance(value, str) and value:
        return
    result.add_issue(issue_code, json_pointer(base_path, field), f"{field} must be a non-empty string")


def _validate_executable_path(data: dict[str, Any], result: ValidationResult) -> None:
    value = data.get("executablePath")
    if not isinstance(value, str) or not value:
        result.add_issue("TOP_executablePath_001", "/executablePath", "executablePath must be a non-empty string")
        return
    if not PurePosixPath(value).is_absolute():
        result.add_issue("TOP_executablePath_002", "/executablePath", "executablePath must be absolute")


def _validate_string_array_field(
    data: dict[str, Any],
    field: str,
    codes: tuple[str, str],
    result: ValidationResult,
    *,
    required: bool,
    base_path: str = "/",
) -> None:
    field_path = json_pointer(base_path, field)
    if field not in data:
        if required:
            result.add_issue(codes[0], field_path, f"{field} must be a string array")
        return
    value = data.get(field)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        result.add_issue(codes[0], field_path, f"{field} must be a string array")
        return
    _validate_duplicate_strings(value, field_path, codes[1], result)


def _validate_duplicate_strings(
    values: list[str],
    path: str,
    issue_code: str,
    result: ValidationResult,
) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            result.add_issue(issue_code, path, "duplicate value is not allowed")
        seen.add(value)


def _validate_event_types(event_types: Any, path: str, prefix: str, result: ValidationResult) -> None:
    if event_types is None:
        return
    if not isinstance(event_types, list) or not all(isinstance(item, str) for item in event_types):
        result.add_issue(f"{prefix}_001", path, "eventTypes must be a string array")
        return
    _validate_duplicate_strings(event_types, path, f"{prefix}_002", result)
    if "result" in event_types:
        result.add_issue(f"{prefix}_003", path, "reserved event 'result' is not allowed")


def _validate_event_schemas(event_schemas: Any, path: str, prefix: str, result: ValidationResult) -> None:
    if event_schemas is None:
        return
    if not isinstance(event_schemas, dict):
        result.add_issue(f"{prefix}_001", path, "eventSchemas must be object")
        return
    for event_name, schema in event_schemas.items():
        _validate_event_schema_entry(event_name, schema, path, prefix, result)


def _validate_event_schema_entry(
    event_name: str,
    schema: Any,
    path: str,
    prefix: str,
    result: ValidationResult,
) -> None:
    schema_path = json_pointer(path, event_name)
    if not isinstance(schema, dict):
        result.add_issue(f"{prefix}_002", schema_path, "event schema must be object")
        return
    type_path = json_pointer(json_pointer(schema_path, "properties"), "type")
    validate_schema_node(schema, schema_path, result, skip_paths={type_path})
    if schema.get("type") != "object":
        result.add_issue(f"{prefix}_003", json_pointer(schema_path, "type"), "event schema root type must be object")
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        result.add_issue(
            f"{prefix}_004",
            json_pointer(schema_path, "properties"),
            "event schema properties must be object",
        )
        return
    if "type" not in properties:
        result.add_issue(
            f"{prefix}_005",
            json_pointer(schema_path, "properties"),
            "event schema must define properties.type",
        )
        return
    if not _is_event_type_const_schema(properties.get("type"), event_name):
        result.add_issue(f"{prefix}_006", type_path, "properties.type must be {'const': event name}")


def _is_event_type_const_schema(schema: Any, event_name: str) -> bool:
    return isinstance(schema, dict) and set(schema.keys()) == {"const"} and schema.get("const") == event_name


def _validate_optional_boolean(
    data: dict[str, Any],
    field: str,
    issue_code: str,
    result: ValidationResult,
) -> None:
    if field not in data:
        return
    if not isinstance(data.get(field), bool):
        result.add_issue(issue_code, f"/{field}", f"{field} must be boolean")


def _validate_input_schema_field(
    data: dict[str, Any],
    path: str,
    missing_code: str,
    result: ValidationResult,
) -> None:
    if path.split("/")[-1] not in data:
        result.add_issue(missing_code, path, "inputSchema is required")
        return
    schema = data.get("inputSchema")
    validate_input_schema(schema, path, result)
    if not isinstance(schema, dict):
        result.add_issue("SCH_INPUT_001", path, "inputSchema must be a valid schema object")
        return
    if _has_schema_errors(result, path):
        result.add_issue("SCH_INPUT_001", path, "inputSchema must be a valid schema object")


def _validate_output_schema_field(
    data: dict[str, Any],
    path: str,
    prefix: str,
    result: ValidationResult,
) -> None:
    field_name = path.split("/")[-1]
    if field_name not in data:
        result.add_issue(f"{prefix}_001", path, "outputSchema is required")
        return
    schema = data.get("outputSchema")
    validate_schema_node(schema, path, result)
    if not isinstance(schema, dict):
        result.add_issue(f"{prefix}_002", path, "outputSchema must be a valid schema object")
        return
    if _has_schema_errors(result, path):
        result.add_issue(f"{prefix}_002", path, "outputSchema must be a valid schema object")
    if schema.get("type") != "object":
        result.add_issue(f"{prefix}_003", json_pointer(path, "type"), "outputSchema root type must be object")
    if not isinstance(schema.get("properties"), dict):
        result.add_issue(f"{prefix}_004", json_pointer(path, "properties"), "outputSchema properties must be object")


def _validate_top_level_relationships(data: dict[str, Any], result: ValidationResult) -> None:
    has_subcommands = data.get("hasSubcommands")
    subcommands_defined = "subcommands" in data
    if has_subcommands is True and not subcommands_defined:
        result.add_issue("TOP_hasSubcommands_101", "/hasSubcommands", "hasSubcommands=true requires subcommands")
    if subcommands_defined and has_subcommands is not True:
        result.add_issue("TOP_hasSubcommands_102", "/subcommands", "subcommands requires hasSubcommands=true")


def _validate_event_relationships(
    event_types: Any,
    event_schemas: Any,
    path: str,
    missing_schema_code: str,
    missing_type_code: str,
    result: ValidationResult,
) -> None:
    type_names = _normalized_string_list(event_types)
    schema_names = set(event_schemas.keys()) if isinstance(event_schemas, dict) else set()
    if type_names is None:
        return
    for event_name in sorted(type_names - schema_names):
        issue_path = json_pointer(path, "eventTypes") if path == "/" else json_pointer(path, "eventTypes")
        result.add_issue(missing_schema_code, issue_path, f"event '{event_name}' is missing from eventSchemas")
    if not isinstance(event_schemas, dict):
        return
    for event_name in sorted(schema_names - type_names):
        issue_path = json_pointer(path, "eventSchemas") if path == "/" else json_pointer(path, "eventSchemas")
        result.add_issue(missing_type_code, issue_path, f"event '{event_name}' is missing from eventTypes")


def _normalized_string_list(value: Any) -> set[str] | None:
    if value is None:
        return set()
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return None
    return set(value)


def _validate_subcommand_name(
    name: Any,
    parent_name: Any,
    path: str,
    result: ValidationResult,
) -> None:
    if not isinstance(name, str) or not name:
        result.add_issue("SUB_name_001", path, "subcommand name must be non-empty string")
        return
    if isinstance(parent_name, str) and name == parent_name:
        result.add_issue("SUB_name_002", path, "subcommand name must not match parent command")


def _has_schema_errors(result: ValidationResult, path: str) -> bool:
    prefix = f"{path.rstrip('/')}/"
    for issue in result.issues:
        if issue.code.startswith("SCH") and (issue.path == path or issue.path.startswith(prefix)):
            return True
    return False
