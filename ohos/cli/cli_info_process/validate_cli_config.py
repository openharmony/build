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

"""Validate CLI tool config.json files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from .validation_loader import load_json_file
    from .validation_rules import validate_config
except ImportError:
    from validation_loader import load_json_file
    from validation_rules import validate_config


def validate_config_result(config_file: str):
    result, data = load_json_file(Path(config_file))
    if data is not None:
        validate_config(data, result)
    result.sort_issues()
    return result, data


def format_result_text(result) -> str:
    lines = [f"[FAIL] {result.file}"]
    for issue in result.issues:
        lines.append(f"  - {issue.code} {issue.path}: {issue.message}")
    return "\n".join(lines)


def format_result_json(result) -> str:
    payload = {
        "file": result.file,
        "valid": result.valid,
        "issues": [
            {"code": issue.code, "path": issue.path, "message": issue.message}
            for issue in result.issues
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def validate_config_file(config_file: str) -> dict:
    result, data = validate_config_result(config_file)
    if not result.valid or data is None:
        raise ValueError(format_result_text(result))
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate CLI tool config.json file")
    parser.add_argument("--config-file", required=True, help="Path to config.json file")
    parser.add_argument("--output-file", help="Output stamp file (optional)")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Render result as JSON")
    args = parser.parse_args()

    result, data = validate_config_result(args.config_file)
    if not result.valid or data is None:
        print(format_result_json(result) if args.json_output else format_result_text(result), file=sys.stderr)
        return 1

    print(f"Validation successful: {data['name']}")
    if data.get("hasSubcommands"):
        print("  Type: Subcommand tool")
        print(f"  Subcommands: {', '.join(data['subcommands'].keys())}")
    else:
        print("  Type: Simple tool")

    if args.output_file:
        Path(args.output_file).write_text("validated\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
