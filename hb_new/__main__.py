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
import argparse

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
from services.interface.menuInterface import MenuInterface

from resolver.interface.argsResolver import ArgsResolver
from resolver.buildArgsResolver import BuildArgsResolver
from resolver.setArgsResolver import SetArgsResolver

from modules.interface.moduleInterface import ModuleInterface
from modules.interface.buildModule import BuildModule
from modules.interface.setModule import SetModule
from modules.ohosBuildmodule import OHOSBuildModule
from modules.ohosSetModule import OHOSSetModule

from resources.config import Config
from resources.global_var import CURRENT_OHOS_ROOT

from containers.arg import Arg
from containers.arg import ModuleType

from exceptions.ohosException import OHOSException

from lite.hb_internal.set.set import exec_command as hb_set


def hb_set_adapt(root_path:str, product_name:str) -> None:
    args_dict = {}
    args_dict['root_path'] = root_path
    args_dict['product'] = product_name if '@' not in product_name else product_name.split("@")[0]
    args = argparse.Namespace(**args_dict)
    hb_set(args)

def init_module(moduleType: ModuleType) -> ModuleInterface:
    module = None
    args_dict = Arg.parse_all_args(moduleType)
    if moduleType == ModuleType.BUILD:
        # set_args_dict = Arg.parse_all_args(ModuleType.SET)
        # setArgsResolever = SetArgsResolver(set_args_dict)
        # setArgsResolever.resolveProductName(set_args_dict['product_name'])
        hb_set_adapt(CURRENT_OHOS_ROOT, args_dict['product_name'].argValue)
        config = Config()

        preloader = PreloaderAdapt(config)
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

def main_hb_new():
    module_type = sys.argv[1]
    if module_type == 'build':
        module = init_module(ModuleType.BUILD)
    elif module_type == 'set':
        module = init_module(ModuleType.SET)
    elif module_type == 'env':
        module = init_module(ModuleType.ENV)
    elif module_type == 'clean':
        module = init_module(ModuleType.CLEAN)
    elif module_type == 'tool':
        module = init_module(ModuleType.TOOL)
    else:
        raise OHOSException('There is no such option {}'.format(module_type))
    module.run()
    

if __name__ == "__main__":
    sys.exit(main_hb_new())
