#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) 2023 Huawei Device Co., Ltd.
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

from services.hdc import CMDTYPE
from modules.interface.push_module_interface import PushModuleInterface
from resolver.interface.args_resolver_interface import ArgsResolverInterface
from exceptions.ohos_exception import OHOSException
from services.interface.build_file_generator_interface import BuildFileGeneratorInterface
from util.log_util import LogUtil
from containers.status import throw_exception


class OHOSPushModule(PushModuleInterface):

    _instance = None

    def __init__(self, args_dict: dict, args_resolver: ArgsResolverInterface, hdc: BuildFileGeneratorInterface):
        super().__init__(args_dict, args_resolver)
        self._hdc = hdc
        OHOSPushModule._instance = self

    @property
    def hdc(self):
        return self._hdc

    @staticmethod
    def get_instance():
        if OHOSPushModule._instance is not None:
            return OHOSPushModule._instance
        else:
            raise OHOSException(
                'OHOSPushModule has not been instantiated', '0000')
        

    @throw_exception
    def run(self):
        try:
            super().run()
        except OHOSException as exception:
            raise exception
    
    def _push(self):
        self._run_phase()

    def _run_phase(self):
        if self.args_dict['list_targets'].arg_value:
            self.args_resolver.resolve_arg(self.args_dict["list_targets"], self)
        else:
            for arg in self.args_dict.values():
                self.args_resolver.resolve_arg(arg, self)
            self.hdc.execute_hdc_cmd(CMDTYPE.PUSH)