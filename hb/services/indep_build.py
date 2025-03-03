#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
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
#

from services.interface.build_file_generator_interface import BuildFileGeneratorInterface
from util.system_util import SystemUtil
from exceptions.ohos_exception import OHOSException
import os


class IndepBuild(BuildFileGeneratorInterface):

    def __init__(self):
        super().__init__()

    def run(self):
        flags_list = self._convert_flags()
        cmd = ["/bin/bash", "build/indep_configs/build_indep.sh"]
        cmd.extend(flags_list)
        variant = self.flags_dict["variant"]
        logpath = os.path.join('out', variant, 'build.log')
        ret_code = SystemUtil.exec_command(cmd, log_path=logpath, pre_msg="run indep build",
                                            after_msg="indeo build end")
        if ret_code != 0:
            raise OHOSException(f'ERROR: build_indep.sh encountered a problem, please check, cmd: {cmd}', '0001')

    def _convert_flags(self) -> list:
        flags_list = []
        flags_list.append(os.path.join(os.path.expanduser("~"), ".hpm/.hpmcache"))
        flags_list.append(self.flags_dict["path"])
        build_type = self.flags_dict["buildType"]
        if build_type == "both":
            flags_list.append("1")
        elif build_type == "onlytest":
            flags_list.append("2")
        else:
            flags_list.append("0")
        variant = self.flags_dict["variant"]
        flags_list.append(variant)
        self.flags_dict.pop("buildType")
        self.flags_dict.pop("path")

        for key in self.flags_dict.keys():
            if isinstance(self.flags_dict[key], bool) and self.flags_dict[key]:
                flags_list.append(f"--{key}")
            if isinstance(self.flags_dict[key], str) and self.flags_dict[key]:
                flags_list.append(f"--{key}")
                flags_list.append(f"{self.flags_dict[key]}")
            if isinstance(self.flags_dict[key], list) and self.flags_dict[key]:
                flags_list.append(f"--{key}")
                flags_list.extend(self.flags_dict[key])
        return flags_list
