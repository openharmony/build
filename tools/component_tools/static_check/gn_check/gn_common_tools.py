#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2022 Huawei Device Co., Ltd.
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

import logging
import os
import re
import typing


class GnCommon:
    """
    处理BUILD.gn文件的通用方法
    """

    @staticmethod
    def contains_keywords(key_words: tuple, target: str) -> bool:
        """
        判断target中是否包含key_words中的元素
        """
        for k in key_words:
            if k in target:
                return True
        return False

    @staticmethod
    def find_files(project_path: str,
                   target_filename=None,
                   black_keywords: tuple = tuple(),
                   black_dirs: tuple = tuple()) -> set:
        """
        基于linux的find命令查找文件
        """
        if target_filename is None:
            target_filename = ["BUILD.gn", "*.gni"]
        cmd = "find {}".format(project_path)
        cmd += " -name {} -or -name {}".format(target_filename[0], target_filename[1])
        result_set = set()
        for black_dir in black_dirs:
            bd_path = os.path.join(project_path, black_dir)
            cmd += " -o -path '{}' -prune".format(bd_path)
        output = os.popen(cmd)
        for file in output:
            if GnCommon.contains_keywords(black_keywords, file):
                continue
            result_set.add(file.strip())
        logging.info("total: %s", len(result_set))
        return result_set

    @staticmethod
    def grep_one(grep_pattern: str,
                 grep_path: str,
                 excludes: tuple = tuple(),
                 black_keyword: tuple = tuple(),
                 includes=None,
                 grep_parameter='Ern'):
        """
        调用linux的grep命令，开启了通用的正则匹配
        grep_path：可以是路径，也可以是文件
        没有grep到内容，返回None
        """
        if includes is None:
            includes = ["BUILD.gn", "*.gni"]
        cmd = "grep -{} -s '{}' {}".format(grep_parameter,
                                        grep_pattern, grep_path)
        for include in includes:
            cmd += " --include={}".format(include)
        for exclude in excludes:
            cmd += " --exclude-dir={}".format(exclude)
        if len(black_keyword) != 0:
            cmd += " | grep -Ev '{}'".format("|".join(black_keyword))
        logging.info(cmd)
        result = None
        output = os.popen(cmd).read().strip()
        if len(output) != 0:
            result = output
        return result

    @staticmethod
    def find_paragraph_iter(pattern: str, content: str) -> typing.Iterator:
        """
        匹配所有pattern
        pattern: 要
        example: 匹配ohos_shared_library
        iter = GnCommon.find_paragraph_iter(start_pattern="ohos_shared_library", end_pattern="\}", content=filecontent)
        for i in iter:
            print(i.group())
        caution：如果是嵌套内容，则只能匹配外层的
        """
        ptrn = re.compile(pattern, flags=re.S | re.M)
        result = re.finditer(ptrn, content)
        return result
