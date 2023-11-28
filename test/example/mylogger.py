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
        self.suffix_time = current_time

    def emit(self, record):
        try:
            if self.check_base_filename():
                self.build_base_filename()
            FileHandler.emit(self, record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def check_base_filename(self):
        time_tuple = time.localtime()

        if self.suffix_time != time.strftime(self.suffix, time_tuple) or not os.path.exists(
                os.path.abspath(self.filename) + '.' + self.suffix_time):
            return 1
        else:
            return 0

    def build_base_filename(self):
        if self.stream:
            self.stream.close()
            self.stream = None

        if self.suffix_time != "":
            index = self.baseFilename.find("." + self.suffix_time)
            if index == -1:
                index = self.baseFilename.rfind(".")
            self.baseFilename = self.baseFilename[:index]

        current_time_tuple = time.localtime()
        self.suffix_time = time.strftime(self.suffix, current_time_tuple)
        self.baseFilename = os.path.abspath(self.filename) + "." + self.suffix_time

        if not self.delay:
            self.stream = open(self.baseFilename, self.mode, encoding=self.encoding)


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
        with open(config_path, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
            return data
    except Exception as e:
        print(e)
