#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (c) 2020 Huawei Device Co., Ltd.
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


from containers.output import Output


class PrealoaderOutputs():

    def __init__(self, output_dir: str):
        self._build_prop = Output(output_dir, 'build.prop', check_build_prop)
        self._build_config_json = Output(output_dir, 'build_config.json', check_build_config)
        self._parts_json = Output(output_dir, 'parts.json', check_parts)
        self._parts_config_json = Output(output_dir, 'parts_config.json', check_parts_config)
        self._build_gnargs_prop = Output(output_dir, 'build_gnargs.prop', check_build_gnargs)
        self._features_json = Output(output_dir, 'features.json', check_features)
        self._syscap_json = Output(output_dir, 'syscap.json', check_syscap)
        self._exclusion_modules_json = Output(output_dir,
                                                   'exclusion_modules.json', check_exclusion_modules)
        self._subsystem_config_json = Output(output_dir,
                                                  'subsystem_config.json', check_subsystem_config)
        self._platforms_build = Output(output_dir, 'platforms.build', check_platforms_build)
        self._systemcapability_json = Output(output_dir, 'SystemCapability.json', check_system_capability)


    def check_outputs(self) -> bool: 
        for name, value in vars(self).items():
            if not value.check_output():
                return False
        return True


def check_build_prop(output:Output) -> bool:
    return True


def check_build_config(output:Output) -> bool:
    return True


def check_parts(output:Output) -> bool:
    return True


def check_parts_config(output:Output) -> bool:
    return True


def check_build_gnargs(output:Output) -> bool:
    return True


def check_features(output:Output) -> bool:
    return True


def check_syscap(output:Output) -> bool:
    return True


def check_exclusion_modules(output:Output) -> bool:
    return True


def check_subsystem_config(output:Output) -> bool:
    return True


def check_platforms_build(output:Output) -> bool:
    return True


def check_system_capability(output:Output) -> bool:
    return True
