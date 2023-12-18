#!/usr/bin/env python3
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
import json

from util.log_util import LogUtil


def parse_cflags(line, cflags_check_list, whitelist):
    cflags_list = []
    for flag in line.split():
        if flag.startswith('-Wno-') and flag not in whitelist:
            cflags_list.append(flag)
        elif flag in cflags_check_list:
            cflags_list.append(flag)
    return cflags_list


def parse_ldflags(line, ldflags_check_list, whitelist):
    ldflags_list = []
    for flag in line.split():
        if flag in ldflags_check_list and flag not in whitelist:
            ldflags_list.append(flag)
    return ldflags_list


def parse_ninja_file(root_path, ninja_file):
    flag = list()
    whitelist, ldflags_check_list, cflags_check_list = read_check_list(root_path)
    with open(ninja_file, 'r') as file:
        for line in file:
            if line.startswith('cflags') or line.startswith('cflags_cc') or line.startswith('cflags_c'):
                flag = parse_cflags(line, cflags_check_list, whitelist)
            elif line.startswith('ldflags'):
                flag = parse_ldflags(line, ldflags_check_list, whitelist)
            elif line.startswith('label_name'):
                label_name = line.split()[2]
            elif line.startswith('target_out_dir'):
                target_out_dir = line.split()[2]
    if flag:
        build_target = '{}:{}'.format(target_out_dir.replace('obj/', ''), label_name)
        LogUtil.hb_info('build target "{}" used illegal build parameters {}'.format(build_target, flag))


def collect_ninja_file_path(obj_path):
    ninja_file_list = []
    for root, dirs, files in os.walk(obj_path):
        for file_name in files:
            if file_name.endswith('.ninja'):
                ninja_file_list.append(os.path.join(root, file_name))
    return ninja_file_list


def read_ohos_config(root_path):
    file_path = os.path.join(root_path, 'out', 'ohos_config.json')
    with open(file_path, 'r') as file:
        file_json = json.load(file)
        out_path = file_json.get('out_path')
    return out_path


def read_check_list(root_path):
    file_path = os.path.join(root_path, 'build', 'hb', 'util', 'post_gn', 'check_list.json')
    with open(file_path, 'r') as file:
        file_json = json.load(file)
        whitelist = file_json.get('whitelist')
        ldflags_check_list = file_json.get('ldflags_check_list')
        cflags_check_list = file_json.get('cflags_check_list')
    return whitelist, ldflags_check_list, cflags_check_list


def check_compilation_parameters(root_path):
    out_path = read_ohos_config(root_path)
    ninja_file_list = collect_ninja_file_path(os.path.join(out_path, 'obj'))
    for ninja_file in ninja_file_list:
        parse_ninja_file(root_path, ninja_file)
    return 0
