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

from containers.arg import Arg
from containers.arg import ModuleType
from resolver.interface.args_resolver_interface import ArgsResolverInterface
from modules.interface.indep_build_module_interface import IndepBuildModuleInterface
from util.component_util import ComponentUtil
from exceptions.ohos_exception import OHOSException
from util.log_util import LogUtil
from util.io_util import IoUtil
import subprocess
from distutils.spawn import find_executable
from resources.global_var import COMPONENTS_PATH_DIR


def get_part_name():
    part_name_list = []
    if len(sys.argv) > 2 and not sys.argv[2].startswith("-"):
        for name in sys.argv[2:]:
            if not name.startswith('-'):
                part_name_list.append(name)
            else:
                break
    return part_name_list


def search_bundle_file_from_ccache(part_name: str) -> str:
    if os.path.exists(COMPONENTS_PATH_DIR):
        data = IoUtil.read_json_file(COMPONENTS_PATH_DIR)
        if data.get(part_name):
            return data.get(part_name)
    return ""


def _search_bundle_path(part_name: str) -> str:
    bundle_path = None
    try:
        bundle_path = search_bundle_file_from_ccache(part_name)
        if not bundle_path:
            bundle_path = ComponentUtil.search_bundle_file(part_name)
        else:
            LogUtil.hb_info(
                "The bundle.json path of component {} is {}, if it's incorrect, please delete {} and try again. ".format(
                    part_name, bundle_path, COMPONENTS_PATH_DIR))
    except Exception as e:
        raise OHOSException('Please check the bundle.json files you updated : {}'.format(e))
    if not bundle_path:
        LogUtil.hb_info('ERROR argument "hb build <part_name>": Invalid part_name "{}". '.format(part_name))
        sys.exit(1)
    return bundle_path


def rename_file(source_file, target_file):
    try:
        os.rename(source_file, target_file)
    except FileNotFoundError as rename_error:
        LogUtil.hb_warning(rename_error)


