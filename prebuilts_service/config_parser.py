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
import copy
import re
import os
from common_utils import load_config
from part_prebuilts_config import get_parts_tag_config


class ConfigParser:
    def __init__(self, config_file: str, global_args):
        self.data = load_config(config_file)
        self.current_cpu = global_args.host_cpu
        self.current_os = global_args.host_platform
        self.input_tag = "all"
        self.input_type = global_args.type
        self.global_config = {
            "code_dir": global_args.code_dir,
            "download_root": self.data["download_root"]
        }
        self._parse_global_config()

    def get_operate(self, part_names=None) -> tuple:
        download_op = []
        other_op = []
        tool_list = self.data["tool_list"]
        # 独立编译按需下载
        parts_configured_tags = get_parts_tag_config(part_names) if part_names else None
        if parts_configured_tags:
            self.input_tag = parts_configured_tags
        # 获取下载操作和其他操作
        for tool in tool_list:
            tool_basic_config = self._parse_tool_basic_config(tool)
            tool_basic_config = self._merge_configs(self.global_config, tool_basic_config)
            if not self._apply_filters([tool_basic_config]):
                continue
            _download, _other = self._get_tool_operate(tool_basic_config, tool.get("config"), tool.get("handle", []))
            download_op.extend(_download)
            other_op.extend(_other) 
        return download_op, other_op
    
    def _parse_global_config(self):
        # 解析全局配置中的变量
        VarParser.parse_vars(self.global_config, self.global_config)
        download_root = self.global_config["download_root"]
        self.global_config["download_root"] = os.path.abspath(os.path.expanduser(download_root))

    def _get_tool_operate(self, tool_basic_config: dict, platform_config: dict, handle_config: list) -> tuple:
        matched_platform_configs = self._match_platform(self.current_os, self.current_cpu, platform_config)
        self._parse_platform_config(matched_platform_configs, tool_basic_config)
        platform_configs = []
        for conf in matched_platform_configs:
            config = self._merge_configs(tool_basic_config, conf)
            platform_configs.append(config)
        platform_configs = self._apply_filters(platform_configs)
        handle = handle_config
        download_operate, other_operate = self._generate_tool_operate(tool_basic_config, platform_configs, handle)
        # 删除存在未知变量的配置
        return VarParser.remove_undefined(download_operate), VarParser.remove_undefined(other_operate)

    def _parse_tool_basic_config(self, tool):
        tool_basic_config = {key: tool[key] for key in tool if key not in {"config", "handle"}}
        VarParser.parse_vars(tool_basic_config, tool_basic_config)
        VarParser.parse_vars(tool_basic_config, self.global_config)
        return tool_basic_config
    
    def _parse_platform_config(self, matched_platform_configs: list, tool_basic_config: dict):
        for config in matched_platform_configs:
            VarParser.parse_vars(config, config)
            VarParser.parse_vars(config, tool_basic_config)

    def _apply_filters(self, configs: list):
        return Filter(configs).apply_filters(self.input_tag, self.input_type)
    
    def _match_platform(self, input_os: str, input_cpu: str, config: dict) -> list:
        """获取匹配当前操作系统的配置"""
        if not config:
            return []
        filtered = []

        matched_os = self._match_os(input_os, config)
        for os_item in matched_os:
            cpu_config = config[os_item]
            matched_cpu = self._match_cpu(input_cpu, cpu_config)
            for cpu_item in matched_cpu:
                platform_configs = cpu_config[cpu_item]
                # 配置内部可以是一个配置，也可以是一个配置列表
                if not isinstance(platform_configs, list):
                    platform_configs = [platform_configs]
                filtered.extend(platform_configs)
        return filtered

    def _match_os(self, input_os: str, os_config: dict) -> list:
        matched_os = []
        for os_key in os_config:
            # 逗号分割操作系统名
            configured_os_list = [o.strip() for o in os_key.split(",")]
            if input_os in configured_os_list or configured_os_list == ["all_os"]:
                matched_os.append(os_key)
        return matched_os
    
    def _match_cpu(self, input_cpu: str, cpu_config: dict) -> list:
        matched_cpu = []
        for cpu_str in cpu_config:
            configured_cpu_list = [c.strip() for c in cpu_str.split(",")]
            if input_cpu in configured_cpu_list or configured_cpu_list == ["all_cpu"]:
                matched_cpu.append(cpu_str)
        return matched_cpu

    def _generate_tool_operate(self, tool_basic_config: dict, platform_configs: list, handles: list) -> tuple:
        download_operate = []
        other_operate = []

        # 根据平台配置生成下载操作
        for config in platform_configs:
            if config.get("remote_url") and config.get("unzip_dir") and config.get("unzip_filename"):
                download_config = self._generate_download_config(config)
                download_operate.append(download_config)

        # 如果没有其他操作，则返回
        if not handles:
            return download_operate, []

        configs = platform_configs if platform_configs else [tool_basic_config]
        operates = self._generate_handles(configs, handles)
        # handle中不允许配置下载操作
        other_operate = []
        for operate in operates:
            if operate["type"] == "download":
                pass
            else:
                other_operate.append(operate)

        return download_operate, other_operate

    def _generate_handles(self, outer_configs: list, handles: list):
        """
        为每个配置生成对应的操作列表
        :param configs: 配置列表
        :param handles: 操作列表
        """
        operate_list = []
        for config in outer_configs:
            special_handle = config.get("handle_index")
            count = 0
            for index, handle in enumerate(handles):
                if special_handle and index not in special_handle:
                    continue
                step_id = "_".join([config.get("name"), os.path.basename(config.get("remote_url", "")), str(count)])
                count += 1
                # 不能改变原来的handle
                new_handle = copy.deepcopy(handle)
                # 解析handle中的变量
                VarParser.parse_vars(new_handle, new_handle)
                VarParser.parse_vars(new_handle, config)
                # 生成操作id
                new_handle["tool_name"] = config.get("name")
                new_handle["step_id"] = step_id
                operate_list.append(new_handle)
        return operate_list

    def _generate_download_config(self, config):
        try:
            return {
                "remote_url": config["remote_url"],
                "unzip_dir": config["unzip_dir"],
                "unzip_filename": config["unzip_filename"],
                "download_dir": config.get("download_dir", config["download_root"]),
                "operate_type": "download",
                "name": config.get("name"),
            }
        except KeyError as e:
            print(f"error config: {config}")
            raise e

    def _merge_configs(self, *additional_configs) -> dict:
        unified_config = dict()
        for config in additional_configs:
            unified_config.update(config)
        return unified_config


