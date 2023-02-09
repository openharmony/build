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
import sys
import importlib
import importlib.util


def is_in_ohos_dir():
    cur_dir = os.getcwd()
    while cur_dir != "/":
        global_var = os.path.join(
            cur_dir, 'build', 'hb', 'resources', 'global_var.py')
        if os.path.exists(global_var):
            return True, cur_dir
        cur_dir = os.path.dirname(cur_dir)
    return False, ''


def main():
    in_ohos_dir, ohos_root_path = is_in_ohos_dir()
    if in_ohos_dir :
        entry_path = os.path.join(os.path.abspath(os.path.relpath(
            ohos_root_path, os.path.curdir)), 'build', 'hb', 'main.py')
        spec = importlib.util.spec_from_file_location('main', entry_path)
        api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api)
        main_api = api.Main()
        main_api.main()
    else:
        raise Exception(
            "[OHOS_ERROR]: Please call hb utilities inside ohos source directory")


if __name__ == "__main__":
    sys.exit(main())
