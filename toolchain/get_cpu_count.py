#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# This script shows cpu count to specify capacity of action pool.

import multiprocessing
import os
import sys


def main():
    print(get_cpu_count())
    return 0


def get_cpu_count():
    cpu_count = 1
    try:
        cpu_count = multiprocessing.cpu_count()
    except OSError:
        pass
    quota_us_file = "/sys/fs/cgroup/cpu/cpu.cfs_quota_us"
    period_us_file = "/sys/fs/cgroup/cpu/cpu.cfs_period_us"
    if os.path.exists(quota_us_file) and os.path.exists(period_us_file):
        cfs_quota_us = -1
        cfs_period_us = 0
        try:
            with open(quota_us_file, 'r') as quota, open(period_us_file, 'r') as period:
                cfs_quota_us = int(quota.read().strip())
                cfs_period_us = int(period.read().strip())
        except IOError:
            pass

        if cfs_quota_us != -1 and cfs_period_us != 0:
            cpu_count = int(cfs_quota_us / cfs_period_us)
    return cpu_count


if __name__ == '__main__':
    sys.exit(main())
