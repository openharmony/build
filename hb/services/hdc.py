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
#

import shutil
import sys
import os
import time
import threading
import subprocess
from enum import Enum

from containers.status import throw_exception
from exceptions.ohos_exception import OHOSException
from services.interface.build_file_generator_interface import BuildFileGeneratorInterface
from containers.arg import Arg, ModuleType
from util.system_util import SystemUtil
from util.io_util import IoUtil
from util.log_util import LogUtil
from util.component_util import ComponentUtil


class CMDTYPE(Enum):
    PUSH = 1
    LIST_TARGETS = 2


class Hdc(BuildFileGeneratorInterface):

    def __init__(self):
        super().__init__()
        self._regist_hdc_path()
        self._regist_hpm_cache()

    def run(self):
        self.execute_hdc_cmd(CMDTYPE.PUSH)

    @throw_exception
    def execute_hdc_cmd(self, cmd_type: int, **kwargs):
        if cmd_type == CMDTYPE.PUSH:
            return self._execute_hdc_push_cmd()
        elif cmd_type == CMDTYPE.LIST_TARGETS:
            return self._execute_hdc_list_targets_cmd()
        else:
            raise OHOSException(
                'You are tring to use an unsupported hdc cmd type "{}"'.format(cmd_type), '3001')

    @throw_exception
    def _regist_hdc_path(self):
        hdc_path = shutil.which("hdc")
        if os.path.exists(hdc_path):
            self.exec = hdc_path
        else:
            raise OHOSException(
                'There is no hdc executable file at {}'.format(hdc_path), '0001')

    @throw_exception
    def _regist_hpm_cache(self):
        self.hpm_config_path = "~/.hpm"
        hpm_path = shutil.which("hpm")
        if os.path.exists(hpm_path):
            command = [hpm_path, "config", "get", "modelRepository"]
            output = subprocess.check_output(command)
            if output:
                self.hpm_config_path = output.decode('utf-8').rstrip("\n")

    # 通过部件名获取部件二进制路径
    def get_send_file(self, part_name):
        srcs = []
        target = ""
        bundle_file = os.path.join(self.hpm_config_path, '.hpmcache/binarys/subsystem', part_name, "bundle.json")
        if not os.path.exists(bundle_file):
            return srcs, target
        bundle_info = IoUtil.read_json_file(bundle_file)
        deployment = bundle_info.get("deployment")
        if deployment:
            src = deployment.get("src", "")
            target = deployment.get("target", "")
            if not src.startswith("/"):
                src = os.path.join(os.path.dirname(bundle_file), src)
            srcs = get_files_by_path(src)
        return srcs, target

    @throw_exception
    def _execute_hdc_push_cmd(self, **kwargs):
        connect_key = self.flags_dict.get("target")
        # mount
        hdc_mount_cmd = [self.exec, '-t', connect_key, 'shell', 'mount', '-o', 'rw,remount', '/']
        SystemUtil.exec_command(hdc_mount_cmd)
        # parse part_name
        part_name = self.flags_dict.get("part_name")
        send_files, target = self.get_send_file(part_name)
        send_src = self.flags_dict.get("src")
        if send_src:
            send_files = get_files_by_path(send_src)
        # send file
        for send_file in send_files:
            hdc_push_cmd = [self.exec, "-t", connect_key, "file", "send", send_file,
                            os.path.join(target, os.path.basename(send_file))]
            SystemUtil.exec_command(hdc_push_cmd)
            hdc_push_chown_cmd = [self.exec, "-t", connect_key, "shell", "chown", "root:root",
                                  os.path.join(target, os.path.basename(send_file))]
            SystemUtil.exec_command(hdc_push_chown_cmd)

        # reboot
        if self.flags_dict.get("reboot"):
            hdc_reboot_cmd = [self.exec, '-t', connect_key, 'shell', 'reboot']
            SystemUtil.exec_command(hdc_reboot_cmd)

    @throw_exception
    def _execute_hdc_list_targets_cmd(self, **kwargs):
        hdc_list_targets_cmd = [self.exec, "list", "targets"]
        SystemUtil.exec_command(hdc_list_targets_cmd)


def get_files_by_path(path):
    output = []
    if os.path.isdir(path):
        for root, dirnames, filenames in os.walk(path):
            for filename in filenames:
                output.append(os.path.join(root, filename))
    else:
        output.append(path)
    return output
