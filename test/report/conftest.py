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

    metadata['System Name'] = platform.system()
    metadata['System Architecture Information'] = platform.machine()
    metadata['Python Version'] = sys.version


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
