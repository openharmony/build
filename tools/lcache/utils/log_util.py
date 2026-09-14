#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
# Description: lcache log util main entry

import os
from datetime import datetime

LEVELS = {"ERROR": -2, "WARN": -1, "QUIET": 0, "INFO": 1, "DEBUG": 2}


class Log():
    def __init__(self, level: str, file: str) -> None:
        self.log_level = LEVELS.get(level, 1)
        self.log_file = file
        self.pid = os.getpid()

    def error(self, msg: str, *, console=False):
        if self.log_level < LEVELS["ERROR"]:
            return
        self.log_print(msg, "ERROR", console=console)

    def warn(self, msg: str, *, console=False):
        if self.log_level < LEVELS["WARN"]:
            return
        self.log_print(msg, "WARN", console=console)

    def quiet(self, msg: str, *, console=False):
        if self.log_level < LEVELS["QUIET"]:
            return
        self.log_print(msg, "QUIET", console=console)

    def info(self, msg: str, *, console=False):
        if self.log_level < LEVELS["INFO"]:
            return
        self.log_print(msg, "INFO", console=console)

    def debug(self, msg: str, *, console=False):
        if self.log_level < LEVELS["DEBUG"]:
            return
        self.log_print(msg, "DEBUG", console=console)
        
    def log_print(self, msg: str, level: str, console=False):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        line = f"[{ts}] [{self.pid}] [{level}] {msg}\n"
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(line)
        if console:
            print(f"[link-cache:{self.pid}] [{level}] {msg}")