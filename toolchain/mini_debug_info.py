#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
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
#

import sys
import argparse
import os
import platform
import subprocess
import stat
import re


def gen_symbols(tmp_file, sort_lines, symbols_path):
    modes = stat.S_IWUSR | stat.S_IRUSR | stat.S_IWGRP | stat.S_IRGRP
    with os.fdopen(os.open(tmp_file, os.O_RDWR | os.O_CREAT, modes), 'w', encoding='utf-8') as output_file:
        for item in sort_lines:
            output_file.write('{}\n'.format(item))

    with os.fdopen(os.open(symbols_path, os.O_RDWR | os.O_CREAT, modes), 'w', encoding='utf-8') as output_file:
        cmd = 'sort {}'.format(tmp_file)
        subprocess.run(cmd.split(), stdout=output_file)


def remove_adlt_postfix(llvm_objcopy_path, keep_path, mini_debug_path):
    modes = stat.S_IWUSR | stat.S_IRUSR | stat.S_IWGRP | stat.S_IRGRP
    pattern = re.compile(r'(__[0-9A-F])$')
    symbols_to_rename = []

    with os.fdopen(os.open(keep_path, os.O_RDWR | os.O_CREAT, modes), 'r', encoding='utf-8') as output_file:
        for line in output_file:
            line = line.strip()
            if pattern.search(line):
                symbols_to_rename.append(line)

    if symbols_to_rename:
        rename_rules_path = keep_path + ".rename"
        with os.fdopen(os.open(rename_rules_path, os.O_RDWR | os.O_CREAT, modes), 'w', encoding='utf-8') as output_file:
            for symbol in symbols_to_rename:
                new_name = pattern.sub('', symbol)
                if new_name != symbol:
                    output_file.write('{} {}\n'.format(symbol, new_name))

        rename_cmd = llvm_objcopy_path + " --redefine-syms=" + rename_rules_path + " " + mini_debug_path
        return rename_cmd, rename_rules_path


def create_mini_debug_info(binary_path, stripped_binary_path, root_path, clang_base_dir, adlt_llvm_tool):
    # temporary file path
    dynsyms_path = stripped_binary_path + ".dynsyms"
    funcsysms_path = stripped_binary_path + ".funcsyms"
    keep_path = stripped_binary_path + ".keep"
    debug_path = stripped_binary_path + ".debug"
    mini_debug_path = stripped_binary_path + ".minidebug"

    # llvm tools path
    host_platform = platform.uname().system.lower()
    host_cpu = platform.uname().machine.lower()
    llvm_dir_path = os.path.join(
        clang_base_dir, host_platform + '-' + host_cpu, 'llvm/bin')
    if not os.path.exists(llvm_dir_path):
        llvm_dir_path = os.path.join(root_path, 'out/llvm-install/bin')
    if adlt_llvm_tool:
        llvm_dir_path = adlt_llvm_tool
    llvm_nm_path = os.path.join(llvm_dir_path, "llvm-nm")
    llvm_objcopy_path = os.path.join(llvm_dir_path, "llvm-objcopy")

    cmd_list = []
    file_list = []

    gen_symbols_cmd = llvm_nm_path + " -D " + binary_path + " --format=posix --defined-only"
    gen_func_symbols_cmd = llvm_nm_path + " " + binary_path + " --format=posix --defined-only"
    gen_keep_symbols_cmd = "comm -13 " + dynsyms_path + " " + funcsysms_path
    gen_keep_debug_cmd = llvm_objcopy_path + \
        " --only-keep-debug " + binary_path + " " + debug_path
    gen_mini_debug_cmd = llvm_objcopy_path + " -S --remove-section .gdb_index --remove-section .comment --keep-symbols=" + \
        keep_path + " " + debug_path + " " + mini_debug_path
    compress_debuginfo = "xz " + mini_debug_path
    gen_stripped_binary = llvm_objcopy_path + " --add-section .gnu_debugdata=" + \
        mini_debug_path + ".xz " + stripped_binary_path


    tmp_file1 = '{}.tmp1'.format(dynsyms_path)
    tmp_file2 = '{}.tmp2'.format(dynsyms_path)
    modes = stat.S_IWUSR | stat.S_IRUSR | stat.S_IWGRP | stat.S_IRGRP
    with os.fdopen(os.open(tmp_file1, os.O_RDWR | os.O_CREAT, modes), 'w', encoding='utf-8') as output_file:
        subprocess.run(gen_symbols_cmd.split(), stdout=output_file)

    with os.fdopen(os.open(tmp_file1, os.O_RDWR | os.O_CREAT, modes), 'r', encoding='utf-8') as output_file:
        lines = output_file.readlines()
        sort_lines = []
        for line in lines:
            columns = line.strip().split()
            if columns:
                sort_lines.append(columns[0])

    gen_symbols(tmp_file2, sort_lines, dynsyms_path)
    os.remove(tmp_file1)
    os.remove(tmp_file2)


    tmp_file1 = '{}.tmp1'.format(funcsysms_path)
    tmp_file2 = '{}.tmp2'.format(funcsysms_path)
    with os.fdopen(os.open(tmp_file1, os.O_RDWR | os.O_CREAT, modes), 'w', encoding='utf-8') as output_file:
        subprocess.run(gen_func_symbols_cmd.split(), stdout=output_file)

    with os.fdopen(os.open(tmp_file1, os.O_RDWR | os.O_CREAT, modes), 'r', encoding='utf-8') as output_file:
        lines = output_file.readlines()
        sort_lines = []
        for line in lines:
            columns = line.strip().split()
            if len(columns) > 2 and ('t' in columns[1] or 'T' in columns[1] or 'd' in columns[1]):
                sort_lines.append(columns[0])

    gen_symbols(tmp_file2, sort_lines, funcsysms_path)
    os.remove(tmp_file1)
    os.remove(tmp_file2)


    with os.fdopen(os.open(keep_path, os.O_RDWR | os.O_CREAT, modes), 'w', encoding='utf-8') as output_file:
        subprocess.run(gen_keep_symbols_cmd.split(), stdout=output_file)


    cmd_list.append(gen_keep_debug_cmd)
    cmd_list.append(gen_mini_debug_cmd)
    if adlt_llvm_tool:
        rename_cmd, rename_rules_path = remove_adlt_postfix(llvm_objcopy_path, keep_path, mini_debug_path)
        cmd_list.append(rename_cmd)
        file_list.append(rename_rules_path)
    cmd_list.append(compress_debuginfo)
    cmd_list.append(gen_stripped_binary)

    # execute each cmd to generate temporary file
    # which .gnu_debugdata section depends on
    for cmd in cmd_list:
        subprocess.call(cmd.split(), shell=False)

    # remove temporary file
    file_list.append(dynsyms_path)
    file_list.append(funcsysms_path)
    file_list.append(keep_path)
    file_list.append(debug_path)
    file_list.append(mini_debug_path + ".xz")
    for file in file_list:
        os.remove(file)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unstripped-path",
                        help="unstripped binary path")
    parser.add_argument("--stripped-path",
                        help="stripped binary path")
    parser.add_argument("--root-path",
                        help="root path is used to search llvm toolchain")
    parser.add_argument("--clang-base-dir", help="")
    parser.add_argument("--adlt-llvm-tool", help="")
    args = parser.parse_args()

    create_mini_debug_info(args.unstripped_path,
                           args.stripped_path, args.root_path, args.clang_base_dir, args.adlt_llvm_tool)


if __name__ == "__main__":
    sys.exit(main())
