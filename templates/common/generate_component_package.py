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
    parser.add_argument("-origin", "--build-origin", default="", type=str,
                        help="Origin marker for HPM package", )
    args = parser.parse_args()
    return args


def create_directories(paths):
    for path in paths:
        os.makedirs(path, exist_ok=True)


def copy_files(src_dst_pairs):
    for src, dst in src_dst_pairs:
        shutil.copy2(src, dst)


def generate_common_configs():
    return """import("//build/ohos.gni")


config("musl_common_configs") {
  visibility = [ ":*" ]
  include_dirs = [
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include",
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include/c++/v1",
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include/c++/v1/__algorithm",
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include/c++/v1/__bit",
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include/c++/v1/__charconv",
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include/c++/v1/__chrono",
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include/c++/v1/__compare",
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include/c++/v1/__concepts",
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include/c++/v1/__debug_utils",
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include/c++/v1/__concepts",
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include/c++/v1/__filesystem",
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include/c++/v1/__format",
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include/c++/v1/__functional",
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include/c++/v1/__fwd",
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include/c++/v1/__ios",
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include/c++/v1/__iterator",
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include/c++/v1/__memory",
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include/c++/v1/__numeric",
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include/c++/v1/__random",
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include/c++/v1/__ranges",
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include/c++/v1/__string",
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include/c++/v1/__support",
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include/c++/v1/__thread",
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include/c++/v1/__type_traits",
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include/c++/v1/__utility",
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include/c++/v1/__variant",
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include/c++/v1/experimental",
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include/c++/v1/ext",
    "//prebuilts/clang/ohos/linux-x86_64/15.0.4/llvm/include/arm-linux-ohos/c++/v1",
  ]

   cflags_c = [
      "-Wno-error=bitwise-op-parentheses",
      "-Wno-error=shift-op-parentheses",
    ]
}
    """


def generate_soft_libc_musl_shared_configs():
    return """
config("soft_libc_musl_shared_configs") {
  visibility = [ ":*" ]
  include_dirs = [
    "innerapis/includes",
  ]
}

ohos_prebuilt_shared_library("soft_libc_musl_shared") {
  public_configs = [":soft_libc_musl_shared_configs",":musl_common_configs"]
  public_external_deps = [
  ]
  source = "innerapis/libs/libc.so"
  part_name = "musl"
  subsystem_name = "thirdparty"
}
    """


def generate_soft_libcrypt_configs():
    return """
config("soft_libcrypt_configs") {
  visibility = [ ":*" ]
  include_dirs = [
    "innerapis/includes",
  ]
}

ohos_prebuilt_static_library("soft_libcrypt") {
  public_configs = [":soft_libcrypt_configs",":musl_common_configs"]
  public_external_deps = [
  ]
  source = "innerapis/libs/libcrypt.a"
  part_name = "musl"
  subsystem_name = "thirdparty"
} 
    """


def generate_soft_libdl_configs():
    return """
config("soft_libdl_configs") {
  visibility = [ ":*" ]
  include_dirs = [
    "innerapis/includes",
  ]
}

ohos_prebuilt_static_library("soft_libdl") {
  public_configs = [":soft_libdl_configs",":musl_common_configs"]
  public_external_deps = [
  ]
  source = "innerapis/libs/libdl.a"
  part_name = "musl"
  subsystem_name = "thirdparty"
}       
    """


def generate_soft_libm_configs():
    return """
config("soft_libm_configs") {
  visibility = [ ":*" ]
  include_dirs = [
    "innerapis/includes",
  ]
}

ohos_prebuilt_static_library("soft_libm") {
  public_configs = [":soft_libm_configs",":musl_common_configs"]
  public_external_deps = [
  ]
  source = "innerapis/libs/libm.a"
  part_name = "musl"
  subsystem_name = "thirdparty"
}        
    """


def generate_soft_libpthread_configs():
    return """
config("soft_libpthread_configs") {
  visibility = [ ":*" ]
  include_dirs = [
    "innerapis/includes",
  ]
}

ohos_prebuilt_static_library("soft_libpthread") {
  public_configs = [":soft_libpthread_configs",":musl_common_configs"]
  public_external_deps = [
  ]
  source = "innerapis/libs/libpthread.a"
  part_name = "musl"
  subsystem_name = "thirdparty"
}       
    """


def generate_soft_libresolv_configs():
    return """
config("soft_libresolv_configs") {
  visibility = [ ":*" ]
  include_dirs = [
    "innerapis/includes",
  ]
}

ohos_prebuilt_static_library("soft_libresolv") {
  public_configs = [":soft_libresolv_configs",":musl_common_configs"]
  public_external_deps = [
  ]
  source = "innerapis/libs/libresolv.a"
  part_name = "musl"
  subsystem_name = "thirdparty"
}
    """


def generate_soft_librt_configs():
    return """
config("soft_librt_configs") {
  visibility = [ ":*" ]
  include_dirs = [
    "innerapis/includes",
  ]
}

ohos_prebuilt_static_library("soft_librt") {
  public_configs = [":soft_librt_configs",":musl_common_configs"]
  public_external_deps = [
  ]
  source = "innerapis/libs/librt.a"
  part_name = "musl"
  subsystem_name = "thirdparty"
}
    """


def generate_soft_libutil_configs():
    return """
config("soft_libutil_configs") {
  visibility = [ ":*" ]
  include_dirs = [
    "innerapis/includes",
  ]
}

ohos_prebuilt_static_library("soft_libutil") {
  public_configs = [":soft_libutil_configs",":musl_common_configs"]
  public_external_deps = [
  ]
  source = "innerapis/libs/libutil.a"
  part_name = "musl"
  subsystem_name = "thirdparty"
}
    """


def generate_soft_libxnet_configs():
    return """
config("soft_libxnet_configs") {
  visibility = [ ":*" ]
  include_dirs = [
    "innerapis/includes",
  ]
}

ohos_prebuilt_static_library("soft_libxnet") {
  public_configs = [":soft_libxnet_configs",":musl_common_configs"]
  public_external_deps = [
  ]
  source = "innerapis/libs/libxnet.a"
  part_name = "musl"
  subsystem_name = "thirdparty"
}
    """


def generate_group_copy_libs_block():
    return """
group("copy_libs") {
    lib_files = [
      "libc.a",
      "libc.so",
      "libcrypt.a",
      "libdl.a",
      "libm.a",
      "libpthread.a",
      "libresolv.a",
      "librt.a",
      "libutil.a",
      "libxnet.a",
      "crtn.o",
      "crti.o",
      "crt1.o",
      "rcrt1.o",
      "Scrt1.o",
    ]
    sources = []
    outputs = []
    deps = []
    foreach(file, lib_files) {
      copy("copy_${file}") {
        sources += [ "innerapis/libs/${file}" ]
        outputs += [ "${target_out_dir}/usr/lib/arm-linux-ohos/${file}" ]
      }
      deps += [ ":copy_${file}" ]
    }
}
group("soft_shared_libs") {
  public_configs = [":musl_common_configs", ":soft_libxnet_configs"]
  deps = [
    ":soft_libc_musl_shared",
    ":soft_libcrypt",
    ":soft_libdl",
    ":soft_libm",
    ":soft_libpthread",
    ":soft_libresolv",
    ":soft_librt",
    ":soft_libutil",
    ":soft_libxnet",
  ]
}
    """


def generate_group_musl_headers_block():
    return """
group("musl_headers") {
  public_configs = [
    ":musl_common_configs",
    ":soft_libxnet_configs",
  ]
}
    """


def generate_gn_file_content(part_data):
    gn_content = []
    gn_content.append(generate_common_configs())
    gn_content.append(generate_soft_libc_musl_shared_configs())
    gn_content.append(generate_soft_libcrypt_configs())
    gn_content.append(generate_soft_libdl_configs())
    gn_content.append(generate_soft_libm_configs())
    gn_content.append(generate_soft_libpthread_configs())
    gn_content.append(generate_soft_libresolv_configs())
    gn_content.append(generate_soft_librt_configs())
    gn_content.append(generate_soft_libutil_configs())
    gn_content.append(generate_soft_libxnet_configs())
    gn_content.append(generate_group_copy_libs_block())
    gn_content.append(generate_group_musl_headers_block())
    return '\n'.join(gn_content)


