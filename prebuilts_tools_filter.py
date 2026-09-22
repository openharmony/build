#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Huawei Device Co., Ltd.
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

import sys
import json
import os
import shutil
from typing import NoReturn


def main():
    if len(sys.argv) != 5:
        print(
            "Usage: prebuilts_tools_filter.py <config.json> <tools.json> <host_platform> <host_cpu>",
            file=sys.stderr,
        )
        sys.exit(1)

    config_file = sys.argv[1]
    tools_file = sys.argv[2]
    host_platform = sys.argv[3]
    host_cpu = sys.argv[4]

    with open(config_file) as f:
        config = json.load(f)

    with open(tools_file) as f:
        tools_config = json.load(f)

    tool_specs = tools_config.get("tool_list")
    if not tool_specs:
        # empty tool list: copy master config as-is
        output_file = _resolve_output(config_file, "prebuilts_config.json")
        shutil.copy2(config_file, output_file)
        print(output_file)
        return

    selected = {}
    for item in tool_specs:
        if not isinstance(item, dict):
            die(
                'invalid tool item %s in %s: expected an object like {"name": ..., "variants": ...}'
                % (item, tools_file)
            )
        name = item.get("name")
        if not name:
            die("tool name is missing in %s" % tools_file)
        variants = item.get("variants")
        if isinstance(variants, dict):
            variants = _select_variants(
                variants, host_platform, host_cpu, name, tools_file
            )
        selected[name] = set(variants) if variants else None

    pruned = []
    for tool in config["tool_list"]:
        name = tool["name"]
        if name not in selected:
            continue
        variants = selected[name]
        if variants:
            original_config = tool.get("config")
            tool = _filter_tool_variants(tool, variants)
            if tool is None:
                die(
                    "tool %s: none of the variants %s matched host %s/%s"
                    % (name, sorted(variants), host_platform, host_cpu)
                )
            if (
                original_config
                and not _host_bucket_empty(original_config, host_platform, host_cpu)
                and _host_bucket_empty(tool.get("config"), host_platform, host_cpu)
            ):
                die(
                    "tool %s: variants %s left no entries for host %s/%s"
                    % (name, sorted(variants), host_platform, host_cpu)
                )
        pruned.append(tool)

    found = set(t["name"] for t in pruned)
    not_found = set(selected) - found
    if not_found:
        die(
            "tool %s not found in prebuilts config, please check the tool list file"
            % sorted(not_found)
        )

    config["tool_list"] = pruned
    output_file = _resolve_output(config_file, "prebuilts_config_pruned.json")
    with open(output_file, "w") as f:
        json.dump(config, f, indent=4)
    print(output_file)


def _select_variants(variants, host_platform, host_cpu, name, tools_file):
    # nested like prebuilts_config.json tool "config":
    #   {"linux": {"x86_64": [...], "arm64": [...]}, "any": {"any": [...]}}
    # os/cpu keys support comma-separated lists and "any", same as
    # ConfigParser._match_os/_match_cpu
    selected = set()
    for os_key, cpu_config in variants.items():
        os_list = [o.strip() for o in str(os_key).split(",")]
        if not (host_platform in os_list or os_list == ["any"]):
            continue
        if not isinstance(cpu_config, dict):
            die("tool %s: invalid variants for %s in %s" % (name, os_key, tools_file))
        for cpu_key, cpu_variants in cpu_config.items():
            cpu_list = [c.strip() for c in str(cpu_key).split(",")]
            if not (host_cpu in cpu_list or cpu_list == ["any"]):
                continue
            if not isinstance(cpu_variants, list):
                die(
                    "tool %s: invalid variants for %s/%s in %s"
                    % (name, os_key, cpu_key, tools_file)
                )
            selected.update(cpu_variants)
    if not selected:
        die(
            "tool %s: no variants configured for host %s/%s in %s"
            % (name, host_platform, host_cpu, tools_file)
        )
    return selected


def _host_bucket_empty(config, host_platform, host_cpu):
    # check with the same os/cpu matching semantics as
    # ConfigParser._match_platform: keys support comma lists and "any"
    for os_key, cpu_config in (config or {}).items():
        os_list = [o.strip() for o in str(os_key).split(",")]
        if not (host_platform in os_list or os_list == ["any"]):
            continue
        for cpu_key in cpu_config:
            cpu_list = [c.strip() for c in str(cpu_key).split(",")]
            if host_cpu in cpu_list or cpu_list == ["any"]:
                return False
    return True


def _resolve_output(config_file, filename):
    # the master config lives at <source_root>/build/prebuilts_config.json;
    # write generated configs into <source_root>/prebuilts/ (this script's
    # install target dir, guaranteed writable)
    source_root = os.path.dirname(os.path.dirname(os.path.abspath(config_file)))
    path = os.path.join(source_root, "prebuilts")
    os.makedirs(path, exist_ok=True)
    return os.path.join(path, filename)


def _filter_tool_variants(tool, variants):
    config = tool.get("config")
    if not config:
        return tool
    filtered = {}
    unzip_dir = tool.get("unzip_dir", "")
    for os_key, cpu_dict in config.items():
        new_cpu = {}
        for cpu_key, entries in cpu_dict.items():
            if not isinstance(entries, list):
                entries = [entries]
            kept = []
            for entry in entries:
                path = "/".join(
                    p
                    for p in [
                        unzip_dir,
                        entry.get("unzip_dir", ""),
                        entry.get("unzip_filename", ""),
                    ]
                    if p
                )
                if any(v in path for v in variants):
                    kept.append(entry)
            if kept:
                new_cpu[cpu_key] = kept if len(kept) > 1 else kept[0]
        if new_cpu:
            filtered[os_key] = new_cpu
    if not filtered:
        return None
    tool["config"] = filtered
    return tool


def die(msg) -> NoReturn:
    print("Error: %s" % msg, file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
