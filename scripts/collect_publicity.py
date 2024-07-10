#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2024 Huawei Device Co., Ltd.
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
import os
import sys
import shutil

from util.build_utils import touch


def parse_args(args):
    parser = argparse.ArgumentParser()

    parser.add_argument("--source", help="specify publicity xml")
    parser.add_argument("--output", required=True, help="specify publicity output")

    options = parser.parse_args(args)
    return options


def main(args):
    options = parse_args(args)

    dest_dir = os.path.dirname(options.output)
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir, exist_ok=True)

    if os.path.exists(options.output):
        os.unlink(options.output)

    if not options.source:
        # touch an empty publicity.xml
        touch(options.output)
        return 0

    shutil.copy2(options.source, options.output)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
