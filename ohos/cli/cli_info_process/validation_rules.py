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
        ALLOWED_MAPPING_KEYS,
        BUILTIN_EVENT_TYPES,
        RESERVED_EVENT_TYPES,
        SUPPORTED_MAPPING_TYPES,
        SUPPORTED_SUBCOMMAND_FIELDS,
        SUPPORTED_TOP_LEVEL_FIELDS,
        ValidationResult,
        is_integer_value,
        json_pointer,
    )
    from .validation_schema import resolve_schema_path_detail, validate_schema_node
except ImportError:
    from validation_model import (
        ALLOWED_MAPPING_KEYS,
        BUILTIN_EVENT_TYPES,
        RESERVED_EVENT_TYPES,
        SUPPORTED_MAPPING_TYPES,
        SUPPORTED_SUBCOMMAND_FIELDS,
        SUPPORTED_TOP_LEVEL_FIELDS,
        ValidationResult,
        is_integer_value,
        json_pointer,
    )
    from validation_schema import resolve_schema_path_detail, validate_schema_node


TOOL_NAME_PATTERN = re.compile(r"^[A-Za-z0-9]+-[A-Za-z0-9-]+$")
ALLOWED_TOOL_PREFIXES = {"ohos", "hms"}


def validate_config(data: dict[str, Any], result: ValidationResult) -> None:
    validate_top_level(data, result)
    if not result.valid and not isinstance(data, dict):
        return

    has_subcommands = data.get("hasSubcommands", False)
    if has_subcommands is True:
        validate_subcommand_tool(data, result)
    elif has_subcommands is False or "hasSubcommands" not in data:
        validate_simple_tool(data, result)
    else:
        result.add_issue("FMT005", "/hasSubcommands", "hasSubcommands must be boolean")


def validate_top_level(data: dict[str, Any], result: ValidationResult) -> None:
    _validate_unknown_fields(
        data,
        SUPPORTED_TOP_LEVEL_FIELDS,
        "/",
        ("TOP013", "unknown top-level field"),
        result,
    )

    _require_non_empty_string(data, "name", "TOP001", result)
    _validate_tool_name(data.get("name"), "/name", result)
    _require_non_empty_string(data, "version", "TOP002", result)
    _require_non_empty_string(data, "description", "TOP003", result)
    _require_non_empty_string(data, "executablePath", "TOP004", result)
    _validate_top_level_executable(data.get("executablePath"), result)
    _validate_permissions(
        data.get("requirePermissions"),
        "/requirePermissions",
        ("TOP006", "TOP007"),
        result,
    )
    _validate_timeout(data.get("timeout"), "/timeout", ("TOP008", "TOP009"), result)
    _validate_event_types(
        data.get("eventTypes"),
        "/eventTypes",
        ("TOP010", "TOP011"),
        result,
    )
    _validate_event_schemas_type(data, "/eventSchemas", "TOP012", result)


def validate_simple_tool(data: dict[str, Any], result: ValidationResult) -> None:
    if "inputSchema" not in data:
        result.add_issue("FMT001", "/inputSchema", "simple tool must define inputSchema")
        return
    if "argMapping" not in data:
        result.add_issue("FMT002", "/argMapping", "simple tool must define argMapping")
        return
    if "subcommands" in data:
        result.add_issue("FMT003", "/subcommands", "simple tool must not define subcommands")
    if "hasSubcommands" in data and not isinstance(data["hasSubcommands"], bool):
        result.add_issue("FMT005", "/hasSubcommands", "hasSubcommands must be boolean")

    validate_input_schema(data["inputSchema"], "/inputSchema", "SCX001", "SCX002", result)
    if "outputSchema" in data:
        validate_output_schema(data["outputSchema"], "/outputSchema", result)
        if not isinstance(data["outputSchema"], dict) or data["outputSchema"].get("type") != "object":
            result.add_issue("FMT004", "/outputSchema", "simple tool outputSchema must be a valid object schema")
    validate_argument_mapping(data.get("argMapping"), data["inputSchema"], "/argMapping", result)
    validate_mapping_relationships(data["inputSchema"], data.get("argMapping"), "/argMapping", result)
    validate_events(data.get("eventTypes"), data.get("eventSchemas"), "/", result)


