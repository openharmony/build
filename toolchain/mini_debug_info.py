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


def create_mini_debug_info(binary_path, stripped_binary_path, root_path):
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
        root_path, 'prebuilts/clang/ohos', host_platform + '-' + host_cpu, 'llvm/bin')
    llvm_nm_path = os.path.join(llvm_dir_path, "llvm-nm")
    llvm_objcopy_path = os.path.join(llvm_dir_path, "llvm-objcopy")

    cmd_list = []

    gen_symbols_cmd = llvm_nm_path + " -D " + binary_path + \
        " --format=posix --defined-only | awk \'{ print $1}\' | sort > " + dynsyms_path
    gen_func_symbols_cmd = llvm_nm_path + " " + binary_path + \
        " --format=posix --defined-only | awk \'{ if ($2 == \"t\" || $2== \"T\" || $2 == \"d\" ) print $1}\' | sort > " + funcsysms_path
    gen_keep_symbols_cmd = "comm -13 " + dynsyms_path + \
        " " + funcsysms_path + " > " + keep_path
    gen_keep_debug_cmd = llvm_objcopy_path + \
        " --only-keep-debug " + binary_path + " " + debug_path
    gen_mini_debug_cmd = llvm_objcopy_path + " -S --remove-section .gbd_index --remove-section .comment --keep-symbols=" + \
        keep_path + " " + debug_path + " " + mini_debug_path
    compress_debuginfo = "xz " + mini_debug_path
    gen_stripped_binary = llvm_objcopy_path + " --add-section .gnu_debugdata=" + \
        mini_debug_path + ".xz " + stripped_binary_path

    cmd_list.append(gen_symbols_cmd)
    cmd_list.append(gen_func_symbols_cmd)
    cmd_list.append(gen_keep_symbols_cmd)
    cmd_list.append(gen_keep_debug_cmd)
    cmd_list.append(gen_mini_debug_cmd)
    cmd_list.append(compress_debuginfo)
    cmd_list.append(gen_stripped_binary)

    # execute each cmd to generate temporary file
    # which .gnu_debugdata section depends on
    for cmd in cmd_list:
        os.system(cmd)

    # remove temporary file
    os.remove(dynsyms_path)
    os.remove(funcsysms_path)
    os.remove(keep_path)
    os.remove(debug_path)
    os.remove(mini_debug_path + ".xz")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unstripped-path",
                        help="unstripped binary path")
    parser.add_argument("--stripped-path",
                        help="stripped binary path")
    parser.add_argument("--root-path",
                        help="root path is used to search llvm toolchain")
    args = parser.parse_args()

    create_mini_debug_info(args.unstripped_path,
                           args.stripped_path, args.root_path)


if __name__ == "__main__":
    sys.exit(main())
