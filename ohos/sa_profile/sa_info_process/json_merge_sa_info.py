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
from json_sort_sa_by_bootphase import SARearrangement
import json_sa_info_config_errors as json_err  # noqa E402


class JsonSAInfoMerger(object):
    class SAInfoCollector(object):
        """
        Class for collecting sa info pieces shared with same process name
        """
        def __init__(self, process_name, wdir):
            self.process_name = process_name
            self.systemabilities = []
            self.wdir = wdir

        @property
        def output_filename(self):
            basename = self.process_name + '.json'
            return os.path.join(self.wdir, basename)

        def add_systemability_info(self, systemability):
            self.systemabilities += systemability

        def merge_sa_info(self):
            """
            Write all pieces of sa info shared with same process to a new file
            """
            xml_lines = {}
            xml_lines['process'] = self.process_name
            xml_lines['systemability'] = self.systemabilities
            if not os.path.exists(self.wdir):
                os.mkdir(self.wdir)
            file_node = os.open(self.output_filename, os.O_RDWR | os.O_CREAT, 0o640)
            with os.fdopen(file_node, 'w') as json_files:
                json.dump(xml_lines, json_files, indent=4, ensure_ascii=False)

    def __init__(self):
        self.process_sas_dict = {}
        self.output_filelist = []

    def __add_to_output_filelist(self, infile):
        self.output_filelist.append(os.path.join(self.output_dir, infile))

    def __parse_json_file(self, file):
        with open(file, 'r') as json_files:
            data = json.load(json_files)
            _format = 'one and only one {} tag is expected, actually {} is found'
        # check process tag
        if 'process' not in data or data['process'] == '':
            raise json_err.BadFormatJsonError('provide a valid value for process', file)
        process_name = data['process']
        if self.process_sas_dict.get(process_name) is None:
            # create a new collector if a new process tag is found
            sa_info_collector = self.SAInfoCollector(process_name, self.temp_dir)
            self.process_sas_dict[process_name] = sa_info_collector
            self.__add_to_output_filelist(process_name + '.json')
        else:
            sa_info_collector = self.process_sas_dict.get(process_name)
        # check systemability tag
        if 'systemability' not in data or data['systemability'] == '':
            raise  json_err.BadFormatJsonError('provide a valid value for systemability', file)
        sys_count = len(data['systemability'])
        if sys_count != 1:
            raise  json_err.BadFormatJsonError(_format.format('systemabiltiy', sys_count), file)
        sys_value = data['systemability']
        if 'name' not in sys_value[0] or 'libpath' not in sys_value[0]:
            raise json_err.BadFormatJsonError('systemability must have name and libpath', file)
        sa_info_collector.add_systemability_info(sys_value)

    def __merge(self, sa_info_filelist, path_merges):
        """
        merge the json files of sa_info_filelist
        :param sa_info_filelist : input_files
        :param path_merges : merges_path
        """
        self.temp_dir = path_merges
        self.output_dir = path_merges
        for file in sa_info_filelist:
            self.__parse_json_file(file)
        global_ordered_systemability_names = []
        global_systemability_deps_dict = {}
        # merge systemability info for each process
        for process, collector in self.process_sas_dict.items():
            rearragement = SARearrangement()
            collector.merge_sa_info()
            merged_file = collector.output_filename
            rearragement.sort(merged_file, merged_file)
            # get deps info for later detecting globally circular
            deps_info = rearragement.get_deps_info()
            global_ordered_systemability_names += deps_info[0]
            global_systemability_deps_dict.update(deps_info[1])
        # detect possible cross-process circular dependency
        try:
            SARearrangement.detect_invalid_dependency_globally(
                global_ordered_systemability_names,
                global_systemability_deps_dict)
        except json_err.CircularDependencyError as error:
            for _file in self.output_filelist:
                try:
                    os.remove(_file)
                except OSError:
                    pass
            raise json_err.CrossProcessCircularDependencyError(error)
        # finally return an output filelist
        return self.output_filelist

    def merge(self, sa_info_filelist, output_dir):
        return self.__merge(sa_info_filelist, output_dir)
