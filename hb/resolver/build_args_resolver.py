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
import re
import sys
import stat
import subprocess

from datetime import datetime
from distutils.spawn import find_executable
from containers.arg import Arg
from containers.status import throw_exception
from exceptions.ohos_exception import OHOSException
from modules.interface.build_module_interface import BuildModuleInterface
from resources.config import Config
from resources.global_var import CURRENT_OHOS_ROOT, DEFAULT_BUILD_ARGS
from resolver.interface.args_resolver_interface import ArgsResolverInterface
from util.type_check_util import TypeCheckUtil
from util.io_util import IoUtil
from util.log_util import LogUtil
from util.system_util import SystemUtil
from util.type_check_util import TypeCheckUtil
from util.component_util import ComponentUtil
from util.product_util import ProductUtil
from util.post_build.part_rom_statistics import output_part_rom_status


class BuildArgsResolver(ArgsResolverInterface):

    def __init__(self, args_dict: dict):
        super().__init__(args_dict)

    @staticmethod
    def resolve_product(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--product-name' arg.
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: prebuild.
        """
        config = Config()
        target_generator = build_module.target_generator
        target_generator.regist_arg('product_name', config.product)
        target_generator.regist_arg('product_path', config.product_path)
        target_generator.regist_arg(
            'product_config_path', config.product_config_path)

        target_generator.regist_arg('device_name', config.board)
        target_generator.regist_arg('device_path', config.device_path)
        target_generator.regist_arg('device_company', config.device_company)
        target_generator.regist_arg(
            'device_config_path', config.device_config_path)

        target_generator.regist_arg('target_cpu', config.target_cpu)
        target_generator.regist_arg(
            'is_{}_system'.format(config.os_level), True)

        target_generator.regist_arg('ohos_kernel_type', config.kernel)
        target_generator.regist_arg('ohos_build_compiler_specified',
                                    ProductUtil.get_compiler(config.device_path))

        target_generator.regist_arg('ohos_build_time',
                                    SystemUtil.get_current_time(time_type='timestamp'))
        target_generator.regist_arg('ohos_build_datetime',
                                    SystemUtil.get_current_time(time_type='datetime'))

        features_dict = ProductUtil.get_features_dict(config.product_json)
        for key, value in features_dict.items():
            target_generator.regist_arg(key, value)

        if ProductUtil.get_compiler(config.device_path) == 'clang':
            target_generator.regist_arg(
                'ohos_build_compiler_dir', config.clang_path)

        if target_arg.arg_value == 'ohos-sdk':
            target_generator = build_module.target_generator
            target_generator.regist_arg('build_ohos_sdk', True)
            target_generator.regist_arg('build_ohos_ndk', True)
            if len(build_module.args_dict['build_target'].arg_value) == 0:
                build_module.args_dict['build_target'].arg_value = [
                    'build_ohos_sdk']
            build_module.args_dict['target_cpu'].arg_value = 'arm64'
        elif target_arg.arg_value == 'arkui-cross':
            target_generator = build_module.target_generator
            target_generator.regist_arg('is_cross_platform_build', True)
            target_generator.regist_arg('build_cross_platform_version', True)
            target_generator.regist_arg('enable_ng_build', True)
            target_generator.regist_arg('is_component_build', False)
            target_generator.regist_arg('use_musl', False)
            if len(build_module.args_dict['build_target'].arg_value) == 0:
                build_module.args_dict['build_target'].arg_value = [
                    'arkui_targets']

    @staticmethod
    def resolve_target_cpu(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--target-cpu' arg.
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: prebuild.
        """
        config = Config()
        default_build_args = IoUtil.read_json_file(DEFAULT_BUILD_ARGS)
        if config.target_cpu == "":
            config.target_cpu = target_arg.arg_value
        elif target_arg.arg_value != default_build_args.get("target_cpu").get("argDefault"):
            config.target_cpu = target_arg.arg_value

    @staticmethod
    def resolve_target_os(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--target-os' arg.
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: prebuild.
        """
        config = Config()
        default_build_args = IoUtil.read_json_file(DEFAULT_BUILD_ARGS)
        if config.target_os == "":
            config.target_os = target_arg.arg_value
        elif target_arg.arg_value != default_build_args.get("target_os").get("argDefault"):
            config.target_os = target_arg.arg_value

    @staticmethod
    @throw_exception
    def resolve_build_target(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--build-target' arg.
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: prebuild.
        :raise OHOSException: when build target not exist in compiling product.
        """
        config = Config()
        build_executor = build_module.target_compiler
        target_list = []
        if len(target_arg.arg_value):
            target_list = target_arg.arg_value
        else:
            if os.getcwd() == CURRENT_OHOS_ROOT:
                target_list = ['images']
            elif ComponentUtil.is_in_component_dir(os.getcwd()) and \
                    ComponentUtil.is_component_in_product(
                    ComponentUtil.get_component_name(os.getcwd()), Config().product):
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
    def resolve_rename_last_log(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--rename-last-log' arg
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: prebuild.
        """
        if target_arg.arg_value:
            config = Config()
            out_path = config.out_path
            logfile = os.path.join(out_path, 'build.log')
            if os.path.exists(logfile):
                mtime = os.stat(logfile).st_mtime
                os.rename(logfile, '{}/build.{}.log'.format(out_path, mtime))

    @staticmethod
    def resolve_ccache(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--ccache' arg
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: prebuild.
        """
        if target_arg.arg_value:
            config = Config()
            ccache_path = find_executable('ccache')
            if ccache_path is None:
                LogUtil.hb_warning('Failed to find ccache, ccache disabled.')
                return
            else:
                target_generator = build_module.target_generator
                target_generator.regist_arg(
                    'ohos_build_enable_ccache', target_arg.arg_value)

            ccache_local_dir = os.environ.get('CCACHE_LOCAL_DIR')
            ccache_base = os.environ.get('CCACHE_BASE')
            if not ccache_local_dir:
                ccache_local_dir = '.ccache'
            if not ccache_base:
                ccache_base = os.environ.get('HOME')
            ccache_base = os.path.join(ccache_base, ccache_local_dir)
            if not os.path.exists(ccache_base):
                os.makedirs(ccache_base)

            ccache_log_suffix = os.environ.get('CCACHE_LOG_SUFFIX')
            if ccache_log_suffix:
                logfile = os.path.join(
                    ccache_base, "ccache.{}.log".format(ccache_log_suffix))
            else:
                logfile = os.path.join(ccache_base, "ccache.log")
            if os.path.exists(logfile):
                oldfile = os.path.join(ccache_base, '{}.old'.format(logfile))
                if os.path.exists(oldfile):
                    os.unlink(oldfile)
                os.rename(logfile, oldfile)

            os.environ['CCACHE_EXEC'] = ccache_path
            os.environ['CCACHE_LOGFILE'] = logfile
            os.environ['USE_CCACHE'] = '1'
            os.environ['CCACHE_DIR'] = ccache_base
            os.environ['CCACHE_UMASK'] = '002'
            os.environ['CCACHE_BASEDIR'] = config.root_path
            ccache_max_size = os.environ.get('CCACHE_MAXSIZE')
            if not ccache_max_size:
                ccache_max_size = '50G'

            cmd = ['ccache', '-M', ccache_max_size]

            SystemUtil.exec_command(cmd, log_path=config.log_path)

    @staticmethod
    def resolve_pycache(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--enable-pycache' arg
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: prebuild.
        """
        if target_arg.arg_value:
            config = Config()
            pycache_dir = os.environ.get('CCACHE_BASE')
            # The default value is HOME for local users
            if not pycache_dir:
                pycache_dir = os.environ.get('HOME')
            pycache_dir = os.path.join(pycache_dir, '.pycache')
            os.environ['PYCACHE_DIR'] = pycache_dir
            pyd_start_cmd = [
                'python3',
                '{}/build/scripts/util/pyd.py'.format(config.root_path),
                '--root',
                pycache_dir,
                '--start',
            ]
            cmd = ['/bin/bash', '-c', ' '.join(pyd_start_cmd), '&']
            subprocess.Popen(cmd)

    @staticmethod
    def resolve_full_compilation(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--full-compilation' arg
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: prebuild.
        """
        if target_arg.arg_value:
            build_executor = build_module.target_compiler
            target_list = build_executor.args_dict.get('build_target', None)
            if isinstance(target_list, list):
                target_list.append('make_all')
                target_list.append('make_test')
            else:
                build_executor.regist_arg(
                    'build_target', ['make_all', 'make_test'])

    @staticmethod
    @throw_exception
    def resolve_gn_args(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--gn-args' arg
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: prebuild.
        :raise OHOSException: when some gn_arg is not in 'key=value' format.
        """
        target_generator = build_module.target_generator
        target_generator.regist_arg(
            'device_type', build_module.args_dict['device_type'].arg_value)
        target_generator.regist_arg(
            'build_variant', build_module.args_dict['build_variant'].arg_value)
        for gn_args in target_arg.arg_value:
            try:
                gn_args_list = gn_args.split()
                for gn_arg in gn_args_list:
                    variable, value = gn_arg.split('=')
                    if TypeCheckUtil.is_bool_type(value):
                        if str(value).lower() == 'false':
                            convert_value = False
                        elif str(value).lower() == 'true':
                            convert_value = True
                    elif TypeCheckUtil.is_int_type(value):
                        convert_value = int(value)
                    elif isinstance(value, list):
                        convert_value = list(value)
                    else:
                        convert_value = str(value).strip('"')
                    target_generator.regist_arg(variable, convert_value)
            except ValueError:
                raise OHOSException(f'Invalid gn args: {gn_arg}', "0001")

    @staticmethod
    @throw_exception
    def resolve_gn_flags(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--gn-flags' arg
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: targetGenerate.
        :raise OHOSException: when some gn_arg is not in 'key=value' format.
        """
        target_generator = build_module.target_generator
        gn_flags_list = []
        for gn_flags in target_arg.arg_value:
            gn_flags = re.sub("'", "", gn_flags)
            gn_flags_list.append(gn_flags)
        target_generator.regist_flag('gn_flags', gn_flags_list)

    @staticmethod
    @throw_exception
    def resolve_ninja_args(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--ninja-args' arg
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: prebuild.
        :raise OHOSException: when the value of the ninja parameter does not use quotation marks.
        """
        build_executor = build_module.target_compiler
        ninja_args_list = []
        for ninja_arg in target_arg.arg_value:
            ninja_arg = re.sub("'", "", ninja_arg)
            ninja_args_list.append(ninja_arg)
        build_executor.regist_arg('ninja_args', ninja_args_list)

    @staticmethod
    @throw_exception
    def resolve_strict_mode(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--strict-mode' arg.
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: load.
        :raise OHOSException: when preloader or loader results not correct
        """
        if target_arg.arg_value:
            preloader = build_module.preloader
            loader = build_module.loader
            if not preloader.outputs.check_outputs():
                raise OHOSException('Preloader result not correct', "1001")
            if not loader.outputs.check_outputs():
                raise OHOSException('Loader result not correct ', "2001")

    @staticmethod
    def resolve_scalable_build(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--scalable-build' arg.
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: load.
        """
        loader = build_module.loader
        loader.regist_arg("scalable_build", target_arg.arg_value)

    @staticmethod
    def resolve_build_example(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--build-example' arg.
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: load.
        """
        loader = build_module.loader
        loader.regist_arg("build_example", target_arg.arg_value)

    @staticmethod
    def resolve_build_platform_name(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '---build-platform-name' arg
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: load.
        """
        loader = build_module.loader
        loader.regist_arg("build_platform_name", target_arg.arg_value)

    @staticmethod
    def resolve_build_xts(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--build-xts' arg
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: load.
        """
        loader = build_module.loader
        for gn_arg in build_module.args_dict['gn_args'].arg_value:
            if 'build_xts' in gn_arg:
                variable, value = gn_arg.split('=')
                if str(value).lower() == 'false':
                    value = False
                elif str(value).lower() == 'true':
                    value = True
                loader.regist_arg(variable, value)
                return
        loader.regist_arg("build_xts", target_arg.arg_value)

    @staticmethod
    def resolve_ignore_api_check(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--ignore-api-check' arg
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: load.
        """
        loader = build_module.loader
        if len(target_arg.arg_value):
            loader.regist_arg("ignore_api_check", target_arg.arg_value)
        else:
            loader.regist_arg("ignore_api_check", [
                              'xts', 'common', 'developertest'])

    @staticmethod
    def resolve_load_test_config(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--load-test-config' arg
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: load.
        """
        loader = build_module.loader
        loader.regist_arg("load_test_config", target_arg.arg_value)

    @staticmethod
    @throw_exception
    def resolve_export_para(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--export-para' arg
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: targetGenerate.
        """
        target_generator = build_module.target_generator
        for gn_arg in target_arg.arg_value:
            try:
                variable, value = gn_arg.split(':')
                if TypeCheckUtil.is_bool_type(value):
                    if str(value).lower() == 'false':
                        value = False
                    elif str(value).lower() == 'true':
                        value = True
                elif TypeCheckUtil.is_int_type(value):
                    value = int(value)
                else:
                    value = str(value)
                target_generator.regist_arg(variable, value)
            except ValueError:
                raise OHOSException(f'Invalid gn args: {gn_arg}', "0001")

    @staticmethod
    def resolve_log_level(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--log-level' arg.
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: targetGenerate.
        """
        if target_arg.arg_value == 'debug':
            target_generator = build_module.target_generator
            target_compiler = build_module.target_compiler
            target_generator.regist_flag('-v', ''),
            target_generator.regist_flag(
                '--tracelog', '{}/gn_trace.log'.format(Config().out_path))
            target_generator.regist_flag('--ide', 'json')
            target_compiler.regist_arg('-v', '')

    @staticmethod
    @throw_exception
    def resolve_test(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--test' arg
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: targetGenerate.
        """
        if len(target_arg.arg_value) > 1:
            target_generator = build_module.target_generator
            # TODO: Ask sternly why the xts subsystem passes parameters in this way?
            if 'notest' in target_arg.arg_value:
                target_generator.regist_arg('ohos_test_args', 'notest')
            elif 'xts' in target_arg.arg_value:
                test_target_index = 1
                if target_arg.arg_value.index('xts') == 1:
                    test_target_index = 0
                target_generator.regist_arg(
                    'ohos_xts_test_args', target_arg.arg_value[test_target_index])
            else:
                raise OHOSException('Test type value "{}" is not support'
                                    .format(target_arg.arg_value), "0002")

    @staticmethod
    def resolve_build_type(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--build-type' arg
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: targetGenerate.
        """
        target_generator = build_module.target_generator
        if target_arg.arg_value == 'debug':
            target_generator.regist_arg('is_debug', True)
        # For historical reasons, this value must be debug
        target_generator.regist_arg('ohos_build_type', 'debug')

    @staticmethod
    def resolve_keep_ninja_going(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--keep-ninja-going' arg
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: targetCompilation.
        """
        if target_arg.arg_value:
            target_compiler = build_module.target_compiler
            target_compiler.regist_arg('-k1000000', '')

    @staticmethod
    def resolve_build_variant(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--build-variant' arg
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
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
                if target_arg.arg_value == 'user':
                    ohos_para_data[i] = 'const.secure=1\n'
                else:
                    ohos_para_data[i] = 'const.secure=0\n'
            if ohos_para_data[i].__contains__('const.debuggable'):
                if target_arg.arg_value == 'user':
                    ohos_para_data[i] = 'const.debuggable=0\n'
                else:
                    ohos_para_data[i] = 'const.debuggable=1\n'
        data = ''
        for line in ohos_para_data:
            data += line
        with os.fdopen(os.open(ohos_para_file_path, os.O_RDWR | os.O_CREAT), 'w', encoding='utf-8') as ohos_para_file:
            ohos_para_file.write(data)

    @staticmethod
    def resolve_device_type(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--device-type' arg
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: postTargetCompilation.
        """
        config = Config()
        ohos_para_data = []
        ohos_para_file_path = os.path.join(
            config.out_path, 'packages/phone/system/etc/param/ohos.para')
        if target_arg.arg_value != 'default':
            with os.fdopen(os.open(ohos_para_file_path,
                                   os.O_RDWR | os.O_CREAT, stat.S_IWUSR | stat.S_IRUSR),
                           'r', encoding='utf-8') as ohos_para_file:
                for line in ohos_para_file:
                    ohos_para_data.append(line)
            for i, line in enumerate(ohos_para_data):
                if ohos_para_data[i].__contains__('const.build.characteristics'):
                    ohos_para_data[i] = 'const.build.characteristics=' + \
                        target_arg.arg_value + '\n'
                    break
            data = ''
            for line in ohos_para_data:
                data += line
            with os.fdopen(os.open(ohos_para_file_path,
                                   os.O_RDWR | os.O_CREAT, stat.S_IWUSR | stat.S_IRUSR),
                           'r', encoding='utf-8') as ohos_para_file:
                ohos_para_file.write(data)

    @staticmethod
    def resolve_archive_image(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--archive-image' arg
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: postTargetCompilation
        """
        if target_arg.arg_value:
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
    def resolve_rom_size_statistics(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--rom-size-statistics' arg
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: postTargetCompilation
        """
        if target_arg.arg_value:
            output_part_rom_status(CURRENT_OHOS_ROOT)

    @staticmethod
    def resolve_stat_ccache(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve "--stat-ccache' arg
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: postTargetCompilation
        """
        if target_arg.arg_value:
            config = Config()
            ccache_path = find_executable('ccache')
            if ccache_path is None:
                LogUtil.hb_warning('Failed to find ccache, ccache disabled.')
                return
            ccache_log_suffix = os.environ.get('CCACHE_LOG_SUFFIX')
            if ccache_log_suffix:
                logfile = "ccache.{}.log".format(ccache_log_suffix)
            else:
                logfile = "ccache.log"
            ccache_local_dir = os.environ.get('CCACHE_LOCAL_DIR')
            if not ccache_local_dir:
                ccache_local_dir = '.ccache'
            ccache_base = os.environ.get('CCACHE_BASE')

            # The default value is HOME for local users
            if not ccache_base:
                ccache_base = os.environ.get('HOME')
            ccache_base = os.path.join(ccache_base, ccache_local_dir)
            cmd = [
                'python3', '{}/build/scripts/summary_ccache_hitrate.py'.format(
                    config.root_path), '{}/{}'.format(ccache_base, logfile)
            ]
            SystemUtil.exec_command(cmd, log_path=config.log_path)

    @staticmethod
    def resolve_get_warning_list(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve "--get-warning-list' arg
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: postTargetCompilation
        """
        if target_arg.arg_value:
            config = Config()
            cmd = [
                'python3',
                '{}/build/scripts/get_warnings.py'.format(config.root_path),
                '--build-log-file',
                '{}/build.log'.format(config.out_path),
                '--warning-out-file',
                '{}/packages/WarningList.txt'.format(config.out_path),
            ]
            SystemUtil.exec_command(cmd, log_path=config.log_path)

    @staticmethod
    def resolve_generate_ninja_trace(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve "--generate-ninja-trace' arg
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: postTargetCompilation
        """
        if target_arg.arg_value:
            config = Config()
            epoch = datetime.utcfromtimestamp(0)
            unixtime = '%f' % (
                (build_module.target_compiler._start_time - epoch).total_seconds() * 10**9)
            cmd = [
                'python3',
                '{}/build/scripts/ninja2trace.py'.format(config.root_path),
                '--ninja-log',
                '{}/.ninja_log'.format(config.out_path),
                "--trace-file",
                "{}/build.trace".format(config.out_path),
                "--ninja-start-time",
                str(unixtime),
                "--duration-file",
                "{}/sorted_action_duration.txt".format(config.out_path),
            ]
            SystemUtil.exec_command(cmd, log_path=config.log_path)

    @staticmethod
    def resolve_compute_overlap_rate(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve "--compute-overlap-rate' arg
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: postTargetCompilation
        """
        if target_arg.arg_value:
            config = Config()
            subsystem_config_overlay_path = os.path.join(config.product_path,
                                                         'subsystem_config_overlay.json')
            if os.path.isfile(subsystem_config_overlay_path):
                cmd = [
                    'python3',
                    '{}/build/ohos/statistics/build_overlap_statistics.py'.format(
                        config.root_path), "--build-out-dir", config.out_path,
                    "--subsystem-config-file",
                    "{}/build/subsystem_config.json".format(config.root_path),
                    "--subsystem-config-overlay-file",
                    "{}/subsystem_config_overlay.json".format(
                        config.product_path),
                    "--root-source-dir", config.root_path
                ]
            else:
                cmd = [
                    'python3',
                    '{}/build/ohos/statistics/build_overlap_statistics.py'.format(
                        config.root_path), "--build-out-dir", config.out_path,
                    "--subsystem-config-file",
                    "{}/build/subsystem_config.json".format(config.root_path),
                    "--root-source-dir", config.root_path
                ]
            SystemUtil.exec_command(cmd, log_path=config.log_path)

    @staticmethod
    def resolve_deps_guard(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--deps-guard' arg
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: postbuild
        """
        if target_arg.arg_value:
            config = Config()
            if config.os_level == "standard":
                sys.path.append(os.path.join(
                    config.root_path, "developtools/integration_verification/tools/deps_guard"))
                from deps_guard import deps_guard
                deps_guard(config.out_path)

    @staticmethod
    def resolve_clean_args(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--clean-args' arg
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: postbuild
        """
        if target_arg.arg_value:
            Arg.clean_args_file()

    # PlaceHolder
    @staticmethod
    def resolve_compiler(target_arg: Arg, build_module: BuildModuleInterface):
        return

    # PlaceHolder
    @staticmethod
    def resolve_jobs(target_arg: Arg, build_module: BuildModuleInterface):
        return

    # PlaceHolder
    @staticmethod
    def resolve_disable_part_of_post_build(target_arg: Arg, build_module: BuildModuleInterface):
        return

    # PlaceHolder
    @staticmethod
    def resolve_disable_package_image(target_arg: Arg, build_module: BuildModuleInterface):
        return

    # PlaceHolder
    @staticmethod
    def resolve_disable_post_build(target_arg: Arg, build_module: BuildModuleInterface):
        return

    # PlaceHolder
    @staticmethod
    def resolve_build_only_gn(target_arg: Arg, build_module: BuildModuleInterface):
        return

    # PlaceHolder
    @staticmethod
    def resolve_fast_rebuild(target_arg: Arg, build_module: BuildModuleInterface):
        return
