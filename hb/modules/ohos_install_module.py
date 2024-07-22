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

from services.hpm import CMDTYPE
from modules.interface.install_module_interface import InstallModuleInterface
from resolver.interface.args_resolver_interface import ArgsResolverInterface
from exceptions.ohos_exception import OHOSException
from services.interface.build_file_generator_interface import BuildFileGeneratorInterface
from util.log_util import LogUtil
from containers.status import throw_exception


class OHOSInstallModule(InstallModuleInterface):

    _instance = None

    def __init__(self, args_dict: dict, args_resolver: ArgsResolverInterface, hpm: BuildFileGeneratorInterface):
        super().__init__(args_dict, args_resolver)
        self._hpm = hpm
        OHOSInstallModule._instance = self

    @property
    def hpm(self):
        return self._hpm
    
    @staticmethod
    def get_instance():
        if OHOSInstallModule._instance is not None:
            return OHOSInstallModule._instance
        else:
            raise OHOSException(
                'OHOSInstallModule has not been instantiated', '0000')

    @throw_exception
    def run(self):
        try:
            super().run()
        except OHOSException as exception:
            raise exception
        else:
            LogUtil.hb_info('{} build success')

    def _install(self):
        self._run_phase()
        self.hpm.execute_hpm_cmd(CMDTYPE.INSTALL)

    def _run_phase(self):
        for arg in self.args_dict.values():
            self.args_resolver.resolve_arg(arg, self)