def write_gn_file(gn_path, content):
    with open(gn_path, 'w') as gn_file:
        gn_file.write(content)


def copy_musl_libs_includes(musl_obj_path, innerapi_target_path):
    for folder_name in ['include', 'lib']:
        src_folder_path = os.path.join(musl_obj_path, folder_name, 'arm-linux-ohos')
        dst_folder_path = os.path.join(innerapi_target_path, folder_name + 's')
        dst_folder_path_1 = os.path.join(innerapi_target_path, 'musl_headers', folder_name + 's')
        dst_folder_path_2 = os.path.join(innerapi_target_path, 'soft_libc_musl_static', folder_name + 's')
        dst_folder_path_3 = os.path.join(innerapi_target_path, 'soft_shared_libs', folder_name + 's')
        if os.path.exists(src_folder_path):
            shutil.copytree(src_folder_path, dst_folder_path, dirs_exist_ok=True)
            shutil.copytree(src_folder_path, dst_folder_path_1, dirs_exist_ok=True)
            shutil.copytree(src_folder_path, dst_folder_path_2, dirs_exist_ok=True)
            shutil.copytree(src_folder_path, dst_folder_path_3, dirs_exist_ok=True)


def write_musl_bundle(musl_bundle_path):
    # 向musl的bundle.json文件里写入下面的接口
    additional_innerkits = [{"name": "//third_party/musl:soft_shared_libs"}, 
                            {"name": "//third_party/musl:musl_headers"}]
    with open(musl_bundle_path, "r") as file:
        musl_bundle_content = json.load(file)
    musl_innerkits = musl_bundle_content["component"]["build"]["inner_kits"]
    musl_innerkits.extend(additional_innerkits)
    with open(musl_bundle_path, "w", encoding='utf-8') as file:
        json.dump(musl_bundle_content, file, ensure_ascii=False, indent=2) 


def process_musl(part_data, parts_path_info, part_name, subsystem_name, components_json):
    musl_obj_path = os.path.join(part_data.get('out_path'), 'obj', 'third_party', 'musl', 'usr')
    musl_dst_path = os.path.join(part_data.get('out_path'), 'component_package', 'third_party', 'musl')
    musl_src_path = os.path.join(part_data.get('root_path'), 'third_party', 'musl')
    create_directories([musl_dst_path])

    # Copy necessary files to the musl destination path
    files_to_copy = [
        'configure',
        'dynamic.list',
        'libc.map.txt',
        'musl_config.gni'
    ]
    copy_files([(os.path.join(musl_src_path, file_name), os.path.join(musl_dst_path, file_name)) for file_name in
                files_to_copy])

    # Generate and write the GN file
    gn_path = os.path.join(musl_dst_path, 'BUILD.gn')
    gn_content = generate_gn_file_content(part_data)
    write_gn_file(gn_path, gn_content)
    innerapi_target_path = os.path.join(musl_dst_path, 'innerapis')
    copy_musl_libs_includes(musl_obj_path, innerapi_target_path)
    modules = _parse_module_list(part_data)
    print('modules', modules)
    if len(modules) == 0:
        return
    _public_deps_list = []
    # ... Additional logic for processing modules, copying docs, and finishing the component build ...
    _copy_required_docs(part_data, _public_deps_list)
    musl_bundle_path = os.path.join(musl_dst_path, "bundle.json")
    write_musl_bundle(musl_bundle_path)
    _finish_component_build(part_data)


def _create_bundle_json(bundle_path, bundle_content):
    bundle = {}
    with open(bundle_path, "w", encoding="utf-8") as f1:
        json.dump(bundle_content, f1, indent=2)


def _generate_rust_bundle_content():
    bundle_content = {
        "name": "@ohos/rust",
        "description": "third party rust tools, provide multiply functions about compiler",
        "version": "3.1.0-snapshot",
        "license": "Apache License 2.0",
        "publishAs": "binary",
        "segment": {"destPath": "third_party/rust/crates"},
        "dirs": {"./": ["*"]},
        "scripts": {},
        "component": {
            "name": "rust",
            "subsystem": "thirdparty",
            "syscap": [],
            "features": [],
            "adapted_system_type": ["standard"],
            "rom": "",
            "ram": "",
            "hisysevent_config": [],
            "deps": {
                "components": [],
                "third_party": []
            },
            "build": {
                "sub_component": [],
                "inner_api": [],
                "test": []
            }
        },
        "os": "linux",
        "buildArch": "x86"
    }
    return bundle_content


def process_rust(part_data, parts_path_info, part_name, subsystem_name, components_json):
    rust_src_path = os.path.join(part_data.get('root_path'), 'third_party', 'rust', 'crates')
    dst_path = os.path.join(part_data.get("out_path"), "component_package", part_data.get("part_path"))
    copy_directory_contents(rust_src_path, dst_path)

    gn_path = os.path.join(dst_path, "bundle.json")
    bundle_content = _generate_rust_bundle_content()
    _create_bundle_json(gn_path, bundle_content)

    _copy_license(part_data)
    _copy_readme(part_data)


def copy_directory_contents(src_path, dst_path):
    if not os.path.exists(dst_path):
        os.makedirs(dst_path)
    for item in os.listdir(src_path):
        src = os.path.join(src_path, item)
        dst = os.path.join(dst_path, item)
        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        elif os.path.isfile(src):
            shutil.copy2(src, dst)


def generate_developer_test_bundle_base_info():
    return {
        "name": "@ohos/developer_test",
        "description": "developer_test",
        "version": "3.1.0-snapshot",
        "license": "Apache License 2.0",
        "publishAs": "binary",
        "segment": {"destPath": "test/testfwk/developer_test"},
        "repository": "",
        "dirs": {"./": ["*"]},
        "scripts": {},
        "os": "linux",
        "buildArch": "x86"
    }


def generate_developer_test_component_info():
    return {
        "name": "developer_test",
        "subsystem": "testfwk",
        "syscap": [],
        "features": [],
        "adapted_system_type": ["mini", "small", "standard"],
        "rom": "0KB",
        "ram": "0KB",
        "deps": {}
    }


def generate_developer_test_build_info():
    return {
        "sub_component": [
            "//test/testfwk/developer_test/examples/app_info:app_info",
            "//test/testfwk/developer_test/examples/detector:detector",
            "//test/testfwk/developer_test/examples/calculator:calculator",
            "//test/testfwk/developer_test/examples/calculator:calculator_static"
        ],
        "inner_kits": [
            {
                "name": "//test/testfwk/developer_test/aw/cxx/distributed:distributedtest_lib",
                "header": {
                    "header_base": [
                        "//test/testfwk/developer_test/aw/cxx/distributed/utils",
                        "//test/testfwk/developer_test/aw/cxx/distributed"
                    ],
                    "header_files": [
                        "csv_transform_xml.h",
                        "distributed.h",
                        "distributed_agent.h",
                        "distributed_cfg.h",
                        "distributed_major.h"
                    ]
                }
            },
            {
                "name": "//test/testfwk/developer_test/aw/cxx/hwext:performance_test_static",
                "header": {
                    "header_base": "//test/testfwk/developer_test/aw/cxx/hwext",
                    "header_files": "perf.h"
                }
            }
        ],
        "test": [
            "//test/testfwk/developer_test/examples/app_info/test:unittest",
            "//test/testfwk/developer_test/examples/calculator/test:unittest",
            "//test/testfwk/developer_test/examples/calculator/test:fuzztest",
            "//test/testfwk/developer_test/examples/calculator/test:benchmarktest",
            "//test/testfwk/developer_test/examples/detector/test:unittest",
            "//test/testfwk/developer_test/examples/sleep/test:performance",
            "//test/testfwk/developer_test/examples/distributedb/test:distributedtest",
            "//test/testfwk/developer_test/examples/stagetest/actsbundlemanagerstagetest:unittest"
        ]
    }


def _generate_developer_test_bundle_content():
    bundle_content = generate_developer_test_bundle_base_info()
    component_info = generate_developer_test_component_info()
    build_info = generate_developer_test_build_info()

    bundle_content["component"] = component_info
    component_info["build"] = build_info

    return bundle_content


