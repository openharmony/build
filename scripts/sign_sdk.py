#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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


import subprocess
import argparse
import os
import sys
import shlex


def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('--sdk-out-dir')
    parser.add_argument('--sign-no-s3', default=False)
    options = parser.parse_args(args)
    return options


def sign_sdk(zipfile, sign_list, sign_results):
    if zipfile.endswith('.zip'):
        sign = os.getenv('SIGN')
        if not sign:
            raise AttributeError(f"SIGN message not in env")
        dir_name = zipfile.split('-')[0]
        cmd1 = ['unzip', "-q", zipfile]
        subprocess.call(cmd1)
        need_sign_files = []
        for root, dirs, files in os.walk(dir_name):
            for file in files:
                file = os.path.join(root, file)
                need_sign_files.append(file)
        
        for file in need_sign_files:
            if file.split('/')[-1] in sign_list or file.endswith('.so') or file.endswith('.dylib') \
                    or file.split('/')[-2] == 'bin':
                cmd2 = ['codesign', '--sign', sign, '--timestamp', '--options=runtime', file]
                subprocess.call(cmd2)
        cmd3 = ['rm', zipfile]
        subprocess.call(cmd3)
        cmd4 = ['zip', '-rq', zipfile, dir_name]
        subprocess.call(cmd4)
        cmd5 = ['rm', '-rf', dir_name]
        subprocess.call(cmd5)
        ohos_name = shlex.quote("ohos-sdk")
        if sign_no_s3 is True:
            cmd6 = ['xcrun', 'notarytool', 'submit', zipfile, '--keychain-profile', ohos_name, '--no-s3-acceleration']
        else
            cmd6 = ['xcrun', 'notarytool', 'submit', zipfile, '--keychain-profile', ohos_name]

        process = subprocess.Popen(cmd6, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        sign_results.append((cmd6, process))


def main(args):
    options = parse_args(args)
    darwin_sdk_dir = os.path.join(options.sdk_out_dir, 'darwin')
    global sign_no_s3
    sign_no_s3 = options.sign_no_s3
    os.chdir(darwin_sdk_dir)
    sign_list = ['lldb-argdumper', 'fsevents.node', 'idl', 'restool', 'diff', 'ark_asm', 'ark_disasm', 'hdc', 'syscap_tool']
    sign_results = []
    for file in os.listdir('.'):
        sign_sdk(file, sign_list, sign_results)
    for cmd, process in sign_results:
        try:
            stdout, stderr = process.communicate(timeout=1200)
            if process.returncode:
                print(f"cmd:{' '.join(cmd)}, result is {stdout}")       
                raise Exception(f"run command {' '.join(cmd)} fail, error is {stderr}")
        except Exception as e:
            raise TimeoutError(r"run xcrun cmd timeout")


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
