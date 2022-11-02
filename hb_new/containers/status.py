#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) 2022 Huawei Device Co., Ltd.
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
import traceback

from exceptions.ohos_exception import OHOSException
from util.log_util import LogUtil
from util.io_util import IoUtil
from resources.global_var import ROOT_CONFIG_FILE, CURRENT_OHOS_ROOT


'''Description: Function decorator that catch all exception raised by target function,
                please DO NOT use this function directly 
@parameter: "func": The function to be decorated
@return:None

Usage:

@throw_exception
def foo():
    ...
    raise OHOSException('SOME ERROR HAPPENDED', '0000')
    ...
    
'''


def throw_exception(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except OHOSException and Exception as exception:
            _code = ''
            _solution = ''

            if isinstance(exception, OHOSException):
                _code = exception._code
                _solution = exception.get_solution()
            else:
                _code = '0000'
                _solution = 'no solution'

            _print_formatted_tracebak(_code, str(exception), _solution)
            exit(-1)
    return wrapper


def _print_formatted_tracebak(_code, _exception, _solution):
    _log_path = ''
    if IoUtil.read_json_file(ROOT_CONFIG_FILE).get('out_path') is not None:
        _log_path = os.path.join(IoUtil.read_json_file(
            ROOT_CONFIG_FILE).get('out_path'), 'build.log')
    else:
        _log_path = os.path.join(CURRENT_OHOS_ROOT, 'out', 'build.log')
    LogUtil.write_log(_log_path, traceback.format_exc() + '\n', 'error')
    LogUtil.write_log(_log_path,
                      'Code:      {}'
                      '\n'
                      '\n'
                      'Reason:    {}'
                      '\n'
                      '\n'
                      'Solution:  {}'
                      '\n'
                      '\n'
                      .format(_code, _exception, _solution), 'error')
