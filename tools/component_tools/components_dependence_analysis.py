#!/usr/bin/python3
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

"""

import sys
import os
import argparse
import re

from graphviz import Digraph
from component_node import Node
from component_node import Module

file_paths = []
module_dict = {}
component_nodes = {}


def draw_deps_pictrue_by_gn(output_path):
    graph = Digraph('deps_graph')
    for node_name in component_nodes:
        graph.node(name=node_name, color='red')
    for node_name in component_nodes:
        deps = component_nodes[node_name]._deps
        external_deps = component_nodes[node_name]._deps
        all_deps = deps | external_deps
        for dep_name in all_deps:
            part_name = dep_name.split(':')[0]
            module_name = dep_name.split(':')[-1]
            if part_name in component_nodes:
                graph.edge(node_name, part_name)
            elif module_name in component_nodes:
                graph.edge(node_name, module_name)
    graph.render(filename=output_path+'/dep_graph')


def merge_module():
    # create component nodes
    for module_name in module_dict:
        part_name = module_dict[module_name]._part_name
        if part_name in component_nodes:
            component_nodes[part_name].add_module(module_dict[module_name])
        else:
            if part_name != '':
                component_nodes[part_name] = Node(part_name)
                component_nodes[part_name].add_module(module_dict[module_name])
            elif module_name != '':
                component_nodes[module_name] = Node(module_name)
                component_nodes[module_name].add_module(module_dict[module_name])
            else:
                pass


def read_build_gn_file(file_path):
    with open(file_path, 'r') as file:
        file_data = file.read()
        pattern = re.compile(r'ohos_shared_library.*?\}', re.DOTALL)
        results = pattern.findall(file_data)
        for ohos_module_string in results:
            module = Module.create_module_by_string(ohos_module_string)
            module_dict[module._module_name] = module


def _colletct_build_gn_path(root_path):
    for file in os.listdir(root_path):
        file_path = os.path.join(root_path, file)
        if file == 'BUILD.gn':
            file_paths.append(file_path)
        if os.path.isdir(file_path):
            _colletct_build_gn_path(file_path)    


def collect_build_gn_path(root_path):
    for file in os.listdir(root_path):
        file_path = os.path.join(root_path, file)
        if file != 'out' and os.path.isdir(file_path):
            _colletct_build_gn_path(file_path)    


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--root-path', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)

    collect_build_gn_path(args.root_path)
    for gn_file in file_paths:
        read_build_gn_file(gn_file)
    
    merge_module()
    draw_deps_pictrue_by_gn(args.output)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))