#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
# Description: lcache context main entry

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

from config import Config


@dataclass
class Context:
    _instance = None

    output: str = None
    work_dir: str = Path("/").absolute().anchor
    real_linker: str = None
    full_args: list[str] = None
    linker_args: list[str] = None
    command_arr: list[str] = None
    default_lib_dirs: list[Path] = None

    config: Config = field(default_factory=Config)