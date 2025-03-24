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
        fix_order_dict, file_list = BootPathCollection.collect_list(origin_path)
        directory = os.path.dirname(os.path.join(dest_path, f"framework/bootpath.json"))
        new_json_file = os.path.join(directory, f"bootpath.json")

        data = {}
        if os.path.exists(new_json_file):
            with open(new_json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

        current_value = data.get("bootpath", "")
        abc_set = set(current_value.split(":")) if current_value else set()
        abc_set.update(file_list)

        fix_path = ":".join(f"{fix_order_dict[key]}" for key in fix_order_dict.keys())
        data["bootpath"] = fix_path + ":" + ":".join(abc_set)

        os.makedirs(directory, exist_ok=True)

        with open(new_json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)


    @staticmethod
    def collect_list(target_out_path):
        directory = os.path.dirname(target_out_path)
        # fix order jsons of bootpath.json, and arkoala will be removed here
        # when bootpath generation is separated from generate static abc
        fix_order_dict = {
            "ets2abc_etsstdlib_bootabc_bootpath.json": "",
            "base_sdk_bootpath.json": "",
            "ets2abc_commonsdk_bootpath.json": "",
            "arkoala_bootpath.json": "/system/framework/arkoala.abc"
        }
        rest_file_list = []
        for root, subdirs, files in os.walk(directory):
            for _filename in files:
                if "_bootpath" in _filename and _filename in fix_order_dict:
                    # target bootpath.json with fixed order, store in fix_order_dict
                    content = read_json_file(os.path.join(root, _filename))
                    fix_order_dict[_filename] = content["bootpath"]
                elif "_bootpath" in _filename:
                    # other bootpath.json, stores in rest_file_list
                    content = read_json_file(os.path.join(root, _filename))
                    rest_file_list.append(content["bootpath"])
        
        return fix_order_dict, rest_file_list


if __name__ == "__main__":
    pass