def validate_subcommand_tool(data: dict[str, Any], result: ValidationResult) -> None:
    if "subcommands" not in data:
        result.add_issue("FMT101", "/subcommands", "subcommand tool must define subcommands")
        return
    subcommands = data["subcommands"]
    if not isinstance(subcommands, dict):
        result.add_issue("FMT102", "/subcommands", "subcommands must be an object")
        return
    if not subcommands:
        result.add_issue("FMT103", "/subcommands", "subcommands must not be empty")
    top_level_has_input = "inputSchema" in data
    top_level_has_mapping = "argMapping" in data
    if top_level_has_input != top_level_has_mapping:
        result.add_issue("FMT105", "/argMapping", "top-level inputSchema and argMapping must be defined together")
    if "inputSchema" in data:
        validate_input_schema(data["inputSchema"], "/inputSchema", "FMT104", "FMT104", result)
        if isinstance(data["inputSchema"], dict) and data["inputSchema"].get("type") != "object":
            result.add_issue("FMT104", "/inputSchema", "top-level inputSchema must be a valid object schema")
    if "argMapping" in data:
        if "inputSchema" not in data or not isinstance(data.get("inputSchema"), dict):
            result.add_issue("FMT105", "/argMapping", "top-level argMapping requires a matching top-level inputSchema")
        elif not isinstance(data["argMapping"], dict):
            result.add_issue("FMT105", "/argMapping", "top-level argMapping must be an object")
        else:
            validate_argument_mapping(data["argMapping"], data["inputSchema"], "/argMapping", result)
            validate_mapping_relationships(data["inputSchema"], data["argMapping"], "/argMapping", result)
    if "outputSchema" in data:
        validate_output_schema(data["outputSchema"], "/outputSchema", result)
        if not isinstance(data["outputSchema"], dict) or data["outputSchema"].get("type") != "object":
            result.add_issue("FMT106", "/outputSchema", "top-level outputSchema must be a valid object schema")

    seen_names: set[str] = set()
    for name, subcommand in subcommands.items():
        path = json_pointer("/subcommands", name)
        if not isinstance(name, str) or not name:
            result.add_issue("FMT107", path, "subcommand name must be a non-empty string")
            continue
        if name in seen_names:
            result.add_issue("FMT108", path, "duplicate subcommand name")
        seen_names.add(name)
        if name == data.get("name"):
            result.add_issue("FMT109", path, "subcommand name must not match parent command name")
        validate_subcommand(name, subcommand, path, result)

    validate_events(data.get("eventTypes"), data.get("eventSchemas"), "/", result)


def validate_subcommand(name: str, subcommand: Any, path: str, result: ValidationResult) -> None:
    if not isinstance(subcommand, dict):
        result.add_issue("SUB001", path, "subcommand definition must be an object")
        return

    if not _validate_subcommand_required_fields(subcommand, path, result):
        return

    event_types = subcommand.get("eventTypes")
    event_schemas = subcommand.get("eventSchemas")
    _validate_subcommand_optional_fields(subcommand, path, result)
    _validate_subcommand_schema_and_mapping(subcommand, path, result)
    validate_events(event_types, event_schemas, path, result)


def validate_input_schema(
    input_schema: Any,
    path: str,
    type_code: str,
    props_code: str,
    result: ValidationResult,
) -> None:
    validate_schema_node(input_schema, path, result)
    if not isinstance(input_schema, dict):
        return
    if input_schema.get("type") != "object":
        result.add_issue(type_code, json_pointer(path, "type"), "inputSchema root type must be object")
    if not isinstance(input_schema.get("properties"), dict):
        result.add_issue(props_code, json_pointer(path, "properties"), "inputSchema must define properties object")


def validate_output_schema(output_schema: Any, path: str, result: ValidationResult) -> None:
    validate_schema_node(output_schema, path, result)
    if isinstance(output_schema, dict) and output_schema.get("type") != "object":
        result.add_issue("SCX003", json_pointer(path, "type"), "outputSchema root type must be object")


def validate_argument_mapping(mapping: Any, input_schema: Any, path: str, result: ValidationResult) -> None:
    if not isinstance(mapping, dict):
        result.add_issue("MAP001", path, "argMapping must be an object")
        return
    if not isinstance(input_schema, dict):
        result.add_issue("MAP005", path, "argMapping must be validated with a matching inputSchema")
        return
    if _is_empty_object(mapping):
        return
    mapping_type = mapping.get("type")
    if mapping_type is None:
        result.add_issue("MAP002", json_pointer(path, "type"), "argMapping.type is required")
        return
    if mapping_type not in SUPPORTED_MAPPING_TYPES:
        result.add_issue(
            "MAP003",
            json_pointer(path, "type"),
            "argMapping.type must be one of flag, positional, flattened, jsonString, mixed",
        )
        return
    _validate_mapping_unknown_fields(mapping, mapping_type, path, result)
    validator = _mapping_validator(mapping_type)
    validator(mapping, input_schema, path, result)


def validate_mapping_relationships(input_schema: Any, mapping: Any, path: str, result: ValidationResult) -> None:
    if not isinstance(input_schema, dict) or not isinstance(mapping, dict):
        return
    if _input_has_no_parameters(input_schema) and _is_empty_object(mapping):
        return

    properties = _schema_properties(input_schema)
    referenced = collect_mapping_references(mapping)
    property_keys = set(properties.keys())
    mapping_type = mapping.get("type")
    if mapping_type == "mixed":
        _validate_mixed_relationships(input_schema, mapping, path, result)
        return
    root_referenced = _collect_root_references(mapping_type, mapping, referenced)

    if _input_has_no_parameters(input_schema) != _is_empty_object(mapping):
        result.add_issue("REL001", path, "inputSchema and argMapping must both be empty when no parameters are defined")
        return
    extra_roots = root_referenced - property_keys
    if extra_roots:
        for root in sorted(extra_roots):
            if mapping_type == "flattened":
                result.add_issue("REL004", path, f"flattened root field '{root}' must exist in inputSchema.properties")
            else:
                result.add_issue("REL003", path, f"mapped field '{root}' is not defined in inputSchema.properties")
    if property_keys != root_referenced:
        result.add_issue("REL001", path, "inputSchema and argMapping must define the same parameter set")

    required = input_schema.get("required", [])
    if isinstance(required, list):
        for key in required:
            if isinstance(key, str) and key not in referenced and key not in root_referenced:
                result.add_issue("REL002", path, f"required field '{key}' is not mapped")


