#!/usr/bin/env python3
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
import argparse

import file_utils
import dependence_analysis


def gen_part_dependence(deps_data):
    part_allowlist = ['unittest', 'moduletest', 'systemtest']
    label_to_alias = {}
    for _module_alias, _info in deps_data.items():
        _module_label = _info.get('module_label').split('(')[0]
        label_to_alias[_module_label] = _module_alias

    part_deps_data = {}
    for _module_alias, _info in deps_data.items():
        deps_part_list = []
        _part_name = _info.get('part_name')
        if _part_name in part_allowlist:
            continue
        _deps_label_list = _info.get('deps')
        for _deps_label in _deps_label_list:
            _alias = label_to_alias.get(_deps_label)
            if _alias is None:
                continue
            _dep_part_name = _alias.split(':')[0]
            if _dep_part_name == _part_name:
                continue
            deps_part_list.append(_dep_part_name)
        _external_deps_list = _info.get('external_deps')
        for _ext_deps in _external_deps_list:
            _dep_part_name = _ext_deps.split(':')[0]
            if _dep_part_name == _part_name:
                continue
            deps_part_list.append(_dep_part_name)

        deps_value = part_deps_data.get(_part_name, [])
        deps_value.extend(deps_part_list)
        part_deps_data[_part_name] = list(set(deps_value))
    return part_deps_data


def _drawing_part_deps(part_deps_data, output_path):
    from graphviz import Digraph
    part_allowlist = ['unittest', 'moduletest', 'systemtest']
    dot = Digraph(comment='OpenHarmony part dependence',
                  node_attr={
                      'style': 'filled',
                      'color': 'lightblue2'
                  })
    lines = []
    tmp_lines = []
    for _part_name, _dep_parts in part_deps_data.items():
        if _part_name in part_allowlist:
            continue
        dot.node(_part_name, _part_name)
        for _dep_part in _dep_parts:
            line = {'start': _part_name, 'end': _dep_part}
            lines.append(line)
            tmp_lines.append('{}={}'.format(_part_name, _dep_part))
    for line in lines:
        start = line.get('start')
        end = line.get('end')
        reverse = '{}={}'.format(end, start)
        if reverse in tmp_lines:
            dot.edge(start, end, color='red')
        else:
            dot.edge(start, end)

    _output_graph_file = os.path.join(output_path, 'part-deps-grahp.gv')
    dot.render(_output_graph_file, view=False)


def run(deps_files_path, output_path, is_graph):
    all_deps_data = dependence_analysis.get_all_deps_data(deps_files_path)
    all_deps_data_file = os.path.join(output_path, 'all_deps_data.json')
    file_utils.write_json_file(all_deps_data_file, all_deps_data)

    part_deps_data = gen_part_dependence(all_deps_data)
    part_deps_data_file = os.path.join(output_path, 'part_deps_info.json')
    file_utils.write_json_file(part_deps_data_file, part_deps_data)
    if is_graph:
        _drawing_part_deps(part_deps_data, output_path)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--deps-files-path', required=True)
    parser.add_argument('--graph', action='store_true')
    parser.set_defaults(graph=False)
    args = parser.parse_args(argv)

    if not os.path.exists(args.deps_files_path):
        raise Exception("'{}' doesn't exist.".format(args.deps_files_path))
    output_path = os.path.join(os.path.dirname(args.deps_files_path),
                               'part_deps_info')
    print("------Generate part dependency info------")
    run(args.deps_files_path, output_path, args.graph)
    print('part deps data output to {}'.format(output_path))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
