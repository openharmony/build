#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 Huawei Device Co., Ltd.
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
#

import json
import os
import subprocess
import shutil
import argparse
import sys
import urllib.request
import socket


def _run_cmd(cmd):
    res = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    sout, serr = res.communicate(timeout=10000)
    return sout.rstrip().decode('utf-8'), serr, res.returncode


def _check_sha256(check_url: str, local_file: str) -> bool:
    check_sha256_cmd = ('curl -s -k ' + check_url + '.sha256').split(' ')
    local_sha256_cmd = ['sha256sum', local_file]
    check_sha256, err, returncode = _run_cmd(check_sha256_cmd)
    local_sha256, err, returncode = _run_cmd(local_sha256_cmd)
    local_sha256 = local_sha256.split(' ')[0]
    if check_sha256 != local_sha256:
        print('remote file {}.sha256 is not found, begin check SHASUMS256.txt'.format(check_url))
        check_sha256 = _obtain_sha256_by_sha_sums256(check_url)
    return check_sha256 == local_sha256


def _obtain_sha256_by_sha_sums256(check_url: str) -> str:
    sha_sums256 = 'SHASUMS256.txt'
    sha_sums256_path = os.path.join(os.path.dirname(check_url), sha_sums256)
    file_name = os.path.basename(check_url)
    cmd = ('curl -s -k ' + sha_sums256_path).split(' ')
    data_sha_sums256, err, returncode = _run_cmd(cmd)
    check_sha256 = None
    for line in data_sha_sums256.split('\n'):
        if file_name in line:
            check_sha256 = line.split(' ')[0]
    return check_sha256


def npm_install(_dir):
    result = subprocess.run(["npm", "install", "--prefix", _dir], capture_output=True, text=True)
    if result.returncode == 0:
        print("{}目录下npm install完毕".format(_dir))
    else:
        print("依赖项安装失败:", result.stderr)


def copy_file(src, dest):
    if not os.path.exists(dest):
        os.makedirs(dest)
    shutil.copy(src, dest)


def copy_folder(src, dest):
    if os.path.exists(dest):
        if os.path.islink(dest):
            os.unlink(dest)
        else:
            shutil.rmtree(dest)
    shutil.copytree(src, dest)


def symlink_src2dest(src_dir, dest_dir):
    if os.path.exists(dest_dir):
        if os.path.islink(dest_dir):
            os.unlink(dest_dir)
        elif os.path.isdir(dest_dir):
            shutil.rmtree(dest_dir)
        else:
            os.remove(dest_dir)
    else:
        os.makedirs(os.path.dirname(dest_dir), exist_ok=True)

    print("symlink {} ---> {}".format(src_dir, dest_dir))
    os.symlink(src_dir, dest_dir)


def install_hpm(code_path, download_dir, symlink_dir, home_path):
    content = """\
package-lock=true
registry=http://repo.huaweicloud.com/repository/npm
strict-ssl=false
lockfile=false
"""
    with os.fdopen(os.open(os.path.join(home_path, '.npmrc'), os.O_WRONLY | os.O_CREAT, mode=0o640), 'w') as f:
        os.truncate(f.fileno(), 0)
        f.write(content)
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    with os.fdopen(os.open(os.path.join(download_dir, 'package.json'), os.O_WRONLY | os.O_CREAT, mode=0o640),
                    'w') as f:
        os.truncate(f.fileno(), 0)
        f.write('{}\n')
    npm_path = os.path.join(code_path, "prebuilts/build-tools/common/nodejs/current/bin/npm")
    node_bin_path = os.path.join(code_path, "prebuilts/build-tools/common/nodejs/current/bin")
    os.environ['PATH'] = f"{node_bin_path}:{os.environ['PATH']}"
    subprocess.run(
        [npm_path, 'install', '@ohos/hpm-cli', '--registry', 'https://repo.huaweicloud.com/repository/npm/', '--prefix',
         download_dir])
    symlink_src2dest(os.path.join(download_dir, 'node_modules'), symlink_dir)


