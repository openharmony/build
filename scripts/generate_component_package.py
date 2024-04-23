#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2024 Huawei Device Co., Ltd.
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
import shutil
import json
import time
from hb.util.log_util import LogUtil
import re


def _get_public_external_deps(data, public_deps):
    if not isinstance(data, dict):
        return ""
    for key, value in data.items():
        if not isinstance(value, dict):
            continue

        for key_1, value_1 in value.items():
            label = value_1.get("label")
            if public_deps == label:
                return key + ":" + key_1

    return ""


def _is_innerkit(data, part, module):
    if not isinstance(data, dict):
        return False

    part_data = data.get(part)
    if not isinstance(part_data, dict):
        return False

    if module in part_data:
        return True

    return False


def _get_inner_kits_info(out_path):
    jsondata = ""
    json_path = os.path.join(out_path + "/build_configs/parts_info/inner_kits_info.json")
    with open(json_path,"r") as f:
        try:
            jsondata = json.load(f)
        except Exception as e:
            print('--_get_inner_kits_info parse json error--', e)
    return jsondata


def _get_module_name(json_data):
    part_data = json_data.get(part_name)
    if isinstance(data_list, list) and len(json_data.get(json_key)) >= 1:
        desc_list.extend(data_list)
    else:
        desc_list.append(json_data.get(json_key))


def _handle_one_layer_json(json_key, json_data, desc_list):
    data_list = json_data.get(json_key)
    if isinstance(data_list, list) and len(json_data.get(json_key)) >= 1:
        desc_list.extend(data_list)
    else:
        desc_list.append(json_data.get(json_key))


def _handle_two_layer_json(json_key, json_data, desc_list):
    value_depth = len(json_data.get(json_key))
    for i in range(value_depth):
        _include_dirs = json_data.get(json_key)[i].get('include_dirs')
        if _include_dirs:
            desc_list.extend(_include_dirs)


def _get_json_data(args, module):
    json_path = os.path.join(args.get("out_path"),
                             args.get("subsystem_name"), args.get("part_name"), "publicinfo", module + ".json")
    with open(json_path,"r") as f:
        try:
            jsondata = json.load(f)
        except Exception as e:
            print('--_get_json_data parse json error--', e)
    return jsondata


def _handle_deps_data(json_data):
    dep_list = []
    if json_data.get('public_deps'):
        _handle_one_layer_json('public_deps', json_data, dep_list)
    return dep_list


def _handle_includes_data(json_data):
    include_list = []
    if json_data.get('public_configs'):
        _handle_two_layer_json('public_configs', json_data, include_list)
    if json_data.get('all_dependent_configs'):
        _handle_two_layer_json('all_dependent_configs', json_data, include_list)
    return include_list


def _get_static_lib_path(args, json_data):
    label = json_data.get('label')
    split_label = label.split("//")[1].split(":")[0]
    real_static_lib_path = os.path.join(args.get("out_path"), "obj",
                                        split_label, json_data.get('out_name'))
    return real_static_lib_path


def _copy_dir(src_path, target_path):
    if not os.path.isdir(src_path):
        return False
    filelist_src = os.listdir(src_path)
    for file in filelist_src:
        path = os.path.join(os.path.abspath(src_path), file)
        if os.path.isdir(path):
            if file.startswith("."):
                continue
            path1 = os.path.join(target_path, file)
            _copy_dir(path, path1)
        else:
            if not path.endswith(".h"):
                continue
            with open(path, 'rb') as read_stream:
                contents = read_stream.read()
            if not os.path.exists(target_path):
                os.makedirs(target_path)
            path1 = os.path.join(target_path, file)
            with os.fdopen(os.open(path1, os.O_WRONLY | os.O_CREAT, mode=0o640), "wb") as write_stream:
                write_stream.write(contents)
    return True


def _copy_includes(args, module, includes: list):
    includes_out_dir = os.path.join(args.get("out_path"), "component_package",
                                    args.get("part_path"), "innerapis", module, "includes")
    if not os.path.exists(includes_out_dir):
        os.makedirs(includes_out_dir)
    for include in includes:
        splitInclude = include.split("//")[1]
        realIncludePath = os.path.join(args.get("root_path"), splitInclude)
        _copy_dir(realIncludePath, includes_out_dir)
    print("_copy_includes has done ")