def process_developer_test(part_data, parts_path_info, part_name, subsystem_name, components_json):
    developer_test_src_path = os.path.join(part_data.get('root_path'), 'test', 'testfwk', 'developer_test')
    dst_path = os.path.join(part_data.get("out_path"), "component_package", part_data.get("part_path"))

    copy_directory_contents(developer_test_src_path, dst_path)

    gn_path = os.path.join(dst_path, "bundle.json")

    bundle_content = _generate_developer_test_bundle_content()
    _create_bundle_json(gn_path, bundle_content)

    _copy_license(part_data)
    _copy_readme(part_data)
    _finish_component_build(part_data)


def process_skia(part_data, parts_path_info, part_name, subsystem_name, components_json):
    skia_piex_path = os.path.join(part_data.get('root_path'), 'third_party', 'skia', 'third_party', 'externals', 'piex')
    skia_libjpeg_path = os.path.join(part_data.get('root_path'), 'third_party', 'skia', 'third_party', 'externals', 'libjpeg-turbo')
    skia_component_piex_path = os.path.join(part_data.get("out_path"), "component_package", part_data.get("part_path"), 'innerapis', 'piex', 'includes')
    skia_component_libjpeg_path = os.path.join(part_data.get("out_path"), "component_package", part_data.get("part_path"), 'innerapis', 'libjpeg', 'includes')
    copy_directory_contents(skia_piex_path, skia_component_piex_path)
    copy_directory_contents(skia_libjpeg_path, skia_component_libjpeg_path)

    part_path = _get_parts_path(parts_path_info, part_name)
    if part_path is None:
        return
    part_data.update({"subsystem_name": subsystem_name, "part_name": part_name,
                      "part_path": part_path})
    modules = _parse_module_list(part_data)
    if len(modules) == 0:
        return
    is_component_build = False
    _public_deps_list = []
    for module in modules:
        module_deps_list = _handle_module(part_data, components_json, module)
        if module_deps_list:
            _public_deps_list.extend(module_deps_list)
            is_component_build = True
    _copy_required_docs(part_data, _public_deps_list)
    _finish_component_build(part_data)


def process_variants_default(part_data, parts_path_info, part_name, subsystem_name, components_json):
    # 减少代码重复调用
    preloader_path = os.path.join(part_data.get('root_path'), 'out', 'preloader', 'rk3568')
    variants_default_source_files = [
        os.path.join(preloader_path, 'build_config.json'),
        os.path.join(part_data.get('root_path'), 'build', 'indep_configs', 'variants', 'common', 'default_deps.json'),
        os.path.join(preloader_path, 'features.json'),
        os.path.join(preloader_path, 'parts_config.json'),
        os.path.join(preloader_path, 'system', 'etc', 'syscap.json'),
        os.path.join(preloader_path, 'system', 'etc', 'param', 'syscap.para'),
        os.path.join(preloader_path, 'system', 'etc', 'SystemCapability.json')
    ]

    variants_root = os.path.join(part_data.get('out_path'), 'component_package', 'variants', 'variants_default')
    variants_component_path = os.path.join(variants_root, 'config')
    try:
        os.makedirs(variants_component_path, exist_ok=True)
        for source_file in variants_default_source_files:
            if not os.path.exists(source_file):
                raise FileNotFoundError(f"Source file not found: {source_file}")
            shutil.copy2(source_file, variants_component_path)
        print("All confiauration files copied successfully")
    
        # 处理bundle.json文件和license文件，readme文件
        bundle_content = generate_variants_default_bundle_info()
        bundle_path = os.path.join(variants_root, 'bundle.json')
        _create_bundle_json(bundle_path, bundle_content)

        # 创建LICENSE文件、readme.md
        variants_default_license_path = os.path.join(variants_root, 'LICENSE')
        variants_default_readme_path = os.path.join(variants_root, 'README.md')
        with open(variants_default_license_path, 'w') as file:
            file.write("license")
        with open(variants_default_readme_path, 'w') as file:
            file.write("readme")

        _finish_component_build(part_data)
    except Exception as e:
        print(f"Error processing variants_default: {str(e)}")
        raise


def generate_variants_default_bundle_info():
    return {
        "name": "@ohos/variants_default",
        "description": "",
        "version": "3.1.0-snapshot",
        "license": "Apache License 2.0",
        "publishAs": "binary",
        "segment": {
            "destPath": "variants/variants_default"
        },
        "dirs": {
            "config": [
                "config/*"
            ]
        },
        "scripts": {},
        "component": {
            "name": "variants_default",
            "subsystem": "build",
            "syscap": [],
            "features": [],
            "adapted_system_type": [],
            "rom": "",
            "ram": "",
            "deps": {
                "components": [
                    "musl",
                    "linux",
                    "googletest"
                ],
                "third_party": []
            },
            "build": {
                "sub_component": [],
                "inner_kits": [],
                "test": []
            }
        },
        "os": "linux",
        "buildArch": "x86",
        "dependencies": {}
    }


def write_hilog_gn(part_data, module):
    gn_path = os.path.join(part_data.get("out_path"), "component_package", part_data.get("part_path"),
                           "innerapis", module, "BUILD.gn")
    if os.path.exists(gn_path):
        os.remove(gn_path)
    fd = os.open(gn_path, os.O_WRONLY | os.O_CREAT, mode=0o640)
    fp = os.fdopen(fd, 'w')
    fp.write("""import("//build/ohos.gni")

    config("hilog_rust_configs") {
      visibility = [ ":*" ]
      include_dirs = [
        "includes",
      ]
      }


    ohos_rust_shared_library("hilog_rust") {
      sources = [ "src/lib.rs" ]

      deps = [ "../libhilog:libhilog" ]
      crate_name = "hilog_rust"
      crate_type = "dylib"
      rustflags = [ "-Zstack-protector=all" ]

      subsystem_name = "hiviewdfx"
      part_name = "hilog"
    }""")
    print("_generate_build_gn has done ")
    fp.close()


def _hilog_rust_handle(part_data, module, components_json):
    public_deps_list = []
    if not _is_innerkit(components_json, part_data.get("part_name"), module):
        return public_deps_list
    json_data = _get_json_data(part_data, module)
    _lib_special_handler(part_data.get("part_name"), module, part_data)
    lib_exists, _ = _copy_lib(part_data, json_data, module)
    if lib_exists is False:
        return public_deps_list
    includes = _handle_includes_data(json_data)
    deps = _handle_deps_data(json_data)
    _copy_includes(part_data, module, includes)
    _list = _generate_build_gn(part_data, module, json_data, deps, components_json, public_deps_list)
    write_hilog_gn(part_data, module)
    _toolchain_gn_copy(part_data, module, json_data['out_name'])
    hilog_rust_out = os.path.join(part_data.get("out_path"), "component_package", part_data.get("part_path"),
                                  "innerapis", module)
    hilog_rust_dir = os.path.join(part_data.get("root_path"), part_data.get("part_path"), "interfaces", "rust")
    folder_to_copy = os.path.join(hilog_rust_dir, "src")  # 替换为实际的文件夹名称
    file_to_copy = os.path.join(hilog_rust_dir, "Cargo.toml")  # 替换为实际的文件名称
    # 检查文件夹和文件是否存在
    if os.path.exists(folder_to_copy) and os.path.exists(file_to_copy):
        # 复制文件夹
        shutil.copytree(folder_to_copy, os.path.join(hilog_rust_out, os.path.basename(folder_to_copy)))
        # 复制文件
        shutil.copy(file_to_copy, os.path.join(hilog_rust_out, os.path.basename(file_to_copy)))
    else:
        print("文件夹或文件不存在，无法复制。")

    return _list


def process_hilog(part_data, parts_path_info, part_name, subsystem_name, components_json):
    # 只处理一个模块
    # 处理分类B的逻辑
    part_path = _get_parts_path(parts_path_info, part_name)
    if part_path is None:
        return
    part_data.update({"subsystem_name": subsystem_name, "part_name": part_name,
                      "part_path": part_path})
    modules = _parse_module_list(part_data)
    print('modules', modules)
    if len(modules) == 0:
        return
    is_component_build = False
    _public_deps_list = []
    for module in modules:
        module_deps_list = _handle_module(part_data, components_json, module)
        if module == 'hilog_rust':
            _hilog_rust_handle(part_data, module, components_json)
        if module_deps_list:
            _public_deps_list.extend(module_deps_list)
        is_component_build = True
    if is_component_build:
        _copy_required_docs(part_data, _public_deps_list)
        _finish_component_build(part_data)


