#!/usr/bin/env python3
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
#


import os
from re import M
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__))) # ohos/build/hb_new dir
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # ohos/build dir
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lite')) # ohos/build/lite dir

from containers.arg import Arg, ModuleType
from containers.status import throw_exception

from exceptions.ohosException import OHOSException

from services.preloader import OHOSPreloader
from services.loader import OHOSLoader
from services.gn import Gn
from services.ninja import Ninja
from services.menu import Menu


from resolver.buildArgsResolver import BuildArgsResolver
from resolver.setArgsResolver import SetArgsResolver
from resolver.cleanArgsResolver import CleanArgsResolver
from resolver.envArgsResolver import EnvArgsResolver

from modules.interface.moduleInterface import ModuleInterface
from modules.interface.buildModuleInterface import BuildModuleInterface
from modules.interface.setModuleInterface import SetModuleInterface
from modules.interface.envModuleInterface import EnvModuleInterface
from modules.interface.cleanModuleInterface import CleanModuleInterface

from modules.ohosBuildmodule import OHOSBuildModule
from modules.ohosSetModule import OHOSSetModule
from modules.ohosCleanModule import OHOSCleanModule
from modules.ohosEnvModule import OHOSEnvModule

from helper.separator import Separator
from util.logUtil import LogUtil


class Main():

    def _init_build_module(self) -> BuildModuleInterface:
        args_dict = Arg.parse_all_args(ModuleType.BUILD)

        if args_dict.get("product_name").argValue != '':
            set_args_dict = Arg.parse_all_args(ModuleType.SET)
            setArgsResolever = SetArgsResolver(set_args_dict)
            menu = Menu()
            ohosSetModule = OHOSSetModule(set_args_dict, setArgsResolever, menu)
            ohosSetModule.set_product()

        preloader = OHOSPreloader()
        loader = OHOSLoader()
        gn = Gn()
        ninja = Ninja()
        buildArgsResolever = BuildArgsResolver(args_dict)

        return OHOSBuildModule(args_dict, buildArgsResolever, preloader, loader, gn, ninja)

    def _init_set_module(self) -> SetModuleInterface:
        Arg.clean_args_file()
        args_dict = Arg.parse_all_args(ModuleType.SET)
        setArgsResolever = SetArgsResolver(args_dict)
        menu = Menu()
        return OHOSSetModule(args_dict, setArgsResolever, menu)

    def _init_env_module(self) -> EnvModuleInterface:
        args_dict = Arg.parse_all_args(ModuleType.ENV)
        envArgsResolver = EnvArgsResolver(args_dict)
        return OHOSEnvModule(args_dict, envArgsResolver)

    def _init_clean_module(self) -> CleanModuleInterface:
        args_dict = Arg.parse_all_args(ModuleType.CLEAN)
        cleanArgsResolever = CleanArgsResolver(args_dict)
        return OHOSCleanModule(args_dict, cleanArgsResolever)

    def init_module(self, moduleType: ModuleType) -> ModuleInterface:
        module = None
        if moduleType == ModuleType.BUILD:
            module = self._init_build_module()
        elif moduleType == ModuleType.SET:
            module = self._init_set_module()
        elif moduleType == ModuleType.ENV:
            module = self._init_env_module()
        elif moduleType == ModuleType.CLEAN:
            module = self._init_clean_module()
        elif moduleType == ModuleType.TOOL:
            pass
        elif moduleType == ModuleType.HELP:
            for type in ModuleType:
                LogUtil.hb_info(Separator.long_line)
                LogUtil.hb_info(Arg.get_help(type))
        return module

    @staticmethod
    @throw_exception
    def main():
        main = Main()
        module_type = sys.argv[1]
        if module_type == 'build':
            module = main.init_module(ModuleType.BUILD)
        elif module_type == 'set':
            module = main.init_module(ModuleType.SET)
        elif module_type == 'env':
            module = main.init_module(ModuleType.ENV)
        elif module_type == 'clean':
            module = main.init_module(ModuleType.CLEAN)
        elif module_type == 'tool':
            module = main.init_module(ModuleType.TOOL)
        elif module_type == 'help':
            module = main.init_module(ModuleType.HELP)
        else:
            raise OHOSException(
                'There is no such option {}'.format(module_type), '0018')

        module.run()

        return 0



if __name__ == "__main__":
    sys.exit(Main.main())
