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

from util import build_utils
from util import file_utils


def parse_args(args):
    parser = argparse.ArgumentParser()
    build_utils.add_depfile_option(parser)

    parser.add_argument('--keyPwd', help='')
    parser.add_argument('--sign-algo', help='')
    parser.add_argument('--keyalias', help='')
    parser.add_argument('--keystoreFile', help='')
    parser.add_argument('--keystorePwd', help='')
    parser.add_argument('--profileFile', help='')
    parser.add_argument('--hapsigner', help='')
    parser.add_argument('--unsigned-hap-path-list', help='')
    parser.add_argument('--compatible_version', help='compatible_version')
    parser.add_argument('--hap-out-dir', help='')
    parser.add_argument('--inFile', help='')
    parser.add_argument('--outFile', help='')
    parser.add_argument('--profileSigned', help='')
    parser.add_argument('--inForm', help='')
    parser.add_argument('--certificate-file', help='')
    options = parser.parse_args(args)
    return options


def sign_app(options, unsigned_hap_path, signed_hap_path):
    cmd = ['java', '-jar', options.hapsigner, 'sign-app']
    cmd.extend(['-mode', 'localsign'])
    cmd.extend(['-signAlg', options.sign_algo])
    cmd.extend(['-keyAlias', options.keyalias])
    cmd.extend(['-inFile', unsigned_hap_path])
    cmd.extend(['-outFile', signed_hap_path])
    cmd.extend(['-profileFile', options.profileFile])
    cmd.extend(['-keystoreFile', options.keystoreFile])
    cmd.extend(['-keystorePwd', options.keystorePwd])
    cmd.extend(['-keyPwd', options.keyPwd])
    cmd.extend(['-appCertFile', options.certificate_file])
    cmd.extend(['-profileSigned', (options.profileSigned or '1')])
    cmd.extend(['-inForm', (options.inForm or 'zip')])
    child = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    stdout, stderr = child.communicate()
    if child.returncode:
        print(stdout.decode(), stderr.decode())
        raise Exception("Failed to sign hap")


def main(args):
    options = parse_args(args)
    if not options.hap_out_dir:
        sign_app(options, options.inFile, options.outFile)
    else:
        if not os.path.exists(options.hap_out_dir):
            os.makedirs(options.hap_out_dir, exist_ok=True)
        unsigned_hap_path_list = file_utils.read_json_file(options.unsigned_hap_path_list)
        for unsigned_hap_path in unsigned_hap_path_list.get('unsigned_hap_path_list'):
            signed_hap_path = unsigned_hap_path.replace('unsigned.hap', 'signed.hap')
            signed_hap_path = os.path.basename(signed_hap_path)
            signed_hap_path = os.path.join(options.hap_out_dir, signed_hap_path)
            sign_app(options, unsigned_hap_path, signed_hap_path)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
