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

import os
import json


def _load_part_download_config():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(current_dir, "part_prebuilts_config.json")
    if not os.path.exists(config_file):
        raise FileNotFoundError("Config file does not exist: {}".format(config_file))
    with open(config_file, 'r') as file:
        config_data = json.load(file)
    return config_data


def _get_tools_by_category(config_data, categorys, exclude_tools):
    """
    Get all tools in the specified category from the config data.
    """
    configured_categorie_config = config_data.get("categories", {})
    tools = set()
    for category in categorys:
        if category not in configured_categorie_config:
            continue
        category_config = configured_categorie_config[category]
        for tool in category_config:
            if tool not in exclude_tools:
                tools.add(tool)
    return tools


def _get_tools_by_part(config_data, part):
    all_required = set()
    all_parts_config = config_data.get("parts", {})
    if part not in all_parts_config:
        return []
    part_config = all_parts_config[part]
    required_categories = part_config.get("required_categories", [])
    required_tools = part_config.get("required_tools", [])
    exclude_tools = part_config.get("exclude_tools", [])
    for item in required_tools:
        all_required.add(item)
    all_required.update(_get_tools_by_category(config_data, required_categories, exclude_tools))
    print("Part: {}, Required tools: {}".format(part, sorted(all_required)))
    return all_required

def get_parts_tool_config(part_names):
    if not part_names:
        return None
    config_data = _load_part_download_config()
    basic_tools = config_data["categories"].get("basic", [])
    all_required_tools = set(basic_tools)
    for part in part_names:
        all_required_tools.update(_get_tools_by_part(config_data, part))
    print("Required tools for parts {}: {}".format(part_names, sorted(all_required_tools)))
    return all_required_tools