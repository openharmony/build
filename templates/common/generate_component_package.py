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
import subprocess
import sys
import stat
import os
import argparse
import shutil
import json
import time
import re
import urllib.request


def _get_args():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("-op", "--out_path", default=r"./", type=str,
                        help="path of out.", )
    parser.add_argument("-rp", "--root_path", default=r"./", type=str,
                        help="path of root. default: ./", )
    parser.add_argument("-cl", "--components_list", default="", type=str,
                        help="components_list , "
                             "pass in the components' name, separated by commas , "
                             "example: A,B,C . "
                             "default: none", )
    parser.add_argument("-bt", "--build_type", default=0, type=int,
                        help="build_type ,default: 0", )
    parser.add_argument("-on", "--organization_name", default='ohos', type=str,
                        help="organization_name ,default: '' ", )
    parser.add_argument("-os", "--os_arg", default=r"linux", type=str,
                        help="path of output file. default: linux", )
    parser.add_argument("-ba", "--build_arch", default=r"x86", type=str,
                        help="build_arch_arg. default: x86", )
    parser.add_argument("-lt", "--local_test", default=0, type=int,
                        help="local test ,default: not local , 0", )
    args = parser.parse_args()
    return args


def _check_label(public_deps, value):
    innerapis = value["innerapis"]
    for _innerapi in innerapis:
        if _innerapi:
            label = _innerapi.get("label")
            if public_deps == label:
                return label.split(':')[-1]
            continue
    return ""


def _get_public_external_deps(data, public_deps):
    if not isinstance(data, dict):
        return ""
    for key, value in data.items():
        if not isinstance(value, dict):
            continue
        _data = _check_label(public_deps, value)
        if _data:
            return f"{key}:{_data}"
        continue
    return ""


def _is_innerkit(data, part, module):
    if not isinstance(data, dict):
        return False

    part_data = data.get(part)
    if not isinstance(part_data, dict):
        return False
    module_list = []
    for i in part_data["innerapis"]:
        if i:
            module_list.append(i["name"])
    if module in module_list:
        return True
    return False


def _get_components_json(out_path):
    jsondata = ""
    json_path = os.path.join(out_path + "/build_configs/parts_info/components.json")
    with os.fdopen(os.open(json_path, os.O_RDWR | os.O_CREAT, stat.S_IWUSR | stat.S_IRUSR),
            'r', encoding='utf-8') as f:
        try:
            jsondata = json.load(f)
        except Exception as e:
            print('--_get_components_json parse json error--')
    return jsondata


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
    with os.fdopen(os.open(json_path, os.O_RDWR | os.O_CREAT, stat.S_IWUSR | stat.S_IRUSR),
            'r', encoding='utf-8') as f:
        try:
            jsondata = json.load(f)
        except Exception as e:
            print(json_path)
            print('--_get_json_data parse json error--')
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
    suffix_list = [".h", ".hpp", ".in", ".inc", ".inl"]
    for file in filelist_src:
        path = os.path.join(os.path.abspath(src_path), file)
        if os.path.isdir(path):
            if file.startswith("."):
                continue
            path1 = os.path.join(target_path, file)
            _copy_dir(path, path1)
        else:
            if not (os.path.splitext(path)[-1] in suffix_list):
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
    if module == 'ipc_single':
        includes = [
            "//foundation/communication/ipc/interfaces/innerkits/ipc_core/include",
            "//foundation/communication/ipc/ipc/native/src/core/include",
            "//foundation/communication/ipc/ipc/native/src/mock/include",
        ]
    includes_out_dir = os.path.join(args.get("out_path"), "component_package",
                                    args.get("part_path"), "innerapis", module, "includes")
    for i in args.get("toolchain_info").keys():
        toolchain_includes_out_dir = os.path.join(args.get("out_path"), "component_package",
                                                  args.get("part_path"), "innerapis", module, i, "includes")
        toolchain_lib_out_dir = os.path.join(args.get("out_path"), "component_package",
                                             args.get("part_path"), "innerapis", module, i, "libs")
        if not os.path.exists(toolchain_includes_out_dir) and os.path.exists(toolchain_lib_out_dir):
            os.makedirs(toolchain_includes_out_dir)
        else:
            continue
        for include in includes:
            part_path = args.get("part_path")
            _sub_include = include.split(f"{part_path}/")[-1]
            split_include = include.split("//")[1]
            real_include_path = os.path.join(args.get("root_path"), split_include)
            if args.get('part_name') == 'libunwind':
                _out_dir = os.path.join(toolchain_includes_out_dir, _sub_include)
                _copy_dir(real_include_path, _out_dir)
                continue
            _copy_dir(real_include_path, toolchain_includes_out_dir)
    if not os.path.exists(includes_out_dir):
        os.makedirs(includes_out_dir)
    for include in includes:
        part_path = args.get("part_path")
        _sub_include = include.split(f"{part_path}/")[-1]
        split_include = include.split("//")[1]
        real_include_path = os.path.join(args.get("root_path"), split_include)
        if args.get('part_name') == 'libunwind':
            _out_dir = os.path.join(includes_out_dir, _sub_include)
            _copy_dir(real_include_path, _out_dir)
            continue
        _copy_dir(real_include_path, includes_out_dir)
    print("_copy_includes has done ")


