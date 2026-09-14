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


def summary_lcache(lcache_log: str):
    hit_num = 0
    miss_num = 0
    hit_str = "LINK_CACHE_HIT"
    miss_str = "LINK_CACHE_MISS"
    if os.path.exists(lcache_log):
        try:
            cmd = "grep -c '{}' '{}'".format(hit_str, lcache_log)
            hit_num = int(
                subprocess.Popen(cmd, shell=True,
                                 stdout=subprocess.PIPE).communicate()[0])
        except ValueError:
            hit_num = 0
        try:
            cmd = "grep -c '{}' '{}'".format(miss_str, lcache_log)
            miss_num = int(
                subprocess.Popen(cmd, shell=True,
                                 stdout=subprocess.PIPE).communicate()[0])
        except ValueError:
            miss_num = 0
    total = hit_num + miss_num
    hit_rate = 0.0
    if total != 0:
        hit_rate = float(hit_num) / float(total)
    return hit_rate, hit_num, miss_num


def main():
    if len(sys.argv) < 2:
        print("Error, please input the lcache log file path.")
        exit(-1)
    
    lcache_log = sys.argv[1]
    hit_rate = 0.0
    hit_num = 0
    miss_num = 0
    if os.path.exists(lcache_log):
        hit_rate, hit_num, miss_num = summary_lcache(lcache_log)
    
    print("============================================\n" +
          "link cache summary:\n" +
          "cache hit: " + str(hit_num) + "\n" +
          "cache miss: " + str(miss_num) + "\n" +
          "hit rate: %.2f%% " % (hit_rate * 100) + "\n" +
          "============================================")


if __name__ == "__main__":
    main()
