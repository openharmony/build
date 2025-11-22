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
    options = parser.parse_args(args)
    return options


def sign_sdk(zipfile, sign_list, sign_results, ohos_sdk_dir):
    out_path = os.path.dirname(os.path.dirname(os.path.dirname(ohos_sdk_dir)))
    packing_tool_dir_re = os.path.join(out_path, 'ohos-sdk', 'linux', 'toolchains', 'lib')
    packing_tool_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), packing_tool_dir_re)
    cert_file_dir_re = os.path.join(out_path, 'ohos-sdk', 'ohos', 'toolchains', 'lib')
    cert_file_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), cert_file_dir_re)
    packing_tool = os.path.abspath(os.path.join(packing_tool_dir, 'binary-sign-tool'))
    
    sign = f"openharmony application release"
    cert_file = os.path.abspath(os.path.join(cert_file_dir, 'OpenHarmonyApplication.pem'))
    key_store_file = os.path.abspath(os.path.join(cert_file_dir, 'OpenHarmony.p12'))
    pwd = '123456'
    if zipfile.endswith('.zip'):

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
                    or file.split('/')[-2] == 'bin' and not file.endswith('.js'):
                cmd2 = [packing_tool, 
                        'sign', 
                        '-keyAlias', sign,  
                        '-signAlg', 'SHA256withECDSA', 
                        '-keystoreFile', key_store_file,
                        '-inFile', file, 
                        '-outFile', file,
                        '-keyPwd', "123456",
                        '-appCertFile', cert_file, 
                        '-keystorePwd',
                        '123456','-profileSigned', '1']
                print(cmd2)
                subprocess.call(cmd2)
        print("cmd2 end")
        cmd3 = ['rm', zipfile]
        subprocess.call(cmd3)
        cmd4 = ['zip', '-rq', zipfile, dir_name]
        subprocess.call(cmd4)
        cmd5 = ['rm', '-rf', dir_name]
        subprocess.call(cmd5)


def main(args):
    options = parse_args(args)
    ohos_sdk_dir = os.path.join(options.sdk_out_dir, 'ohos')
    
    
    os.chdir(ohos_sdk_dir)
    sign_list = ['lldb-argdumper', 'fsevents.node', 'idl', 'restool', 'diff', 'ark_asm',
                 'ark_disasm', 'hdc', 'syscap_tool', 'hnpcli', 'rawheap_translator']
    sign_results = []
    for file in os.listdir('.'):
        sign_sdk(file, sign_list, sign_results, ohos_sdk_dir)
    for cmd, process in sign_results:
        try:
            stdout, stderr = process.communicate(timeout=3600)
            if process.returncode:
                print(f"cmd:{' '.join(cmd)}, result is {stdout}")       
                raise Exception(f"run command {' '.join(cmd)} fail, error is {stderr}")
        except Exception as e:
            raise TimeoutError(r"sign timeout")


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

