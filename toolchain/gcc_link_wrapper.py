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


def is_lto_enabled(cmd: list) -> bool:
    lto_enabled = False
    for arg in cmd:
        if arg == "-fno-lto":
            lto_enabled = False
            continue
        if arg.startswith("-flto"):
            if arg == "-flto":
                lto_enabled = True
                continue
            if "=" in arg:
                value = arg.split("=", 1)[1].strip().lower()
                if value in ("false", "0", "off", "no"):
                    lto_enabled = False
                else:
                    lto_enabled = True
                continue
        if arg.startswith("-Wl,"):
            wl_args = arg[4:].split(",")
            for item in wl_args:
                if item.startswith("-plugin-opt=lto") or item.startswith("-plugin-opt=thinlto"):
                    return True
        if arg == "-plugin-liblto" or arg.startswith("-plugin=liblto"):
            return True
    return lto_enabled


def main():
    wrapper_utils.remove_duplicate_static_deps()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--strip', help='The strip binary to run', metavar='PATH')
    parser.add_argument('--unstripped-file', help='Executable file produced by linking command', metavar='FILE')
    parser.add_argument('--map-file', help=('Use --Wl,-Map to generate a map file. Will be gzipped if extension ends with .gz'), 
        metavar='FILE')
    parser.add_argument('--output', required=True, help='Final output executable file', metavar='FILE')
    parser.add_argument('--clang_rt_dso_path', help=('Clang asan runtime shared library'))
    parser.add_argument('command', nargs='+', help='Linking command')
    parser.add_argument('--mini-debug', action='store_true', default=False, help='Add .gnu_debugdata section for stripped sofile')
    parser.add_argument('--clang-base-dir', help='')
    parser.add_argument('--remove-unstripped-exe', action='store_true', default=False, help='remove exe.unstripped after used')
    parser.add_argument('--lcache-path', default='', help='link cache binary path')
    args = parser.parse_args()
    # Work-around for gold being slow-by-default. http://crbug.com/632230
    fast_env = dict(os.environ)
    fast_env['LC_ALL'] = 'C'
    if is_static_link(args.command):
        command = update_crt(args.command)
        if args.clang_rt_dso_path is not None:
            return 0
    else:
        command = args.command
    _has_ohos_target = any(a.startswith('--target=') and a.endswith('-linux-ohos') for a in command)
    _debug_log = os.environ.get('LCACHE_DEBUG_LOG', '')
    if _debug_log:
        with open(_debug_log, 'a') as f:
            f.write(f"[gcc_link_wrapper] lcache_path={args.lcache_path} _has_ohos_target={_has_ohos_target} is_lto={is_lto_enabled(command)}\n")
    if args.lcache_path != '' and _has_ohos_target:
        work_dir = os.getcwd()
        if os.path.exists(args.lcache_path):
            command.insert(0, 'python3')
            command.insert(1, args.lcache_path)
            command.insert(2, f'--work-dir={work_dir}')
    result = wrapper_utils.run_link_with_optional_map_file(
        command, env=fast_env, map_file=args.map_file)
    if result != 0:
        return result
    # Finally, strip the linked executable (if desired).
    if args.strip:
        result = subprocess.call(
            command_to_run(
                [args.strip, '-o', args.output, args.unstripped_file]))
    if args.mini_debug and args.unstripped_file and not args.unstripped_file.endswith(".exe") and not args.unstripped_file.endswith(".dll"):
        unstripped_libfile = os.path.abspath(args.unstripped_file)
        script_path = os.path.join(
            os.path.dirname(__file__), 'mini_debug_info.py')
        ohos_root_path = os.path.join(os.path.dirname(__file__), '../..')
        result = subprocess.call(
            wrapper_utils.command_to_run(
                ['python3', script_path, '--unstripped-path', unstripped_libfile, '--stripped-path', args.output,
                '--root-path', ohos_root_path, '--clang-base-dir', args.clang_base_dir]))
    if args.remove_unstripped_exe:
        os.remove(args.unstripped_file)
    return result


if __name__ == "__main__":
    sys.exit(main())

