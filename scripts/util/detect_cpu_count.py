#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Huawei Device Co., Ltd.
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
import multiprocessing


def detect_cgroup_version():
    with os.popen("stat -fc %T /sys/fs/cgroup") as f:
        fs_type = f.read().strip()
        return "v2" if fs_type == "cgroup2fs" else "v1"


def get_cpuinfo_core_count():
    try:
        return multiprocessing.cpu_count()
    except IOError:
        return 8


def get_cpu_count_v2():
    with open("/proc/self/cgroup") as f:
        for line in f:
            if not line.startswith("0::"):
                continue
            path = line.strip().split("::")[1]
            cpu_max_path = "/sys/fs/cgroup{}/cpu.max".format(path)
            if not os.path.exists(cpu_max_path):
                continue
            return read_cgroup_info(cpu_max_path)
    return None


def read_cgroup_info(cpu_max_path):
    with open(cpu_max_path) as cf:
        quota, period = cf.read().strip().split()
        if quota == "max":
            return get_cpuinfo_core_count()
        return int(int(quota) / int(period))


def get_cpu_count_v1():
    quota_us_file = "/sys/fs/cgroup/cpu/cpu.cfs_quota_us"
    period_us_file = "/sys/fs/cgroup/cpu/cpu.cfs_period_us"

    if os.path.exists(quota_us_file) and os.path.exists(period_us_file):
        cfs_quota_us = -1
        cfs_period_us = 0
        try:
            with open(quota_us_file, "r") as quota, open(period_us_file, "r") as period:
                cfs_quota_us = int(quota.read().strip())
                cfs_period_us = int(period.read().strip())
        except IOError:
            return None
        
        if cfs_quota_us != -1 and cfs_period_us != 0:
            return int(cfs_quota_us / cfs_period_us)
    return None


def get_cpu_count():
    version = detect_cgroup_version()
    if version == "v2":
        result = get_cpu_count_v2()
    elif version == "v1":
        result = get_cpu_count_v1()
    else:
        result = get_cpuinfo_core_count()
    if not result:
        result = get_cpuinfo_core_count()
    return result


def main():
    print(get_cpu_count())


if __name__ == "__main__":
    main()
