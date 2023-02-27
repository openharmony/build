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


import sys
import os
from enum import Enum

from containers.status import throw_exception
from exceptions.ohos_exception import OHOSException
from services.interface.build_file_generator_interface import BuildFileGeneratorInterface
from resources.config import Config
from containers.arg import Arg, ModuleType
from util.system_util import SystemUtil
from util.io_util import IoUtil
from util.log_util import LogUtil


class CMDTYPE(Enum):
    GEN = 1
    PATH = 2
    DESC = 3
    LS = 4
    REFS = 5
    FORMAT = 6
    CLEAN = 7


class Gn(BuildFileGeneratorInterface):

    def __init__(self):
        super().__init__()
        self.config = Config()
        self._regist_gn_path()

    def run(self):
        self.execute_gn_cmd(CMDTYPE.GEN)

    @throw_exception
    def execute_gn_cmd(self, cmd_type: int, **kwargs):
        if cmd_type == CMDTYPE.GEN:
            return self._execute_gn_gen_cmd()
        elif cmd_type == CMDTYPE.PATH:
            return self._execute_gn_path_cmd(**kwargs)
        elif cmd_type == CMDTYPE.DESC:
            return self._execute_gn_desc_cmd(**kwargs)
        elif cmd_type == CMDTYPE.LS:
            return self._execute_gn_ls_cmd(**kwargs)
        elif cmd_type == CMDTYPE.REFS:
            return self._execute_gn_refs_cmd(**kwargs)
        elif cmd_type == CMDTYPE.FORMAT:
            return self._execute_gn_format_cmd(**kwargs)
        elif cmd_type == CMDTYPE.CLEAN:
            return self._execute_gn_clean_cmd(**kwargs)
        else:
            raise OHOSException(
                'You are tring to use an unsupported gn cmd type "{}"'.format(cmd_type), '3001')

    '''Description: Get gn excutable path and regist it
    @parameter: none
    @return: Status
    '''

    @throw_exception
    def _regist_gn_path(self):
        config_data = IoUtil.read_json_file(os.path.join(
            self.config.root_path, 'build/prebuilts_download_config.json'))
        copy_config_list = config_data[os.uname().sysname.lower(
        )][os.uname().machine.lower()]['copy_config']

        gn_path = ''
        for config in copy_config_list:
            if config['unzip_filename'] == 'gn':
                gn_path = os.path.join(
                    self.config.root_path, config['unzip_dir'], 'gn')
                break

        if os.path.exists(gn_path):
            self.exec = gn_path
        else:
            raise OHOSException(
                'There is no gn executable file at {}'.format(gn_path), '0001')

    '''Description: Convert all registed args into a list
    @parameter: none
    @return: list of all registed args
    '''

    def _convert_args(self) -> list:
        args_list = []

        for key, value in self.args_dict.items():
            if isinstance(value, bool):
                args_list.append('{}={}'.format(key, str(value).lower()))

            elif isinstance(value, str):
                args_list.append('{}="{}"'.format(key, value))

            elif isinstance(value, int):
                args_list.append('{}={}'.format(key, value))

            elif isinstance(value, list):
                args_list.append('{}="{}"'.format(key, "&&".join(value)))

        return args_list

    '''Description: Convert all registed flags into a list
    @parameter: none
    @return: list of all registed flags
    '''

    def _convert_flags(self) -> list:
        flags_list = []

        for key, value in self.flags_dict.items():
            if value == '':
                flags_list.append('{}'.format(key))
            else:
                flags_list.append('{}={}'.format(key, str(value)).lower())

        return flags_list

    '''Description: Option validity check
    @parameter: "option": Option to be checked
                "args_file": Option config file
    @return: Inspection result(True|False)
    '''

    def _check_options_validity(self, option: str, args_file: dict):
        support_sub_options = args_file.get(
            "arg_attribute").get("support_sub_options")
        option_name = option.lstrip('-')
        option_value = ""
        if '=' in option:
            option_name, option_value = option.lstrip('-').split('=')
        if option_name in support_sub_options:
            sub_optional_list = support_sub_options.get(
                option_name).get("arg_attribute").get("optional")
            if sub_optional_list and option_value not in sub_optional_list:
                if not len(option_value):
                    raise OHOSException('ERROR argument "--{}": Invalid choice "{}". '
                                        'choose from {}'.format(option_name, option_value, sub_optional_list), '3006')
                else:
                    raise OHOSException('ERROR argument "--{}": Invalid choice "{}". '
                                        'choose from {}'.format(option_name, option_value, sub_optional_list), '3003')
        else:
            raise OHOSException('ERROR argument "{}": Invalid choice "{}". '
                                'choose from {}'.format(args_file.get("arg_name"),
                                                        option, list(support_sub_options.keys())), '3003')

    '''Description: Execute 'gn gen' command using registed args
    @parameter: kwargs TBD
    @return: None
    '''

    @throw_exception
    def _execute_gn_gen_cmd(self, **kwargs):
        gn_gen_cmd = [self.exec, 'gen',
                      '--args={}'.format(' '.join(self._convert_args())),
                      self.config.out_path] + self._convert_flags()
        if self.config.os_level == 'mini' or self.config.os_level == 'small':
            gn_gen_cmd.append(f'--script-executable={sys.executable}')
        try:
            LogUtil.write_log(self.config.log_path, 'Excuting gn command: {} {} --args="{}" {}'.format(
                self.exec, 'gen',
                ' '.join(self._convert_args()).replace('"', "\\\""),
                ' '.join(gn_gen_cmd[3:])),
                'info')
            SystemUtil.exec_command(gn_gen_cmd, self.config.log_path)
        except OHOSException:
            raise OHOSException('GN phase failed', '3000')

    '''Description: Execute 'gn path' command using registed args
    @parameter: kwargs TBD
    @return: None
    '''

    @throw_exception
    def _execute_gn_path_cmd(self, **kwargs):
        out_dir = kwargs.get("out_dir")
        default_options = ['--all']
        args_file = Arg.read_args_file(ModuleType.TOOL)['path']
        if (os.path.exists(os.path.join(out_dir, "args.gn"))):
            gn_path_cmd = [self.exec, 'path', out_dir]
            for arg in kwargs.get('args_list'):
                if arg.startswith('-'):
                    self._check_options_validity(arg, args_file)
                gn_path_cmd.append(arg)
            gn_path_cmd.extend(default_options)
            sort_index = gn_path_cmd.index
            gn_path_cmd = list(set(gn_path_cmd))
            gn_path_cmd.sort(key=sort_index)
            SystemUtil.exec_command(gn_path_cmd)
        else:
            raise OHOSException(
                '"{}" Not a build directory.'.format(out_dir), '3004')

    '''Description: Execute 'gn desc' command using registed args
    @parameter: kwargs TBD
    @return: None
    '''

    @throw_exception
    def _execute_gn_desc_cmd(self, **kwargs):
        out_dir = kwargs.get("out_dir")
        default_options = ['--tree', '--blame']
        args_file = Arg.read_args_file(ModuleType.TOOL)['desc']
        if (os.path.exists(os.path.join(out_dir, "args.gn"))):
            gn_desc_cmd = [self.exec, 'desc', out_dir]
            for arg in kwargs.get('args_list'):
                if arg.startswith('-'):
                    self._check_options_validity(arg, args_file)
                gn_desc_cmd.append(arg)
            gn_desc_cmd.extend(default_options)
            sort_index = gn_desc_cmd.index
            gn_desc_cmd = list(set(gn_desc_cmd))
            gn_desc_cmd.sort(key=sort_index)
            SystemUtil.exec_command(gn_desc_cmd)
        else:
            raise OHOSException(
                '"{}" Not a build directory.'.format(out_dir), '3004')

    '''Description: Execute 'gn ls' command using registed args
    @parameter: kwargs TBD
    @return: None
    '''

    @throw_exception
    def _execute_gn_ls_cmd(self, **kwargs):
        out_dir = kwargs.get("out_dir")
        args_file = Arg.read_args_file(ModuleType.TOOL)['ls']
        if (os.path.exists(os.path.join(out_dir, "args.gn"))):
            gn_ls_cmd = [self.exec, 'ls', out_dir]
            for arg in kwargs.get('args_list'):
                if arg.startswith('-'):
                    self._check_options_validity(arg, args_file)
                gn_ls_cmd.append(arg)
            SystemUtil.exec_command(gn_ls_cmd)
        else:
            raise OHOSException(
                '"{}" Not a build directory.'.format(out_dir), '3004')

    '''Description: Execute 'gn refs' command using registed args
    @parameter: kwargs TBD
    @return: None
    '''

    @throw_exception
    def _execute_gn_refs_cmd(self, **kwargs):
        out_dir = kwargs.get("out_dir")
        args_file = Arg.read_args_file(ModuleType.TOOL)['refs']
        if (os.path.exists(os.path.join(out_dir, "args.gn"))):
            gn_refs_cmd = [self.exec, 'refs', out_dir]
            for arg in kwargs.get('args_list'):
                if arg.startswith('-'):
                    self._check_options_validity(arg, args_file)
                gn_refs_cmd.append(arg)
            SystemUtil.exec_command(gn_refs_cmd)
        else:
            raise OHOSException(
                '"{}" Not a build directory.'.format(out_dir), '3004')

    '''Description: Execute 'gn format' command using registed args
    @parameter: kwargs TBD
    @return: None
    '''

    @throw_exception
    def _execute_gn_format_cmd(self, **kwargs):
        gn_format_cmd = [self.exec, 'format']
        args_file = Arg.read_args_file(ModuleType.TOOL)['format']
        for arg in kwargs.get("args_list"):
            if (arg.endswith('.gn')):
                if (os.path.exists(arg)):
                    gn_format_cmd.append(arg)
                else:
                    raise OHOSException(
                        "ERROR Couldn't read '{}'".format(arg), '3005')
            else:
                if arg.startswith('-'):
                    self._check_options_validity(arg, args_file)
                gn_format_cmd.append(arg)
        SystemUtil.exec_command(gn_format_cmd)

    '''Description: Execute 'gn clean' command using registed args
    @parameter: kwargs TBD
    @return: None
    '''

    @throw_exception
    def _execute_gn_clean_cmd(self, **kwargs):
        out_dir = kwargs.get("out_dir")
        if (os.path.exists(os.path.join(out_dir, "args.gn"))):
            gn_clean_cmd = [self.exec, 'clean', out_dir]
            SystemUtil.exec_command(gn_clean_cmd)
        else:
            raise OHOSException('"{}" Not a build directory.'
                                'Usage: "gn clean <out_dir>"'.format(out_dir), '3004')