def process_npm(npm_dict, args):
    code_path = args.code_path
    home_path = args.home_path
    name = npm_dict.get('name')
    npm_download = npm_dict.get('download')
    package_path = os.path.join(code_path, npm_download.get('package_path'))
    package_lock_path = os.path.join(code_path, npm_download.get('package_lock_path'))
    hash_value = \
        subprocess.run(['sha256sum', package_lock_path], capture_output=True, text=True).stdout.strip().split(' ')[0]
    download_dir = os.path.join(home_path, npm_download.get('download_dir'), hash_value)

    if '@ohos/hpm-cli' == name:
        symlink = os.path.join(code_path, npm_download.get('symlink'))
        install_hpm(code_path, os.path.join(home_path, download_dir), os.path.join(code_path, symlink), home_path)
        return

    copy_file(package_path, download_dir)
    copy_file(package_lock_path, download_dir)

    if not os.path.exists(os.path.join(download_dir, "npm-install.js")):
        npm_install_script = os.path.join(os.path.dirname(package_path), "npm-install.js")
        if os.path.exists(npm_install_script):
            shutil.copyfile(npm_install_script, os.path.join(download_dir, "npm-install.js"))

    npm_install(download_dir)

    if name == 'legacy_bin':
        for link in npm_download.get('symlink', []):
            symlink_src2dest(os.path.join(download_dir, "node_modules"), os.path.join(code_path, link))
        return

    symlink = os.path.join(code_path, npm_download.get('symlink'))

    if name in ['parse5']:
        copy_folder(os.path.join(download_dir, "node_modules"), symlink)
        return

    copy_folder(os.path.join(download_dir, "node_modules"), symlink)

    for copy_entry in npm_download.get('copy', []):
        copy_folder(os.path.join(code_path, copy_entry['src']), os.path.join(code_path, copy_entry['dest']))

    for copy_ext_entry in npm_download.get('copy_ext', []):
        copy_folder(os.path.join(code_path, copy_ext_entry['src']), os.path.join(code_path, copy_ext_entry['dest']))


def download_url(url, folder_path):
    filename = url.split('/')[-1]
    file_path = os.path.join(folder_path, filename)
    if os.path.exists(file_path):
        if _check_sha256(url, file_path):
            return
        else:
            os.remove(file_path)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    try:
        print("Downloading {}".format(url))
        with urllib.request.urlopen(url) as response, os.fdopen(
                os.open(file_path, os.O_WRONLY | os.O_CREAT, mode=0o640), 'wb') as out_file:
            total_size = int(response.headers['Content-Length'])
            chunk_size = 16 * 1024
            downloaded_size = 0
            print_process(chunk_size, downloaded_size, out_file, response, total_size)
        print("\n{} downloaded successfully".format(url))
    except urllib.error.URLError as e:
        print("Error:", e.reason)
    except socket.timeout:
        print("Timeout error: Connection timed out")


def print_process(chunk_size, downloaded_size, out_file, response, total_size):
    while True:
        chunk = response.read(chunk_size)
        if not chunk:
            break
        out_file.write(chunk)
        downloaded_size += len(chunk)
        if total_size != 0:
            progress = downloaded_size / total_size * 50
            print(f'\r[{"=" * int(progress)}{" " * (50 - int(progress))}] {progress * 2:.2f}%', end='', flush=True)
        else:
            print("\r[Error] Total size is zero, unable to calculate progress.", end='', flush=True)


def extract_compress_files(source_file, destination_folder):
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder, exist_ok=True)
    if source_file.endswith('.zip'):
        command = ['unzip', '-qq', '-o', '-d', destination_folder, source_file]
    elif source_file.endswith('.tar.gz'):
        command = ['tar', '-xzf', source_file, '-C', destination_folder]
    elif source_file.endswith('.tar.xz'):
        command = ['tar', '-xJf', source_file, '-C', destination_folder]
    else:
        print("暂不支持解压此类型压缩文件！")
        command = []
    try:
        subprocess.run(command, check=True)
        print(f"{source_file} extracted to {destination_folder}")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")


def install_python(version, download_dir, one_type, code_path):
    after_extract_folder = os.listdir(os.path.join(download_dir, version))[0]
    copy_folder(os.path.join(download_dir, version, after_extract_folder, one_type.get('copy_src')),
                os.path.join(download_dir, version, after_extract_folder, one_type.get('copy_dest')))
    copy_folder(os.path.join(download_dir, version, after_extract_folder),
                os.path.join(code_path, one_type.get('symlink')))
    python3_path = os.path.join(download_dir, version, after_extract_folder, one_type.get('copy_src'),
                                'bin', 'python3.11')
    pip3_path = os.path.join(download_dir, version, after_extract_folder, one_type.get('copy_src'), 'bin',
                             'pip3.11')
    subprocess.run(
        [python3_path, pip3_path, "install", "--trusted-host", "repo.huaweicloud.com", "-i",
         "http://repo.huaweicloud.com/repository/pypi/simple"] + one_type.get(
            'pip_install'))