def generate_hisysevent_gn(part_data, module):
    gn_path = os.path.join(part_data.get("out_path"), "component_package", part_data.get("part_path"),
                           "innerapis", module, "BUILD.gn")
    if os.path.exists(gn_path):
        os.remove(gn_path)
    fd = os.open(gn_path, os.O_WRONLY | os.O_CREAT, mode=0o640)
    fp = os.fdopen(fd, 'w')
    fp.write("""import("//build/ohos.gni")

    ohos_rust_shared_library("hisysevent_rust") {
      sources = [
        "src/lib.rs",
        "src/macros.rs",
        "src/sys_event.rs",
        "src/sys_event_manager.rs",
        "src/utils.rs",
      ]

      external_deps = [
        "hisysevent:hisysevent_c_wrapper",
        "hisysevent:libhisysevent",
        "hisysevent:libhisyseventmanager",
      ]

      crate_name = "hisysevent"
      crate_type = "dylib"
      rustflags = [ "-Zstack-protector=all" ]

      part_name = "hisysevent"
      subsystem_name = "hiviewdfx"
    }
    """)
    print("_generate_build_gn has done ")
    fp.close()


def _hisysevent_rust_handle(part_data, module, components_json):
    public_deps_list = []
    if not _is_innerkit(components_json, part_data.get("part_name"), module):
        return public_deps_list
    json_data = _get_json_data(part_data, module)
    _lib_special_handler(part_data.get("part_name"), module, part_data)
    lib_exists, _ = _copy_lib(part_data, json_data, module)
    if lib_exists is False:
        return public_deps_list
    includes = _handle_includes_data(json_data)
    deps = _handle_deps_data(json_data)
    _copy_includes(part_data, module, includes)
    _list = _generate_build_gn(part_data, module, json_data, deps, components_json, public_deps_list)
    generate_hisysevent_gn(part_data, module)
    _toolchain_gn_copy(part_data, module, json_data['out_name'])
    hisysevent_rust_out = os.path.join(part_data.get("out_path"), "component_package", part_data.get("part_path"),
                                       "innerapis", module)
    hisysevent_rust_dir = os.path.join(part_data.get("root_path"), part_data.get("part_path"), "interfaces",
                                       "innerkits", "rust")
    folder_to_copy = os.path.join(hisysevent_rust_dir, "src")  # 替换为实际的文件夹名称
    file_to_copy = os.path.join(hisysevent_rust_dir, "Cargo.toml")  # 替换为实际的文件名称
    # 检查文件夹和文件是否存在
    if os.path.exists(folder_to_copy) and os.path.exists(file_to_copy):
        # 复制文件夹
        shutil.copytree(folder_to_copy, os.path.join(hisysevent_rust_out, os.path.basename(folder_to_copy)))
        # 复制文件
        shutil.copy(file_to_copy, os.path.join(hisysevent_rust_out, os.path.basename(file_to_copy)))
    else:
        print("文件夹或文件不存在，无法复制。")

    return _list


def process_hisysevent(part_data, parts_path_info, part_name, subsystem_name, components_json):
    # 只处理一个模块
    part_path = _get_parts_path(parts_path_info, part_name)
    if part_path is None:
        return
    part_data.update({"subsystem_name": subsystem_name, "part_name": part_name,
                      "part_path": part_path})
    modules = _parse_module_list(part_data)
    print('modules', modules)
    if len(modules) == 0:
        return
    is_component_build = False
    _public_deps_list = []
    for module in modules:
        module_deps_list = _handle_module(part_data, components_json, module)
        if module == 'hisysevent_rust':
            _hisysevent_rust_handle(part_data, module, components_json)
        if module_deps_list:
            _public_deps_list.extend(module_deps_list)
        is_component_build = True
    if is_component_build:
        _copy_required_docs(part_data, _public_deps_list)
        _finish_component_build(part_data)


def _generate_runtime_core_build_gn():
    gn_path = os.path.join(args.get("out_path"), "component_package", args.get("part_path"),
                           "innerapis", module, "BUILD.gn")
    fd = os.open(gn_path, os.O_WRONLY | os.O_CREAT, mode=0o640)
    fp = os.fdopen(fd, 'w')
    _generate_import(fp)
    _generate_configs(fp, module)
    _generate_prebuilt_shared_library(fp, json_data.get('type'), module)
    _generate_public_configs(fp, module)
    _list = _generate_public_external_deps(fp, module, deps, components_json, public_deps_list)
    _generate_other(fp, args, json_data, module)
    _generate_end(fp)
    print("_generate_build_gn has done ")
    fp.close()
    return _list


def _handle_module_runtime_core(args, components_json, module):
    public_deps_list = []
    if _is_innerkit(components_json, args.get("part_name"), module) == False:
        return public_deps_list
    json_data = _get_json_data(args, module)
    _lib_special_handler(args.get("part_name"), module, args)
    lib_exists, is_ohos_ets_copy = _copy_lib(args, json_data, module)
    if lib_exists is False:
        return public_deps_list
    includes = _handle_includes_data(json_data)
    deps = _handle_deps_data(json_data)
    _copy_includes(args, module, includes)
    _list = _generate_build_gn(args, module, json_data, deps, components_json, public_deps_list, is_ohos_ets_copy)
    _toolchain_gn_copy(args, module, json_data['out_name'])
    return _list


def process_runtime_core(part_data, parts_path_info, part_name, subsystem_name, components_json):
    # 处理分类runtime_core的逻辑
    part_path = _get_parts_path(parts_path_info, part_name)
    if part_path is None:
        return
    part_data.update({"subsystem_name": subsystem_name, "part_name": part_name,
                      "part_path": part_path})
    modules = _parse_module_list(part_data)
    print('modules', modules)
    if len(modules) == 0:
        return
    is_component_build = False
    _public_deps_list = []
    for module in modules:
        module_deps_list = _handle_module_runtime_core(part_data, components_json, module)
        if module_deps_list:
            _public_deps_list.extend(module_deps_list)
            is_component_build = True
    if is_component_build:
        _copy_required_docs(part_data, _public_deps_list)
        _finish_component_build(part_data)


def process_drivers_interface_display(part_data, parts_path_info, part_name, subsystem_name, components_json):
    part_path = _get_parts_path(parts_path_info, part_name)
    if part_path is None:
        return
    part_data.update({"subsystem_name": subsystem_name, "part_name": part_name,
                      "part_path": part_path})
    modules = _parse_module_list(part_data)
    print('modules', modules)
    if len(modules) == 0:
        return
    is_component_build = False
    _public_deps_list = []
    for module in modules:
        module_deps_list = _handle_module(part_data, components_json, module)
        if module_deps_list:
            _public_deps_list.extend(module_deps_list)
            is_component_build = True
    lib_out_dir = os.path.join(part_data.get("out_path"), "component_package",
                               part_data.get("part_path"), "innerapis", "display_commontype_idl_headers", "libs")
    if not os.path.exists(lib_out_dir):
        os.makedirs(lib_out_dir)
    file_path = os.path.join(lib_out_dir, 'libdisplay_commontype_idl_headers')
    with open(file_path, 'wb') as file:
        pass
    if is_component_build:
        _copy_required_docs(part_data, _public_deps_list)
        _finish_component_build(part_data)


def process_drivers_interface_usb(part_data, parts_path_info, part_name, subsystem_name, components_json):
    part_path = _get_parts_path(parts_path_info, part_name)
    if part_path is None:
        return
    part_data.update({"subsystem_name": subsystem_name, "part_name": part_name,
                      "part_path": part_path})
    modules = _parse_module_list(part_data)
    print('modules', modules)
    if len(modules) == 0:
        return
    is_component_build = False
    _public_deps_list = []
    for module in modules:
        module_deps_list = _handle_module(part_data, components_json, module)
        if module_deps_list:
            _public_deps_list.extend(module_deps_list)
            is_component_build = True
    lib_out_dir = os.path.join(part_data.get("out_path"), "component_package",
                               part_data.get("part_path"), "innerapis", "usb_idl_headers_1.1", "libs")
    if not os.path.exists(lib_out_dir):
        os.makedirs(lib_out_dir)
    file_path = os.path.join(lib_out_dir, 'libusb_idl_headers_1.1')
    with open(file_path, 'wb') as file:
        pass
    if is_component_build:
        _copy_required_docs(part_data, _public_deps_list)
        _finish_component_build(part_data)


