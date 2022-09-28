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
import json
import argparse



sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.preloader import PreloaderAdapt
from services.preloader import OHOSPreloader
from services.interface.preload import Preload

from services.loader import LoaderAdapt
from services.loader import OHOSLoader
from services.interface.load import Load

from services.gn import GnAdapter
from services.gn import Gn
from services.interface.buildFileGenerator import BuildFileGenerator

from services.ninja import NinjaAdapter
from services.ninja import Ninja
from services.interface.buildExecutor import BuildExecutor

from resolver.interface.argsResolver import ArgsResolver
from resolver.buildArgsResolver import BuildArgsResolver
from resolver.argsFactory import ArgsFactory

from modules.interface.buildModule import BuildModule
from modules.ohosBuildmodule import OHOSBuildModule

from resources.config import Config

from containers.arg import Arg
from util.logUtil import LogUtil

from lite.hb_internal.set.set import exec_command as hb_set
VERSION = "0.4.6"

CURRENT_OHOS_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def add_options(parser: argparse.ArgumentParser):
    args_file_path = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'resources/args/buildargs.json')
    args_dict = {}
    with open(args_file_path) as args_file:
        all_args = json.load(args_file)
        for arg in all_args['args']:
            arg = dict(arg)
            ArgsFactory.genenic_add_option(parser, arg)

            oh_arg = Arg.createInstanceByDict(arg)
            if oh_arg.argAttribute.get('deprecated', None):
                LogUtil.hb_warning('{} will be deprecated, please consider use other options'.format(oh_arg.argName))
            args_dict[oh_arg.argName] = oh_arg
    args = parser.parse_args(sys.argv[2:])
    
    for oh_arg in args_dict.values():
        assigned_value = args.__dict__[oh_arg.argName]
        if oh_arg.argType == 'list':
            assigned_value = sum(assigned_value, [])
        elif oh_arg.argType == 'bool':
            assigned_value = bool(assigned_value)
        oh_arg.argValue = assigned_value
    return args_dict

def hb_set_adapt(root_path:str, product_name:str) -> None:
    args_dict = {}
    args_dict['root_path'] = root_path
    args_dict['product'] = product_name if '@' not in product_name else product_name.split("@")[0]
    args = argparse.Namespace(**args_dict)
    hb_set(args)

def main_hb_new():
    parser = argparse.ArgumentParser()
    args_dict = add_options(parser)
    
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

    ohosBuildModule = OHOSBuildModule(args_dict, argsResolver, preload, load, buildFileGenerator, buildExecutor)
    builder = BuildModule(ohosBuildModule)
    builder.run()
    

if __name__ == "__main__":
    sys.exit(main_hb_new())
