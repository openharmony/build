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
import subprocess
import argparse
import shlex
from tempfile import NamedTemporaryFile
from shutil import copyfile
from datetime import datetime


def cmd_exec(command: str, temp_file: str, error_log_path: str):
    start_time = datetime.now().replace(microsecond=0)
    cmd = shlex.split(command)

    proc = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            encoding='utf-8')

    out, err = proc.communicate(timeout=500)
    ret_code = proc.returncode
    if ret_code != 0:
        temp_file.close()
        copyfile(temp_file.name, error_log_path)
        os.remove(temp_file.name)
        raise Exception("out: {} err: {}".format(out, err))

    end_time = datetime.now().replace(microsecond=0)
    temp_file.write(f'cmd:{command}\ncost time:{end_time-start_time}\n')
    return ret_code


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', help='Build path.')
    parser.add_argument('--prebuilts', help='Build prebuilts.')
    parser.add_argument('--command', help='Build command.')
    parser.add_argument('--enable', help='enable python.', nargs='*')
    parser.add_argument('--target_dir', nargs=1)
    parser.add_argument('--out_dir', nargs=1)
    args = parser.parse_args()

    if args.enable:
        if args.enable[0] == 'false':
            return 0

    if args.path:
        curr_dir = os.getcwd()
        os.chdir(args.path)
        temp_file = NamedTemporaryFile(mode='wt', delete=False)
        if args.prebuilts:
            status = cmd_exec(args.prebuilts, temp_file, args.out_dir[0])
            if status != 0:
                return status
        if args.command:
            if '&&' in args.command:
                command = args.command.split('&&')
                for data in command:
                    status = cmd_exec(data, temp_file, args.out_dir[0])
                    if status != 0:
                        return status
            else:
                status = cmd_exec(args.command, temp_file, args.out_dir[0])
                if status != 0:
                    return status
        temp_file.close()
        copyfile(temp_file.name, args.target_dir[0])
        os.remove(temp_file.name)

        os.chdir(curr_dir)
    return 0


if __name__ == '__main__':
    sys.exit(main())
