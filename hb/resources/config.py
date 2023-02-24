#!/usr/bin/env python
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
import platform

from resources.global_var import CURRENT_OHOS_ROOT
from resources.global_var import BUILD_CONFIG_FILE
from resources.global_var import ROOT_CONFIG_FILE
from exceptions.ohos_exception import OHOSException
from helper.singleton import Singleton
from util.io_util import IoUtil
from containers.status import throw_exception


def get_config_path():
    if not os.path.exists(ROOT_CONFIG_FILE):
        IoUtil.copy_file(BUILD_CONFIG_FILE, ROOT_CONFIG_FILE)
    return ROOT_CONFIG_FILE


class Config(metaclass=Singleton):
    def __init__(self):
        self.config_json = ""
        self._root_path = ""
        self._board = ""
        self._kernel = ""
        self._product = ""
        self._product_path = ""
        self._device_path = ""
        self._device_company = ""
        self._patch_cache = ""
        self._version = ""
        self._os_level = ""
        self._product_json = ""
        self._target_os = ""
        self._target_cpu = ""
        self._out_path = ""
        self._compile_config = ""
        self._component_type = ""
        self._device_config_path = ""
        self._product_config_path = ""
        self._subsystem_config_json = ""
        self._subsystem_config_overlay_json = ""
        self._support_cpu = ""
        self.fs_attr = set()
        self.platform = platform.system()
        self.__post__init()

    def __post__init(self):
        self.config_json = get_config_path()
        config_content = IoUtil.read_json_file(self.config_json)
        self.root_path = CURRENT_OHOS_ROOT
        self.board = config_content.get('board', None)
        self.kernel = config_content.get('kernel', None)
        self.product = config_content.get('product', None)
        self.product_path = config_content.get('product_path', None)
        self.device_path = config_content.get('device_path', None)
        self.device_company = config_content.get('device_company', None)
        self.patch_cache = config_content.get('patch_cache', None)
        self.version = config_content.get('version', '3.0')
        self.os_level = config_content.get('os_level', 'small')
        self.product_json = config_content.get('product_json', None)
        self.target_os = config_content.get('target_os', None)
        self.target_cpu = config_content.get('target_cpu', None)
        self.out_path = config_content.get('out_path', None)
        self.compile_config = config_content.get('compile_config', None)
        self.component_type = config_content.get('component_type', None)
        self.device_config_path = config_content.get('device_config_path',
                                                     None)
        self.product_config_path = config_content.get('product_config_path',
                                                      None)
        self.subsystem_config_json = config_content.get(
            'subsystem_config_json', None)
        self.support_cpu = config_content.get('support_cpu', None)
        self.fs_attr = set()
        self.platform = platform.system()

    @property
    def component_type(self):
        return self._component_type

    @component_type.setter
    def component_type(self, value):
        self._component_type = value
        self.config_update('component_type', self._component_type)

    @property
    def target_os(self):
        return self._target_os

    @target_os.setter
    def target_os(self, value):
        self._target_os = value
        self.config_update('target_os', self._target_os)

    @property
    def target_cpu(self):
        return self._target_cpu

    @target_cpu.setter
    def target_cpu(self, value):
        self._target_cpu = value
        self.config_update('target_cpu', self._target_cpu)

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, value):
        self._version = value
        self.config_update('version', self._version)

    @property
    def compile_config(self):
        return self._compile_config

    @compile_config.setter
    def compile_config(self, value):
        self._compile_config = value
        self.config_update('compile_config', self._compile_config)

    @property
    def os_level(self):
        return self._os_level

    @os_level.setter
    def os_level(self, value):
        self._os_level = value
        self.config_update('os_level', self._os_level)

    @property
    def product_json(self):
        return self._product_json

    @product_json.setter
    def product_json(self, value):
        self._product_json = value
        self.config_update('product_json', self._product_json)

    @property
    @throw_exception
    def root_path(self):
        if self._root_path is None:
            raise OHOSException('Failed to init compile config', '0019')

        return self._root_path

    @root_path.setter
    def root_path(self, value):
        self._root_path = os.path.abspath(value)
        self.config_update('root_path', self._root_path)

    @property
    def board(self):
        if self._board is None:
            raise OHOSException('Failed to init compile config', '0019')
        return self._board

    @board.setter
    def board(self, value):
        self._board = value
        self.config_update('board', self._board)

    @property
    def device_company(self):
        if self._device_company is None:
            raise OHOSException('Failed to init compile config', '0019')
        return self._device_company

    @device_company.setter
    def device_company(self, value):
        self._device_company = value
        self.config_update('device_company', self._device_company)

    @property
    def kernel(self):
        return self._kernel

    @kernel.setter
    def kernel(self, value):
        self._kernel = value
        self.config_update('kernel', self._kernel)

    @property
    def product(self):
        if self._product is None:
            raise OHOSException('Failed to init compile config', '0019')
        return self._product

    @product.setter
    def product(self, value):
        self._product = value
        self.config_update('product', self._product)

    @property
    def product_path(self):
        if self._product_path is None:
            raise OHOSException('Failed to init compile config', '0019')
        return self._product_path

    @product_path.setter
    def product_path(self, value):
        self._product_path = value
        self.config_update('product_path', self._product_path)

    @property
    def gn_product_path(self):
        return self.product_path.replace(self.root_path, '/')

    @property
    def device_path(self):
        if self._device_path is None:
            raise OHOSException('Failed to init compile config', '0019')
        return self._device_path

    @device_path.setter
    def device_path(self, value):
        self._device_path = value
        self.config_update('device_path', self._device_path)

    @property
    def gn_device_path(self):
        return self.device_path.replace(self.root_path, '/')

    @property
    def build_path(self):
        _build_path = os.path.join(self.root_path, 'build', 'lite')
        if not os.path.isdir(_build_path):
            raise OHOSException(f'Invalid build path: {_build_path}')
        return _build_path

    @property
    def out_path(self):
        return self._out_path

    @out_path.setter
    def out_path(self, value):
        self._out_path = value
        self.config_update('out_path', self._out_path)

    @property
    def device_config_path(self):
        return self._device_config_path

    @device_config_path.setter
    def device_config_path(self, value):
        self._device_config_path = value
        self.config_update('device_config_path', self._device_config_path)

    @property
    def product_config_path(self):
        return self._product_config_path

    @product_config_path.setter
    def product_config_path(self, value):
        self._product_config_path = value
        self.config_update('product_config_path', self._product_config_path)

    @property
    def subsystem_config_json(self):
        return self._subsystem_config_json

    @subsystem_config_json.setter
    def subsystem_config_json(self, value):
        self._subsystem_config_json = value
        self.config_update('subsystem_config_json',
                           self._subsystem_config_json)

    @property
    def subsystem_config_overlay_json(self):
        return self._subsystem_config_overlay_json

    @subsystem_config_overlay_json.setter
    def subsystem_config_overlay_json(self, value):
        self._subsystem_config_overlay_json = value
        self.config_update('subsystem_config_overlay_json',
                           self._subsystem_config_overlay_json)

    @property
    def support_cpu(self):
        return self._support_cpu

    @support_cpu.setter
    def support_cpu(self, value):
        self._support_cpu = value
        self.config_update('support_cpu', self._support_cpu)

    @property
    def log_path(self):
        if self.out_path is not None:
            return os.path.join(self.out_path, 'build.log')
        else:
            raise OHOSException(f'Failed to get log_path')

    @property
    def vendor_path(self):
        _vendor_path = os.path.join(self.root_path, 'vendor')
        if not os.path.isdir(_vendor_path):
            _vendor_path = ''
        return _vendor_path

    @property
    def built_in_product_path(self):
        _built_in_product_path = os.path.join(self.root_path,
                                              'productdefine/common/products')
        if not os.path.isdir(_built_in_product_path):
            raise OHOSException(
                f'Invalid built-in product path: {_built_in_product_path}')
        return _built_in_product_path

    @property
    def build_tools_path(self):
        try:
            tools_path = IoUtil.read_json_file(
                'build_tools/build_tools_config.json')[self.platform]['build_tools_path']
            return os.path.join(self.root_path, tools_path)
        except KeyError:
            raise OHOSException(f'unidentified platform: {self.platform}')

    @property
    def gn_path(self):
        repo_gn_path = os.path.join(self.build_tools_path, 'gn')
        # gn exist.
        if os.path.isfile(repo_gn_path):
            return repo_gn_path
        else:
            raise OHOSException('There is no clang executable file at {}, \
                          please execute build/prebuilts_download.sh'.format(repo_gn_path))

    @property
    def ninja_path(self):
        repo_ninja_path = os.path.join(self.build_tools_path, 'ninja')
        # ninja exist.
        if os.path.isfile(repo_ninja_path):
            return repo_ninja_path
        else:
            raise OHOSException('There is no clang executable file at {}, \
                          please execute build/prebuilts_download.sh'.format(repo_ninja_path))

    @property
    def clang_path(self):
        repo_clang_path = os.path.join('prebuilts', 'clang', 'ohos',
                                       'linux-x86_64', 'llvm')
        # clang exist
        if os.path.isdir(repo_clang_path):
            return f'//{repo_clang_path}'
        # clang installed manually or auto download
        else:
            raise OHOSException('There is no clang executable file at {}, \
                          please execute build/prebuilts_download.sh'.format(repo_clang_path))

    @property
    def patch_cache(self):
        return self._patch_cache

    @patch_cache.setter
    def patch_cache(self, value):
        self._patch_cache = value
        self.config_update('patch_cache', self._patch_cache)

    def config_update(self, key, value):
        config_content = IoUtil.read_json_file(self.config_json)
        config_content[key] = value
        IoUtil.dump_json_file(self.config_json, config_content)
