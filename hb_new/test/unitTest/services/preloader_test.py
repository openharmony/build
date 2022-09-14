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

import unittest

from services.preloader import Preloader
from resources.config import Config

class PreloaderTest(unittest.TestCase):
    
    def setUp(self):
        self.preloader = Preloader(Config())
        return super().setUp()
    
    def tearDown(self):
        return super().tearDown()
    
    def test_generate_build_prop(self):
        pass

    def test_generate_build_config_json(self):
        pass

    def test_generate_parts_json(self):
        pass

    def test_generate_parts_config_json(self):
        pass

    def test_generate_build_gnargs_prop(self):
        pass

    def test_generate_features_json(self):
        pass

    def test_generate_syscap_json(self):
        pass

    def test_generate_exclusion_modules_json(self):
        pass

    def test_generate_subsystem_config_json(self):
        pass

    def test_generate_platforms_build(self):
        pass

    def test_generate_systemcapability_json(self):
        pass
    
    def test_internel_run(self):
        pass
