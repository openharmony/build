#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) 2023 Huawei Device Co., Ltd.
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

from services.interface.load_interface import LoadInterface
from containers.status import throw_exception
from exceptions.ohos_exception import OHOSException
from util.loader import platforms_loader  # noqa: E402
from util.loader import generate_targets_gn  # noqa: E402
from util.loader import load_ohos_build  # noqa: E402
from util.loader import subsystem_scan  # noqa: E402
from util.loader import subsystem_info  # noqa: E402
from scripts.util.file_utils import read_json_file, write_json_file, write_file  # noqa: E402, E501
from util.log_util import LogUtil


class OHOSLoader(LoadInterface):

    def __init__(self):
        super().__init__()
        self.source_root_dir = ""
        self.gn_root_out_dir = ""
        self.os_level = ""
        self.target_cpu = ""
        self.target_os = ""
        self.config_output_relpath = ""
        self.config_output_dir = ""
        self.target_arch = ""
        self.subsystem_config_file = ""
        self.subsystem_config_overlay_file = ""
        self.platforms_config_file = ""
        self.exclusion_modules_config_file = ""
        self.example_subsystem_file = ""
        self.build_example = ""
        self.scalable_build = ""
        self.build_platform_name = ""
        self.build_xts = ""
        self.ignore_api_check = ""
        self.load_test_config = ""
        self.subsystem_configs = ""
        self._subsystem_info = ""

    def __post_init__(self):
        self.source_root_dir = self.config.root_path + '/'
        self.gn_root_out_dir = self.config.out_path if not self.config.out_path.startswith(
            '/') else os.path.relpath(self.config.out_path, self.config.root_path)
        self.os_level = self.config.os_level if self.config.os_level else "standard"
        self.target_cpu = self.config.target_cpu if self.config.target_cpu else "arm"
        self.target_os = self.config.target_os if self.config.target_os else "ohos"
        self.config_output_relpath = os.path.join(
            self.gn_root_out_dir, 'build_configs')
        self.config_output_dir = os.path.join(
            self.source_root_dir, self.config_output_relpath)
        self.target_arch = '{}_{}'.format(self.target_os, self.target_cpu)
        self.subsystem_config_file = os.path.join(
            self.config.root_path, 'out/preloader', self.config.product, 'subsystem_config.json')
        self.platforms_config_file = os.path.join(
            self.config.root_path, 'out/preloader', self.config.product, 'platforms.build')
        self.exclusion_modules_config_file = os.path.join(
            self.config.root_path, 'out/preloader', self.config.product, 'exclusion_modules.json')
        self.example_subsystem_file = os.path.join(
            self.config.root_path, 'build', 'subsystem_config_example.json')

        # check config args
        self._check_args()

        self.build_example = self.args_dict.get('build_example')
        if not self.build_example:
            self.example_subsystem_file = ""
        self.scalable_build = self.args_dict.get('scalable_build')
        self.build_platform_name = self.args_dict.get('build_platform_name')
        self.build_xts = self.args_dict.get('build_xts')
        self.ignore_api_check = self.args_dict.get('ignore_api_check')
        self.load_test_config = self.args_dict.get('load_test_config')
        self.subsystem_configs = subsystem_scan.scan(self.subsystem_config_file,
                                                     self.example_subsystem_file,
                                                     self.source_root_dir)

        self._subsystem_info = subsystem_info.get_subsystem_info(
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
        self.variant_toolchains = self._platforms_info.get(
            'variant_toolchain_info').get('platform_toolchain')
        self._all_platforms = self.variant_toolchains.keys()
        self.build_platforms = self._get_build_platforms()
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
        self.phony_targets = self.parts_config_info.get('phony_target')
        self.parts_info = self.parts_config_info.get('parts_info')
        self.target_platform_parts = self._get_platforms_all_parts()
        self.target_platform_stubs = self._get_platforms_all_stubs()
        self.required_parts_targets_list = self._get_required_build_parts_list()
        self.required_phony_targets = self._get_required_phony_targets()
        self.required_parts_targets = self._get_required_build_targets()

# check method

    '''Description: Check the parameters passed in config. If the parameters are not 
                    specified or the file content pointed to by the parameters does not 
                    exist, an exception will be thrown directly.
    @parameter:none
    @return :none
    '''
    @throw_exception
    def _check_args(self):
        LogUtil.hb_info("Checking all build args...")
        # check subsystem_config_file
        if not read_json_file(self.subsystem_config_file):
            self.subsystem_config_file = os.path.join(
                self.source_root_dir, 'build/subsystem_config.json')
        if not read_json_file(self.subsystem_config_file):
            raise OHOSException("Cannot get the content from platform config file, \
                            please check whether the corresponding file('out/preloader/{}/subsystem_config.json' or \
                            'build/subsystem_config.json') is written correctly.".format(self.config.product), "2001")

        # check gn_root_out_dir
        if not self.gn_root_out_dir:
            raise OHOSException("Args gn_root_out_dir is required.", "2002")
        if not os.path.realpath(self.gn_root_out_dir).startswith(self.source_root_dir):
            raise OHOSException("Args gn_root_out_dir is incorrect.", "2003")

        # check platform config file
        if not read_json_file(self.platforms_config_file):
            raise OHOSException("Cannot get the content from platform config file, \
                            please check whether the corresponding file('out/preloader/${product_name}/platforms.build') \
                            is written correctly.".format(self.config.product), "2004")

        # check example subsystem file
        if not read_json_file(self.example_subsystem_file):
            raise OHOSException("Cannot get the content from example subsystem file, please check whether \
                                the corresponding file ('build/subsystem_config_example.json') exists.", "2005")

    @throw_exception
    def _check_product_part_feature(self):
        LogUtil.hb_info("Checking all product features...")
        product_preloader_dir = os.path.dirname(self.platforms_config_file)
        _preloader_feature_file = os.path.join(product_preloader_dir,
                                               'features.json')
        _preloader_feature_info = read_json_file(_preloader_feature_file)
        part_to_feature = _preloader_feature_info.get('part_to_feature')
        for key, vals in part_to_feature.items():
            part = self.parts_info.get(key)
            if part is None:
                continue
            _p_info = part[0]
            def_feature_list = _p_info.get('feature_list')
            if not def_feature_list:
                continue
            for _f_name in vals:
                if _f_name not in def_feature_list:
                    raise OHOSException(
                        "The product use a feature that is not supported"
                        " by this part, part_name='{}', feature='{}'".format(
                            key, _f_name), "2006")

    @throw_exception
    def _check_parts_config_info(self):
        LogUtil.hb_info("Checking parts config...")
        if not ('parts_info' in self.parts_config_info
                and 'subsystem_parts' in self.parts_config_info
                and 'parts_variants' in self.parts_config_info
                and 'parts_kits_info' in self.parts_config_info
                and 'parts_inner_kits_info' in self.parts_config_info
                and 'parts_targets' in self.parts_config_info):
            raise OHOSException(
                "Loading ohos.build information is incorrect.", "2007")

# generate method

    '''Description: Generate SystemCapability.json & syscap.json & syscap.para, dir:[
        (//out/preloader/${product_name}/system/etc/SystemCapability.json),
        (//out/preloader/${product_name}/system/etc/syscap.json),
        (//out/preloader/${product_name}/system/etc/param/syscap.para)]
    @parameter:none
    @return :none
    '''
    @throw_exception
    def _generate_syscap_files(self):
        pre_syscap_info_path = os.path.dirname(self.platforms_config_file)
        system_path = os.path.join(self.source_root_dir, os.path.join(
            os.path.dirname(self.platforms_config_file), "system/"))
        syscap_product_dict = read_json_file(
            os.path.join(pre_syscap_info_path, "syscap.json"))
        syscap_info_list = self.parts_config_info.get('syscap_info')
        target_syscap_with_part_name_list = []
        target_syscap_list = []
        target_syscap_for_init_list = []
        all_syscap_list = []
        for syscap in syscap_info_list:
            if syscap['component'] not in self.required_parts_targets_list:
                continue
            if 'syscap' not in syscap or syscap['syscap'] is None \
                    or len(syscap['syscap']) == 0 or syscap['syscap'] == [""]:
                continue
            for syscap_string in syscap['syscap']:
                all_syscap_list.append(syscap_string.split('=')[0].strip())

        for key, value in syscap_product_dict['part_to_syscap'].items():
            for syscap in value:
                if syscap not in all_syscap_list:
                    raise OHOSException(
                        "In config.json of part [{}],the syscap[{}] is incorrect, \
                        please check the syscap name".format(key, syscap), "2008")

        for syscap in syscap_info_list:
            remove_list = []
            if syscap['component'] not in self.required_parts_targets_list:
                continue
            if 'syscap' not in syscap or syscap['syscap'] is None \
                    or len(syscap['syscap']) == 0 or syscap['syscap'] == [""]:
                continue
            for syscap_string in syscap['syscap']:
                if syscap_string.startswith("SystemCapability.") is True:
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
                        target_syscap_for_init_list.append(
                            target_syscap_init_str)
                else:
                    raise OHOSException("""In bundle.json of part [{}], The syscap string [{}] is incorrect,
                    need start with \"SystemCapability.\"""".format(syscap['component'], syscap_string), "2009")

            for remove_str in remove_list:
                syscap['syscap'].remove(remove_str)
            for i in range(len(syscap['syscap'])):
                if syscap['syscap'][i].endswith('true') or syscap['syscap'][i].endswith('false'):
                    syscap['syscap'][i] = syscap['syscap'][i].split('=')[
                        0].strip()

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
        syscap_info_json = os.path.join(
            system_etc_path, "SystemCapability.json")
        write_json_file(syscap_info_json, syscap_info_dict)
        LogUtil.hb_info(
            "generate syscap info file to '{}'".format(syscap_info_json))
        target_syscap_with_part_name_list.sort(
            key=lambda syscap: syscap['component'])
        syscap_info_with_part_name_file = os.path.join(
            system_etc_path, "syscap.json")
        write_json_file(syscap_info_with_part_name_file, {
            'components': target_syscap_with_part_name_list})
        LogUtil.hb_info("generate syscap info with part name list to '{}'".format(
            syscap_info_with_part_name_file))
        if not os.path.exists(os.path.join(system_etc_path, "param/")):
            os.mkdir(os.path.join(system_etc_path, "param/"))
        target_syscap_for_init_file = os.path.join(
            system_etc_path, "param/syscap.para")
        file = open(target_syscap_for_init_file, "w")
        file.writelines(target_syscap_for_init_list)
        file.close()
        LogUtil.hb_info("generate target syscap for init list to '{}'".format(
            target_syscap_for_init_file))

    '''Description: output infos for testfwk into a json file. \
        (/out/${product_name}/build_configs/infos_for_testfwk.json)
    @parameter:none
    @return :none
    '''

    def _generate_infos_for_testfwk(self):
        infos_for_testfwk_file = os.path.join(self.config_output_dir,
                                              "infos_for_testfwk.json")
        parts_info = self.parts_config_info.get('parts_info')
        parts_info_dict = {}
        for _part_name, _parts in parts_info.items():
            for _info in _parts:
                parts_info_dict[_info.get('part_name')] = _info
        _output_infos = {}
        for _platform, _parts in self.target_platform_parts.items():
            result = self._output_infos_by_platform(_parts, parts_info_dict)
            _output_infos[_platform] = result
        write_json_file(infos_for_testfwk_file,
                        _output_infos, check_changes=True)
        LogUtil.hb_info("generate infos for testfwk to '{}'".format(
            infos_for_testfwk_file))

    '''Description: output all target platform parts into a json file \
        (/out/${product_name}/build_configs/target_platforms_parts.json)
    @parameter:none
    @return :none
    '''

    def _generate_target_platform_parts(self):
        target_platform_parts_file = os.path.join(self.config_output_dir,
                                                  "target_platforms_parts.json")
        write_json_file(target_platform_parts_file,
                        self.target_platform_parts,
                        check_changes=True)
        LogUtil.hb_info("generate target platform parts to '{}'".format(
            target_platform_parts_file))

    '''Description: Generate parts differences in different platforms, using phone as base. \
        (/out/${product_name}/build_configs/parts_different_info.json)
    @parameter: none
    @return :none
    '''

    def _generate_part_different_info(self):
        parts_different_info = self._get_parts_by_platform()
        parts_different_info_file = os.path.join(self.config_output_dir,
                                                 "parts_different_info.json")
        write_json_file(parts_different_info_file,
                        parts_different_info,
                        check_changes=True)
        LogUtil.hb_info("generate part different info to '{}'".format(
            parts_different_info_file))

    '''Description: output platforms list into a gni file. \
        (/out/${product_name}/build_configs/platforms_list.gni)
    @parameter: none
    @return: none
    '''

    def _generate_platforms_list(self):
        platforms_list_gni_file = os.path.join(self.config_output_dir,
                                               "platforms_list.gni")
        _platforms = set(self.build_platforms)
        _gni_file_content = ['target_platform_list = [', '  "{}"'.format('",\n  "'.join(_platforms)), ']',
                             'kits_platform_list = [', '  "{}",'.format('",\n  "'.join(_platforms))]
        if 'phone' not in self.build_platforms:
            _gni_file_content.append('  "phone"')
        _gni_file_content.append(']')
        write_file(platforms_list_gni_file, '\n'.join(_gni_file_content))
        LogUtil.hb_info("generate platforms list to '{}'".format(
            platforms_list_gni_file))

    '''Description: output auto install part into a json file. \
        (/out/${product_name}/build_configs/auto_install_parts.json)
    @parameter: none
    @return: none
    '''

    def _generate_auto_install_part(self):
        parts_path_info = self.parts_config_info.get("parts_path_info")
        auto_install_part_list = []
        for part, path in parts_path_info.items():
            if str(path).startswith("drivers/interface") or \
                    str(path).startswith("third_party"):
                auto_install_part_list.append(part)
        auto_install_list_file = os.path.join(
            self.config_output_dir, "auto_install_parts.json")
        write_json_file(auto_install_list_file, auto_install_part_list)
        LogUtil.hb_info("generate auto install part to '{}'".format(
            auto_install_list_file))

    '''Description: output src flag into a json file. \
        (/out/${product_name}/build_configs/parts_src_flag.json)
    @parameter: none
    @return :none
    '''

    def _generate_src_flag(self):
        parts_src_flag_file = os.path.join(self.config_output_dir,
                                           "parts_src_flag.json")
        write_json_file(parts_src_flag_file,
                        self._get_parts_src_list(),
                        check_changes=True)
        LogUtil.hb_info(
            "generated parts src flag to '{}/subsystem_info/parts_src_flag.json'".format(self.config_output_dir))

    '''Description: output build target list into a json file.\
        (/out/${product_name}/build_configs/required_parts_targets_list.json)
    @parameter: none
    @return :none
    '''

    def _generate_required_parts_targets_list(self):
        build_targets_list_file = os.path.join(self.config_output_dir,
                                               "required_parts_targets_list.json")
        write_json_file(build_targets_list_file,
                        list(self.required_parts_targets.values()))
        LogUtil.hb_info("generate build targets list file to '{}'".format(
            build_targets_list_file))

    '''Description: output build target info into a json file. \
        (/out/${product_name}/build_configs/required_parts_targets.json)
    @parameter: none
    @return: none
    '''

    def _generate_required_parts_targets(self):
        build_targets_info_file = os.path.join(self.config_output_dir,
                                               "required_parts_targets.json")
        write_json_file(build_targets_info_file, self.required_parts_targets)
        LogUtil.hb_info("generate required parts targets to '{}'".format(
            build_targets_info_file))

    '''Description: output platforms part by src into a json file. \
        (/out/${product_name}/build_configs/platforms_parts_by_src.json)
    @parameter: none
    @return :none
    '''

    def _generate_platforms_part_by_src(self):
        platforms_parts_by_src = self._get_platforms_parts()
        platforms_parts_by_src_file = os.path.join(self.source_root_dir,
                                                   self.config_output_relpath,
                                                   "platforms_parts_by_src.json")
        write_json_file(platforms_parts_by_src_file,
                        platforms_parts_by_src,
                        check_changes=True)
        LogUtil.hb_info("generated platforms parts by src to '{}'".format(
            platforms_parts_by_src_file))

    '''Description: output system configs info into 4 files:[
        (/out/${product_name}/build_configs/subsystem_info/parts_list.gni),
        (/out/${product_name}/build_configs/subsystem_info/inner_kits_list.gni),
        (/out/${product_name}/build_configs/subsystem_info/system_kits_list.gni),
        (/out/${product_name}/build_configs/subsystem_info/parts_test_list.gni),
        (/out/${product_name}/build_configs/subsystem_info/BUILD.gn)]
    @parameter: none
    @return :none
    '''

    def _generate_target_gn(self):
        generate_targets_gn.gen_targets_gn(self.required_parts_targets,
                                           self.config_output_dir)

    '''Description: output phony targets build file. \
        (/out/${product_name}/build_configs/phony_target/BUILD.gn)
    @parameter: none
    @return :none
    '''

    def _generate_phony_targets_build_file(self):
        generate_targets_gn.gen_phony_targets(self.required_phony_targets,
                                              self.config_output_dir)

    '''Description: output system configs info into 2 files:[
        (/out/${product_name}/build_configs/subsystem_info/${platform}-stub/BUILG.gn),
        (/out/${product_name}/build_configs/subsystem_info/${platform}-stub/zframework_stub_exists.gni)]
    @parameter: none
    @return :none
    '''

    def _generate_stub_targets(self):
        generate_targets_gn.gen_stub_targets(
            self.parts_config_info.get('parts_kits_info'),
            self.target_platform_stubs,
            self.config_output_dir)

    '''Description: output system capabilities into a json file. \
        (/out/${product_name}/build_configs/${platform}_system_capabilities.json)
    @parameter: none
    @return :none
    '''

    def _generate_system_capabilities(self):
        for platform in self.build_platforms:
            platform_parts = self.target_platform_parts.get(platform)
            platform_capabilities = []
            for _, origin in platform_parts.items():
                # parts_info.get() might be None if the part is a binary package
                all_parts_variants = self.parts_info.get(origin)
                if all_parts_variants is None:
                    continue
                part = all_parts_variants[0]
                if part.get('system_capabilities'):
                    entry = part.get('system_capabilities')
                    if len(entry) > 0:
                        platform_capabilities.extend(entry)
            platform_part_json_file = os.path.join(
                self.config_output_dir, "{0}_system_capabilities.json".format(platform))
            write_json_file(platform_part_json_file,
                            sorted(platform_capabilities),
                            check_changes=True)
            LogUtil.hb_info(
                "generated system capabilities to '{}/{}_system_capabilities.json'".format(
                    self.config_output_dir, platform))

    '''Description: output system configs info into three json files:[
        (/out/${product_name}/build_configs/subsystem_info/subsystem_build_config.json),
        (/out/${product_name}/build_configs/subsystem_info/src_subsystem_info.json),
        (/out/${product_name}/build_configs/subsystem_info/no_src_subsystem_info.json)]
    @parameter: none
    @return :none
    '''

    def _generate_subsystem_configs(self):

        # The function has been implemented in module util/loader/subsystem_info.py
        LogUtil.hb_info(
            "generated subsystem build config to '{}/subsystem_info/subsystem_build_config.json'".format(
                self.config_output_dir))
        LogUtil.hb_info(
            "generated src subsystem info to '{}/subsystem_info/src_subsystem_info.json'".format(
                self.config_output_dir))
        LogUtil.hb_info(
            "generated no src subsystem info to '{}/subsystem_info/no_src_subsystem_info.json'".format(
                self.config_output_dir))

# get method
    @throw_exception
    def _get_build_platforms(self) -> list:
        build_platforms = []
        if self.build_platform_name == 'all':
            build_platforms = self._all_platforms
        elif self.build_platform_name in self._all_platforms:
            build_platforms = [self.build_platform_name]
        else:
            raise OHOSException(
                "The target_platform is incorrect, only allows [{}].".format(
                    ', '.join(self._all_platforms)), "2010")
        return build_platforms

    def _get_parts_by_platform(self) -> dict:
        parts_info = {}
        if 'phone' in self.target_platform_parts:
            phone_parts_list = self.target_platform_parts.get('phone').keys()
        else:
            phone_parts_list = []
        for _platform, _parts_info in self.target_platform_parts.items():
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

    def _get_platforms_all_parts(self) -> dict:
        _dist_parts_variants = self._load_component_dist()
        target_platform_parts = {}
        all_parts = self._platforms_info.get('all_parts')
        parts_variants = self.parts_config_info.get('parts_variants')
        for _platform, _parts in all_parts.items():
            if _platform not in self.build_platforms:
                continue
            part_name_info = {}
            for part_def in _parts:
                real_name, original_name = self._get_real_part_name(
                    part_def, _platform, parts_variants)
                if real_name is None:
                    # find this from component_dist
                    real_name, original_name = self._get_real_part_name(
                        part_def, _platform, _dist_parts_variants)
                if real_name is None:
                    continue
                part_name_info[real_name] = original_name
            target_platform_parts[_platform] = part_name_info
        return target_platform_parts

    def _get_platforms_all_stubs(self) -> dict:
        _dist_parts_variants = self._load_component_dist()
        platform_stubs = {}
        all_stubs = self._platforms_info.get('all_stubs')
        parts_variants = self.parts_config_info.get('parts_variants')
        for _platform, _part_names in all_stubs.items():
            if _platform not in self.build_platforms:
                continue
            stub_parts_from_src = []
            stub_parts_from_dist = []
            for part_name in _part_names:
                real_name, original_name = self._get_real_part_name(
                    part_name, _platform, parts_variants)
                # real_name=None means part_name doesn't exist in source tree,
                # use binary in component_dist then.
                if real_name is None:
                    # find this from component_dist
                    real_name, original_name = self._get_real_part_name(
                        part_name, _platform, _dist_parts_variants)
                    if real_name is None:
                        continue
                    else:
                        stub_sources = os.path.join(
                            self.source_root_dir,
                            "component_dist/{}-{}/api_stubs/{}/stubs_sources_list.txt"  # noqa: E501
                            .format(self.target_os, self.target_cpu, real_name))
                        stub_parts_from_dist.append(
                            '"{}"'.format(stub_sources))
                else:
                    stub_parts_from_src.append(real_name)
            platform_stubs[_platform] = {
                "src": stub_parts_from_src,
                "dist": stub_parts_from_dist,
            }
        return platform_stubs

    def _get_platforms_parts(self) -> dict:
        platforms_parts = {}
        src_parts_targets = self.parts_targets
        src_all_parts = src_parts_targets.keys()
        for _platform, _all_parts in self.target_platform_parts.items():
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

    def _get_parts_src_list(self) -> list:
        parts_name_map = {}
        for _list in self.parts_info.values():
            for _info in _list:
                parts_name_map[_info.get('part_name')] = _info.get(
                    'origin_part_name')
        _src_set = set()
        for _name in self.required_parts_targets.keys():
            _origin_name = parts_name_map.get(_name)
            if _origin_name is None:
                continue
            _src_set.add(_origin_name)
        return list(_src_set)

    def _get_required_build_targets(self) -> dict:
        required_build_targets = {}
        for _p_name, _info in self.parts_targets.items():
            if _p_name not in self.required_parts_targets_list:
                continue
            required_build_targets[_p_name] = _info
        return required_build_targets

    def _get_required_phony_targets(self) -> dict:
        required_build_targets = {}
        for _p_name, _info in self.phony_targets.items():
            if _p_name not in self.required_parts_targets_list:
                continue
            required_build_targets[_p_name] = _info
        return required_build_targets

    def _get_required_build_parts_list(self) -> list:
        parts_set = set()
        for _parts_list in self.target_platform_parts.values():
            parts_set.update(_parts_list)
        return list(parts_set)

# util method

    def _load_component_dist(self) -> dict:
        _parts_variants_info = {}
        _dir = "component_dist/{}-{}/packages_to_install".format(
            self.target_os, self.target_cpu)
        _file_name = "dist_parts_info.json"
        _dist_parts_info_file = os.path.join(
            self.source_root_dir, _dir, _file_name)
        if not os.path.exists(_dist_parts_info_file):
            # If the file does not exist, do nothing and return
            return _parts_variants_info
        _parts_info = read_json_file(_dist_parts_info_file)
        if _parts_info is None:
            raise Exception("read file '{}' failed.".format(
                _dist_parts_info_file))
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

    def _get_real_part_name(self, original_part_name, current_platform, parts_variants):
        part_info = parts_variants.get(original_part_name)
        if part_info is None:
            return None, None
        if current_platform in part_info and current_platform != 'phone':
            real_name = '{}_{}'.format(original_part_name, current_platform)
        else:
            real_name = original_part_name
        return real_name, original_part_name

    '''Description: called by _out_infos_for_testfwk, output information by platform
    @parameter:none
    @return :none
    '''

    def _output_infos_by_platform(self, part_name_infos, parts_info_dict):
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

    def _execute_loader_args_display(self):
        LogUtil.hb_info('Loading configuration file...')
        args = []
        args.append('platforms_config_file="{}"'.format(
            self.platforms_config_file))
        args.append('subsystem_config_file="{}"'.format(
            self.subsystem_config_file))
        args.append('example_subsystem_file="{}"'.format(
            self.example_subsystem_file))
        args.append('exclusion_modules_config_file="{}"'.format(
            self.exclusion_modules_config_file))
        args.append('source_root_dir="{}"'.format(self.source_root_dir))
        args.append('gn_root_out_dir="{}"'.format(self.gn_root_out_dir))
        args.append('build_platform_name={}'.format(self.build_platform_name))
        args.append('build_xts={}'.format(self.build_xts))
        args.append('load_test_config={}'.format(self.load_test_config))
        args.append('target_os={}'.format(self.target_os))
        args.append('target_cpu={}'.format(self.target_cpu))
        args.append('os_level={}'.format(self.os_level))
        args.append('ignore_api_check={}'.format(self.ignore_api_check))
        args.append('scalable_build={}'.format(self.scalable_build))
        LogUtil.write_log(self.config.log_path,
                          'loader args:{}'.format(args), 'info')