def validate_events(event_types: Any, event_schemas: Any, base_path: str, result: ValidationResult) -> None:
    event_types_path = json_pointer(base_path, "eventTypes") if base_path != "/" else "/eventTypes"
    event_schemas_path = json_pointer(base_path, "eventSchemas") if base_path != "/" else "/eventSchemas"

    if not _validate_event_types_payload(event_types, event_types_path, result):
        return
    if not _validate_event_schemas_payload(event_schemas, event_schemas_path, result):
        return
    _validate_declared_event_schemas(event_types, event_schemas, event_schemas_path, result)
    _validate_missing_custom_event_schemas(event_types, event_schemas, event_types_path, result)


def _validate_flag_mapping(
    mapping: dict[str, Any],
    input_schema: Any,
    path: str,
    result: ValidationResult,
) -> None:
    templates = mapping.get("templates")
    if "templates" not in mapping:
        result.add_issue("MAP101", json_pointer(path, "templates"), "flag mapping requires templates object")
        return
    if not isinstance(templates, dict):
        result.add_issue("MAP102", json_pointer(path, "templates"), "flag mapping templates must be an object")
        result.add_issue("MAP101", json_pointer(path, "templates"), "flag mapping requires templates object")
        return
    if not templates:
        result.add_issue("MAP103", json_pointer(path, "templates"), "templates must not be empty")
    properties = _schema_properties(input_schema)
    for key, value in templates.items():
        key_path = json_pointer(json_pointer(path, "templates"), key)
        if not key:
            result.add_issue("MAP111", key_path, "template key must not be empty")
            continue
        if key not in properties:
            result.add_issue(
                "MAP104",
                key_path,
                f"template key '{key}' is not defined in inputSchema.properties",
            )
            continue
        schema = properties[key]
        if not isinstance(schema, dict):
            continue
        _validate_flag_template_value(schema.get("type"), value, key_path, result)


def _validate_positional_mapping(mapping: dict, input_schema: Any, path: str, result: ValidationResult) -> None:
    order_path = json_pointer(path, "order")
    if "order" not in mapping:
        result.add_issue("MAP201", order_path, "positional mapping requires order")
        return
    order = mapping.get("order")
    if not (isinstance(order, list) and order and all(isinstance(item, str) and item for item in order)):
        result.add_issue("MAP202", order_path, "order must be a non-empty string array")
        return
    seen = set()
    properties = _schema_properties(input_schema)
    for item in order:
        item_path = json_pointer(order_path, item)
        if item in seen:
            result.add_issue("MAP203", order_path, f"duplicate positional field '{item}'")
            continue
        seen.add(item)
        if item not in properties:
            result.add_issue("MAP204", item_path, f"positional field '{item}' is not defined")
            continue
        schema = properties[item]
        if not isinstance(schema, dict):
            continue
        schema_type = schema.get("type")
        if schema_type == "object":
            result.add_issue("MAP205", item_path, "object field cannot be used in positional mapping")
            result.add_issue("REL005", item_path, "mapping type does not match field type")
        if schema_type == "array":
            result.add_issue("MAP206", item_path, "array field cannot be used in positional mapping")
            result.add_issue("REL005", item_path, "mapping type does not match field type")


def _validate_flattened_mapping(mapping: dict, input_schema: Any, path: str, result: ValidationResult) -> None:
    templates = mapping.get("templates")
    if not _require_templates_object(
        mapping,
        path,
        (
            "MAP301",
            "MAP302",
            "flattened mapping requires templates object",
            "flattened mapping templates must be an object",
        ),
        result,
    ):
        return
    if not templates:
        result.add_issue("MAP303", json_pointer(path, "templates"), "templates must not be empty")
    separator = _normalize_flattened_separator(mapping.get("separator"), path, "MAP304", result)

    for key, value in templates.items():
        _validate_flattened_template_entry(
            key,
            value,
            (separator, input_schema, path),
            result,
        )


def _validate_json_string_mapping(mapping: dict, input_schema: Any, path: str, result: ValidationResult) -> None:
    templates = mapping.get("templates")
    if not _require_templates_object(
        mapping,
        path,
        (
            "MAP401",
            "MAP402",
            "jsonString mapping requires templates object",
            "jsonString mapping templates must be an object",
        ),
        result,
    ):
        return
    if not templates:
        result.add_issue("MAP403", json_pointer(path, "templates"), "templates must not be empty")

    properties = _schema_properties(input_schema)
    for key, value in templates.items():
        key_path = json_pointer(json_pointer(path, "templates"), key)
        if key not in properties:
            result.add_issue(
                "MAP404",
                key_path,
                f"template key '{key}' is not defined in inputSchema.properties",
            )
            continue
        schema = properties[key]
        if not isinstance(schema, dict):
            continue
        _validate_json_string_template_value(schema.get("type"), value, key_path, result)


def _validate_mixed_mapping(mapping: dict, input_schema: Any, path: str, result: ValidationResult) -> None:
    mappings_path = json_pointer(path, "mappings")
    if "mappings" not in mapping:
        result.add_issue("MAP501", mappings_path, "mixed mapping requires mappings object")
        return
    mappings = mapping.get("mappings")
    if not isinstance(mappings, dict) or not mappings:
        result.add_issue("MAP502", mappings_path, "mappings must be a non-empty object")
        return

    properties = _schema_properties(input_schema)
    seen_positional_orders: dict[int, str] = {}
    consumed_refs: dict[str, str] = {}

    for param, entry in mappings.items():
        _validate_mixed_entry(
            param,
            entry,
            (properties, input_schema, mappings_path, seen_positional_orders, consumed_refs),
            result,
        )


