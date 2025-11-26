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

import json
from pathlib import Path

# 全局调试开关状态
_DEBUG_ENABLED = False

# 加载配置文件路径
_CONFIG_PATH = Path(__file__).parent / 'dfx_config.json'


def _load_debug_config():
    """加载调试配置"""
    global _DEBUG_ENABLED
    try:
        if _CONFIG_PATH.exists():
            with open(_CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
                _DEBUG_ENABLED = config.get('build_dfx_debug_enable', 'false').lower() == 'true'
    except Exception:
        # 如果配置加载失败，默认关闭调试
        _DEBUG_ENABLED = False


# 初始化时加载配置
_load_debug_config()


def dfx_info(*args, **kwargs):
    """根据配置决定是否输出打印信息"""
    if _DEBUG_ENABLED:
        print('[DFX INFO]', *args, **kwargs)


def dfx_error(*args, **kwargs):
    """根据配置决定是否输出打印信息"""
    if _DEBUG_ENABLED:
        print("[DFX ERROR]", *args, **kwargs)


def dfx_debug(*args, **kwargs):
    """仅在调试模式下输出，带[DEBUG]前缀"""
    if _DEBUG_ENABLED:
        print('[DFX DEBUG]', *args, **kwargs)


def is_debug_enabled():
    """检查调试模式是否启用"""
    return _DEBUG_ENABLED


def reload_config():
    """重新加载配置"""
    _load_debug_config()
