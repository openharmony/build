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

import argparse
import os
import sys
import subprocess
from gn_check.check_gn_online import CheckGnOnline
from bundle_check.bundle_json_check_online import BundleCheckTools
from csct_online_prehandle import GiteeCsctPrehandler

def auto_install_required_package():
    cmd = '{} -m pip install prettytable'.format(sys.executable)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, errors='replace')
    _, __ = p.communicate()
    return 0

if auto_install_required_package() == 0:
    from prettytable import PrettyTable

VERSION='0.0.1'

def verbose_print(verbose_flag, print_content):
    if (verbose_flag == True):
        print(print_content)

def main():
    parser = argparse.ArgumentParser(
        description=f'Component Static Check Tool Online version {VERSION}',
    )
    parser.add_argument('-v', '--verbose', action='store_true',
                        dest='verbose', default=False,
                        help='verbose mode')
    parser.add_argument(metavar='pr_list', type=str, dest='pr_list',
                        help='pull request url list')
    args = parser.parse_args()
    pr_list = args.pr_list
    v_flag = args.verbose

    verbose_print(v_flag, '\nCsct check begin!')
    verbose_print(v_flag, '\tPull request list: {}.'.format(pr_list))
    csct_prehandler = GiteeCsctPrehandler(pr_list, "BUILD.gn", "bundle.json", ".gni")
    gn_status, gn_errs = CheckGnOnline(csct_prehandler.get_diff_dict("BUILD.gn")).output()
    gni_status, gni_errs = CheckGnOnline(csct_prehandler.get_diff_dict(".gni")).output()
    bundle_status, bundle_errs = BundleCheckTools.check_diff(csct_prehandler.get_diff_dict("bundle.json"))
    errs_info = bundle_errs + gn_errs + gni_errs
    status = gn_status and gni_status and bundle_status
    verbose_print(v_flag, 'gn_errs {}, gni_errs {}, bundle_errs{}'.format(len(gn_errs), len(gni_errs), len(bundle_errs)))
    verbose_print(v_flag, 'Csct check end!\n')

    if len(errs_info)==0:
        verbose_print(v_flag, 'Result: without any errors.')
        return

    table = PrettyTable(['文件', '定位', '违反规则', '错误说明'])
    table.add_rows(errs_info)
    table.align['文件'] = 'l'
    table.align['定位'] = 'l'
    table.align['错误说明'] = 'l'
    info = table.get_string()
    print('If you have any question, please access component static check rules:',
    'https://gitee.com/openharmony/docs/blob/master/zh-cn/device-dev/subsystems/subsys-build-component-building-rules.md',
    'or https://gitee.com/openharmony/build/tree/master/tools/component_tools/static_check/readme.md')
    print('There are(is) {} error(s):\n'.format(len(errs_info)))
    print(str(info))
    return

if __name__ == '__main__':
    sys.exit(main())
