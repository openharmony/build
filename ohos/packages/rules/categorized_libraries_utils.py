#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2024 Huawei Device Co., Ltd.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#	 http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import os

sys.path.append(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))))
from scripts.util.file_utils import read_json_file  # noqa: E402


def __get_relative_install_dir(categories):
    is_platforsdk = False
    is_chipsetsdk = False
    is_chipsetsdk_sp = False
    is_llndk = False
    is_ndk = False
    is_passthrough = False
    is_passthrough_indirect = False
    for cat in categories:
        if cat.startswith("platformsdk"):
            is_platforsdk = True
        elif cat.startswith("chipsetsdk"):
            if cat.startswith("chipsetsdk_sp"):
                is_chipsetsdk_sp = True
            else:
                is_chipsetsdk = True
        elif cat.startswith("passthrough"):
            if cat.startswith("passthrought_indirect"):
                is_passthrough_indirect = True
            else:
                is_passthrough = True
        if cat == "ndk":
            is_ndk = True
        if cat == "llndk":
            is_llndk = True
    if is_llndk:
        return "llndk"
    if is_ndk:
        return "ndk"
    if is_chipsetsdk_sp:
        return "chipset-sdk-sp"
    if is_chipsetsdk:
        return "chipset-sdk"
    if is_passthrough:
        return "passthrough"
    if is_passthrough_indirect:
        return "passthrough/indirect"
    if is_platforsdk:
        return "platformsdk"
    return ""


def load_categorized_libraries(file_name):
    res = read_json_file(file_name)

    for key, val in res.items():
        val["relative_install_dir"] = __get_relative_install_dir(val["categories"])
    return res


#
# module_info is an json object including label and dest 
# update_module_info will update dest according to label category
#
def update_module_info(module_info, categorized_libraries):
    if "dest" not in module_info:
        return

    label = module_info["label"]
    pos = label.find("(")
    if pos > 0:
        label = label[:label.find("(")]
    if label not in categorized_libraries:
        return

    dest = []
    for item in module_info["dest"]:
        pos = item.rfind("/")
        if pos < 0:
            dest.append(item)
            continue
        lib_name = item[pos + 1:]
        dir_name = item[:pos]

        if dir_name.endswith("chipset-sdk") or dir_name.endswith("platformsdk") \
        or dir_name.endswith("chipsetsdk") or dir_name.endswith("chipset-sdk-sp") or dir_name.endswith("chipset-pub-sdk") or \
                dir_name.endswith("passthrough/indirect") or dir_name.endswith("passthrough"):
            dir_name = dir_name[:dir_name.rfind("/")]
        dest.append("{}/{}/{}".format(dir_name, categorized_libraries[label]["relative_install_dir"], lib_name))
    module_info["dest"] = dest


if __name__ == '__main__':
    categories = load_categorized_libraries(os.path.join(
          os.path.dirname(os.path.abspath(__file__)), "categorized-libraries.json"))
    module_info = {
        "dest": ["system/lib/chipset-pub-sdk/libaccesstoken_sdk.z.so"],
        "label": "//base/security/access_token/interfaces/innerkits/accesstoken:libaccesstoken_sdk"
    }
    update_module_info(module_info, categories)
    print(module_info)
