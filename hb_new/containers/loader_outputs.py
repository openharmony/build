#!/usr/bin/env python
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

from containers.output import Output


class LoaderOutputs():

    def __init__(self, output_dir: str):

        self._no_src_subsystem_info = Output(os.path.join(
            output_dir, 'build_configs/subsystem_info'), 'no_src_subsystem_info.json')
        self._src_subsystem_info = Output(os.path.join(
            output_dir, 'build_configs/subsystem_info'), 'src_subsystem_info.json')
        self._subsystem_build_config = Output(os.path.join(
            output_dir, 'build_configs/subsystem_info'), 'subsystem_build_config.json')

        self._all_parts = Output(os.path.join(
            output_dir, 'build_configs/platforms_info'), 'all_parts.json')
        self._toolchain_to_variant = Output(os.path.join(
            output_dir, 'build_configs/platforms_info'), 'toolchain_to_variant.json')

        # This outputs represent all BUILD.gn in out/{product}/build_configs/{subsystem}/{component} of each component
        self._all_component_build_file = Output(os.path.join(output_dir), '')

        self._parts_info = Output(os.path.join(
            output_dir, 'build_configs/parts_info'), 'parts_info.json')
        self._subsystem_parts = Output(os.path.join(
            output_dir, 'build_configs/parts_info'), 'subsystem_parts.json')
        self._parts_variants = Output(os.path.join(
            output_dir, 'build_configs/parts_info'), 'parts_variants.json')
        self._parts_inner_kits_info = Output(os.path.join(
            output_dir, 'build_configs/parts_info'), 'inner_kits_info.json')
        self._parts_targets = Output(os.path.join(
            output_dir, 'build_configs/parts_info'), 'parts_targets.json')
        self._phony_target = Output(os.path.join(
            output_dir, 'build_configs/parts_info'), 'phony_target.json')
        self._parts_path_info = Output(os.path.join(
            output_dir, 'build_configs/parts_info'), 'parts_path_info.json')
        self._path_to_parts = Output(os.path.join(
            output_dir, 'build_configs/parts_info'), 'path_to_parts.json')
        self._hisysevent_config = Output(os.path.join(
            output_dir, 'build_configs/parts_info'), 'hisysevent_configs.json')
        self._parts_modules_info = Output(os.path.join(
            output_dir, 'build_configs/parts_info'), 'parts_info.json')

        self._target_platforms_parts = Output(os.path.join(
            output_dir, 'build_configs'), 'target_platforms_parts.json')
        self._platform_system_capabilities = Output(os.path.join(
            output_dir, 'build_configs'), 'system_capabilities.json')

        # TODO:"phone" should be a variant which represent each platform
        self._stub_gn = Output(os.path.join(
            output_dir, 'build_configs/phone-stub'), 'BUILD.gn')
        self._stub_gni = Output(os.path.join(
            output_dir, 'build_configs/phone-stub'), 'zframework_stub_exists.gni')

        self._platforms_parts_by_src = Output(os.path.join(
            output_dir, 'build_configs'), 'platforms_parts_by_src.json')

        self._parts_list = Output(os.path.join(
            output_dir, 'build_configs'), 'parts_list.gni')
        self._inner_kits_list = Output(os.path.join(
            output_dir, 'build_configs'), 'inner_kits_list.gni')
        self._system_kits_list = Output(os.path.join(
            output_dir, 'build_configs'), 'system_kits_list.gni')
        self._parts_test_list = Output(os.path.join(
            output_dir, 'build_configs'), 'parts_test_list.gni')
        self._build_gn = Output(os.path.join(
            output_dir, 'build_configs'), 'BUILD.gn')
        self._phony_build_file = Output(os.path.join(
            output_dir, 'build_configs/phony_targets'), 'BUILD.gn')
        self._required_parts_targets = Output(os.path.join(
            output_dir, 'build_configs'), 'required_parts_targets.json')
        self._parts_src_flag = Output(os.path.join(
            output_dir, 'build_configs'), 'parts_src_flag.json')
        self._auto_install_list = Output(os.path.join(
            output_dir, 'build_configs'), 'auto_install_parts.json')
        self._platforms_list_gni_file = Output(os.path.join(
            output_dir, 'build_configs'), "platforms_list.gni")
        self._parts_different_info_file = Output(os.path.join(
            output_dir, 'build_configs'), "parts_different_info.json")
        self._infos_for_testfwk_file = Output(os.path.join(
            output_dir, 'build_configs'), "infos_for_testfwk.json")

        # there are some produce like syscap.para, syscap.json have been generated on proloader phase,
        # so we don't define those produce as loader produce

    def check_outputs(self) -> bool: 
        '''TODO: check whether the loader phase is executed successfully
        '''
        return True