def _copy_toolchain_lib(file_name, root, _name, lib_out_dir):
    if not file_name.startswith('.') and file_name.startswith(_name):
        if not os.path.exists(lib_out_dir):
            os.makedirs(lib_out_dir)
        file = os.path.join(root, file_name)
        shutil.copy(file, lib_out_dir)


def _toolchain_lib_handler(args, toolchain_path, _name, module, toolchain_name):
    for root, dirs, files in os.walk(toolchain_path):
        for file_name in files:
            lib_out_dir = os.path.join(args.get("out_path"), "component_package",
                                       args.get("part_path"), "innerapis", module, toolchain_name, "libs")
            _copy_toolchain_lib(file_name, root, _name, lib_out_dir)


def _toolchain_static_file_path_mapping(subsystem_name, args, i):
    if subsystem_name == "thirdparty":
        subsystem_name = "third_party"
    toolchain_path = os.path.join(args.get("out_path"), i, 'obj', subsystem_name,
                                  args.get("part_name"))
    return toolchain_path


def _copy_lib(args, json_data, module):
    so_path = ""
    lib_status = False
    subsystem_name = args.get("subsystem_name")
    if json_data.get('type') == 'static_library':
        so_path = _get_static_lib_path(args, json_data)
    else:
        so_path = os.path.join(args.get("out_path"), subsystem_name,
                               args.get("part_name"), json_data.get('out_name'))
    if args.get("toolchain_info").keys():
        for i in args.get("toolchain_info").keys():
            so_type = ''
            toolchain_path = os.path.join(args.get("out_path"), i, subsystem_name,
                                          args.get("part_name"))
            _name = json_data.get('out_name').split('.')[0]
            if json_data.get('type') == 'static_library':
                _name = json_data.get('out_name')
                toolchain_path = _toolchain_static_file_path_mapping(subsystem_name, args, i)
            _toolchain_lib_handler(args, toolchain_path, _name, module, i)
            lib_status = lib_status or True
    if os.path.isfile(so_path):
        lib_out_dir = os.path.join(args.get("out_path"), "component_package",
                                   args.get("part_path"), "innerapis", module, "libs")
        if not os.path.exists(lib_out_dir):
            os.makedirs(lib_out_dir)
        shutil.copy(so_path, lib_out_dir)
        lib_status = lib_status or True
    return lib_status


def _dirs_handler(bundlejson_out):
    dirs = dict()
    dirs['./'] = []
    directory = bundlejson_out
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            dirs['./'].append(filename)
        else:
            dirs[filename] = [f"{filename}/*"]
    delete_list = ['LICENSE', 'README.md', 'README_zh.md', 'README_en.md', 'bundle.json']
    for delete_txt in delete_list:
        if delete_txt in dirs['./']:
            dirs['./'].remove(delete_txt)
    if dirs['./'] == []:
        del dirs['./']
    return dirs