def install_rustc(url, download_dir, version, one_type, code_path):
    part_file_name = url.split('/')[-1].split('linux')[0]
    after_extract_file_list = os.listdir(os.path.join(download_dir, version))
    for file_name in after_extract_file_list:
        if part_file_name in file_name:
            script_path = os.path.join(download_dir, version, file_name, "install.sh")
            subprocess.run([script_path, "--prefix=''",
                            "--destdir='{}'".format(os.path.join(code_path, one_type.get('destdir')))])
            break


def process_tar(tar_dict, args):
    code_path = args.code_path
    home_path = args.home_path
    os_type = args.target_os
    cpu_type = args.target_cpu
    tar_name = tar_dict.get('name')
    print(tar_name)
    tar_download = tar_dict.get('download')
    for one_type in tar_download:
        download_flag = download_or_not(cpu_type, one_type, os_type)
        if download_flag == True:
            version = one_type.get('version')
            url = os.path.join(args.repo_https, one_type.get('url'))
            download_dir = os.path.join(home_path, one_type.get('download_dir'))
            download_url(url, download_dir)
            extract_compress_files(os.path.join(download_dir, url.split('/')[-1]),
                                   os.path.join(download_dir, version))
            if tar_name == 'python':
                install_python(version, download_dir, one_type, code_path)
                continue
            if 'rustc' in tar_name:
                install_rustc(url, download_dir, version, one_type, code_path)
                continue
            if tar_name == 'llvm':
                after_extract_folder = os.listdir(os.path.join(download_dir, version))[0]
                copy_folder(os.path.join(download_dir, version, after_extract_folder, one_type.get('copy_src')),
                            os.path.join(download_dir, version, after_extract_folder, one_type.get('copy_dest')))
                copy_folder(os.path.join(download_dir, version, after_extract_folder),
                            os.path.join(code_path, one_type.get('symlink')))
                continue
            if tar_name in ['ark_tools']:
                after_extract_folder = os.listdir(os.path.join(download_dir, version))[0]
                copy_folder(os.path.join(download_dir, version, after_extract_folder),
                            os.path.join(code_path, one_type.get('symlink')))
                continue
            after_extract_file_list = os.listdir(os.path.join(download_dir, version))
            symlink = os.path.join(code_path, one_type.get('symlink'))
            if one_type.get('type') == 'dir':
                deal_tar_dir(after_extract_file_list, download_dir, symlink, tar_name, version)
            else:
                file_name = after_extract_file_list[0]
                symlink_src2dest(os.path.join(download_dir, version, file_name), symlink)
            if tar_name == 'nodejs' and url == os.path.join(args.repo_https,
                                                            "nodejs/v14.21.1/node-v14.21.1-linux-x64.tar.gz"):
                symlink_src2dest(symlink, os.path.join(os.path.dirname(symlink), 'current'))


def download_or_not(cpu_type, one_type, os_type):
    download_flag = False
    if cpu_type == 'any':
        if one_type.get('target_os') == os_type:
            download_flag = True
    else:
        if one_type.get('target_os') == os_type and (
                one_type.get('target_cpu') == cpu_type or one_type.get('target_cpu') == ""):
            download_flag = True
    return download_flag


def deal_tar_dir(after_extract_file_list, download_dir, symlink, tar_name, version):
    for one_file in after_extract_file_list:
        if tar_name == 'packing_tool':
            symlink_src2dest(os.path.join(download_dir, version, one_file),
                             os.path.join(symlink, one_file))
        else:
            symlink_src2dest(os.path.join(download_dir, version, one_file),
                             symlink)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--code_path', required=True, type=str, help='path of openharmony code')
    parser.add_argument('--home_path', required=True, type=str, help='path of home')
    parser.add_argument('--config_file', required=True, type=str, help='path of prebuilts_config.json')
    parser.add_argument('--repo_https', required=True, type=str, default='https://repo.huaweicloud.com',
                        help='path of prebuilts_config.json')
    parser.add_argument('--target_os', required=True, type=str, help='type of os')
    parser.add_argument('--target_cpu', type=str, default='any', help='type of cpu')
    args = parser.parse_args()
    config_file = args.config_file
    with open(config_file, 'r', encoding='utf-8') as r:
        config = json.load(r)
    tar = config['tar']
    for one_tar in tar:
        process_tar(one_tar, args)
    npm = config['npm']
    for one_npm in npm:
        process_npm(one_npm, args)


if __name__ == '__main__':
    sys.exit(main())
