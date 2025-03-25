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
from threading import Lock
from pathlib import Path

_indep_args_cache = None
_cache_lock = Lock()


def get_json(file_path):
    data = {}
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"can not find file: {file_path}.")
    except Exception as e:
        print(f"{file_path}: \n {e}")
    return data


def get_indep_args():
    """
    Read the JSON file of independent build parameters and return the parsed data.
    :return: A dictionary containing independent build parameters (on success) or None (on failure)
    """
    global _indep_args_cache
    if _indep_args_cache:
        return _indep_args_cache

    src_root = Path(__file__).parent.parent.parent.parent
    file_path = os.path.join(src_root, "out/hb_args/indepbuildargs.json")

    with _cache_lock:
        if _indep_args_cache is not None:
            return _indep_args_cache
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            _indep_args_cache = data
            return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        print(f"Invalid JSON format in {file_path}: {e}")
    except PermissionError as e:
        print(f"Permission denied for {file_path}: {e}")
    except Exception as e:
        print(f"Unexpected error reading {file_path}: {e}")
    return None


def is_export_compile_commands():
    data = get_indep_args()
    return data["export_compile_commands"]["argDefault"]


def get_ninja_args():
    """
    Obtain the parameters for the Ninja build system from the independent build parameters.
    :return: A list of Ninja parameters
    """
    input_ninja_args = []
    data = get_indep_args()
    input_ninja_args.extend(data["ninja_args"]["argDefault"])
    if data["keep_ninja_going"]["argDefault"]:
        input_ninja_args.append("-k10000")
    return input_ninja_args


def get_gn_args():
    """
    Obtain the parameters for the GN build system from the independent build parameters.
    :return: A list of GN parameters
    """
    input_gn_args = []
    data = get_indep_args()
    if data["gn_args"]["argDefault"]:
        input_gn_args.extend(data["gn_args"]["argDefault"])

    return input_gn_args


def get_build_target():
    """
    Obtain the build targets from the independent build parameters.
    :return: A list of build targets
    """
    input_build_target = []
    data = get_indep_args()
    if data["build_target"]["argDefault"]:
        input_build_target.extend(data["build_target"]["argDefault"])
    return input_build_target


def is_enable_ccache():
    """
    Check if ccache is enabled.
    :return: Returns True if ccache is enabled; otherwise, returns False.
    """
    return get_indep_args()["ccache"]["argDefault"]


def print_ccache_stats():
    """
    Print the ccache statistics information.
    If ccache is enabled, execute the 'ccache -s' command and print the output.
    If the ccache command is not found or execution fails, print the corresponding error message.
    """
    if is_enable_ccache():
        try:
            output = subprocess.check_output(["ccache", "-s"], text=True)
            print("ccache hit statistics:")
            print(output)
        except FileNotFoundError:
            print("Error: ccache command not found")
        except subprocess.CalledProcessError as e:
            print(f"Failed to execute ccache command: {e}")


def clean_ccache_info():
    """
    Clean the ccache statistics information.
    If ccache is enabled, execute the 'ccache -z' command to reset the ccache statistics.
    If the ccache command is not found or execution fails, print the corresponding error message.
    """
    if is_enable_ccache():
        try:
            subprocess.check_output(["ccache", "-z"], text=True)
        except FileNotFoundError:
            print("Error: ccache command not found")
        except subprocess.CalledProcessError as e:
            print(f"Failed to execute ccache command: {e}")
