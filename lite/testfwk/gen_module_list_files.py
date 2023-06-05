#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
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
#

import argparse
import stat
import os
import sys
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import makedirs


def get_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('--depfile', help='Path to depfile (refer to `gn help depfile`)')
    parser.add_argument('--output_dir', help='output directory')
    parser.add_argument('--source_dir', help='source directory')
    parser.add_argument('--target', help='name of target')
    parser.add_argument('--target_label')
    parser.add_argument('--test_type')
    parser.add_argument('--module_list_file', help='file name of module list')
    parser.add_argument('--sources_file_search_root_dir', 
                        help='root dir to search xx.sources files')
    parser.add_argument('--sources', 
                        help='case sources path defined in test template')
    options = parser.parse_args(args)
    return options


def main(args):
    options = get_args(args)
    print("test module_list_file = {}".\
        format(os.path.dirname(options.module_list_file)))
    if not os.path.exists(os.path.dirname(options.module_list_file)):
        makedirs(os.path.dirname(options.module_list_file))

    with os.fdopen(os.open(options.module_list_file, 
                           os.O_RDWR | os.O_CREAT, stat.S_IWUSR | stat.S_IRUSR), 
                   'w', encoding='utf-8') as module_list_file:
        contents = json.dumps([{
            'target': options.target,
            'label': options.target_label,
            'source_directory': options.source_dir,
            'output_directory': options.output_dir,
            'test_type': options.test_type
        }])
        module_list_file.write(contents)

    # create xx.sources file
    fold = os.path.join(options.sources_file_search_root_dir, \
        options.source_dir[(options.source_dir.rfind("../") + len("../")):])
    if not os.path.exists(fold):
        makedirs(fold)
    sources_file_name = fold[fold.rfind("/") + len("/"):] + ".sources"

    arg_sources = options.sources[0: (len(options.sources) - len(","))]
    
    with os.fdopen(os.open(os.path.join(fold, sources_file_name), 
                           os.O_RDWR | os.O_CREAT, stat.S_IWUSR | stat.S_IRUSR), 
                   'a', encoding='utf-8') as source_defined_file:
        list_sources = arg_sources.split(",")
        for source in list_sources:
            content = "{}/{}\n".format(
                os.path.dirname(options.source_dir), source)
            source_defined_file.write(content)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
