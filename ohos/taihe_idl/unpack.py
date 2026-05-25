#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2026 Huawei Device Co., Ltd.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import os
import subprocess
import tarfile
import zipfile

def unpack(src, dst):
    os.makedirs(dst, exist_ok=True)
    
    if src.endswith(('.tar.gz', '.tgz')):
        with tarfile.open(src, 'r:gz') as tf:
            tf.extractall(dst)
    elif src.endswith('.tar.bz2'):
        with tarfile.open(src, 'r:bz2') as tf:
            tf.extractall(dst)
    elif src.endswith('.tar.xz'):
        with tarfile.open(src, 'r:xz') as tf:
            tf.extractall(dst)
    elif src.endswith('.tar'):
        with tarfile.open(src, 'r') as tf:
            tf.extractall(dst)
    elif src.endswith('.zip'):
        with zipfile.ZipFile(src, 'r') as zf:
            zf.extractall(dst)
    else:
        subprocess.run(['tar', '-xf', src, '-C', dst], check=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--src', required=True)
    parser.add_argument('--dst', required=True)
    args = parser.parse_args()
    
    unpack(args.src, args.dst)


if __name__ == '__main__':
    main()