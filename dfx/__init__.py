#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) 2025 Huawei Device Co., Ltd.
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
#

from .dfx_config_manager import get_config_manager, reload_config as reload_dfx_config

# Get initial debug state from config manager
_DEBUG_ENABLED = get_config_manager().build_dfx_debug_enable


def _load_debug_config():
    """Load debug configuration"""
    global _DEBUG_ENABLED
    _DEBUG_ENABLED = get_config_manager().build_dfx_debug_enable


def dfx_info(*args, **kwargs):
    """Print information based on configuration settings"""
    if _DEBUG_ENABLED:
        print('[DFX INFO]', *args, **kwargs)


def dfx_error(*args, **kwargs):
    """Print error information based on configuration settings"""
    if _DEBUG_ENABLED:
        print("[DFX ERROR]", *args, **kwargs)


def dfx_debug(*args, **kwargs):
    """Print debug information only in debug mode with [DEBUG] prefix"""
    if _DEBUG_ENABLED:
        print('[DFX DEBUG]', *args, **kwargs)


def is_debug_enabled():
    """Check if debug mode is enabled"""
    return _DEBUG_ENABLED


def reload_config():
    """Reload configuration"""
    reload_dfx_config()
    _load_debug_config()
