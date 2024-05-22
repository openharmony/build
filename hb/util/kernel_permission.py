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
import json
from collections import OrderedDict

from exceptions.ohos_exception import OHOSException
from util.system_util import SystemUtil
from util.io_util import IoUtil
from util.log_util import LogUtil


class KernelPermission():


    @staticmethod
    def run(out_path, root_path):
        log_path = os.path.join(out_path, 'build.log')
        KernelPermission.execute_kernel_permission_cmd(log_path, out_path, root_path)


    @staticmethod
    def scan_file(out_path):
        """scan path uild_configs/kernel_permission/
        return file_list include kernel_permission.json
        """
        file_list = []
        file_path = file_path = os.path.join(out_path, "build_configs/kernel_permission/")
        for root, subdirs, files in os.walk(file_path):
            for _filename in files:
                content = IoUtil.read_json_file(os.path.join(root, _filename))
                file_list.append(content[0])
        return file_list


    @staticmethod
    def execute_kernel_permission_cmd(log_path, out_path, root_path):
        """execute cmd
        llvm-object --add-section .kernelpermission=json_file xx/xx.so
        """
        LogUtil.write_log(
            log_path,
            "begin run kernel permission cmd log_path:{}".format(log_path),
            'info')
        
        try:
            llvm_tool = KernelPermission.regist_llvm_objcopy_path(root_path)
        except OHOSException as e:
            LogUtil.write_log(
                log_path,
                "regist_llvm_objcopy_path failed:{}".format(e),
                'warning')
            return
        
        file_list = KernelPermission.scan_file(out_path)
        
        cmds = KernelPermission.gen_cmds(file_list, out_path, llvm_tool)
        if cmds:
            for cmd in cmds:
                LogUtil.write_log(
                    log_path,
                    cmd,
                    'info')
                SystemUtil.exec_command(
                    cmd,
                    log_path
                    )
        else:
            LogUtil.write_log(
                log_path,
                "There is no kernel permission json file,no need to run llvm-object cmd.",
                'info')


    @staticmethod
    def regist_llvm_objcopy_path(root_path):
        """find llvm_objcopy_path executable
        :raise OHOSException: when can't find the llvm_objcopy_path excutable
        """
        llvm_objcopy_path = os.path.join(root_path, "prebuilts/clang/ohos/linux-x86_64/llvm/bin/llvm-objcopy")
        if os.path.exists(llvm_objcopy_path):
            return llvm_objcopy_path
        else:
            raise OHOSException(
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
                raise OHOSException(
                    'kernel_permission json file {} invalid!'.format(kernel_permission_file), '0001')
            target_name = info.get("target_name")
            output_extension = info.get("gn_output_extension")
            output_name = info.get("gn_output_name")
            part_name = info.get("part_name")
            subsystem_name = info.get("subsystem_name")
            type = info.get("type")
            module_name = target_name
            if output_name == "" and output_extension == "":
                if type == "lib" and target_name.startswith("lib"):
                    module_name = "{}.z.so".format(target_name)
                elif type == "lib" and not target_name.startswith("lib"):
                    module_name = "lib{}.z.so".format(target_name)
            print("module_name:{}".format(module_name))
            module_path = os.path.join(subsystem_name, part_name)
            module_path = os.path.join(module_path, module_name)
            print("module_path:{}".format(module_path))
            target_source = os.path.join(out_path, module_path)
            if target_name:
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
                    print(json_data)
                    file.seek(0)
                    file.truncate()
                    json.dump(json_data, file, indent=4)
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
        cnt = 0
        encaps_data = json_data["encaps"]
        new_data = OrderedDict()
        new_data["ohos.encaps.count"] = cnt
        new_data.update(encaps_data)
        for key, value in new_data.items():
            if not isinstance(value, (bool, int)):
                return False
            cnt += 1
        new_data["ohos.encaps.count"] = cnt -1
        json_data["encaps"] = new_data
        return True


if __name__ == "__main__":
    pass
