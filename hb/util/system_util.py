#!/usr/bin/env python3
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
#

import os
import re
import subprocess
import copy

from datetime import datetime

from resources.global_var import CURRENT_BUILD_DIR, CURRENT_OHOS_ROOT
from util.io_util import IoUtil
from util.log_util import LogUtil
from hb.helper.no_instance import NoInstance
from containers.status import throw_exception


class HandleKwargs(metaclass=NoInstance):
    compile_item_pattern = re.compile(r'\[\d+/\d+\].+')
    key_word_register_list = ["pre_msg", "log_stage", "after_msg", "log_filter", "custom_line_handle"]
    filter_print = False

    @staticmethod
    def remove_registry_kwargs(kw_dict):
        for item in HandleKwargs.key_word_register_list:
            kw_dict.pop(item, "")

    @staticmethod
    def before_msg(kw_dict):
        pre_msg = kw_dict.get('pre_msg', '')
        if pre_msg:
            LogUtil.hb_info(pre_msg)

    @staticmethod
    def set_log_stage(kw_dict):
        log_stage = kw_dict.get('log_stage', '')
        if log_stage:
            LogUtil.set_stage(log_stage)

    @staticmethod
    def remove_useless_space(cmd):
        while "" in cmd:
            cmd.remove("")
        return cmd

    @staticmethod
    def after_msg(kw_dict):
        after_msg = kw_dict.get('after_msg', '')
        if after_msg:
            LogUtil.hb_info(after_msg)

    @staticmethod
    def clear_log_stage(kw_dict):
        log_stage = kw_dict.get('log_stage', '')
        if log_stage:
            LogUtil.clear_stage()

    @staticmethod
    def handle_line(line, kw_dict):
        filter_function = kw_dict.get('custom_line_handle', False)
        if filter_function:
            return filter_function(line)
        else:
            return True, line

    @staticmethod
    def set_filter_print(log_mode, kw_dict):
        if kw_dict.get('log_filter', False) or log_mode == 'silent':
            HandleKwargs.filter_print = True

    @staticmethod
    def handle_print(line, log_mode):
        if HandleKwargs.filter_print:
            info = re.findall(HandleKwargs.compile_item_pattern, line)
            if len(info):
                LogUtil.hb_info(info[0], mode=log_mode)
        else:
            LogUtil.hb_info(line)


class SystemUtil(metaclass=NoInstance):
    @staticmethod
    def exec_command(cmd: list, log_path='out/build.log', exec_env=None, log_mode='normal',
                     **kwargs):
        raw_kwargs = copy.deepcopy(kwargs)
        HandleKwargs.remove_registry_kwargs(kwargs)

        HandleKwargs.set_log_stage(raw_kwargs)
        HandleKwargs.set_filter_print(log_mode, raw_kwargs)
        cmd = HandleKwargs.remove_useless_space(cmd)

        if not os.path.exists(os.path.dirname(log_path)):
            os.makedirs(os.path.dirname(log_path), exist_ok=True)

        HandleKwargs.before_msg(raw_kwargs)
        hidden_pattern = SensitiveHidden.load_sensitive_conf()
        with open(log_path, 'at', encoding='utf-8') as log_file:
            process = subprocess.Popen(cmd,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT,
                                       encoding='utf-8',
                                       env=exec_env,
                                       errors="ignore",
                                       **kwargs)
            for _line in iter(process.stdout.readline, ''):
                line = SensitiveHidden.hidden_sensitive_info(hidden_pattern, _line)
                keep_deal, new_line = HandleKwargs.handle_line(line, raw_kwargs)
                if keep_deal:
                    log_file.write(new_line)
                    HandleKwargs.handle_print(new_line, log_mode)

        process.wait()
        HandleKwargs.after_msg(raw_kwargs)
        HandleKwargs.clear_log_stage(raw_kwargs)

        ret_code = process.returncode
        if ret_code != 0:
            cmd_str = " ".join(cmd)
            LogUtil.hb_error(f"command failed: \"{cmd_str}\" , ret_code: {ret_code}")
            LogUtil.get_failed_log(log_path)

    @staticmethod
    def get_current_time(time_type: str = 'default'):
        if time_type == 'timestamp':
            return int(datetime.utcnow().timestamp() * 1000)
        if time_type == 'datetime':
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return datetime.now().replace(microsecond=0)


class ExecEnviron:
    def __init__(self):
        self._env = None

    @property
    def allenv(self):
        return self._env

    @property
    def allkeys(self):
        if self._env is None:
            return []
        return list(self._env.keys())

    def initenv(self):
        self._env = os.environ.copy()

    def allow(self, allowed_vars: list):
        if self._env is not None:
            allowed_env = {k: v for k, v in self._env.items() if k in allowed_vars}
            self._env = allowed_env


class SensitiveHidden:
    @staticmethod
    def determine_conf_file():
        config_file = os.path.join(CURRENT_BUILD_DIR, "sensitive_info_config.json")
        sensitive_config_ext = os.path.join(CURRENT_OHOS_ROOT, "out/products_ext/sensitive_info_config.json")
        if os.path.exists(sensitive_config_ext):
            config_file = sensitive_config_ext

        return config_file

    @staticmethod
    def parse_sensitive_conf(sensitive_config_file: str) -> set:
        hidden_pattern = set()

        if not os.path.isfile(sensitive_config_file):
            return hidden_pattern

        config = IoUtil.read_json_file(sensitive_config_file)
        hidden_pattern.update(config.get("keywords", []))

        for var_name in config.get("env_vars", []):
            env_value = os.getenv(var_name)
            if env_value:
                hidden_pattern.add(env_value)

        for pattern_str in config.get("regex_patterns", []):
            try:
                # compile regex ignore case
                hidden_pattern.add(re.compile(pattern_str, re.IGNORECASE))
            except re.error as e:
                raise ValueError(f"invalid regex pattern '{pattern_str}': {e}") from e

        return hidden_pattern

    @staticmethod
    def load_sensitive_conf() -> set:
        config_file = SensitiveHidden.determine_conf_file()

        try:
            hidden_pattern = SensitiveHidden.parse_sensitive_conf(config_file)
        except Exception as e:
            raise ValueError(f"{config_file} is invalid file, please check: {e}") from e

        return hidden_pattern

    @staticmethod
    def hidden_sensitive_info(hidden_pattern: set, text: str, replace_text: str = "******") -> str:
        if not hidden_pattern:
            return text
        hidden_text = text
        for pattern in hidden_pattern:
            if isinstance(pattern, str):
                hidden_text = hidden_text.replace(pattern, replace_text)
            elif isinstance(pattern, re.Pattern):
                hidden_text = pattern.sub(replace_text, hidden_text)
            else:
                continue

        return hidden_text
