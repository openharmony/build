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

VERSION = "1.0.0"
CURRENT_OHOS_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CURRENT_BUILD_DIR = os.path.join(CURRENT_OHOS_ROOT, 'build')
CURRENT_HB_DIR = os.path.join(CURRENT_BUILD_DIR, 'hb_new')
DEFAULT_CCACHE_DIR = os.path.join(CURRENT_OHOS_ROOT, '.ccache')

ARGS_DIR = os.path.join(CURRENT_HB_DIR, 'resources/args')

DEFAULT_BUILD_ARGS = os.path.join(CURRENT_HB_DIR, 'resources/args/default/buildargs.json')
DEFAULT_SET_ARGS = os.path.join(CURRENT_HB_DIR, 'resources/args/default/setargs.json')
DEFAULT_CLEAN_ARGS = os.path.join(CURRENT_HB_DIR, 'resources/args/default/cleanargs.json')
DEFAULT_ENV_ARGS = os.path.join(CURRENT_HB_DIR, 'resources/args/default/envargs.json')

CURRENT_BUILD_ARGS = os.path.join(CURRENT_HB_DIR, 'resources/args/buildargs.json')
CURRENT_SET_ARGS = os.path.join(CURRENT_HB_DIR, 'resources/args/setargs.json')
CURRENT_CLEAN_ARGS = os.path.join(CURRENT_HB_DIR, 'resources/args/cleanargs.json')
CURRENT_ENV_ARGS = os.path.join(CURRENT_HB_DIR, 'resources/args/envargs.json')

BUILD_CONFIG_FILE = os.path.join(CURRENT_HB_DIR, 'resources/config/config.json')
ROOT_CONFIG_FILE = os.path.join(CURRENT_OHOS_ROOT, 'ohos_config.json')
STATUS_FILE = os.path.join(CURRENT_HB_DIR, 'resources/status/status.json')

ENV_SETUP_FILE = os.path.join(CURRENT_BUILD_DIR, 'build_scripts', 'env_setup.sh')
