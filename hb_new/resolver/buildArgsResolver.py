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
from containers.status import throw_exception

from containers.arg import Arg
from exceptions.ohosException import OHOSException
from modules.interface.buildModuleInterface import BuildModuleInterface
from resources.config import Config
from resources.global_var import CURRENT_OHOS_ROOT
from resolver.interface.argsResolverInterface import ArgsResolverInterface
from util.typeCheckUtil import TypeCheckUtil
from util.logUtil import LogUtil
from util.systemUtil import SystemUtil
from util.typeCheckUtil import TypeCheckUtil
from util.componentUtil import ComponentUtil

class BuildArgsResolver(ArgsResolverInterface):

    def __init__(self, args_dict: dict):
        super().__init__(args_dict)

    def resolveProduct(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        if targetArg.argValue == 'ohos-sdk':
            targetGenerator = buildModule.targetGenerator.unwrapped_build_file_generator
            targetGenerator.regist_arg('build_ohos_sdk', True)
            if len(buildModule.args_dict['build_target'].argValue) == 0:
                buildModule.args_dict['build_target'].argValue = [
                    'build_ohos_sdk']
            buildModule.args_dict['target_cpu'].argValue = 'arm64'
        

    def resolveTargetCpu(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        config.target_cpu = targetArg.argValue
        
    @throw_exception
    def resolveBuildTarget(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        build_executor = buildModule.targetCompiler.unwrapped_build_executor
        target_list = []
        if len(targetArg.argValue):
            target_list = targetArg.argValue
        else:
            if os.getcwd() == CURRENT_OHOS_ROOT:
                target_list = [
                    'images'] if config.os_level == 'standard' else ['packages']
            elif ComponentUtil.is_in_component_dir(os.getcwd()) and \
                    ComponentUtil.is_component_in_product(ComponentUtil.get_component_name(os.getcwd()), Config().product):
                '''TODO:Using full path name compile component to resolve some target has same name with component
                '''
                component_name = ComponentUtil.get_component_name(os.getcwd())
                LogUtil.write_log(Config().log_path, 'In the component "{}" directory,'
                                  'this compilation will compile only this component'.format(component_name),
                                  'warning')
                target_list.append(component_name)
                target_list.append(component_name + '_test')
            else:
                component_name = ComponentUtil.get_component_name(os.getcwd())
                component_name = os.path.basename(os.getcwd()) if component_name == '' else component_name
                raise OHOSException('There is no target component "{}" for the current product {}'
                                  .format(component_name, Config().product), "4001")
        build_executor.regist_arg('build_target', target_list)
        

    def resolveLogLevel(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        if targetArg.argValue == 'debug':
            targetGenerator = buildModule.targetGenerator.unwrapped_build_file_generator
            targetCompiler = buildModule.targetCompiler.unwrapped_build_executor
            targetGenerator.regist_flag('-v', ''),
            targetCompiler.regist_arg('-v', '')
        
    @throw_exception
    def resolveStrictMode(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        if targetArg.argValue:
            preloader = buildModule.preloader.unwrapped_preloader
            loader = buildModule.loader.unwrapped_loader
            if not (preloader.outputs.check_outputs() and loader.outputs.check_outputs()):
                raise OHOSException('ERROR', "3002")
        

    def resolveScalableBuild(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        loader = buildModule.loader.unwrapped_loader
        loader.regist_arg("scalable_build", bool(targetArg.argValue))
        

    def resolveBuildPlatformName(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        loader = buildModule.loader.unwrapped_loader
        loader.regist_arg("build_platform_name", targetArg.argValue)
        

    def resolveBuildXts(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        loader = buildModule.loader.unwrapped_loader
        for gn_arg in buildModule.args_dict['gn_args'].argValue:
            if 'build_xts' in gn_arg:
                variable, value = gn_arg.split('=')
                loader.regist_arg(variable, bool(value))
                return
        loader.regist_arg("build_xts", bool(targetArg.argValue))
        

    def resolveIgnoreApiCheck(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        loader = buildModule.loader.unwrapped_loader
        if len(targetArg.argValue):
            loader.regist_arg("ignore_api_check", targetArg.argValue)
        else:
            loader.regist_arg("ignore_api_check", [
                              'xts', 'common', 'developertest'])
        

    def resolveLoadTestConfig(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        loader = buildModule.loader.unwrapped_loader
        loader.regist_arg("load_test_config", bool(targetArg.argValue))
        

    def resolveRenameLastLog(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        if targetArg.argValue:
            out_path = config.out_path
            logfile = os.path.join(out_path, 'build.log')
            if os.path.exists(logfile):
                mtime = os.stat(logfile).st_mtime
                os.rename(logfile, '{}/build.{}.log'.format(out_path, mtime))
        

    def resolveCCache(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        if targetArg.argValue:
            ccache_path = find_executable('ccache')
            if ccache_path is None:
                LogUtil.hb_warning('Failed to find ccache, ccache disabled.')
                return

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
        

    def resolvePycache(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        if targetArg.argValue:
            gn = buildModule.targetGenerator.unwrapped_build_file_generator
            gn.regist_arg('pycache_enable', targetArg.argValue)
        

    def resolveBuildType(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        targetGenerator = buildModule.targetGenerator.unwrapped_build_file_generator
        if targetArg.argValue == 'debug':
            targetGenerator.regist_arg('is_debug', True)
        '''For historical reasons, this value must be debug
        '''
        targetGenerator.regist_arg('ohos_build_type', 'debug')
        

    def resolveFullCompilation(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        if targetArg.argValue:
            build_executor = buildModule.targetCompiler.unwrapped_build_executor
            target_list = build_executor.args_dict.get('build_target', None)
            if isinstance(target_list, list):
                target_list.append('make_all')
                target_list.append('make_test')
            else:
                build_executor.regist_arg(
                    'build_target', ['make_all', 'make_test'])
        
    @throw_exception
    def resolveGnArgs(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        targetGenerator = buildModule.targetGenerator.unwrapped_build_file_generator
        targetGenerator.regist_arg(
            'device_type', buildModule.args_dict['device_type'].argValue)
        targetGenerator.regist_arg(
            'build_variant', buildModule.args_dict['build_variant'].argValue)
        for gn_arg in targetArg.argValue:
            try:
                variable, value = gn_arg.split('=')
                if TypeCheckUtil.isBoolType(value):
                    value = bool(value)
                elif TypeCheckUtil.isIntType(value):
                    value = int(value)
                else:
                    value = str(value)
                targetGenerator.regist_arg(variable, value)
            except ValueError:
                raise OHOSException(f'Invalid gn args: {gn_arg}')
        
    @throw_exception
    def resolveExportPara(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        targetGenerator = buildModule.targetGenerator.unwrapped_build_file_generator
        for gn_arg in targetArg.argValue:
            try:
                variable, value = gn_arg.split(':')
                if TypeCheckUtil.isBoolType(value):
                    value = bool(value)
                elif TypeCheckUtil.isIntType(value):
                    value = int(value)
                else:
                    value = str(value)
                targetGenerator.regist_arg(variable, value)
            except ValueError:
                raise OHOSException(f'Invalid gn args: {gn_arg}')
        
    @throw_exception
    def resolveTest(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        if len(targetArg.argValue) > 1:
            targetGenerator = buildModule.targetGenerator.unwrapped_build_file_generator
            test_type = targetArg.argValue[0]
            test_target = targetArg.argValue[1]
            if test_type == 'notest':
                targetGenerator.regist_arg('ohos_test_args', 'notest')
            elif test_type == "xts":
                targetGenerator.regist_arg('ohos_xts_test_args', test_target)
            else:
                raise OHOSException('Option not support', "3003")
        

    def resolveKeepNinjaGoing(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        if targetArg.argValue:
            targetCompiler = buildModule.targetCompiler.unwrapped_build_executor
            targetCompiler.regist_arg('-k', '1000000000')
        
    def resolveBuildVariant(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        ohos_para_data = []
        ohos_para_file_path = os.path.join(
            config.out_path, 'packages/phone/system/etc/param/ohos.para')
        if not os.path.exists(ohos_para_file_path):
            return
        with open(ohos_para_file_path, 'r', encoding='utf-8') as ohos_para_file:
            for line in ohos_para_file:
                ohos_para_data.append(line)
        for i, line in enumerate(ohos_para_data):
            if ohos_para_data[i].__contains__('const.secure'):
                if targetArg.argValue == 'user':
                    ohos_para_data[i] = 'const.secure=1\n'
                else:
                    ohos_para_data[i] = 'const.secure=0\n'
            if ohos_para_data[i].__contains__('const.debuggable'):
                if targetArg.argValue == 'user':
                    ohos_para_data[i] = 'const.debuggable=0\n'
                else:
                    ohos_para_data[i] = 'const.debuggable=1\n'
        data = ''
        for line in ohos_para_data:
            data += line
        with open(ohos_para_file_path, 'w', encoding='utf-8') as ohos_para_file:
            ohos_para_file.write(data)
        

    def resolveDeviceType(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        ohos_para_data = []
        ohos_para_file_path = os.path.join(
            config.out_path, 'packages/phone/system/etc/param/ohos.para')
        if targetArg.argValue != 'default':
            with open(ohos_para_file_path, 'r', encoding='utf-8') as ohos_para_file:
                for line in ohos_para_file:
                    ohos_para_data.append(line)
            for i, line in enumerate(ohos_para_data):
                if ohos_para_data[i].__contains__('const.build.characteristics'):
                    ohos_para_data[i] = 'const.build.characteristics=' + \
                        targetArg.argValue + '\n'
                    break
            data = ''
            for line in ohos_para_data:
                data += line
            with open(ohos_para_file_path, 'w', encoding='utf-8') as ohos_para_file:
                ohos_para_file.write(data)
        

    def resolveCleanArgs(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        if targetArg.argValue:
            Arg.clean_args_file()
        
    # PlaceHolder
    def resolveCompiler(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        return

    # PlaceHolder
    def resolveJobs(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        return
    
    # PlaceHolder
    def resolveDisablePartOfPostBuild(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        return
    
    # PlaceHolder
    def resolveDisablePackageImage(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        return
    
    # PlaceHolder
    def resolveDisablePartofPostBuild(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        return

    # PlaceHolder
    def resolveBuildOnlyGn(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        return
    
    # PlaceHolder
    def resolveFastRebuild(self, targetArg: Arg, buildModule: BuildModuleInterface, config: Config):
        return

    @throw_exception
    def _mapArgsToFunction(self, args_dict: dict):
        for entity in args_dict.values():
            if isinstance(entity, Arg):
                argsName = entity.argName
                functionName = entity.resolveFuntion
                if not hasattr(self, functionName) or \
                        not hasattr(self.__getattribute__(functionName), '__call__'):
                    raise OHOSException(
                        f'There is no resolution for arg: ' + argsName)
                entity.resolveFuntion = self.__getattribute__(functionName)
                self._argsToFunction[argsName] = self.__getattribute__(
                    functionName)
