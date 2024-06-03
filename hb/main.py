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
import subprocess
import json
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))  # ohos/build/hb dir
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # ohos/build dir
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lite'))  # ohos/build/lite dir

from containers.arg import Arg, ModuleType
from containers.status import throw_exception
from resources.global_var import ARGS_DIR
from resources.global_var import CURRENT_OHOS_ROOT
from exceptions.ohos_exception import OHOSException

from services.preloader import OHOSPreloader
from services.loader import OHOSLoader
from services.gn import Gn
from services.ninja import Ninja
from services.hpm import Hpm
from services.hdc import Hdc

from resolver.build_args_resolver import BuildArgsResolver
from resolver.set_args_resolver import SetArgsResolver
from resolver.clean_args_resolver import CleanArgsResolver
from resolver.env_args_resolver import EnvArgsResolver
from resolver.tool_args_resolver import ToolArgsResolver
from resolver.indep_build_args_resolver import IndepBuildArgsResolver
from resolver.install_args_resolver import InstallArgsResolver
from resolver.package_args_resolver import PackageArgsResolver
from resolver.publish_args_resolver import PublishArgsResolver
from resolver.update_args_resolver import UpdateArgsResolver
from resolver.push_args_resolver import PushArgsResolver

from modules.interface.module_interface import ModuleInterface
from modules.interface.build_module_interface import BuildModuleInterface
from modules.interface.set_module_interface import SetModuleInterface
from modules.interface.env_module_interface import EnvModuleInterface
from modules.interface.clean_module_interface import CleanModuleInterface
from modules.interface.tool_module_interface import ToolModuleInterface
from modules.interface.indep_build_module_interface import IndepBuildModuleInterface
from modules.interface.install_module_interface import InstallModuleInterface
from modules.interface.package_module_interface import PackageModuleInterface
from modules.interface.publish_module_interface import PublishModuleInterface
from modules.interface.update_module_interface import UpdateModuleInterface
from modules.interface.push_module_interface import PushModuleInterface

from modules.ohos_build_module import OHOSBuildModule
from modules.ohos_set_module import OHOSSetModule
from modules.ohos_clean_module import OHOSCleanModule
from modules.ohos_env_module import OHOSEnvModule
from modules.ohos_tool_module import OHOSToolModule
from modules.ohos_indep_build_module import OHOSIndepBuildModule
from modules.ohos_install_module import OHOSInstallModule
from modules.ohos_package_module import OHOSPackageModule
from modules.ohos_publish_module import OHOSPublishModule
from modules.ohos_update_module import OHOSUpdateModule
from modules.ohos_push_module import OHOSPushModule

from helper.separator import Separator
from util.log_util import LogUtil
from util.system_util import SystemUtil


