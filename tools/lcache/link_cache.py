#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
# Description: lcache command-line main entry

import os
import sys
import shlex
import subprocess
import shutil

from pathlib import Path
from dataclasses import fields

from config import Config
from context import Context
from utils.exec_error import ExecError
from utils.hash_util import HashUtil
from utils.storage import Storage
from utils.log_util import Log
from utils.help import print_help
from utils.zstd_util import load_meta, check_zstd

log: Log = None


def parse_arguments(argv: list[str]) -> Context:
    context = Context()
    context.linker_args = list()
    context.command_arr = list()
    config = context.config
    args_iter = iter(argv)
    for a in args_iter:
        if a.startswith("--work-dir="):
            context.work_dir = a.split("=", 1)[1]
            continue

        if a.startswith("--real-linker="):
            context.real_linker = a.split("=", 1)[1]
            continue
        
        if a.startswith("--lcache-dir="):
            config.lcache_dir = a.split("=", 1)[1]
            continue

        if a.startswith("--lcache-logfile="):
            config.lcache_logfile = a.split("=", 1)[1]
            continue

        if a.startswith("--lcache-allow-env="):
            config.lcache_allow_env = a.split("=", 1)[1]
            continue

        if a.startswith("--lcache-compiler-check="):
            config.lcache_compiler_check = a.split("=", 1)[1]
            continue

        if a.startswith("--lcache-mode="):
            config.lcache_mode = a.split("=", 1)[1]
            continue

        if a.startswith("--lcache-max-size="):
            config.lcache_max_size = int(a.split("=", 1)[1])
            continue

        if a.startswith("--lcache-max-rsp-depth="):
            config.lcache_max_rsp_depth = int(a.split("=", 1)[1])
            continue

        if a.startswith("--lcache-log-level="):
            config.lcache_log_level = a.split("=", 1)[1]
            continue

        if a.startswith("--lcache-config-file="):
            config.lcache_config_file = a.split("=", 1)[1]
            continue
        
        context.command_arr.append(a)
    # 读取环境变量中的配置
    get_config_from_env(context)
    # 读取配置文件中的配置
    get_config_from_file(config)
    # 设置默认值
    set_default_config(config)

    return context


def get_config_from_env(context: Context):
    config = context.config
    config_envs = {k: v for k, v in os.environ.items() if k.startswith('LCACHE')}
    for k, v in config_envs.items():
        if k == "LCACHE_WORK_DIR":
            context.work_dir = v
            continue
        fill_config_value(config, k, v)


def get_config_from_file(config: Config):
    file = config.lcache_config_file
    if file is None:
        return
    if not os.path.exists(file):
        return
    with open(file, 'r') as f:
        config_list = f.readlines()
    for line in config_list:
        # 去除首尾空白
        line = line.strip()
        # 跳过空行和注释
        if not line or line.startswith('#'):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        fill_config_value(config, k, v)


def set_default_config(config: Config):
    default_config = {
        "lcache_max_size": 20,
        "lcache_max_rsp_depth": 10,
        "lcache_compiler_check": "mtime",
        "lcache_mode": "ALL",
        "lcache_log_level": "INFO",
        "lcache_dir": os.path.join(Path.home(), ".link-cache"),
    }
    for k, v in default_config.items():
        fill_config_value(config, k, v)
    if config.lcache_lru_dir is None:
        config.lcache_lru_dir = os.path.join(config.lcache_dir, "lru")
    if config.lcache_logfile is None:
        config.lcache_logfile = os.path.join(config.lcache_dir, "link_cache.log")
    if config.lcache_config_file is None:
        config.lcache_config_file = os.path.join(config.lcache_dir, "link_cache.cfg")
        

def fill_config_value(config: Config, k: str, v: str):
    field_name = str(k).lower()
    if not hasattr(config, field_name):
        return
    value = getattr(config, field_name)
    if value is not None:
        return
    # 获取该字段的预期类型
    target_field = next(f for f in fields(config) if f.name == field_name)
    try:
        converted_value = target_field.type(v)
        setattr(config, field_name, converted_value)
    except (ValueError, TypeError):
        # 转换失败
        log.error(f"The value of {k} is invalid.", console=False)


