#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) 2023 Huawei Device Co., Ltd.
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
import platform
import sys

from py.xml import html
import pytest
import time


def pytest_html_report_title(report):
    report.title = "OpenHarmony Build Test Report"


@pytest.mark.optionalhook
def pytest_metadata(metadata):
    metadata.clear()

    metadata['Python Version'] = sys.version
    metadata['Cpu Count'] = os.cpu_count()
    metadata["System Info"] = platform.platform()
    try:
        disk_info = os.statvfs('/')
        total_disk = round(float(disk_info.f_frsize * disk_info.f_blocks) / (1024 ** 3), 4)
        metadata["Disk Size"] = "{} GB".format(total_disk)

        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
        total_memory_line = [line for line in lines if line.startswith('MemTotal')]
        total_memory = round(float(total_memory_line[0].split()[1]) / (1024 ** 2), 4) if total_memory_line else " "
        metadata["Totla Memory"] = "{} GB".format(total_memory)
    except Exception as e:
        print(e)


def pytest_html_results_table_header(cells):
    cells.insert(2, html.th("Description", class_="sortable desc", col="desc"))
    cells.insert(1, html.th("Time", class_="sortable time", col="time"))
    cells.pop()


def pytest_html_results_table_row(report, cells):
    cells.insert(2, html.th(report.description))
    cells.insert(1, html.th(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), class_="col-time"))
    cells.pop()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if str(item.function.__doc__) != "None":
        report.description = str(item.function.__doc__)
    else:
        report.description = "this is description info"

