#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2024 Huawei Device Co., Ltd.
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

import json
import os
import subprocess


def get_json(file_path):
    data = {}
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"can not find file: {file_path}.")
    except Exception as e:
        print(f"{file_path}: \n {e}")
    return data


def get_indep_args():
    """
    读取独立构建参数的JSON文件，并返回解析后的数据。
    :return: 包含独立构建参数的字典（成功时）或 None（失败时）
    """
    src_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    file_path = os.path.join(src_root, "out/hb_args/indepbuildargs.json")
    try:
        # 以只读模式打开文件，并使用json模块加载内容
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        # 如果文件不存在
        print(f"file not found：{file_path}")
        return None
    except Exception as e:
        print(f"something wrong with file：{e}")
        return None


def get_ninja_args():
    """
    从独立构建参数中获取Ninja构建系统的参数。
    :return: Ninja参数列表
    """
    input_ninja_args = []
    data = get_indep_args()
    # 如果配置中设置了保持Ninja运行，则添加相应的参数
    if data["keep_ninja_going"]["argDefault"]:
        input_ninja_args.append("-k10000")
    return input_ninja_args


def get_gn_args():
    """
    从独立构建参数中获取GN构建系统的参数。
    :return: GN参数列表
    """
    input_gn_args = []
    data = get_indep_args()
    # 如果配置中设置了GN参数，则扩展到参数列表中
    if data["gn_args"]["argDefault"]:
        input_gn_args.extend(data["gn_args"]["argDefault"])

    return input_gn_args


def get_build_target():
    """
    从独立构建参数中获取编译目标。
    :return: 编译目标
    """
    input_build_target = []
    data = get_indep_args()
    if data["build_target"]["argDefault"]:
        input_build_target.extend(data["build_target"]["argDefault"])
    return input_build_target


def is_enable_ccache():
    """
    检查是否启用了ccache。
    :return: 如果启用了ccache，则返回True；否则返回False。
    """
    # Read the independent build parameters JSON file and get the value of the "ccache" key's "argDefault"
    return get_indep_args()["ccache"]["argDefault"]



def print_ccache_stats():
    """
    打印ccache的统计信息。
    如果ccache已启用，则执行ccache -s命令并打印输出。
    如果ccache命令未找到或执行失败，则打印相应的错误消息。
    """
    # Check if ccache is enabled
    if is_enable_ccache():
        try:
            # Execute the 'ccache -s' command and capture the output
            output = subprocess.check_output(["ccache", "-s"], text=True)
            # Print the header for ccache hit statistics
            print("ccache hit statistics:")
            # Print the output of the 'ccache -s' command
            print(output)
        except FileNotFoundError:
            # Print an error message if the 'ccache' command is not found
            print("Error: ccache command not found")
        except subprocess.CalledProcessError as e:
            # Print an error message if the 'ccache -s' command fails
            print(f"Failed to execute ccache command: {e}")


def clean_ccache_info():
    """
    清除ccache的统计信息。
    如果ccache已启用，则执行ccache -z命令以重置ccache的统计信息。
    如果ccache命令未找到或执行失败，则打印相应的错误消息。
    """
    # Check if ccache is enabled
    if is_enable_ccache():
        try:
            # Execute the 'ccache -z' command to reset the ccache statistics
            subprocess.check_output(["ccache", "-z"], text=True)
        except FileNotFoundError:
            # Print an error message if the 'ccache' command is not found
            print("Error: ccache command not found")
        except subprocess.CalledProcessError as e:
            # Print an error message if the 'ccache -z' command fails
            print(f"Failed to execute ccache command: {e}")
