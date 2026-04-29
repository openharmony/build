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

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: str
    message: str


@dataclass
class ValidationResult:
    file: str
    valid: bool = True
    issues: list[ValidationIssue] = field(default_factory=list)

    def add_issue(self, code: str, path: str, message: str) -> None:
        self.valid = False
        self.issues.append(ValidationIssue(code=code, path=path, message=message))

    def sort_issues(self) -> None:
        self.issues.sort(key=lambda issue: (issue.path, issue.code, issue.message))


SUPPORTED_TOP_LEVEL_FIELDS = {
    "name",
    "version",
    "description",
    "executablePath",
    "requirePermissions",
    "eventTypes",
    "eventSchemas",
    "hasSubcommands",
    "inputSchema",
    "outputSchema",
    "subcommands",
}

SUPPORTED_SUBCOMMAND_FIELDS = {
    "description",
    "requirePermissions",
    "inputSchema",
    "outputSchema",
    "eventTypes",
    "eventSchemas",
}

SUPPORTED_SCHEMA_TYPES = {"string", "number", "integer", "boolean", "array", "object"}

SUPPORTED_STRING_FORMATS = {
    "ipv4",
    "ipv6",
    "hostname",
    "email",
    "uri",
    "date",
    "date-time",
}

SCHEMA_ALLOWED_KEYS = {
    "string": {"type", "description", "default", "enum", "minLength", "maxLength", "pattern", "format"},
    "number": {
        "type",
        "description",
        "default",
        "enum",
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "multipleOf",
    },
    "integer": {
        "type",
        "description",
        "default",
        "enum",
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "multipleOf",
    },
    "boolean": {"type", "description", "default"},
    "array": {"type", "description", "default", "items", "minItems", "maxItems", "uniqueItems"},
    "object": {"type", "description", "default", "properties", "required"},
}

RESERVED_EVENT_TYPES = {"result"}


def is_integer_value(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def is_number_value(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def json_pointer(parent: str, child: str) -> str:
    base = parent.rstrip("/")
    escaped = child.replace("~", "~0").replace("/", "~1")
    return f"{base}/{escaped}" if base else f"/{escaped}"
