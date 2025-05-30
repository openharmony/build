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
from services.interface.build_file_generator_interface import BuildFileGeneratorInterface


class PreuiltsService(BuildFileGeneratorInterface):

    def __init__(self):
        super().__init__()

    def _get_part_names(self):
        part_name_list = []
        if len(sys.argv) > 2 and not sys.argv[2].startswith("-"):
            for name in sys.argv[2:]:
                if not name.startswith('-'):
                    part_name_list.append(name)
                else:
                    break
        return part_name_list

        
    def run(self):
        if "--skip-prebuilts" in sys.argv:
            print("Skip preuilts download")
            return
        part_names = self._get_part_names()
        tips = "[TIPS] Running prebuilts_config.sh for parts:" + " ".join(part_names) + ", you can use --skip-preuilts to skip this step"
        print(tips)
        try:
            cmd = [
                "/bin/bash", 
                "build/prebuilts_config.sh",
                "--part-names"
            ]
            cmd.extend(part_names)
            subprocess.run(cmd, 
                           check=True,
                           stdout=None,  # 直接输出到终端
                           stderr=None)  # 直接输出到终端
        except subprocess.CalledProcessError as e:
            print(f"{cmd} execute failed: {e.returncode}")
            raise e