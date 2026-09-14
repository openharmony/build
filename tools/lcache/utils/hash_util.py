#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
# Description: lcache hash util main entry

import re
import os

from pathlib import Path
from blake3 import blake3
from typing import List, Optional

from context import Context
from utils.log_util import Log
from utils.exec_error import ExecError


class LinkMode:
    STATIC = "static"  # -Bstatic
    DYNAMIC = "dynamic"  # 默认：先 so 再 a


# 文件型参数
FILE_INPUT_FLAGS = {
    "--symbol-order-file",
    "--section-ordering-file",
    "--version-script",
    "--dynamic-list",
    "--retain-symbols-file",
    "--pgo-profile",
    "--bolt-profile",
    "--fdo-profile",
}


# lds文件解析
LDS_INCLUDE_RE = re.compile(r'^\s*INCLUDE\s+(\S+)', re.IGNORECASE)


class HashUtil:
    def __init__(self, log: Log, context: Context) -> None:
        self.log = log
        self.context = context
        self.file_hash = []
        pass

    @staticmethod
    def norm_path(path: Path, work_dir: Path) -> bytes:
        path = path.resolve()
        work_dir = work_dir.resolve()
        return os.path.relpath(path, work_dir).encode()

    @staticmethod
    def default_system_lib_dirs(sysroot: Path | None):
        if sysroot:
            return [sysroot / "lib", sysroot / "usr/lib"]
        return [Path("/lib"), Path("/usr/lib")]

    @staticmethod
    def find_lds_file(name: str, script_dir: Path, search_dirs: list[Path]) -> Path | None:
        for d in [script_dir] + search_dirs:
            p = d / name
            if p.is_file():
                return p.resolve()
        raise ExecError(f"Can not find linker script: {name}.")

    @staticmethod
    def parse_lds_includes(path: Path) -> list[str]:
        includes = []
        for line in path.read_text(errors="ignore").splitlines():
            m = LDS_INCLUDE_RE.match(line)
            if m:
                includes.append(m.group(1))
        return includes
    
    def compute_link_hash(self):
        h = blake3()
        # hash lcache版本
        h.update(self.context.config.lcache_version.encode("utf-8"))
        self.log.info(f"Lcache version hash is : {h.hexdigest()}", console=False)
        # hash编译器
        compiler_hash = self.hash_compiler()
        h.update(compiler_hash)
        # hash环境变量
        if self.context.config.lcache_allow_env is not None and len(self.context.config.lcache_allow_env) > 0:
            self.log.info(f"Need hash environment variable : {self.context.config.lcache_allow_env}", console=False)
            env_hash = self.hash_env_vars()
            h.update(env_hash)
        # hash 链接命令
        command_hash = self.hash_link_command()
        h.update(command_hash)
        return h.hexdigest(), self.file_hash

    def hash_compiler(self) -> bytes:
        real_linker, mode = self.context.real_linker, self.context.config.lcache_compiler_check
        h = blake3()
        if mode == "content":
            linker_path = Path(os.path.realpath(real_linker))
            h.update(self.hash_file_content(linker_path))
        elif mode == "none":
            self.log.info(f"Do not hash link compiler.", console=False)
        else:
            st = os.stat(real_linker)
            h.update(st.st_mtime_ns.to_bytes(8, "little", signed=False))
            h.update(st.st_size.to_bytes(8, "little", signed=False))
        self.log.info(f"Linker hash is : {h.hexdigest()}", console=False)
        return h.digest()

    def hash_env_vars(self) -> bytes:
        """
        获取当前进程可见的所有环境变量，并计算 BLAKE3 hash
        """
        envs = self.context.config.lcache_allow_env
        h = blake3()
        env_list = []
        if len(envs) > 0:
            env_list = [var.strip() for var in envs.split(",")]
        
        # 按 key 排序，保证 hash 稳定
        for key in sorted(os.environ.keys()):
            if key not in env_list:
                continue
            value = os.environ[key]
            self.log.info(f"Environment {key} value is : {value}", console=False)

            h.update(key.encode("utf-8"))
            h.update(b"\x00")  # key/value 分隔符
            h.update(value.encode("utf-8"))
            h.update(b"\x00")  # 变量分隔符
        self.log.info(f"Environment hash is : {h.hexdigest()}", console=False)
        return h.digest()

    def hash_link_command(self) -> bytes:
        """
        argv     : 链接参数（不含 clang/gcc/ld 本身）
        work_dir : 执行链接命令时的工作目录
        """
        argv = self.context.full_args
        work_dir = Path(self.context.work_dir)
        h = blake3()

        link_mode = LinkMode.DYNAMIC
        sysroot: Optional[Path] = None
        library_dirs: List[Path] = []
        lds_files: List[Path] = []

        i = 0
        while i < len(argv):
            arg = argv[i]

            # ----------------------------
            # 链接模式
            # ----------------------------
            if arg == "-Bstatic":
                link_mode = LinkMode.STATIC
                h.update(b"-Bstatic")
                i += 1
                continue

            if arg == "-Bdynamic":
                link_mode = LinkMode.DYNAMIC
                h.update(b"-Bdynamic")
                i += 1
                continue

            # ----------------------------
            # 处理输出产物
            # ----------------------------
            if arg == "-o":
                h.update(b"-o")
                output = argv[i + 1]
                h.update(self.norm_path(Path(output), Path(self.context.work_dir)))
                i += 2
                continue

            # ----------------------------
            # --sysroot
            # ----------------------------
            if arg.startswith("--sysroot"):
                if arg == "--sysroot":
                    sysroot = Path(argv[i + 1])
                    i += 2
                else:
                    sysroot = Path(arg.split("=", 1)[1])
                    i += 1
            
                h.update(b"--sysroot")
                h.update(self.norm_path(sysroot, work_dir))
                continue

            # ----------------------------
            # -L
            # ----------------------------
            if arg.startswith("-L"):
                if arg == "-L":
                    d = Path(argv[i + 1])
                    i += 2
                else:
                    d = Path(arg[2:])
                    i += 1
                
                library_dirs.append(d)
                h.update(b"-L")
                h.update(self.norm_path(d, work_dir))
                continue
            
            # ----------------------------
            # -fprofile-use
            # ----------------------------
            if arg.startswith("-fprofile-use"):
                if arg == "-fprofile-use":
                    prof_dir = Path(argv[i + 1])
                    i += 2
                else:
                    prof_dir = Path(arg.split("=", 1)[1])
                    i += 1
                
                h.update(b"-fprofile-use")
                h.update(self.norm_path(prof_dir, work_dir))

                if prof_dir.is_dir():
                    h.update(self.hash_directory_contents(prof_dir, work_dir))
                elif prof_dir.is_file():
                    h.update(self.hash_file_content(prof_dir))
                else:
                    self.log.warn(f"Can not find profile dir: {prof_dir}")
                    h.update(b"MISSING_PROFILE_DIR")
                continue
            
            # ----------------------------
            # -lxxx
            # ----------------------------
            if arg.startswith("-l"):
                name = arg[2:]

                default_dirs = self.default_system_lib_dirs(sysroot)
                search_dirs = library_dirs + default_dirs + self.context.default_lib_dirs

                lib = self.resolve_library(name, search_dirs, link_mode)
                if not lib:
                    raise ExecError(f"library -l{name} not found")
                
                h.update(b"-l")
                h.update(name.encode())
                h.update(self.norm_path(lib, work_dir))
                h.update(self.hash_file_content(lib))
                i += 1
                continue
            
            # ----------------------------
            # -T / --script / *.lds
            # ----------------------------
            if arg == "-T" or arg == "--script":
                if i + 1 >= len(argv):
                    raise ExecError(f"{arg} missing argument")
                
                lds_file = Path(argv[i + 1])
                lds_files.append(lds_file)
                h.update(arg.encode())
                h.update(self.norm_path(lds_file, work_dir))
                i += 2
                continue
            
            if arg.startswith("-T") and arg != "-T":
                lds_file = Path(arg[2:])
                lds_files.append(lds_file)

                h.update(b"-T")
                h.update(self.norm_path(lds_file, work_dir))

                i += 1
                continue

            if arg.startswith("--script="):
                lds_file = Path(arg.split("=", 1)[1])
                lds_files.append(lds_file)

                h.update(b"--script")
                h.update(self.norm_path(lds_file, work_dir))

                i += 1
                continue
            
            if arg.endswith(".lds"):
                p = Path(arg)
                lds_files.append(p)
                h.update(self.norm_path(p, work_dir))
                i += 1
                continue
            
            # ----------------------------
            # 文件型输入参数 --flag=xxx / --flag xxx
            # ----------------------------
            if any(arg.startswith(flag + "=") for flag in FILE_INPUT_FLAGS):
                path = Path(arg.split("=", 1)[1])
                h.update(arg.split("=", 1)[0].encode())
                h.update(self.norm_path(path, work_dir))
                h.update(self.hash_file_content(path))
                i += 1
                continue
            
            if arg in FILE_INPUT_FLAGS:
                path = Path(argv[i + 1])
                h.update(arg.encode())
                h.update(self.norm_path(path, work_dir))
                h.update(self.hash_file_content(path))
                i += 2
                continue
            
            # ----------------------------
            # 普通输入文件
            # ----------------------------
            p = Path(arg)
            if p.is_file():
                self.log.debug(f"Hash file: {p.resolve()}.", console=False)
                h.update(b"FILE")
                h.update(self.norm_path(p, work_dir))
                h.update(self.hash_file_content(p))
                i += 1
                continue
            
            # ----------------------------
            # 其他参数
            # ----------------------------
            h.update(b"ARG")
            h.update(arg.encode())
            i += 1
        
        # ----------------------------
        # .lds INCLUDE 文件hash计算
        # ----------------------------
        search_dirs = library_dirs + self.default_system_lib_dirs(sysroot)
        lds_all: list[Path] = []

        for item in lds_files:
            self.resolve_lds_file(item, search_dirs, set(), lds_all)
        for lds_path in lds_all:
            h.update(self.norm_path(lds_path, work_dir))
        
        return h.digest()

    def hash_directory_contents(self, dir_path: Path, work_dir: Path) -> bytes:
        h = blake3()
        files: List[Path] = []

        for root, _, names in os.walk(dir_path):
            for n in names:
                p = Path(root) / n
                if p.is_file():
                    files.append(p)
        
        for p in sorted(files):
            h.update(self.norm_path(p, work_dir))
            h.update(self.hash_file_content(p))
        
        return h.digest()

    def resolve_library(self, name: str, search_dirs: List[Path], mode: str) -> Optional[Path]:
        if mode == LinkMode.STATIC:
            candidates = (f"lib{name}.a",)
        else:
            candidates = (f"lib{name}.so", f"lib{name}.a")
        
        for d in search_dirs:  # 目录优先
            if not d.is_dir():
                continue
            for lib_name in candidates:  # 在该目录内决定 .so / .a
                p = d / lib_name
                if p.is_file():
                    self.log.debug(f"Lib {name}  find in {p.resolve()}", console=False)
                    return p.resolve()
        raise ExecError(f"library -l{name} not found in search dirs: {[str(d) for d in search_dirs]}")
    
    def resolve_lds_file(self, lds_file: Path, search_dirs: List[Path], seen: set[Path], out: list[Path]):
        lds_path = self.find_lds_file(lds_file.name, lds_file.parent, search_dirs)
        if lds_path in seen:
            return
        
        seen.add(lds_path)
        out.append(lds_path)

        for inc in self.parse_lds_includes(lds_file):
            include_file = self.find_lds_file(inc, lds_file.parent, search_dirs)
            if include_file:
                self.resolve_lds_file(include_file, search_dirs, seen, out)

    def hash_file_content(self, path: Path) -> bytes:
        h = blake3()
        try:
            with path.open("rb") as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    h.update(chunk)
        except (IOError, OSError) as e:
            self.log.error(f"Failed to read file {path}: {e}", console=False)
            raise ExecError(f"Failed to read file {path}: {e}")
        
        item = {
            "name": str(path),
            "hash": h.hexdigest()
        }
        self.file_hash.append(item)
        return h.digest()