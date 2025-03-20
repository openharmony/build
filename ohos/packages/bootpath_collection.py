#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Huawei Device Co., Ltd.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import json

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from scripts.util.file_utils import read_json_file


class BootPathCollection():

    @staticmethod
    def run(dest_path):
        origin_path = "obj/arkcompiler/ets_frontend/ets2panda/aot/build/config/components/ets_frontend/bootpath.json"
        file_list = BootPathCollection.collect_list(origin_path)
        directory = os.path.dirname(os.path.join(dest_path, f"framework/bootpath.json"))
        new_json_file = os.path.join(directory, f"bootpath.json")

        data = {}
        if os.path.exists(new_json_file):
            with open(new_json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

        current_value = data.get("bootpath", "")
        abc_set = set(current_value.split(":")) if current_value else set()
        abc_set.update(file_list)
        data["bootpath"] = ":".join(abc_set)

        os.makedirs(directory, exist_ok=True)

        with open(new_json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)


    @staticmethod
    def collect_list(target_out_path):
        directory = os.path.dirname(target_out_path)
        file_list = []
        for root, subdirs, files in os.walk(directory):
            for _filename in files:
                if "_bootpath" in _filename:
                    content = read_json_file(os.path.join(root, _filename))
                    file_list.append(content["bootpath"])
        return file_list


if __name__ == "__main__":
    pass