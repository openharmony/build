#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import os
import sys
import subprocess

def csct_online(pr_list):
    """
    pr_list: pull request list, example: https://xxxxx/pulls/1410;https://xxxxx/pulls/250
    return: status: True or False
            resutl: check result
    """
    if len(pr_list) == 0:
        sys.stderr.write('error: pr_list is empty.\n')
        return True, " "

    status = True
    result = " "
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csct_project_path = os.path.join(root_dir, "build/tools/component_tools/static_check/")

    try:
        cmd = "python3 " + csct_project_path + "csct_online.py " + "'" + pr_list + "'"
        print(cmd)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, errors='replace')
        result, errcode = p.communicate()
        if len(errcode) != 0:
            print("Popen error: ", errcode)
            status = False
        else:
            status = False if len(result) != 0 else True
    except Exception as r:
        status = False
        print('error: ', r)

    return status, result

def test():
    if len(sys.argv) == 1:
        sys.stderr.write('test error: pr_list is empty.\n')
        return False

    prs = sys.argv[1]
    status, result = csct_online(prs)
    return status, result

if __name__ == '__main__':
    sys.exit(test())