def print_config(context: Context):
    config = context.config
    log.info(F"=== LINK CACHE {config.lcache_version} STARTED ======================================", console=False)
    log.info(f"Config: cache_dir = {config.lcache_dir}", console=False)
    log.info(f"Config: cache_mode = {config.lcache_mode}", console=False)
    log.info(f"Config: cache_compiler_check = {config.lcache_compiler_check}", console=False)
    log.info(f"Config: real_linker = {context.real_linker}", console=False)
    log.info(f"Config: work_dir = {context.work_dir}", console=False)
    log.info(f"Config: log_file = {config.lcache_logfile}", console=False)
    log.info(f"Config: log_level = {config.lcache_log_level}", console=False)
    log.info(f"Config: allowed_env = {config.lcache_allow_env}", console=False)
    log.info(f"Config: max_cache_size = {config.lcache_max_size} GB", console=False)
    log.info(f"Config: max_rsp_depth = {config.lcache_max_rsp_depth}", console=False)
    log.info(f"Config: lru_dir = {config.lcache_lru_dir}", console=False)


def find_compiler(context: Context):
    if context.real_linker:
        arg0 = context.real_linker
    else:
        arg0 = context.command_arr[0]
    # 1. 查找路径
    executable = arg0 if os.path.sep in arg0 else shutil.which(arg0)
    if not executable:
        raise ExecError("Can not find compiler, please use --real-linker to specify the compiler path.")
    
    # 2. 规范化并检查权限
    real_path = os.path.realpath(executable)
    if not (os.path.isfile(real_path) and os.access(real_path, os.X_OK)):
        raise ExecError("Can not find compiler, please use --real-linker to specify the compiler path.")

    # 3. 快速名称匹配
    basename = os.path.basename(real_path).lower()
    patterns = ("gcc", "g++", "clang", "cc", "icc", "icpc", "c++")
    if any(p in basename for p in patterns):
        context.real_linker = real_path
        return
    
    raise ExecError("Can not find compiler, please use --real-linker to specify the compiler path.")


def find_output_file(context: Context):
    i = 0
    full_args = context.full_args
    while i < len(full_args):
        arg = full_args[i]
        # 解析输出
        if arg == "-o":
            if i + 1 >= len(full_args):
                raise ExecError("Can not find output file.")
            context.output = full_args[i + 1]
            return
        i += 1


def expand_response_file(context: Context):
    linker_args = expand_linker_args(context.linker_args)
    full_args = []
    for arg in linker_args:
        # 解析rsp文件
        if arg.startswith("@"):
            rsp_file = Path(arg[1:])
            rsp_args = parse_response_file(rsp_file, context)
            full_args.extend(rsp_args)
            continue
        full_args.append(arg)
    context.full_args = full_args


def expand_linker_args(argv: list[str]) -> list[str]:
    """
    展开 -Wl, 以及 -Xlinker 形式参数
    """
    expanded: list[str] = []
    i = 0

    while i < len(argv):
        arg = argv[i]

        # ----------------------------
        # -Wl,a,b,c
        # ----------------------------
        if arg.startswith("-Wl,"):
            parts = arg[4:].split(",")
            expanded.append("-Wl,")
            expanded.extend(parts)
            i += 1
            continue

        # ----------------------------
        # -Xlinker xxx
        # ----------------------------
        if arg == "-Xlinker":
            if i + 1 >= len(argv):
                raise ExecError("-Xlinker missing argument")
            expanded.append("-Xlinker")
            expanded.append(argv[i + 1])
            i += 2
            continue
        
        expanded.append(arg)
        i += 1
    
    return expanded


def parse_response_file(path: Path, context: Context, depth=0):
    if not path.exists():
        raise ExecError(f"Can not find rsp file: {path.resolve()}.")
    if depth > context.config.lcache_max_rsp_depth:
        raise ExecError("Rsp file nesting too deep.")
    args = shlex.split(path.read_text())
    out = []
    for a in args:
        if a.startswith("@"):
            out.extend(parse_response_file(path.parent / a[1:], context, depth + 1))
        else:
            out.append(a)
    return out


