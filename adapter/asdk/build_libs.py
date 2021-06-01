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
import shutil
import sys

import build_utils as utils


class GenModuleSDK:
    def __init__(self, product_build_info, root_dir, out_dir, enable_java,
                 java_type_list):
        self._build_info = product_build_info
        self._product_platform = product_build_info.get('TARGET_PRODUCT')
        self._product_arch = product_build_info.get('TARGET_ARCH')
        self._root_dir = root_dir
        self._out_dir = out_dir
        product_out = os.path.join(self._root_dir, 'out/target/product')
        target_device = product_build_info.get('PRODUCT_DEVICE')
        self._product_out_target = os.path.join(product_out, target_device)
        self._product_out_host = os.path.join(self._root_dir,
                                              'out/host/linux-x86/')
        self._enable_java = enable_java
        self._java_type_list = java_type_list
        self._module_info = {}

    def _add_module_info(self, module_name, library_type, info):
        if library_type not in self._module_info:
            self._module_info[library_type] = {}
        self._module_info[library_type][module_name] = info

    def _get_lib_out_path(self, module_name, arch_value, library_type,
                          current_arch):
        config_attr_dict = {}
        if arch_value == 'arm64':
            config_attr_dict['product_out'] = self._product_out_target
            config_attr_dict['lib'] = 'lib64'
            config_attr_dict['obj_target'] = 'obj'
            config_attr_dict['system_vendor'] = 'system'
            config_attr_dict['obj_host'] = ''
        elif arch_value == 'arm':
            config_attr_dict['product_out'] = self._product_out_target
            config_attr_dict['lib'] = 'lib'
            _obj_target = 'obj_arm' if current_arch == 'arm64' else 'obj'
            config_attr_dict['obj_target'] = _obj_target
            config_attr_dict['system_vendor'] = 'system'
            config_attr_dict['obj_host'] = ''
        elif arch_value == 'linux_x86_64':
            config_attr_dict['product_out'] = self._product_out_host
            config_attr_dict['lib'] = 'lib64'
            config_attr_dict['obj_target'] = 'obj'
            config_attr_dict['system_vendor'] = ''
            config_attr_dict['obj_host'] = ''
            config_attr_dict['host_node'] = True
        elif arch_value == 'linux_x86':
            config_attr_dict['product_out'] = self._product_out_host
            config_attr_dict['lib'] = 'lib'
            _obj_target = 'obj32' if current_arch == 'arm64' else 'obj'
            config_attr_dict['obj_target'] = 'obj32'
            config_attr_dict['system_vendor'] = ''
            config_attr_dict['obj_host'] = ''
            config_attr_dict['host_node'] = True

        libraries_dir = 'SHARED_LIBRARIES'
        if library_type == 'static_library':
            libraries_dir = 'STATIC_LIBRARIES'
        elif library_type == 'header_library':
            libraries_dir = 'HEADER_LIBRARIES'

        intermediates_dir = os.path.join(
            config_attr_dict.get('product_out'),
            config_attr_dict.get('obj_target'), libraries_dir,
            '{}_intermediates'.format(module_name))
        return intermediates_dir

    def _copy_cc_library(self, module_name, gn_target_name, library_type,
                         config_library, support_arch_list):
        lib_sources = {}
        lib_header_dir = {}
        _origin_library_type = library_type
        for arch in config_library.get('src'):
            arch_value = arch.get('arch')

            if arch_value not in support_arch_list:
                continue

            src_dir = self._get_lib_out_path(module_name, arch_value,
                                             _origin_library_type,
                                             self._product_arch)

            if library_type == 'header_library':
                library_type = 'static_library'
            dest_dir = os.path.join(self._out_dir, library_type, arch_value)

            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)

            lib_value = arch.get('lib')
            src_file = os.path.join(src_dir, lib_value)
            if not os.path.exists(src_file) or not os.path.isfile(src_file):
                logging.error("{}: file '{}' not exist.".format(
                    module_name, src_file))
                sys.exit(1)
            shutil.copy2(src_file, dest_dir)

            # export_includes
            inter_out_path = os.path.join(self._out_dir, '.inter',
                                          library_type)
            intre_dest_dir = os.path.join(inter_out_path, arch_value,
                                          module_name)
            if not os.path.exists(intre_dest_dir):
                os.makedirs(intre_dest_dir, exist_ok=True)

            export_includes_file = os.path.join(src_dir, "export_includes")
            if os.path.exists(export_includes_file):
                shutil.copy2(export_includes_file, intre_dest_dir)

                header_dest_dir = os.path.join(dest_dir, "include")
                result_header_list = self._parse_copy_export_header(
                    export_includes_file, header_dest_dir)
                lib_header_dir_list = []
                for header_dir in result_header_list:
                    lib_header_dir_list.append(
                        os.path.join(arch_value, 'include', header_dir))
                lib_header_dir[arch_value] = lib_header_dir_list
            # add source
            lib_sources[arch_value] = os.path.join(arch_value, lib_value)

        info = {
            "name": gn_target_name,
            "source": lib_sources,
            "include_dir": lib_header_dir
        }
        self._add_module_info(module_name, library_type, info)

    def _parse_copy_export_header(self, export_includes_file, header_dest_dir):
        if not os.path.exists(export_includes_file):
            return
        header_dir_list = []
        with open(export_includes_file, 'r') as file_obj:
            for line in file_obj.readlines():
                header_dir_list.extend(line.rstrip().split(' '))

        if not os.path.exists(header_dest_dir):
            os.makedirs(header_dest_dir, exist_ok=True)

        result_header_list = []
        for line in header_dir_list:
            if line.startswith('-D'):
                continue
            if line.startswith('-I'):
                header_dir = line[2:]
            else:
                header_dir = line
            if header_dir == '':
                continue
            header_dir_abs = os.path.join(self._root_dir, header_dir)
            if os.path.exists(header_dir_abs) and os.path.isdir(
                    header_dir_abs):
                result_header_list.append(header_dir)
                self._copy_header_dir(
                    header_dir_abs, os.path.join(header_dest_dir, header_dir))
        return result_header_list

    def _copy_header_dir(self, header_file_dir, dest_dir):
        for file_name in os.listdir(header_file_dir):
            if file_name == '.' or file_name == '..':
                continue

            header_file = os.path.join(header_file_dir, file_name)
            if os.path.isfile(header_file) and file_name.endswith('.h'):
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                shutil.copy2(header_file, dest_dir)
            elif os.path.isdir(header_file):
                self._copy_header_dir(header_file,
                                      os.path.join(dest_dir, file_name))
            else:
                continue

    def _copy_java_library(self, module_name, config_jars):
        if len(config_jars) == 0:
            return

        java_out_root_dir = os.path.join(self._out_dir, 'java')
        dest_dir = os.path.join(java_out_root_dir, module_name)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)

        info = {'name': module_name}
        for config_jar in config_jars:
            type_value = config_jar.get('type')
            if type_value not in self._java_type_list:
                continue

            if type_value == 'class':
                lib_value = config_jar.get('lib')
                src_dir = os.path.join(self._root_dir,
                                       'out/target/common/obj/JAVA_LIBRARIES',
                                       '{}_intermediates'.format(module_name))
                src_file = os.path.join(src_dir, lib_value)
                if not os.path.exists(src_file):
                    logging.error(
                        "module '{}' jar class file not exist.".format(
                            module_name))
                    sys.exit(1)
                shutil.copy2(src_file, dest_dir)
                info['jar_path'] = os.path.join(module_name, lib_value)

            if type_value == 'maple_so':
                lib_value = config_jar.get('lib')
                src_dir = os.path.join(
                    self._product_out_target, 'obj', 'SHARED_LIBRARIES',
                    'libmaple{}_intermediates'.format(module_name))
                src_file = os.path.join(src_dir, lib_value)
                if not os.path.exists(src_file):
                    logging.error(
                        "module '{}' maple file '{}' not exist.".format(
                            module_name, lib_value))
                    sys.exit(1)
                shutil.copy2(src_file, dest_dir)

                export_mplts_file = os.path.join(src_dir, 'export_mplts')
                if not os.path.exists(export_mplts_file):
                    logging.error(
                        "module '{}' export_mplts file not exist.".format(
                            module_name))
                    sys.exit(1)
                # copy export_mplts
                inter_out_path = os.path.join(self._out_dir, '.inter', 'java')
                intre_dest_dir = os.path.join(inter_out_path, module_name)
                if not os.path.exists(intre_dest_dir):
                    os.makedirs(intre_dest_dir, exist_ok=True)
                shutil.copy2(export_mplts_file, intre_dest_dir)

                f_list = []
                with open(export_mplts_file, 'r') as mplts_file:
                    for line in mplts_file.readlines():
                        f_list.extend(line.split(','))

                if f_list:
                    mplt_dest_dir = os.path.join(dest_dir, 'mplts')
                    if not os.path.exists(mplt_dest_dir):
                        os.makedirs(mplt_dest_dir, exist_ok=True)
                    for mplt_f in f_list:
                        if mplt_f.strip() == '':
                            continue
                        mplt_file = os.path.join(self._root_dir, mplt_f)
                        if os.path.exists(mplt_file):
                            shutil.copy2(mplt_file, mplt_dest_dir)

                info['maple_name'] = "libmaple{}".format(module_name)
                info['maple_so'] = os.path.join(module_name, lib_value)
                info['mplt_dir'] = os.path.join(module_name, 'mplts')
        self._add_module_info(module_name, "java_libs", info)

    def _copy_host_utility(self, module_name, host_utility):
        if not ('type' in host_utility and host_utility['type']
                in ['executable', 'lib64', 'lib', 'java_library']):
            logging.error(
                "module '{}' configuration error, type incorrect.".format(
                    module_name))
            sys.exit(1)

        if host_utility['type'] == 'executable':
            dest_dir = os.path.join(self._out_dir, 'host/linux-x86/bin')
            src_file = os.path.join(self._root_dir, 'out/host/linux-x86/bin',
                                    host_utility['lib'])
        elif host_utility['type'] == 'lib64':
            dest_dir = os.path.join(self._out_dir, 'host/linux-x86/lib64')
            src_file = os.path.join(self._root_dir, 'out/host/linux-x86/lib64',
                                    host_utility['lib'])
        elif host_utility['type'] == 'lib':
            dest_dir = os.path.join(self._out_dir, 'host/linux-x86/lib')
            src_file = os.path.join(self._root_dir, 'out/host/linux-x86/lib',
                                    host_utility['lib'])
        elif host_utility['type'] == 'java_library':
            if not self._enable_java:
                return
            dest_dir = os.path.join(self._out_dir, 'host/linux-x86/framework')
            src_file = os.path.join(self._root_dir,
                                    'out/host/linux-x86/framework',
                                    host_utility['lib'])
        os.makedirs(dest_dir, exist_ok=True)
        shutil.copy2(src_file, dest_dir)

    def _gen_module_process(self, config_lib, support_arch_list):
        module_name = config_lib.get('name')
        gn_target_name = config_lib.get('gn_target_name')
        if gn_target_name is None:
            gn_target_name = module_name
        if 'shared_library' in config_lib:
            self._copy_cc_library(module_name, gn_target_name, 'shared_library',
                                  config_lib.get('shared_library'),
                                  support_arch_list)
        if 'static_library' in config_lib:
            self._copy_cc_library(module_name, gn_target_name, 'static_library',
                                  config_lib.get('static_library'),
                                  support_arch_list)
        if 'header_library' in config_lib:
            self._copy_cc_library(module_name, gn_target_name, 'header_library',
                                  config_lib.get('header_library'),
                                  support_arch_list)
        if 'host' in config_lib:
            self._copy_host_utility(module_name, config_lib.get('host'))

        if 'java' in config_lib and self._enable_java:
            self._copy_java_library(module_name, config_lib.get('java'))

    def _copy_global_headers(self, global_headers, library_type):
        out_dir = os.path.join(self._out_dir, library_type, 'global_header')
        for global_header_dir in global_headers:
            utils.copy_dir(os.path.join(self._root_dir, global_header_dir),
                           os.path.join(out_dir, global_header_dir))
        if 'global_headers' not in self._module_info:
            self._module_info['global_headers'] = {}
        self._module_info['global_headers'][library_type] = global_headers

    def _rmdir(self):
        libs_out_dir = os.path.join(self._out_dir, 'shared_library')
        if os.path.exists(libs_out_dir):
            shutil.rmtree(libs_out_dir)
        libs_out_dir = os.path.join(self._out_dir, 'static_library')
        if os.path.exists(libs_out_dir):
            shutil.rmtree(libs_out_dir)
        libs_out_dir = os.path.join(self._out_dir, 'java')
        if os.path.exists(libs_out_dir):
            shutil.rmtree(libs_out_dir)

    def generate_modules(self, libs_config_file):
        config_data = utils.read_json_file(libs_config_file)
        if config_data is None:
            logging.error(
                "read config file failed or config data incorrect. file: '{}'".
                format(libs_config_file))
            sys.exit(1)

        target_arch_type = self._build_info.get('TARGET_ARCH_TYPE')
        support_arch_list = utils.get_support_arch_list(
            config_data.get("support_arch"), target_arch_type)

        self._rmdir()
        config_libs = config_data.get('libs')
        for config_lib in config_libs:
            if 'name' not in config_lib:
                logging.error(
                    'lib configuration error, missing name attribute.')
                sys.exit(1)
            self._gen_module_process(config_lib, support_arch_list)

        # copy global header dir
        global_headers = config_data.get('global_headers')
        for library_type in ['shared_library', 'static_library']:
            if os.path.exists(os.path.join(self._out_dir, library_type)):
                self._copy_global_headers(global_headers, library_type)

        utils.write_json_file(os.path.join(self._out_dir, 'module_info.json'),
                              self._module_info,
                              sort_keys=True)
        self._module_info = None


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('action_type', choices=['get-modules', 'gen-modules'])
    parser.add_argument('--product-build-prop-file', required=True)
    parser.add_argument('--libs-config-file',
                        required=True,
                        help='config file')
    parser.add_argument('--out-dir', required=True, default='out/a_sdk')
    parser.add_argument('--enable-java',
                        dest='enable_java',
                        action='store_true')
    parser.set_defaults(enable_java=False)
    args = parser.parse_args(argv)

    # get source root dir
    root_dir = utils.get_topdir()
    if root_dir is None:
        return 1

    product_build_info = utils.parse_product_build_info(
        args.product_build_prop_file)
    if not product_build_info:
        logging.error("read file '{}' failed.".format(
            args.product_build_prop_file))
        return 1

    libs_config_file = args.libs_config_file
    if not os.path.exists(libs_config_file):
        logging.error(
            "libs config file '{}' not exist.".format(libs_config_file))
        return 1

    java_type_list = ['class']
    if args.action_type == 'gen-modules':
        gen_modules = GenModuleSDK(product_build_info, root_dir, args.out_dir,
                                   args.enable_java, java_type_list)
        gen_modules.generate_modules(libs_config_file)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