def _copy_lib(args, json_data, module):
    so_path = ""
    if json_data.get('type') == 'static_library':
        so_path = _get_static_lib_path(args, json_data)
    else:
        so_path = os.path.join(args.get("out_path"), args.get("subsystem_name"),
                               args.get("part_name"), json_data.get('out_name'))
    if os.path.isfile(so_path):
        lib_out_dir = os.path.join(args.get("out_path"), "component_package",
                                   args.get("part_path"), "innerapis", module, "libs")
        if not os.path.exists(lib_out_dir):
            os.makedirs(lib_out_dir)
        shutil.copy(so_path, lib_out_dir)
        return True
    else:
        return False


def _copy_bundlejson(args):
    bundlejson_out = os.path.join(args.get("out_path"), "component_package", args.get("part_path"))
    print("bundlejson_out : ", bundlejson_out)
    if not os.path.exists(bundlejson_out):
        os.makedirs(bundlejson_out)
    bundlejson = os.path.join(args.get("root_path"), args.get("part_path"), "bundle.json")
    if os.path.isfile(bundlejson):
        with open(bundlejson, 'r') as f:
            bundle_data = json.load(f)
        bundle_data['publishAs'] = 'binary'
        bundle_data['os'] = 'linux'
        bundle_data['buildArch'] = 'x86'
        dirs = dict()
        dirs['./'] = []
        directory = bundlejson_out
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                dirs['./'].append(filename)
            else:
                dirs[filename] = [filename + "/*"]
        delete_list = ['LICENSE', 'README.md', 'README_zh.md', 'README_en.md', 'bundle.json']
        for delete_txt in delete_list:
            if delete_txt in dirs['./']:
                dirs['./'].remove(delete_txt)
        if dirs['./'] == []:
            del dirs['./']
        bundle_data['dirs'] = dirs
        bundle_data['version'] = str(bundle_data['version'])
        if bundle_data['version'] == '':
            bundle_data['version'] = '1.0.0'
        pattern = r'^(\d+)\.(\d+)(-[a-zA-Z]+)?$'  # 正则表达式匹配a.b[-后缀]格式的字符串
        match = re.match(pattern, bundle_data['version'])
        if match:
            a = match.group(1)
            b = match.group(2)
            suffix = match.group(3) if match.group(3) else ""
            bundle_data['version'] = f"{a}.{b}.0{suffix}"
        with os.fdopen(os.open(os.path.join(bundlejson_out, "bundle.json"), os.O_WRONLY | os.O_CREAT, mode=0o640), "w",
                       encoding='utf-8') as fd:
            json.dump(bundle_data, fd, indent=4, ensure_ascii=False)


def _copy_license(args):
    license_out = os.path.join(args.get("out_path"), "component_package", args.get("part_path"))
    print("license_out : ", license_out)
    if not os.path.exists(license_out):
        os.makedirs(license_out)
    license = os.path.join(args.get("root_path"), args.get("part_path"), "LICENSE")
    if os.path.isfile(license):
        shutil.copy(license, license_out)


def _copy_readme(args):
    readme_out = os.path.join(args.get("out_path"), "component_package", args.get("part_path"))
    print("readme_out : ", readme_out)
    if not os.path.exists(readme_out):
        os.makedirs(readme_out)
    readme = os.path.join(args.get("root_path"), args.get("part_path"), "README.md")
    if os.path.isfile(readme):
        shutil.copy(readme, readme_out)
    readme_zh = os.path.join(args.get("root_path"), args.get("part_path"), "README_zh.md")
    if os.path.isfile(readme_zh):
        shutil.copy(readme_zh, readme_out)
    readme_en = os.path.join(args.get("root_path"), args.get("part_path"), "README_en.md")
    if os.path.isfile(readme_en):
        shutil.copy(readme_en, readme_out)


def _generate_import(fp):
    fp.write('import("//build/ohos.gni")\n')


def _generate_configs(fp, module):
    fp.write('\nconfig("' + module + '_configs") {\n')
    fp.write('  visibility = [ ":*" ]\n')
    fp.write('  include_dirs = [\n')
    fp.write('    "includes"\n')
    fp.write('  ]\n}\n')


def _generate_prebuilt_shared_library(fp, type, module):
    if type == 'static_library':
        fp.write('ohos_prebuilt_static_library("' + module + '") {\n')
    else:
        fp.write('ohos_prebuilt_shared_library("' + module + '") {\n')


def _generate_public_configs(fp, module):
    fp.write('  public_configs = [":' + module + '_configs"]\n')


