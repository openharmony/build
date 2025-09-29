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

import sys
import re
import os

from containers.colors import Colors
from hb.helper.no_instance import NoInstance
from resources.global_var import STATUS_FILE, NINJA_DESCRIPTION
from util.io_util import IoUtil
from exceptions.ohos_exception import OHOSException


class LogLevel():
    INFO = 0
    WARNING = 1
    ERROR = 2
    DEBUG = 3


class LogUtil(metaclass=NoInstance):
    # static member for store current stage
    stage = ""

    @staticmethod
    def set_stage(stage):
        LogUtil.stage = stage

    @staticmethod
    def clear_stage():
        LogUtil.stage = ""

    @staticmethod
    def hb_info(msg, stage='', mode='normal'):
        level = 'info'
        if not stage:
            stage = LogUtil.stage
        if mode == 'silent':
            for line in str(msg).splitlines():
                sys.stdout.write('\033[K')
                sys.stdout.write(
                    '\r' + (LogUtil.message(level, line, stage)).strip('\n'))
                sys.stdout.flush()
        elif mode == 'normal':
            level = 'info'
            for line in str(msg).splitlines():
                sys.stdout.write(LogUtil.message(level, line, stage))
                sys.stdout.flush()

    @staticmethod
    def hb_warning(msg, stage=''):
        level = 'warning'
        if not stage:
            stage = LogUtil.stage
        for line in str(msg).splitlines():
            sys.stderr.write(LogUtil.message(level, line, stage))
            sys.stderr.flush()

    @staticmethod
    def hb_error(msg, stage=''):
        level = 'error'
        if not stage:
            stage = LogUtil.stage
        sys.stderr.write('\n')
        for line in str(msg).splitlines():
            sys.stderr.write(LogUtil.message(level, line, stage))
            sys.stderr.flush()

    @staticmethod
    def message(level, msg, stage=''):
        if isinstance(msg, str) and not msg.endswith('\n'):
            msg += '\n'
        if level == 'error':
            msg = msg.replace('error:', f'{Colors.ERROR}error{Colors.END}:')
            return f'{Colors.ERROR}[OHOS {level.upper()}]{Colors.END} {stage} {msg}'
        elif level == 'info':
            return f'[OHOS {level.upper()}] {stage} {msg}'
        else:
            return f'{Colors.WARNING}[OHOS {level.upper()}]{Colors.END} {stage} {msg}'

    @staticmethod
    def write_log(log_path, msg, level):
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        sys.stderr.write('\n')
        with open(log_path, 'at', encoding='utf-8') as log_file:
            for line in str(msg).splitlines():
                sys.stderr.write(LogUtil.message(level, line, LogUtil.stage))
                sys.stderr.flush()
                log_file.write(LogUtil.message(level, line, LogUtil.stage))

    @staticmethod
    def analyze_build_error(error_log, status_code_prefix):
        with open(error_log, 'rt', encoding='utf-8') as log_file:
            data = log_file.read()
            status_file = IoUtil.read_json_file(STATUS_FILE)
            choices = []
            status_map = {}
            for status_code, status in status_file.items():
                if not status_code.startswith(status_code_prefix):
                    continue
                if isinstance(status, dict) and status.get('pattern'):
                    choices.append(status['pattern'])
                    status_map[status['pattern']] = status.get('code')
            best_match = None
            best_ratio = 0
            for choice in choices:
                pattern = re.compile(choice, re.DOTALL)
                match = pattern.search(data)
                if not match:
                    continue
                ratio = len(match.group()) / len(data)
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = choice
            return_status_code = status_map.get(
                best_match) if best_match else f'{status_code_prefix}000'
        return return_status_code

    @staticmethod
    def get_gn_failed_log(log_path):
        error_log = os.path.join(os.path.dirname(log_path), 'error.log')
        is_gn_failed = False
        with open(log_path, 'rt', encoding='utf-8') as log_file:
            lines = log_file.readlines()
        error_lines = []
        for i, line in enumerate(lines):
            if line.startswith('ERROR at'):
                error_lines.extend(lines[i: i + 50])
                is_gn_failed = True
                break
        for log in error_lines[:50]:
            LogUtil.hb_error(log)
            with open(error_log, 'at', encoding='utf-8') as log_file:
                log_file.write(log + '\n')
        if is_gn_failed:
            return_status_code = LogUtil.analyze_build_error(error_log, '3')
            raise OHOSException(
                'GN Failed! Please check error in {}, and for more build information in {}'.format(
                    error_log, log_path), return_status_code)

    @staticmethod
    def get_ninja_failed_log(log_path):
        error_log = os.path.join(os.path.dirname(log_path), 'error.log')
        is_ninja_failed = False
        with open(log_path, 'rt', encoding='utf-8') as log_file:
            data = log_file.read()
        failed_pattern = re.compile(r'(ninja: (?:error|fatal):.*?)\n', re.DOTALL)
        failed_log = failed_pattern.findall(data)
        if failed_log:
            is_ninja_failed = True
        for log in failed_log:
            LogUtil.hb_error(log)
            with open(error_log, 'at', encoding='utf-8') as log_file:
                log_file.write(log)
        if is_ninja_failed:
            return_status_code = LogUtil.analyze_build_error(error_log, '4')
            raise OHOSException(
                'NINJA Failed! Please check error in {}, and for more build information in {}'.format(
                    error_log, log_path), return_status_code)

    @staticmethod
    def get_compiler_failed_pattern(cmd: list):
        # in verbose mode, output commands instead of descriptions.
        if any(flag in cmd for flag in ("-v", "--verbose")):
            prefix = r"\[\d+/\d+]"
        else:
            description_str = "|".join(re.escape(k) for k in NINJA_DESCRIPTION)
            prefix = rf'(?:\[\d+/\d+\]\s+\b(?:{description_str}))\b'

        pattern_str = rf'({prefix}.*?)(?={prefix}|ninja: build stopped)'
        failed_pattern = re.compile(pattern_str, re.DOTALL)

        return failed_pattern

    @staticmethod
    def get_compiler_failed_log(log_path, cmd: list):
        error_log = os.path.join(os.path.dirname(log_path), 'error.log')
        is_compiler_failed = False
        with open(log_path, 'rt', encoding='utf-8') as log_file:
            data = log_file.read()
        failed_pattern = LogUtil.get_compiler_failed_pattern(cmd)
        failed_log = failed_pattern.findall(data)
        if failed_log:
            is_compiler_failed = True
        for log in failed_log:
            if any(line.startswith("FAILED:") for line in log.splitlines()):
                LogUtil.hb_error(log)
                with open(error_log, 'at', encoding='utf-8') as log_file:
                    log_file.write(log)
        if is_compiler_failed:
            return_status_code = LogUtil.analyze_build_error(error_log, '4')
            raise OHOSException(
                'COMPILE Failed! Please check error in {}, and for more build information in {}'.format(
                    error_log, log_path), return_status_code)

    @staticmethod
    def get_failed_log(log_path, cmd: list):
        last_error_log = os.path.join(os.path.dirname(log_path), 'error.log')
        if os.path.exists(last_error_log):
            mtime = os.stat(last_error_log).st_mtime
            os.rename(
                last_error_log, '{}/error.{}.log'.format(os.path.dirname(last_error_log), mtime))
        LogUtil.get_gn_failed_log(log_path)
        LogUtil.get_ninja_failed_log(log_path)
        LogUtil.get_compiler_failed_log(log_path, cmd)
        raise OHOSException(
            'BUILD Failed! Please check build log for more information: {}'.format(log_path))
