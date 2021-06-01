#!/usr/bin/env python3
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

import argparse
import logging
import os
import sys

import build_utils as utils

RM_ASDK_WARNING_TEMPLATE = """
config("remove_asdk_warnings") {
  cflags = []
  if (is_clang) {
    cflags += [
      "-Wno-inconsistent-missing-override",
      "-Wno-thread-safety-analysis",
      "-Wno-thread-safety-attributes",
    ]
  }
}
"""


class CreateBuildGN:
    def __init__(self, out_dir, target_arch_type_list):
        self._out_dir = out_dir
        self._target_arch_type_list = target_arch_type_list

    def _cc_library(self, target_arch_type, library_type, libraries,
                    global_header_dirs):
        module_define = []
        module_define.extend(['import("//build/ohos.gni")\n'])
        module_define.append(RM_ASDK_WARNING_TEMPLATE)

        global_config = False
        if global_header_dirs:
            module_define.append('config("%s_config") {' % library_type)
            module_define.append('  include_dirs = [')
            for h_dir in global_header_dirs:
                module_define.append(
                    '    "../global_header/{}",'.format(h_dir))
            module_define.append('  ]')
            module_define.append('}\n')
            global_config = True

        for lib in libraries:
            module_name = lib.get('name')
            template_type = 'shared'
            if library_type == 'header_library':
                library_type = 'static_library'
            if library_type == 'static_library':
                module_name = '{}_static'.format(module_name)
                template_type = 'static'

            lib_config = False
            include_dir = lib.get('include_dir')
            if include_dir.get(target_arch_type):
                module_define.append('config("%s_config") {' % module_name)
                module_define.append('  include_dirs = [')
                for h_dir in include_dir.get(target_arch_type):
                    module_define.append('    "{}",'.format(
                        os.path.relpath(h_dir, target_arch_type)))
                module_define.append('  ]')
                module_define.append('}\n')
                lib_config = True

            source = lib.get('source')
            if not source.get(target_arch_type):
                continue
            module_define.append('ohos_prebuilt_%s_library("%s") {' %
                                 (template_type, module_name))
            module_define.append('  source = "{}"'.format(
                os.path.relpath(source.get(target_arch_type),
                                target_arch_type)))
            module_define.append('  public_configs = [')
            if RM_ASDK_WARNING_TEMPLATE != '':
                module_define.append('    ":remove_asdk_warnings",')
            if global_config:
                module_define.append('    ":{}_config",'.format(library_type))
            if lib_config:
                module_define.append('    ":{}_config",'.format(module_name))
            module_define.append('  ]')
            module_define.append('  subsystem_name = "a_sdk"')
            module_define.append('  part_name = "a_sdk"')
            module_define.append('}\n')
        return module_define

    def _get_files_from_dir(self, file_dir, suffix=None):
        file_list = []
        for file_name in os.listdir(
                os.path.join(self._out_dir, 'java', file_dir)):
            if suffix and os.path.splitext(file_name)[1] != suffix:
                continue
            file_list.append(os.path.join(file_dir, file_name))
        return file_list

    def _java_library(self, java_libs):
        module_define = []
        module_define.extend(['import("//build/config/ohos/rules.gni")\n'])
        for java_lib in java_libs:
            module_name = java_lib.get('name')
            module_define.append('java_prebuilt("%s_java") {' % module_name)
            module_define.append('  jar_path = "{}"'.format(
                java_lib.get('jar_path')))
            module_define.append('  subsystem_name = "a_sdk"')
            module_define.append('  part_name = "a_sdk"')
            module_define.append('  collect = false')
            module_define.append('}')
            if 'maple_so' in java_lib:
                module_define.append(
                    'ohos_maple_java_prebuilt("%s_maple_java") {' %
                    (module_name))
                module_define.append('  jar_path = "{}"'.format(
                    java_lib.get('jar_path')))
                module_define.append('  so = "{}"'.format(
                    java_lib.get('maple_so')))
                mplt_files = self._get_files_from_dir(java_lib.get('mplt_dir'))
                module_define.append('  mplt = [ "{}" ]'.format(
                    "\",\n    \"".join(mplt_files)))
                module_define.append('}')
            module_define.append('')
        return module_define

    def generate_template(self, module_info_file):
        module_info = utils.read_json_file(module_info_file)
        if module_info is None:
            logging.error('read config file failed or config data incorrect.')
            sys.exit(1)

        global_headers = module_info.get('global_headers')

        shared_libs = module_info.get('shared_library')
        if shared_libs:
            global_header_dirs = None
            if 'shared_library' in global_headers:
                global_header_dirs = global_headers.get('shared_library')
            for _arch_type in self._target_arch_type_list:
                module_define = self._cc_library(_arch_type, 'shared_library',
                                                 shared_libs.values(),
                                                 global_header_dirs)
                gn_build_file = os.path.join(self._out_dir, 'shared_library',
                                             _arch_type, 'BUILD.gn')
                utils.write_file(gn_build_file, '\n'.join(module_define))

        static_libs = module_info.get('static_library')
        if static_libs:
            global_header_dirs = None
            if 'static_library' in global_headers:
                global_header_dirs = global_headers.get('static_library')
            for _arch_type in self._target_arch_type_list:
                module_define = self._cc_library(_arch_type, 'static_library',
                                                 static_libs.values(),
                                                 global_header_dirs)
                gn_build_file = os.path.join(self._out_dir, 'static_library',
                                             _arch_type, 'BUILD.gn')
                utils.write_file(gn_build_file, '\n'.join(module_define))

        java_libs = module_info.get('java_libs')
        if java_libs:
            module_define = self._java_library(java_libs.values())
            gn_build_file = os.path.join(self._out_dir, 'java', 'BUILD.gn')
            utils.write_file(gn_build_file, '\n'.join(module_define))


def _get_support_arch_list(current_arch_type):
    current_arch_list = []
    if current_arch_type == 'arm':
        current_arch_list.extend(['arm64', 'arm'])
    elif current_arch_type == 'x86':
        current_arch_list.append('x86_64')
    return current_arch_list


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--libs-config-file',
                        required=True,
                        help='config file dir')
    parser.add_argument('--out-dir', default='out/a_sdk')
    parser.add_argument('--current-arch-type', default='arm')
    args = parser.parse_args(argv)

    # get source root dir
    root_dir = utils.get_topdir()
    if root_dir is None:
        return 1

    support_arch_list = _get_support_arch_list(args.current_arch_type)
    out_dir = os.path.join(root_dir, args.out_dir)

    libs_config_file = os.path.join(root_dir, args.libs_config_file)
    if not os.path.exists(libs_config_file):
        logging.error(
            "module info config file '{}' not exist.".format(libs_config_file))
        return 1

    gen_build_gn = CreateBuildGN(out_dir, support_arch_list)
    gen_build_gn.generate_template(libs_config_file)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
