#!/usr/bin/env python3
# coding: utf-8

"""
Copyright (c) 2021 Huawei Device Co., Ltd.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Description: Generate javascript byte code using es2abc
"""

import os
import subprocess
import platform
import argparse


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--src-js',
                        help='js source file')
    parser.add_argument('--dst-file',
                        help='the converted target file')
    parser.add_argument('--frontend-tool-path',
                        help='path of the frontend conversion tool')
    parser.add_argument('--extension',
                        help='source file extension')
    parser.add_argument("--debug", action='store_true',
                        help='whether add debuginfo')
    parser.add_argument("--module", action='store_true',
                        help='whether is module')
    parser.add_argument("--commonjs", action='store_true',
                        help='whether is commonjs')
    parser.add_argument("--merge-abc", action='store_true',
                        help='whether is merge abc')
    parser.add_argument("--generate-patch", action='store_true',
                        help='generate patch abc')
    parser.add_argument("--dump-symbol-table",
                        help='dump symbol table of base abc')
    parser.add_argument("--input-symbol-table",
                        help='input symbol table for patch abc')
    parser.add_argument("--target-api-sub-version",
                        help='input symbol table for patch abc')
    parser.add_argument("--module-record-field-name",
                        help='specify the field name of module record in unmerged abc. This argument is optional, ' +
                             'its value will be the path of input file if not specified')
    parser.add_argument("--source-file",
                        help='specify the file path info recorded in generated abc. This argument is optional, ' +
                             'its value will be the path of input file if not specified')
    parser.add_argument("--enable-annotations", action='store_true',
                        help='whether annotations are enabled or not')
    arguments = parser.parse_args()
    return arguments


def run_command(cmd, execution_path):
    print(" ".join(cmd) + " | execution_path: " + execution_path)
    proc = subprocess.Popen(cmd, cwd=execution_path)
    proc.wait()
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd)


def gen_abc_info(input_arguments):
    frontend_tool_path = input_arguments.frontend_tool_path

    (path, name) = os.path.split(frontend_tool_path)

    cmd = [os.path.join("./", name, "es2abc"),
           '--output', input_arguments.dst_file,
           input_arguments.src_js]

    if input_arguments.extension:
        cmd += ['--extension', input_arguments.extension]
    if input_arguments.dump_symbol_table:
        cmd += ['--dump-symbol-table', input_arguments.dump_symbol_table]
    if input_arguments.input_symbol_table:
        cmd += ['--input-symbol-table', input_arguments.input_symbol_table]
    if input_arguments.debug:
        src_index = cmd.index(input_arguments.src_js)
        cmd.insert(src_index, '--debug-info')
    if input_arguments.module:
        src_index = cmd.index(input_arguments.src_js)
        cmd.insert(src_index, '--module')
    if input_arguments.commonjs:
        src_index = cmd.index(input_arguments.src_js)
        cmd.insert(src_index, '--commonjs')
    if input_arguments.merge_abc:
        src_index = cmd.index(input_arguments.src_js)
        cmd.insert(src_index, '--merge-abc')
    if input_arguments.generate_patch:
        src_index = cmd.index(input_arguments.src_js)
        cmd.insert(src_index, '--generate-patch')
    if input_arguments.module_record_field_name:
        cmd += ["--module-record-field-name", input_arguments.module_record_field_name]
    if input_arguments.source_file:
        cmd += ["--source-file", input_arguments.source_file]
    if input_arguments.enable_annotations:
        src_index = cmd.index(input_arguments.src_js)
        cmd.insert(src_index, '--enable-annotations')
        # insert d.ts option to cmd later
    cmd.append("--target-api-sub-version=beta3")

    try:
        run_command(cmd, path)
    except subprocess.CalledProcessError as e:
        exit(e.returncode)


if __name__ == '__main__':
    gen_abc_info(parse_args())
