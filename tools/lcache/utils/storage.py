#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
# Description: lcache storage main entry

import os
import tempfile
import json
import fcntl
import time

from pathlib import Path
from datetime import datetime

from context import Context
from utils.log_util import Log
from utils.zstd_util import zstd_compress, zstd_decompress


class Storage:
    def __init__(self, context: Context, log: Log) -> None:
        self.lcache_dir = context.config.lcache_dir
        self.lcache_lru_dir = context.config.lcache_lru_dir
        self.lcache_logfile = context.config.lcache_logfile
        self.lcache_max_size = context.config.lcache_max_size
        self.output = context.output
        self.linker = context.real_linker
        self.full_args = context.full_args
        self.lcache_allow_env = context.config.lcache_allow_env
        self.log = log

    @staticmethod
    def atomic_output_path(output: Path) -> Path:
        fd, tmp = tempfile.mkstemp(
            prefix=f".{output.name}.",
            dir=str(output.parent),
        )
        os.close(fd)
        return Path(tmp)

    def get_lru_path(self, key: str) -> Path:
        path = os.path.join(self.lcache_lru_dir, f"{key}.lru")
        return Path(path)

    def get_result_path(self, key: str) -> Path:
        path = os.path.join(self.lcache_dir, key[0], key[1], f"{key}.result")
        return Path(path)
    
    def get_meta_path(self, key: str) -> Path:
        path = os.path.join(self.lcache_dir, key[0], key[1], f"{key}.meta")
        return Path(path)
    
    def update_lru(self, key: str):
        self.get_lru_path(key).touch(exist_ok=True)
    
    def cleanup_cache(self):
        cache_dir = Path(self.lcache_dir)
        lru_dir = Path(self.lcache_lru_dir)
        cache_size = self.lcache_max_size * 1024 * 1024 * 1024 * 0.9
        lock_file = cache_dir / ".cleanup.lock"
        VALID_SUFFIXES = ('.meta', '.result')

        # 打开锁文件，如果不存在则创建
        lock_file.parent.mkdir(parents=True, exist_ok=True)
        with open(lock_file, 'w') as f:
            try:
                # 加排他锁（非阻塞），如果锁被占用则直接跳过
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                self.log.warn("Cleanup is in progress, skip.")
                return
            
            # 计算当前缓存总大小
            total = sum(p.stat().st_size for p in cache_dir.rglob("*")
                        if p.is_file() and p.name.endswith(VALID_SUFFIXES))
            
            if total <= cache_size:
                return

            self.log.info(f"Cache size {total} exceeds limit {cache_size}, starting cleanup.")

            # 按最久未使用顺序清理
            lrus = sorted(lru_dir.glob("*.lru"), key=lambda p: p.stat().st_mtime)
            for lru in lrus:
                key = lru.stem
                blob = self.get_result_path(key)
                meta = self.get_meta_path(key)
                size = blob.stat().st_size if blob.exists() else 0
                self.log.info(f"Cleaning cache {key}, data size {size}.")
                blob.unlink(missing_ok=True)
                meta.unlink(missing_ok=True)
                lru.unlink(missing_ok=True)
                total -= size
                if total <= cache_size * 0.9:
                    break
            
            self.log.info(f"Cache cleanup finished. Current size: {total}.")
    
    def store_result(self, key: str, file_hash: list):
        rp = self.get_result_path(key)
        # 检查是否已被其他进程写入
        if rp.exists():
            self.log.info(f"Cache {key} already exists, skip storing", console=False)
            return
        mp = self.get_meta_path(key)
        rp.parent.mkdir(parents=True, exist_ok=True)
        output_path = Path(self.output)

        self.log.info(f"Storing result to {rp}", console=False)
        # -------- result --------
        tmp_rp = self.atomic_output_path(rp)
        try:
            zstd_compress(
                src=output_path,
                dst=tmp_rp,
                threads=4,
            )
            # 再次检查，防止竞态
            if not rp.exists():
                tmp_rp.replace(rp)
            else:
                self.log.info(f"Cache {key} was created by another process", console=False)
        finally:
            if tmp_rp.exists():
                tmp_rp.unlink(missing_ok=True)

        # -------- meta --------
        self.log.info(f"Storing meta to {mp}", console=False)
        meta = {
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "linker": self.linker,
            "args": self.full_args,
            "allowed_env": "" if self.lcache_allow_env is None else self.lcache_allow_env,
            "file_hash": file_hash
        }
        meta_bytes = json.dumps(meta, separators=(",", ":")).encode("utf-8")
        tmp_mp = self.atomic_output_path(mp)
        tmp_mp.write_bytes(meta_bytes)
        zstd_compress(
            src=tmp_mp,
            dst=mp,
            threads=1,
        )
        tmp_mp.unlink()
    
    def restore_result(self, key: str, output: Path):
        rp = self.get_result_path(key)
        output.parent.mkdir(parents=True, exist_ok=True)

        zstd_decompress(
            src=rp,
            dst=output,
            threads=8,
        )
        output.touch()