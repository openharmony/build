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
            module_info_file = os.path.join(out_path, info.get("module_info_file"))
            target_info = IoUtil.read_json_file(module_info_file)
            label_name = target_info.get("label_name")
            target_source = os.path.join(out_path, target_info.get("source"))
            if target_name == label_name:
                cmd = [llvm_path, 
                        "--add-section", 
                        ".kernelpermission=" + kernel_permission_file,
                        target_source
                        ]
            cmds.append(cmd)
        return cmds


    @staticmethod
    def check_json_file(file_path):
        json_data = IoUtil.read_json_file(file_path)
        if KernelPermission.check_json_content(json_data):
            return True
        else:
            print("kernel_permission.json is invalid at file_path: {}".format(file_path))
            return False


    @staticmethod
    def check_json_content(json_data):
        if len(json_data) == 1 and "kernelpermission" in json_data:
            json_data = json_data["kernelpermission"]
            return KernelPermission.check_json_value(json_data)
        else:
            return False


    @staticmethod
    def check_json_value(json_data):
        for key, value in json_data.items():
            if not isinstance(value, (bool, str, list)):
                return False
            if isinstance(value, list):
                if not all(isinstance(item, str) for item in value):
                    return False
        return True


if __name__ == "__main__":
    pass
