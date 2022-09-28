#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) 2020 Huawei Device Co., Ltd.
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

import os
import argparse
import sys

from loader.load import load

from containers.statusCode import StatusCode
from services.interface.loadInterface import LoadInterface
from resources.config import Config

from util.loader import subsystem_info  # noqa: E402
from util.loader import platforms_loader  # noqa: E402
from util.loader import generate_targets_gn  # noqa: E402
from util.loader import load_ohos_build  # noqa: E402
from util.loader import subsystem_scan  # noqa: E402
from scripts.util.file_utils import read_json_file, write_json_file, write_file  # noqa: E402, E501


class LoaderAdapt(LoadInterface):

    def __init__(self, config: Config):
        super().__init__(config)
        self.config = config

    def _create_NameSpace(self) -> argparse.Namespace:
        args_dict = {}
        args_dict['subsystem_config_file'] = os.path.join(
            self.config.root_path, 'out/preloader', self.config.product, 'subsystem_config.json')
        args_dict['platforms_config_file'] = os.path.join(
            self.config.root_path, 'out/preloader', self.config.product, 'platforms.build')
        args_dict['exclusion_modules_config_file'] = os.path.join(
            self.config.root_path, 'out/preloader', self.config.product, 'exclusion_modules.json')
        # origin loader depends on '/' to split path, so we use '/' buf for os.join()
        args_dict['source_root_dir'] = self.config.root_path + '/'
        args_dict['gn_root_out_dir'] = self.config.out_path
        args_dict['build_platform_name'] = 'phone'
        args_dict['build_xts']
        return argparse.Namespace(**args_dict)

    def parse_config(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser()

        parser.add_argument('--subsystem-config-file', required=False)
        _subsystem_config_file = os.path.join(
            self.config.root_path, 'out/preloader', self.config.product, 'subsystem_config.json')
        parser.set_defaults(subsystem_config_file=_subsystem_config_file)

        parser.add_argument('--platforms-config-file', required=False)
        _platforms_config_file = os.path.join(
            self.config.root_path, 'out/preloader', self.config.product, 'platforms.build')
        parser.set_defaults(platforms_config_file=_platforms_config_file)

        parser.add_argument('--example-subsystem-file', required=False)

        parser.add_argument('--exclusion-modules-config-file', required=False)
        _exclusion_modules_config_file = os.path.join(
            self.config.root_path, 'out/preloader', self.config.product, 'exclusion_modules.json')
        parser.set_defaults(
            exclusion_modules_config_file=_exclusion_modules_config_file)

        parser.add_argument('--source-root-dir', required=False)
        _source_root_dir = self.config.root_path + '/'
        parser.set_defaults(source_root_dir=_source_root_dir)

        parser.add_argument('--gn-root-out-dir', default='.')
        _gn_root_out_dir = self.config.out_path
        parser.set_defaults(gn_root_out_dir=_gn_root_out_dir)

        parser.add_argument('--build-platform-name', default='phone')
        parser.add_argument('--build-xts', dest='build_xts',
                            action='store_true', default=False)
        parser.add_argument('--load-test-config',
                            action='store_true', default=True)

        # TODO: resolve Config class default target-os and target-cpu values
        parser.add_argument('--target-os', default='ohos')
        parser.add_argument('--target-cpu', default='arm64')
        _target_cpu = self.config.target_cpu
        parser.set_defaults(target_cpu=_target_cpu)

        parser.add_argument('--os-level', default='standard')
        _os_level = self.config.os_level
        parser.set_defaults(os_level=_os_level)

        parser.add_argument('--ignore-api-check', nargs='*',
                            default=['xts', 'common', 'developertest'])

        parser.add_argument('--scalable-build', action='store_true')
        parser.set_defaults(scalable_build=False)

        return parser.parse_args([])

    def _internel_run(self) -> StatusCode:
        args = self.parse_config()
        return load(args)


class OHOSLoader(LoadInterface):

    def __init__(self, config: Config):
        super().__init__(config)
        self.config = config
        self.subsystem_config_file = os.path.join(
            self.config.root_path, 'out/preloader', self.config.product, 'subsystem_config.json')
        self.platforms_config_file = os.path.join(
            self.config.root_path, 'out/preloader', self.config.product, 'platforms.build')
        self.exclusion_modules_config_file = os.path.join(
            self.config.root_path, 'out/preloader', self.config.product, 'exclusion_modules.json')
        self.source_root_dir = self.config.root_path + '/'

        self.gn_root_out_dir = self.config.out_path
        if self.gn_root_out_dir.startswith('/'):
            self.gn_root_out_dir = os.path.relpath(self.gn_root_out_dir,
                                                   self.config.root_path)

        self.os_level = self.config.os_level if self.config.os_level else "standard"
        self.target_cpu = self.config.target_cpu if self.config.target_cpu else "arm"
        self.target_os = self.config.target_os if self.config.target_os else "ohos"
        self.config_output_relpath = os.path.join(self.gn_root_out_dir, 'build_configs')
        self.config_output_dir = os.path.join(self.source_root_dir, self.config_output_relpath)
        self.target_arch = '{}_{}'.format(self.target_os, self.target_cpu)

        self.example_subsystem_file = os.path.join(
            self.config.root_path, 'build',
            'subsystem_config_example.json')

    def __post_init__(self):

        self.scalable_build = self.args_dict['scalable_build']
        self.build_platform_name = self.args_dict['build_platform_name']
        self.build_xts = self.args_dict['build_xts']
        self.ignore_api_check = self.args_dict['ignore_api_check']
        self.load_test_config = self.args_dict['load_test_config']

        self._subsystem_info = _get_subsystem_info(
            self.subsystem_config_file,
            self.example_subsystem_file,
            self.source_root_dir,
            self.config_output_relpath,
            self.os_level)

        self._platforms_info = platforms_loader.get_platforms_info(
            self.platforms_config_file,
            self.source_root_dir,
            self.gn_root_out_dir,
            self.target_arch,
            self.config_output_relpath,
            self.scalable_build)

        self.variant_toolchains = self._platforms_info.get('variant_toolchain_info').get('platform_toolchain')
        self._all_platforms = self.variant_toolchains.keys()

        if self.build_platform_name == 'all':
            self.build_platforms = self._all_platforms
        elif self.build_platform_name in self._all_platforms:
            self.build_platforms = [self.build_platform_name]
        else:
            raise Exception(
                "The target_platform is incorrect, only allows [{}].".format(
                    ', '.join(self._all_platforms)))

        self.parts_config_info = load_ohos_build.get_parts_info(
            self.source_root_dir,
            self.config_output_relpath,
            self._subsystem_info,
            self.variant_toolchains,
            self.target_arch,
            self.ignore_api_check,
            self.exclusion_modules_config_file,
            self.load_test_config,
            self.build_xts)

        self.parts_targets = self.parts_config_info.get('parts_targets')
        self.parts_info = self.parts_config_info.get('parts_info')
        self.target_platform_parts = _get_platforms_all_parts(
            self.source_root_dir,
            self.target_os,
            self.target_cpu,
            self._platforms_info.get('all_parts'),
            self.build_platforms,
            self.parts_config_info.get('parts_variants'))

        self.target_platform_stubs = _get_platforms_all_stubs(
            self.source_root_dir,
            self.target_os,
            self.target_cpu,
            self._platforms_info.get('all_stubs'),
            self.build_platforms,
            self.parts_config_info.get('parts_variants'))

        self.required_phony_targets = _get_required_build_targets(
            self.parts_config_info.get('phony_target'),
            self.target_platform_parts)

        self.required_parts_targets = _get_required_build_targets(
            self.parts_targets, self.target_platform_parts)

    def _internel_run(self) -> StatusCode:
        
        self.__post_init__()

        _check_parts_config_info(self.parts_config_info)

        _generate_target_platform_parts(self.config_output_dir, self.target_platform_parts)

        _generate_system_capabilities(self.build_platforms, self.config_output_dir, self.target_platform_parts,
                                      self.parts_info)

        generate_targets_gn.gen_stub_targets(
            self.parts_config_info.get('parts_kits_info'),
            self.target_platform_stubs,
            self.config_output_dir)

        # platforms_parts_by_src.json
        _generate_platforms_part_by_src(self.parts_targets, self.source_root_dir, self.config_output_relpath,
                                        self.target_platform_parts)

        generate_targets_gn.gen_targets_gn(self.required_parts_targets,
                                           self.config_output_dir)

        generate_targets_gn.gen_phony_targets(self.required_phony_targets,
                                              self.config_output_dir)

        _generate_build_targets_info(self.config_output_dir, self.required_parts_targets)

        # required_parts_targets_list.json
        _generate_build_target_list(self.config_output_dir, self.required_parts_targets)

        # parts src flag file
        _generate_src_flag(self.config_output_dir, self.required_parts_targets, self.parts_info)

        # write auto install part file
        _generate_auto_install_part(self.parts_config_info, self.config_output_dir)

        # write platforms_list.gni
        _generate_platforms_list(self.config_output_dir, self.build_platforms)

        # parts_different_info.json
        # Generate parts differences in different platforms, using phone as base.
        _generate_part_different_info(self.target_platform_parts, self.config_output_dir)

        # for testfwk
        _output_infos_for_testfwk(self.parts_config_info, self.target_platform_parts,
                                  self.config_output_dir)

        # check part feature
        _check_product_part_feature(self.parts_info,
                                    os.path.dirname(self.platforms_config_file))

        # generate syscap
        pre_syscap_info_path = os.path.dirname(self.platforms_config_file)
        system_path = os.path.join(self.source_root_dir, os.path.join(
            os.path.dirname(self.platforms_config_file), "system/"))
        _generate_syscap_files(
            self.parts_config_info, self.target_platform_parts, pre_syscap_info_path, system_path)

def _load_component_dist(source_root_dir, target_os, target_cpu):
    _parts_variants_info = {}
    _dir = "component_dist/{}-{}/packages_to_install".format(
        target_os, target_cpu)
    _file_name = "dist_parts_info.json"
    _dist_parts_info_file = os.path.join(source_root_dir, _dir, _file_name)
    if not os.path.exists(_dist_parts_info_file):
        # If the file does not exist, do nothing and return
        return _parts_variants_info
    _parts_info = read_json_file(_dist_parts_info_file)
    if _parts_info is None:
        raise Exception("read file '{}' failed.".format(_dist_parts_info_file))
    for _part_info in _parts_info:
        origin_part_name = _part_info.get('origin_part_name')
        if origin_part_name in _parts_variants_info:
            variants = _parts_variants_info.get(origin_part_name)
        else:
            variants = []
        _variant_name = _part_info.get('variant_name')
        variants.append(_variant_name)
        _parts_variants_info[origin_part_name] = variants
    return _parts_variants_info

def _get_real_part_name(original_part_name, current_platform, parts_variants):
    part_info = parts_variants.get(original_part_name)
    if part_info is None:
        return None, None
    if current_platform in part_info and current_platform != 'phone':
        real_name = '{}_{}'.format(original_part_name, current_platform)
    else:
        real_name = original_part_name
    return real_name, original_part_name

def _get_platforms_all_parts(source_root_dir, target_os, target_cpu, all_parts,
                             build_platforms, parts_variants):
    _dist_parts_variants = _load_component_dist(source_root_dir, target_os,
                                                target_cpu)
    target_platform_parts = {}
    for _platform, _parts in all_parts.items():
        if _platform not in build_platforms:
            continue
        part_name_info = {}
        for part_def in _parts:
            real_name, original_name = _get_real_part_name(
                part_def, _platform, parts_variants)
            if real_name is None:
                # find this from component_dist
                real_name, original_name = _get_real_part_name(
                    part_def, _platform, _dist_parts_variants)
            if real_name is None:
                continue
            part_name_info[real_name] = original_name
        target_platform_parts[_platform] = part_name_info
    return target_platform_parts

def _get_platforms_all_stubs(source_root_dir, target_os, target_cpu, all_stubs,
                             build_platforms, parts_variants):
    _dist_parts_variants = _load_component_dist(source_root_dir, target_os,
                                                target_cpu)
    platform_stubs = {}
    for _platform, _part_names in all_stubs.items():
        if _platform not in build_platforms:
            continue
        stub_parts_from_src = []
        stub_parts_from_dist = []
        for part_name in _part_names:
            real_name, original_name = _get_real_part_name(
                part_name, _platform, parts_variants)
            # real_name=None means part_name doesn't exist in source tree,
            # use binary in component_dist then.
            if real_name is None:
                # find this from component_dist
                real_name, original_name = _get_real_part_name(
                    part_name, _platform, _dist_parts_variants)
                if real_name is None:
                    continue
                else:
                    stub_sources = os.path.join(
                        source_root_dir,
                        "component_dist/{}-{}/api_stubs/{}/stubs_sources_list.txt"  # noqa: E501
                        .format(target_os, target_cpu, real_name))
                    stub_parts_from_dist.append('"{}"'.format(stub_sources))
            else:
                stub_parts_from_src.append(real_name)
        platform_stubs[_platform] = {
            "src": stub_parts_from_src,
            "dist": stub_parts_from_dist,
        }
    return platform_stubs

def _get_platforms_parts(src_parts_targets, target_platform_parts):
    platforms_parts = {}
    src_all_parts = src_parts_targets.keys()
    for _platform, _all_parts in target_platform_parts.items():
        src_parts_list = []
        no_src_parts_list = []
        for _part in _all_parts.keys():
            if _part in src_all_parts:
                src_parts_list.append(_part)
            else:
                no_src_parts_list.append(_part)
        _data = {
            'src_parts': src_parts_list,
            'no_src_parts': no_src_parts_list
        }
        platforms_parts[_platform] = _data
    return platforms_parts

def _get_parts_by_platform(target_platform_parts):
    parts_info = {}
    if 'phone' in target_platform_parts:
        phone_parts_list = target_platform_parts.get('phone').keys()
    else:
        phone_parts_list = []
    for _platform, _parts_info in target_platform_parts.items():
        base_parts_list = []
        curr_parts_list = []
        for _real_name, _original_name in _parts_info.items():
            if _real_name in phone_parts_list:
                base_parts_list.append(_real_name)
            elif _original_name in phone_parts_list:
                base_parts_list.append(_real_name)
            else:
                curr_parts_list.append(_real_name)
        result_data = {
            "base_parts_list": base_parts_list,
            "curr_parts_list": curr_parts_list
        }
        parts_info[_platform] = result_data
    return parts_info

def _check_parts_config_info(parts_config_info):
    if not ('parts_info' in parts_config_info and
            'subsystem_parts' in parts_config_info
            and 'parts_variants' in parts_config_info
            and 'parts_kits_info' in parts_config_info
            and 'parts_inner_kits_info' in parts_config_info
            and 'parts_targets' in parts_config_info):
        raise Exception("Loading ohos.build information is incorrect.")

def _get_required_build_parts_list(target_platform_parts):
    parts_set = set()
    for _parts_list in target_platform_parts.values():
        parts_set.update(_parts_list)
    return list(parts_set)

def _get_required_build_targets(parts_targets, target_platform_parts):
    required_build_targets = {}
    _parts_list = _get_required_build_parts_list(target_platform_parts)
    for _p_name, _info in parts_targets.items():
        if _p_name not in _parts_list:
            continue
        required_build_targets[_p_name] = _info
    return required_build_targets

def _get_auto_install_list(parts_path_info):
    auto_install_part_list = []
    for part, path in parts_path_info.items():
        if str(path).startswith("drivers/interface") or \
                str(path).startswith("third_party"):
            auto_install_part_list.append(part)
    return auto_install_part_list

def _get_parts_src_list(required_parts_targets, parts_info):
    parts_name_map = {}
    for _list in parts_info.values():
        for _info in _list:
            parts_name_map[_info.get('part_name')] = _info.get(
                'origin_part_name')
    _src_set = set()
    for _name in required_parts_targets.keys():
        _origin_name = parts_name_map.get(_name)
        if _origin_name is None:
            continue
        _src_set.add(_origin_name)
    return list(_src_set)

def _check_product_part_feature(parts_info, product_preloader_dir):
    _preloader_feature_file = os.path.join(product_preloader_dir,
                                           'features.json')
    _preloader_feature_info = read_json_file(_preloader_feature_file)
    part_to_feature = _preloader_feature_info.get('part_to_feature')
    for key, vals in part_to_feature.items():
        part = parts_info.get(key)
        if part is None:
            continue
        _p_info = part[0]
        def_feature_list = _p_info.get('feature_list')
        if not def_feature_list:
            continue
        for _f_name in vals:
            if _f_name not in def_feature_list:
                raise Exception(
                    "The product use a feature that is not supported"
                    " by this part, part_name='{}', feature='{}'".format(
                        key, _f_name))

def _check_args(args, source_root_dir):
    print('args:', args)
    if 'gn_root_out_dir' not in args:
        raise Exception("args gn_root_out_dir is required.")
    if 'platforms_config_file' not in args:
        raise Exception("args platforms_config_file is required.")
    if 'subsystem_config_file' not in args:
        raise Exception("args subsystem_config_file is required.")
    gn_root_out_dir = args.gn_root_out_dir
    if gn_root_out_dir.startswith('/'):
        args.gn_root_out_dir = os.path.relpath(args.gn_root_out_dir,
                                               source_root_dir)
    else:
        _real_out_dir = os.path.realpath(gn_root_out_dir)
        if not _real_out_dir.startswith(source_root_dir):
            raise Exception("args gn_root_out_dir is incorrect.")

def syscap_sort(syscap):
    return syscap['component']

'''Description: Generate SystemCapability.json & syscap.json & syscap.para
@parameter:parts config info, target platform parts, pre syscap info path, system path
@return :none
'''
def _generate_syscap_files(parts_config_info, target_platform_parts, pre_syscap_info_path, system_path):
    syscap_product_dict = read_json_file(
        os.path.join(pre_syscap_info_path, "syscap.json"))
    target_parts_list = _get_required_build_parts_list(target_platform_parts)
    syscap_info_list = parts_config_info.get('syscap_info')
    target_syscap_with_part_name_list = []
    target_syscap_list = []
    target_syscap_for_init_list = []
    all_syscap_list = []
    for syscap in syscap_info_list:
        if syscap['component'] not in target_parts_list:
            continue
        if 'syscap' not in syscap or syscap['syscap'] == None or len(syscap['syscap']) == 0 or syscap['syscap'] == [""]:
            continue
        for syscap_string in syscap['syscap']:
            all_syscap_list.append(syscap_string.split('=')[0].strip())

    for key, value in syscap_product_dict['part_to_syscap'].items():
        for syscap in value:
            if syscap not in all_syscap_list:
                raise Exception(
                    "In config.json of part [{}],the syscap[{}] is incorrect, \
                    please check the syscap name".format(key, syscap))

    for syscap in syscap_info_list:
        remove_list = []
        if syscap['component'] not in target_parts_list:
            continue
        if 'syscap' not in syscap or syscap['syscap'] == None or len(syscap['syscap']) == 0 or syscap['syscap'] == [""]:
            continue
        for syscap_string in syscap['syscap']:
            if syscap_string.startswith("SystemCapability.") == True:
                target_syscap_init_str = "const."
                syscap_name = syscap_string.split('=')[0].strip()
                all_syscap_product = syscap_product_dict['syscap']
                if syscap_name in all_syscap_product and not all_syscap_product[syscap_name]:
                    remove_list.append(syscap_string)
                    continue
                elif syscap_name in all_syscap_product and all_syscap_product[syscap_name]:
                    target_syscap_init_str += syscap_name + '=true\n'
                else:
                    if syscap_string.endswith('true'):
                        target_syscap_init_str += syscap_name + '=true\n'
                    elif syscap_string.endswith('false'):
                        remove_list.append(syscap_string)
                        continue
                    else:
                        target_syscap_init_str += syscap_string + "=true\n"
                if target_syscap_init_str not in target_syscap_for_init_list:
                    target_syscap_for_init_list.append(target_syscap_init_str)
            else:
                raise Exception("""In bundle.json of part [{}], The syscap string [{}] is incorrect,
                 need start with \"SystemCapability.\"""".format(syscap['component'], syscap_string))

        for remove_str in remove_list:
            syscap['syscap'].remove(remove_str)
        for i in range(len(syscap['syscap'])):
            if syscap['syscap'][i].endswith('true') or syscap['syscap'][i].endswith('false'):
                syscap['syscap'][i] = syscap['syscap'][i].split('=')[0].strip()

        syscap['syscap'].sort()
        target_syscap_with_part_name_list.append(syscap)
        target_syscap_list.extend(syscap['syscap'])

    # Generate SystemCapability.json & syscap.json & syscap.para
    target_syscap_list.sort()
    syscap_info_dict = read_json_file(os.path.join(
        pre_syscap_info_path, "SystemCapability.json"))
    syscap_info_dict.update({'syscap': {'os': target_syscap_list}})
    system_etc_path = os.path.join(system_path, "etc/")
    if not os.path.exists(system_path):
        os.mkdir(system_path)
    if not os.path.exists(system_etc_path):
        os.mkdir(system_etc_path)
    syscap_info_json = os.path.join(system_etc_path, "SystemCapability.json")
    write_json_file(syscap_info_json, syscap_info_dict)
    target_syscap_with_part_name_list.sort(key=syscap_sort)
    syscap_info_with_part_name_file = os.path.join(
        system_etc_path, "syscap.json")
    write_json_file(syscap_info_with_part_name_file, {
        'components': target_syscap_with_part_name_list})
    if not os.path.exists(os.path.join(system_etc_path, "param/")):
        os.mkdir(os.path.join(system_etc_path, "param/"))
    target_syscap_for_init_file = os.path.join(
        system_etc_path, "param/syscap.para")
    f = open(target_syscap_for_init_file, "w")
    f.writelines(target_syscap_for_init_list)
    f.close()

'''Description: called by _out_infos_for_testfwk, output information by platform
@parameter:part name information, part name information
@return :none
'''
def _output_infos_by_platform(part_name_infos, parts_info_dict):
    required_parts = {}
    subsystem_infos = {}
    for part_name, origin_part_name in part_name_infos.items():
        part_info = parts_info_dict.get(part_name)
        if part_info is None:
            continue
        if origin_part_name != part_info.get('origin_part_name'):
            raise Exception("part configuration is incorrect.")
        required_parts[origin_part_name] = part_info
        _subsystem_name = part_info.get('subsystem_name')
        if _subsystem_name in subsystem_infos:
            p_list = subsystem_infos.get(_subsystem_name)
        else:
            p_list = []
        p_list.append(origin_part_name)
        subsystem_infos[_subsystem_name] = p_list
    result = {}
    result['subsystem_infos'] = subsystem_infos
    result['part_infos'] = required_parts
    return result

'''Description: output infos for testfwk into a json file(/out/${product_name}/build_configs/infos_for_testfwk.json)
@parameter:config output directory, target platform parts, parts config information
@return :none
'''
def _output_infos_for_testfwk(parts_config_info, target_platform_parts,
                              config_output_dir):
    infos_for_testfwk_file = os.path.join(config_output_dir,
                                            "infos_for_testfwk.json")
    parts_info = parts_config_info.get('parts_info')
    parts_info_dict = {}
    for _part_name, _parts in parts_info.items():
        for _info in _parts:
            parts_info_dict[_info.get('part_name')] = _info
    _output_infos = {}
    for _platform, _parts in target_platform_parts.items():
        result = _output_infos_by_platform(_parts, parts_info_dict)
        _output_infos[_platform] = result
    write_json_file(infos_for_testfwk_file, _output_infos, check_changes=True)

'''Description: output all target platform parts into a json file(/out/${product_name}/build_configs/target_platforms_parts.json)
@parameter:config output directory, target platform parts
@return :none
'''
def _generate_target_platform_parts(config_output_dir, target_platform_parts):
    target_platform_parts_file = os.path.join(config_output_dir,
                                            "target_platforms_parts.json")
    write_json_file(target_platform_parts_file,
                    target_platform_parts,
                    check_changes=True)
    
'''Description: Generate parts differences in different platforms, using phone as base.(/out/${product_name}/build_configs/parts_different_info.json)
@parameter: target platform parts, config output directory
@return :none
'''
def _generate_part_different_info(target_platform_parts, config_output_dir):
    parts_different_info = _get_parts_by_platform(target_platform_parts)
    parts_different_info_file = os.path.join(config_output_dir,
                                            "parts_different_info.json")
    write_json_file(parts_different_info_file,
                    parts_different_info,
                    check_changes=True)

'''Description: output platforms list into a gni file.(/out/${product_name}/build_configs/platforms_list.gni)
@parameter: build platforms, config output directory
@return :none
'''
def _generate_platforms_list(config_output_dir, build_platforms):
    platforms_list_gni_file = os.path.join(config_output_dir,
                                            "platforms_list.gni")
    _platforms = set(build_platforms)
    _gni_file_content = ['target_platform_list = [', '  "{}"'.format('",\n  "'.join(_platforms)), ']',
                         'kits_platform_list = [', '  "{}",'.format('",\n  "'.join(_platforms))]
    if 'phone' not in build_platforms:
        _gni_file_content.append('  "phone"')
    _gni_file_content.append(']')
    write_file(platforms_list_gni_file, '\n'.join(_gni_file_content))

'''Description: output auto install part into a json file.(/out/${product_name}/build_configs/auto_install_parts.json)
@parameter: parts config information, config output directory
@return :none
'''
def _generate_auto_install_part(parts_config_info, config_output_dir):
    auto_install_list = _get_auto_install_list(
        parts_config_info.get("parts_path_info"))
    auto_install_list_file = os.path.join(
        config_output_dir, "auto_install_parts.json")
    write_json_file(auto_install_list_file, auto_install_list)

'''Description: output src flag into a json file.(/out/${product_name}/build_configs/parts_src_flag.json)
@parameter: parts information, config output directory, required parts targets
@return :none
'''
def _generate_src_flag(config_output_dir, required_parts_targets, parts_info):
    parts_src_flag_file = os.path.join(config_output_dir,
                                        "parts_src_flag.json")
    write_json_file(parts_src_flag_file,
                    _get_parts_src_list(required_parts_targets, parts_info),
                    check_changes=True)

'''Description: output build target list into a json file.(/out/${product_name}/build_configs/required_parts_targets_list.json)
@parameter: required parts targets, config output directory
@return :none
'''
def _generate_build_target_list(config_output_dir, required_parts_targets):
    build_targets_list_file = os.path.join(config_output_dir,
                                        "required_parts_targets_list.json")
    write_json_file(build_targets_list_file,
                    list(required_parts_targets.values()))

'''Description: output build target info into a json file.(/out/${product_name}/build_configs/required_parts_targets.json)
@parameter: required parts targets, config output directory
@return :none
'''
def _generate_build_targets_info(config_output_dir, required_parts_targets):
    build_targets_info_file = os.path.join(config_output_dir,
                                           "required_parts_targets.json")
    write_json_file(build_targets_info_file, required_parts_targets)

'''Description: output platforms part by src into a json file.(/out/${product_name}/build_configs/platforms_parts_by_src.json)
@parameter: parts targets, source root directopry, config output relpath, target platform parts
@return :none
'''
def _generate_platforms_part_by_src(parts_targets, source_root_dir, config_output_relpath, target_platform_parts):
    platforms_parts_by_src = _get_platforms_parts(parts_targets,
                                                  target_platform_parts)
    platforms_parts_by_src_file = os.path.join(source_root_dir,
                                               config_output_relpath,
                                               "platforms_parts_by_src.json")
    write_json_file(platforms_parts_by_src_file,
                    platforms_parts_by_src,
                    check_changes=True)

'''Description: output system capabilities into a json file.(/out/${product_name}/build_configs/${platform}_system_capabilities.json)
@parameter: parts targets, source root directopry, config output relpath, target platform parts
@return :none
'''
def _generate_system_capabilities(build_platforms, config_output_dir, target_platform_parts, parts_info):
    for platform in build_platforms:
        platform_parts = target_platform_parts.get(platform)
        platform_capabilities = []
        for _, origin in platform_parts.items():
            # parts_info.get() might be None if the part is a binary package
            all_parts_variants = parts_info.get(origin)
            if all_parts_variants is None:
                continue
            part = all_parts_variants[0]
            if part.get('system_capabilities'):
                entry = part.get('system_capabilities')
                if len(entry) > 0:
                    platform_capabilities.extend(entry)
        platform_part_json_file = os.path.join(
            config_output_dir, "{0}_system_capabilities.json".format(platform))
        write_json_file(platform_part_json_file,
                        sorted(platform_capabilities),
                        check_changes=True)

def _generate_subsystem_configs(output_dir, subsystem_configs):
    build_config_file = os.path.join(output_dir, 'subsystem_info',
                                     "subsystem_build_config.json")
    write_json_file(build_config_file, subsystem_configs)

    src_subsystem = {}
    for key, val in subsystem_configs.get('subsystem').items():
        src_subsystem[key] = val.get('path')
    src_output_file = os.path.join(output_dir, 'subsystem_info',
                                   "src_subsystem_info.json")
    write_json_file(src_output_file, src_subsystem)

    no_src_output_file = os.path.join(output_dir, 'subsystem_info',
                                      "no_src_subsystem_info.json")
    write_json_file(no_src_output_file,
                    subsystem_configs.get('no_src_subsystem'))

def _get_subsystem_info(subsystem_config_file, example_subsystem_file,
                        source_root_dir, config_output_relpath, os_level):
    if not subsystem_config_file:
        subsystem_config_file = 'build/subsystem_config.json'

    subsystem_configs = {}
    output_dir_realpath = os.path.join(source_root_dir, config_output_relpath)
    subsystem_configs = subsystem_scan.scan(subsystem_config_file,
                                            example_subsystem_file,
                                            source_root_dir)

    _generate_subsystem_configs(output_dir_realpath, subsystem_configs)
    return subsystem_configs.get('subsystem')