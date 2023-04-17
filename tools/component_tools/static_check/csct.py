#!/usr/bin/env python3
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
import stat
import xml.etree.ElementTree as ET
import pandas as pd
from prettytable import PrettyTable

from gn_check.check_gn import CheckGn
from bundle_check.bundle_json_check import BundlesCheck


class CsctGlobal(object):
    """This is a gn variable check class"""

    version = ""
    csct_path = ""
    ohos_root = ""
    repo_url = ""
    repo_num = ""
    diff_files_path = ""
    output_format = ""
    check_path = ""
    whitelist = ()

    def __init__(self) -> None:
        version = "0.0.1"
        self.csct_path = sys.path[0]
        root = os.path.join(self.csct_path, "../../../..")
        self.ohos_root = os.path.normpath(root)
        self.whitelist = tuple()

    def load_ohos_xml(self, path):
        ret_dict = dict()
        tree = ET.parse(path)
        root = tree.getroot()
        for node in root.iter():
            if node.tag != 'project':
                continue
            repo_info = node.attrib
            ret_item = {repo_info['path']: repo_info['groups']}
            ret_dict.update(ret_item)
        return ret_dict

    def handle_white_dir(self):
        xml_dict = self.load_ohos_xml(os.path.join(
            self.ohos_root, '.repo/manifests/ohos/ohos.xml'))
        ret_list = ['device', 'vendor', 'build', 'third_party', 'out']
        for key, vlaues in xml_dict.items():
            if key.startswith('third_party'):
                continue
            if vlaues.find('ohos:mini') != -1:
                ret_list.append(key)
            elif vlaues.find('ohos:small') != -1:
                ret_list.append(key)

        return tuple(ret_list)

    def add_option(self, parser):
        parser.add_argument(
            "-w",
            "--white_dir_on",
            dest="white_dir_settings",
            type=str,
            default="on",
            choices=["on", "off"],
            help="turn on white dir function or not",
        )
        parser.add_argument(
            "-v", "--version", action="version", version=f"%(prog)s {self.version}."
        )
        parser.add_argument(
            "-gd",
            "--generate_diff",
            metavar=("repo", "prNum"),
            dest="repo_pr",
            nargs=2,
            type=str,
            help="generate diff files.",
        )
        parser.add_argument(
            "-cd",
            "--check_diffs",
            metavar="diffFilesPath",
            dest="diff_files_path",
            nargs=1,
            type=str,
            help="check all diff files as specific path.",
        )
        parser.add_argument(
            "-p",
            metavar="path",
            type=str,
            dest="path",
            help="check all files as specific path\
                            (the current directory by default).",
        )
        parser.add_argument(
            "-o",
            metavar="stdout/xls/json",
            nargs=1,
            dest="output_format",
            default="stdout",
            choices=["stdout", "xls", "json"],
            type=str,
            help="specific output format(stdout by default).",
        )

    def store_args(self, args):
        if args.repo_pr is not None:
            self.repo_url = args.repo_pr[0]
            self.repo_num = args.repo_pr[1]
        self.diff_files_path = args.diff_files_path
        self.output_format = args.output_format
        if (args.path):
            self.check_path = os.path.normpath(args.path)
        self.white_dir_settings = args.white_dir_settings

    def pre_check(self):
        if self.white_dir_settings == 'on':
            self.whitelist = self.handle_white_dir()

    def start_check(self):
        print("---Start  check---\n")
        # check all gn
        gn_errs = CheckGn(self.ohos_root, black_dir=self.whitelist,
                          check_path=self.check_path).output()

        # check all bundle.json
        bundle_errs = BundlesCheck.to_df(self.check_path)

        if not os.path.exists("out"):
            os.mkdir("out")
        out_path = os.path.join(os.getcwd(), "out")
        table = PrettyTable(gn_errs.columns.to_list())
        table.add_rows(gn_errs.values.tolist())
        table_str = table.get_string()
        flags = os.O_WRONLY | os.O_CREAT
        modes = stat.S_IWUSR | stat.S_IRUSR
        with os.fdopen(
            os.open(os.path.join(out_path, "gn_problems.txt"), flags, modes), "w"
        ) as file:
            file.write(table_str)

        # merge excel
        output_path = os.path.join(out_path, "output_errors.xlsx")
        with pd.ExcelWriter(output_path) as writer:
            bundle_errs.to_excel(writer, sheet_name="bundle_check", index=None)
            gn_errs.to_excel(writer, sheet_name="gn_check", index=None)

        print("\nStatic check finish.\nPlease check: " + output_path)
        return

    def check_end(self):
        print("\n---End check---")
        return


def main():
    csctglb = CsctGlobal()
    parser = argparse.ArgumentParser(
        description=f"Component Static Check Tool version {csctglb.version}",
    )
    csctglb.add_option(parser)
    args = parser.parse_args()
    csctglb.store_args(args)
    csctglb.pre_check()
    csctglb.start_check()
    csctglb.check_end()
    return 0


if __name__ == "__main__":
    sys.exit(main())
