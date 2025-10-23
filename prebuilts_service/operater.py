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
import shutil
import subprocess
from common_utils import (
    symlink_src2dest,
    copy_folder,
    remove_dest_path,
    run_cmd_directly,
    install_hpm,
    install_hpm_in_other_platform,
    npm_install,
    is_system_component,
    get_code_dir,
    check_hpm_version,
    save_data,
    load_config,
)
import re
import platform
from collections import OrderedDict


class OperateHanlder:
    global_args = None

    @staticmethod
    def process_step(process_item: str, step_list: list, unchanged_list: list, processed_dict: dict):
        process_result_file = os.path.join(OperateHanlder.global_args.code_dir, "prebuilts/.local_data/processed.json")
        for step in step_list:
            try:
                getattr(OperateHanlder, "_" + step.get("type"))(step)
            except Exception as e:
                # if the process item is already being processed, but not being recorded(that means prebuilts/processed.json is not exist),
                # in this situation, we just check if the process item is in unchanged_list,
                # if it is, then we don't need to process it again, we can just mark it as processed.
                if process_item in unchanged_list:
                    processed_dict[process_item] = True
                    break
                # If an error occurs, save the processed status
                processed_dict[process_item] = False
                save_data(process_result_file, processed_dict)
                raise e

    @staticmethod
    def run(operate_list: list, global_args, unchanged_list: tuple = ()):
        OperateHanlder.global_args = global_args
        # read and reset processed record
        process_result_file = os.path.join(global_args.code_dir, "prebuilts/.local_data/processed.json")
        if os.path.exists(process_result_file):
            processed_dict = load_config(process_result_file)
        else:
            processed_dict = dict()
        for key in processed_dict.keys():
            if key not in unchanged_list:
                processed_dict[key] = False

        # group operate_list by process item
        item_steps_dict = OrderedDict()
        for current_operate in operate_list:
            current_process_item = re.match(r"(.*)_\d$", current_operate.get("step_id")).group(1)
            if current_process_item not in item_steps_dict:
                item_steps_dict[current_process_item] = [current_operate]
            else:
                item_steps_dict[current_process_item].append(current_operate)

        # process each item
        for process_item, step_list in item_steps_dict.items():
            process_item_without_suffix = re.sub(r"(\.[A-Za-z]+)+$", "", process_item).strip("_")
            # If the process item is in unchanged_list and has been processed, skip it
            if process_item in unchanged_list:
                if process_item in processed_dict and processed_dict[process_item]:
                    print(f"==> {process_item_without_suffix} is unchanged, skip")
                    continue
            print(f"\n==> process {process_item_without_suffix}")
            processed_dict[process_item] = False
            OperateHanlder.process_step(process_item, step_list, unchanged_list, processed_dict)
            processed_dict[process_item] = True
        # save the processed status of each item
        save_data(process_result_file, processed_dict)

    @staticmethod
    def _symlink(operate: dict):
        src = operate.get("src")
        dest = operate.get("dest")
        symlink_src2dest(src, dest)

    @staticmethod
    def _copy(operate: dict):
        src = operate.get("src")
        dest = operate.get("dest")
        try:
            shutil.copy2(src, dest)
        except IsADirectoryError:
            copy_folder(src, dest)
        print(f"copy {src} ---> dest: {dest}")

    @staticmethod
    def _remove(operate: dict):
        path = operate.get("path")
        if isinstance(path, list):
            for p in path:
                remove_dest_path(p)
        else:
            remove_dest_path(path)
        print(f"remove {path}")

    @staticmethod
    def _move(operate: dict):
        src = operate.get("src")
        dest = operate.get("dest")

        filetype = operate.get("filetype", None)
        if filetype:
            file_list = os.listdir(src)
            for file in file_list:
                if file.endswith(filetype):
                    file_path = os.path.join(src, file)
                    shutil.move(file_path, dest)
                    print(f"move {file_path} ---> dest: {dest}")
        else:
            shutil.move(src, dest)
            print(f"move {src} ---> dest: {dest}")

    @staticmethod
    def _shell(operate: dict):
        cmd = operate.get("cmd")
        run_cmd_directly(cmd)

    @staticmethod
    def _hpm_download(operate: dict):
        hpm_path = os.path.join(OperateHanlder.global_args.code_dir, "prebuilts/hpm/node_modules/.bin/hpm")
        npm_tool_path = os.path.join(OperateHanlder.global_args.code_dir,
                                     "prebuilts/build-tools/common/nodejs/current/bin/npm")
        if check_hpm_version(hpm_path, npm_tool_path):
            print("hpm version is ok, skip hpm download")
            return
        name = operate.get("name")
        download_dir = operate.get("download_dir")
        symlink_dest = operate.get("symlink")
        if "@ohos/hpm-cli" == name:
            install_hpm(npm_tool_path, download_dir)
            symlink_src2dest(os.path.join(download_dir, "node_modules"), symlink_dest)
            return
        else:
            install_hpm_in_other_platform(name, operate)

    @staticmethod
    def _npm_install(operate: dict, max_retry_times=2):
        if OperateHanlder.global_args.build_type != "indep":
            # 若不是系统组件，直接返回
            if not is_system_component():
                return
        OperateHanlder.global_args.success_installed = []
        OperateHanlder.global_args.parallel_install = True
        for retry_times in range(max_retry_times + 1):
            try:
                result, error = npm_install(operate, OperateHanlder.global_args)
                if result:
                    return
                print("npm install error, error info: %s", error)
            except Exception as e:
                print("An unexpected error occurred during npm install: %s", str(e))
                error = str(e)
            OperateHanlder.global_args.parallel_install = False

        # 重试次数超过最大限制，处理错误日志
        for error_info in error.split("\n"):
            if error_info.endswith("debug.log"):
                log_path = error_info.split()[-1]
                try:
                    # 读取日志文件内容
                    result = subprocess.run(
                        ["cat", log_path],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    print("npm debug log content:\n%s", result.stdout)
                except subprocess.TimeoutExpired:
                    print("Reading npm debug log timed out after 60 seconds.")
                except Exception as e:
                    print("Error reading npm debug log: %s", str(e))
                break

        # 抛出最终异常
        raise Exception("npm install error with three times, prebuilts download exit")

    @staticmethod
    def _node_modules_copy(operate: dict):
        if OperateHanlder.global_args.build_type != "indep":
            if not is_system_component():
                return

        copy_list = operate.get("copy_list")
        for copy_config in copy_list:
            src_dir = copy_config.get("src")
            if not os.path.exists(src_dir):
                print(f"{src_dir} not exist, skip node_modules copy.")
                continue
            dest_dir = copy_config.get("dest")
            use_symlink = copy_config.get("use_symlink")
            if os.path.exists(os.path.dirname(dest_dir)):
                print("remove", os.path.dirname(dest_dir))
                shutil.rmtree(os.path.dirname(dest_dir))
            if use_symlink == "True" and OperateHanlder.global_args.enable_symlink == True:
                os.makedirs(os.path.dirname(dest_dir), exist_ok=True)
                os.symlink(src_dir, dest_dir)
                print(f"symlink {src_dir} ---> dest: {dest_dir}")
            else:
                shutil.copytree(src_dir, dest_dir, symlinks=True)
                print(f"copy {src_dir} ---> dest: {dest_dir}")

    @staticmethod
    def _download_sdk(operate: dict):
        # 获取操作系统信息
        system = platform.system()
        if system == "Linux":
            host_platform = "linux"
        elif system == "Darwin":
            host_platform = "darwin"
        else:
            print(f"Unsupported host platform: {system}")
            exit(1)

        # 获取 CPU 架构信息
        machine = platform.machine()
        if machine == "arm64":
            host_cpu_prefix = "arm64"
        elif machine == "aarch64":
            host_cpu_prefix = "aarch64"
        else:
            host_cpu_prefix = "x86"

        # 假设 code_dir 是当前目录，可根据实际情况修改
        code_dir = get_code_dir()
        prebuilts_python_dir = os.path.join(code_dir, "prebuilts", "python", f"{host_platform}-{host_cpu_prefix}")
        python_dirs = [os.path.join(prebuilts_python_dir, d) for d in os.listdir(prebuilts_python_dir) if
                       os.path.isdir(os.path.join(prebuilts_python_dir, d))]
        python_dirs.sort(reverse=True)
        if python_dirs:
            python_path = os.path.join(python_dirs[0], "bin")
        else:
            raise Exception("python path not exist")
        ohos_sdk_linux_dir = os.path.join(code_dir, "prebuilts", "ohos-sdk", "linux")
        if not os.path.isdir(ohos_sdk_linux_dir):
            python_executable = os.path.join(python_path, "python3")
            script_path = os.path.join(code_dir, "build", "scripts", "download_sdk.py")
            try:
                subprocess.run(
                    [python_executable, script_path, "--branch", "master", "--product-name", operate.get("sdk_name"),
                     "--api-version", str(operate.get("version"))], check=True)

            except subprocess.CalledProcessError as e:
                print(f"Error running download_sdk.py: {e}")