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
#

import traceback

from resources.config import Config
from exceptions.ohosException import OHOSException
from util.logUtil import LogUtil


'''Description: Function decorator that catch all exception raised by target function,
                please DO NOT use this function directly 
@parameter: "func": The function to be decorated
@return:None

Usage:

@throw_exception
def foo():
    ...
    raise OHOSException('SOME ERROR HAPPENDED', '0000')
    ....
    
'''
def throw_exception(func):
    def wrapper(*args, **kwargs):
        try:
            r = func(*args, **kwargs)
        except OHOSException as exception:
            LogUtil.write_log(Config().log_path,
                              traceback.format_exc() + '\n',
                              'error')
            LogUtil.write_log(Config().log_path,
                              'Code:      {}'
                              '\n'
                              '\n'
                              'Reason:    {}\n'
                              '\n'
                              'Solution:  {}\n'
                              .format(exception._code, str(exception), exception.get_solution()), 'error')
            exit()
        except Exception as exception:
            LogUtil.write_log(Config().log_path, str(exception), 'error')
            exit()
        else:
            return r
    return wrapper