def _validate_mixed_flag_entry(param: str, entry: dict, schema_type: Any, path: str, result: ValidationResult) -> None:
    template_path = json_pointer(path, "template")
    if "template" not in entry:
        result.add_issue("MAP505", template_path, "flag mixed entry requires template")
        return
    if "order" in entry or "separator" in entry:
        result.add_issue("MAP504", path, "flag mixed entry only uses mode and template")
    template = entry.get("template")
    if not isinstance(template, (str, dict)):
        result.add_issue("MAP505", template_path, "flag mixed entry template must be string or object")
        return
    if isinstance(template, dict):
        _validate_boolean_object_template(schema_type, template, template_path, result)
    else:
        _validate_flag_string_template(schema_type, template, template_path, result)


def _validate_mixed_json_string_entry(
    param: str,
    entry: dict,
    schema_type: Any,
    path: str,
    result: ValidationResult,
) -> None:
    template_path = json_pointer(path, "template")
    if "template" not in entry:
        result.add_issue("MAP505", template_path, "jsonString mixed entry requires template")
        return
    if "order" in entry or "separator" in entry:
        result.add_issue("MAP504", path, "jsonString mixed entry only uses mode and template")
    template = entry.get("template")
    if not isinstance(template, (str, dict)):
        result.add_issue("MAP505", template_path, "jsonString mixed entry template must be string or object")
        return
    _validate_json_string_template_value(schema_type, template, template_path, result)


def _validate_mixed_positional_entry(
    param: str,
    entry: dict,
    schema_type: Any,
    path: str,
    result: ValidationResult,
) -> None:
    order_path = json_pointer(path, "order")
    if "template" in entry or "separator" in entry:
        result.add_issue("MAP506", path, "positional mixed entry only allows mode and order")
    order = entry.get("order")
    if not (is_integer_value(order) and order > 0):
        result.add_issue("MAP506", order_path, "positional mixed entry order must be a positive integer")
    if schema_type == "object":
        result.add_issue("MAP205", path, "object field cannot be used in positional mapping")
        result.add_issue("REL005", path, "mapping type does not match field type")
    if schema_type == "array":
        result.add_issue("MAP206", path, "array field cannot be used in positional mapping")
        result.add_issue("REL005", path, "mapping type does not match field type")


def _validate_mixed_flattened_entry(
    param: str,
    entry: dict,
    input_schema: Any,
    path: str,
    result: ValidationResult,
) -> None:
    template_path = json_pointer(path, "template")
    if "order" in entry:
        result.add_issue("MAP507", path, "flattened mixed entry only allows mode, template and separator")
    if "template" not in entry:
        result.add_issue("MAP507", template_path, "flattened mixed entry requires non-empty template object")
        return
    template = entry.get("template")
    if not isinstance(template, dict) or not template:
        result.add_issue("MAP507", template_path, "flattened mixed entry template must be a non-empty object")
        return
    separator = _normalize_flattened_separator(
        entry.get("separator"),
        path,
        "MAP507",
        result,
        "flattened mixed entry separator must be one of '.', '_' or '-'",
    )
    prefix = f"{param}{separator}"
    for key in template.keys():
        key_path = json_pointer(template_path, key)
        if not isinstance(key, str) or not key.startswith(prefix):
            result.add_issue("MAP508", key_path, f"flattened template key must start with '{prefix}'")
    flattened_mapping = {
        "type": "flattened",
        "separator": separator,
        "templates": template,
    }
    _validate_flattened_mapping(flattened_mapping, input_schema, path, result)


def _record_mixed_consumption(consumed_refs: dict[str, str], ref: str, path: str, result: ValidationResult) -> None:
    previous = consumed_refs.get(ref)
    if previous is not None:
        result.add_issue("MAP509", path, f"mixed field or path '{ref}' is consumed more than once")
    else:
        consumed_refs[ref] = path


def _validate_mixed_relationships(input_schema: Any, mapping: dict, path: str, result: ValidationResult) -> None:
    if _input_has_no_parameters(input_schema) and _is_empty_object(mapping):
        return
    properties = _schema_properties(input_schema)
    property_keys = set(properties.keys())
    mappings = mapping.get("mappings")
    if not isinstance(mappings, dict):
        if _input_has_no_parameters(input_schema) != _is_empty_object(mapping):
            message = "inputSchema and argMapping must both be empty when no parameters are defined"
            result.add_issue("REL001", path, message)
        return
    root_referenced = {key for key in mappings.keys() if isinstance(key, str)}

    if _input_has_no_parameters(input_schema):
        result.add_issue("REL001", path, "inputSchema and argMapping must both be empty when no parameters are defined")
        return

    extra_roots = root_referenced - property_keys
    if extra_roots:
        for root in sorted(extra_roots):
            mode = mappings.get(root, {}).get("mode") if isinstance(mappings.get(root), dict) else None
            if mode == "flattened":
                result.add_issue("REL004", path, f"flattened root field '{root}' must exist in inputSchema.properties")
            else:
                result.add_issue("REL003", path, f"mapped field '{root}' is not defined in inputSchema.properties")
    if property_keys != root_referenced:
        result.add_issue("REL001", path, "inputSchema and argMapping must define the same parameter set")

    required = input_schema.get("required", [])
    if isinstance(required, list):
        for key in required:
            if isinstance(key, str) and key not in root_referenced:
                result.add_issue("REL002", path, f"required field '{key}' is not mapped")


