#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Runs 'ld -shared' and generates a .TOC file that's untouched when unchanged.

This script exists to avoid using complex shell commands in
gcc_toolchain.gni's tool("solink"), in case the host running the compiler
does not have a POSIX-like shell (e.g. Windows).
"""

import argparse
import os
import subprocess
import sys
import shutil
import json

import wrapper_utils


def collect_soname(args):
    """Replaces: readelf -d $sofile | grep SONAME"""
    toc = ''
    readelf = subprocess.Popen(wrapper_utils.command_to_run(
        [args.readelf, '-d', args.sofile]),
        stdout=subprocess.PIPE,
        bufsize=-1)
    for line in readelf.stdout:
        if b'SONAME' in line:
            toc += line.decode()
    return readelf.wait(), toc


def collect_dyn_sym(args):
    """Replaces: nm --format=posix -g -D $sofile | cut -f1-2 -d' '"""
    toc = ''
    _command = [args.nm]
    if args.sofile.endswith('.dll'):
        _command.append('--extern-only')
    else:
        _command.extend(['--format=posix', '-g', '-D'])
    _command.append(args.sofile)
    nm = subprocess.Popen(wrapper_utils.command_to_run(_command),
                          stdout=subprocess.PIPE,
                          bufsize=-1)
    for line in nm.stdout:
        toc += '{}\n'.format(' '.join(line.decode().split(' ', 2)[:2]))
    return nm.wait(), toc


def collect_toc(args):
    result, toc = collect_soname(args)
    if result == 0:
        result, dynsym = collect_dyn_sym(args)
        toc += dynsym
    return result, toc


def update_toc(tocfile, toc):
    if os.path.exists(tocfile):
        with open(tocfile, 'r') as f:
            old_toc = f.read()
    else:
        old_toc = None
    if toc != old_toc:
        with open(tocfile, 'w') as fp:
            fp.write(toc)


def reformat_rsp_file(rspfile):
    """ Move all implibs from --whole-archive section"""
    with open(rspfile, "r") as fi:
        rspcontent = fi.read()
    result = []
    implibs = []
    naflag = False
    for arg in rspcontent.split(" "):
        if naflag and arg.endswith(".lib"):
            implibs.append(arg)
            continue
        result.append(arg)
        if arg == "-Wl,--whole-archive":
            naflag = True
            continue
        if arg == "-Wl,--no-whole-archive":
            naflag = False
            result.extend(implibs)

    with open(rspfile, "w") as fo:
        fo.write(" ".join(result))


def get_install_dest_dir(args):
    file_list = os.listdir(args.target_out_dir)
    target_name = args.target_name
    match_file = f'{target_name}_module_info.json'
    if not f'{target_name}_module_info.json' in file_list:
        return None
    with open(os.path.join(args.target_out_dir, match_file), "r") as f:
        module_info = json.load(f)
        dest_dirs = module_info.get("dest")
        for dest_dir in dest_dirs:
            if dest_dir.startswith("system"):
                return dest_dir
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--readelf',
                        required=True,
                        help='The readelf binary to run',
                        metavar='PATH')
    parser.add_argument('--nm',
                        required=True,
                        help='The nm binary to run',
                        metavar='PATH')
    parser.add_argument('--strip',
                        help='The strip binary to run',
                        metavar='PATH')
    parser.add_argument('--strip-debug-whitelist',
                        help='The strip debug whitelist, lines of which are names of shared objects with .symtab kept.',
                        metavar='PATH')
    parser.add_argument('--sofile',
                        required=True,
                        help='Shared object file produced by linking command',
                        metavar='FILE')
    parser.add_argument('--tocfile',
                        required=False,
                        help='Output table-of-contents file',
                        metavar='FILE')
    parser.add_argument('--map-file',
                        help=('Use --Wl,-Map to generate a map file. Will be '
                              'gzipped if extension ends with .gz'),
                        metavar='FILE')
    parser.add_argument('--output',
                        required=True,
                        help='Final output shared object file',
                        metavar='FILE')
    parser.add_argument('--libfile', required=False, metavar='FILE')
    parser.add_argument('command', nargs='+', help='Linking command')
    parser.add_argument('--mini-debug',
                        action='store_true',
                        default=False,
                        help='Add .gnu_debugdata section for stripped sofile')
    parser.add_argument('--target-name', help='')
    parser.add_argument('--target-out-dir', help='')
    parser.add_argument('--allowed-lib-list', help='')
    parser.add_argument('--clang-base-dir', help='')
    args = parser.parse_args()

    if args.sofile.endswith(".dll"):
        rspfile = None
        for a in args.command:
            if a[0] == "@":
                rspfile = a[1:]
                break
        if rspfile:
            reformat_rsp_file(rspfile)
    # Work-around for gold being slow-by-default. http://crbug.com/632230
    fast_env = dict(os.environ)
    fast_env['LC_ALL'] = 'C'

    # First, run the actual link.
    command = wrapper_utils.command_to_run(args.command)
    result = wrapper_utils.run_link_with_optional_map_file(
        command, env=fast_env, map_file=args.map_file)

    if result != 0:
        return result

    # Next, generate the contents of the TOC file.
    result, toc = collect_toc(args)
    if result != 0:
        return result

    # If there is an existing TOC file with identical contents, leave it alone.
    # Otherwise, write out the TOC file.
    if args.tocfile:
        update_toc(args.tocfile, toc)

    # Finally, strip the linked shared object file (if desired).
    if args.strip:
        strip_option = []
        strip_command = [args.strip, '-o', args.output]

        #ADLT so should not be stripped
        if args.target_out_dir and os.path.exists(args.target_out_dir):
            install_dest = get_install_dest_dir(args)
        else:
            install_dest = None
        if install_dest:
            with open(args.allowed_lib_list, 'r') as f:
                lines = f.readlines()
            lines = [line.strip()[1:] for line in lines]
            if install_dest in lines:
                strip_option.extend(['-S'])
        if args.strip_debug_whitelist:
            with open(args.strip_debug_whitelist, 'r') as whitelist:
                for strip_debug_sofile in whitelist.readlines():
                    if args.sofile.endswith(strip_debug_sofile.strip()):
                        strip_option.extend(['--strip-debug', '-R', '.comment'])
                        break
        strip_command.extend(strip_option)

        strip_command.append(args.sofile)
        result = subprocess.call(
            wrapper_utils.command_to_run(strip_command))
    if args.libfile:
        libfile_name = os.path.basename(args.libfile)
        sofile_output_dir = os.path.dirname(args.sofile)
        unstripped_libfile = os.path.join(sofile_output_dir, libfile_name)
        shutil.copy2(unstripped_libfile, args.libfile)

    if args.mini_debug and not args.sofile.endswith(".dll"):
        unstripped_libfile = os.path.abspath(args.sofile)
        script_path = os.path.join(
            os.path.dirname(__file__), 'mini_debug_info.py')
        ohos_root_path = os.path.join(os.path.dirname(__file__), '../..')
        result = subprocess.call(
            wrapper_utils.command_to_run(
                ['python3', script_path, '--unstripped-path', unstripped_libfile, '--stripped-path', args.output,
                '--root-path', ohos_root_path, '--clang-base-dir', args.clang_base_dir]))

    return result


if __name__ == "__main__":
    sys.exit(main())
