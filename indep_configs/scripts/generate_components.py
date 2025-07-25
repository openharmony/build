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

import argparse
import json
import os
import shutil
import stat
import utils
import subprocess


def _get_args():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "-sp",
        "--source_code_path",
        default=r".",
        type=str,
        help="Path of source code",
    )
    parser.add_argument(
        "-hp",
        "--hpmcache_path",
        default=r".",
        type=str,
        help="Path of .hpmcache",
    )
    parser.add_argument(
        "-v",
        "--variants",
        default=r".",
        type=str,
        help="variants of build target",
    )
    parser.add_argument(
        "-rp",
        "--root_path",
        default=r".",
        type=str,
        help="Path of root",
    )
    parser.add_argument(
        "-t", "--test",
        default=1, type=int,
        help="whether the target contains test type. default 0 , choices: 0 or 1 2",
    )
    parser.add_argument(
        "-out", 
        "--out_dir",
        default="src", 
        type=str,
        help="the independent build out storage dir. default src , choices: src src_test or test",
    )
    args = parser.parse_args()
    return args


def _get_dependence_json(_path) -> dict:
    dependences_path = os.path.join(_path, 'dependences.json')
    _json = utils.get_json(dependences_path)
    return _json


def _get_bundle_path(hpm_cache_path, dependences_json, part_name):
    bundle_path = (hpm_cache_path +
                   dependences_json[part_name]['installPath'] + os.sep + 'bundle.json')
    return bundle_path


def _get_src_bundle_path(source_code_path):
    bundle_paths = list()
    for root, dirs, files in os.walk(source_code_path):
        for file in files:
            if file == "bundle.json":
                bundle_paths.append(os.path.join(root, file))
    return bundle_paths


def _symlink_src2dest(src_dir, dest_dir):
    if os.path.exists(dest_dir) and os.path.islink(dest_dir):
        os.unlink(dest_dir)
    if os.path.exists(dest_dir) and dest_dir != src_dir:
        if os.path.isdir(dest_dir):
            shutil.rmtree(dest_dir)
        else:
            os.remove(dest_dir)
    os.symlink(src_dir, dest_dir)


def _symlink_binarys(hpm_cache_path, bundle_json, dependences_json, part_name):
    path = bundle_json["segment"]["destPath"]
    link_path = os.path.join("binarys", path)
    if not os.path.isdir(link_path):
        try:
            os.remove(link_path)
        except FileNotFoundError:
            pass
        os.makedirs(link_path, exist_ok=True)
    real_path = hpm_cache_path + dependences_json[part_name]['installPath']
    _symlink_src2dest(real_path, link_path)


def _get_target_cpu(code_path, variants):
    target_cpu_str = ""
    config_path = os.path.join(code_path, "binarys", "variants", "variants_" + variants, "config", "build_config.json")
    target_cpu = utils.get_json(config_path).get("target_cpu")
    if target_cpu == "arm":
        target_cpu_str = "arm"
    elif target_cpu == "arm64":
        target_cpu_str = "aarch64"
    return target_cpu_str


def _link_kernel_binarys(variants, hpm_cache_path, dependences_json, target_cpu):
    target_path = target_cpu + "-linux-ohos"
    musl_real_path = hpm_cache_path + dependences_json["musl"]['installPath']
    musl_include_link_path = os.path.join("out", variants, "obj/binarys/third_party/musl/usr/include", target_path)
    musl_lib_link_path = os.path.join("out", variants, "obj/binarys/third_party/musl/usr/lib", target_path)
    os.makedirs(musl_include_link_path, exist_ok=True)
    os.makedirs(musl_lib_link_path, exist_ok=True)

    _symlink_src2dest(os.path.join(musl_real_path, 'innerapis', 'includes'), musl_include_link_path)
    _symlink_src2dest(os.path.join(musl_real_path, 'innerapis', 'libs'), musl_lib_link_path)
    
    kernel_real_path = hpm_cache_path + dependences_json["linux"]['installPath']    
    kernel_link_path = os.path.join("kernel", "linux")
    if not os.path.exists(kernel_link_path):
        os.makedirs(kernel_link_path)
        _symlink_src2dest(os.path.join(kernel_real_path, "innerapis"), kernel_link_path)


def is_directory_empty(path):
    return len([f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]) == 0


