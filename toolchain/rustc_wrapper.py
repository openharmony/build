#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2022 Huawei Device Co., Ltd.
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

"""
1. add {{ldflags}} and extend everyone in {{ldflags}} to -Clink-args=%s.
2. replace blank with newline in .rsp file because of rustc.
3. add {{rustenv}} and in order to avoid ninja can't incremental compiling,
   delete them from .d files.
"""

import os
import stat
import sys
import re
import argparse
import pathlib
import subprocess

import rust_strip
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.util import build_utils  # noqa: E402


def exec_formatted_command(args):
    remaining_args = args.args

    ldflags_index = remaining_args.index("LDFLAGS")
    rustenv_index = remaining_args.index("RUSTENV", ldflags_index)
    rustc_args = remaining_args[:ldflags_index]
    ldflags = remaining_args[ldflags_index + 1:rustenv_index]
    rustenv = remaining_args[rustenv_index + 1:]

    rustc_args.extend(["-Clink-arg=%s" % arg for arg in ldflags])
    rustc_args.insert(0, args.rustc)

    if args.rsp:
        flags = os.O_WRONLY
        modes = stat.S_IWUSR | stat.S_IRUSR
        with open(args.rsp) as rspfile:
            rsp_content = [l.rstrip() for l in rspfile.read().split(' ') if l.rstrip()]
        with open(args.rsp, 'w') as rspfile:
            rspfile.write("\n".join(rsp_content))
        rustc_args.append(f'@{args.rsp}')

    env = os.environ.copy()
    fixed_env_vars = []
    for item in rustenv:
        (key, value) = item.split("=", 1)
        env[key] = value
        fixed_env_vars.append(key)

    ret = subprocess.run([args.clippy_driver, *rustc_args], env=env, check=False)
    if ret.returncode != 0:
        sys.exit(ret.returncode)

    if args.depfile is not None:
        env_dep_re = re.compile("# env-dep:(.*)=.*")
        replacement_lines = []
        dirty = False
        with open(args.depfile, encoding="utf-8") as depfile:
            for line in depfile:
                matched = env_dep_re.match(line)
                if matched and matched.group(1) in fixed_env_vars:
                    dirty = True
                else:
                    replacement_lines.append(line)
        if dirty:
            with build_utils.atomic_output(args.depfile) as output:
                output.write("\n".join(replacement_lines).encode("utf-8"))
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--clippy-driver',
                        required=True,
                        type=pathlib.Path)
    parser.add_argument('--rustc',
                        required=True,
                        type=pathlib.Path)
    parser.add_argument('--depfile',
                        type=pathlib.Path)
    parser.add_argument('--rsp',
                        type=pathlib.Path)
    parser.add_argument('--strip',
                        help='The strip binary to run',
                        metavar='PATH')
    parser.add_argument('--unstripped-file',
                        help='Executable file produced by linking command',
                        metavar='FILE')
    parser.add_argument('--output',
                        help='Final output executable file',
                        metavar='FILE')
    parser.add_argument('--mini-debug',
                        action='store_true',
                        default=False,
                        help='Add .gnu_debugdata section for stripped sofile')

    parser.add_argument('args', metavar='ARG', nargs='+')

    args = parser.parse_args()

    result = exec_formatted_command(args)
    if result != 0:
        return result
    if args.strip:
        result = rust_strip.do_strip(args.strip, args.output, args.unstripped_file, args.mini_debug)
    return result


if __name__ == '__main__':
    sys.exit(main())