class IndepBuildArgsResolver(ArgsResolverInterface):

    def __init__(self, args_dict: dict):
        super().__init__(args_dict)

    @staticmethod
    def resolve_target_cpu(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        build_executor = indep_build_module.hpm
        arg_value = ""
        if target_arg.arg_value:
            arg_value = target_arg.arg_value
        else:
            args_dict = Arg.read_args_file(ModuleType.ENV)
            arg_value = args_dict.get("target_cpu").get("argDefault")
        build_executor.regist_flag('cpu', arg_value)
        Arg.write_args_file("target_cpu", arg_value, ModuleType.INDEP_BUILD)

    @staticmethod
    def resolve_target_os(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        build_executor = indep_build_module.hpm
        arg_value = ""
        if target_arg.arg_value:
            arg_value = target_arg.arg_value
        else:
            args_dict = Arg.read_args_file(ModuleType.ENV)
            arg_value = args_dict.get("target_os").get("argDefault")
        build_executor.regist_flag('os', arg_value)
        Arg.write_args_file("target_os", arg_value, ModuleType.INDEP_BUILD)

    @staticmethod
    def resolve_part(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        '''
        编译部件名获取优先级： hb build 指定的部件名参数  > hb build 在部件源码仓运行时通过找到bundle.json获取到的部件名 > hb env 设置的部件名参数
        '''
        hpm_executor = indep_build_module.hpm
        indep_build_executor = indep_build_module.indep_build
        target_arg.arg_value_list = get_part_name()
        arg_value = ""

        if target_arg.arg_value_list:
            if hasattr(IndepBuildArgsResolver, "bundle_path_ccache"):
                arg_value = IndepBuildArgsResolver.bundle_path_ccache
            else:
                bundle_path_list = []
                LogUtil.hb_info("collecting bundle.json, please wait")
                for part_name in target_arg.arg_value_list:
                    bundle_path = _search_bundle_path(part_name)
                    bundle_path_list.append(bundle_path)
                LogUtil.hb_info("collect done")
                arg_value = ','.join(bundle_path_list)
                IndepBuildArgsResolver.bundle_path_ccache = arg_value
        elif ComponentUtil.is_in_component_dir(os.getcwd()):
            part_name, bundle_path = ComponentUtil.get_component(os.getcwd())
            if part_name:
                target_arg.arg_value_list = part_name
                arg_value = bundle_path
            else:
                raise OHOSException('ERROR argument "no bundle.json": Invalid directory "{}". '.format(os.getcwd()))
        else:
            args_dict = Arg.read_args_file(ModuleType.ENV)
            arg = args_dict.get("part")
            if arg.get("argDefault"):
                bundle_path = ComponentUtil.search_bundle_file(arg.get("argDefault"))
                if not bundle_path:
                    raise OHOSException('ERROR argument "hb env --part <part_name>": Invalid part_name "{}". '.format(
                        target_arg.arg_value_list))
                arg_value = bundle_path
            else:
                raise OHOSException('ERROR argument "hb build <part_name>": no part_name . ')
        hpm_executor.regist_flag('path', arg_value)
        indep_build_executor.regist_flag('path', arg_value)
        Arg.write_args_file("part", arg_value, ModuleType.INDEP_BUILD)

    @staticmethod
    def resolve_variant(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        build_executor = indep_build_module.hpm
        arg_value = ""
        if target_arg.arg_value:
            build_executor.regist_flag('defaultDeps', ComponentUtil.get_default_deps(target_arg.arg_value,
                                                                                     True if '-t' in sys.argv else False))
            arg_value = target_arg.arg_value
        else:
            build_executor.regist_flag('defaultDeps', ComponentUtil.get_default_deps("argDefault"))
            args_dict = Arg.read_args_file(ModuleType.ENV)
            arg_value = args_dict.get("variant").get("argDefault")

        build_executor.regist_flag('variant', arg_value)
        indep_build_module.indep_build.regist_flag('variant', arg_value)
        Arg.write_args_file("variant", arg_value, ModuleType.INDEP_BUILD)

    @staticmethod
    def resolve_branch(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        build_executor = indep_build_module.hpm
        arg_value = ""
        if target_arg.arg_value:
            arg_value = target_arg.arg_value
        else:
            args_dict = Arg.read_args_file(ModuleType.ENV)
            arg_value = args_dict.get("branch").get("argDefault")
        build_executor.regist_flag('branch', arg_value)
        Arg.write_args_file("branch", arg_value, ModuleType.INDEP_BUILD)

    @staticmethod
    def resolve_build_type(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        arg_value = ""
        if (sys.argv[1] == 'build' and
                '-i' in sys.argv[3:] and
                {'-t', '-test'} & set(sys.argv[3:])):
            arg_value = "both"
        elif (sys.argv[1] == 'build' and
              '-i' not in sys.argv[3:] and
              (sys.argv[-1] == "-t" or ("-t" in sys.argv and sys.argv[sys.argv.index("-t") + 1][0] == '-'))):
            arg_value = "onlytest"
        else:
            arg_value = "onlysrc"
            indep_build_module.indep_build.regist_flag("buildType", "onlysrc")
        if arg_value != "onlysrc":
            indep_build_module.hpm.regist_flag("buildType", arg_value)
        indep_build_module.indep_build.regist_flag("buildType", arg_value)
        Arg.write_args_file("build_type", arg_value, ModuleType.INDEP_BUILD)

    @staticmethod
    def resolve_keep_ninja_going(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        indep_build_module.indep_build.regist_flag('keep-ninja-going', target_arg.arg_value)

    @staticmethod
    def resolve_gn_args(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        indep_build_module.indep_build.regist_flag('gn-args', target_arg.arg_value)
    
    @staticmethod
    def resolve_gn_flags(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        indep_build_module.indep_build.regist_flag('gn-flags', target_arg.arg_value)

    @staticmethod
    def resolve_ninja_args(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        indep_build_module.indep_build.regist_flag('ninja-args', target_arg.arg_value)
    
    @staticmethod
    def resolve_skip_download(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        indep_build_module.hpm.regist_flag('skip-download', target_arg.arg_value)
        indep_build_module.indep_build.regist_flag('skip-download', target_arg.arg_value)

    @staticmethod
    def resolve_build_target(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        if "--build-target" in sys.argv and not target_arg.arg_value:
            raise OHOSException("ERROR argument \"--build-target\": no build target. ")
        indep_build_module.indep_build.regist_flag('build-target', target_arg.arg_value)

    @staticmethod
    def resolve_fast_rebuild(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        indep_build_module.indep_build.regist_flag('fast-rebuild', target_arg.arg_value)
        indep_build_module.hpm.regist_flag('fast-rebuild', target_arg.arg_value)

    @staticmethod
    def resolve_ccache(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        # 检查是否启用了 ccache
        if target_arg.arg_value:
            # 查找 ccache 可执行文件的路径
            ccache_path = find_executable('ccache')
            if ccache_path is None:
                LogUtil.hb_warning('Failed to find ccache, ccache disabled.')
                return
            else:
                # 注册 ccache 启用标志
                indep_build_module.indep_build.regist_arg(
                    'ohos_build_enable_ccache', target_arg.arg_value)

            # 设置缓存目录
            ccache_local_dir = os.environ.get('CCACHE_LOCAL_DIR')
            ccache_base = os.environ.get('CCACHE_BASE')
            if not ccache_local_dir:
                ccache_local_dir = '.ccache'
            if not ccache_base:
                ccache_base = os.environ.get('HOME')
            ccache_base = os.path.join(ccache_base, ccache_local_dir)
            if not os.path.exists(ccache_base):
                os.makedirs(ccache_base, exist_ok=True)

            # 日志文件处理
            ccache_log_suffix = os.environ.get('CCACHE_LOG_SUFFIX')
            if ccache_log_suffix:
                logfile = os.path.join(
                    ccache_base, "ccache.{}.log".format(ccache_log_suffix))
            elif os.environ.get('CCACHE_LOGFILE'):
                logfile = os.environ.get('CCACHE_LOGFILE')
                if not os.path.exists(os.path.dirname(logfile)):
                    os.makedirs(os.path.dirname(logfile), exist_ok=True)
            else:
                logfile = os.path.join(ccache_base, "ccache.log")
            if os.path.exists(logfile):
                oldfile = '{}.old'.format(logfile)
                if os.path.exists(oldfile):
                    os.unlink(oldfile)
                rename_file(logfile, oldfile)
            # 获取项目根目录
            src_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            # 设置ccache相关环境变量
            os.environ['CCACHE_EXEC'] = ccache_path
            os.environ['CCACHE_LOGFILE'] = logfile
            os.environ['USE_CCACHE'] = '1'
            os.environ['CCACHE_DIR'] = ccache_base
            os.environ['CCACHE_UMASK'] = '002'
            os.environ['CCACHE_BASEDIR'] = src_root
            ccache_max_size = os.environ.get('CCACHE_MAXSIZE')
            if not ccache_max_size:
                ccache_max_size = '100G'

            # 构建设置 ccache 最大缓存大小的命令
            cmd = ['ccache', '-M', ccache_max_size]
            try:
                subprocess.check_output(cmd, text=True)
            except FileNotFoundError:
                LogUtil.hb_info("Error: ccache command not found")
            except subprocess.CalledProcessError as e:
                LogUtil.hb_info(f"Failed to execute ccache command: {e}")
    
    def resolve_prebuilts_download(self, target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        indep_build_module.prebuilts.regist_flag('skip-prebuilts', target_arg.arg_value)
    
    def resolve_local_repo(self, target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        indep_build_module.indep_build.regist_flag('local-binarys', target_arg.arg_value)
        indep_build_module.hpm.regist_flag('local-binarys', target_arg.arg_value)