def exec_command(commands: list) -> int:
    log.info(f"Run real link command :  {' '.join(commands)}", console=False)
    result = subprocess.run(commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # 返回码
    ret = result.returncode
    # 标准错误
    stderr = result.stderr.decode()
    if ret != 0:
        log.error(f"Linker failed ({ret}), error is {stderr}", console=True)
    return ret


def update_cache(key: str, storage: Storage, file_hash: list):
    log.info(f"Update local link cache.", console=False)
    storage.store_result(key, file_hash)
    storage.update_lru(key)
    storage.cleanup_cache()


def find_default_library_dirs(context: Context):
    name = Path(context.real_linker).name
    if "gcc" in name or "g++" in name or "clang" in name:
        context.default_lib_dirs = _from_print_search_dirs(context)
    elif "ld" in name:
        context.default_lib_dirs = _from_verbose_linker(context)
    else:
        raise ExecError(f"Can not find default library dirs from linker {context.real_linker}")


def _from_print_search_dirs(context: Context) -> list[Path]:
    compiler = context.real_linker
    proc = subprocess.run(
        [compiler, "-print-search-dirs"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=True,
    )
    for line in proc.stdout.splitlines():
        if not line.startswith("libraries:"):
            continue
        
        _, value = line.split(":", 1)
        value = value.strip()

        if value.startswith("="):
            value = value[1:]
        
        return [Path(p) for p in value.split(os.pathsep) if p]
    
    return []


def _from_verbose_linker(context: Context) -> list[Path]:
    linker = context.real_linker
    proc = subprocess.run(
        [linker, "--verbose"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=True,
    )

    lib_dirs = set()

    for line in proc.stdout.splitlines():
        line = line.strip()

        # ld.bfd / gold / lld 常见格式
        if line.startswith("SEARCH_DIR"):
            start = line.find("(")
            end = line.find(")")
            if start != -1 and end != -1:
                path = line[start + 1:end].strip('"')
                if path.startswith("="):
                    path = path[1:]
                lib_dirs.add(Path(path))

    return list(lib_dirs)


def make_dirs(context: Context):
    Path(context.config.lcache_dir).mkdir(parents=True, exist_ok=True)
    Path(context.config.lcache_lru_dir).mkdir(parents=True, exist_ok=True)
    Path(context.config.lcache_logfile).parent.mkdir(parents=True, exist_ok=True)


# ============================================================
# Main
# ============================================================
def link_cache_process(context: Context) -> int:
    # 校验环境
    check_zstd()
    # 创建工作目录
    make_dirs(context)
    # 查找编译器
    find_compiler(context)
    # 获取编译器默认库文件查找路径
    find_default_library_dirs(context)
    # 打印配置信息
    print_config(context)
    # 截取链接参数
    context.linker_args = context.command_arr[1:]
    log.info(f"Command line: {' '.join(context.command_arr)}", console=False)

    # 展开@rsp文件
    expand_response_file(context)
    # 解析输出文件
    find_output_file(context)
    log.info(f"Output file: {context.output}", console=False)

    hashutil = HashUtil(log, context=context)
    key, file_hash = hashutil.compute_link_hash()
    log.info(f"Result key hash is {key}", console=False)

    storage = Storage(context, log)
    if context.config.lcache_mode.upper() == "UPDATE":
        log.info(f"Cache mode is UPDATE, update cache.", console=False)
        ret = exec_command(context.command_arr)
        if ret == 1:
            return 1
        update_cache(key, storage, file_hash)
        return 0
    
    result_path = storage.get_result_path(key)
    log.info(f"Looking for result file in {result_path}", console=False)

    if result_path.exists():
        log.info(f"Got link cache from {key}", console=False)
        log.info(f"Copying {result_path} to {context.output}", console=False)
        storage.restore_result(key, Path(context.output))
        log.info(f"Update lru file.", console=False)
        storage.update_lru(key)
        log.info(f"LINK_CACHE_HIT", console=False)
        return 0

    log.info(f"Can not find link cache from {result_path}", console=False)
    ret = exec_command(context.command_arr)
    if ret == 1:
        return 1

    if context.config.lcache_mode.upper() == "SEARCH":
        log.info(f"Cache mode is SEARCH, do not update cache.", console=False)
        log.info(f"LINK_CACHE_MISS", console=False)
        return 0

    update_cache(key, storage, file_hash)
    log.info(f"LINK_CACHE_MISS", console=False)
    return 0


def main():
    if len(sys.argv) == 1:
        print_help()
        sys.exit(0)
    
    # 解析参数
    args = sys.argv[1:]
    context = parse_arguments(args)
    global log
    log = Log(context.config.lcache_log_level, context.config.lcache_logfile)
    if len(sys.argv) == 2:
        arg = args[0]
        if arg in ("-v", "--version"):
            print(f"lcache(link cache) version is {context.config.lcache_version}.")
        elif arg.startswith("--metadata-load-key="):
            key = arg.split("=", 1)[1]
            meta_path = os.path.join(context.config.lcache_dir, key[0], key[1], f"{key}.meta")
            print(load_meta(Path(meta_path)))
        else:
            print_help()
        sys.exit(0)
    
    try:
        # 主处理函数
        result = link_cache_process(context)
    except ExecError as e:
        log.error(f"Linker failed, error is {e}, run real command.", console=False)
        log.info(f"LINK_CACHE_MISS", console=False)
        return exec_command(context.command_arr)
    except Exception as e:
        log.error(f"Linker failed, error is {e}, run real command.", console=False)
        log.info(f"LINK_CACHE_MISS", console=False)
        return exec_command(context.command_arr)
    
    return result


if __name__ == "__main__":
    sys.exit(main())