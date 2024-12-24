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

import argparse
import json
import os
import sys
from enum import Enum
from os.path import realpath, basename, relpath, join, dirname, exists


class TokenType(Enum):
    UNKNOWN = 0
    COMMENT = 1
    PACKAGE = 2
    IMPORT = 3
    INTERFACE = 4
    CALLBACK = 5
    ID = 6
    END_OF_FILE = 7


class Token:
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

    def info(self):
        return "{}:{}:{}".format(self.file_name, self.row, self.col)


class Char:
    def __init__(self, is_eof, char):
        self.is_eof = is_eof
        self.char = char


class Lexer:
    _key_words = {
        "package": TokenType.PACKAGE,
        "import": TokenType.IMPORT,
        "interface": TokenType.INTERFACE,
        "callback": TokenType.CALLBACK,
    }

    def __init__(self, idl_file_path):
        self.have_peek = False
        with open(idl_file_path, 'r') as idl_file:
            file_info = idl_file.read()
        self.data = file_info
        self.data_len = len(self.data)
        self.read_index = 0
        self.cur_token = Token(basename(idl_file_path), TokenType.UNKNOWN, "")
        self.cur_row = 1
        self.cur_col = 1

    def peek_char(self, peek_count=0):
        index = self.read_index + peek_count
        if index >= self.data_len:
            return Char(True, '0')
        return Char(False, self.data[index])

    def next_char(self):
        return self.peek_char(1)

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
            c = self.peek_char()
            if c.char.isspace():
                self.get_char()
                continue
            self.cur_token.row = self.cur_row
            self.cur_token.col = self.cur_col
            if c.char.isalpha() or c.char == '_' or (c.char == '.' and self.next_char().char == '.'):
                self.read_id()
                return
            if c.char == '/':
                self.read_comment()
                return
            self.cur_token.value = c.char
            self.cur_token.token_type = TokenType.UNKNOWN
            self.get_char()
            return
        self.cur_token.token_type = TokenType.END_OF_FILE

    def read_id(self):
        token_value = [self.get_char().char]
        while not self.peek_char().is_eof:
            c = self.peek_char()
            if c.char.isalpha() or c.char.isdigit() or c.char == '_' or c.char == '.' or c.char == '/':
                token_value.append(c.char)
                self.get_char()
                continue
            break

        key = "".join(token_value)
        if key in self._key_words.keys():
            self.cur_token.token_type = self._key_words[key]
        else:
            self.cur_token.token_type = TokenType.ID
        self.cur_token.value = key

    def read_comment(self):
        token_value = [self.get_char().char]
        c = self.peek_char()
        if not c.is_eof:
            if c.char == '/':
                self.read_line_comment(token_value)
                return
            elif c.char == '*':
                self.read_block_comment(token_value)
                return
        self.cur_token.token_type = TokenType.UNKNOWN
        self.cur_token.value = "".join(token_value)

    def read_line_comment(self, token_value):
        token_value.append(self.get_char().char)
        while not self.peek_char().is_eof:
            c = self.get_char()
            if c.char == '\n':
                break
            token_value.append(c.char)
        self.cur_token.token_type = TokenType.COMMENT
        self.cur_token.value = "".join(token_value)

    def read_block_comment(self, token_value):
        token_value.append(self.get_char().char)
        while not self.peek_char().is_eof:
            c = self.get_char()
            token_value.append(c.char)
            if c.char == '*' and self.peek_char().char == '/':
                token_value.append(self.get_char().char)
                break

        value = "".join(token_value)
        if value.endswith("*/"):
            self.cur_token.token_type = TokenType.COMMENT
        else:
            self.cur_token.token_type = TokenType.UNKNOWN
        self.cur_token.value = value


# module info of all idl
class BuildInfo:
    include_dirs = set()
    out_dir = ""
    sources = []
    proxy_sources = []
    stub_sources = []

    @staticmethod
    def json_info():
        include_dirs_ret = sorted(list(BuildInfo.include_dirs))
        BuildInfo.sources.sort()
        BuildInfo.proxy_sources.sort()
        BuildInfo.stub_sources.sort()

        result = {
            "include_dirs": include_dirs_ret,
            "out_dir": BuildInfo.out_dir,
            "sources": BuildInfo.sources,
            "proxy_sources": BuildInfo.proxy_sources,
            "stub_sources": BuildInfo.stub_sources,
        }
        return json.dumps(result, indent=4, separators=(',', ':'))


