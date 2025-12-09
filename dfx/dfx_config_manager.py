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

"""
DFX Configuration Manager
Unified configuration reading interface with support for config files and environment variables
Priority: config file > environment variable
"""

import json
import os
from pathlib import Path
from typing import Any, Optional


class DFXConfigManager:
    """DFX Configuration Manager"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager

        Args:
            config_path: Configuration file path, default is dfx_config.json in current directory
        """
        if config_path is None:
            self._config_path = Path(__file__).parent / 'dfx_config.json'
        else:
            self._config_path = Path(config_path)

        self._config_cache = {}
        self._load_config()

    # Convenience methods: directly get each configuration item
    @property
    def build_dfx_enable(self) -> str:
        """Whether to enable DFX build tracking"""
        return self.get_str('build_dfx_enable')

    @property
    def build_dfx_enable_bool(self) -> bool:
        """Whether to enable DFX build tracking (boolean value)"""
        value = self.build_dfx_enable
        return value.lower() in ('true', '1', 'yes', 'on') if value else False

    @property
    def build_dfx_debug_enable(self) -> bool:
        """Whether to enable DFX debug mode"""
        return self.get_bool('build_dfx_debug_enable')

    @property
    def trace_log_dir(self) -> str:
        """Log storage directory"""
        value = self.get_str('trace_log_dir')
        return value if value else 'out/dfx'

    @property
    def trace_log_upload_api(self) -> str:
        """Log upload API address"""
        return self.get_str('trace_log_upload_api')

    @property
    def extra_request_header_fields(self) -> str:
        """Extra request header fields"""
        return self.get_str('extra_request_header_fields')

    @property
    def extra_request_header_values(self) -> str:
        """Extra request header values"""
        return self.get_str('extra_request_header_values')

    @property
    def extra_request_header_fields_encrypted(self) -> bool:
        """Whether request header fields are encrypted"""
        return self.get_bool('extra_request_header_fields_encrypted')

    @property
    def extra_request_header_encryption_key(self) -> str:
        """Request header encryption key"""
        return self.get_str('extra_request_header_encryption_key')
    
    def get(self, key: str) -> Any:
        """
        Get configuration value

        Priority: config file > environment variable

        Args:
            key: Configuration key name

        Returns:
            Configuration value
        """
        # First try to read from config file
        config_value = self._config_cache.get(key)
        if config_value is not None and config_value != "":
            return config_value

        # If not in config file or empty, try to read from environment variable
        env_key = self._get_env_key(key)
        env_value = os.environ.get(env_key)
        if env_value is not None:
            return env_value

        # Return None if neither exists
        return None

    def get_bool(self, key: str) -> bool:
        """
        Get boolean configuration value

        Args:
            key: Configuration key name

        Returns:
            Boolean value
        """
        value = self.get(key)
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        return str(value).lower() in ('true', '1', 'yes', 'on')

    def get_str(self, key: str) -> str:
        """
        Get string configuration value

        Args:
            key: Configuration key name

        Returns:
            String value
        """
        value = self.get(key)
        return str(value) if value is not None else ""

    def reload(self):
        """Reload configuration file"""
        self._load_config()
    
    def _load_config(self):
        """Load configuration file"""
        try:
            if self._config_path.exists():
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    self._config_cache = json.load(f)
        except Exception as e:
            # Use empty config if config file loading fails
            self._config_cache = {}

    def _get_env_key(self, config_key: str) -> str:
        """
        Convert configuration key to environment variable key

        Args:
            config_key: Key name in config file

        Returns:
            Environment variable key (DFX_ prefix, uppercase)
        """
        return f"DFX_{config_key.upper()}"


# Global configuration manager instance
_config_manager = None


def get_config_manager() -> DFXConfigManager:
    """Get global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = DFXConfigManager()
    return _config_manager


def reload_config():
    """Reload configuration"""
    global _config_manager
    if _config_manager is not None:
        _config_manager.reload()


# Convenience functions: directly get configuration values
def get_build_dfx_enable() -> str:
    """Get whether to enable DFX build tracking"""
    return get_config_manager().build_dfx_enable


def get_build_dfx_enable_bool() -> bool:
    """Get whether to enable DFX build tracking (boolean value)"""
    return get_config_manager().build_dfx_enable_bool


def get_build_dfx_debug_enable() -> bool:
    """Get whether to enable DFX debug mode"""
    return get_config_manager().build_dfx_debug_enable


def get_trace_log_dir() -> str:
    """Get log storage directory"""
    return get_config_manager().trace_log_dir


def get_trace_log_upload_api() -> str:
    """Get log upload API address"""
    return get_config_manager().trace_log_upload_api


def get_extra_request_header_fields() -> str:
    """Get extra request header fields"""
    return get_config_manager().extra_request_header_fields


def get_extra_request_header_values() -> str:
    """Get extra request header values"""
    return get_config_manager().extra_request_header_values


def get_extra_request_header_fields_encrypted() -> bool:
    """Get whether request header fields are encrypted"""
    return get_config_manager().extra_request_header_fields_encrypted


def get_extra_request_header_encryption_key() -> str:
    """Get request header encryption key"""
    return get_config_manager().extra_request_header_encryption_key