def _copy_test_binarys(test_check, variants, hpm_cache_path, dependences_json):
    if test_check != 0:
        googletest_real_path = hpm_cache_path + dependences_json["googletest"]['installPath']
        googletest_link_path = os.path.join("out", variants, "obj/binarys/third_party/googletest")
        os.makedirs(googletest_link_path, exist_ok=True)
        if is_directory_empty(googletest_link_path):
            shutil.copytree(os.path.join(googletest_real_path, 'innerapis'), 
                            os.path.join(googletest_link_path, 'innerapis'))
        else:
            shutil.rmtree(googletest_link_path, True)
            os.makedirs(googletest_link_path, exist_ok=True)
            shutil.copytree(os.path.join(googletest_real_path, 'innerapis'), 
                            os.path.join(googletest_link_path, 'innerapis'))


def _gen_components_info(components_json, bundle_json, part_name, src_build_name_list, _part_toolchain_map_dict):
    subsystem = bundle_json["component"]["subsystem"]
    path = bundle_json["segment"]["destPath"]
    try:
        component = bundle_json["component"]["build"]["inner_kits"]
    except KeyError:
        if not bundle_json["component"]["build"]:
            bundle_json["component"]["build"] = {}
        if "inner_api" not in bundle_json["component"]["build"].keys():
            bundle_json["component"]["build"]["inner_api"] = []
        component = bundle_json["component"]["build"]["inner_api"]
    innerapi_value_list = list()
    for i in component:
        innerapi_name = i["name"].split(':')[-1]
        if part_name == 'musl':
            innerapi_label = "{}:{}".format(os.path.join("//binarys", path), innerapi_name)
        elif part_name in src_build_name_list:
            innerapi_label = i['name']
        else:
            innerapi_label = "{}:{}".format(os.path.join("//binarys", path, "innerapis", innerapi_name), innerapi_name)
        innerapi_value_list.append({"name": innerapi_name, "label": innerapi_label})
        if innerapi_name in _part_toolchain_map_dict.keys() and part_name not in src_build_name_list:
            _name = innerapi_name
            innerapi_name = f"{innerapi_name}({_part_toolchain_map_dict[_name]['toolchain_value']})"
            innerapi_label = "{}:{}".format(os.path.join("//binarys", path, "innerapis",
                                          _name,
                                          _part_toolchain_map_dict[_name]['toolchain_key']), innerapi_name)
            innerapi_value_list.append({"name": innerapi_name, "label": innerapi_label})
    if part_name == 'cjson':
        part_name = 'cJSON'
    if part_name == 'freebsd':
        part_name = 'FreeBSD'
    spe_component_names = ['astc_encoder', 'llvm_project', 'alsa_lib', 'alsa_utils', 'abseil_cpp', 'cups_filters',
                           'libnfc_nci', 'vulkan_loader', 'libjpeg_turbo', 'opencl_headers', 'f2fs_tools', 'noto_cjk',
                           'fsverity_utils', 'vk_gl_cts',
                           'spirv_tools', 'spirv_headers', 'vulkan_headers', 'u_boot', 'weex_loader', 'ntfs_3g',
                           'css_what']
    if part_name in spe_component_names:
        part_name = part_name.replace('_', '-')
    one_component_dict = {part_name: {
        "innerapis": innerapi_value_list,
        "path": path,
        "subsystem": subsystem
    }}
    components_json.update(one_component_dict)

    return components_json


def _get_src_part_name(src_bundle_paths):
    _name = ''
    _path = ''
    for src_bundle_path in src_bundle_paths:
        src_bundle_json = utils.get_json(src_bundle_path)
        part_name = ""
        try:
            part_name = src_bundle_json['component']['name']
        except KeyError:
            print(f'--get bundle json component name error--')
        if part_name.endswith('_lite'):
            pass
        else:
            _name = part_name
            _path = src_bundle_path
    return [_name, _path]


def _binarys_permissions_handler():
    binarys_path = "binarys"
    cmd = ["chmod", "755", "-R", binarys_path]
    subprocess.Popen(cmd)


