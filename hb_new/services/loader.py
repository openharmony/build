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
        
    def _internel_run(self) -> StatusCode:
        pass
