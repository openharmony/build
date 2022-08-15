#!/usr/bin/env python
# coding: utf-8
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
import configparser
import json
import os
import shutil
import sys
import argparse
import subprocess
import filecmp


def args_parse(args):
    parser = argparse.ArgumentParser(description='mkcpioimage.py')

    parser.add_argument("src_dir", help="The source file for sload.")
    parser.add_argument("device", help="The device for mkfs.")
    parser.add_argument("conf_size", help="The deivce config image size.")

    args = parser.parse_known_args(args)[0]
    return args


def run_cmd(cmd, dir_list=None):
    res = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                           stdin=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    if dir_list is not None:
        for each_path in dir_list:
            print("mkcpio image, cpio stdin: ", each_path)
            res.stdin.write(("%s\n" % each_path).encode('utf-8'))
    sout, serr = res.communicate()
    res.wait()
    return res.pid, res.returncode, sout, serr


def get_dir_list(input_path, dir_list):
    if os.path.isdir(input_path) and not os.path.islink(input_path):
        dir_list.append(input_path)
        tem_list = os.listdir(input_path)
        for each in tem_list:
            each_path = os.path.join(input_path, each)
            get_dir_list(each_path, dir_list)
    else:
        dir_list.append(input_path)


def build_run_cpio(args):
    work_dir = os.getcwd()
    os.chdir(args.src_dir)

    conf_size = int(args.conf_size)
    if args.device == "ramdisk.img":
        output_path = os.path.join("%s/../images" % os.getcwd(), args.device)
    elif args.device == "updater_ramdisk.img":
        output_path = os.path.join("%s/../images" % os.getcwd(), "updater.img")
    else:
        output_path = os.path.join(work_dir, args.device)
    ramdisk_cmd = ['cpio', '-o', '-H', 'newc', '-O', output_path]
    dir_list = []
    get_dir_list("./", dir_list)
    res = run_cmd(ramdisk_cmd, dir_list)
    os.chdir(work_dir)
    if conf_size < os.path.getsize(output_path):
        print("Image size is larger than the conf image size. "
              "conf_size: %d, image_size: %d" %
              (conf_size, os.path.getsize(output_path)))
        sys.exit(1)
    if res[1] != 0:
        print("error run cpio ramdisk errno: %s" % str(res))
        print(" ".join(["pid ", str(res[0]), " ret ", str(res[1]), "\n",
                        res[2].decode(), res[3].decode()]))
        clear_resource_file(need_clear_section_target_path_list)
        sys.exit(1)
    return


def build_run_chmod(args):
    src_dir = args.src_dir
    src_index = src_dir.rfind('/')
    root_dir = src_dir[:src_index]

    if "updater_ramdisk.img" in args.device:
        chmod_cmd = ['chmod', '664', os.path.join(root_dir, "images", "updater.img")]
    else:
        chmod_cmd = ['chmod', '664', os.path.join(root_dir, "images", "ramdisk.img")]
    res = run_cmd(chmod_cmd)
    if res[1] != 0:
        print("error run chmod errno: %s" % str(res))
        print(" ".join(["pid ", str(res[0]), " ret ", str(res[1]), "\n",
                        res[2].decode(), res[3].decode()]))
        clear_resource_file(need_clear_section_target_path_list)
        sys.exit(3)
    return res[1]


def main(args):
    args = args_parse(args)
    print("Make cpio image!")
    config = {}
    with open("../../ohos_config.json") as f:
        config = json.load(f)
    build_run_cpio(args)
    build_run_chmod(args)



if __name__ == '__main__':
    main(sys.argv[1:])
