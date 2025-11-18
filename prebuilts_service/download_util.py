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

import importlib
import os
import stat
from common_utils import run_cmd
import threading
import hashlib
import time


remote_sha256_cache = dict()
_cache_lock = threading.Lock()


def import_rich_module():
    module = importlib.import_module("rich.progress")
    progress = module.Progress(
        module.TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
        module.BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        module.DownloadColumn(),
        "•",
        module.TransferSpeedColumn(),
        "•",
        module.TimeRemainingColumn(),
    )
    return progress


def check_sha256_by_mark(remote_url, unzip_dir: str, unzip_filename: str) -> tuple:
    """
    检查是否存在和远程文件哈希值匹配的解压完成标记文件
    标记文件名：远程文件哈希值 + '.' + unzip_filename + '.mark'
    """
    

    remote_sha256 = get_remote_sha256(remote_url)
    mark_file_name = remote_sha256 + '.' + unzip_filename + '.mark'
    mark_file_path = os.path.join(unzip_dir, mark_file_name)
    return os.path.exists(mark_file_path), mark_file_path


def file_sha256(file_path):
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):  # 分块读取大文件，避免内存问题
            sha.update(chunk)
    return sha.hexdigest()


def check_sha256(remote_url: str, local_file: str) -> bool:
    """
    检查本地文件的SHA256值是否与远程文件一致
    """

    remote_sha256 = get_remote_sha256(remote_url)
    local_sha256 = file_sha256(local_file)
    if remote_sha256 != local_sha256:
        print(
            "remote file {}.sha256 is not found, begin check SHASUMS256.txt".format(
                remote_url
            )
        )
        remote_sha256 = obtain_sha256_by_sha_sums256(remote_url)
    return remote_sha256 == local_sha256


def get_remote_sha256(remote_url: str) -> str:
    """
    从远程.sha256文件中获取哈希值
    """
    start_time = time.time()
    with _cache_lock:  # 加锁检查缓存
        if remote_url in remote_sha256_cache:
            return remote_sha256_cache[remote_url]
    
    # 在锁外执行耗时操作（如网络请求）
    check_sha256_cmd = f"curl -s -k {remote_url}.sha256"
    remote_sha256, _, _ = run_cmd(check_sha256_cmd.split())

    with _cache_lock:  # 加锁更新缓存
        remote_sha256_cache[remote_url] = remote_sha256
    endtime = time.time()
    cost_time = endtime - start_time
    remote_file_name = os.path.basename(remote_url)
    if cost_time > 3:
        print(f"get remote sha256 for {remote_file_name} cost time: {cost_time}")
    return remote_sha256


def obtain_sha256_by_sha_sums256(remote_url: str) -> str:
    """
    从远程的SHASUMS256.txt中获取SHA256值
    """
    sha_sums256 = "SHASUMS256.txt"
    sha_sums256_path = os.path.join(os.path.dirname(remote_url), sha_sums256)
    file_name = os.path.basename(remote_url)
    cmd = "curl -s -k " + sha_sums256_path
    data_sha_sums256, _, _ = run_cmd(cmd.split())
    remote_sha256 = None
    for line in data_sha_sums256.split("\n"):
        if file_name in line:
            remote_sha256 = line.split(" ")[0]
    return remote_sha256


def get_local_path(download_root: str, remote_url: str):
    """根据远程URL生成本地路径,本地文件名为url的MD5值+远程文件名
    """
    remote_file_name = os.path.basename(remote_url)
    remote_url_md5_value = hashlib.md5((remote_url + '\n').encode()).hexdigest()
    local_path = os.path.join(download_root, '{}.{}'.format(remote_url_md5_value, remote_file_name))
    return local_path


def extract_compress_files_and_gen_mark(source_file: str, unzip_dir: str, mark_file_path: str):
    """
    解压缩文件并生成解压完成标记文件
    标记文件名：远程文件哈希值 + '.' + unzip_filename + '.mark'
    """
    if not os.path.exists(unzip_dir):
        os.makedirs(unzip_dir, exist_ok=True)
    if source_file.endswith(".zip"):
        command = ["unzip", "-qq", "-o", "-d", unzip_dir, source_file]
    elif source_file.endswith(".tar.gz"):
        command = ["tar", "-xzf", source_file, "-C", unzip_dir]
    elif source_file.endswith(".tar.xz"):
        command = ["tar", "-xJf", source_file, "-C", unzip_dir]
    elif source_file.endswith(".tar"):
        command = ["tar", "-xvf", source_file, "-C", unzip_dir]
    else:
        print("暂不支持解压此类型压缩文件！")
        return
    
    _, err, retcode = run_cmd(command)
    if retcode != 0:
        print("解压失败，错误信息：", err)
        return
    else:
        flag = os.O_WRONLY | os.O_CREAT
        mode = stat.S_IWUSR | stat.S_IRUSR
        with os.fdopen(os.open(mark_file_path, flag, mode), "w") as f:
            f.write("0")
