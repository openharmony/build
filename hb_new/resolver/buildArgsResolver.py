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

from distutils.spawn import find_executable
from distutils.util import strtobool


from containers.arg import Arg
from containers.statusCode import StatusCode
from exceptions.ohosException import OHOSException
from modules.interface.buildModuleInterface import BuildModuleInterface
from resources.config import Config
from resolver.interface.argsResolverInterface import ArgsResolverInterface
from util.typeCheckUtil import TypeCheckUtil
from util.logUtil import LogUtil
from util.systemUtil import SystemUtil




class BuildArgsResolver(ArgsResolverInterface):

    def __init__(self, json):
        super().__init__(json)

    def resolveVerbose(self, targetArg: Arg, **kwargs) -> StatusCode:
        return StatusCode()
        
    def resolveStrictMode(self, targetArg: Arg, **kwargs) -> StatusCode:
        buildModule = kwargs.get("buildModule")
        if strtobool(Arg.argValue) and isinstance(buildModule, BuildModuleInterface) :
            preloader = buildModule.preloader.unwrapped_preloader
            loader = buildModule.loader.unwrapped_loader
            if not (preloader.outputs.check_outputs() and loader.outputs.check_outputs()):
                return StatusCode(status=False, info='')
        return StatusCode()
            
    def resolveRenameLastLog(self, targetArg, **kwargs) -> StatusCode:
        TypeCheckUtil.checkArgType(kwargs.get('config'), Config)
        config = kwargs.get("config")

        out_path = config.out_path
        logfile = os.path.join(out_path, 'build.log')
        if os.path.exists(logfile):
            mtime = os.stat(logfile).st_mtime
            os.rename(logfile, '{}/build.{}.log'.format(out_path, mtime))
            
        return StatusCode()

    def resolveCCache(self, targetArg: Arg, **kwargs) -> StatusCode:
        if targetArg.argValue:
            TypeCheckUtil.checkArgType(kwargs.get('config'), Config)
            config = kwargs.get("config")

            ccache_path = find_executable('ccache')
            if ccache_path is None:
                LogUtil.hb_warning('Failed to find ccache, ccache disabled.')
                return StatusCode()

            ccache_local_dir = os.environ.get('CCACHE_LOCAL_DIR')
            ccache_base = os.environ.get('CCACHE_BASE')
            if not ccache_local_dir:
                ccache_local_dir = '.ccache'
            if ccache_base is None:
                ccache_base = os.path.join(config.root_path, ccache_local_dir)
                if not os.path.exists(ccache_base):
                    os.makedirs(ccache_base)

            logfile = os.path.join(config.root_path, 'ccache.log')
            if os.path.exists(logfile):
                oldfile = os.path.join(config.root_path, 'ccache.log.old')
                if os.path.exists(oldfile):
                    os.unlink(oldfile)
                os.rename(logfile, oldfile)

            os.environ['CCACHE_EXEC'] = ccache_path
            os.environ['CCACHE_LOGFILE'] = logfile
            os.environ['USE_CCACHE'] = '1'
            os.environ['CCACHE_DIR'] = ccache_base
            os.environ['CCACHE_MASK'] = '002'
            ccache_max_size = os.environ.get('CCACHE_MAXSIZE')
            if not ccache_max_size:
                ccache_max_size = '100G'

            cmd = ['ccache', '-M', ccache_max_size]
            
            SystemUtil.exec_command(cmd, log_path=config.log_path)
        return StatusCode()

    def resolvePycache(self, targetArg: Arg, **kwargs) -> StatusCode:
        return StatusCode()
    
    def resolveTargetCpu(self, targetArg: Arg, **kwargs) -> StatusCode:
        config = kwargs.get("config")
        if isinstance(config, Config):
            config.target_cpu = targetArg.argValue
        return StatusCode()
    
    def resolveBuildType(self, targetArg: Arg, **kwargs) -> StatusCode:
        return StatusCode()
    
    def resolveFullCompilation(self, targetArg: Arg, **kwargs) -> StatusCode:
        return StatusCode()
    
    def resolveBuildTarget(self, targetArg: Arg, **kwargs) -> StatusCode:
        return StatusCode()
    
    def resolveGnArgs(self, targetArg: Arg, **kwargs) -> StatusCode:
        return StatusCode()
    
    def resolveKeepNinjaGoing(self, targetArg: Arg, **kwargs) -> StatusCode:
        return StatusCode()
    
    def resolveBuildOnlyGn(self, targetArg: Arg, **kwargs) -> StatusCode:
        return StatusCode()
    
    def resolveDisablePackageImage(self, targetArg: Arg, **kwargs) -> StatusCode:
        return StatusCode()
    
    def resolveDisablePartofPostBuild(self, targetArg: Arg, **kwargs) -> StatusCode:
        return StatusCode()
    
    def resolveProduct(self, targetArg: Arg, **kwargs) -> StatusCode:
        
        return StatusCode()
    
    def resolveBuildVariant(self, targetArg: Arg, **kwargs) -> StatusCode:
        return StatusCode()
    
    def resolveDeviceType(self, targetArg: Arg, **kwargs) -> StatusCode:
        return StatusCode()
    
    def _mapArgsToFunction(self, json: dict):
        for entity in json['args']:
            argsName = str(entity['argName']).replace("-", "_")[2:]
            functionName = entity['resolveFuntion']
            if not hasattr(self, functionName) or \
                    not hasattr(self.__getattribute__(functionName), '__call__'):
                raise OHOSException(
                    f'There is no resolution for arg: ' + argsName)
            self._argsToFunction[argsName] = self.__getattribute__(
                functionName)
