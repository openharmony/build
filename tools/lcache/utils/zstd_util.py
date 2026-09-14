#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
# Description: lcache zstd main entry

import sys
import subprocess
import json
import os
import shutil

from pathlib import Path

from utils.exec_error import ExecError


def _get_bundled_zstd() -> Path:
    # 1. 从环境变量读取
    env_zstd = os.environ.get("ZSTD_PATH")
    if env_zstd:
        zstd = Path(env_zstd)
        if zstd.exists():
            return zstd
    # 2. 从系统 PATH 查找
    path_zstd = shutil.which("zstd")
    if path_zstd:
        return Path(path_zstd)

    # 3. 未找到 zstd
    raise ExecError("zstd not found. Please install zstd or set ZSTD_PATH environment variable.")


def check_zstd():
    _get_bundled_zstd()


def zstd_compress(src: Path, dst: Path, threads: int = 4):
    zstd = _get_bundled_zstd()
    result = subprocess.run(
        [
            str(zstd),
            f"-T{threads}",
            "-3",
            "-f",
            "-o", str(dst),
            str(src),
        ],
        check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    # 返回码
    ret = result.returncode
    # 标准错误
    stderr = result.stderr.decode()
    if ret != 0:
        raise ExecError(f"ERROR: Zstd compress failed ({ret}), error is {stderr}.")


def zstd_decompress(src: Path, dst: Path, threads: int = 4):
    zstd = _get_bundled_zstd()
    result = subprocess.run(
        [
            str(zstd),
            "-d",
            f"-T{threads}",
            "-f",
            "-o", str(dst),
            str(src),
        ],
        check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    # 返回码
    ret = result.returncode
    # 标准错误
    stderr = result.stderr.decode()
    if ret != 0:
        raise ExecError(f"ERROR: Zstd decompress failed ({ret}), error is {stderr}.")


def load_meta(meta_path: Path) -> dict:
    zstd = _get_bundled_zstd()
    result = subprocess.run(
        [
            str(zstd),
            "-d",
            "--stdout",
        ],
        check=True,
        input=meta_path.read_bytes(),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    return json.loads(result.stdout.decode("utf-8"))