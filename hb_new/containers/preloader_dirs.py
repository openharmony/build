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

class PreloaderDirs():

    def __init__(self, config):
        self.__post_init__(config)

    def __post_init__(self, config):
        self.source_root_dir = config.root_path
        self.built_in_product_dir = config.built_in_product_path
        self.productdefine_dir = os.path.join(self.source_root_dir,
                                              'productdefine/common')
        self.built_in_device_dir = config.built_in_device_path
        self.built_in_base_dir = os.path.join(self.productdefine_dir, 'base')

        # Configs of vendor specified products are stored in
        # ${vendor_dir} directory.
        self.vendor_dir = config.vendor_path
        # Configs of device specified products are stored in
        # ${device_dir} directory.
        self.device_dir = os.path.join(config.root_path, 'device')

        self.subsystem_config_json = os.path.join(config.root_path,
                                                  config.subsystem_config_json)
        self.lite_components_dir = os.path.join(config.root_path,
                                                'build/lite/components')

        self.preloader_output_dir = os.path.join(config.root_path,
                                                'out/preloader',
                                                config.product)