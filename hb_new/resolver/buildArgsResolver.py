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

from lite.hb_internal.build.part_rom_statistics import output_part_rom_status
from distutils.spawn import find_executable

from containers.arg import Arg
from containers.status import throw_exception
from exceptions.ohosException import OHOSException
from modules.interface.buildModuleInterface import BuildModuleInterface
from resources.config import Config
from resources.global_var import CURRENT_OHOS_ROOT, DEFAULT_CCACHE_DIR
from resolver.interface.argsResolverInterface import ArgsResolverInterface
from util.typeCheckUtil import TypeCheckUtil
from util.logUtil import LogUtil
from util.systemUtil import SystemUtil
from util.typeCheckUtil import TypeCheckUtil
from util.componentUtil import ComponentUtil
from util.productUtil import ProductUtil


class BuildArgsResolver(ArgsResolverInterface):

    def __init__(self, args_dict: dict):
        super().__init__(args_dict)

    @staticmethod
    def resolveProduct(targetArg: Arg, buildModule: BuildModuleInterface):
        """resolve '--product-name' arg.
        :param targetArg: arg object which is used to get arg value.
        :param buildModule [maybe unused]: build module object which is used to get other services.
        :phase: prebuild.
        """
        config = Config()
        targetGenerator = buildModule.targetGenerator
        targetGenerator.regist_arg('product_name', config.product)
        targetGenerator.regist_arg('product_path', config.product_path)
        targetGenerator.regist_arg(
            'product_config_path', config.product_config_path)

        targetGenerator.regist_arg('device_name', config.board)
        targetGenerator.regist_arg('device_path', config.device_path)
        targetGenerator.regist_arg('device_company', config.device_company)
        targetGenerator.regist_arg(
            'device_config_path', config.device_config_path)

        targetGenerator.regist_arg('target_cpu', config.target_cpu)
        targetGenerator.regist_arg(
            'is_{}_system'.format(config.os_level), True)

        targetGenerator.regist_arg('ohos_kernel_type', config.kernel)
        targetGenerator.regist_arg('ohos_build_compiler_specified',
                                   ProductUtil.get_compiler(config.device_path))

        targetGenerator.regist_arg('ohos_build_time',
                                   SystemUtil.get_current_time(type='timestamp'))
        targetGenerator.regist_arg('ohos_build_datetime',
                                   SystemUtil.get_current_time(type='datetime'))

        features_dict = ProductUtil.get_features_dict(config.product_json)
        for key, value in features_dict.items():
            targetGenerator.regist_arg(key, value)

        if ProductUtil.get_compiler(config.device_path) == 'clang':
            targetGenerator.regist_arg(
                'ohos_build_compiler_dir', config.clang_path)

        if targetArg.argValue == 'ohos-sdk':
            targetGenerator = buildModule.targetGenerator
            targetGenerator.regist_arg('build_ohos_sdk', True)
            if len(buildModule.args_dict['build_target'].argValue) == 0:
                buildModule.args_dict['build_target'].argValue = [
                    'build_ohos_sdk']
            buildModule.args_dict['target_cpu'].argValue = 'arm64'

    @staticmethod
    def resolveTargetCpu(targetArg: Arg, buildModule: BuildModuleInterface):
        """resolve '--target-cpu' arg.
        :param targetArg: arg object which is used to get arg value.
        :param buildModule [maybe unused]: build module object which is used to get other services.
        :phase: prebuild.
        """
        config = Config()
        config.target_cpu = targetArg.argValue

    @staticmethod
    @throw_exception
    def resolveBuildTarget(targetArg: Arg, buildModule: BuildModuleInterface):
        """resolve '--build-target' arg.
        :param targetArg: arg object which is used to get arg value.
        :param buildModule [maybe unused]: build module object which is used to get other services.
        :phase: prebuild.
        :raise OHOSException: when build target not exist in compiling product.
        """
        config = Config()
        build_executor = buildModule.targetCompiler
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
                                  'this compilation will compile only this component'.format(
                                      component_name),
                                  'warning')
                target_list.append(component_name)
                target_list.append(component_name + '_test')
            else:
                component_name = ComponentUtil.get_component_name(os.getcwd())
                component_name = os.path.basename(
                    os.getcwd()) if component_name == '' else component_name
                raise OHOSException('There is no target component "{}" for the current product "{}"'
                                    .format(component_name, Config().product), "4001")
        build_executor.regist_arg('build_target', target_list)

    @staticmethod
    def resolveLogLevel(targetArg: Arg, buildModule: BuildModuleInterface):
        """resolve '--log-level' arg.
        :param targetArg: arg object which is used to get arg value.
        :param buildModule [maybe unused]: build module object which is used to get other services.
        :phase: targetGenerate.
        """
        if targetArg.argValue == 'debug':
            targetGenerator = buildModule.targetGenerator
            targetCompiler = buildModule.targetCompiler
            targetGenerator.regist_flag('-v', ''),
            targetGenerator.regist_flag(
                '--tracelog', '{}/gn_trace.log'.format(Config().out_path))
            targetGenerator.regist_flag('--ide', 'json')
            targetCompiler.regist_arg('-v', '')

    @staticmethod
    @throw_exception
    def resolveStrictMode(targetArg: Arg, buildModule: BuildModuleInterface):
        """resolve '--strict-mode' arg.
        :param targetArg: arg object which is used to get arg value.
        :param buildModule [maybe unused]: build module object which is used to get other services.
        :phase: load.
        :raise OHOSException: when preloader or loader results not correct
        """
        if targetArg.argValue:
            preloader = buildModule.preloader
            loader = buildModule.loader
            if not preloader.outputs.check_outputs():
                raise OHOSException('Preloader result not correct', "1001")
            if not loader.outputs.check_outputs():
                raise OHOSException('Loader result not correct ', "2001")

    @staticmethod
    def resolveScalableBuild(targetArg: Arg, buildModule: BuildModuleInterface):
        """resolve '--scalable-build' arg.
        :param targetArg: arg object which is used to get arg value.
        :param buildModule [maybe unused]: build module object which is used to get other services.
        :phase: load.
        """
        loader = buildModule.loader
        loader.regist_arg("scalable_build", bool(targetArg.argValue))

    @staticmethod
    def resolveBuildPlatformName(targetArg: Arg, buildModule: BuildModuleInterface):
        """resolve '---build-platform-name' arg
        :param targetArg: arg object which is used to get arg value.
        :param buildModule [maybe unused]: build module object which is used to get other services.
        :phase: load.
        """
        loader = buildModule.loader
        loader.regist_arg("build_platform_name", targetArg.argValue)

    @staticmethod
    def resolveBuildXts(targetArg: Arg, buildModule: BuildModuleInterface):
        """resolve '--build-xts' arg
        :param targetArg: arg object which is used to get arg value.
        :param buildModule [maybe unused]: build module object which is used to get other services.
        :phase: load.
        """
        loader = buildModule.loader
        for gn_arg in buildModule.args_dict['gn_args'].argValue:
            if 'build_xts' in gn_arg:
                variable, value = gn_arg.split('=')
                loader.regist_arg(variable, bool(value))
                return
        loader.regist_arg("build_xts", bool(targetArg.argValue))

    @staticmethod
    def resolveIgnoreApiCheck(targetArg: Arg, buildModule: BuildModuleInterface):
        """resolve '--ignore-api-check' arg
        :param targetArg: arg object which is used to get arg value.
        :param buildModule [maybe unused]: build module object which is used to get other services.
        :phase: load.
        """
        loader = buildModule.loader
        if len(targetArg.argValue):
            loader.regist_arg("ignore_api_check", targetArg.argValue)
        else:
            loader.regist_arg("ignore_api_check", [
                              'xts', 'common', 'developertest'])

    @staticmethod
    def resolveLoadTestConfig(targetArg: Arg, buildModule: BuildModuleInterface):
        """resolve '--load-test-config' arg
        :param targetArg: arg object which is used to get arg value.
        :param buildModule [maybe unused]: build module object which is used to get other services.
        :phase: load.
        """
        loader = buildModule.loader
        loader.regist_arg("load_test_config", bool(targetArg.argValue))

    @staticmethod
    def resolveRenameLastLog(targetArg: Arg, buildModule: BuildModuleInterface):
        """resolve '--rename-last-log' arg
        :param targetArg: arg object which is used to get arg value.
        :param buildModule [maybe unused]: build module object which is used to get other services.
        :phase: prebuild.
        """
        if targetArg.argValue:
            config = Config()
            out_path = config.out_path
            logfile = os.path.join(out_path, 'build.log')
            if os.path.exists(logfile):
                mtime = os.stat(logfile).st_mtime
                os.rename(logfile, '{}/build.{}.log'.format(out_path, mtime))

    @staticmethod
    def resolveCCache(targetArg: Arg, buildModule: BuildModuleInterface):
        """resolve '--ccache' arg
        :param targetArg: arg object which is used to get arg value.
        :param buildModule [maybe unused]: build module object which is used to get other services.
        :phase: prebuild.
        """
        if targetArg.argValue:
            config = Config()
            ccache_path = find_executable('ccache')
            if ccache_path is None:
                LogUtil.hb_warning('Failed to find ccache, ccache disabled.')
                return

            ccache_local_dir = os.environ.get('CCACHE_LOCAL_DIR')
            ccache_base = os.environ.get('CCACHE_BASE')
            if not ccache_local_dir:
                ccache_local_dir = '.ccache'
            if ccache_base is None:
                ccache_base = DEFAULT_CCACHE_DIR
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
                ccache_max_size = '50G'

            cmd = ['ccache', '-M', ccache_max_size]

            SystemUtil.exec_command(cmd, log_path=config.log_path)

    @staticmethod
    def resolvePycache(targetArg: Arg, buildModule: BuildModuleInterface):
        """resolve '--enable-pycache' arg
        :param targetArg: arg object which is used to get arg value.
        :param buildModule [maybe unused]: build module object which is used to get other services.
        :phase: prebuild.
        """
        if targetArg.argValue:
            gn = buildModule.targetGenerator
            gn.regist_arg('pycache_enable', targetArg.argValue)

    @staticmethod
    def resolveBuildType(targetArg: Arg, buildModule: BuildModuleInterface):
        """resolve '--build-type' arg
        :param targetArg: arg object which is used to get arg value.
        :param buildModule [maybe unused]: build module object which is used to get other services.
        :phase: targetGenerate.
        """
        targetGenerator = buildModule.targetGenerator
        if targetArg.argValue == 'debug':
            targetGenerator.regist_arg('is_debug', True)
        # For historical reasons, this value must be debug
        targetGenerator.regist_arg('ohos_build_type', 'debug')

    @staticmethod
    def resolveFullCompilation(targetArg: Arg, buildModule: BuildModuleInterface):
        """resolve '--full-compilation' arg
        :param targetArg: arg object which is used to get arg value.
        :param buildModule [maybe unused]: build module object which is used to get other services.
        :phase: prebuild.
        """
        if targetArg.argValue:
            build_executor = buildModule.targetCompiler
            target_list = build_executor.args_dict.get('build_target', None)
            if isinstance(target_list, list):
                target_list.append('make_all')
                target_list.append('make_test')
            else:
                build_executor.regist_arg(
                    'build_target', ['make_all', 'make_test'])

    @staticmethod
    @throw_exception
    def resolveGnArgs(targetArg: Arg, buildModule: BuildModuleInterface):
        """resolve '--gn-args' arg
        :param targetArg: arg object which is used to get arg value.
        :param buildModule [maybe unused]: build module object which is used to get other services.
        :phase: prebuild.
        :raise OHOSException: when some gn_arg is not in 'key=value' format.
        """
        targetGenerator = buildModule.targetGenerator
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
                raise OHOSException(f'Invalid gn args: {gn_arg}', "0001")

    @staticmethod
    @throw_exception
    def resolveExportPara(targetArg: Arg, buildModule: BuildModuleInterface):
        """resolve '--export-para' arg
        :param targetArg: arg object which is used to get arg value.
        :param buildModule [maybe unused]: build module object which is used to get other services.
        :phase: targetGenerate.
        """
        targetGenerator = buildModule.targetGenerator
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
                raise OHOSException(f'Invalid gn args: {gn_arg}', "0001")

    @staticmethod
    @throw_exception
    def resolveTest(targetArg: Arg, buildModule: BuildModuleInterface):
        """resolve '--test' arg
        :param targetArg: arg object which is used to get arg value.
        :param buildModule [maybe unused]: build module object which is used to get other services.
        :phase: targetGenerate.
        """
        if len(targetArg.argValue) > 1:
            targetGenerator = buildModule.targetGenerator
            # TODO: Ask sternly why the xts subsystem passes parameters in this way?
            if 'notest' in targetArg.argValue:
                targetGenerator.regist_arg('ohos_test_args', 'notest')
            elif 'xts' in targetArg.argValue:
                test_target_index = 1
                if targetArg.argValue.index('xts') == 1:
                    test_target_index = 0
                targetGenerator.regist_arg(
                    'ohos_xts_test_args', targetArg.argValue[test_target_index])
            else:
                raise OHOSException('Test type value "{}" is not support'
                                    .format(targetArg.argValue), "0002")

    @staticmethod
    def resolveKeepNinjaGoing(targetArg: Arg, buildModule: BuildModuleInterface):
        """resolve '--keep-ninja-going' arg
        :param targetArg: arg object which is used to get arg value.
        :param buildModule [maybe unused]: build module object which is used to get other services.
        :phase: targetCompilation.
        """
        if targetArg.argValue:
            targetCompiler = buildModule.targetCompiler
            targetCompiler.regist_arg('-k', '1000000000')

    @staticmethod
    def resolveBuildVariant(targetArg: Arg, buildModule: BuildModuleInterface):
        """resolve '--build-variant' arg
        :param targetArg: arg object which is used to get arg value.
        :param buildModule [maybe unused]: build module object which is used to get other services.
        :phase: postTargetCompilation.
        """
        config = Config()
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

    @staticmethod
    def resolveDeviceType(targetArg: Arg, buildModule: BuildModuleInterface):
        """resolve '--device-type' arg
        :param targetArg: arg object which is used to get arg value.
        :param buildModule [maybe unused]: build module object which is used to get other services.
        :phase: postTargetCompilation.
        """
        config = Config()
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

    @staticmethod
    def resolveCleanArgs(targetArg: Arg, buildModule: BuildModuleInterface):
        """resolve '--clean-args' arg
        :param targetArg: arg object which is used to get arg value.
        :param buildModule [maybe unused]: build module object which is used to get other services.
        :phase: postbuild
        """
        if targetArg.argValue:
            Arg.clean_args_file()

    @staticmethod
    def resolveArchiveImage(targetArg: Arg, buildModule: BuildModuleInterface):
        """resolve '--archive-image' arg
        :param targetArg: arg object which is used to get arg value.
        :param buildModule [maybe unused]: build module object which is used to get other services.
        :phase: postTargetCompilation
        """
        if targetArg.argValue:
            config = Config()
            image_path = os.path.join(
                config.out_path, 'packages', 'phone', 'images')
            if os.path.exists(image_path):
                packaged_file_path = os.path.join(
                    config.out_path, 'images.tar.gz')
                cmd = ['tar', '-zcvf', packaged_file_path, image_path]
                SystemUtil.exec_command(cmd, log_path=config.out_path)
            else:
                LogUtil.hb_info(
                    '"--archive-image" option not work, cause the currently compiled product is not a standard product')

    @staticmethod
    def resolveRomSizeStatistics(targetArg: Arg, buildModule: BuildModuleInterface):
        """resolve '--rom-size-statistics' arg
        :param targetArg: arg object which is used to get arg value.
        :param buildModule [maybe unused]: build module object which is used to get other services.
        :phase: postTargetCompilation
        """
        if targetArg.argValue:
            output_part_rom_status(CURRENT_OHOS_ROOT)

    # PlaceHolder
    @staticmethod
    def resolveCompiler(targetArg: Arg, buildModule: BuildModuleInterface):
        return

    # PlaceHolder
    @staticmethod
    def resolveJobs(targetArg: Arg, buildModule: BuildModuleInterface):
        return

    # PlaceHolder
    @staticmethod
    def resolveDisablePartOfPostBuild(targetArg: Arg, buildModule: BuildModuleInterface):
        return

    # PlaceHolder
    @staticmethod
    def resolveDisablePackageImage(targetArg: Arg, buildModule: BuildModuleInterface):
        return

    # PlaceHolder
    @staticmethod
    def resolveDisablePartofPostBuild(targetArg: Arg, buildModule: BuildModuleInterface):
        return

    # PlaceHolder
    @staticmethod
    def resolveBuildOnlyGn(targetArg: Arg, buildModule: BuildModuleInterface):
        return

    # PlaceHolder
    @staticmethod
    def resolveFastRebuild(targetArg: Arg, buildModule: BuildModuleInterface):
        return