def _validate_unknown_fields(
    data: dict[str, Any],
    supported_fields: set[str],
    path: str,
    issue: tuple[str, str],
    result: ValidationResult,
) -> None:
    code, message = issue
    for key in data.keys():
        if key not in supported_fields:
            result.add_issue(code, json_pointer(path, key), message)


def _validate_subcommand_required_fields(
    subcommand: dict[str, Any],
    path: str,
    result: ValidationResult,
) -> bool:
    _validate_unknown_fields(
        subcommand,
        SUPPORTED_SUBCOMMAND_FIELDS,
        path,
        ("SUB007", "unknown subcommand field"),
        result,
    )
    _require_non_empty_string(subcommand, "description", "SUB003", result, parent=path)
    if "description" not in subcommand:
        result.add_issue("SUB002", json_pointer(path, "description"), "subcommand must define description")
    if "inputSchema" not in subcommand:
        result.add_issue("SUB004", json_pointer(path, "inputSchema"), "subcommand must define input")
        return False
    if "argMapping" not in subcommand:
        result.add_issue("SUB005", json_pointer(path, "argMapping"), "subcommand must define argMapping")
        return False
    return True


def _validate_subcommand_optional_fields(
    subcommand: dict[str, Any],
    path: str,
    result: ValidationResult,
) -> None:
    _validate_permissions(
        subcommand.get("requirePermissions"),
        json_pointer(path, "requirePermissions"),
        ("SUB010", "SUB010"),
        result,
        allow_duplicates=True,
    )
    _validate_timeout(
        subcommand.get("timeout"),
        json_pointer(path, "timeout"),
        ("SUB011", "SUB011"),
        result,
    )
    _validate_event_types(
        subcommand.get("eventTypes"),
        json_pointer(path, "eventTypes"),
        ("SUB008", "SUB008"),
        result,
        allow_duplicates=True,
    )
    _validate_object_field(
        subcommand.get("eventSchemas"),
        json_pointer(path, "eventSchemas"),
        "SUB009",
        "subcommand eventSchemas must be an object",
        result,
    )


def _validate_subcommand_schema_and_mapping(
    subcommand: dict[str, Any],
    path: str,
    result: ValidationResult,
) -> None:
    input_schema_path = json_pointer(path, "inputSchema")
    mapping_path = json_pointer(path, "argMapping")
    input_schema = subcommand.get("inputSchema")
    arg_mapping = subcommand.get("argMapping")
    validate_input_schema(input_schema, input_schema_path, "SCX004", "SCX005", result)
    _validate_subcommand_output_schema(subcommand.get("outputSchema"), path, result)
    validate_argument_mapping(arg_mapping, input_schema, mapping_path, result)
    validate_mapping_relationships(input_schema, arg_mapping, mapping_path, result)


def _validate_subcommand_output_schema(
    output_schema: Any,
    path: str,
    result: ValidationResult,
) -> None:
    if output_schema is None:
        return
    output_schema_path = json_pointer(path, "outputSchema")
    validate_output_schema(output_schema, output_schema_path, result)
    if isinstance(output_schema, dict) and output_schema.get("type") == "object":
        return
    result.add_issue(
        "SUB006",
        output_schema_path,
        "subcommand outputSchema must be a valid object schema",
    )


def _validate_top_level_executable(executable_path: Any, result: ValidationResult) -> None:
    if isinstance(executable_path, str) and not executable_path.startswith("/"):
        result.add_issue("TOP005", "/executablePath", "executablePath must be an absolute path")


def _validate_permissions(
    permissions: Any,
    path: str,
    codes: tuple[str, str],
    result: ValidationResult,
    allow_duplicates: bool = False,
) -> None:
    type_code, duplicate_code = codes
    if permissions is None:
        return
    if not _is_string_list(permissions):
        result.add_issue(type_code, path, "requirePermissions must be a string array")
        return
    if not allow_duplicates and len(set(permissions)) != len(permissions):
        result.add_issue(duplicate_code, path, "requirePermissions must not contain duplicates")


def _validate_timeout(
    timeout: Any,
    path: str,
    codes: tuple[str, str],
    result: ValidationResult,
) -> None:
    type_code, range_code = codes
    if timeout is None:
        return
    if not is_integer_value(timeout):
        result.add_issue(type_code, path, "timeout must be an integer")
    elif timeout < 0:
        result.add_issue(range_code, path, "timeout must be >= 0")


def _validate_event_types(
    event_types: Any,
    path: str,
    codes: tuple[str, str],
    result: ValidationResult,
    allow_duplicates: bool = False,
) -> None:
    type_code, duplicate_code = codes
    if event_types is None:
        return
    if not _is_string_list(event_types):
        result.add_issue(type_code, path, "eventTypes must be a string array")
        return
    if not allow_duplicates and len(set(event_types)) != len(event_types):
        result.add_issue(duplicate_code, path, "eventTypes must not contain duplicates")


def _validate_event_schemas_type(
    data: dict[str, Any],
    path: str,
    code: str,
    result: ValidationResult,
) -> None:
    if "eventSchemas" in data and not isinstance(data["eventSchemas"], dict):
        result.add_issue(code, path, "eventSchemas must be an object")


def _validate_object_field(
    value: Any,
    path: str,
    code: str,
    message: str,
    result: ValidationResult,
) -> None:
    if value is not None and not isinstance(value, dict):
        result.add_issue(code, path, message)


