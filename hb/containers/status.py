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
import traceback
import sys
from exceptions.ohos_exception import OHOSException
from util.log_util import LogUtil
from util.io_util import IoUtil
from resources.global_var import ROOT_CONFIG_FILE, CURRENT_OHOS_ROOT


def throw_exception(func):
    """Description: Function decorator that catch all exception raised by target function,
                please DO NOT use this function directly 
    @parameter: "func": The function to be decorated
    @return:None
    @OHOSException: The first digit of the code represents the compilation stage,
        '1', '2', '3', '4' corresponds to preloader, loader, gn, ninja stages respectively

    Usage:

    @throw_exception
    def foo():
        ...
        raise OHOSException('SOME ERROR HAPPENDED', '0000')
        ...

    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except OHOSException and Exception as exception:
            _code = ''
            _type = ''
            _desc = ''
            _solution = ''

            if isinstance(exception, OHOSException):
                _code = exception._code
                _type = exception.get_type()
                _desc = exception.get_desc()
                _solution = exception.get_solution()
            else:
                _code = '0000'
                _type = 'UNKNOWN ERROR TYPE'
                _desc = 'NO DESCRIPTION'
                _solution = 'NO SOLUTION'
            if not judge_indep():
                _print_formatted_tracebak(_code, str(exception), _type, _desc, _solution)
            else:
                print(exception)
                traceback.print_exc()
            exit(-1)
    return wrapper


def judge_indep():
    """Description: judge whether it is related to independent build
    """
    return sys.argv[1] == 'build' and (
            "--indep-build" in sys.argv[2:] or "-i" in sys.argv[2:] or sys.argv[-1] == "-t" or (
            "-t" in sys.argv and sys.argv[sys.argv.index("-t") + 1][0] == '-'))


def _print_formatted_tracebak(_code, _exception, _type, _desc, _solution):
    _log_path = ''
    if IoUtil.read_json_file(ROOT_CONFIG_FILE).get('out_path') is not None:
        _log_path = os.path.join(IoUtil.read_json_file(
            ROOT_CONFIG_FILE).get('out_path'), 'build.log')
    else:
        _log_path = os.path.join(CURRENT_OHOS_ROOT, 'out', 'build.log')
    if isinstance(_solution, list):
        _solution = '\n\t\t'.join(str(elem) for elem in _solution)
    LogUtil.write_log(_log_path, traceback.format_exc() + '\n', 'error')
    LogUtil.write_log(_log_path,
                      'Code:        {}'
                      '\n'
                      '\n'
                      'Reason:      {}'
                      '\n'
                      '\n'
                      'Error Type:  {}'
                      '\n'
                      '\n'
                      'Description: {}'
                      '\n'
                      '\n'
                      'Solution:    {}'
                      '\n'
                      '\n'
                      .format(_code, _exception, _type, _desc, _solution), 'error')