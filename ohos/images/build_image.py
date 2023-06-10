#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 Huawei Device Co., Ltd.
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

import sys
import os
import shutil
import argparse
import json
from mkimage import mkimages

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from scripts.util import build_utils  # noqa: E402


def _prepare_userdata(userdata_path):
    if os.path.exists(userdata_path):
        shutil.rmtree(userdata_path)
    os.makedirs(userdata_path)


def _prepare_root(system_path, target_cpu):
    root_dir = os.path.join(os.path.dirname(system_path), 'root')
    if os.path.exists(root_dir):
        shutil.rmtree(root_dir)
    os.makedirs(root_dir, exist_ok=True)
    _dir_list = [
        'config', 'dev', 'proc', 'sys', 'updater', 'system', 'vendor', 'data',
        'storage', 'mnt', 'tmp', 'sys_prod', 'chip_prod', 'module_update', 'eng_system', 'eng_chipset'
    ]
    for _dir_name in _dir_list:
        os.makedirs(os.path.join(root_dir, _dir_name), exist_ok=True)
    os.symlink('/system/bin', os.path.join(root_dir, 'bin'))
    os.symlink('/system/bin/init', os.path.join(root_dir, 'init'))
    os.symlink('/system/etc', os.path.join(root_dir, 'etc'))
    os.symlink('/vendor', os.path.join(root_dir, 'chipset'))
    if target_cpu == 'arm64':
        os.symlink('/system/lib64', os.path.join(root_dir, 'lib64'))
    os.symlink('/system/lib', os.path.join(root_dir, 'lib'))


def _prepare_updater(updater_path):
    _dir_list = ['dev', 'proc', 'sys', 'system', 'tmp', 'lib', 'lib64', 'vendor']
    for _dir_name in _dir_list:
        _path = os.path.join(updater_path, _dir_name)
        if os.path.exists(_path):
            continue
        os.makedirs(_path, exist_ok=True)
    os.symlink('bin/init', os.path.join(updater_path, 'init'))
    os.symlink('/bin', os.path.join(updater_path, 'system/bin'))
    os.symlink('/lib', os.path.join(updater_path, 'system/lib'))
    os.symlink('/lib64', os.path.join(updater_path, 'system/lib64'))
    os.symlink('/lib64', os.path.join(updater_path, 'vendor/lib64'))
    os.symlink('/etc', os.path.join(updater_path, 'system/etc'))


def _prepare_ramdisk(ramdisk_path):
    _dir_list = ['bin', 'dev', 'etc', 'lib', 'proc', 'sys', 'system', 'usr', 'mnt', 'storage']
    for _dir_name in _dir_list:
        _path = os.path.join(ramdisk_path, _dir_name)
        if os.path.exists(_path):
            continue
        os.makedirs(_path, exist_ok=True)
    os.symlink('bin/init', os.path.join(ramdisk_path, 'init'))


def _prepare_eng_ststem(eng_system_path, build_variant):
    if os.path.exists(eng_system_path):
        shutil.rmtree(eng_system_path)
    os.makedirs(eng_system_path)
    if build_variant == "user":
        return 
    _dir_list_first = ['etc', 'bin']
    for _dir_name in _dir_list_first:
        _path = os.path.join(eng_system_path, _dir_name)
        if os.path.exists(_path):
            shutil.rmtree(_path)
        os.makedirs(_path, exist_ok=True)
    _dir_list_second = ['param', 'init', 'selinux']
    for _dir_name in _dir_list_second:
        _path = os.path.join(eng_system_path, 'etc', _dir_name)
        if os.path.exists(_path):
            shutil.rmtree(_path)
        os.makedirs(_path, exist_ok=True)
    _target_policy_path = os.path.join(eng_system_path, 'etc', 'selinux', 'targeted', 'policy')
    if os.path.exists(_target_policy_path):
        shutil.rmtree(_target_policy_path)
    os.makedirs(_target_policy_path, exist_ok=True)

    copy_eng_system_config = '../../build/ohos/images/mkimage/root_image.json'
    with open(copy_eng_system_config, 'rb') as input_f:
        default_build_args = json.load(input_f)
    for arg in default_build_args.values():
        sources_file = arg.get('source_file')
        dest_file = arg.get('dest_file')
        if(os.path.exists(dest_file)):
            os.remove(dest_file)
        shutil.copy(sources_file, dest_file)


def _make_image(args):
    if args.image_name == 'system':
        _prepare_root(args.input_path, args.target_cpu)
    elif args.image_name == 'updater':
        _prepare_updater(args.input_path)
    elif args.image_name == 'updater_ramdisk':
        _prepare_updater(args.input_path)
    elif args.image_name == 'ramdisk':
        _prepare_ramdisk(args.input_path)
    image_type = "raw"
    if args.sparse_image:
        image_type = "sparse"
    config_file = args.image_config_file
    if (os.path.exists(args.device_image_config_file)):
        config_file = args.device_image_config_file
    mk_image_args = [
        args.input_path, config_file, args.output_image_path,
        image_type
    ]
    if args.build_image_tools_path:
        env_path = ':'.join(args.build_image_tools_path)
        os.environ['PATH'] = '{}:{}'.format(env_path, os.environ.get('PATH'))
    mkimages.mk_images(mk_image_args)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--depfile', required=True)
    parser.add_argument('--image-name', required=True)
    parser.add_argument('--build-variant', required=True)
    parser.add_argument('--image-config-file', required=True)
    parser.add_argument('--device-image-config-file', required=True)
    parser.add_argument('--input-path', required=True)
    parser.add_argument('--output-image-path', required=True)
    parser.add_argument('--sparse-image',
                        dest="sparse_image",
                        action='store_true')
    parser.set_defaults(sparse_image=False)
    parser.add_argument('--build-image-tools-path', nargs='*', required=False)
    parser.add_argument('--target-cpu', required=False)
    args = parser.parse_args(argv)

    if os.path.exists(args.output_image_path):
        os.remove(args.output_image_path)
    if args.image_name == 'userdata':
        _prepare_userdata(args.input_path)
    elif args.image_name == 'eng_system':
        _prepare_eng_ststem(args.input_path, args.build_variant)
    if os.path.isdir(args.input_path):
        _make_image(args)
        _dep_files = []
        for _root, _, _files in os.walk(args.input_path):
            for _file in _files:
                _dep_files.append(os.path.join(_root, _file))
        if (os.path.exists(args.device_image_config_file)):
            _dep_files.append(args.device_image_config_file)
        build_utils.write_depfile(args.depfile,
                                  args.output_image_path,
                                  _dep_files,
                                  add_pydeps=False)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
