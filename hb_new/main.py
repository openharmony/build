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
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.preloader import PreloaderAdapt
from services.preloader import OHOSPreloader
from services.interface.preload import Preload

from services.loader import OHOSLoader
from services.interface.load import Load

from services.gn import Gn
from services.interface.buildFileGenerator import BuildFileGenerator

from services.ninja import Ninja
from services.interface.buildExecutor import BuildExecutor

from services.menu import Menu

from resolver.interface.argsResolver import ArgsResolver
from resolver.buildArgsResolver import BuildArgsResolver
from resolver.setArgsResolver import SetArgsResolver

from modules.interface.moduleInterface import ModuleInterface
from modules.interface.buildModule import BuildModule
from modules.interface.setModule import SetModule
from modules.ohosBuildmodule import OHOSBuildModule
from modules.ohosSetModule import OHOSSetModule

from resources.config import Config

from containers.arg import Arg
from containers.arg import ModuleType

from exceptions.ohosException import OHOSException

from util.logUtil import LogUtil

class Main():

    @staticmethod
    def init_module(moduleType: ModuleType) -> ModuleInterface:
        module = None
        args_dict = Arg.parse_all_args(moduleType)
        if moduleType == ModuleType.BUILD:

            if args_dict.get("product_name").argValue != '':
                set_args_dict = Arg.parse_all_args(ModuleType.SET)
                setArgsResolever = SetArgsResolver(set_args_dict)
                menu = Menu()
                ohosSetModule = OHOSSetModule(
                    set_args_dict, setArgsResolever, menu)
                set_module = SetModule(ohosSetModule)
                set_module.run()

            config = Config()

            preloader = OHOSPreloader(config)
            preload = Preload(preloader)

            loader = OHOSLoader(config)
            load = Load(loader)

            gn = Gn(config)
            buildFileGenerator = BuildFileGenerator(gn)

            ninja = Ninja(config)
            buildExecutor = BuildExecutor(ninja)

            buildArgsResolever = BuildArgsResolver(args_dict)
            argsResolver = ArgsResolver(buildArgsResolever)

            ohosBuildModule = OHOSBuildModule(args_dict, argsResolver, preload, load,
                                              buildFileGenerator, buildExecutor)

            module = BuildModule(ohosBuildModule)
        elif moduleType == ModuleType.SET:
            setArgsResolever = SetArgsResolver(args_dict)
            menu = Menu()
            ohosSetModule = OHOSSetModule(args_dict, setArgsResolever, menu)

            module = SetModule(ohosSetModule)
        elif moduleType == ModuleType.ENV:
            pass
        elif moduleType == ModuleType.CLEAN:
            pass
        elif moduleType == ModuleType.TOOL:
            pass

        return module

    @staticmethod
    def main():
        module_type = sys.argv[1]
        if module_type == 'build':
            module = Main.init_module(ModuleType.BUILD)
        elif module_type == 'set':
            module = Main.init_module(ModuleType.SET)
        elif module_type == 'env':
            module = Main.init_module(ModuleType.ENV)
        elif module_type == 'clean':
            module = Main.init_module(ModuleType.CLEAN)
        elif module_type == 'tool':
            module = Main.init_module(ModuleType.TOOL)
        else:
            raise OHOSException(
                'There is no such option {}'.format(module_type))

        status = module.run()
        return 0


if __name__ == "__main__":
    sys.exit(Main.main())
