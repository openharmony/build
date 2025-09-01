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

VERSION = "1.0.0"
CURRENT_OHOS_ROOT = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CURRENT_BUILD_DIR = os.path.join(CURRENT_OHOS_ROOT, 'build')
CURRENT_HB_DIR = os.path.join(CURRENT_BUILD_DIR, 'hb')
DEFAULT_CCACHE_DIR = os.path.join(CURRENT_OHOS_ROOT, '.ccache')

ARGS_DIR = os.path.join(CURRENT_HB_DIR, 'resources/args')

DEFAULT_BUILD_ARGS = os.path.join(
    CURRENT_HB_DIR, 'resources/args/default/buildargs.json')
DEFAULT_SET_ARGS = os.path.join(
    CURRENT_HB_DIR, 'resources/args/default/setargs.json')
DEFAULT_CLEAN_ARGS = os.path.join(
    CURRENT_HB_DIR, 'resources/args/default/cleanargs.json')
DEFAULT_ENV_ARGS = os.path.join(
    CURRENT_HB_DIR, 'resources/args/default/envargs.json')
DEFAULT_TOOL_ARGS = os.path.join(
    CURRENT_HB_DIR, 'resources/args/default/toolargs.json')

DEFAULT_INDEP_BUILD_ARGS = os.path.join(
    CURRENT_HB_DIR, 'resources/args/default/indepbuildargs.json')

DEFAULT_INSTALL_ARGS = os.path.join(
    CURRENT_HB_DIR, 'resources/args/default/installargs.json')

DEFAULT_PACKAGE_ARGS = os.path.join(
    CURRENT_HB_DIR, 'resources/args/default/packageargs.json')

DEFAULT_PUBLISH_ARGS = os.path.join(
    CURRENT_HB_DIR, 'resources/args/default/publishargs.json')

DEFAULT_UPDATE_ARGS = os.path.join(
    CURRENT_HB_DIR, 'resources/args/default/updateargs.json')

DEFAULT_PUSH_ARGS = os.path.join(
    CURRENT_HB_DIR, 'resources/args/default/pushargs.json')

CURRENT_ARGS_DIR = os.path.join(CURRENT_OHOS_ROOT, 'out/hb_args')
CURRENT_BUILD_ARGS = os.path.join(
    CURRENT_ARGS_DIR, 'buildargs.json')
CURRENT_SET_ARGS = os.path.join(
    CURRENT_ARGS_DIR, 'setargs.json')
CURRENT_CLEAN_ARGS = os.path.join(
    CURRENT_ARGS_DIR, 'cleanargs.json')
CURRENT_ENV_ARGS = os.path.join(
    CURRENT_ARGS_DIR, 'envargs.json')
CURRENT_TOOL_ARGS = os.path.join(
    CURRENT_ARGS_DIR, 'toolargs.json')
CURRENT_INDEP_BUILD_ARGS = os.path.join(
    CURRENT_ARGS_DIR, 'indepbuildargs.json')
CURRENT_INSTALL_ARGS = os.path.join(
    CURRENT_ARGS_DIR, 'installargs.json')
CURRENT_PACKAGE_ARGS = os.path.join(
    CURRENT_ARGS_DIR, 'packageargs.json')
CURRENT_PUBLISH_ARGS = os.path.join(
    CURRENT_ARGS_DIR, 'publishargs.json')
CURRENT_UPDATE_ARGS = os.path.join(
    CURRENT_ARGS_DIR, 'updateargs.json')
CURRENT_PUSH_ARGS = os.path.join(
    CURRENT_ARGS_DIR, 'pushargs.json')

BUILD_CONFIG_FILE = os.path.join(
    CURRENT_HB_DIR, 'resources/config/config.json')
ROOT_CONFIG_FILE = os.path.join(CURRENT_OHOS_ROOT, 'out/ohos_config.json')
STATUS_FILE = os.path.join(CURRENT_HB_DIR, 'resources/status/status.json')

ENV_SETUP_FILE = os.path.join(
    CURRENT_BUILD_DIR, 'build_scripts', 'env_setup.sh')

COMPONENTS_PATH_DIR = os.path.join(CURRENT_OHOS_ROOT, 'out/components_path.json')

HPM_CHECK_INFO = ""

NINJA_DESCRIPTION = {
    "ASM",
    "CC",
    "CXX",
    "clang",
    "clang++",
    "cross compiler",
    "gcc",
    "iccarm",
    "LLVM",
    "OBJC",
    "OBJCXX",
    "AR",
    "LINK",
    "SOLINK",
    "SOLINK_MODULE",
    "RUST",
    "ACTION",
    "COPY",
    "STAMP",
}


def set_hpm_check_info(info):
    global HPM_CHECK_INFO
    HPM_CHECK_INFO = info


def get_hpm_check_info():
    return HPM_CHECK_INFO
