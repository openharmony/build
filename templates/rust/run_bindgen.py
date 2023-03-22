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

import argparse
import os
import subprocess
import sys


def ohos_filter_clang_args(ohos_clangargs):
    def ohos_do_filter(args):
        cnt = 0
        while cnt < len(args):
            # Intercept plugin arguments
            if args[cnt] == '-Xclang':
                cnt += 1
                if args[cnt] == '-add-plugin':
                    pass
                elif args[cnt].startswith('-plugin-arg'):
                    cnt += 2
            else:
                yield args[cnt]
            cnt += 1
    return list(ohos_do_filter(ohos_clangargs))


def main():
    parser = argparse.ArgumentParser("run_bindgen.py")
    parser.add_argument("--exe", help="Path to bindgen", required=True)
    parser.add_argument("--llvm-config-path", help="Path to bindgen", required=True)
    parser.add_argument("--clang-path", help="Path to bindgen", required=True)
    parser.add_argument("--output", help="output .rs bindings", required=True)
    parser.add_argument("--ld-library-path", help="LD_LIBRARY_PATH to set")
    parser.add_argument("--header",
                        help="C header file to generate bindings for",
                        required=True)
    parser.add_argument("--depfile",
                        help="depfile to output with header dependencies")
    parser.add_argument("-I", "--include", help="include path", action="append")
    parser.add_argument(
        "ohos_clangargs",
        metavar="CLANGARGS",
        help="arguments to pass to libclang (see "
        "https://docs.rs/bindgen/latest/bindgen/struct.Builder.html#method.clang_args)",
        nargs="*")
    args = parser.parse_args()
    ohos_genargs = []
    ohos_genargs.append('--no-layout-tests')
    ohos_genargs.append('--size_t-is-usize')
    ohos_genargs += ['--rust-target', 'nightly']
    if args.depfile:
        ohos_genargs.append('--depfile')
        ohos_genargs.append(args.depfile)
    ohos_genargs.append('--output')
    ohos_genargs.append(args.output)
    ohos_genargs.append(args.header)
    ohos_genargs.append('--')
    ohos_genargs.extend(ohos_filter_clang_args(args.ohos_clangargs))
    env = os.environ
    if args.ld_library_path:
        env["LD_LIBRARY_PATH"] = args.ld_library_path
    env["LLVM_CONFIG_PATH"] = args.llvm_config_path
    env["CLANG_PATH"] = args.clang_path
    rescode = subprocess.run([args.exe, *ohos_genargs], env=env).returncode
    if rescode != 0:
        if os.path.exists(args.depfile):
            os.remove(args.depfile)
        if os.path.exists(args.output):
            os.remove(args.output)
    return rescode
if __name__ == '__main__':
    sys.exit(main())