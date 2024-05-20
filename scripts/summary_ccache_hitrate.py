#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright (c) 2021 Huawei Device Co., Ltd.
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


def summary_ccache_new(ccache_log: str):
    hit_dir_num = 0
    hit_pre_num = 0
    mis_num = 0
    hit_rate = 0
    mis_rate = 0
    hit_dir_str = "Result: direct_cache_hit"
    hit_pre_str = "Result: preprocessed_cache_hit"
    mis_str = "Result: cache_miss"
    if os.path.exists(ccache_log):
        cmd = "grep -c \'{}\'  '{}'".format(hit_dir_str, ccache_log)
        hit_dir_num = int(
            subprocess.Popen(cmd, shell=True,
                             stdout=subprocess.PIPE).communicate()[0])
        cmd = "grep -c \'{}\'  '{}'".format(hit_pre_str, ccache_log)
        hit_pre_num = int(
            subprocess.Popen(cmd, shell=True,
                             stdout=subprocess.PIPE).communicate()[0])
        cmd = "grep -c \'{}\'  '{}'".format(mis_str, ccache_log)
        mis_num = int(
            subprocess.Popen(cmd, shell=True,
                             stdout=subprocess.PIPE).communicate()[0])
    sum_ccache = hit_dir_num + hit_pre_num + mis_num
    if sum_ccache != 0:
        hit_rate = (float(hit_dir_num) +
                    float(hit_pre_num)) / float(sum_ccache)
        mis_rate = float(mis_num) / float(sum_ccache)
    return hit_rate, mis_rate, hit_dir_num, hit_pre_num, mis_num


def summary_ccache_size():
    cache_size, ccache_version = "", ""
    ccache_exec = os.environ.get('CCACHE_EXEC')
    ccache_dir = os.environ.get('CCACHE_DIR')
    print("ccache_dir = {}, ccache_exec = {}".format(ccache_dir, ccache_exec))
    if ccache_exec is None or ccache_dir is None:
        print("ccache_exec or ccache_dir is None, summary ccache size failed...")
        return cache_size, ccache_version
    cmd = [ccache_exec, '-s', '-V']
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0].decode("utf-8").split("\n")
    cache_size_str = "Cache size"
    ccache_version_str = "ccache version"
    for line in process:
        if cache_size_str in line:
            cache_size = line.split(":")[1].strip()
        if ccache_version_str in line:
            ccache_version = line.split(" ")[2].strip()
    return cache_size, ccache_version


def main():
    if len(sys.argv) < 2:
        print("Error, please input the ccache log file path.")
        exit(-1)

    ccache_log = sys.argv[1]
    hit_rate = 0
    miss_rate = 0
    hit_dir_num = 0
    hit_pre_num = 0
    miss_num = 0
    cache_size = ""
    ccache_version = ""
    if os.path.exists(ccache_log):
        hit_rate, miss_rate, hit_dir_num, hit_pre_num, miss_num = summary_ccache_new(
            ccache_log)
        cache_size, ccache_version = summary_ccache_size()

    print(f"--------------------------------------------\n" +
          "ccache summary:\n" +
          "ccache version: " + ccache_version + "\n" +
          "cache hit (direct): " + str(hit_dir_num) + "\n" +
          "cache hit (preprocessed): " + str(hit_pre_num) + "\n" +
          "cache miss: " + str(miss_num) + "\n" +
          "hit rate: %.2f%% " % (hit_rate * 100) + "\n" +
          "miss rate: %.2f%% " % (miss_rate * 100) + "\n" +
          "Cache size (GB): " + cache_size + "\n" +
          "---------------------------------------------")


if __name__ == "__main__":
    main()