def _copy_bundlejson(args, public_deps_list):
    bundlejson_out = os.path.join(args.get("out_path"), "component_package", args.get("part_path"))
    print("bundlejson_out : ", bundlejson_out)
    if not os.path.exists(bundlejson_out):
        os.makedirs(bundlejson_out)
    bundlejson = os.path.join(args.get("root_path"), args.get("part_path"), "bundle.json")
    dependencies_dict = {}
    for public_deps in public_deps_list:
        _public_dep_part_name = public_deps.split(':')[0]
        if _public_dep_part_name != args.get("part_name"):
            _public_dep = f"@{args.get('organization_name')}/{_public_dep_part_name}"
            dependencies_dict.update({_public_dep: "*"})
    if os.path.isfile(bundlejson):
        with open(bundlejson, 'r') as f:
            bundle_data = json.load(f)
            bundle_data['publishAs'] = 'binary'
            bundle_data.update({'os': args.get('os')})
            bundle_data.update({'buildArch': args.get('buildArch')})
            dirs = _dirs_handler(bundlejson_out)
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
            if args.get('build_type') in [0, 1]:
                bundle_data['version'] += '-snapshot'
            if args.get('organization_name'):
                _name_pattern = r'@(.*.)/'
                bundle_data['name'] = re.sub(_name_pattern, '@' + args.get('organization_name') + '/',
                                             bundle_data['name'])
            if bundle_data.get('scripts'):
                bundle_data.update({'scripts': {}})
            if bundle_data.get('licensePath'):
                del bundle_data['licensePath']
            if bundle_data.get('readmePath'):
                del bundle_data['readmePath']
            bundle_data['dependencies'] = dependencies_dict
            if os.path.isfile(os.path.join(bundlejson_out, "bundle.json")):
                os.remove(os.path.join(bundlejson_out, "bundle.json"))
            with os.fdopen(os.open(os.path.join(bundlejson_out, "bundle.json"), os.O_WRONLY | os.O_CREAT, mode=0o640),
                           "w",
                           encoding='utf-8') as fd:
                json.dump(bundle_data, fd, indent=4, ensure_ascii=False)


def _copy_license(args):
    license_out = os.path.join(args.get("out_path"), "component_package", args.get("part_path"))
    print("license_out : ", license_out)
    if not os.path.exists(license_out):
        os.makedirs(license_out)
    license_file = os.path.join(args.get("root_path"), args.get("part_path"), "LICENSE")
    if os.path.isfile(license_file):
        shutil.copy(license_file, license_out)
    else:
        license_default = os.path.join(args.get("root_path"), "build", "LICENSE")
        shutil.copy(license_default, license_out)
        bundlejson_out = os.path.join(args.get("out_path"), "component_package", args.get("part_path"), 'bundle.json')
        with open(bundlejson_out, 'r') as f:
            bundle_data = json.load(f)
            bundle_data.update({"license": "Apache License 2.0"})
        if os.path.isfile(bundlejson_out):
            os.remove(bundlejson_out)
        with os.fdopen(os.open(bundlejson_out, os.O_WRONLY | os.O_CREAT, mode=0o640), "w",
                       encoding='utf-8') as fd:
            json.dump(bundle_data, fd, indent=4, ensure_ascii=False)