def _validate_mapping_unknown_fields(
    mapping: dict[str, Any],
    mapping_type: str,
    path: str,
    result: ValidationResult,
) -> None:
    for key in mapping.keys():
        if key in ALLOWED_MAPPING_KEYS[mapping_type]:
            continue
        key_path = json_pointer(path, key)
        if mapping_type == "flattened":
            result.add_issue(
                "MAP313",
                key_path,
                "flattened mapping only allows type, separator and templates",
            )
        elif mapping_type == "positional":
            result.add_issue("MAP207", key_path, "positional mapping only allows type and order")
        else:
            result.add_issue("MAP004", key_path, f"unknown field for {mapping_type} mapping")


def _mapping_validator(mapping_type: str):
    validators = {
        "flag": _validate_flag_mapping,
        "positional": _validate_positional_mapping,
        "flattened": _validate_flattened_mapping,
        "jsonString": _validate_json_string_mapping,
        "mixed": _validate_mixed_mapping,
    }
    return validators[mapping_type]


def _collect_root_references(
    mapping_type: str,
    mapping: dict[str, Any],
    referenced: set[str],
) -> set[str]:
    if mapping_type != "flattened":
        return {ref.split(".")[0] for ref in referenced}
    separator = mapping.get("separator", ".")
    if separator not in {".", "_", "-"}:
        separator = "."
    return {ref.split(separator)[0] for ref in referenced}


def _validate_event_types_payload(
    event_types: Any,
    event_types_path: str,
    result: ValidationResult,
) -> bool:
    if event_types is None:
        return True
    if not _is_string_list(event_types):
        result.add_issue("EVT001", event_types_path, "eventTypes must be a string array")
        return False
    for invalid in [value for value in event_types if not _is_valid_declared_event_type(value)]:
        message = f"custom event name must match [A-Za-z][A-Za-z0-9_.-]*: '{invalid}'"
        result.add_issue("EVT007", event_types_path, message)
    return True


def _validate_event_schemas_payload(
    event_schemas: Any,
    event_schemas_path: str,
    result: ValidationResult,
) -> bool:
    if event_schemas is None:
        return True
    if not isinstance(event_schemas, dict):
        result.add_issue("EVT002", event_schemas_path, "eventSchemas must be an object")
        return False
    return True


def _validate_declared_event_schemas(
    event_types: Any,
    event_schemas: Any,
    event_schemas_path: str,
    result: ValidationResult,
) -> None:
    if not isinstance(event_schemas, dict):
        return
    for key, schema in event_schemas.items():
        key_path = json_pointer(event_schemas_path, key)
        if key in RESERVED_EVENT_TYPES:
            result.add_issue("EVT006", key_path, f"{key} must not be declared in eventSchemas")
            continue
        if not isinstance(event_types, list) or key not in event_types:
            result.add_issue("EVT003", key_path, "event schema key must exist in events")
        if not _is_valid_custom_event_name(key):
            result.add_issue(
                "EVT007",
                key_path,
                "custom event name must match [A-Za-z][A-Za-z0-9_.-]*",
            )
        if not isinstance(schema, dict):
            result.add_issue("EVT005", key_path, "event schema must be an object")
            continue
        validate_schema_node(schema, key_path, result)


def _validate_missing_custom_event_schemas(
    event_types: Any,
    event_schemas: Any,
    event_types_path: str,
    result: ValidationResult,
) -> None:
    if not isinstance(event_types, list):
        return
    schema_keys = set(event_schemas.keys()) if isinstance(event_schemas, dict) else set()
    for event_name in [name for name in event_types if name not in BUILTIN_EVENT_TYPES]:
        if event_name not in schema_keys:
            message = f"custom event '{event_name}' must be declared in eventSchemas"
            result.add_issue("EVT008", event_types_path, message)


def _validate_flag_template_value(
    schema_type: Any,
    value: Any,
    key_path: str,
    result: ValidationResult,
) -> None:
    if isinstance(value, dict):
        _validate_boolean_object_template(schema_type, value, key_path, result)
        return
    if isinstance(value, str):
        _validate_flag_string_template(schema_type, value, key_path, result)
        return
    result.add_issue("MAP105", key_path, "template value must be string or object")


def _validate_boolean_object_template(
    schema_type: Any,
    value: dict[str, Any],
    key_path: str,
    result: ValidationResult,
) -> None:
    if set(value.keys()) - {"if_true", "if_false"}:
        result.add_issue("MAP106", key_path, "flag template object only allows if_true and if_false")
    if "if_true" not in value or "if_false" not in value:
        result.add_issue("MAP107", key_path, "flag template object must define both if_true and if_false")
    if schema_type != "boolean":
        result.add_issue("MAP108", key_path, "if_true/if_false can only be used with boolean fields")


def _validate_flag_string_template(
    schema_type: Any,
    value: str,
    key_path: str,
    result: ValidationResult,
) -> None:
    if schema_type == "object":
        result.add_issue("MAP109", key_path, "object field must not use flag mapping")
        result.add_issue("REL005", key_path, "mapping type does not match field type")
    if schema_type == "array" and "{value}" not in value:
        result.add_issue("MAP110", key_path, "array flag template must contain {value}")
    if "{value}" not in value:
        result.add_issue("MAP112", key_path, "flag string template must contain {value}")


