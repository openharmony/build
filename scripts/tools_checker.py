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

import os
import sys
import subprocess
import json


def run_command(cmd, verbose=None):
    """Execute command `cmd`
    :param cmd: Command to be executed.
    :param verbose: Whether echo runtime infomation and output of command `cmd`.
    :return output: The output of command `cmd`.
    :return returncode: The return code of command `cmd`.
    """
    if verbose:
        print("Running: {}".format(' '.join(cmd)))
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, _ = p.communicate()
    if verbose:
        print(output.decode().rstrip())
    return output, p.returncode


def package_installed(pkg_name):
    """Check whether package `pkg_name` is installed or not.
    Got package `pkg_name` installation state by executing `dpkg -s pkg_name`.
    :param pkg_name: Package name to check.
    :return r: Check result, 0 means installed, non-zero means not installed.
    """
    cmd = ['dpkg', '-s', pkg_name]
    _, r = run_command(cmd)
    return r


def check_build_requried_packages(host_version, check=True):
    """Check whether packages required by build process installed or not.
    By parsing file `REPO_ROOT/build/scripts/build_package_list.json`.
    Example content: `{"18.04":{"dep_package":["pkg1","pkg2",...]}, "20.04":{...}}`
    Currently there are only lists for `Ubuntu 18.04` and `Ubuntu 20.04`.
    :param host_version: OS version of the host.
    :param check: Whether to prompt user of missing package.
    :return _build_package_list: List of packages required by build process.
    :return install_package_list: Packages installed.
    :return uninstall_package_list: Packages missing.
    """
    cur_dir = os.getcwd()
    build_package_json = os.path.join(cur_dir, 'build/scripts/build_package_list.json')
    with open(build_package_json, 'r') as file:
        file_json = json.load(file)
        for _version in file_json.keys():
            if host_version == _version or host_version.startswith(_version):
                _build_package_list = file_json["{}".format(_version)]["dep_package"]
    uninstall_package_list = []
    for pkg in _build_package_list:
        if package_installed(pkg):
            if check:
                print("\033[33m {} is not installed. please install it.\033[0m".
                      format(pkg))
            uninstall_package_list.append(pkg)
    install_package_list = list(set(_build_package_list).difference(uninstall_package_list))
    return _build_package_list,install_package_list, uninstall_package_list


def check_os_version():
    """Check OS type and version.
    By parsing file `/etc/issue`.
    :return -1: Retuern -1 if OS is not supported.
    :return host_os: Host OS type, currently only `Ubuntu` supported.
    :return host_version: Host OS version, currently only `18.04[.X]` or `20.04[.X]` supported.
    """
    available_os = ('Ubuntu')
    available_releases = ('18.04', '20.04')
    _os_info, _returncode = run_command(['cat', '/etc/issue'])
    if _returncode != 0:
        return -1

    _os_info = _os_info.decode().rstrip().split()
    host_os = _os_info[0]
    host_version = _os_info[1]
    if host_os not in available_os:
        print("\033[33m OS {} is not supported for ohos build.\033[0m".format(
            host_os))
        return -1
    version_available = False
    for _version in available_releases:
        if host_version == _version or host_version.startswith(_version):
            version_available = True
            break
    if not version_available:
        print("\033[33m OS version {} is not supported for ohos build.\033[0m".
              format(host_version))
        print("\033[33m Available OS version are {}.\033[0m".format(
            ', '.join(available_releases)))
        return -1
    return host_os, host_version


def main():
    """Entrance function.
    :return -1: Return -1 on error.
    :return 0: Return 0 on success.
    """
    check_result = check_os_version()
    
    if check_result == -1:
        return -1

    _, _, missing_packages = check_build_requried_packages(check_result[1], check=True)

    if(len(missing_packages) == 0):
        return 0
    else:
        print("\033[31m Missing dependencies, please check!\033[0m")
        return -1


if __name__ == '__main__':
    sys.exit(main())
