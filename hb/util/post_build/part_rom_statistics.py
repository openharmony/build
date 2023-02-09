#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright 2023 Huawei Device Co., Ltd.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""

import os
import re
import json

from util.log_util import LogUtil
from resources.config import Config

budle_json_files = []
standard_part_roms = []
part_info_list = []


def part_size_compare(module_info_list, part_name, part_size):
    for standard_part in standard_part_roms:
        if standard_part['part_name'] == part_name and standard_part['part_size'] != 'None':
            sta_size = re.findall(r"\d+", standard_part['part_size'])
            rea_size = re.findall(r"\d+", part_size)
            if int(sta_size[0]) >= int(rea_size[0]):
                conform_str = ("part_name: " + part_name).ljust(55) + \
                              ("actual_size: " + part_size).ljust(25) + \
                              ("standard_size: " + standard_part['part_size']).ljust(25) + \
                               " 'rom' conform to the rules"
                LogUtil.hb_info(conform_str)
                part_info_dict = {}
                part_info_dict["part_name"] = part_name
                part_info_dict["actual_size"] = part_size
                part_info_dict["standard_size"] = standard_part['part_size']
                part_info_dict["status_info"] = "'rom' conform to the rules"
                part_info_dict["modules_info"] = module_info_list
                part_info_list.append(part_info_dict)

            elif int(sta_size[0]) < int(rea_size[0]):
                out_of_standard_str = ("part_name: " + part_name).ljust(55) + \
                                      ("actual_size: " + part_size).ljust(25) + \
                                      ("standard_size: " + standard_part['part_size']).ljust(25) + \
                                       " 'rom' out of standard"
                LogUtil.hb_info(out_of_standard_str)
                part_info_dict = {}
                part_info_dict["part_name"] = part_name
                part_info_dict["actual_size"] = part_size
                part_info_dict["standard_size"] = standard_part['part_size']
                part_info_dict["status_info"] = "'rom' out of standard"
                part_info_dict["modules_info"] = module_info_list
                part_info_list.append(part_info_dict)
        else:
            if standard_part['part_name'] == part_name and standard_part['part_size'] == 'None':
                not_yet_standard_str = ("part_name: " + part_name).ljust(55) + \
                                       ("actual_size: " + part_size).ljust(50) + \
                                        "This part does not set standard 'rom' size".ljust(25)
                LogUtil.hb_info(not_yet_standard_str)
                part_info_dict = {}
                part_info_dict["part_name"] = part_name
                part_info_dict["actual_size"] = part_size
                part_info_dict["standard_size"] = standard_part['part_size']
                part_info_dict["status_info"] = "This part does not set standard 'rom' size"
                part_info_dict["modules_info"] = module_info_list
                part_info_list.append(part_info_dict)


def collect_part_name(root_path):
    install_parts = []
    file_path = os.path.join(root_path, "packages/phone/system_install_parts.json")
    if os.path.isfile(file_path):
        with open(file_path, 'rb') as file:
            file_json = json.load(file)
            for part_info in file_json:
                part_info_dict = {}
                part_info_dict["part_name"] = part_info["part_name"]
                part_info_dict["part_info_file"] = part_info["part_info_file"]
                install_parts.append(part_info_dict)
    return install_parts


def colletct_modules_json_path(out_path, install_parts):
    module_info_list = []
    for part_info_dict in install_parts:
        part_info_path = os.path.join(out_path, part_info_dict["part_info_file"])
        if os.path.isfile(part_info_path):
            with open(part_info_path, 'rb') as file:
                file_json = json.load(file)
                for module_info in file_json:
                    if module_info["part_name"] == part_info_dict["part_name"]:
                        module_json_path = {}
                        module_json_path["module_info_path"] = module_info["module_info_file"]
                        module_json_path["part_name"] = module_info["part_name"]
                        module_info_list.append(module_json_path)
    return module_info_list


def sum_of_statistics(out_path, part_name, module_info_list):
    part_so_size = 0
    module_list = []
    for module_info in module_info_list:
        if part_name == module_info['part_name']:
            module_info_path = os.path.join(out_path, module_info['module_info_path'])
            if os.path.isfile(module_info_path):
                with open(module_info_path, 'rb') as file:
                    file_json = json.load(file)
                    so_file_dir = os.path.join(out_path, file_json["source"])
                    if so_file_dir.endswith(".so") and os.path.isfile(so_file_dir):
                        module_info_dict = {}
                        module_info_dict["module_name"] = file_json["label_name"]
                        module_info_dict["source"] = file_json["source"]
                        module_info_dict["dest"] = file_json["dest"]
                        dest_num = len(file_json["dest"])
                        so_file_size = os.path.getsize(so_file_dir) * dest_num
                        part_so_size += so_file_size
                        module_info_dict["module_size"] = f'{round(so_file_size / 1024, 2)}KB'
                        module_list.append(module_info_dict)
    return module_list, part_so_size


