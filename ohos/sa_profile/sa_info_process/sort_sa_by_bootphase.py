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

import os
import json
import copy
import sa_info_config_errors as json_err


class RearrangementPolicy(object):
    BOOT_START_PHASE = "BootStartPhase"
    CORE_START_PHASE = "CoreStartPhase"
    DEFAULT_START_PHASE = "OthersStartPhase"

    rearrange_category_order = (BOOT_START_PHASE, CORE_START_PHASE,
                                DEFAULT_START_PHASE)

    bootphase_priority_table = {
        BOOT_START_PHASE: 3,
        CORE_START_PHASE: 2,
        DEFAULT_START_PHASE: 1
    }

    def __init__(self):
        self.bootphase_categories = {
            RearrangementPolicy.BOOT_START_PHASE: [],
            RearrangementPolicy.CORE_START_PHASE: [],
            RearrangementPolicy.DEFAULT_START_PHASE: []
        }


class SARearrangement(object):
    def __init__(self):
        self.rearranged_systemabilities = []
        self.ordered_systemability_names = []
        self.name_node_dict = {}
        self.systemability_deps_dict = {}
        self.bootphase_dict = {}
        self.creation_dict = {}
        self.policy = RearrangementPolicy()
        self.sanode_start_idx = 0
        self.systemability_nodes = []
        self.sa_nodes_count = 0

    def __parse_json_file(self, source_file):
        with open(source_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        self.systemability_nodes = data['systemability']
        try:
            first_sa_node = self.systemability_nodes[0]
            self.sa_nodes_count = len(self.systemability_nodes)
        except IndexError:
            pass

    def __rearrange_systemability_node_strict(self, source_file, dest_file):
        rearranged_name = self.rearranged_systemabilities
        final_systemability = []
        for name in rearranged_name:
            temp = self.name_node_dict.get(name)
            final_systemability.append(temp)
        with open(source_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        data['systemability'] = final_systemability
        file_node = os.open(dest_file, os.O_RDWR | os.O_CREAT, 0o640)
        with os.fdopen(file_node, 'w') as json_files:
            json.dump(data, json_files, indent=4, ensure_ascii=False)

    @classmethod
    def __detect_invalid_dependency(self, dependency_checkers, ordered_sa_names,
                                    sa_deps_dict):
        """
        Iterate over the dependency tree, to detect whether there
        exists circular dependency and other kinds bad dependency
        """
        deps_visit_cnt = {}
        ordered_systemability_names = ordered_sa_names
        systemability_deps_dict = sa_deps_dict

        def init_dependencies_visit_counter():
            for name in ordered_systemability_names:
                deps_visit_cnt[name] = 0

        def do_check(systemability, dependency):
            """
            Check other kind dependency problem
            """
            for checker in dependency_checkers:
                checker(systemability, dependency)

        def check_depend(cur_systemability, deps_count, dependencies, depend_path):
            if deps_visit_cnt.get(cur_systemability) < deps_count:
                index = deps_visit_cnt.get(cur_systemability)
                cur_dependency = dependencies[index]
                # execute other kind dependency checkers right here
                do_check(cur_systemability, cur_dependency)
                try:
                    depend_path.index(cur_dependency)
                    depend_path.append(cur_dependency)
                    _format = "A circular dependency found: {}"
                    route = "->".join(map(str, depend_path))
                    raise json_err.CircularDependencyError(_format.format(route))
                except ValueError:
                    depend_path.append(cur_dependency)
                    deps_visit_cnt[cur_systemability] += 1
            else:
                # pop the systemability in process if it's all
                # dependencies have been visited
                depend_path.pop()

        init_dependencies_visit_counter()
        for systemability in ordered_systemability_names:
            depend_path = []
            depend_path.append(systemability)
            while len(depend_path) != 0:
                cur_systemability = depend_path[-1]
                # the cur_systemability may be in a different process,
                # thus can't find it's dependency info
                dependencies = systemability_deps_dict.get(cur_systemability)
                if dependencies is None:
                    dependencies = []
                deps_count = len(dependencies)
                if deps_count == 0:
                    depend_path.pop()
                else:
                    check_depend(cur_systemability, deps_count, dependencies, depend_path)

    def __extract_info_from_systemability_nodes(self):
        """
        Extract info like dependencies and bootphase from a systemability node
        """
        def validate_creation(creation):
            _format = ("In tag {} only a boolean value is expected, " +
                       "but actually is '{}'")
            if str(creation) not in {"true", "false", "True", "False"}:
                raise json_err.BadFormatJsonError(_format.format("run-on-create", creation),
                                        self.file_in_process)

        def validate_bootphase(bootphase, nodename):
            _format = ("In systemability: {}, The bootphase '{}' is not supported " +
                "please check yourself")
            if self.policy.bootphase_categories.get(bootphase) is None:
                raise json_err.NotSupportedBootphaseError(_format.format(nodename, bootphase))

        def validate_systemability_name(nodename):
            if nodename < 1 or nodename > 16777215:
                _format = ("name's value should be [1-16777215], but actually is {}")
                raise json_err.BadFormatJsonError(_format.format(nodename),
                                        self.file_in_process)

        def check_nodes_constraints_one(systemability_node, tag):
            _format = ("The tag {} should exist, but it does not exist")
            if tag not in systemability_node:
                raise json_err.BadFormatJsonError(_format.format(tag), self.file_in_process)
            tags_nodes = systemability_node[tag]
            return tags_nodes

        def check_nodes_constraints_two(systemability_node, tag):
            if tag not in systemability_node or systemability_node[tag] == '':
                return ""
            tags_nodes = systemability_node[tag]
            return tags_nodes

        default_bootphase = RearrangementPolicy.DEFAULT_START_PHASE
        for systemability_node in self.systemability_nodes:
            # Required <name> one and only one is expected
            name_node = check_nodes_constraints_one(systemability_node, "name")
            validate_systemability_name(name_node)
            try:
                self.ordered_systemability_names.index(name_node)
                raise json_err.SystemAbilityNameConflictError(name_node)
            except ValueError:
                self.ordered_systemability_names.append(name_node)
            self.name_node_dict[name_node] = systemability_node
            self.systemability_deps_dict[name_node] = []
            self.bootphase_dict[name_node] = default_bootphase
            # Optional bootphase: zero or one are both accepted
            bootphase_nodes = check_nodes_constraints_two(systemability_node,
                                "bootphase")
            if bootphase_nodes != '':
                validate_bootphase(bootphase_nodes, name_node)
                self.bootphase_dict[name_node] = bootphase_nodes
            # Required run-on-create one and only one is expected
            runoncreate_node = check_nodes_constraints_one(systemability_node,
                                "run-on-create")
            validate_creation(runoncreate_node)
            self.creation_dict[name_node] = runoncreate_node
            # Optional depend:
            depend_nodes = check_nodes_constraints_two(systemability_node,
                             "depend")
            for depend_node in depend_nodes:
                deps = self.systemability_deps_dict.get(name_node)
                deps.append(depend_node)

    def __sort_systemability_by_bootphase_priority(self):
        def check_index(systemabilities, dependency, idx_self):
            try:
                idx_dep = systemabilities.index(dependency)
                # if the dependency is behind, then exchange the order
                if idx_self < idx_dep:
                    tmp = systemabilities[idx_dep]
                    systemabilities[idx_dep] = systemabilities[idx_self]
                    systemabilities[idx_self] = tmp
            except ValueError:
                pass  # ignore different category of dependencies

        def inner_category_sort(systemabilities):
            """
            Sort dependencies with same bootphase category, preserve the
            original order in source file
            """
            systemabilities_ = systemabilities[:]
            for systemability in systemabilities_:
                dependencies = self.systemability_deps_dict.get(systemability)
                for dependency in dependencies:
                    # should update idx_self each iteration
                    idx_self = systemabilities.index(systemability)
                    check_index(systemabilities, dependency, idx_self)

        # put the systemability nodes into different categories
        for systemability_name in self.ordered_systemability_names:
            bootphase = self.bootphase_dict.get(systemability_name)
            salist = self.policy.bootphase_categories.get(bootphase)
            salist.append(systemability_name)

        # sort the systemability nodes according to RearrangementPolicy
        for category in RearrangementPolicy.rearrange_category_order:
            salist = self.policy.bootphase_categories.get(category)
            inner_category_sort(salist)
            self.rearranged_systemabilities += salist

    def __detect_invert_dependency(self, systemability, depend):
        """
        Detect invert dependency: systemability with high boot priority depends
        on systemability with low ones, e.g. a systemability named 'sa1' with
        BootStartPhase priority depends on a systemability named 'sa2' with
        CoreStartPhase
        """
        _format = ("Bad dependency found: the {} with high priority " +
                   "depends on a {} with low one")
        self_idx = self.bootphase_dict.get(systemability)
        # The depend may be in other process
        dep_idx = self.bootphase_dict.get(depend)
        if dep_idx is None:
            return
        self_priority = RearrangementPolicy.bootphase_priority_table.get(
            self_idx)
        depend_priority = RearrangementPolicy.bootphase_priority_table.get(
            dep_idx)
        if self_priority > depend_priority:
            raise json_err.InvertDependencyError(
                _format.format(systemability, depend))

    def __detect_creation_dependency(self, systemability, depend):
        """
        Detect dependency related to configuration on <run-on-create>:
        if a sa with <run-on-create> set to 'true' depending on a sa
        with 'false', then a RunOnCreateDependencyError will be thrown
        """
        _format = ("Bad dependency found: the {} with run-on-create " +
                   "depends on a {} with run-on-demand")
        self_creation = self.creation_dict.get(systemability)
        dep_creation = self.creation_dict.get(depend)
        if self_creation is True and dep_creation is False:
            raise json_err.RunOnCreateDependencyError(_format.format(systemability, depend))

    def sort(self, source_file, dest_file):
        self.file_in_process = source_file
        dependency_checkers = []
        dependency_checkers.append(self.__detect_invert_dependency)
        dependency_checkers.append(self.__detect_creation_dependency)

        self.__parse_json_file(source_file)
        self.__extract_info_from_systemability_nodes()
        self.__detect_invalid_dependency(dependency_checkers,
                                         self.ordered_systemability_names,
                                         self.systemability_deps_dict)
        self.__sort_systemability_by_bootphase_priority()
        self.__rearrange_systemability_node_strict(source_file, dest_file)

    @classmethod
    def detect_invalid_dependency_globally(clazz,
                                           global_ordered_systemability_names,
                                           global_systemability_deps_dict):
        dependency_checkers = []
        clazz.__detect_invalid_dependency(dependency_checkers,
                                        global_ordered_systemability_names,
                                        global_systemability_deps_dict)

    def get_deps_info(self):
        """
        Returns systemabilities and their dependencies for later detecting
        possible globally circular dependency problem
        """
        return [self.ordered_systemability_names, self.systemability_deps_dict]