def _components_info_handler(part_name_list, source_code_path: str, hpm_cache_path, root_path, dependences_json,
                             _part_toolchain_map_dict):
    source_code_path_list = source_code_path.split(",")
    components_json = dict()
    src_build_name_list = ['build_framework']

    # 获取源代码路径和组件名称的映射
    src_bundle_path_dict = {
        _get_src_part_name(_get_src_bundle_path(src_path))[0]: _get_src_part_name(_get_src_bundle_path(src_path))[1]
        for src_path in source_code_path_list
    }
    # 更新构建名称列表并生成组件信息
    src_build_name_list.extend(src_bundle_path_dict.keys())
    for src_part_name, src_bundle_path in src_bundle_path_dict.items():
        components_json = _gen_components_info(components_json, utils.get_json(src_bundle_path), src_part_name,
                                               src_build_name_list, _part_toolchain_map_dict)

    # 处理构建框架
    build_framework_bundle_path = os.path.join(root_path, "build", "bundle.json")
    components_json = _gen_components_info(components_json, utils.get_json(build_framework_bundle_path),
                                           "build_framework", src_build_name_list, _part_toolchain_map_dict)

    # 处理其他组件
    for part_name in part_name_list:
        if part_name and part_name not in src_bundle_path_dict:
            bundle_path = _get_bundle_path(hpm_cache_path, dependences_json, part_name)
            bundle_json = utils.get_json(bundle_path)
            _symlink_binarys(hpm_cache_path, bundle_json, dependences_json, part_name)
            if part_name == 'developer_test':
                continue
            components_json = _gen_components_info(components_json, bundle_json, part_name, src_build_name_list,
                                                   _part_toolchain_map_dict)

    return components_json


def _out_components_json(components_json, output_path):
    file_name = os.path.join(output_path, "components.json")
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    modes = stat.S_IWUSR | stat.S_IRUSR
    with os.fdopen(os.open(file_name, flags, modes), 'w') as f:
        json.dump(components_json, f, indent=4)


def _generate_platforms_list(output_path):
    platforms_list_gni_file = os.path.join(output_path, "platforms_list.gni")
    platforms_list = ['phone']
    platforms_list_strings = ' "," '.join(platforms_list)
    gni_file_content = [f'target_platform_list = [ "{platforms_list_strings}" ]',
                        f'kits_platform_list  = [ "{platforms_list_strings}" ]']
    flags = os.O_WRONLY | os.O_CREAT
    modes = stat.S_IWUSR | stat.S_IRUSR
    with os.fdopen(os.open(platforms_list_gni_file, flags, modes), 'w') as f:
        f.write('\n'.join(gni_file_content))


def _get_toolchain_json(_path):
    toolchain_json = os.path.join(_path, 'build', 'indep_configs', 'variants', 'common', 'toolchain.json')
    _json = utils.get_json(toolchain_json)
    return _json


def _get_all_have_toolchain_component(toolchain_json, hpm_cache_path):
    _toolchain_list = toolchain_json.keys()
    binarys_path = os.path.join(hpm_cache_path, 'binarys')
    _part_toolchain_map_dict = dict()
    for toolchain in _toolchain_list:
        for root, dirs, files in os.walk(binarys_path, topdown=False, followlinks=True):
            if toolchain in dirs:
                _part_name = os.path.basename(root)
                _part_toolchain_map_dict.update({
                    _part_name: {
                        'toolchain_key': toolchain,
                        'toolchain_value': toolchain_json[toolchain]
                    }
                })
    return _part_toolchain_map_dict


def main():
    args = _get_args()
    source_code_path = args.source_code_path
    hpm_cache_path = args.hpmcache_path
    variants = args.variants
    root_path = args.root_path
    test_check = args.test
    out_dir = args.out_dir
    project_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    output_part_path = os.path.join(project_path, 'out', variants, out_dir, 'build_configs', 'parts_info')
    output_config_path = os.path.join(project_path, 'out', variants, out_dir, 'build_configs')
    dependences_json = _get_dependence_json(hpm_cache_path)
    toolchain_json = _get_toolchain_json(root_path)
    part_name_list = dependences_json.keys()

    _part_toolchain_map_dict = _get_all_have_toolchain_component(toolchain_json, hpm_cache_path)
    components_json = _components_info_handler(part_name_list, source_code_path,
                                               hpm_cache_path, root_path, dependences_json, _part_toolchain_map_dict)
    _binarys_permissions_handler()
    _out_components_json(components_json, output_part_path)
    _generate_platforms_list(output_config_path)
    _link_kernel_binarys(variants + os.sep + out_dir, hpm_cache_path, dependences_json, _get_target_cpu(root_path, variants))
    _copy_test_binarys(test_check, variants + os.sep + out_dir, hpm_cache_path, dependences_json)


if __name__ == '__main__':
    main()