def check_image_size(out_path):
    image_list = []
    image_path = os.path.join(out_path, 'packages/phone/images/')
    if os.path.isdir(image_path):
        for file in os.listdir(image_path):
            if file.endswith(".img"):
                image_dict = {}
                img_path = os.path.join(image_path, file)
                image_dict['img_size'] = f'{round(os.path.getsize(img_path) / 1024, 2)}KB'
                image_dict['img_name'] = file
                image_list.append(image_dict)
    return image_list


def actual_rom_statistics(out_path):
    rom_statistics = {}
    install_parts = collect_part_name(out_path)
    module_info_list = colletct_modules_json_path(out_path, install_parts)
    image_list = check_image_size(out_path)
    rom_statistics["images_info"] = image_list

    for part_info_dict in install_parts:
        statistics_result = sum_of_statistics(out_path, part_info_dict["part_name"], module_info_list)
        part_so_size = f'{round(statistics_result[1] / 1024, 2)}KB'
        part_size_compare(statistics_result[0],
                            part_info_dict["part_name"],
                            part_so_size)
    rom_statistics["parts_info"] = part_info_list
    json_path = os.path.join(out_path, 'rom_statistics_table.json')
    json_str = json.dumps(rom_statistics, indent=4)
    with open(json_path, 'w') as json_file:
        json_file.write(json_str)
    

def read_bundle_json_file(file_path):
    with open(file_path, 'rb') as file:
        file_json = json.load(file)
        standard_part_rom = {}
        standard_part_rom["part_name"] = file_json["component"]["name"]
        if 'rom' not in file_json["component"].keys() or file_json["component"]["rom"] == '':
            standard_part_rom["part_size"] = 'None'
        else:
            standard_part_rom["part_size"] = file_json["component"]["rom"]
        if standard_part_roms.count(standard_part_rom) == 0:
            standard_part_roms.append(standard_part_rom)


def collect_bundle_json_path(part_root_path):
    for root, dirs, files in os.walk(part_root_path):
        abs_path = os.path.abspath(root)
        for file_name in files:
            if file_name == 'bundle.json':
                budle_json_files.append(os.path.join(abs_path, file_name))


def read_subsystem_config(root_path):
    part_json_paths = []
    part_json_path = os.path.join(root_path, 'build/subsystem_config.json')
    if os.path.isfile(part_json_path):
        with open(part_json_path, 'r') as file:
            file_json = json.load(file)
            for part_info_valule in file_json.values():
                for path_k, path_v in part_info_valule.items():
                    if path_k == "path":
                        part_json_paths.append(path_v)
    config = Config()
    part_json_overlay_path = config.product_path
    if os.path.isfile(part_json_overlay_path):
        with open(part_json_overlay_path, 'r') as file:
            file_json = json.load(file)
            for part_info_valule in file_json.values():
                for path_k, path_v in part_info_valule.items():
                    if path_k == "path":
                        part_json_paths.append(path_v)

    return part_json_paths


def read_ohos_config(root_path):
    file_path = os.path.join(root_path, "ohos_config.json")
    with open(file_path, 'r') as file:
        file_json = json.load(file)
        os_level = file_json["os_level"]
        out_path = file_json["out_path"]
        board = file_json["board"]
        product = file_json["product"]
    return (out_path, board, product, os_level)


def output_part_rom_status(root_path):
    ohos_config = read_ohos_config(root_path)
    if ohos_config[3] == "mini":
        return -1
    elif ohos_config[3] == "small":
        return -1
    else:
        part_paths = read_subsystem_config(root_path)
        for part_path in part_paths:
            part_root_path = os.path.join(root_path, part_path)
            if os.path.isdir(part_root_path):
                collect_bundle_json_path(part_root_path)
        for json_file in budle_json_files:
            if os.path.exists(json_file):
                read_bundle_json_file(json_file)
        actual_rom_statistics(ohos_config[0])
    return 0
