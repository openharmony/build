#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Runs a linking command and optionally a strip command.

This script exists to avoid using complex shell commands in
gcc_toolchain.gni's tool("link"), in case the host running the compiler
does not have a POSIX-like shell (e.g. Windows).
"""

import argparse
import os
import subprocess
import sys

import wrapper_utils

# When running on a Windows host and using a toolchain whose tools are
# actually wrapper scripts (i.e. .bat files on Windows) rather than binary
# executables, the "command" to run has to be prefixed with this magic.
# The GN toolchain definitions take care of that for when GN/Ninja is
# running the tool directly.  When that command is passed in to this
# script, it appears as a unitary string but needs to be split up so that
# just 'cmd' is the actual command given to Python's subprocess module.
BAT_PREFIX = 'cmd /c call '


def command_to_run(command):
    if command[0].startswith(BAT_PREFIX):
        command = command[0].split(None, 3) + command[1:]
    return command


def is_static_link(command):
    if "-static" in command:
        return True
    else:
        return False


""" since static link and dynamic link have different CRT files on ohos,
and we use dynamic link CRT files as default, so when link statically,
we need change the CRT files
"""


def update_crt(command):
    for item in command:
        if str(item).find("crtbegin_dynamic.o") >= 0:
            index = command.index(item)
            new_crtbegin = str(item).replace("crtbegin_dynamic.o",
                                             "crtbegin_static.o")
            command[index] = new_crtbegin
    return command


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--strip',
                        help='The strip binary to run',
                        metavar='PATH')
    parser.add_argument('--unstripped-file',
                        help='Executable file produced by linking command',
                        metavar='FILE')
    parser.add_argument('--map-file',
                        help=('Use --Wl,-Map to generate a map file. Will be '
                              'gzipped if extension ends with .gz'),
                        metavar='FILE')
    parser.add_argument('--output',
                        required=True,
                        help='Final output executable file',
                        metavar='FILE')
    parser.add_argument('--clang_rt_dso_path',
                        help=('Clang asan runtime shared library'))
    parser.add_argument('command', nargs='+', help='Linking command')
    parser.add_argument('--mini-debug',
                        action='store_true',
                        default=False,
                        help='Add .gnu_debugdata section for stripped sofile')
    args = parser.parse_args()

    result = subprocess.call(
                wrapper_utils.command_to_run(args.command))
                
    if result != 0:
        return result

    # Finally, strip the linked executable (if desired).
    if args.strip:
        result = subprocess.call(
            command_to_run(
                [args.strip, '-o', args.output, args.unstripped_file]))

    if args.mini_debug and not args.unstripped_file.endswith(".exe"):
        unstripped_libfile = os.path.abspath(args.unstripped_file)
        script_path = os.path.join(
            os.path.dirname(__file__), 'mini_debug_info.py')
        ohos_root_path = os.path.join(os.path.dirname(__file__), '../..')
        result = subprocess.call(
            wrapper_utils.command_to_run(
                ['python3', script_path, '--unstripped-path', unstripped_libfile, '--stripped-path', args.output,
                '--root-path', ohos_root_path]))

    return result


if __name__ == "__main__":
    sys.exit(main())
