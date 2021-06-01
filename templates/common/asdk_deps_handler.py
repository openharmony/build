#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 Huawei Device Co., Ltd.
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

import sys
import os
import argparse
import json

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from scripts.util.file_utils import read_json_file, \
    write_json_file  # noqa: E402

ASDK_LIBS_SDK_DIR = 'prebuilts/aosp_prebuilt_libs/asdk_libs/sdk'

LIB_TYPE_LIST = ['shared_library', 'static_library']


def _search_for_allowlist_file(current_dir, top_dir, allowlist_file):
    if (not current_dir) or current_dir == top_dir:
        return None
    if not os.path.exists(current_dir):
        return _search_for_allowlist_file(os.path.dirname(current_dir),
                                          top_dir, allowlist_file)
    for _file in os.listdir(current_dir):
        file_path = os.path.join(current_dir, _file)
        if os.path.isfile(file_path) and os.path.basename(
                file_path) == allowlist_file:
            return '{}/{}'.format(current_dir, allowlist_file)
    return _search_for_allowlist_file(os.path.dirname(current_dir), top_dir,
                                      allowlist_file)


def _get_label_name(lib_type, lib_name):
    if lib_type == 'static_library':
        return '{}_static'.format(lib_name)
    elif lib_type == 'jar':
        return '{}_java'.format(lib_name)
    elif lib_type == 'maple':
        return '{}_maple_java'.format(lib_name)
    else:
        return lib_name


def _get_adapter_module_cc(libraries, lib_name):
    labels = None
    if libraries:
        lib_desc = libraries.get(lib_name)
        if lib_desc:
            label_info = lib_desc.get('label')
            if isinstance(label_info, list):
                labels = label_info
            else:
                labels = [label_info]
    return labels


def _get_adapter_module_java(libraries, lib_name):
    labels = None
    if libraries:
        lib_desc = libraries.get(lib_name)
        if lib_desc:
            label_info = lib_desc.get('label')
            if isinstance(label_info, list):
                labels = label_info
            else:
                labels = [label_info]
    return labels


def _is_cc_library(lib_type):
    return lib_type in ['shared_library', 'static_library']


def _cc_handle(lib_type, lib_name, target_arch, adapter_modules_info):
    _dep_modules_info = []
    if lib_name in adapter_modules_info:
        adapter_labels = _get_adapter_module_cc(adapter_modules_info, lib_name)
        if adapter_labels is None:
            raise Exception("error: asdk adapter config error.")
        for adapter_label in adapter_labels:
            info_dict = {}
            info_dict['label'] = adapter_label
            _dep_modules_info.append(info_dict)
    else:
        _build_file_path = '//{}/{}/{}'.format(ASDK_LIBS_SDK_DIR, lib_type,
                                               target_arch)
        _real_name = _get_label_name(lib_type, lib_name)
        info_dict = {'label': '{}:{}'.format(_build_file_path, _real_name)}
        _dep_modules_info.append(info_dict)
    return _dep_modules_info


def _java_handle(lib_type, lib_name, adapter_modules_info):
    _dep_modules_info = []
    _real_name = _get_label_name(lib_type, lib_name)
    if _real_name in adapter_modules_info:
        adapter_labels = _get_adapter_module_java(adapter_modules_info,
                                                  _real_name)
        if adapter_labels is None:
            raise Exception("error: asdk adapter config error.")
        for _label in adapter_labels:
            info_dict = {'label': _label}
            _dep_modules_info.append(info_dict)
    else:
        build_file_path = '//{}/java'.format(ASDK_LIBS_SDK_DIR)
        info_dict = {'label': '{}:{}'.format(build_file_path, _real_name)}
        _dep_modules_info.append(info_dict)
    return _dep_modules_info


def _handle(asdk_deps, target_arch, adapter_modules_info):
    _result = []
    cc_libs_list = []
    for asdk_dep in asdk_deps:
        asdk_dep_desc = asdk_dep.split(':')
        if len(asdk_dep_desc) != 2:
            raise Exception("asdk dep '{}' config error.".format(asdk_dep))
        lib_type = asdk_dep_desc[0]
        lib_name = asdk_dep_desc[1]
        if lib_type not in LIB_TYPE_LIST:
            raise Exception(
                "asdk dep '{}' config error, lib type not support.".format(
                    asdk_dep))
        if _is_cc_library(lib_type):
            cc_libs_list.append(lib_name)
            dep_modules_info = _cc_handle(lib_type, lib_name, target_arch,
                                          adapter_modules_info)
        else:
            dep_modules_info = _java_handle(lib_type, lib_name,
                                            adapter_modules_info)
        _result.extend(dep_modules_info)
    return _result


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--asdk-deps', nargs='+', required=True)
    parser.add_argument('--asdk-deps-temp-file', required=True)
    parser.add_argument('--target-os', default='ohos')
    parser.add_argument('--target-cpu', default='arm64')
    args = parser.parse_args(argv)
    result = []
    # read adapter modules info
    adapter_modules_info = {}
    target_arch = args.target_cpu
    result = _handle(args.asdk_deps, target_arch, adapter_modules_info)
    write_json_file(args.asdk_deps_temp_file, result)
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
