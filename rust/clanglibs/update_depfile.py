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

import argparse
import sys
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--filename', required=True)
    parser.add_argument('--type', default='file')
    args = parser.parse_args()
    if args.type == 'file':
        result = os.path.exists(
            args.filename) and os.path.isfile(args.filename)
    elif args.type == 'dir':
        result = os.path.exists(args.filename) and os.path.isdir(args.filename)
    else:
        result = False
    sys.stdout.write(str(result))
    if result:
        os.remove(args.filename)
    return 0


if __name__ == '__main__':
    sys.exit(main())