class Main():

    def _set_path(self):
        user_home = os.path.expanduser("~")
        prebuilts_cache_path = os.path.join(user_home, '.prebuilts_cache', 'hpm', 'node_modules', '.bin')
        nodejs_bin_path = os.path.join(CURRENT_OHOS_ROOT, 'prebuilts', 'build-tools', 'common', 'nodejs', 'current',
                                       'bin')
        os.environ['PATH'] = prebuilts_cache_path + os.pathsep + nodejs_bin_path + os.pathsep + os.environ['PATH']

    def _init_build_module(self) -> BuildModuleInterface:
        args_dict = Arg.parse_all_args(ModuleType.BUILD)

        if args_dict.get("product_name").arg_value != '':
            set_args_dict = Arg.parse_all_args(ModuleType.SET)
            set_args_resolver = SetArgsResolver(set_args_dict)
            ohos_set_module = OHOSSetModule(set_args_dict, set_args_resolver, "")
            ohos_set_module.set_product()

        preloader = OHOSPreloader()
        loader = OHOSLoader()
        generate_ninja = Gn()
        ninja = Ninja()
        build_args_resolver = BuildArgsResolver(args_dict)

        return OHOSBuildModule(args_dict, build_args_resolver, preloader, loader, generate_ninja, ninja)

    def _init_hb_init_module(self):
        subprocess.run(['bash', os.path.join(CURRENT_OHOS_ROOT, 'build', 'prebuilts_config.sh')])
        sys.exit()

    def _init_set_module(self) -> SetModuleInterface:
        Arg.clean_args_file()
        args_dict = Arg.parse_all_args(ModuleType.SET)
        set_args_resolver = SetArgsResolver(args_dict)
        from services.menu import Menu
        menu = Menu()
        return OHOSSetModule(args_dict, set_args_resolver, menu)

    def _init_env_module(self) -> EnvModuleInterface:
        if len(sys.argv) > 2 and sys.argv[2] in ['--sshkey', '-s']:
            self._set_path()
            subprocess.run(['hpm', 'config', 'set', 'loginUser', str(sys.argv[3])])
            subprocess.run(['hpm', 'gen-keys'])
            key_path = os.path.join(os.path.expanduser("~"), '.hpm', 'key', 'publicKey_' + sys.argv[3] + '.pem')
            print(f'Please add the content of {key_path} to https://repo.harmonyos.com/#/cn/profile/sshkeys')
            sys.exit()
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

    def _init_indep_build_module(self) -> IndepBuildModuleInterface:
        self._set_path()
        Arg.clean_args_file_by_type(ModuleType.INDEP_BUILD)
        args_dict = Arg.parse_all_args(ModuleType.INDEP_BUILD)
        hpm = Hpm()
        indep_build_args_resolver = IndepBuildArgsResolver(args_dict)
        return OHOSIndepBuildModule(args_dict, indep_build_args_resolver, hpm)

    def _is_indep_build(self) -> bool:
        if "--indep-build" in sys.argv[2:] or "-i" in sys.argv[2:]:
            return True
        env_args_dict = Arg.read_args_file(ModuleType.ENV)
        return env_args_dict.get("indep_build").get("argDefault")

    def _init_install_module(self) -> InstallModuleInterface:
        self._set_path()
        Arg.clean_args_file_by_type(ModuleType.INSTALL)
        args_dict = Arg.parse_all_args(ModuleType.INSTALL)
        hpm = Hpm()
        install_args_resolver = InstallArgsResolver(args_dict)
        return OHOSInstallModule(args_dict, install_args_resolver, hpm)

    def _init_package_module(self) -> PackageModuleInterface:
        self._set_path()
        Arg.clean_args_file_by_type(ModuleType.PACKAGE)
        args_dict = Arg.parse_all_args(ModuleType.PACKAGE)
        hpm = Hpm()
        package_args_resolver = PackageArgsResolver(args_dict)
        return OHOSPackageModule(args_dict, package_args_resolver, hpm)

    def _init_publish_module(self) -> PublishModuleInterface:
        self._set_path()
        args_dict = Arg.parse_all_args(ModuleType.PUBLISH)
        hpm = Hpm()
        publish_args_resolver = PublishArgsResolver(args_dict)
        return OHOSPublishModule(args_dict, publish_args_resolver, hpm)

    def _init_update_module(self) -> UpdateModuleInterface:
        self._set_path()
        Arg.clean_args_file_by_type(ModuleType.UPDATE)
        args_dict = Arg.parse_all_args(ModuleType.UPDATE)
        hpm = Hpm()
        update_args_resolver = UpdateArgsResolver(args_dict)
        return OHOSUpdateModule(args_dict, update_args_resolver, hpm)

    def _init_push_module(self) -> PushModuleInterface:
        args_dict = Arg.parse_all_args(ModuleType.PUSH)
        hdc = Hdc()
        update_args_resolver = PushArgsResolver(args_dict)
        return OHOSPushModule(args_dict, update_args_resolver, hdc)

    def _push_module(self):
        if sys.argv[2] in ['-h', '-help', 'h', 'help']:
            print('Please use the command "hb push" like this: hb push component_name -t device_num')
            sys.exit()
        check_hdc = subprocess.run(['hdc', '-v'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if check_hdc.returncode != 0:
            print("Error: Please make sure 'hdc' is installed and properly configured.")
            sys.exit()
        check_device = subprocess.run(['hdc', 'list', 'targets'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      text=True)
        if check_device.stdout.strip() == "[Empty]":
            print("Error: Device is not connected.")
            sys.exit()
        if len(check_device.stdout.strip().split('\n')) == 1:
            device = check_device.stdout.strip()
        else:
            device = sys.argv[4]
            if device not in check_device.stdout:
                print("Error: Wrong device number")
                sys.exit()
        subprocess.run(["hdc", "-t", str(device), "shell", "mount", "-o", "rw,remount", "/"], check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        default = os.path.join(CURRENT_OHOS_ROOT, "out", "default")
        with open(os.path.join(default, "build_configs", "component_mapping.json"), 'r') as r:
            single_component_path = json.load(r).get("single_component_path")
        part_path = next(iter(single_component_path.values()))
        with open(os.path.join(CURRENT_OHOS_ROOT, part_path, "bundle.json"), 'r') as r:
            bundle = json.load(r)
        push_list = bundle.get("deployment")
        if push_list:
            if not isinstance(push_list, list):
                print("Error: Deployment value format error, should be in list format!")
            for one_push in push_list:
                if one_push.get("src") and not os.path.exists(os.path.join(CURRENT_OHOS_ROOT, one_push.get("src"))):
                    print("Error: The path in src does not exist, please modify the src path!")
                if one_push.get("src") and one_push.get("target"):
                    subprocess.run(
                        ["hdc", "-t", str(device), "file", "send", os.path.join(CURRENT_OHOS_ROOT, one_push.get("src")),
                         one_push.get("target")], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("hb push success!")
        sys.exit()

    @staticmethod
    @throw_exception
    def main():
        main = Main()
        module_initializers = {
            'build': main._init_indep_build_module if main._is_indep_build() else main._init_build_module,
            'init': main._init_hb_init_module,
            'indep_build': main._init_indep_build_module,
            'set': main._init_set_module,
            'env': main._init_env_module,
            'clean': main._init_clean_module,
            'tool': main._init_tool_module,
            'install': main._init_install_module,
            'package': main._init_package_module,
            'publish': main._init_publish_module,
            'update': main._init_update_module,
            'push': main._push_module
        }

        module_type = sys.argv[1]
        if module_type == 'help':
            for all_module_type in ModuleType:
                LogUtil.hb_info(Separator.long_line)
                LogUtil.hb_info(Arg.get_help(all_module_type))
            exit()

        if module_type not in module_initializers:
            raise OHOSException(f'There is no such option {module_type}', '0018')

        start_time = SystemUtil.get_current_time()
        module = module_initializers[module_type]()
        try:
            module.run()
            if module_type == 'build':
                LogUtil.hb_info('Cost Time:  {}'.format(SystemUtil.get_current_time() - start_time))
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
