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


from modules.interface.build_module_interface import BuildModuleInterface
from resolver.interface.args_resolver_interface import ArgsResolverInterface
from services.interface.preload_interface import PreloadInterface
from services.interface.load_interface import LoadInterface
from services.interface.build_file_generator_interface import BuildFileGeneratorInterface
from services.interface.build_executor_interface import BuildExecutorInterface
from containers.arg import BuildPhase
from exceptions.ohos_exception import OHOSException
from util.system_util import SystemUtil
from util.log_util import LogUtil
from containers.status import throw_exception


class OHOSBuildModule(BuildModuleInterface):

    _instance = None

    def __init__(self,
                 args_dict: dict,
                 args_resolver: ArgsResolverInterface,
                 preloader: PreloadInterface,
                 loader: LoadInterface,
                 target_generator: BuildFileGeneratorInterface,
                 target_compiler: BuildExecutorInterface):

        super().__init__(args_dict, args_resolver, preloader,
                         loader, target_generator, target_compiler)
        OHOSBuildModule._instance = self
        self._start_time = SystemUtil.get_current_time()

    @property
    def build_time(self):
        return SystemUtil.get_current_time() - self._start_time

    @staticmethod
    def get_instance():
        if OHOSBuildModule._instance is not None:
            return OHOSBuildModule._instance
        else:
            raise OHOSException(
                'OHOSBuildModule has not been instantiated', '0000')

    @throw_exception
    def run(self):
        try:
            super().run()
        except OHOSException as exception:
            raise exception
        else:
            LogUtil.hb_info('{} build success'.format(
                self.args_dict.get('product_name').arg_value))
            LogUtil.hb_info('Cost time:  {}'.format(self.build_time))

    def _prebuild(self):
        self._run_phase(BuildPhase.PRE_BUILD)

    def _preload(self):
        self._run_phase(BuildPhase.PRE_LOAD)
        if self.args_dict.get('fast_rebuild', None) and not self.args_dict.get('fast_rebuild').arg_value:
            self.preloader.run()

    def _load(self):
        self._run_phase(BuildPhase.LOAD)
        if self.args_dict.get('fast_rebuild', None) and not self.args_dict.get('fast_rebuild').arg_value:
            self.loader.run()

    def _pre_target_generate(self):
        self._run_phase(BuildPhase.PRE_TARGET_GENERATE)

    def _target_generate(self):
        self._run_phase(BuildPhase.TARGET_GENERATE)
        if self.args_dict.get('fast_rebuild', None) and not self.args_dict.get("fast_rebuild").arg_value:
            self.target_generator.run()

    def _post_target_generate(self):
        self._run_phase(BuildPhase.POST_TARGET_GENERATE)

    def _pre_target_compilation(self):
        self._run_phase(BuildPhase.PRE_TARGET_COMPILATION)

    def _target_compilation(self):
        self._run_phase(BuildPhase.TARGET_COMPILATION)
        if self.args_dict.get('build_only_gn', None) and not self.args_dict.get("build_only_gn").arg_value:
            self.target_compiler.run()

    def _post_target_compilation(self):
        self._run_phase(BuildPhase.POST_TARGET_COMPILATION)

    def _post_build(self):
        self._run_phase(BuildPhase.POST_BUILD)

    def _run_phase(self, phase: BuildPhase):
        '''Description: Traverse all registered parameters in build process and 
            execute the resolver function of the corresponding phase
        @parameter: [phase]:  Build phase corresponding to parameter
        @return :none
        '''
        for phase_arg in [arg for arg in self.args_dict.values()if arg.arg_phase == phase]:
            self.args_resolver.resolve_arg(phase_arg, self)
