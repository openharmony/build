#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""
1. add {{ldflags}} and extend everyone in {{ldflags}} to -Clink-args=%s.
2. replace blank with newline in .rsp file because of rustc.
3. add {{rustenv}} and in order to avoid ninja can't incremental compiling,
   delete them from .d files.
"""

import argparse
import pathlib
import subprocess
import os
import sys
import re

import rust_strip
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.util import build_utils  # noqa: E402


def exec_formatted_command(args):
    remaining_args = args.args

    ldflags_separator = remaining_args.index("LDFLAGS")
    rustenv_separator = remaining_args.index("RUSTENV", ldflags_separator)
    rustc_args = remaining_args[:ldflags_separator]
    ldflags = remaining_args[ldflags_separator + 1:rustenv_separator]
    rustenv = remaining_args[rustenv_separator + 1:]

    rustc_args.extend(["-Clink-arg=%s" % arg for arg in ldflags])
    rustc_args.insert(0, args.rustc)

    # Workaround for https://bugs.chromium.org/p/gn/issues/detail?id=249
    if args.rsp:
        with open(args.rsp) as rspfile:
            rsp_args = [l.rstrip() for l in rspfile.read().split(' ') if l.rstrip()]
        with open(args.rsp, 'w') as rspfile:
            rspfile.write("\n".join(rsp_args))
        rustc_args.append(f'@{args.rsp}')

    env = os.environ.copy()
    fixed_env_vars = []
    for item in rustenv:
        (k, v) = item.split("=", 1)
        env[k] = v
        fixed_env_vars.append(k)

    r = subprocess.run([args.clippy_driver, *rustc_args], env=env, check=False)
    if r.returncode != 0:
        sys.exit(r.returncode)

    # Now edit the depfile produced
    if args.depfile is not None:
        env_dep_re = re.compile("# env-dep:(.*)=.*")
        replacement_lines = []
        dirty = False
        with open(args.depfile, encoding="utf-8") as d:
            for line in d:
                m = env_dep_re.match(line)
                if m and m.group(1) in fixed_env_vars:
                    dirty = True  # skip this line
                else:
                    replacement_lines.append(line)
        if dirty:  # we made a change, let's write out the file
            with build_utils.atomic_output(args.depfile) as output:
                output.write("\n".join(replacement_lines).encode("utf-8"))
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--clippy-driver', required=True, type=pathlib.Path)
    parser.add_argument('--rustc', required=True, type=pathlib.Path)
    parser.add_argument('--depfile', type=pathlib.Path)
    parser.add_argument('--rsp', type=pathlib.Path)
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
