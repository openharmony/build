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
from common_utils import get_code_dir, load_config


def get_parts_tag_config(part_names: list) -> set:
    if not part_names:
        return None
    config_data = _load_part_download_config()
    all_required_tags = set()
    for part in part_names:
        all_required_tags.update(_get_tags_by_part(config_data, part))
    all_required_tags.add("base")
    print(
        "Required tags for parts {}: {}".format(
            ",".join(part_names), sorted(all_required_tags)
        )
    )
    return all_required_tags


def _load_part_download_config() -> dict:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(current_dir, "part_prebuilts_config.json")
    if not os.path.exists(config_file):
        raise FileNotFoundError("Config file does not exist: {}".format(config_file))
    return load_config(config_file)


def _get_tags_by_part(config_data: dict, part: str) -> set:
    all_tags = _load_all_tags()
    if part not in config_data:
        return set()
    configured_tags = set(config_data[part])
    custom_tags = configured_tags - all_tags
    if custom_tags:
        raise Exception(
            f"Custom tags {custom_tags} are not defined in prebuilts_config.json"
        )
    return configured_tags


def _load_all_tags() -> set:
    code_dir = get_code_dir()
    prebuilts_config_json = os.path.join(code_dir, "build", "prebuilts_config.json")
    if not os.path.exists(prebuilts_config_json):
        raise FileNotFoundError(
            "Config file does not exist: {}".format(prebuilts_config_json)
        )
    tool_configs = load_config(prebuilts_config_json)["tool_list"]
    tags = {tool.get("tag") for tool in tool_configs}
    return tags