def _copy_readme(args):
    readme_out = os.path.join(args.get("out_path"), "component_package", args.get("part_path"))
    print("readme_out : ", readme_out)
    if not os.path.exists(readme_out):
        os.makedirs(readme_out)
    readme = os.path.join(args.get("root_path"), args.get("part_path"), "README.md")
    readme_zh = os.path.join(args.get("root_path"), args.get("part_path"), "README_zh.md")
    readme_en = os.path.join(args.get("root_path"), args.get("part_path"), "README_en.md")
    readme_out_file = os.path.join(readme_out, "README.md")
    if os.path.isfile(readme):
        shutil.copy(readme, readme_out)
    elif os.path.isfile(readme_zh):
        shutil.copy(readme_zh, readme_out_file)
    elif os.path.isfile(readme_en):
        shutil.copy(readme_en, readme_out_file)
    else:
        try:
            with os.fdopen(os.open(readme_out_file, os.O_WRONLY | os.O_CREAT, mode=0o640), 'w') as fp:
                fp.write('READ.ME')
        except FileExistsError:
            pass


def _generate_import(fp):
    fp.write('import("//build/ohos.gni")\n')


def _generate_configs(fp, module):
    fp.write('\nconfig("' + module + '_configs") {\n')
    fp.write('  visibility = [ ":*" ]\n')
    fp.write('  include_dirs = [\n')
    fp.write('    "includes",\n')
    if module == 'libunwind':
        fp.write('    "includes/libunwind/src",\n')
        fp.write('    "includes/libunwind/include",\n')
        fp.write('    "includes/libunwind/include/tdep-arm",\n')
    if module == 'ability_runtime':
        fp.write('    "includes/context",\n')
        fp.write('    "includes/app",\n')
    fp.write('  ]\n')
    if module == 'libunwind':
        fp.write('  cflags = [\n')
        fp.write("""    "-D_GNU_SOURCE",
    "-DHAVE_CONFIG_H",
    "-DNDEBUG",
    "-DCC_IS_CLANG",
    "-fcommon",
    "-Werror",
    "-Wno-absolute-value",
    "-Wno-header-guard",
    "-Wno-unused-parameter",
    "-Wno-unused-variable",
    "-Wno-int-to-pointer-cast",
    "-Wno-pointer-to-int-cast",
    "-Wno-inline-asm",
    "-Wno-shift-count-overflow",
    "-Wno-tautological-constant-out-of-range-compare",
    "-Wno-unused-function",\n""")
        fp.write('  ]\n')
    fp.write('  }\n')


def _generate_prebuilt_shared_library(fp, lib_type, module):
    if lib_type == 'static_library':
        fp.write('ohos_prebuilt_static_library("' + module + '") {\n')
    elif lib_type == 'executable':
        fp.write('ohos_prebuilt_executable("' + module + '") {\n')
    elif lib_type == 'etc':
        fp.write('ohos_prebuilt_etc("' + module + '") {\n')
    else:
        fp.write('ohos_prebuilt_shared_library("' + module + '") {\n')


def _generate_public_configs(fp, module):
    fp.write(f'  public_configs = [":{module}_configs"]\n')


def _public_deps_special_handler(module):
    if module == 'appexecfwk_core':
        return ["ability_base:want"]
    return []


def _generate_public_deps(fp, module, deps: list, components_json, public_deps_list: list):
    if not deps:
        return public_deps_list
    fp.write('  public_external_deps = [\n')
    for dep in deps:
        public_external_deps = _get_public_external_deps(components_json, dep)
        if len(public_external_deps) > 0:
            fp.write(f"""    "{public_external_deps}",\n""")
            public_deps_list.append(public_external_deps)
    for _public_external_deps in _public_deps_special_handler(module):
        fp.write(f"""    "{_public_external_deps}",\n""")
        public_deps_list.append(_public_external_deps)
    fp.write('  ]\n')

    return public_deps_list


def _generate_other(fp, args, json_data, module):
    so_name = json_data.get('out_name')
    fp.write('  source = "libs/' + so_name + '"\n')
    fp.write('  part_name = "' + args.get("part_name") + '"\n')
    fp.write('  subsystem_name = "' + args.get("subsystem_name") + '"\n')


def _generate_end(fp):
    fp.write('}')


