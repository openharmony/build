#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Huawei Device Co., Ltd.
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

import os
import argparse
import ssl
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "prebuilts_service"))
from prebuilts_service.operater import OperateHanlder
from prebuilts_service.pool_downloader import PoolDownloader
from prebuilts_service.config_parser import ConfigParser
import json
from prebuilts_service.common_utils import get_code_dir

global_args = None


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip-ssl', action='store_true', help='skip ssl authentication')
    parser.add_argument('--unsafe-perm', action='store_true', help='add "--unsafe-perm" for npm install')
    parser.add_argument('--disable-rich', action='store_true', help='disable the rich module')
    parser.add_argument('--enable-symlink', action='store_true', help='enable symlink while copying node_modules')
    parser.add_argument('--build-arkuix', action='store_true', help='build ArkUI-X SDK')
    parser.add_argument('--tool-repo', default='https://repo.huaweicloud.com', help='prebuilt file download source')
    parser.add_argument('--npm-registry', default='https://repo.huaweicloud.com/repository/npm/',
                        help='npm download source')
    parser.add_argument('--host-cpu', help='host cpu', required=True)
    parser.add_argument('--host-platform', help='host platform', required=True)
    parser.add_argument('--glibc-version', help='glibc version', required=False)
    parser.add_argument('--config-file', help='prebuilts download config file')
    parser.add_argument('--build-type', help='compilation type', default="indep")
    parser.add_argument('--part-names', help='current building part', default=None, nargs='+')

    return parser


def main():
    parser = _parse_args()
    global global_args
    global_args = parser.parse_args()

    if global_args.skip_ssl:
        global_args._create_default_https_context = ssl._create_unverified_context
    global_args.code_dir = get_code_dir()

    config_file = os.path.join(global_args.code_dir, "build", "prebuilts_config.json")
    if global_args.config_file:
        config_file = global_args.config_file
    print(f"start parse config file {config_file}")
    config_parser = ConfigParser(config_file, global_args)
    download_operate, other_operate = config_parser.get_operate(global_args.part_names)
    prebuilts_path = os.path.join(global_args.code_dir, "prebuilts")
    if not os.path.exists(prebuilts_path):
        os.makedirs(prebuilts_path)

    # 使用线程池下载
    print(f"start download prebuilts, total {len(download_operate)}, tool list is:")
    for item in download_operate:
        print(item.get("remote_url"))
    pool_downloader = PoolDownloader(download_operate, global_args)
    unchanged = pool_downloader.start()
    print(f"start handle other operate")
    OperateHanlder.run(other_operate, global_args, unchanged)


if __name__ == "__main__":
    sys.exit(main())