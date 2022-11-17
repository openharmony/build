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
import chardet
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


def strip_diff(diff_dict, gitee_path_prefix, gitee_pr_diff):
    pattern1 = "---\ (a/)?.*"
    pattern2 = "\+\+\+\ b/(.*)"
    pattern3 = "@@\ -[0-9]+,[0-9]+\ \+([0-9]+)(,[0-9]+)?\ @@.*"
    pattern4 = "[\ +-](.*)"
    pattern5 = "([\ +])?(.*)"
    line_num = 0
    fullpath = ""
    match_flag = False
    curr_key = ""

    for line in gitee_pr_diff.splitlines():
        if re.match(pattern1, line) is not None:
            match_flag = False
            continue
        elif re.match(pattern2, line) is not None:
            for key in diff_dict:
                if re.search(key, line) is not None:
                    curr_key = key
                    res = re.match(pattern2, line)
                    fullpath = gitee_path_prefix + res.group(1).strip()
                    match_flag = True
        elif match_flag is True and re.match(pattern3, line) is not None:
            res = re.match(pattern3, line)
            line_num = int(res.group(1))
        elif match_flag is True and re.match(pattern4, line) is not None:
            res = re.match(pattern5, line)
            if res.group(1) == "+":
                add2dict(diff_dict[curr_key], fullpath, line_num, res.group(2))
            if res.group(1) != "-":
                line_num = line_num + 1


def get_diff_by_repo_pr_num(repo_url, pr_num):
    diff_url = "%spulls/%s.diff" % (repo_url, str(pr_num))
    cmd = "curl -L -s " + diff_url
    gitee_pr_diff = ""
    try:
        ret = subprocess.Popen(
            ["curl", "-L", "-s", diff_url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            errors="replace",
        )
        gitee_pr_diff, errorout = ret.communicate(timeout=20)
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
            strip_diff(self.diff_dict, repo_url, gitee_pr_diff)

    def clear_repo_num_file(self):
        self.diff_dict.clear()

    def get_diff_dict(self, pattern):
        if pattern in self.diff_dict.keys():
            return self.diff_dict[pattern]
        return None


def test(repo_num_file):
    result = "test finish"
    csct_prehandler = GiteeCsctPrehandler(
        repo_num_file, "BUILD.gn", "bundle.json", ".gni"
    )

    print("==================start get diff====================")
    print(csct_prehandler.get_diff_dict("BUILD.gn"))
    print("==================start get diff====================")
    print(csct_prehandler.get_diff_dict("bundle.json"))
    print("========================end=========================")
    return True, result


if __name__ == "__main__":
    sys.exit(test("repo_prNum.conf"))
