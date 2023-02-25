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


import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__))) # ohos/build/hb dir
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # ohos/build dir
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lite')) # ohos/build/lite dir

from containers.arg import Arg, ModuleType
from containers.status import throw_exception
from resources.global_var import ARGS_DIR
from exceptions.ohos_exception import OHOSException

from services.preloader import OHOSPreloader
from services.loader import OHOSLoader
from services.gn import Gn
from services.ninja import Ninja

is_platform_support =False
if sys.platform != "darwin":
    is_platform_support = True
    from services.menu import Menu


from resolver.build_args_resolver import BuildArgsResolver
from resolver.set_args_resolver import SetArgsResolver
from resolver.clean_args_resolver import CleanArgsResolver
from resolver.env_args_resolver import EnvArgsResolver
from resolver.tool_args_resolver import ToolArgsResolver

from modules.interface.module_interface import ModuleInterface
from modules.interface.build_module_interface import BuildModuleInterface
from modules.interface.set_module_interface import SetModuleInterface
from modules.interface.env_module_interface import EnvModuleInterface
from modules.interface.clean_module_interface import CleanModuleInterface
from modules.interface.tool_module_interface import ToolModuleInterface

from modules.ohos_build_module import OHOSBuildModule
from modules.ohos_set_module import OHOSSetModule
from modules.ohos_clean_module import OHOSCleanModule
from modules.ohos_env_module import OHOSEnvModule
from modules.ohos_tool_module import OHOSToolModule

from helper.separator import Separator
from util.log_util import LogUtil


class Main():

    def _init_build_module(self) -> BuildModuleInterface:
        args_dict = Arg.parse_all_args(ModuleType.BUILD)

        if args_dict.get("product_name").arg_value != '':
            set_args_dict = Arg.parse_all_args(ModuleType.SET)
            set_args_resolver = SetArgsResolver(set_args_dict)
            if is_platform_support:
                menu = Menu()
            else:
                menu = "Menu()"
            ohos_set_module = OHOSSetModule(set_args_dict, set_args_resolver, menu)
            ohos_set_module.set_product()

        preloader = OHOSPreloader()
        loader = OHOSLoader()
        generate_ninja = Gn()
        ninja = Ninja()
        build_args_resolver = BuildArgsResolver(args_dict)

        return OHOSBuildModule(args_dict, build_args_resolver, preloader, loader, generate_ninja, ninja)

    def _init_set_module(self) -> SetModuleInterface:
        Arg.clean_args_file()
        args_dict = Arg.parse_all_args(ModuleType.SET)
        set_args_resolver = SetArgsResolver(args_dict)
        if is_platform_support:
            menu = Menu()
        else:
            menu = "Menu()"
        return OHOSSetModule(args_dict, set_args_resolver, menu)

    def _init_env_module(self) -> EnvModuleInterface:
        args_dict = Arg.parse_all_args(ModuleType.ENV)
        env_args_resolver = EnvArgsResolver(args_dict)
        return OHOSEnvModule(args_dict, env_args_resolver)

    def _init_clean_module(self) -> CleanModuleInterface:
        args_dict = Arg.parse_all_args(ModuleType.CLEAN)
        clean_args_resolever = CleanArgsResolver(args_dict)
        return OHOSCleanModule(args_dict, clean_args_resolever)

    def _init_tool_module(self) -> ToolModuleInterface:
        Arg.clean_args_file()
        args_dict = Arg.parse_all_args(ModuleType.TOOL)
        generate_ninja = Gn()
        tool_args_resolever = ToolArgsResolver(args_dict)
        return OHOSToolModule(args_dict, tool_args_resolever, generate_ninja)

    @staticmethod
    @throw_exception
    def main():
        main = Main()
        module_type = sys.argv[1]
        if module_type == 'build':
            module = main._init_build_module()
        elif module_type == 'set':
            module = main._init_set_module()
        elif module_type == 'env':
            module = main._init_env_module()
        elif module_type == 'clean':
            module = main._init_clean_module()
        elif module_type == 'tool':
            module = main._init_tool_module()
        elif module_type == 'help':
            for all_module_type in ModuleType:
                LogUtil.hb_info(Separator.long_line)
                LogUtil.hb_info(Arg.get_help(all_module_type))
            exit()
        else:
            raise OHOSException(
                'There is no such option {}'.format(module_type), '0018')
        try:
            module.run()
        except KeyboardInterrupt:
            for file in os.listdir(ARGS_DIR):
                if file.endswith('.json') and os.path.exists(os.path.join(ARGS_DIR, file)):
                    os.remove(os.path.join(ARGS_DIR, file))
            print('User abort')
            return -1
        else:
            return 0



if __name__ == "__main__":
    sys.exit(Main.main())