def process_drivers_interface_ril(part_data, parts_path_info, part_name, subsystem_name, components_json):
    part_path = _get_parts_path(parts_path_info, part_name)
    if part_path is None:
        return
    part_data.update({"subsystem_name": subsystem_name, "part_name": part_name,
                      "part_path": part_path})
    modules = _parse_module_list(part_data)
    print('modules', modules)
    if len(modules) == 0:
        return
    is_component_build = False
    _public_deps_list = []
    for module in modules:
        module_deps_list = _handle_module(part_data, components_json, module)
        if module_deps_list:
            _public_deps_list.extend(module_deps_list)
            is_component_build = True
    lib_out_dir = os.path.join(part_data.get("out_path"), "component_package",
                               part_data.get("part_path"), "innerapis", "ril_idl_headers", "libs")
    if not os.path.exists(lib_out_dir):
        os.makedirs(lib_out_dir)
    file_path = os.path.join(lib_out_dir, 'libril_idl_headers')
    with open(file_path, 'wb') as file:
        pass
    if is_component_build:
        _copy_required_docs(part_data, _public_deps_list)
        _finish_component_build(part_data)


# 函数映射字典
function_map = {
    'musl': process_musl,
    "developer_test": process_developer_test,  # 同rust
    "drivers_interface_display": process_drivers_interface_display,  # 驱动的, 新建一个libs目录/ innerapi同名文件
    "runtime_core": process_runtime_core,  # 编译参数, 所有下面的innerapi的cflags都不
    "drivers_interface_usb": process_drivers_interface_usb,  # 同驱动
    "drivers_interface_ril": process_drivers_interface_ril,  # 同驱动
    "skia": process_skia,
    "variants_default": process_variants_default,
}


def _process_part(args, parts_path_info, part_name, subsystem_name, components_json):
    # 使用映射字典来调用对应的函数
    if part_name in function_map.keys():
        function_map[part_name](args, parts_path_info, part_name, subsystem_name, components_json)
    else:
        print(f"没有找到处理分类{part_name}的函数。")


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


def _get_external_public_config(_path, _config_name):
    py_args = _get_args()
    out_path = py_args.out_path
    _json_path = os.path.join(out_path, 'external_public_configs', _path, f'{_config_name}.json')
    try:
        with os.fdopen(os.open(_json_path, os.O_RDWR | os.O_CREAT, stat.S_IWUSR | stat.S_IRUSR),
                       'r', encoding='utf-8') as f:
            jsondata = json.load(f)
    except Exception as e:
        print('_json_path: ', _json_path)
        print('--_get_external_public_config parse json error--')
        return []

    include_dirs = jsondata.get('include_dirs')
    return include_dirs


def _handle_two_layer_json(json_key, json_data, desc_list):
    value_depth = len(json_data.get(json_key))
    for i in range(value_depth):
        _label = json_data.get(json_key)[i].get('label')
        _include_dirs = json_data.get(json_key)[i].get('include_dirs')
        if _include_dirs:
            desc_list.extend(_include_dirs)
        else:
            full_path = _label.split('//')[-1]
            _path = full_path.split(':')[0]
            _config_name = full_path.split(':')[-1]
            _include_dirs = _get_external_public_config(_path, _config_name)
            if _include_dirs:
                desc_list.extend(_include_dirs)


def _get_json_data(args, module):
    json_path = os.path.join(args.get("out_path"),
                             args.get("subsystem_name"), args.get("part_name"), "publicinfo", module + ".json")
    with os.fdopen(os.open(json_path, os.O_RDWR | os.O_CREAT, stat.S_IWUSR | stat.S_IRUSR),
                   'r', encoding='utf-8') as f:
        try:
            file_content = f.read()
            jsondata = json.loads(file_content)
        except Exception as e:
            print(json_path)
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
    for file in os.listdir(src_path):
        path = os.path.join(src_path, file)
        if os.path.isdir(path):
            if file.startswith("."):
                continue
            path1 = os.path.join(target_path, file)
            _copy_dir(path, path1)
        else:
            _, file_extension = os.path.splitext(file)
            if file_extension not in [".h", ".hpp", ".in", ".inc", ".inl"]:
                continue
            if not os.path.exists(target_path):
                os.makedirs(target_path)
            # 打包时存在同名头文件时，使用先遍历到的
            if not os.path.exists(os.path.join(target_path, file)):
                shutil.copy2(path, os.path.join(target_path, file))
    return True


def _get_target_include(part_name, include):
    # 需要多层提取include头文件的白名单路径
    multilayer_include_config_path = os.path.join('build', 'indep_configs', 'config', 'multilayer_include_config.json')
    with open(multilayer_include_config_path, "r") as f:
        part_whitch_use_multilayer_include = json.load(f)
        if part_name in part_whitch_use_multilayer_include:
            target_include = include.replace("//", "")
            if target_include.endswith("/"):
                target_include = target_include[:-1]
            return target_include
        else:
            return ""


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
            relative_target_include = _get_target_include(args.get("part_name"), include)
            toolchain_real_include_out_dir = os.path.join(toolchain_includes_out_dir, relative_target_include)
            if not os.path.exists(toolchain_real_include_out_dir):
                os.makedirs(toolchain_real_include_out_dir)
            part_path = args.get("part_path")
            _sub_include = include.split(f"{part_path}/")[-1]
            split_include = include.split("//")[1]
            real_include_path = os.path.join(args.get("root_path"), split_include)
            _copy_dir(real_include_path, toolchain_real_include_out_dir)
    if not os.path.exists(includes_out_dir):
        os.makedirs(includes_out_dir)
    for include in includes:
        relative_target_include = _get_target_include(args.get("part_name"), include)
        includes_real_out_dir = os.path.join(includes_out_dir, relative_target_include)
        if not os.path.exists(includes_real_out_dir):
            os.makedirs(includes_real_out_dir)
        part_path = args.get("part_path")
        _sub_include = include.split(f"{part_path}/")[-1]
        split_include = include.split("//")[1]
        real_include_path = os.path.join(args.get("root_path"), split_include)
        _copy_dir(real_include_path, includes_real_out_dir)
    print("_copy_includes has done ")


def _copy_toolchain_lib(file_name, root, _name, lib_out_dir):
    if not file_name.startswith('.') and file_name.startswith(_name):
        if not os.path.exists(lib_out_dir):
            os.makedirs(lib_out_dir)
        file = os.path.join(root, file_name)
        shutil.copy(file, lib_out_dir)


def _toolchain_lib_handler(args, toolchain_path, _name, module, toolchain_name):
    lib_out_dir = os.path.join(args.get("out_path"), "component_package",
                                       args.get("part_path"), "innerapis", module, toolchain_name, "libs")
    if os.path.isfile(toolchain_path):
        if not os.path.exists(lib_out_dir):
            os.makedirs(lib_out_dir)
        shutil.copy(toolchain_path, lib_out_dir)
    else:
        for root, dirs, files in os.walk(toolchain_path):
            for file_name in files:
                _copy_toolchain_lib(file_name, root, _name, lib_out_dir)


def _toolchain_static_file_path_mapping(subsystem_name, args, i):
    if subsystem_name == "thirdparty":
        subsystem_name = "third_party"
    toolchain_path = os.path.join(args.get("out_path"), i, 'obj', subsystem_name,
                                  args.get("part_name"))
    return toolchain_path


def replace_default_toolchains_in_output(path, default_toolchain="ohos_clang_arm64/"):
    return path.replace(default_toolchain, "")


