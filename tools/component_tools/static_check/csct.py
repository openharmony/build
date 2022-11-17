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
import pandas as pd
from prettytable import PrettyTable

from gn_check.check_gn import CheckGn
from bundle_check.bundle_json_check import BundlesCheck


class CsctGlobal(object):
    """This is a gn variable check class"""

    VERSION = ""
    csct_path = ""
    ohos_root = ""
    repo_url = ""
    repo_num = ""
    diff_files_path = ""
    output_format = ""
    check_path = ""
    whitelist = ()

    def __init__(self) -> None:
        VERSION = "0.0.1"
        self.csct_path = sys.path[0]
        root = os.path.join(self.csct_path, "../../../..")
        self.ohos_root = os.path.normpath(root)
        whitelist_file = os.path.join(self.csct_path, "config/csct_whitelist.conf")
        with open(whitelist_file, "r") as file:
            whitelist = file.read().split("\n")
            self.whitelist = tuple(whitelist)


    def add_option(self, parser):
        parser.add_argument(
            "-v", "--version", action="version", version=f"%(prog)s {self.VERSION}."
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
        self.check_path = args.path


    def start_check(self):
        print("---Start  check---\n")
        # check all gn
        gn_errs = CheckGn(self.ohos_root, check_path=self.check_path).output()

        # check all bundle.json
        bundle_errs = BundlesCheck.to_df(self.check_path)

        if not os.path.exists("out"):
            os.mkdir("out")
        out_path = os.path.join(os.getcwd(), "out")
        table = PrettyTable(gn_errs.columns.to_list())
        table.add_rows(gn_errs.values.tolist())
        table_str = table.get_string()
        with open(os.path.join(out_path, "gn_problems.txt"), "w") as file:
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
        description=f"Component Static Check Tool version {csctglb.VERSION}",
    )
    csctglb.add_option(parser)
    args = parser.parse_args()
    csctglb.store_args(args)

    csctglb.start_check()
    csctglb.check_end()
    return 0


if __name__ == "__main__":
    sys.exit(main())
