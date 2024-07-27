#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) 2023 Huawei Device Co., Ltd.
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


import codecs
import sys
import time
import os
import json
import logging.config
import stat
from logging import FileHandler


class SafeFileHandler(FileHandler):
    def __init__(self, filename, mode="a", encoding="utf-8", delay=0, suffix="%Y-%m-%d_%H"):
        if codecs is None:
            encoding = None
        current_time = time.strftime(suffix, time.localtime())
        FileHandler.__init__(self, filename + "." + current_time, mode, encoding, delay)

        self.filename = os.fspath(filename)

        self.mode = mode
        self.encoding = encoding
        self.suffix = suffix
        self.suftime = current_time

    def emit(self, record):
        try:
            if self.parse_file_name():
                self.gen_file_name()
            FileHandler.emit(self, record)
        except Exception as e:
            print(e)
            self.handleError(record)

    def parse_file_name(self):
        time_tuple = time.localtime()

        if self.suftime != time.strftime(self.suffix, time_tuple) or not os.path.exists(
                os.path.abspath(self.filename) + '.' + self.suftime):
            return 1
        else:
            return 0

    def gen_file_name(self):
        if self.stream:
            self.stream.close()
            self.stream = None

        if self.suftime != "":
            index = self.baseFilename.find("." + self.suftime)
            if index == -1:
                index = self.baseFilename.rfind(".")
            self.baseFilename = self.baseFilename[:index]

        cur_time = time.localtime()
        self.suftime = time.strftime(self.suffix, cur_time)
        self.baseFilename = os.path.abspath(self.filename) + "." + self.suftime

        if not self.delay:
            with os.fdopen(os.open(self.baseFilename, os.O_WRONLT | os.CREAT | os.O_EXCL,
                           stat.S_IWUSR | stat.S_IRUSR), self.mode, encoding=self.encoding) as f:
                self.stream = f


def get_logger(class_name, level="info"):
    formate = "%(asctime)s -%(levelname)s - %(name)s - %(message)s"
    formatter = logging.Formatter(formate)
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "log")
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    tfr_handler = SafeFileHandler(os.path.join(log_path, class_name + ".log"))
    tfr_handler.setFormatter(formatter)

    sh = logging.StreamHandler()
    sh.setFormatter(formatter)

    logger = logging.getLogger(class_name)
    logger.addHandler(tfr_handler)
    logger.addHandler(sh)

    if level == 'info':
        logger.setLevel(logging.INFO)
    elif level == 'error':
        logger.setLevel(logging.ERROR)
    return logger


def parse_json():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_example.json")
    try:
        with os.fdopen(os.open(config_path, os.O_WRONLT | os.CREAT | os.O_EXCL,
                       stat.S_IWUSR | stat.S_IRUSR), "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
            return data
    except Exception as e:
        print(e)
    return None