class Option:
    language = "cpp"
    root_path = ""  # absolute root path of this project
    gen_dir = ""  # absolute path of the directory where the file is generated
    main_file_path = ""  # absolute path of the interface file
    main_file_dir = ""  # absolute path of interface file directory
    idl_sources = []

    @staticmethod
    def load(opt_args):
        Option.language = opt_args.language
        Option.root_path = opt_args.root_path

        if opt_args.out == "":
            raise Exception("the gen_dir '{}' is empty, please check input".format(opt_args.out))
        else:
            Option.gen_dir = realpath(opt_args.out)

        if len(opt_args.file) == 0:
            raise Exception("the idl sources is empty, please check input")
        else:
            Option.idl_sources = opt_args.file
            Option.main_file_path = realpath(opt_args.file[0])
            Option.main_file_dir = realpath(dirname(opt_args.file[0]))


class IdlType(Enum):
    INTERFACE = 1
    CALLBACK = 2
    TYPES = 3


# file detail of idl file
class IdlDetail:
    def __init__(self, path):
        self.idl_type = IdlType.TYPES
        self.imports = []  # imported IDL file
        self.file_path = realpath(path)  # absolute file path
        self.file_name = basename(path)  # file name
        self.file_dir = realpath(dirname(path))  # absolute path of the directory where the file is located
        self.name = self.file_name.split('.')[0]  # file name without suffix

    def full_name(self):
        return self.file_path


class IdlParser:
    @staticmethod
    def get_sources(all_idl_details: dict[str, IdlDetail], generator: "CodeGen"):
        BuildInfo.include_dirs.add(CodeGen.convert_to_out_dir(Option.gen_dir))
        for idl_detail in all_idl_details.values():
            sources, proxy_sources, sub_sources = generator.gen_code(idl_detail)
            BuildInfo.sources.extend(sources)
            BuildInfo.proxy_sources.extend(proxy_sources)
            BuildInfo.stub_sources.extend(sub_sources)

    @staticmethod
    def parse_callback(lex, idl_detail: IdlDetail):
        lex.get_token()
        idl_detail.idl_type = IdlType.CALLBACK

    @staticmethod
    def parse_interface(lex, idl_detail: IdlDetail):
        lex.get_token()
        if lex.peek_token().token_type != TokenType.ID:
            token = lex.peek_token()
            raise Exception("{}: expected interface name before '{}'".format(token.info(), token.value))

        lex.get_token()
        if idl_detail.idl_type != IdlType.CALLBACK:
            idl_detail.idl_type = IdlType.INTERFACE

    def parse_import(self, lex, all_idl_details: dict[str, IdlDetail], idl_detail: IdlDetail):
        lex.get_token()
        token = lex.peek_token()
        if token.token_type != TokenType.ID:
            raise Exception("{}: expected package name before '{}'".format(token.info(), token.value))

        import_name = lex.get_token().value
        idl_file = realpath(join(idl_detail.file_dir, import_name + ".idl"))
        if not exists(idl_file):
            raise Exception("{}: import file '{}' not found".format(token.info(), idl_file))

        # Recursive parsing the imported idl files
        self.parse_one(all_idl_details, idl_file)

    def parse(self):
        all_idl_details: dict[str, IdlDetail] = {}
        for idl_file in Option.idl_sources:
            self.parse_one(all_idl_details, idl_file)
        self.get_build_info(all_idl_details)

    def parse_one(self, all_idl_details: dict[str, IdlDetail], file_path):
        idl_detail = IdlDetail(file_path)
        if idl_detail.full_name() in all_idl_details:
            return

        lex = Lexer(file_path)
        while lex.peek_token().token_type != TokenType.END_OF_FILE:
            cur_token_type = lex.peek_token().token_type
            if cur_token_type == TokenType.IMPORT:
                self.parse_import(lex, all_idl_details, idl_detail)
            elif cur_token_type == TokenType.CALLBACK:
                self.parse_callback(lex, idl_detail)
            elif cur_token_type == TokenType.INTERFACE:
                self.parse_interface(lex, idl_detail)
            else:
                lex.get_token()

        all_idl_details[idl_detail.full_name()] = idl_detail

    def get_build_info(self, all_idl_details: dict[str, IdlDetail]):
        generator = CodeGenFactory.create_code_generate()
        if generator is None:
            return

        BuildInfo.out_dir = CodeGen.convert_to_out_dir(Option.gen_dir)
        self.get_sources(all_idl_details, generator)


