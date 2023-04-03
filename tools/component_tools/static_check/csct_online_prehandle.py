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

import os
import sys
import re
import argparse
import subprocess
import logging


def add2dict(diff_dict, path, line_num: str, content):
    key = path
    value = [line_num, content]

    if key in diff_dict:
        value_list = diff_dict.pop(key)
        value_list.append(value)
    else:
        value_list = [value]

    diff_dict.update({key: value_list})


def __diff_match_file_start(control_block, line):
    pattern = "diff --git"
    if not line.startswith(pattern):
        return False

    control_block["line_num"] = 0
    control_block["fullpath"] = ""
    control_block["match_flag"] = False
    control_block["curr_key"] = ""
    control_block["is_new_file"] = False

    return True


def __diff_match_is_newfile(control_block, line):
    pattern = "new file"
    if not line.startswith(pattern):
        return False
        
    control_block["is_new_file"] = True
    return True


def __diff_match_filename_with_minus(control_block, line):
    pattern = "---\ (a/)?.*"
    if re.match(pattern, line) is None:
        return False

    control_block["match_flag"] = False
    return True


def __diff_match_filename_with_plus(control_block, line):
    pattern = "\+\+\+\ b/(.*)"
    if re.match(pattern, line) is None:
        return False

    for key in control_block["diff_dict"]:
        if re.search(key, line) is not None:
            control_block["curr_key"] = key
            res = re.match(pattern, line)
            control_block["fullpath"] = (
                "{}, {}".format(control_block["pull_request_url"], res.group(1).strip())
            )
            if control_block['is_new_file'] is True:
                control_block["fullpath"] = "%s%s" % (
                    control_block["fullpath"], "(new file)")
            control_block["match_flag"] = True
    return True


def __diff_match_start_linenum(control_block, line):
    pattern = "@@\ -[0-9]+,[0-9]+\ \+([0-9]+)(,[0-9]+)?\ @@.*"
    if control_block["match_flag"] is False or re.match(pattern, line) is None:
        return False

    res = re.match(pattern, line)
    control_block["line_num"] = int(res.group(1))
    return True


def __diff_match_code_line(control_block, line):
    diff_dict = control_block["diff_dict"]
    pattern1 = "[\ +-](.*)"
    pattern2 = "([\ +])?(.*)"
    if control_block["match_flag"] is False or re.match(pattern1, line) is None:
        return False

    res = re.match(pattern2, line)
    if res.group(1) == "+":
        add2dict(
            diff_dict[control_block["curr_key"]],
            control_block["fullpath"],
            control_block["line_num"],
            res.group(2),
        )
    if res.group(1) != "-":
        control_block["line_num"] = control_block["line_num"] + 1
    return True


def strip_diff(diff_dict, pull_request_url, gitee_pr_diff):
    control_block = {
        "line_num": 0,
        "fullpath": "",
        "match_flag": False,
        "curr_key": "",
        "diff_dict": diff_dict,
        "pull_request_url": pull_request_url,
        "is_new_file": False,
    }

    strip_diff_handlers = [
        __diff_match_file_start,
        __diff_match_is_newfile,
        __diff_match_filename_with_minus,
        __diff_match_filename_with_plus,
        __diff_match_start_linenum,
        __diff_match_code_line,
    ]

    for line in gitee_pr_diff.splitlines():
        for handler in strip_diff_handlers:
            if handler(control_block, line) is True:
                break


def get_diff_by_repo_pr_num(repo_url, pr_num):
    diff_url = "%spulls/%s.diff" % (repo_url, str(pr_num))
    cmd = "curl -L -s " + diff_url
    gitee_pr_diff = ""
    try:
        ret = subprocess.Popen(
            ["/usr/bin/curl", "-L", "-s", diff_url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            errors="replace",
        )
        gitee_pr_diff, errorout = ret.communicate()
        if len(errorout) != 0:
            logging.error("Popen error: ", errorout)
    except Exception as err:
        logging.error("error %s", err, cmd)

    return gitee_pr_diff


class GiteeCsctPrehandler:
    def __init__(self, pr_list: str, *patterns):
        self.diff_dict = {}
        for pattern in patterns:
            pattern_dict = {pattern: {}}
            self.diff_dict.update(pattern_dict)

        repo_pr_num_list = pr_list.split(";")
        for pr_item in repo_pr_num_list:
            pr_split_group = pr_item.split("pulls/")
            repo_url = pr_split_group[0].strip()
            pr_num = pr_split_group[1].strip("/")

            gitee_pr_diff = get_diff_by_repo_pr_num(repo_url, pr_num)
            strip_diff(self.diff_dict, pr_item, gitee_pr_diff)

    def clear_repo_num_file(self):
        self.diff_dict.clear()

    def get_diff_dict(self, pattern):
        ret_diff = {}
        if pattern in self.diff_dict.keys():
            ret_diff = self.diff_dict[pattern]
        return ret_diff


def test():
    if len(sys.argv) == 1:
        sys.stderr.write("test error: pr_list is empty.\n")
        return

    pr_list = sys.argv[1]
    csct_prehandler = GiteeCsctPrehandler(
        pr_list, "BUILD.gn", "bundle.json", ".gni")

    print("==================start get diff====================")
    print(csct_prehandler.get_diff_dict("BUILD.gn"))
    print("==================start get diff====================")
    print(csct_prehandler.get_diff_dict("bundle.json"))
    print("========================end=========================")


if __name__ == "__main__":
    sys.exit(test())
