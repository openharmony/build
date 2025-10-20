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

import sys
import os
import argparse

from util.file_utils import read_json_file, write_json_file  # noqa: E402

PARTS_TEST_GNI_TEMPLATE = """
parts_test_list = [
  {}
]
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config-output-dir', required=True)
    args = parser.parse_args()

    test_filter_info_file = os.path.join(args.config_output_dir, "test_filter_info.json")
    parts_test_filter_list_file = os.path.join(args.config_output_dir, "parts_test_filter_list.gni")

    test_filter_info = read_json_file(test_filter_info_file)
    if test_filter_info:
        test_list_content = '"{}",'.format('",\n  "'.join(test_filter_info))
        write_file(parts_test_gni_file,
                           PARTS_TEST_GNI_TEMPLATE.format(test_list_content))

    return 0


if __name__ == '__main__':
    sys.exit(main())