def _copy_lib(args, json_data, module):
    so_path = ""
    lib_status = True
    _target_type = json_data.get('type')
    subsystem_name = args.get("subsystem_name")
    is_ohos_ets_copy = False
    ets_outputs = []

    # 根据 type 字段和 module 选择正确的 so_path
    if _target_type == 'copy' and module == 'ipc_core':
        so_path = os.path.join(subsystem_name, args.get("part_name"), 'libipc_single.z.so')
    elif _target_type == "rust_library" or _target_type == "rust_proc_macro":
        # 选择包含 'lib.unstripped' 的路径
        outputs = json_data.get('outputs', [])
        for output in outputs:
            if 'lib.unstripped' in output:
                output = replace_default_toolchains_in_output(output)
                so_path = output
                break
        # 如果没有找到包含 'lib.unstripped' 的路径，则选择最后一个路径
        if not so_path and outputs:
            so_path = outputs[-1]
    else:
        # 对于非 rust_library 类型，选择不包含 'lib.unstripped' 的路径
        outputs = json_data.get('outputs', [])
        for output in outputs:
            if 'ohos_ets' in output:
                is_ohos_ets_copy = True
                ets_outputs.append(output)
            elif '.unstripped' not in output:
                output = replace_default_toolchains_in_output(output)
                so_path = output
                break
        # 如果所有路径都包含 'lib.unstripped' 或者没有 outputs，则使用 out_name
        if not so_path:
            so_path = json_data.get('out_name')
    if is_ohos_ets_copy:
        for output in ets_outputs:
            if not copy_so_file(args, module, output, _target_type):
                lib_status = False
    elif so_path:
        lib_status = copy_so_file(args, module, so_path, _target_type)
    if lib_status and _target_type == 'static_library':
        copy_static_deps_file(args, json_data.get('label'), module, so_path)
    return lib_status, is_ohos_ets_copy


def _do_copy_static_deps_file(args, out_path, lib_path, toolchain):
    lib_status = False
    static_lib_path = os.path.join(out_path, lib_path)
    lib_out_dir = os.path.join(out_path, "component_package",
                                   args.get("part_path"), "common", toolchain, "deps")
    lib_status = _copy_file(static_lib_path, lib_out_dir) or lib_status
    return lib_status


def is_not_basic_lib(lib_path):
    if "obj/third_party/musl" in lib_path or "prebuilts/clang" in lib_path:
        return False
    else:
        return True


def read_deps_from_ninja_file(ninja_file, prefix):
    print("ninja file: ", ninja_file)
    with open(ninja_file, 'r') as f:
        for line in f:
            if line.strip().startswith(prefix):
                deps_libs = line.strip().split(' ')
                return deps_libs
    return []


def copy_static_deps_file(args, label, module, so_path):
    toolchains = set(args.get("toolchain_info").keys())
    toolchains.add("")
    lib_status = False
    out_path = args.get("out_path")
    for toolchain in toolchains:
        ninja_file = os.path.join(out_path, toolchain, "obj", (label.split(':')[0]).split('//')[1], label.split(':')[1] + ".ninja")
        if not os.path.exists(ninja_file):
            continue
        prefix = "build " + os.path.join(toolchain, so_path)
        deps_libs = read_deps_from_ninja_file(ninja_file, prefix)
        static_deps = []
        toolchain_module = toolchain + "_" + module
        for lib in deps_libs:
            lib_name = os.path.basename(lib)
            if lib_name in static_deps:
                print("lib_name: {} already in static_deps".format(lib_name))
                continue
            if lib.endswith(".a") and lib != so_path and is_not_basic_lib(lib):
                static_deps.append(lib_name)
                lib_status = _do_copy_static_deps_file(args, out_path, lib, toolchain) or lib_status
        args.get("static_deps")[toolchain_module] = static_deps
        print("copy static deps: ", static_deps)
    return lib_status


def copy_so_file(args, module, so_path, target_type):
    lib_status = False
    out_path = args.get("out_path")
    so_path_with_out_path = os.path.join(out_path, so_path)
    lib_out_dir = os.path.join(out_path, "component_package",
                                   args.get("part_path"), "innerapis", module, "libs")
    if args.get("toolchain_info").keys():
        for toolchain_name in args.get("toolchain_info").keys():
            lib_out_dir_with_toolchain = os.path.join(args.get("out_path"), "component_package",
                                       args.get("part_path"), "innerapis", module, toolchain_name, "libs")
            so_path_with_toolchain = os.path.join(args.get("out_path"), toolchain_name, so_path)
            unzipped_so_path_with_toolchain = so_path_with_toolchain.replace(".z.", ".")
            if toolchain_name in so_path:
                lib_status = _copy_file(so_path_with_out_path, lib_out_dir_with_toolchain, target_type) or lib_status
            elif os.path.isfile(so_path_with_toolchain):
                lib_status = _copy_file(so_path_with_toolchain, lib_out_dir_with_toolchain, target_type) or lib_status
            elif os.path.isfile(unzipped_so_path_with_toolchain):
                lib_status = _copy_file(unzipped_so_path_with_toolchain, lib_out_dir_with_toolchain, target_type) or lib_status
    lib_status = _copy_file(so_path_with_out_path, lib_out_dir, target_type) or lib_status
    return lib_status


def _copy_file(so_path, lib_out_dir, target_type=""):
    # 处理静态库依赖
    if lib_out_dir.endswith("deps") or lib_out_dir.endswith("deps/"):
        if not os.path.isfile(so_path):
            print("WARNING: {} is not a file!".format(so_path))
            return False
        if not os.path.exists(lib_out_dir):
            os.makedirs(lib_out_dir)
        shutil.copy(so_path, lib_out_dir)
        return True
    if target_type != 'copy' and not os.path.isfile(so_path):
        print("WARNING: {} is not a file!".format(so_path))
        return False
    if os.path.exists(lib_out_dir):
        shutil.rmtree(lib_out_dir)
    if os.path.isfile(so_path):
        if not os.path.exists(lib_out_dir):
            os.makedirs(lib_out_dir)
            shutil.copy(so_path, lib_out_dir)
    elif os.path.exists(so_path):
        dir_name = os.path.basename(so_path)
        new_lib_out_dir = os.path.join(lib_out_dir, dir_name)
        shutil.copytree(so_path, new_lib_out_dir)
    return True


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
    sorted_dict = {}
    for public_deps in public_deps_list:
        _public_dep_part_name = public_deps.split(':')[0]
        if _public_dep_part_name != args.get("part_name"):
            _public_dep = f"@{args.get('organization_name')}/{_public_dep_part_name}"
            dependencies_dict.update({_public_dep: "*"})
            sorted_dict = dict(sorted(dependencies_dict.items()))
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
            bundle_data['dependencies'] = sorted_dict
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


def _generate_import(fp, is_ohos_ets_copy=False):
    fp.write('import("//build/ohos.gni")\n')
    if is_ohos_ets_copy:
        fp.write('import("//build/templates/common/copy.gni")\n')


def _gcc_flags_info_handle(json_data):
    def should_process_key(k):
        return k not in ["label", "include_dirs"]

    def process_config(config):
        result = {}
        for k, v in config.items():
            if should_process_key(k):
                result.setdefault(k, []).extend(v)
        return result

    _flags_info = {}
    _public_configs = json_data.get('public_configs')
    if _public_configs:
        for config in _public_configs:
            config_info = process_config(config)
            for k, v in config_info.items():
                _flags_info.setdefault(k, []).extend(v)
    return _flags_info


def _generate_configs(fp, module, json_data, _part_name):
    includes = _handle_includes_data(json_data)
    target_includes = []

    fp.write('\nconfig("' + module + '_configs") {\n')
    fp.write('  visibility = [ ":*" ]\n')
    fp.write('  include_dirs = [\n')
    for include in includes:
        target_include = _get_target_include(_part_name, include)
        if target_include not in target_includes:
            target_includes.append(target_include)
    for include_dir in target_includes:
        include_dir = os.path.join('includes', include_dir)
        fp.write('    "{}",\n'.format(include_dir))
    if module == 'ability_runtime':
        fp.write('    "includes/context",\n')
        fp.write('    "includes/app",\n')
    fp.write('  ]\n')
    if _part_name == 'runtime_core':
        fp.write('  }\n')
        return
    _flags_info = _gcc_flags_info_handle(json_data)
    if _flags_info:
        for k, _list in _flags_info.items():
            fp.write(f'  {k} = [\n')
            for j in _list:
                # 保留所有 \ 转义符号
                j_escaped = j.replace('"', '\\"')
                fp.write(f'  "{j_escaped}",\n')
            fp.write('  ]\n')
    fp.write('  }\n')


