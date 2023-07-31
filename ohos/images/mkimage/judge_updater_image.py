# coding: utf-8
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

import os
import sys
import subprocess


def run_cmd(cmd):
    res = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    sout, serr = res.communicate()

    return res.pid, res.returncode, sout, serr


def get_needed_lib(file_path):
    cmd = " ".join(["readelf", "-d", file_path])
    res = run_cmd(cmd)
    if res[1] != 0:
        print("error run readelf -d %s, errno: %s" % (file_path, str(res)))
        print(" ".join(["pid ", str(res[0]), " ret ", str(res[1]), "\n",
                        res[2].decode(), res[3].decode()]))
        sys.exit(1)
    needed_lib_name = set()
    lib_info = res[2].decode().split()
    for i, val in enumerate(lib_info):
        if val == "(NEEDED)" and lib_info[i+3].startswith("[") and lib_info[i+3].endswith("]"):
            needed_lib_name.add(lib_info[i+3][1:-1]) #... (NEEDED) Shared library: [libc++.so] ...
    return needed_lib_name


def judge_updater_binary_available(updater_root_path):
    updater_binary_path = os.path.join(updater_root_path, "bin", "updater_binary")
    updater_binary_needed_lib = get_needed_lib(updater_binary_path)
    updater_binary_lib_scope = {'libc.so', 'libc++.so', 'libselinux.z.so', 'librestorecon.z.so', 'libbegetutil.z.so'}
    extra_lib = updater_binary_needed_lib - updater_binary_lib_scope
    if len(extra_lib) != 0:
        print("error not allow updater_binary to depend new dynamic library: %s" % (" ".join(extra_lib)))
        return False
    return True

def judge_updater_available(updater_root_path):
    updater_path = os.path.join(updater_root_path, "bin", "updater") 
    updater_needed_lib = get_needed_lib(updater_path)
    all_lib_path = [os.path.join(updater_root_path, "lib64"), os.path.join(updater_root_path, "lib")]
    all_lib_name = set()
    for path in all_lib_path:
        for root,dirs,files in os.walk(path):
            for file in files:
                all_lib_name.add(file)
    extra_lib = updater_needed_lib - all_lib_name
    if len(extra_lib) != 0:
        print("error not allow updater to depend dynamic library which not exist in updater.img: %s" % (" ".join(extra_lib)))
        return False
    return True


def judge_updater_img_available(updater_root_path):
    return judge_updater_binary_available(updater_root_path) and\
           judge_updater_available(updater_root_path)