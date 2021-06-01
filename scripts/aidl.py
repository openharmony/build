#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 Huawei Device Co., Ltd.
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
import re
import sys
import zipfile
import shutil

from util import build_utils


def main(argv):
    argv = build_utils.expand_file_args(argv)

    option_parser = optparse.OptionParser()
    build_utils.add_depfile_option(option_parser)

    option_parser.add_option('--aidl-path', help='Path to the'
                                                 ' aidl binary.')
    option_parser.add_option('--libcxx-path', help='path to libc++.so')
    option_parser.add_option('--imports', help='Files to import.')
    option_parser.add_option(
        '--includes', help='Directories to add as import search paths.')
    option_parser.add_option(
        '--generated-cpp-files', action='append', help='generated cpp'
                                                       ' files.')
    option_parser.add_option(
        '--src-archive',
        help='archive path to generated source, spruce files.')
    option_parser.add_option(
        '--gen-cpp',
        action='store_true',
        help='Whether to generate cpp code or java code.')
    options, args = option_parser.parse_args(argv[1:])

    aidl_cmd = [options.aidl_path]
    if options.gen_cpp:
        if options.imports:
            for s in build_utils.parse_gn_list(options.imports):
                aidl_cmd.extend(['-p', s])
        if options.includes:
            for s in build_utils.parse_gn_list(options.includes):
                aidl_cmd.extend(['-I', s])
    else:
        if options.imports:
            aidl_cmd += [
                '-p' + s for s in build_utils.parse_gn_list(options.imports)
            ]
        if options.includes:
            aidl_cmd += [
                '-I' + s for s in build_utils.parse_gn_list(options.includes)
            ]

    outputs = [options.src_archive]
    if options.gen_cpp:
        outputs += [os.path.dirname(options.src_archive)]
    build_utils.call_and_write_depfile_if_stale(
        lambda: on_stale_md5(options, args, aidl_cmd),
        options,
        depfile_deps=([options.aidl_path] + args),
        input_paths=(args + [options.aidl_path]),
        output_paths=(outputs),
        input_strings=aidl_cmd,
        force=False,
        add_pydeps=False)


def on_stale_md5(options, aidl_files, aidl_cmd):
    ld_library = os.path.dirname(options.libcxx_path)
    if 'LD_LIBRARY_PATH' in os.environ:
        ld_library = '{}:{}'.format(
            ld_library,
            os.environ.get('LD_LIBRARY_PATH').strip(':'))
    my_env = {"LD_LIBRARY_PATH": ld_library}

    with build_utils.temp_dir() as temp_dir:
        for f in aidl_files:
            cmd = []
            cmd.extend(aidl_cmd)
            classname = os.path.splitext(os.path.basename(f))[0]
            if options.gen_cpp:
                output = os.path.join(temp_dir, '{}.cpp'.format(classname))
                cmd.extend([f, os.path.dirname(output), output])
            else:
                output = os.path.join(temp_dir, '{}.java'.format(classname))
                cmd += [f, output]
            build_utils.check_output(cmd, env=my_env)

        if options.gen_cpp:
            output_dir = os.path.dirname(options.src_archive)
            os.makedirs(output_dir, exist_ok=True)
            if os.path.exists(options.src_archive):
                os.remove(options.src_archive)

            build_utils.zip_dir(options.src_archive, temp_dir)
            build_utils.extract_all(options.src_archive,
                                   output_dir,
                                   no_clobber=False)
        else:
            with build_utils.atomic_output(options.src_archive) as f:
                with zipfile.ZipFile(f, 'w') as srcjar:
                    for path in build_utils.find_in_directory(temp_dir, '*.java'):
                        with open(path) as fileobj:
                            data = fileobj.read()
                        pkg_name = re.search(r'^\s*package\s+(.*?)\s*;', data,
                                             re.M).group(1)
                        arcname = '%s/%s' % (pkg_name.replace(
                            '.', '/'), os.path.basename(path))
                        build_utils.add_to_zip_hermetic(srcjar, arcname, data=data)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
