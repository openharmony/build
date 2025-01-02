#!/usr/bin/env python3
# coding: utf-8
#
# Copyright (c) 2023-2024 Huawei Device Co., Ltd.
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
import subprocess
import argparse
import sys


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--src-idl', required=True, help='idl source file')
    parser.add_argument('--dst-path', required=True, help='the converted target path')
    parser.add_argument('--dst-file', required=True, help='the converted target file')
    parser.add_argument('--idl-tool-path', required=True, help='path of the idl conversion tool')
    parser.add_argument('--log-domainid', help='hilog domain id')
    parser.add_argument('--log-tag', help='hilog tag')
    parser.add_argument('--hitrace', help='hitrace switch, default off')
    parser.add_argument('--language', help='language switch, default cpp')
    arguments = parser.parse_args()
    return arguments


def run_command(cmd, execution_path):
    print("cmd:", " ".join(cmd))
    print("execution_path:", execution_path)
    proc = subprocess.Popen(cmd, cwd=execution_path, stdout=subprocess.PIPE)
    proc.wait()
    return proc.returncode


def idl_gen_interface(input_arguments):
    if not os.path.exists(input_arguments.dst_path):
        try:
            os.makedirs(input_arguments.dst_path, 0o750, exist_ok=True)
        except (OSError, TypeError) as excep:
            raise excep
        finally:
            pass

    print("idl_gen_interface run os.remove start")
    dst_file_list = input_arguments.dst_file.split(',')
    for dst_file in dst_file_list:
        if os.path.exists(dst_file):
            os.remove(dst_file)
            print("idl_gen_interface run os.remove", dst_file)

    gen_language = "-gen-cpp"
    if input_arguments.language == "rust":
        gen_language = "-gen-rust"
    elif input_arguments.language == "ts":
        gen_language = "-gen-ts"

    src_idl_list = input_arguments.src_idl.split(",")
    for src_idl in src_idl_list:
        cmd = [os.path.join(".", "idl"), gen_language, "-d", input_arguments.dst_path, "-c", src_idl]
        if input_arguments.log_domainid:
            cmd += ['-log-domainid', input_arguments.log_domainid]
        if input_arguments.log_tag:
            cmd += ['-log-tag', input_arguments.log_tag]
        if input_arguments.hitrace:
            cmd += ['-t', input_arguments.hitrace]
        ret = run_command(cmd, input_arguments.idl_tool_path)
        if ret != 0:
            return ret
    return 0


if __name__ == '__main__':
    sys.exit(idl_gen_interface(parse_args()))