# generate code file info
class CodeGen:
    @staticmethod
    def str_to_snake_case(s):
        under_line = '_'
        result = []
        name_len = len(s)
        for index in range(name_len):
            cur_char = s[index]
            if cur_char.isupper():
                if index > 1:
                    result.append(under_line)
                result.append(cur_char.lower())
            else:
                result.append(cur_char)
        return "".join(result)

    @staticmethod
    def get_proxy_name(name):
        temp_name = CodeGen.str_to_snake_case(name)
        return "{}_proxy".format(temp_name)

    @staticmethod
    def get_stub_name(name):
        temp_name = CodeGen.str_to_snake_case(name)
        return "{}_stub".format(temp_name)

    @staticmethod
    def get_file_names(idl_detail: IdlDetail):
        interface_name = ""
        proxy_name = ""
        stub_name = ""
        types_name = ""

        if idl_detail.idl_type == IdlType.TYPES:
            types_name = CodeGen.str_to_snake_case(idl_detail.name)
            return interface_name, proxy_name, stub_name, types_name

        base_name = idl_detail.name[1:] if idl_detail.name.startswith("I") else idl_detail.name
        interface_name = CodeGen.str_to_snake_case(idl_detail.name)
        proxy_name = CodeGen.get_proxy_name(base_name)
        stub_name = CodeGen.get_stub_name(base_name)
        return interface_name, proxy_name, stub_name, types_name

    @staticmethod
    def header_file(file_dir, name):
        return join(file_dir, "{}.h".format(name))

    @staticmethod
    def cpp_source_file(file_dir, name):
        return join(file_dir, "{}.cpp".format(name))

    @staticmethod
    def convert_to_out_dir(path):
        # convert the path to a relative path based on the root path of this project,
        # this relative path starts with two separators
        return os.sep + os.sep + relpath(path, Option.root_path)

    def gen_code(self, idl_detail: IdlDetail):
        return [], [], []


# generate ipc cpp code file information
class IpcCppCodeGen(CodeGen):
    def gen_code(self, idl_detail: IdlDetail):
        # relative path of the current file to the interface file
        relative_path = relpath(idl_detail.file_dir, Option.main_file_dir)
        out_dir = self.convert_to_out_dir(realpath(join(Option.gen_dir, relative_path)))
        sources = []
        proxy_sources = []
        stub_sources = []
        interface_name, proxy_name, stub_name, types_name = self.get_file_names(idl_detail)
        iface_header_file = self.header_file(out_dir, interface_name)
        proxy_header_file = self.header_file(out_dir, proxy_name)
        proxy_source_file = self.cpp_source_file(out_dir, proxy_name)
        stub_header_file = self.header_file(out_dir, stub_name)
        stub_source_file = self.cpp_source_file(out_dir, stub_name)
        types_header_file = self.header_file(out_dir, types_name)
        types_source_file = self.cpp_source_file(out_dir, types_name)

        if idl_detail.idl_type == IdlType.INTERFACE:
            sources.extend([
                iface_header_file, proxy_header_file, proxy_source_file,
                stub_header_file, stub_source_file
            ])
            proxy_sources.append(proxy_source_file)
            stub_sources.append(stub_source_file)
        elif idl_detail.idl_type == IdlType.CALLBACK:
            sources.extend([
                iface_header_file, proxy_header_file, proxy_source_file,
                stub_header_file, stub_source_file
            ])
            proxy_sources.append(stub_source_file)
            stub_sources.append(proxy_source_file)
        elif idl_detail.idl_type == IdlType.TYPES:
            sources.extend([types_header_file, types_source_file])
            proxy_sources.append(types_source_file)
            stub_sources.append(types_source_file)

        return sources, proxy_sources, stub_sources


class CodeGenFactory:
    action_config = {
        "c": None,
        "cpp": IpcCppCodeGen()
    }

    @staticmethod
    def create_code_generate() -> CodeGen:
        generator = CodeGenFactory.action_config.get(Option.language)
        if generator is None:
            raise Exception("The '{}' language is not support".format(Option.language))
        return generator


def check_python_version():
    if sys.version_info < (3, 0):
        raise Exception("Please run with python version >= 3.0")


if __name__ == "__main__":
    check_python_version()

    # load options
    option_parser = argparse.ArgumentParser(description="Tools for generating compilation information of idl files")
    option_parser.add_argument("-l", "--language", choices=["c", "cpp"], default="cpp",
                               help="language of generating code")
    option_parser.add_argument("-o", "--out", required=True, help="directory of generate file")
    option_parser.add_argument("-f", "--file", required=True, action="append", help="the idl files")
    option_parser.add_argument("-r", "--root-path", required=True,
                               help="absolute root path of this project")
    Option.load(option_parser.parse_args())

    # parse idl files
    idl_parser = IdlParser()
    idl_parser.parse()

    # output generating files as JSON
    sys.stdout.write(BuildInfo.json_info())
    sys.stdout.flush()