def _generate_public_deps(fp, deps: list, innerkit_json):
    if not deps:
        return
    fp.write('  public_external_deps = [\n')
    for dep in deps:
        public_external_deps = _get_public_external_deps(innerkit_json, dep)
        if len(public_external_deps) > 0:
            fp.write('    "' + public_external_deps + '",\n')
    fp.write('  ]\n')


def _generate_other(fp, args, json_data, module):
    so_name = json_data.get('out_name')
    fp.write('  source = "libs/' + so_name + '"\n')
    fp.write('  part_name = "' + args.get("part_name") + '"\n')
    fp.write('  subsystem_name = "' + args.get("subsystem_name") + '"\n')


def _generate_end(fp):
    fp.write('}')


def _generate_build_gn(args, module, json_data, deps: list, innerkit_json):
    gn_path = os.path.join(args.get("out_path"), "component_package", args.get("part_path"),
                           "innerapis", module, "BUILD.gn")
    fd = os.open(gn_path, os.O_WRONLY | os.O_CREAT, mode=0o640)
    fp = os.fdopen(fd, 'w')
    _generate_import(fp)
    _generate_configs(fp, module)
    _generate_prebuilt_shared_library(fp, json_data.get('type'), module)
    _generate_public_configs(fp, module)
    _generate_public_deps(fp, deps, innerkit_json)
    _generate_other(fp, args, json_data, module)
    _generate_end(fp)
    print("_generate_build_gn has done ")
    fp.close()


def _parse_module_list(args):
    module_list = []
    publicinfoPath = os.path.join(args.get("out_path"),
                                  args.get("subsystem_name"), args.get("part_name"), "publicinfo")
    print('publicinfoPath', publicinfoPath)
    if os.path.exists(publicinfoPath) is False:
        return module_list
    publicinfoDir = os.listdir(publicinfoPath)
    for filename in publicinfoDir:
        if filename.endswith(".json"):
            module_name = filename.split(".json")[0]
            module_list.append(module_name)
            print('filename', filename)
    print('module_list', module_list)
    return module_list


def _generate_component_package(args, innerkit_json):
    modules = _parse_module_list(args)
    if len(modules) == 0:
        return
    is_component_build = False
    for module in modules:
        if _is_innerkit(innerkit_json, args.get("part_name"), module) == False:
            continue
        json_data = _get_json_data(args, module)
        lib_exists = _copy_lib(args, json_data, module)
        if lib_exists is False:
            continue
        is_component_build = True
        includes = _handle_includes_data(json_data)
        deps = _handle_deps_data(json_data)
        _copy_includes(args, module, includes)
        _generate_build_gn(args, module, json_data, deps, innerkit_json)
    if is_component_build:
        _copy_bundlejson(args)
        _copy_license(args)
        _copy_readme(args)


def _get_part_subsystem(out_path):
    jsondata = ""
    json_path = os.path.join(out_path + "/build_configs/parts_info/part_subsystem.json")
    with open(json_path,"r") as f:
        try:
            jsondata = json.load(f)
        except Exception as e:
            print('--_get_part_subsystem parse json error--', e)
    return jsondata


def _get_parts_path_info(out_path):
    jsondata = ""
    json_path = os.path.join(out_path + "/build_configs/parts_info/parts_path_info.json")
    with open(json_path,"r") as f:
        try:
            jsondata = json.load(f)
        except Exception as e:
            print('--_get_parts_path_info parse json error--', e)
    return jsondata


def _get_parts_path(json_data, part_name):
    parts_path = None
    if json_data.get(part_name) is not None:
        parts_path = json_data[part_name]
    return parts_path


def generate_component_package(out_path, root_path):
    start_time = time.time()
    part_subsystem = _get_part_subsystem(out_path)
    parts_path_info = _get_parts_path_info(out_path)
    inner_kits_info = _get_inner_kits_info(out_path)
    for key, value in part_subsystem.items():
        part_name = key
        subsystem_name = value
        part_path = _get_parts_path(parts_path_info, part_name)
        if part_path is None:
            continue
        args = {"subsystem_name": subsystem_name, "part_name": part_name,
                "out_path": out_path, "root_path": root_path, "part_path": part_path}
        _generate_component_package(args, inner_kits_info)
    end_time = time.time()
    run_time = end_time - start_time
    print("generate_component_package out_path", out_path)
    print(f"生成二进制产物包耗时：{run_time}秒")