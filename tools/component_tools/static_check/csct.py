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

import bundle_check.bundle_json_check as CheckBd
import pandas as pd
from gn_check.check_gn import CheckGn
from prettytable import PrettyTable


class csctGlobal(object):
    """ This is a gn variable check class"""
    VERSION = '0.0.1'
    csct_path = ''
    ohos_root = ''
    repo_url = ''
    repo_num = ''
    diff_files_path = ''
    output_format = ''
    check_path = ''
    whitelist = ()

    def __init__(self) -> None:
        self.csct_path = sys.path[0]
        root = os.path.join(self.csct_path, '../../../..')
        self.ohos_root = os.path.normpath(root)
        whitelist_file = os.path.join(self.csct_path, 'config/csct_whitelist.conf')
        with open(whitelist_file, 'r') as f:
            whitelist = f.read().split('\n')
            self.whitelist = tuple(whitelist)

csctglb = csctGlobal()

def add_option(parser):
    parser.add_argument('-v', '--version',
                        action='version',
                        version=f'%(prog)s {csctglb.VERSION}.')
    parser.add_argument('-gd', '--generate_diff',
                        metavar=('repo', 'prNum'), dest='repo_pr', nargs=2, type=str,
                        help='generate diff files.')
    parser.add_argument('-cd', '--check_diffs',
                        metavar='diffFilesPath', dest='diff_files_path', nargs=1, type=str,
                        help='check all diff files as specific path.')
    parser.add_argument('-p',
                        metavar='path', type=str, dest='path',
                        help='check all files as specific path\
                        (the current directory by default).')
    parser.add_argument('-o',
                        metavar='stdout/xls/json', nargs=1, dest='output_format',
                        default="stdout", choices=['stdout', 'xls', 'json'], type=str,
                        help='specific output format(stdout by default).')

def store_args(args):
    if args.repo_pr is not None:
        csctglb.repo_url = args.repo_pr[0]
        csctglb.repo_num = args.repo_pr[1]
    csctglb.diff_files_path = args.diff_files_path
    csctglb.output_format = args.output_format
    csctglb.check_path = args.path

def start_check():
    print('---Start  check---\n')
    # check all gn
    cg = CheckGn(csctglb.ohos_root, check_path=csctglb.check_path)
    gn_errs = cg.output()

    # check all bundle.json
    dict_all_bundle_errs = CheckBd.check_all_bundle_json(csctglb.ohos_root)
    bundle_errs = CheckBd.BundleCheckTools.trans_to_df(dict_all_bundle_errs)

    if not os.path.exists('out'):
        os.mkdir('out')
    out_path = os.path.join(os.getcwd(), 'out')
    table = PrettyTable(gn_errs.columns.to_list())
    table.add_rows(gn_errs.values.tolist())
    table_str = table.get_string()
    with open(os.path.join(out_path, 'gn_problems.txt'),'w')as f:
        f.write(table_str)

    # merge excel
    output_path = os.path.join(out_path, "output_errors.xlsx")
    with pd.ExcelWriter(output_path) as writer:
        bundle_errs.to_excel(writer, sheet_name='bundle_check',index=None)
        gn_errs.to_excel(writer, sheet_name='gn_check',index=None)

    print('\nStatic check finish.\nPlease check: ' + output_path)
    return

def check_end():
    print('\n---End check---')
    return

def main():
    parser = argparse.ArgumentParser(
        description=f'Component Static Check Tool version {csctglb.VERSION}',
    )
    add_option(parser)
    args = parser.parse_args() 
    store_args(args)

    start_check()
    check_end()
    return 0

if __name__ == '__main__':
    sys.exit(main())