def _require_templates_object(
    mapping: dict[str, Any],
    path: str,
    messages: tuple[str, str, str, str],
    result: ValidationResult,
) -> bool:
    missing_code, type_code, missing_message, type_message = messages
    templates_path = json_pointer(path, "templates")
    if "templates" not in mapping:
        result.add_issue(missing_code, templates_path, missing_message)
        return False
    if not isinstance(mapping.get("templates"), dict):
        result.add_issue(type_code, templates_path, type_message)
        result.add_issue(missing_code, templates_path, missing_message)
        return False
    return True


def _normalize_flattened_separator(
    separator: Any,
    path: str,
    code: str,
    result: ValidationResult,
    message: str = "separator must be one of '.', '_' or '-'",
) -> str:
    if separator is None:
        return "."
    if not isinstance(separator, str) or separator not in {".", "_", "-"}:
        result.add_issue(code, json_pointer(path, "separator"), message)
        return "."
    return separator


def _validate_flattened_template_entry(
    key: str,
    value: Any,
    context: tuple[str, Any, str],
    result: ValidationResult,
) -> None:
    separator, input_schema, path = context
    key_path = json_pointer(json_pointer(path, "templates"), key)
    if not isinstance(value, (str, dict)):
        result.add_issue("MAP105", key_path, "template value must be string or object")
    if _has_wrong_flattened_separator(key, separator):
        result.add_issue(
            "MAP312",
            key_path,
            "flattened path must use the configured separator consistently",
        )
        return
    if separator not in key:
        result.add_issue("MAP305", key_path, "flattened template key must be a nested path")
        return
    status, schema = resolve_schema_path_detail(input_schema, key.split(separator))
    if not _handle_flattened_resolution_status(status, key, key_path, result):
        return
    if not isinstance(schema, dict):
        result.add_issue("MAP306", key_path, f"flattened path '{key}' is not defined")
        return
    _validate_flattened_leaf(schema.get("type"), value, key_path, result)


def _has_wrong_flattened_separator(key: str, separator: str) -> bool:
    wrong = {candidate for candidate in {".", "_", "-"} - {separator} if candidate in key}
    return bool(wrong)


def _handle_flattened_resolution_status(
    status: str,
    key: str,
    key_path: str,
    result: ValidationResult,
) -> bool:
    if status == "ok":
        return True
    if status == "path_missing":
        result.add_issue("MAP306", key_path, f"flattened path '{key}' is not defined")
    elif status == "intermediate_not_object":
        result.add_issue("MAP307", key_path, "flattened path intermediate nodes must be object")
    elif status == "leaf_missing":
        result.add_issue("MAP308", key_path, "flattened path leaf field must be declared")
    else:
        result.add_issue("MAP306", key_path, f"flattened path '{key}' is not defined")
    return False


def _validate_flattened_leaf(
    schema_type: Any,
    value: Any,
    key_path: str,
    result: ValidationResult,
) -> None:
    if schema_type == "object":
        result.add_issue("MAP309", key_path, "flattened leaf field must not be object")
        return
    if schema_type == "array":
        result.add_issue("MAP310", key_path, "flattened leaf field must not be array")
        return
    if schema_type == "boolean":
        _validate_boolean_flattened_template(value, key_path, result)
        return
    if isinstance(value, dict):
        result.add_issue(
            "MAP311",
            key_path,
            "boolean template object can only be used on boolean leaf fields",
        )


def _validate_boolean_flattened_template(value: Any, key_path: str, result: ValidationResult) -> None:
    if isinstance(value, str):
        if "{value}" not in value:
            result.add_issue(
                "MAP311",
                key_path,
                "boolean flattened string template must contain {value}",
            )
        return
    if not isinstance(value, dict):
        return
    if set(value.keys()) - {"if_true", "if_false"}:
        result.add_issue(
            "MAP311",
            key_path,
            "boolean flattened template object only allows if_true and if_false",
        )
    elif "if_true" not in value and "if_false" not in value:
        result.add_issue(
            "MAP311",
            key_path,
            "boolean flattened template object must define if_true or if_false",
        )


def _validate_json_string_template_value(
    schema_type: Any,
    value: Any,
    key_path: str,
    result: ValidationResult,
) -> None:
    if isinstance(value, dict):
        _validate_json_string_object_template(schema_type, key_path, value, result)
        return
    if isinstance(value, str):
        _validate_json_string_string_template(schema_type, key_path, value, result)
        return
    result.add_issue("MAP405", key_path, "template value must be string or object")


def _validate_json_string_object_template(
    schema_type: Any,
    key_path: str,
    value: dict[str, Any],
    result: ValidationResult,
) -> None:
    if set(value.keys()) - {"if_true", "if_false"}:
        result.add_issue(
            "MAP405",
            key_path,
            "jsonString template object only allows if_true and if_false",
        )
    if schema_type != "boolean":
        result.add_issue("MAP407", key_path, "if_true/if_false can only be used with boolean fields")
        result.add_issue("MAP410", key_path, "object/array fields must not use if_true/if_false")


def _validate_json_string_string_template(
    schema_type: Any,
    key_path: str,
    value: str,
    result: ValidationResult,
) -> None:
    if schema_type == "boolean" and "{value}" not in value:
        result.add_issue(
            "MAP409",
            key_path,
            "boolean jsonString template must contain {value} when using string form",
        )
    elif "{value}" not in value:
        result.add_issue("MAP408", key_path, "template must use the supported {value} placeholder")


