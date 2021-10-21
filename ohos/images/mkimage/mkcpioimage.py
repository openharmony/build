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

import os
import shutil
import sys
import stat
import argparse
import subprocess


def args_parse(args):
    parser = argparse.ArgumentParser(description='mkcpioimage.py')

    parser.add_argument("src_dir", help="The source file for sload.")
    parser.add_argument("device", help="The deivce for mkfs.")

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
    if os.path.isdir(input_path):
        dir_list.append(input_path)
        tem_list = os.listdir(input_path)
        for each in tem_list:
            each_path = os.path.join(input_path, each)
            get_dir_list(each_path, dir_list)
    else:
        dir_list.append(input_path)


def build_run_fitimage(args):
    src_dir = args.src_dir
    index = src_dir.rfind('/')
    root_dir = src_dir[:index]

    if not os.path.exists(os.path.join(root_dir, "images", "ohos.its")):
        print("error there is no configuration file")
        return -1
    if not os.path.exists(os.path.join(root_dir, "images", "zImage-dtb")):
        print("error there is no kernel image")
        return -1

    dtc_419_src_path = \
        "../../out/KERNEL_OBJ/kernel/src_tmp/linux-4.19/scripts/dtc/dtc"
    dtc_510_src_path = \
        "../../out/KERNEL_OBJ/kernel/OBJ/linux-5.10/scripts/dtc/dtc"
    dtc_dst_path = "../../third_party/e2fsprogs/prebuilt/host/bin/dtc"
    if os.path.exists(dtc_510_src_path):
        shutil.copy(dtc_510_src_path, dtc_dst_path)
    elif os.path.exists(dtc_419_src_path):
        shutil.copy(dtc_419_src_path, dtc_dst_path)
    else:
        print("error device tree compiler not found")

    mkimage_path = "../../device/hisilicon/hispark_taurus/prebuilts/mkimage"
    fit_cmd = \
        [mkimage_path, '-f', os.path.join(root_dir, "images", "ohos.its"),
        os.path.join(root_dir, "images", "boot.img")]

    res = run_cmd(fit_cmd)
    if os.path.exists(dtc_dst_path):
        os.remove(dtc_dst_path)
    if res[1] != 0:
        print(" ".join(["pid ", str(res[0]), " ret ", str(res[1]), "\n",
                        res[2].decode(), res[3].decode()]))

    return res[1]


def build_run_cpio(args):
    work_dir = os.getcwd()
    os.chdir(args.src_dir)

    output_path = os.path.join(work_dir, args.device)
    ramdisk_cmd = ['cpio', '-o', '-H', 'newc', '-O', output_path]
    dir_list = []
    get_dir_list("./", dir_list)
    res = run_cmd(ramdisk_cmd, dir_list)
    if res[1] != 0:
        print(" ".join(["pid ", str(res[0]), " ret ", str(res[1]), "\n",
                        res[2].decode(), res[3].decode()]))
    os.chdir(work_dir)
    return res[1]

def build_run_chmod(args):
    src_dir = args.src_dir
    src_index = src_dir.rfind('/')
    root_dir = src_dir[:src_index]

    chmod_cmd = ['chmod', '664', os.path.join(root_dir, "images", "boot.img")]
    res = run_cmd(chmod_cmd)
    if res[1] != 0:
        print(" ".join(["pid ", str(res[0]), " ret ", str(res[1]), "\n",
                        res[2].decode(), res[3].decode()]))
    return res[1]

def main(args):
    args = args_parse(args)
    print("Make cpio image!")

    res = build_run_cpio(args)
    if res != 0:
        print("error run cpio ramdisk errno: %s" % str(res))
        sys.exit(1)
    res = build_run_fitimage(args)
    if res != 0:
        print("error run fit image errno: %s" % str(res))
        sys.exit(2)
    res = build_run_chmod(args)
    if res != 0:
        print("error run chmod errno: %s" % str(res))
        sys.exit(3)

if __name__ == '__main__':
    main(sys.argv[1:])