class Filter:
    def __init__(self, configs=[]):
        self.input_configs = copy.deepcopy(configs)

    def apply_filters(self, input_tag: str, input_type: str):
        return self.filter_tag(input_tag).filter_type(input_type).result()

    def filter_tag(self, input_tag: str) -> 'Filter':
        """过滤tag字段"""
        filtered = []
        for config in self.input_configs:
            tool_tag = config["tag"]
            if input_tag == "all" or tool_tag in input_tag:
                filtered.append(config)    
        self.input_configs = filtered
        return self

    def filter_type(self, input_type: str) -> 'Filter':
        """过滤type字段"""
        filtered = []
        for config in self.input_configs:
            _type = config.get("type")
            if not _type:
                filtered.append(config)
                continue
            # 配置的type，转set
            if isinstance(_type, str):
                configured_types = set([t.strip() for t in _type.split(",")])
            else:
                configured_types = set(_type)
            # 输入的type，转set
            input_types = set([t.strip() for t in input_type.split(",")])

            # 检查二者是否有交集，有则添加
            if not input_types.isdisjoint(configured_types):
                filtered.append(config)
        self.input_configs = filtered
        return self

    def result(self):
        return self.input_configs


class VarParser:
    var_pattern: re.Pattern = re.compile(r'\$\{.*?\}')  # 正则表达式

    @classmethod
    def remove_undefined(cls, configs: list) -> list:
        useful_config = []
        for config in configs:
            if not cls.has_undefined_var(config):
                useful_config.append(config)
        return useful_config

    @classmethod
    def has_undefined_var(cls, data):
        try:
            if isinstance(data, str):
                return bool(cls.var_pattern.findall(data))
            elif isinstance(data, list):
                return any(cls.has_undefined_var(item) for item in data)
            elif isinstance(data, dict):
                return any(cls.has_undefined_var(value) for value in data.values())
            else:
                return False
        except AttributeError:
            print("var_pattern不是有效的正则表达式对象")
            return False

    @classmethod
    def parse_vars(cls, data: any, dictionary: dict) -> any:
        """
        用dictionary字典中的值替换data中的变量,data可以为列表、字典、字符串等类型, 变量使用${var_name}形式
        若data是字符串, 则返回新值, 否则, 更改原值
        return: 更改之后的值
        """
        if isinstance(data, str):
            return cls.replace_vars_in_string(data, dictionary)
        elif isinstance(data, dict):
            for k in list(data.keys()):
                original_value = data[k]
                new_value = cls.parse_vars(original_value, dictionary)
                if new_value is not original_value:  # 仅当original_value为字符串时成立
                    data[k] = new_value
        elif isinstance(data, list):
            for i in range(len(data)):
                original_value = data[i]
                new_value = cls.parse_vars(original_value, dictionary)
                if new_value is not original_value:
                    data[i] = new_value
        else:
            return data
        return data

    @classmethod
    def replace_vars_in_string(cls, s: str, dictionary: dict) -> str:

        """用dictionary字典中的值替换字符串s中的变量, 变量使用${var_name}形式"""
        ref_dict = dict()
        while True:
            try:
                replaced = cls.var_pattern.sub(
                    lambda matched_var: cls._replace_var_with_dict_value(matched_var, dictionary, ref_dict),
                    s)
                if replaced == s:
                    break
                s = replaced
            except ValueError as e:
                print(f"replace var in string {s} failed")
                raise e
        return s

    @classmethod
    def _replace_var_with_dict_value(cls, matched_var, dictionary, ref_dict):
        var_name = matched_var.group()[2:-1]
        if dictionary.get(var_name):
            cls._update_ref_dict(ref_dict, var_name, dictionary.get(var_name))
            return dictionary.get(var_name) # 找得到就替换
        else:
            return matched_var.group() # 找不到就保留原始值
    
    @classmethod
    def _update_ref_dict(cls, ref_dict, var_name, var_value):
        if var_name not in ref_dict:
            ref_dict[var_name] = []
        ref_vars = cls.var_pattern.findall(var_value)
        for var in ref_vars:
            name = var[2:-1]
            ref_dict[var_name].append(name)
        # 检测循环依赖
        cls._check_cycle_rely(ref_dict, var_name)

    @classmethod
    def _check_cycle_rely(cls, ref_dict, var_name):
        ref_list = ref_dict.get(var_name, [])
        for ref_var in ref_list:
            if var_name in ref_dict.get(ref_var, []):
                raise ValueError(f"Cycle dependency exists between {var_name} and {ref_var}")