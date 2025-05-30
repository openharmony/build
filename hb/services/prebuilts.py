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

import subprocess
import sys
from services.interface.build_file_generator_interface import (
    BuildFileGeneratorInterface,
)
from util.log_util import LogUtil


class PreuiltsService(BuildFileGeneratorInterface):

    def __init__(self):
        super().__init__()

    def run(self):
        if not "--open-prebuilts" in sys.argv:
            return
        flags_list = self._convert_flags()
        if "--skip-prebuilts" in flags_list:
            print("Skip preuilts download")
            return
        part_names = self._get_part_names()
        try:
            cmd = ["/bin/bash", "build/prebuilts_config.sh", "--part-names"]
            cmd.extend(part_names)
            cmd_str = " ".join(cmd)
            tips = (
                f"Running cmd: \"{cmd_str}\""
                + ", you can use --skip-preuilts to skip this step"
            )
            LogUtil.hb_info(tips)
            subprocess.run(
                cmd, check=True, stdout=None, stderr=None  # 直接输出到终端
            )  # 直接输出到终端
        except subprocess.CalledProcessError as e:
            print(f"{cmd} execute failed: {e.returncode}")
            raise e

    def _get_part_names(self):
        part_name_list = []
        if len(sys.argv) > 2 and not sys.argv[2].startswith("-"):
            for name in sys.argv[2:]:
                if not name.startswith("-"):
                    part_name_list.append(name)
                else:
                    break
        return part_name_list

    def _convert_flags(self) -> list:
        flags_list = []
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
