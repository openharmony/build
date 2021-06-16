#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import sys
import os
import argparse
import shutil


def _merge_txt_file(ohos_notice, aosp_notice, output_notice):
    if not os.path.exists(ohos_notice):
        print("Warning, can not find the ohos notice file: {}.".format(
            ohos_notice))
        return

    if not os.path.exists(aosp_notice):
        print("Warning, can not find the aosp notice file: {}.".format(
            aosp_notice))
        shutil.move(ohos_notice, aosp_notice)
        return

    with open(output_notice, 'a') as aosp_file:
        with open(ohos_notice, 'r', errors='ignore') as _file:
            data = _file.readlines()
            del data[0]
            for line in data:
                aosp_file.write(line)
        with open(aosp_notice, 'r', errors='ignore') as _file:
            data = _file.readlines()
            del data[0]
            for line in data:
                aosp_file.write(line)

    if os.path.exists(ohos_notice):
        os.remove(ohos_notice)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ohos-notice',
                        help='ohos notice file',
                        required=True)
    parser.add_argument('--aosp-notice',
                        help='aosp notice file',
                        required=True)
    parser.add_argument('--output-notice',
                        help='final notice file',
                        required=True)
    args = parser.parse_args()

    # merge NOTICE.txt file
    _merge_txt_file(args.ohos_notice, args.aosp_notice, args.output_notice)

    return 0


if __name__ == '__main__':
    sys.exit(main())