def _generate_build_gn(args, module, json_data, deps: list, components_json, public_deps_list):
    gn_path = os.path.join(args.get("out_path"), "component_package", args.get("part_path"),
                           "innerapis", module, "BUILD.gn")
    fd = os.open(gn_path, os.O_WRONLY | os.O_CREAT, mode=0o640)
    fp = os.fdopen(fd, 'w')
    _generate_import(fp)
    _generate_configs(fp, module)
    _generate_prebuilt_shared_library(fp, json_data.get('type'), module)
    _generate_public_configs(fp, module)
    _list = _generate_public_deps(fp, module, deps, components_json, public_deps_list)
    _generate_other(fp, args, json_data, module)
    _generate_end(fp)
    print("_generate_build_gn has done ")
    fp.close()
    return _list


def _toolchain_gn_modify(gn_path, file_name, toolchain_gn_file):
    if os.path.isfile(gn_path) and file_name:
        with open(gn_path, 'r') as f:
            _gn = f.read()
            pattern = r"libs/(.*.)"
            toolchain_gn = re.sub(pattern, 'libs/' + file_name + '\"', _gn)
        fd = os.open(toolchain_gn_file, os.O_WRONLY | os.O_CREAT, mode=0o640)
        fp = os.fdopen(fd, 'w')
        fp.write(toolchain_gn)
        fp.close()


def _get_toolchain_gn_file(lib_out_dir):
    file_name = ''
    try:
        file_list = os.scandir(lib_out_dir)
    except FileNotFoundError:
        return file_name
    for file in file_list:
        if not file.name.startswith('.') and file.is_file():
            file_name = file.name
    return file_name


def _toolchain_gn_copy(args, module):
    gn_path = os.path.join(args.get("out_path"), "component_package", args.get("part_path"),
                           "innerapis", module, "BUILD.gn")
    for i in args.get("toolchain_info").keys():
        lib_out_dir = os.path.join(args.get("out_path"), "component_package",
                                   args.get("part_path"), "innerapis", module, i, "libs")
        file_name = _get_toolchain_gn_file(lib_out_dir)
        if not file_name:
            continue
        toolchain_gn_file = os.path.join(args.get("out_path"), "component_package",
                                         args.get("part_path"), "innerapis", module, i, "BUILD.gn")
        if not os.path.exists(toolchain_gn_file):
            os.mknod(toolchain_gn_file)
        _toolchain_gn_modify(gn_path, file_name, toolchain_gn_file)


def _parse_module_list(args):
    module_list = []
    publicinfo_path = os.path.join(args.get("out_path"),
                                   args.get("subsystem_name"), args.get("part_name"), "publicinfo")
    print('publicinfo_path', publicinfo_path)
    if os.path.exists(publicinfo_path) is False:
        return module_list
    publicinfo_dir = os.listdir(publicinfo_path)
    for filename in publicinfo_dir:
        if filename.endswith(".json"):
            module_name = filename.split(".json")[0]
            module_list.append(module_name)
            print('filename', filename)
    print('module_list', module_list)
    return module_list


def _lib_special_handler(part_name, module, args):
    if part_name == 'mksh':
        mksh_file_path = os.path.join(args.get('out_path'), 'startup', 'init', 'sh')
        sh_out = os.path.join(args.get("out_path"), "thirdparty", "mksh")
        if os.path.isfile(mksh_file_path):
            shutil.copy(mksh_file_path, sh_out)
    if module == 'blkid':
        blkid_file_path = os.path.join(args.get('out_path'), 'filemanagement', 'storage_service', 'blkid')
        blkid_out = os.path.join(args.get("out_path"), "thirdparty", "e2fsprogs")
        if os.path.isfile(blkid_file_path):
            shutil.copy(blkid_file_path, blkid_out)
    if module == 'grpc_cpp_plugin':
        blkid_file_path = os.path.join(args.get('out_path'), 'clang_x64', 'thirdparty', 'grpc', 'grpc_cpp_plugin')
        blkid_out = os.path.join(args.get("out_path"), "thirdparty", "grpc")
        if os.path.isfile(blkid_file_path):
            shutil.copy(blkid_file_path, blkid_out)


