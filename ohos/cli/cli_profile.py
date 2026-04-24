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

"""Generate CLI tool installation information"""

import argparse
import dataclasses
import json
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(ROOT_DIR)

try:
    from build.ohos.cli.cli_info_process.validate_cli_config import validate_config_file  # noqa: E402
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from cli_info_process.validate_cli_config import validate_config_file  # noqa: E402


@dataclasses.dataclass
class CliToolConfig:

    config_file: str
    tool_name: str
    output_info_file: str
    subsystem_name: str = ""
    part_name: str = ""
    final_executable: str = ""
    output_config_file: str = ""


def write_ordered_json_file(output_file: str, content: object) -> None:
    file_dir = os.path.dirname(os.path.abspath(output_file))
    if not os.path.exists(file_dir):
        os.makedirs(file_dir, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as output_f:
        json.dump(content, output_f, ensure_ascii=False, indent=2, sort_keys=False)


def validate_tool_name(config: dict, tool_name: str) -> None:
    config_name = config.get("name")
    if config_name != tool_name:
        message = (
            f"config name '{config_name}' must equal "
            f"ohos_cli_executable target_name '{tool_name}'"
        )
        raise ValueError(message)


def generate_tool_info(config: CliToolConfig, validated_config: dict) -> dict:
    return {
        "tool_name": config.tool_name,
        "config_file": config.config_file,
        "subsystem_name": config.subsystem_name,
        "part_name": config.part_name,
        "config": validated_config,
        "output_config_file": config.output_config_file,
    }


def generate_cli_info(config: CliToolConfig) -> None:
    validated_config = validate_config_file(config.config_file)
    validate_tool_name(validated_config, config.tool_name)

    if config.final_executable:
        validated_config["executablePath"] = config.final_executable

    info = generate_tool_info(config, validated_config)
    write_ordered_json_file(config.output_info_file, info)

    if config.output_config_file:
        write_ordered_json_file(config.output_config_file, validated_config)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate CLI tool installation information"
    )
    parser.add_argument("--config-file", required=True, help="Path to config.json file")
    parser.add_argument("--tool-name", required=True, help="Name of the CLI tool")
    parser.add_argument(
        "--output-info-file", required=True, help="Output info file path"
    )
    parser.add_argument("--subsystem-name", default="", help="Subsystem name")
    parser.add_argument("--part-name", default="", help="Part name")
    parser.add_argument(
        "--final-executable", default="", help="Final installed executable absolute path"
    )
    parser.add_argument(
        "--output-config-file", default="", help="Output exported tool config file path"
    )
    return parser


def main() -> int:
    parser = build_argument_parser()
    args = parser.parse_args()

    try:
        config = CliToolConfig(
            config_file=args.config_file,
            tool_name=args.tool_name,
            output_info_file=args.output_info_file,
            subsystem_name=args.subsystem_name,
            part_name=args.part_name,
            final_executable=args.final_executable,
            output_config_file=args.output_config_file,
        )
        generate_cli_info(config)
        print(f"Generated: {args.output_info_file}")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