def _generate_prebuilt_target(fp, target_type, module, is_ohos_ets_copy=False):
    if target_type == 'static_library':
        fp.write('ohos_prebuilt_static_library("' + module + '") {\n')
    elif target_type == 'executable':
        fp.write('ohos_prebuilt_executable("' + module + '") {\n')
    elif module != 'ipc_core' and (target_type == 'etc' or target_type == 'copy'):
        if is_ohos_ets_copy:
            fp.write('ohos_copy("' + module + '") {\n')
        else:
            fp.write('ohos_prebuilt_etc("' + module + '") {\n')
    elif target_type == 'rust_library' or target_type == 'rust_proc_macro':
        fp.write('ohos_prebuilt_rust_library("' + module + '") {\n')
    else:
        fp.write('ohos_prebuilt_shared_library("' + module + '") {\n')


def _generate_public_configs(fp, module):
    fp.write(f'  public_configs = [":{module}_configs"]\n')


# 目前特殊处理的依赖关系映射
_DEPENDENCIES_MAP = {
    ('ets_runtime', 'libark_jsruntime'): ["runtime_core:libarkfile_static"],
}


def _public_deps_special_handler(module, args):
    _part_name = args.get('part_name')
    # 使用映射字典来获取依赖列表
    return _DEPENDENCIES_MAP.get((_part_name, module), [])


def _generate_public_external_deps(fp, module, deps: list, components_json, public_deps_list: list, args):
    fp.write('  public_external_deps = [\n')
    for dep in deps:
        public_external_deps = _get_public_external_deps(components_json, dep)
        if len(public_external_deps) > 0:
            fp.write(f"""    "{public_external_deps}",\n""")
            public_deps_list.append(public_external_deps)
    for _public_external_deps in _public_deps_special_handler(module, args):
        fp.write(f"""    "{_public_external_deps}",\n""")
        public_deps_list.append(_public_external_deps)
    fp.write('  ]\n')

    return public_deps_list


def _find_ohos_ets_dir(outputs):
    for path in outputs:
        parts = path.split('/')
        for part in parts:
            if "ohos_ets" in part:
                return '/'.join(parts[:-1])
    return None


def _generate_other(fp, args, json_data, module, is_ohos_ets_copy=False):
    outputs = json_data.get('outputs', [])
    ohos_ets_dir = _find_ohos_ets_dir(outputs)
    if is_ohos_ets_copy:
        sources_arr = [f"libs/{path.split('/')[-1]}" for path in outputs]
        sources_str = str(sources_arr).replace("'", '"')
        fp.write(f'  sources = {sources_str}\n')
        fp.write('  outputs = [ "$root_out_dir/' + ohos_ets_dir + '/{{source_file_part}}" ]\n')
        fp.write('  part_name = "' + args.get("part_name") + '"\n')
        fp.write('  subsystem_name = "' + args.get("subsystem_name") + '"\n') 
    else:
        if json_data.get('type') == 'copy' and module == 'ipc_core':
            so_name = 'libipc_single.z.so'
        else:
            so_name = json_data.get('out_name')
            for output in outputs:
                so_name = output.split('/')[-1]
        if json_data.get('type') == 'copy' and module != 'ipc_core':
            fp.write('  copy_linkable_file = true \n')
        fp.write('  source = "libs/' + so_name + '"\n')
        fp.write('  part_name = "' + args.get("part_name") + '"\n')
        fp.write('  subsystem_name = "' + args.get("subsystem_name") + '"\n')


def _generate_end(fp):
    fp.write('}')


def convert_rustdeps_to_innerapi(dep, components_json):
    # 分割路径和模块名
    dep_parts = dep.split(':', 1)
    if len(dep_parts) != 2:
        return False, "" # 格式不正确，不是 innerapi

    path, module = dep_parts
    path = path.lstrip('//')

    # 遍历 components.json 中的每个部件
    for component, info in components_json.items():
        if path.startswith(info['path']) and _check_dep_in_innerapi(info.get('innerapis', []), dep):
            return True, f"{component}:{module}"
    return False, ""


def _check_dep_in_innerapi(innerapis, dep):
    for innerapi in innerapis:
        if innerapi['label'] == (dep.split('(')[0] if ('(' in dep) else dep):
            return True
    return False


def _generate_rust_deps(fp, json_data, components_json):
    rust_deps = json_data.get("rust_deps")
    external_deps = []
    for _dep in rust_deps:
        has_innerapi, innerapi = convert_rustdeps_to_innerapi(_dep, components_json)
        if has_innerapi:
            external_deps.append(innerapi)
    fp.write('  external_deps = [\n')
    for external_dep in external_deps:
        fp.write(f"""    "{external_dep}",\n""")
    fp.write('  ]\n')


def _copy_rust_crate_info(fp, json_data):
    fp.write(f'  rust_crate_name = \"{json_data.get("rust_crate_name")}\"\n')
    fp.write(f'  rust_crate_type = \"{json_data.get("rust_crate_type")}\"\n')


def _get_static_deps(args, module, toolchain):
    default_toolchain_module = toolchain + "_" + module
    return args.get("static_deps").get(default_toolchain_module, [])


def _generate_static_public_deps_string(args, deps: list, toolchain: str):
    public_deps_str = ""
    if not deps:
        return ""
    public_deps_str += '  public_deps = [\n'
    for dep in deps:
        public_deps_str += f"""    ":{dep}", \n"""
    public_deps_str += '  ]\n'
    return public_deps_str


def _generate_static_deps_target_string(args, deps: list, toolchain: str):
    # target_path: part_name/innerapis/${innerapi_name}/${toolchain}/BUILD.gn
    # static_lib_path: part_name/common/${toolchain}/deps
    if toolchain:
        source_prefix = os.path.join("../../../common", toolchain, "deps/")
    else:
        source_prefix = os.path.join("../../common", toolchain, "deps/")
    output_prefix = os.path.join("common", toolchain, "deps/")
    target_string = ""
    for dep in deps:
        target_string += '\n'
        target_string += 'ohos_prebuilt_static_library("' + dep + '") {\n'
        target_string += '  source = "' + source_prefix + dep + '"\n'
        target_string += '  output = "' + output_prefix + dep + '"\n'
        target_string += '  part_name = "' + args.get("part_name") + '"\n'
        target_string += '  subsystem_name = "' + args.get("subsystem_name") + '"\n'
        target_string += '}'
    return target_string


def _generate_static_deps_target(fp, args, deps: list, toolchain):
    target_string = _generate_static_deps_target_string(args, deps, toolchain)
    fp.write(target_string)


def _generate_static_public_deps(fp, args, deps: list, toolchain):
    public_deps_string = _generate_static_public_deps_string(args, deps, toolchain)
    fp.write(public_deps_string)


def _generate_build_gn(args, module, json_data, deps: list, components_json, public_deps_list, is_ohos_ets_copy=False):
    gn_path = os.path.join(args.get("out_path"), "component_package", args.get("part_path"),
                           "innerapis", module, "BUILD.gn")
    static_deps_files = _get_static_deps(args, module, "") # 处理静态库依赖
    fd = os.open(gn_path, os.O_WRONLY | os.O_CREAT, mode=0o640)
    fp = os.fdopen(fd, 'w')
    _generate_import(fp, is_ohos_ets_copy)
    _generate_configs(fp, module, json_data, args.get('part_name'))
    _target_type = json_data.get('type')
    _generate_prebuilt_target(fp, _target_type, module, is_ohos_ets_copy)
    _generate_public_configs(fp, module)
    _list = _generate_public_external_deps(fp, module, deps, components_json, public_deps_list, args)
    _generate_static_public_deps(fp, args, static_deps_files, "") # 处理静态库依赖
    if _target_type == "rust_library" or _target_type == "rust_proc_macro":
        _copy_rust_crate_info(fp, json_data)
        _generate_rust_deps(fp, json_data, components_json)
    _generate_other(fp, args, json_data, module, is_ohos_ets_copy)
    _generate_end(fp)
    _generate_static_deps_target(fp, args, static_deps_files, "") # 处理静态库依赖
    print(f"{module}_generate_build_gn has done ")
    fp.close()
    return _list