def _generate_component_package(args, components_json):
    part_name = args.get("part_name")
    modules = _parse_module_list(args)
    print('modules', modules)
    if len(modules) == 0:
        return
    is_component_build = False
    _public_deps_list = []
    for module in modules:
        public_deps_list = []
        if _is_innerkit(components_json, args.get("part_name"), module) == False:
            continue
        json_data = _get_json_data(args, module)
        _lib_special_handler(part_name, module, args)
        lib_exists = _copy_lib(args, json_data, module)
        if lib_exists is False:
            continue
        is_component_build = True
        includes = _handle_includes_data(json_data)
        deps = _handle_deps_data(json_data)
        _copy_includes(args, module, includes)
        _list = _generate_build_gn(args, module, json_data, deps, components_json, public_deps_list)
        if _list:
            _public_deps_list.extend(_list)
        _toolchain_gn_copy(args, module)
    if is_component_build:
        _copy_bundlejson(args, _public_deps_list)
        _copy_license(args)
        _copy_readme(args)
        if args.get("build_type") in [0, 1]:
            _hpm_status = _hpm_pack(args)
            if _hpm_status:
                _copy_hpm_pack(args)


def _get_part_subsystem(components_json: dict):
    jsondata = dict()
    try:
        for component, v in components_json.items():
            jsondata[component] = v.get('subsystem')
    except Exception as e:
        print('--_get_part_subsystem parse json error--')
    return jsondata


def _get_parts_path_info(components_json):
    jsondata = dict()
    try:
        for component, v in components_json.items():
            jsondata[component] = v.get('path')
    except Exception as e:
        print('--_get_part_subsystem parse json error--')
    return jsondata


def _get_toolchain_info(root_path):
    jsondata = ""
    json_path = os.path.join(root_path + "/build/indep_configs/variants/common/toolchain.json")
    with os.fdopen(os.open(json_path, os.O_RDWR | os.O_CREAT, stat.S_IWUSR | stat.S_IRUSR),
            'r', encoding='utf-8') as f:
        try:
            jsondata = json.load(f)
        except Exception as e:
            print('--_get_toolchain_info parse json error--')
    return jsondata


def _get_parts_path(json_data, part_name):
    parts_path = None
    if json_data.get(part_name) is not None:
        parts_path = json_data[part_name]
    return parts_path


def _hpm_pack(args):
    part_path = os.path.join(args.get("out_path"), "component_package", args.get("part_path"))
    cmd = ['hpm', 'pack']
    try:
        subprocess.run(cmd, shell=False, cwd=part_path)
    except Exception as e:
        print("{} pack fail".format(args.get("part_name")))
        return 0
    print("{} pack succ".format(args.get("part_name")))
    return 1


def _copy_hpm_pack(args):
    hpm_packages_path = args.get('hpm_packages_path')
    part_path = os.path.join(args.get("out_path"), "component_package", args.get("part_path"))
    dirs = os.listdir(part_path)
    tgz_file_name = ''
    for file in dirs:
        if file.endswith(".tgz"):
            tgz_file_name = file
    tgz_file_out = os.path.join(part_path, tgz_file_name)
    if tgz_file_name:
        shutil.copy(tgz_file_out, hpm_packages_path)


def _make_hpm_packages_dir(root_path):
    _out_path = os.path.join(root_path, 'out')
    hpm_packages_path = os.path.join(_out_path, 'hpm_packages')
    os.makedirs(hpm_packages_path, exist_ok=True)
    return hpm_packages_path


def _del_exist_component_package(out_path):
    _component_package_path = os.path.join(out_path, 'component_package')
    if os.path.isdir(_component_package_path):
        try:
            print('del dir component_package start..')
            shutil.rmtree(_component_package_path)
            print('del dir component_package end..')
        except Exception as e:
            print('del dir component_package FAILED')


