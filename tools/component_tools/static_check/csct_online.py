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
import subprocess
from gn_check.check_gn_online import CheckGnOnline
from bundle_check.bundle_check_online import BundleCheckOnline
from csct_online_prehandle import GiteeCsctPrehandler


class CsctOnline(object):
    """This is a component static checker online class"""

    version = ""
    log_verbose = False
    pr_list = ""

    def __init__(self, pr_list="", log_verbose=False) -> None:
        self.version = "0.0.1"
        self.pr_list = pr_list
        self.log_verbose = log_verbose

    def __verbose_print(self, verbose_flag, print_content):
        if verbose_flag is True:
            print(print_content)

    def __print_pretty(self, errs_info):
        try:
            from prettytable import PrettyTable
            print('already exist prettytable')
        except Exception:
            print('no prettytable')
            ret = subprocess.Popen(
                [sys.executable, "-m", "pip", "install", "prettytable"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                errors="replace",
            )
            print('installing prettytable')
            try:
                _, __ = ret.communicate(timeout=120)
                print('prettytable installed successfully')
                from prettytable import PrettyTable
            except Exception:
                print('prettytable installed failed')


        table = PrettyTable(["文件", "定位", "违反规则", "错误说明"])
        table.add_rows(errs_info)
        table.align["文件"] = "l"
        table.align["定位"] = "l"
        table.align["错误说明"] = "l"
        info = table.get_string()
        print(
            "If you have any question, please access component static check rules:",
            "https://gitee.com/openharmony/docs/blob/master/zh-cn/device-dev/"
            "subsystems/subsys-build-component-building-rules.md",
            "or https://gitee.com/openharmony/build/tree/master/tools/component_tools/static_check/readme.md",
        )
        print("There are(is) {} error(s):\n".format(len(errs_info)))
        print(str(info))

    def csct_check_process(self):
        pr_list = self.pr_list
        self.__verbose_print(
            self.log_verbose,
            "\nCsct check begin!\tPull request list: {}.".format(pr_list),
        )
        csct_prehandler = GiteeCsctPrehandler(
            pr_list, "BUILD.gn", "bundle.json"
        )

        _, gn_errs = CheckGnOnline(csct_prehandler.get_diff_dict("BUILD.gn")).output()
        _, bundle_errs = BundleCheckOnline.check_diff(
            csct_prehandler.get_diff_dict("bundle.json")
        )

        errs_info = gn_errs + bundle_errs
        if len(errs_info) == 0:
            self.__verbose_print(self.log_verbose, "Result: without any errors.")
        else:
            self.__print_pretty(errs_info)

        self.__verbose_print(self.log_verbose, "Csct check end!\n")
        return errs_info


def add_options(version):
    parser = argparse.ArgumentParser(
        description=f"Component Static Check Tool Online version {version}",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        dest="verbose",
        default=False,
        help="verbose mode",
    )
    parser.add_argument(
        metavar="pr_list", type=str, dest="pr_list", help="pull request url list"
    )
    args = parser.parse_args()
    return args


def main():
    csct_online = CsctOnline()
    args = add_options(csct_online.version)
    csct_online.pr_list = args.pr_list
    csct_online.log_verbose = args.verbose
    errs_info = csct_online.csct_check_process()


if __name__ == "__main__":
    sys.exit(main())
