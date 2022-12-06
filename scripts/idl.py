#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import optparse
import os
import sys

from util import build_utils


def parse_args(args):
    args = build_utils.expand_file_args(args)

    parser = optparse.OptionParser()
    build_utils.add_depfile_option(parser)

    parser.add_option('--idl-path', help='path to idl')
    parser.add_option('--libcxx-path', help='path to libc++.so')
    parser.add_option('--output-archive-path', help='path to output archive')
    parser.add_option(
        '--genenrated-cpp-files',
        action='append',
        help='generated cpp files'
    )
    parser.add_option(
        '--generated-src-directory',
        help='directory that stores generated source code'
    )
    parser.add_option(
        '--gen-type', help='generate type code'
    )
    options, paths = parser.parse_args(args)
    return options, paths


def idl_compile(options, paths, cmd):
    my_env = None
    ld_library = os.path.dirname(options.libcxx_path)
    if 'LD_LIBRARY_PATH' in os.environ:
        ld_library = '{}.{}'.format(
            ld_library,
            os.environ.get('LD_LIBRARY_PATH').strip(':')
        )
    my_env = {'LD_LIBRARY_PATH': ld_library}

    with build_utils.temp_dir() as tmp_dir:
        for f in paths:
            cmd.extend(['-c', f, '-d', tmp_dir])
            build_utils.check_output(cmd, env=my_env)
        build_utils.zip_dir(options.output_archive_path, tmp_dir)
        os.makedirs(options.generated_src_directory, exist_ok=True)
        build_utils.extract_all(options.output_archive_path,
                                options.generated_src_directory)


def main(args):
    args = build_utils.expand_file_args(args)
    options, paths = parse_args(args)
    cmd = [options.idl_path]
    if options.gen_type == "cpp":
        cmd.extend(['-gen-cpp'])
    elif options.gen_type == "ts":
        cmd.extend(['-gen-ts'])

    outputs = [options.output_archive_path]

    build_utils.call_and_write_depfile_if_stale(
        lambda: idl_compile(options, paths, cmd),
        options,
        depfile_deps=([options.idl_path]),
        input_paths=(paths + [options.idl_path]),
        output_paths=(outputs),
        input_strings=cmd,
        force=False,
        add_pydeps=False
    )

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