def _get_component_check(local_test) -> list:
    check_list = []
    if local_test == 0:
        contents = urllib.request.urlopen(
            "https://ci.openharmony.cn/api/daily_build/component/check/list").read().decode(
            encoding="utf-8")
        _check_json = json.loads(contents)
        try:
            check_list.extend(_check_json["data"]["dep_list"])
            check_list.extend(_check_json["data"]["indep_list"])
        except Exception as e:
            print("Call the component check API something wrong, plz check the API return..")
    check_list = list(set(check_list))
    check_list = sorted(check_list)
    return check_list


def _package_interface(args, parts_path_info, part_name, subsystem_name, components_json):
    part_path = _get_parts_path(parts_path_info, part_name)
    if part_path is None:
        return
    args.update({"subsystem_name": subsystem_name, "part_name": part_name,
                 "part_path": part_path})
    _generate_component_package(args, components_json)


def generate_component_package(out_path, root_path, components_list=None, build_type=0, organization_name='ohos',
                               os_arg='linux', build_arch_arg='x86', local_test=0):
    """

    Args:
        out_path: output path of code default : out/rk3568
        root_path: root path of code default : oh/
        components_list: list of all components that need to be built
        build_type: build type
            0: default pack,do not change organization_name
            1: pack ,change organization_name
            2: do not pack,do not change organization_name
        organization_name: default ohos, if diff then change
        os_arg: default : linux
        build_arch_arg:  default : x86
        local_test: 1 to open local test , 0 to close , 2 to pack init and init deps
    Returns:

    """
    start_time = time.time()
    _check_list = _get_component_check(local_test)
    if local_test == 1 and not components_list:
        components_list = []
    elif local_test == 1 and components_list:
        components_list = [component for component in components_list.split(",")]
    elif local_test == 2:
        components_list = ["init", "appspawn", "safwk", "c_utils",
                           "napi", "ipc", "config_policy", "hilog", "hilog_lite", "samgr", "access_token", "common",
                           "dsoftbus", "hvb", "hisysevent", "hiprofiler", "bounds_checking_function",
                           "bundle_framework", "selinux", "selinux_adapter", "storage_service",
                           "mbedtls", "zlib", "libuv", "cJSON", "mksh", "libunwind", "toybox",
                           "bounds_checking_function",
                           "selinux", "libunwind", "mbedtls", "zlib", "cJSON", "mksh", "toybox", "config_policy",
                           "e2fsprogs", "f2fs-tools", "selinux_adapter", "storage_service"
                           ]
    else:
        components_list = [component for component in components_list.split(",") if component in _check_list]
        if not components_list:
            sys.exit("stop for no target to pack..")
    print('components_list', components_list)
    components_json = _get_components_json(out_path)
    part_subsystem = _get_part_subsystem(components_json)
    parts_path_info = _get_parts_path_info(components_json)
    hpm_packages_path = _make_hpm_packages_dir(root_path)
    toolchain_info = _get_toolchain_info(root_path)
    # del component_package
    _del_exist_component_package(out_path)
    args = {"out_path": out_path, "root_path": root_path,
            "os": os_arg, "buildArch": build_arch_arg, "hpm_packages_path": hpm_packages_path,
            "build_type": build_type, "organization_name": organization_name,
            "toolchain_info": toolchain_info
            }
    for key, value in part_subsystem.items():
        part_name = key
        subsystem_name = value
        # components_list is NONE or part name in components_list
        if not components_list:
            _package_interface(args, parts_path_info, part_name, subsystem_name, components_json)
        for component in components_list:
            if part_name == component:
                _package_interface(args, parts_path_info, part_name, subsystem_name, components_json)

    end_time = time.time()
    run_time = end_time - start_time
    print("generate_component_package out_path", out_path)
    print(f"Generating binary product package takes time：{run_time}")


def main():
    py_args = _get_args()
    generate_component_package(py_args.out_path,
                               py_args.root_path,
                               components_list=py_args.components_list,
                               build_type=py_args.build_type,
                               organization_name=py_args.organization_name,
                               os_arg=py_args.os_arg,
                               build_arch_arg=py_args.build_arch,
                               local_test=py_args.local_test)


if __name__ == '__main__':
    main()
