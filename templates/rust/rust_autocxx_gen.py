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

sys.path.append(
    os.path.join(os.path.dirname(__file__),os.pardir,os.pardir)
)
from scripts.util import build_utils


def ohos_filter_clang_args(clangargs):
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
    return list(ohos_do_filter(clangargs))


def ohos_atomic_copy(in_path, out_path):
    with open(in_path, 'rb') as input:
        with build_utils.atomic_output(out_path, only_if_changed=True) as output:
            content = input.read()
            output.write(content)

def copy_to_prefixed_filename(path, filename, prefix):
    ohos_atomic_copy(os.path.join(path, filename),
                os.path.join(path, prefix + "_" + filename))

def main():
    parser = argparse.ArgumentParser("run_autocxx_gen.py")
    parser.add_argument("--exe", help="Path to autocxx_gen executable", required=True),
    parser.add_argument("--clang-path", help="Path to clang executable", required=True)
    parser.add_argument("--source",
                        help="rust files containing autocxx or cxx macros",
                        required=True)
    parser.add_argument("--outdir", help="output dir to set", required=True)
    parser.add_argument(
        "--header", help="output header filename to set", required=True)
    parser.add_argument("--llvm-config-path",
                    help="Path to llvm-config executable", required=True)
    parser.add_argument("--ld-library-path", help="LD_LIBRARY_PATH to set")
    parser.add_argument("--cxx-h-path", help="path to cxx.h")
    parser.add_argument(
        "--output-prefix",
        help="prefix for output filenames (cc only, not h/rs). We do this for the purpose : "
        "to ensure every .o file has his unique name, as is required by ninja.")
    parser.add_argument("--cxx-impl-annotations",
                        help="annotation for exported symbols to set")
    parser.add_argument("-I", "--include",
                        help="include path to set", action="append")
    parser.add_argument(
        "clangargs",
        metavar="CLANGARGS",
        help="arguments to pass to libclang",
        nargs="*")
    args = parser.parse_args()
    autocxx_gen_args = []
    autocxx_gen_args.append(args.source)
    autocxx_gen_args.append('--gen-rs-include')
    autocxx_gen_args.append('--gen-cpp')
    autocxx_gen_args.append('--outdir')
    autocxx_gen_args.append(args.outdir)
    autocxx_gen_args.append('--generate-exact')
    autocxx_gen_args.append('2')
    autocxx_gen_args.append('--fix-rs-include-name')
    if args.cxx_impl_annotations:
        autocxx_gen_args.append('--cxx-impl-annotations')
        autocxx_gen_args.append(args.cxx_impl_annotations)
    if args.cxx_h_path:
        autocxx_gen_args.append('--cxx-h-path')
        autocxx_gen_args.append(args.cxx_h_path)
    autocxx_gen_args.append('--')
    autocxx_gen_args.append('-I../..')
    autocxx_gen_args.extend(ohos_filter_clang_args(args.clangargs))
    env = os.environ
    if args.ld_library_path:
        env["LD_LIBRARY_PATH"] = args.ld_library_path
    env["LLVM_CONFIG_PATH"] = args.llvm_config_path
    env["CLANG_PATH"] = args.clang_path
    subprocess.run([args.exe, *autocxx_gen_args], check=True, env=env)
    if args.output_prefix:
        copy_to_prefixed_filename(args.outdir, "gen1.cc", args.output_prefix)
        copy_to_prefixed_filename(args.outdir, "gen0.cc", args.output_prefix)
    ohos_atomic_copy(os.path.join(args.outdir, "gen0.h"), args.header)
    ohos_rs_include_path = os.path.join(args.outdir, "gen0.include.rs")
    if not os.path.exists(ohos_rs_include_path):
        # Make a blank file
        with build_utils.atomic_output(ohos_rs_include_path, only_if_changed=True) as output:
            pass


if __name__ == '__main__':
    sys.exit(main())
