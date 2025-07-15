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
import os
import json
import time


class PreuiltsService(BuildFileGeneratorInterface):

    def __init__(self):
        ohos_dir = self.get_ohos_dir()
        self.last_update = os.path.join(ohos_dir, "prebuilts/.local_data/last_update.json")
        super().__init__()

    def run(self):
        if not "--enable-prebuilts" in sys.argv:
            return
        if not self.check_whether_need_update():
            LogUtil.hb_info("you have already execute prebuilts download step and no configs changed, skip this step")
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
            self.write_last_update({"last_update": time.time()})
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

    def check_whether_need_update(self) -> bool:
        last_update = self.read_last_update().get("last_update", 0)
        if not last_update:
            LogUtil.hb_info("No last update record found, will update prebuilts")
            return True
        else:
            if self.check_file_changes():
                LogUtil.hb_info("Prebuilts config file has changed, will update prebuilts")
                return True
            else:
                return False

    def read_last_update(self):
        if not os.path.exists(self.last_update):
            return {}
        try:
            with open(self.last_update, 'r') as f:
                return json.load(f)
        except Exception as e:
            LogUtil.hb_error(f"Failed to read last update file: {e}")
            return {}
    
    def write_last_update(self, data):
        os.makedirs(os.path.dirname(self.last_update), exist_ok=True)
        try:
            with open(self.last_update, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            LogUtil.hb_error(f"Failed to write last update file: {e}")

    def get_ohos_dir(self):
        cur_dir = os.getcwd()
        while cur_dir != "/":
            global_var = os.path.join(
                cur_dir, 'build', 'hb', 'resources', 'global_var.py')
            if os.path.exists(global_var):
                return cur_dir
            cur_dir = os.path.dirname(cur_dir)
        raise Exception("you must run this script in ohos dir")

    def get_preguilt_download_related_files_mtimes(self) -> dict:
        dir_path = os.path.join(self.get_ohos_dir(), "build/prebuilts_service")
        mtimes = {}
        for root, _, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                mtimes[file_path] = os.path.getmtime(file_path)
        prebuilts_config_json_path = os.path.join(self.get_ohos_dir(), "build/prebuilts_config.json")
        prebuilts_config_py_path = os.path.join(self.get_ohos_dir(), "build/prebuilts_config.py")
        prebuilts_config_shell_path = os.path.join(self.get_ohos_dir(), "build/prebuilts_config.sh")
        mtimes.update({prebuilts_config_json_path: os.path.getmtime(prebuilts_config_json_path)})
        mtimes.update({prebuilts_config_py_path: os.path.getmtime(prebuilts_config_py_path)})
        mtimes.update({prebuilts_config_shell_path: os.path.getmtime(prebuilts_config_shell_path)})
        return mtimes

    def check_file_changes(self) -> bool:
        """
        check if the directory has changed by comparing file modification times.
        :param dir_path: directory
        :param prev_mtimes: last known modification times of files in the directory 
        :return: if the directory has changed, and the current modification times of files in the directory
        """
        last_update = self.read_last_update().get("last_update", 0)
        current_mtimes = self.get_preguilt_download_related_files_mtimes()
        for _, mtime in current_mtimes.items():
            if mtime > last_update:
                return True
        return False