def _validate_mixed_entry(
    param: str,
    entry: Any,
    context: tuple[dict[str, dict], Any, str, dict[int, str], dict[str, str]],
    result: ValidationResult,
) -> None:
    properties, input_schema, mappings_path, seen_positional_orders, consumed_refs = context
    entry_path = json_pointer(mappings_path, param)
    if not isinstance(entry, dict):
        result.add_issue("MAP504", entry_path, "mixed mapping entry must be an object")
        return
    mode = entry.get("mode")
    if not _validate_mixed_entry_mode(mode, entry_path, result):
        return
    _validate_mixed_entry_fields(entry, entry_path, result)

    schema = properties.get(param)
    schema_type = schema.get("type") if isinstance(schema, dict) else None
    if mode == "flag":
        _validate_mixed_flag_entry(param, entry, schema_type, entry_path, result)
        _record_mixed_consumption(consumed_refs, param, entry_path, result)
    elif mode == "jsonString":
        _validate_mixed_json_string_entry(param, entry, schema_type, entry_path, result)
        _record_mixed_consumption(consumed_refs, param, entry_path, result)
    elif mode == "positional":
        _validate_mixed_positional_entry(param, entry, schema_type, entry_path, result)
        _record_mixed_order(param, entry, entry_path, seen_positional_orders, result)
        _record_mixed_consumption(consumed_refs, param, entry_path, result)
    elif mode == "flattened":
        _validate_mixed_flattened_entry(param, entry, input_schema, entry_path, result)
        _record_mixed_template_refs(entry.get("template"), entry_path, consumed_refs, result)


def _validate_mixed_entry_mode(mode: Any, entry_path: str, result: ValidationResult) -> bool:
    if mode in {"flag", "positional", "flattened", "jsonString"}:
        return True
    result.add_issue(
        "MAP503",
        json_pointer(entry_path, "mode"),
        "mixed mapping mode must be one of flag, positional, flattened, jsonString",
    )
    return False


def _validate_mixed_entry_fields(entry: dict[str, Any], entry_path: str, result: ValidationResult) -> None:
    for key in entry.keys():
        if key not in {"mode", "template", "separator", "order"}:
            result.add_issue(
                "MAP504",
                json_pointer(entry_path, key),
                "mixed entry only allows mode, template, separator and order",
            )


def _record_mixed_order(
    param: str,
    entry: dict[str, Any],
    entry_path: str,
    seen_positional_orders: dict[int, str],
    result: ValidationResult,
) -> None:
    order = entry.get("order")
    if not (is_integer_value(order) and order > 0):
        return
    if order in seen_positional_orders:
        result.add_issue("MAP510", json_pointer(entry_path, "order"), f"duplicate positional order '{order}'")
        return
    seen_positional_orders[order] = param


def _record_mixed_template_refs(
    template: Any,
    entry_path: str,
    consumed_refs: dict[str, str],
    result: ValidationResult,
) -> None:
    if not isinstance(template, dict):
        return
    for ref in template.keys():
        if isinstance(ref, str):
            _record_mixed_consumption(consumed_refs, ref, entry_path, result)


def _schema_properties(input_schema: Any) -> dict[str, dict]:
    if isinstance(input_schema, dict) and isinstance(input_schema.get("properties"), dict):
        return input_schema["properties"]
    return {}


def collect_mapping_references(mapping: dict) -> set[str]:
    mapping_type = mapping.get("type")
    if mapping_type == "positional":
        order = mapping.get("order", [])
        return {item for item in order if isinstance(item, str)}
    templates = mapping.get("templates", {})
    if isinstance(templates, dict):
        return {key for key in templates.keys() if isinstance(key, str)}
    return set()


def _require_non_empty_string(
    data: dict[str, Any],
    field: str,
    code: str,
    result: ValidationResult,
    parent: str = "",
) -> None:
    path = json_pointer(parent, field) if parent else json_pointer("", field)
    value = data.get(field)
    if not isinstance(value, str) or not value:
        result.add_issue(code, path, f"{field} must be a non-empty string")


def _validate_tool_name(value: Any, path: str, result: ValidationResult) -> None:
    if not isinstance(value, str) or not value:
        return
    if not TOOL_NAME_PATTERN.fullmatch(value):
        result.add_issue("TOP014", path, "name must match prefix-toolName using letters, digits, and hyphen")
        return
    prefix, suffix = value.split("-", 1)
    if prefix not in ALLOWED_TOOL_PREFIXES:
        result.add_issue("TOP014", path, "name prefix must be 'ohos' or 'hms'")
        return
    if len(suffix) > 16:
        result.add_issue("TOP015", path, "toolName segment after prefix- must be at most 16 characters")


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _is_valid_custom_event_name(value: str) -> bool:
    if not isinstance(value, str) or not value:
        return False
    if value in RESERVED_EVENT_TYPES:
        return False
    if not value[0].isalpha():
        return False
    return all(ch.isalnum() or ch in {"_", "-", "."} for ch in value[1:])


def _is_valid_declared_event_type(value: str) -> bool:
    if value in RESERVED_EVENT_TYPES:
        return True
    return _is_valid_custom_event_name(value)


def _is_empty_object(value: Any) -> bool:
    return isinstance(value, dict) and not value


def _input_has_no_parameters(value: Any) -> bool:
    return isinstance(value, dict) and isinstance(value.get("properties"), dict) and not value.get("properties")
