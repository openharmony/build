#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2024 Huawei Device Co., Ltd.
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

import os
import sys
from queue import Queue


class TokenType(object):
    UNKNOWN = 0
    END_OF_FILE = 1
    COMMENT = 2  # comment
    INCLUDE = 3  # include
    STRING = 4   # character string


class Token(object):
    def __init__(self, file_name, token_type, value):
        self.token_type = token_type
        self.value = value
        self.row = 1
        self.col = 1
        self.file_name = file_name

    def clean(self):
        self.token_type = TokenType.UNKNOWN
        self.value = ""
        self.row = 1
        self.col = 1

    def dump(self):
        return "<{}:{}:{}: {},'{}'>".format(self.file_name, self.row, self.col,
                                            self.token_type, self.value)

    def info(self):
        return "{}:{}:{}".format(self.file_name, self.row, self.col)


class Char(object):
    def __init__(self, is_eof, char):
        self.is_eof = is_eof
        self.char = char

    def dump(self):
        return "{%s, %s}" % (self.is_eof, self.char)


class Lexer(object):
    def __init__(self, idl_file_path):
        self.have_peek = False
        with open(idl_file_path, 'r') as idl_file:
            file_info = idl_file.read()
        self.data = file_info
        self.data_len = len(self.data)
        self.read_index = 0
        self.cur_token = Token(os.path.basename(idl_file_path),
                               TokenType.UNKNOWN, "")
        self.cur_row = 1
        self.cur_col = 1

    def peek_char(self, peek_count=0):
        index = self.read_index + peek_count
        if index >= self.data_len:
            return Char(True, '0')
        return Char(False, self.data[index])

    def get_char(self):
        if self.read_index >= self.data_len:
            return Char(True, '0')
        read_index = self.read_index
        self.read_index += 1
        if self.data[read_index] == '\n':
            self.cur_row += 1
            self.cur_col = 1
        else:
            self.cur_col += 1
        return Char(False, self.data[read_index])

    def peek_token(self):
        if not self.have_peek:
            self.read_token()
            self.have_peek = True
        return self.cur_token

    def get_token(self):
        if not self.have_peek:
            self.read_token()
        self.have_peek = False
        return self.cur_token

    def read_token(self):
        self.cur_token.clean()
        while not self.peek_char().is_eof:
            new_char = self.peek_char()
            if new_char.char.isspace():
                self.get_char()
                continue
            self.cur_token.row = self.cur_row
            self.cur_token.col = self.cur_col
            if new_char.char == '#':
                self.read_include()
                return
            if new_char.char == '"':
                self.read_string()
                return
            if new_char.char == '/':
                self.read_comment()
                return
            self.cur_token.value = new_char.char
            self.cur_token.token_type = TokenType.UNKNOWN
            self.get_char()
            return
        self.cur_token.token_type = TokenType.END_OF_FILE

    def read_include(self):
        token_value = []
        token_value.append(self.get_char().char)
        while not self.peek_char().is_eof:
            new_char = self.peek_char()
            if new_char.char.isalpha():
                token_value.append(new_char.char)
                self.get_char()
                continue
            break
        key_str = "".join(token_value)
        if key_str == "#include":
            self.cur_token.token_type = TokenType.INCLUDE
        else:
            self.cur_token.token_type = TokenType.UNKNOWN
        self.cur_token.value = key_str

    def read_string(self):
        token_value = []
        self.get_char()
        while not self.peek_char().is_eof and self.peek_char().char != '"':
            token_value.append(self.get_char().char)

        if self.peek_char().char == '"':
            self.cur_token.token_type = TokenType.STRING
            self.get_char()
        else:
            self.cur_token.token_type = TokenType.UNKNOWN
        self.cur_token.value = "".join(token_value)

    def read_comment(self):
        token_value = []
        token_value.append(self.get_char().char)
        new_char = self.peek_char()
        if not new_char.is_eof:
            if new_char.char == '/':
                self.read_line_comment(token_value)
                return
            elif new_char.char == '*':
                self.read_block_comment(token_value)
                return
        self.cur_token.token_type = TokenType.UNKNOWN
        self.cur_token.value = "".join(token_value)

    def read_line_comment(self, token_value):
        token_value.append(self.get_char().char)
        while not self.peek_char().is_eof:
            new_char = self.get_char()
            if new_char.char == '\n':
                break
            token_value.append(new_char.char)
        self.cur_token.token_type = TokenType.COMMENT
        self.cur_token.value = "".join(token_value)

    def read_block_comment(self, token_value):
        # read *
        token_value.append(self.get_char().char)
        while not self.peek_char().is_eof:
            new_char = self.get_char()
            token_value.append(new_char.char)
            if new_char.char == '*' and self.peek_char().char == '/':
                token_value.append(self.get_char().char)
                break
        value = "".join(token_value)
        if value.endswith("*/"):
            self.cur_token.token_type = TokenType.COMMENT
        else:
            self.cur_token.token_type = TokenType.UNKNOWN
        self.cur_token.value = value


class HcsParser(object):
    def __init__(self):
        self.all_hcs_files = set()
        self.src_queue = Queue()

    # get all hcs files by root hcs file
    def get_hcs_info(self):
        result_str = ""
        all_hcs_files_list = sorted(list(self.all_hcs_files))
        for file_path in all_hcs_files_list:
            result_str += "{}\n".format(file_path)
        return result_str

    def parse(self, root_hcs_file):
        if not os.path.exists(root_hcs_file):
            return
        self.src_queue.put(os.path.abspath(root_hcs_file))
        while not self.src_queue.empty():
            cur_hcs_file = self.src_queue.get()
            self.all_hcs_files.add(cur_hcs_file)
            self.parse_one(cur_hcs_file)

    def parse_one(self, cur_hcs_file_path):
        hcs_file_dir = os.path.dirname(cur_hcs_file_path)
        lex = Lexer(cur_hcs_file_path)
        while lex.peek_token().token_type != TokenType.END_OF_FILE:
            cur_token_type = lex.peek_token().token_type
            if cur_token_type == TokenType.INCLUDE:
                self.parse_include(lex, hcs_file_dir)
            else:
                lex.get_token()

    def parse_include(self, lex, hcs_file_dir):
        lex.get_token()  # include token
        token = lex.peek_token()
        if token.token_type == TokenType.STRING:
            hcs_file_path = os.path.join(hcs_file_dir, token.value)
            # do not parse the hcs file that does not exist
            if not os.path.exists(hcs_file_path):
                return
            self.src_queue.put(os.path.abspath(hcs_file_path))


def check_python_version():
    if sys.version_info < (3, 0):
        raise Exception("Please run with python version >= 3.0")


if __name__ == "__main__":
    check_python_version()
    if len(sys.argv) < 2:
        raise Exception("No hcs source files, please check input")
    all_hcs_files = sys.argv[1:]
    parser = HcsParser()
    for hcs_file in all_hcs_files:
        parser.parse(hcs_file)

    sys.stdout.write(parser.get_hcs_info())
    sys.stdout.flush()
