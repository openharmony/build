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
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lite'))

from services.preloader import OHOSPreloader
from services.interface.preload import Preload

from services.loader import OHOSLoader
from services.interface.load import Load

from services.gn import Gn
from services.interface.buildFileGenerator import BuildFileGenerator

from services.ninja import Ninja
from services.interface.buildExecutor import BuildExecutor

from resolver.interface.argsResolver import ArgsResolver
from resolver.buildArgsResolver import BuildArgsResolver

from modules.interface.buildModule import BuildModule
from modules.ohosBuildmodule import OHOSBuildModule

from resources.config import Config

from containers.arg import Arg

from lite.hb_internal.set.set import exec_command as hb_set
VERSION = "1.0.0"

CURRENT_OHOS_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def hb_set_adapt(root_path:str, product_name:str) -> None:
    args_dict = {}
    args_dict['root_path'] = root_path
    args_dict['product'] = product_name if '@' not in product_name else product_name.split("@")[0]
    args = argparse.Namespace(**args_dict)
    hb_set(args)

def main_hb_new():
    args_dict = Arg.parse_all_args()
    
    hb_set_adapt(CURRENT_OHOS_ROOT, args_dict['product_name'].argValue)

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

    ohosBuildModule = OHOSBuildModule(args_dict, argsResolver, preload, load, buildFileGenerator, buildExecutor)
    builder = BuildModule(ohosBuildModule)
    builder.run()
    

if __name__ == "__main__":
    sys.exit(main_hb_new())
