#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
import sys
import subprocess
import argparse


def run(cxx_exe, args, output, is_header):
    run_cmdargs = [os.path.abspath(cxx_exe)]
    run_cmdargs.extend(args)
    if is_header:
        run_cmdargs.extend(["--header"])
    res_job = subprocess.run(run_cmdargs, capture_output=True)
    decode_messages = res_job.stderr.decode('utf-8')
    if decode_messages.rstrip():
        print(decode_messages, file=sys.stderr)
    if res_job.returncode != 0:
        return res_job.returncode
    sys.path.append(
        os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
    from scripts.util import build_utils
    with build_utils.atomic_output(output) as output:
        output.write(res_job.stdout)
    return 0


def main():
    parser = argparse.ArgumentParser("run_cxxbridge.py")
    parser.add_argument("--exe", help="The path of cxxbridge executable", required=True),
    parser.add_argument("--header", help="output h file with cxxbridge", required=True),
    parser.add_argument("--cc", help="output cc file with cxxbridge", required=True)

    parser.add_argument('args',
                        metavar='args',
                        nargs='+',
                        help="Args to pass through in script run_cxxbridge.py")
    args = parser.parse_args()
    ret = run(args.exe, args.args, args.cc, False)
    if ret != 0:
        return ret
    return run(args.exe, args.args, args.header, True)


if __name__ == '__main__':
    sys.exit(main())
