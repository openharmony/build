#!/usr/bin/env python
# coding=utf-8

#
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
#

import os
import sys
import subprocess
import json
from collections import OrderedDict

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from scripts.util.file_utils import read_json_file


class KernelPermission():


    @staticmethod
    def run(out_path, root_path):
        target_out_path = os.path.join(root_path, out_path.lstrip("//"))
        print("target_out_path:", target_out_path)
        KernelPermission.execute_kernel_permission_cmd(target_out_path, root_path)


    @staticmethod
    def scan_file(out_path):
        """scan path uild_configs/kernel_permission/
        return file_list include kernel_permission.json
        """
        file_list = []
        file_path = file_path = os.path.join(out_path, "build_configs/kernel_permission/")
        for root, subdirs, files in os.walk(file_path):
            for _filename in files:
                content = read_json_file(os.path.join(root, _filename))
                file_list.append(content[0])
        return file_list


    @staticmethod
    def execute_kernel_permission_cmd(out_path, root_path):
        """execute cmd
        llvm-object --add-section .kernelpermission=json_file xx/xx.so
        """
        print("begin run kernel permission cmd")
        
        try:
            llvm_tool = KernelPermission.regist_llvm_objcopy_path(root_path)
        except FileNotFoundError as e:
            print("regist_llvm_objcopy_path failed:{}".format(e))        
        file_list = KernelPermission.scan_file(out_path)
        
        cmds = KernelPermission.gen_cmds(file_list, out_path, llvm_tool)
        if cmds:
            for cmd in cmds:
                print("llvm cmd: {}".format(cmd))
                KernelPermission.exec_command(cmd)
        else:
            print("There is no kernel permission json file,no need to run llvm-object cmd.")


    @staticmethod
    def regist_llvm_objcopy_path(root_path):
        """find llvm_objcopy_path executable
        :raise FileNotFoundError: when can't find the llvm_objcopy_path excutable
        """
        llvm_objcopy_path = os.path.join(root_path, "prebuilts/clang/ohos/linux-x86_64/llvm/bin/llvm-objcopy")
        if os.path.exists(llvm_objcopy_path):
            return llvm_objcopy_path
        else:
            raise FileNotFoundError(
                'There is no llvm-object executable file at {}'.format(llvm_objcopy_path), '0001')


    @staticmethod
    def gen_cmds(file_list, out_path, llvm_path):
        """generate cmd
        llvm-object --add-section .kernelpermission=json_file xx/xx.so
        """
        cmds = []
        cmd = []
        for info in file_list: 
            kernel_permission_file = os.path.join(out_path, info.get("kernel_permission_path"))
            if not KernelPermission.check_json_file(kernel_permission_file):
                raise FileExistsError(
                    'kernel_permission json file {} invalid!'.format(kernel_permission_file), '0001')
            target_name = info.get("target_name")
            output_extension = info.get("gn_output_extension")
            output_name = info.get("gn_output_name")
            part_name = info.get("part_name")
            subsystem_name = info.get("subsystem_name")
            target_type = info.get("type")
            module_name = target_name
            if output_name == "" and output_extension == "":
                if target_type == "lib" and target_name.startswith("lib"):
                    module_name = "{}.z.so".format(target_name)
                elif target_type == "lib" and not target_name.startswith("lib"):
                    module_name = "lib{}.z.so".format(target_name)
            print("module_name:{}".format(module_name))
            module_path = os.path.join(subsystem_name, part_name)
            module_path = os.path.join(module_path, module_name)
            print("module_path:{}".format(module_path))
            target_source = os.path.join(out_path, module_path)
            if os.path.exists(target_source):
                cmd = [llvm_path, 
                        "--add-section", 
                        ".kernelpermission=" + kernel_permission_file,
                        target_source
                        ]
                cmds.append(cmd)
        return cmds


    @staticmethod
    def check_json_file(file_path):
        try:
            with os.fdopen(os.open(file_path, os.O_RDWR, 0o640), 'r+') as file:
                json_data = json.load(file)
                if KernelPermission.check_json_content(json_data):
                    return True
                else:
                    print("encaps.json is invalid")
                    return False
        except FileNotFoundError:
            print("encaps.json is not found")
            return False
        except json.JSONDecodeError:
            print("encaps.json doesn't conform to json format")
            return False
        except Exception:
            print("encaps.json error")
            return False


    @staticmethod
    def check_json_content(json_data):
        if len(json_data) == 1 and "encaps" in json_data:
            return KernelPermission.check_json_value(json_data)
        else:
            return False


    @staticmethod
    def check_json_value(json_data):
        encaps_data = json_data["encaps"]
        for key, value in new_data.items():
            if not isinstance(value, (bool, int)):
                return False
        return True


    @staticmethod
    def exec_command(cmd: list, exec_env=None, **kwargs):
        process = subprocess.Popen(cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   encoding='utf-8',
                                   errors='ignore',
                                   env=exec_env,
                                   **kwargs)
        for line in iter(process.stdout.readline, ''):
            print(line)

        process.wait()
        ret_code = process.returncode

        if ret_code != 0:
            raise Exception(
                'please check llvm cmd: {}'.format(cmd))

if __name__ == "__main__":
    pass