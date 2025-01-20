#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) 2023 Huawei Device Co., Ltd.
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
import tarfile
import shutil
import argparse


def read_dependencies_file(hpm_cache_home):
    # 构造文件路径
    dependences_path = os.path.join(hpm_cache_home, "dependences.json")
    try:
        with open(dependences_path, 'r') as file:
            dependencies = json.load(file)
            return dependencies
    except FileNotFoundError:
        print(f"文件 {dependences_path} 未找到。")
        return None
    except json.JSONDecodeError:
        print(f"文件 {dependences_path} 不是有效的 JSON 格式。")
        return None
    except Exception as e:
        print(f"读取文件时发生错误: {e}")
        return None


def remove_directory(path):
    try:
        shutil.rmtree(path)
        print(f"文件夹 {path} 已成功删除。")
    except Exception as e:
        print(f"删除文件夹时出错: {e}")


def extract_tarfile(file_path, install_path):
    try:
        with tarfile.open(file_path, 'r:gz') as tar:
            tar.extractall(path=install_path)
        print(f"组件已成功安装到 {install_path}")
    except tarfile.ReadError:
        print(f"文件 {file_path} 不是有效的 tar.gz 格式。")
    except Exception as e:
        print(f"安装组件时发生错误: {e}")


def find_and_install_component(packages_dir, dependencies, hpm_cache_home):
    for component_name in dependencies.keys():
        print(component_name)
        # 构造文件名
        version = dependencies[component_name]['version'].replace("-snapshot", "")
        install_path = hpm_cache_home + dependencies[component_name]['installPath']
        file_name = f"@ohos-{component_name}-{version}.tgz"
        file_path = os.path.join(packages_dir, file_name)
        if not os.path.exists(file_path):
            print(f"文件 {file_path} 不存在。")
            continue
        # 检查 install_path 是否存在，如果存在直接删除
        if os.path.exists(install_path):
            remove_directory(install_path)
        try:
            # 解压文件
            extract_tarfile(file_path, install_path)
        except Exception as e:
            print(f"安装组件时发生错误: {e}")
        else:
            print(f"文件夹 {install_path} 不存在。")


def main():
    parser = argparse.ArgumentParser(description="安装指定组件到指定目录")
    parser.add_argument("--packages_dir", required=True, help="包目录路径")
    args = parser.parse_args()
    home_dir = os.path.expanduser("~")
    hpm_cache_home = os.path.join(home_dir, ".hpm", ".hpmcache")
    dependencies = read_dependencies_file(hpm_cache_home)
    if dependencies:
        find_and_install_component(args.packages_dir, dependencies, hpm_cache_home)


if __name__ == "__main__":
    main()
