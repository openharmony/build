#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
# Description: lcache config main entry

from dataclasses import dataclass


@dataclass
class Config:
    lcache_version: str = "1.0.0"
    lcache_max_size: int = None
    lcache_max_rsp_depth: int = None
    lcache_allow_env: str = None
    lcache_compiler_check: str = None
    lcache_mode: str = None
    lcache_log_level: str = None
    lcache_dir: str = None
    lcache_lru_dir: str = None
    lcache_logfile: str = None
    lcache_config_file: str = None