def _toolchain_gn_modify(args, module, toolchain_name, gn_path, so_name, toolchain_gn_file):
    if os.path.isfile(gn_path) and so_name:
        with open(gn_path, 'r') as f:
            _gn = f.read()
            pattern = r"libs/(.*.)"
            toolchain_gn = re.sub(pattern, 'libs/' + so_name + '\"', _gn)
            # 处理静态库依赖传递
            static_deps = _get_static_deps(args, module, toolchain_name)
            public_deps_str = _generate_static_public_deps_string(args, static_deps, toolchain_name)
            static_deps_target_str = _generate_static_deps_target_string(args, static_deps, toolchain_name)
            public_deps_pattern = r"  public_deps\s*=\s*\[\s*([^]]*)\s*\]"
            toolchain_gn = re.sub(public_deps_pattern, public_deps_str, toolchain_gn, re.DOTALL)
            static_deps_target_pattern = re.compile(r'ohos_prebuilt_static_library\("([^"]+\.a)"\)\s*\{[^}]*\}', re.DOTALL)
            toolchain_gn = static_deps_target_pattern.sub("", toolchain_gn)
            # toolchain_gn = re.sub(r"[\n]{2,}", "\n", toolchain_gn, re.DOTALL) # 删除多余换行符
            toolchain_gn += "\n"
            toolchain_gn += static_deps_target_str
        fd = os.open(toolchain_gn_file, os.O_WRONLY | os.O_CREAT, mode=0o640)
        fp = os.fdopen(fd, 'w')
        fp.write(toolchain_gn)
        fp.close()


def _get_toolchain_gn_file(lib_out_dir, out_name):
    unzipped_out_name = out_name.replace(".z.", ".")
    if os.path.exists(os.path.join(lib_out_dir, out_name)):
        return out_name
    elif os.path.exists(os.path.join(lib_out_dir, unzipped_out_name)):
        return unzipped_out_name
    else:
        print('Output file not found in toolchain dir.')
        return ''


def _toolchain_gn_copy(args, module, out_name):
    gn_path = os.path.join(args.get("out_path"), "component_package", args.get("part_path"),
                           "innerapis", module, "BUILD.gn")
    for i in args.get("toolchain_info").keys():
        lib_out_dir = os.path.join(args.get("out_path"), "component_package",
                                   args.get("part_path"), "innerapis", module, i, "libs")
        so_name = _get_toolchain_gn_file(lib_out_dir, out_name)
        if not so_name:
            continue
        toolchain_gn_file = os.path.join(args.get("out_path"), "component_package",
                                         args.get("part_path"), "innerapis", module, i, "BUILD.gn")
        if not os.path.exists(toolchain_gn_file):
            os.mknod(toolchain_gn_file)
        _toolchain_gn_modify(args, module, i, gn_path, so_name, toolchain_gn_file)


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


def _handle_module(args, components_json, module):
    public_deps_list = []
    if _is_innerkit(components_json, args.get("part_name"), module) == False:
        return public_deps_list
    json_data = _get_json_data(args, module)
    _lib_special_handler(args.get("part_name"), module, args)
    libstatus, is_ohos_ets_copy = _copy_lib(args, json_data, module)
    includes = _handle_includes_data(json_data)
    deps = _handle_deps_data(json_data)
    _copy_includes(args, module, includes)
    _list = _generate_build_gn(args, module, json_data, deps, components_json, public_deps_list, is_ohos_ets_copy)
    _toolchain_gn_copy(args, module, json_data['out_name'])
    return _list


def _copy_required_docs(args, public_deps_list):
    _copy_bundlejson(args, public_deps_list)
    _copy_license(args)
    _copy_readme(args)


def _finish_component_build(args):
    if args.get("build_type") in [0, 1]:
        _hpm_status = _hpm_pack(args)
        if _hpm_status:
            _copy_hpm_pack(args)


def _generate_component_package(args, components_json):
    modules = _parse_module_list(args)
    print('modules', modules)
    if len(modules) == 0:
        return
    is_component_build = False
    _public_deps_list = []
    for module in modules:
        module_deps_list = _handle_module(args, components_json, module)
        if module_deps_list:
            _public_deps_list.extend(module_deps_list)
        is_component_build = True
    if is_component_build:
        _copy_required_docs(args, _public_deps_list)
        _finish_component_build(args)


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


def generate_made_in_mark_file(args):
    from datetime import datetime
    import pytz
    str_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y_%m_%d_%H_%M_%S")
    build_origin = args.get("build_origin", "")
    if not build_origin:
        return
    mark_file = os.path.join(args.get("out_path"), "component_package", args.get("part_path"), f"made_in_{build_origin}")
    basic_dir = os.path.dirname(mark_file)
    os.makedirs(basic_dir, exist_ok=True)
    with open(f"{mark_file}_{str_time}", 'w') as f:
        f.write(f"the hpm package is made in {build_origin}, {str_time}")


def _package_interface(args, parts_path_info, part_name, subsystem_name, components_json):
    part_path = _get_parts_path(parts_path_info, part_name)
    if part_path is None:
        return
    args.update({"subsystem_name": subsystem_name, "part_name": part_name,
                 "part_path": part_path})
    generate_made_in_mark_file(args)
    if part_name in [
        "musl",  # 从obj/third_party/musl/usr 下提取到includes和libs
        "developer_test",  # 同rust
        "drivers_interface_display",  # 驱动的, 新建一个libs目录/ innerapi同名文件
        "runtime_core",  # 编译参数, 所有下面的innerapi的cflags都不
        "drivers_interface_usb",  # 同驱动
        "drivers_interface_ril",  # 同驱动
        "skia",
        "variants_default",
    ]:
        _process_part(args, parts_path_info, part_name, subsystem_name, components_json)
    else:
        _generate_component_package(args, components_json)


def _get_exclusion_list(root_path):
    part_black_list_path = os.path.join(root_path, "build", "indep_configs", "config",
                                        "binary_package_exclusion_list.json")
    data = []
    try:
        with open(part_black_list_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"can not find file: {part_black_list_path}.")
    except Exception as e:
        print(f"{part_black_list_path}: \n {e}")
    return data


def additional_comoponents_json():
    return {"rust": {
        "innerapis": [],
        "path": "third_party/rust",
        "subsystem": "thirdparty",
        "variants": []
    },
        "developer_test": {
            "innerapis": [],
            "path": "test/testfwk/developer_test",
            "subsystem": "testfwk",
            "variants": []
        },
        "variants_default": {
        "innerapis": [],
        "path": "variants/variants_default",
        "subsystem": "build",
        "variants": []
        },
    }


def generate_component_package(out_path, root_path, components_list=None, build_type=0, organization_name='ohos',
                               os_arg='linux', build_arch_arg='x86', local_test=0, build_origin=''):
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
        local_test: 1 to open local test , default 0 to close
        build_origin: Origin marker for HPM package
    Returns:

    """
    start_time = time.time()
    components_json = _get_components_json(out_path)
    additional_comoponents_json_data = additional_comoponents_json()
    components_json.update(additional_comoponents_json_data)
    part_subsystem = _get_part_subsystem(components_json)
    parts_path_info = _get_parts_path_info(components_json)
    hpm_packages_path = _make_hpm_packages_dir(root_path)
    toolchain_info = _get_toolchain_info(root_path)

    ### add
    exclusion_list = _get_exclusion_list(root_path)  # 黑名单列表
    # 如果没有提供 components_list，则默认为所有非黑名单组件
    all_components = components_json.keys()
    if local_test == 1:
        components_list = components_list.split(",") if components_list else all_components
    elif local_test == 0:
        if components_list:
            components_list = [component for component in components_list.split(",") if component not in exclusion_list]
        else:
            components_list = [component for component in all_components if component not in exclusion_list]
        # 如果 components_list 为空，则退出程序
        if not components_list:
            sys.exit("stop for no target to pack..")
    print('components_list', components_list)

    # del component_package
    _del_exist_component_package(out_path)
    args = {"out_path": out_path, "root_path": root_path,
            "os": os_arg, "buildArch": build_arch_arg, "hpm_packages_path": hpm_packages_path,
            "build_type": build_type, "organization_name": organization_name,
            "toolchain_info": toolchain_info,
            "static_deps": {},
            "build_origin": build_origin
            }
    for key, value in part_subsystem.items():
        part_name = key
        subsystem_name = value
        if not components_list or part_name in components_list:
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
                               local_test=py_args.local_test,
                               build_origin=py_args.build_origin)


if __name__ == '__main__':
    main()
