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

import sys
import os

_SOURCE_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..'))
# Import jinja2 from third_party/jinja2
sys.path.insert(1, os.path.join(_SOURCE_ROOT, 'third_party'))
from jinja2 import FileSystemLoader, Environment  # noqa: E402

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from scripts.util.file_utils import read_json_file, write_file  # noqa: E402,


def _get_template_content(toolchain_template_file, part_attributes,
                          product_name):
    _loader_dir_rel = os.path.relpath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.')
    _toolchain_template_dir = os.path.join(_loader_dir_rel,
                                           "toolchain_template")
    templateEnv = Environment(loader=FileSystemLoader(_toolchain_template_dir))
    template = templateEnv.get_template(toolchain_template_file)
    part_attributes_list = "\n".join(_get_part_attributes(part_attributes))
    result = template.render(part_attributes_list=part_attributes_list,
                             product_name=product_name)
    return result


def _get_part_attributes(part_attributes):
    attr_list = []
    for key, val in part_attributes.items():
        _item = ''
        if isinstance(val, bool):
            _item = f'{key} = {str(val).lower()}'
        elif isinstance(val, int):
            _item = f'{key} = {val}'
        elif isinstance(val, str):
            _item = f'{key} = "{val}"'
        else:
            raise Exception("part feature '{key}:{val}' type not support.")
        attr_list.append(_item)
    return attr_list


def get_toolchain_gn(target_os, target_cpu, part_attributes,
                     product_info_output_path, product_name):
    toolchain_template_file = f'{target_os}_{target_cpu}_clang.template'
    template_content = _get_template_content(toolchain_template_file,
                                             part_attributes, product_name)
    toolchain_build_gn = os.path.join(product_info_output_path,
                                      'toolchain/BUILD.gn')
    write_file(toolchain_build_gn, template_content)
    return toolchain_build_gn


def main(argv):
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))