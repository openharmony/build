#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2021-2023 Huawei Device Co., Ltd.
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
import re
import sys


class TokenType(object):
    UNKNOWN = 0
    COMMENT = 1
    PACKAGE = 2
    IMPORT = 3
    INTERFACE = 4
    CALLBACK = 5
    ID = 6
    END_OF_FILE = 7


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
            if new_char.char.isalpha() or new_char.char == '_':
                self.read_id()
                return
            if new_char.char == '/':
                self.read_comment()
                return
            self.cur_token.value = new_char.char
            self.cur_token.token_type = TokenType.UNKNOWN
            self.get_char()
            return
        self.cur_token.token_type = TokenType.END_OF_FILE

    def read_id(self):
        token_value = []
        token_value.append(self.get_char().char)
        while not self.peek_char().is_eof:
            new_char = self.peek_char()
            if new_char.char.isalpha() or new_char.char.isdigit(
            ) or new_char.char == '_' or new_char.char == '.':
                token_value.append(new_char.char)
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


# module info of all idl
class ModuleInfo(object):
    package = ""
    version = ""
    include_dirs = set()
    out_dir = ""
    sources = []
    proxy_sources = []
    stub_sources = []
    proxy_deps = []
    stub_deps = []
    header_deps = []

    @staticmethod
    def json_info():
        include_dirs_ret = sorted(list(ModuleInfo.include_dirs))
        ModuleInfo.sources.sort()
        ModuleInfo.proxy_sources.sort()
        ModuleInfo.stub_sources.sort()

        result = {
            "package": ModuleInfo.package,
            "version": ModuleInfo.version,
            "include_dirs": include_dirs_ret,
            "out_dir": ModuleInfo.out_dir,
            "sources": ModuleInfo.sources,
            "proxy_sources": ModuleInfo.proxy_sources,
            "stub_sources": ModuleInfo.stub_sources,
            "proxy_deps": ModuleInfo.proxy_deps,
            "stub_deps": ModuleInfo.stub_deps,
            "header_deps": ModuleInfo.header_deps,
        }
        return json.dumps(result)


class Option(object):
    system = "full"
    mode = "ipc"
    language = "cpp"
    gen_dir = ""
    root_package = ""
    root_path = ""
    idl_sources = []
    imports = []

    @staticmethod
    def load(opt_args):
        Option.system = opt_args.system
        Option.mode = opt_args.mode
        Option.language = opt_args.language

        if opt_args.out == "":
            raise Exception(
                "the gen_dir '{}' is empty, please check input".format(
                    opt_args.out))
        else:
            Option.gen_dir = opt_args.out

        map_result = opt_args.root.split(":")
        if len(map_result) != 2:
            raise Exception(
                "the package path '{}' is valid, please check input".format(
                    opt_args.root))
        else:
            Option.root_package = map_result[0]
            Option.root_path = map_result[1]

        if len(opt_args.file) == 0:
            raise Exception("the idl sources is empty, please check input")
        else:
            Option.idl_sources = opt_args.file

        if opt_args.imports is not None:
            Option.imports = opt_args.imports

    @staticmethod
    def dump():
        result = {
            "system": Option.system,
            "kernel": Option.kernel,
            "mode": Option.mode,
            "language": Option.language,
            "gen_dir": Option.gen_dir,
            "root_package": Option.root_package,
            "root_path": Option.root_path,
            "idl_sources": Option.idl_sources
        }
        return json.dumps(result)


class IdlType(object):
    INTERFACE = 1
    CALL_INTERFACE = 2
    CALLBACK = 3
    TYPES = 4


# file detail of idl file
class IdlDetail(object):
    def __init__(self, path):
        self.package = ""
        self.idl_type = IdlType.TYPES
        self.imports = []
        self.file_path = path

        self.file_name = os.path.basename(self.file_path)
        self.name = self.file_name.split('.')[0]

    # package + file name, like 'ohos.hdi.foo.v1_0.IFoo'
    def full_name(self):
        return "{}.{}".format(self.package, self.name)

    def dump(self):
        result = {
            "package": self.package,
            "type": self.idl_type,
            "imports": self.imports,
            "path": self.file_path
        }
        return json.dumps(result)


class IdlParser(object):
    def parse(self, ):
        all_idl_details = {}
        if Option.language == "c":
            self.parse_c_idl_files(all_idl_details)
            self.parse_deps(all_idl_details)
            self.parse_module_info(all_idl_details)
            return

        for idl_file in Option.idl_sources:
            idl_detail = self.parse_one(idl_file)
            all_idl_details[idl_detail.full_name()] = idl_detail
        self.parse_deps(all_idl_details)
        self.parse_module_info(all_idl_details)

    def parse_one(self, file_path):
        cur_idl_detail = IdlDetail(file_path)
        lex = Lexer(file_path)
        while lex.peek_token().token_type != TokenType.END_OF_FILE:
            cur_token_type = lex.peek_token().token_type
            if cur_token_type == TokenType.PACKAGE:
                self.parse_package(lex, cur_idl_detail)
            elif cur_token_type == TokenType.IMPORT:
                self.parse_import(lex, cur_idl_detail)
            elif cur_token_type == TokenType.CALLBACK:
                cur_idl_detail.idl_type = IdlType.CALLBACK
                lex.get_token()
            elif cur_token_type == TokenType.INTERFACE:
                self.parse_interface(lex, cur_idl_detail)
            else:
                lex.get_token()
        return cur_idl_detail

    def parse_c_idl_files(self, all_idl_details):
        idl_sources_set = set()
        idl_queue = []
        for idl_file in Option.idl_sources:
            idl_queue.append(idl_file)
        while len(idl_queue) > 0:
            cur_idl_file = idl_queue.pop(0)
            if cur_idl_file in idl_sources_set:
                continue
            idl_sources_set.add(cur_idl_file)
            self.parse_c_idl_files_import(cur_idl_file, idl_queue)
        for idl_file in idl_sources_set:
            idl_detail = self.parse_one(idl_file)
            all_idl_details[idl_detail.full_name()] = idl_detail
        self.merged_idl_details(all_idl_details)

    def parse_c_idl_files_import(self, file_path, idl_queue):
        lex = Lexer(file_path)
        while lex.peek_token().token_type != TokenType.END_OF_FILE:
            cur_token_type = lex.peek_token().token_type
            if cur_token_type == TokenType.IMPORT:
                lex.get_token()
                token = lex.peek_token()
                if lex.peek_token().token_type != TokenType.ID:
                    raise Exception("{}: expected package name before '{}'".format(
                        token.info(), token.value))
                idl_queue.append(
                    CodeGen.get_package_path(token.value) + ".idl")
            lex.get_token()

    def update_imports(self, all_idl_details, idl_detail, merged_details):
        if idl_detail.full_name() not in merged_details:
            imports = []
            for import_name in idl_detail.imports:
                import_idl = all_idl_details[import_name]
                if import_idl.full_name() in imports:
                    continue
                if import_idl.full_name() != idl_detail.full_name():
                    imports.append(import_idl.full_name())
            idl_detail.imports = imports
            merged_details[idl_detail.full_name()] = idl_detail
        else:
            for import_name in idl_detail.imports:
                import_idl = all_idl_details[import_name]
                merged_detail = merged_details[idl_detail.full_name()]
                if import_idl.full_name() in merged_detail.imports:
                    continue
                if import_idl.full_name() != idl_detail.full_name():
                    merged_detail.imports.append(import_idl.full_name())

    def merged_idl_details(self, all_idl_details):
        merged_details = {}
        source_idl_detail = self.parse_one(Option.idl_sources[0])
        for _, idl_detail in all_idl_details.items():
            idl_detail.package = source_idl_detail.package
            idl_detail.version = source_idl_detail.version
        for _, idl_detail in all_idl_details.items():
            self.update_imports(all_idl_details, idl_detail, merged_details)
        all_idl_details.clear()
        for key, value in merged_details.items():
            all_idl_details[key] = value

    def parse_package(self, lex, cur_idl_detail):
        lex.get_token()  # package token
        token = lex.peek_token()
        if token.token_type != TokenType.ID:
            raise Exception("{}: expected package name before '{}'".format(
                token.info(), token.value))
        token = lex.get_token()
        if not self.parse_version(token.value, cur_idl_detail):
            raise Exception("{}: failed to parse package name '{}'".format(
                token.info(), token.vlaue))

    def parse_version(self, package_name, cur_idl_detail):
        result = re.findall(r'\w+(?:\.\w+)*\.[V|v](\d+)_(\d+)', package_name)
        if len(result) > 0:
            cur_idl_detail.package = package_name
            major_version = result[0][0]
            minor_version = result[0][1]
            cur_idl_detail.version = "{}.{}".format(major_version, minor_version)
            return True
        return False

    def parse_import(self, lex, cur_idl_detail):
        lex.get_token()  # import token
        if lex.peek_token().token_type != TokenType.ID:
            token = lex.peek_token()
            raise Exception("{}: expected package name before '{}'".format(
                token.info(), token.value))
        cur_idl_detail.imports.append(lex.get_token().value)

    def parse_interface(self, lex, cur_idl_detail):
        lex.get_token()  # interface token
        if lex.peek_token().token_type != TokenType.ID:
            token = lex.peek_token()
            raise Exception("{}: expected interface name before '{}'".format(
                token.info(), token.value))
        token = lex.get_token()
        interface_name = token.value
        if interface_name != cur_idl_detail.name:
            raise Exception(
                "{}: interface name '{}' does not match file name '{}'".format(
                    token.info(), interface_name, cur_idl_detail.file_name))
        if cur_idl_detail.idl_type != IdlType.CALLBACK:
            cur_idl_detail.idl_type = IdlType.INTERFACE

    def parse_deps(self, all_idl_details):
        for detail_name, idl_detail in all_idl_details.items():
            self.query_and_update_idl_type(idl_detail, all_idl_details)

    # update interface idl file type if the file import by other idl file
    def query_and_update_idl_type(self, idl_detail, all_idl_details):
        for other_name, other_detail in all_idl_details.items():
            if idl_detail.full_name() == other_name:
                continue
            if self.imported_by_other_idl(idl_detail, other_detail) and idl_detail.idl_type == IdlType.INTERFACE:
                idl_detail.idl_type = IdlType.CALL_INTERFACE
                break

    def imported_by_other_idl(self, idl_detail, other_detail):
        for import_name in other_detail.imports:
            if idl_detail.full_name() == import_name:
                return True
        return False

    def parse_module_info(self, all_idl_details):
        generator = CodeGenFactory.create_code_generate()
        if generator is None:
            return
        ModuleInfo.out_dir = Option.gen_dir
        self.parse_sources(all_idl_details, generator)
        ModuleInfo.proxy_deps, ModuleInfo.stub_deps, ModuleInfo.header_deps = CodeGen.get_lib_deps(Option.imports)

    def parse_sources(self, all_idl_details, generator):
        ModuleInfo.include_dirs.add(Option.gen_dir)
        for idl_detail in all_idl_details.values():
            ModuleInfo.package = idl_detail.package
            ModuleInfo.version = idl_detail.version
            ModuleInfo.include_dirs.add(
                generator.parse_include_dirs(idl_detail.package))

            sources, proxy_sources, sub_sources = generator.gen_code(
                idl_detail)
            ModuleInfo.sources.extend(sources)
            ModuleInfo.proxy_sources.extend(proxy_sources)
            ModuleInfo.stub_sources.extend(sub_sources)


# generate code file info of hdi
class CodeGen(object):
    # package is 'ohos.hdi.foo.v1_0'
    # -r ohos.hdi:./interface
    # sub_package is foo.v1_0
    @staticmethod
    def get_sub_package(package):
        if package.startswith(Option.root_package):
            root_package_len = len(Option.root_package)
            return package[root_package_len + 1:]
        return package

    @staticmethod
    def get_package_path(package):
        package_path = ""
        if package.startswith(Option.root_package):
            root_package_len = len(Option.root_package)
            sub_package = package[root_package_len:]
            sub_package_path = sub_package.replace(".", os.sep)
            package_path = "{}{}".format(Option.root_path, sub_package_path)
        else:
            raise Exception("find root package '{}' failed in '{}'".format(
                Option.root_package, package))

        return package_path

    @staticmethod
    def get_version(package):
        major_version = 0
        minor_version = 0
        result = re.findall(r'\w+(?:\.\w+)*\.[V|v](\d+)_(\d+)', package)
        if len(result) > 0:
            major_version = result[0][0]
            minor_version = result[0][1]
        return major_version, minor_version

    # transalte package name to include directory
    @staticmethod
    def parse_include_dirs(package):
        sub_package = CodeGen.get_sub_package(package)
        last_point_index = sub_package.rfind('.')
        package_without_version = sub_package[:last_point_index]
        package_dir_without_version = package_without_version.replace(
            '.', os.sep)
        return os.path.join(Option.gen_dir, package_dir_without_version)

    # translate package name to directory
    @staticmethod
    def get_source_file_dir(package):
        sub_package = CodeGen.get_sub_package(package)
        sub_package_dir = "{}{}".format(sub_package.replace('.', os.sep),
                                        os.sep)
        return os.path.join(Option.gen_dir, sub_package_dir)

    # translate idl file name to c/c++ file name
    @staticmethod
    def translate_file_name(file_name):
        under_line = '_'
        result = []
        name_len = len(file_name)
        for index in range(name_len):
            cur_char = file_name[index]
            if cur_char.isupper():
                if index > 1:
                    result.append(under_line)
                result.append(cur_char.lower())
            else:
                result.append(cur_char)
        return "".join(result)

    @staticmethod
    def translate_proxy_name(base_name):
        temp_name = "{}Proxy".format(base_name)
        return CodeGen.translate_file_name(temp_name)

    @staticmethod
    def translate_stub_name(base_name):
        temp_name = "{}Stub".format(base_name)
        return CodeGen.translate_file_name(temp_name)

    @staticmethod
    def translate_service_name(base_name):
        temp_name = "{}Service".format(base_name)
        return CodeGen.translate_file_name(temp_name)

    @staticmethod
    def translate_driver_name(base_name):
        temp_name = "{}Driver".format(base_name)
        return CodeGen.translate_file_name(temp_name)

    @staticmethod
    def get_type_names(name):
        base_name = CodeGen.translate_file_name(name)
        return base_name

    # translate idl file name to c/c++ file name
    # for example, IFoo -> ifoo, foo_proxy, foo_stub, foo_service, foo_driver, foo
    @staticmethod
    def get_file_names(idl_detail):
        interface_name = ""
        proxy_name = ""
        stub_name = ""
        service_name = ""
        driver_name = ""
        types_name = ""

        if idl_detail.idl_type == IdlType.TYPES:
            types_name = CodeGen.get_type_names(idl_detail.name)
            return interface_name, proxy_name, stub_name, service_name, driver_name, types_name

        base_name = idl_detail.name[1:] if idl_detail.name.startswith(
            "I") else idl_detail.name
        interface_name = CodeGen.translate_file_name(idl_detail.name)
        proxy_name = CodeGen.translate_proxy_name(base_name)
        stub_name = CodeGen.translate_stub_name(base_name)
        service_name = CodeGen.translate_service_name(base_name)
        driver_name = CodeGen.translate_driver_name(base_name)
        if idl_detail.idl_type == IdlType.INTERFACE:
            driver_name = CodeGen.translate_driver_name(base_name)
        return interface_name, proxy_name, stub_name, service_name, driver_name, types_name

    @staticmethod
    def header_file(file_dir, name):
        return os.path.join(file_dir, "{}.h".format(name))

    @staticmethod
    def c_source_file(file_dir, name):
        return os.path.join(file_dir, "{}.c".format(name))

    @staticmethod
    def cpp_source_file(file_dir, name):
        return os.path.join(file_dir, "{}.cpp".format(name))

    @staticmethod
    def get_import(imp):
        package = ""
        module_name = ""
        imp_result = imp.split(":")
        if len(imp_result) == 2:
            package = imp_result[0]
            module_name = imp_result[1]
        return package, module_name

    # get lib deps from imports
    @staticmethod
    def get_lib_deps(imports):
        proxy_deps = []
        stub_deps = []
        header_deps = []
        for imps in imports:
            package, module_name = CodeGen.get_import(imps)
            package_path = CodeGen.get_package_path(package)
            major_version, minor_version = CodeGen.get_version(package)
            proxy_lib_name = "lib{}_proxy_{}.{}".format(module_name, major_version, minor_version)
            stub_lib_name = "lib{}_stub_{}.{}".format(module_name, major_version, minor_version)
            header_config = "{}_idl_headers_{}.{}".format(module_name, major_version, minor_version)
            proxy_lib_dep = "{}:{}".format(package_path, proxy_lib_name)
            stub_lib_dep = "{}:{}".format(package_path, stub_lib_name)
            header_dep = "{}:{}".format(package_path, header_config)
            proxy_deps.append(proxy_lib_dep)
            stub_deps.append(stub_lib_dep)
            header_deps.append(header_dep)
        return proxy_deps, stub_deps, header_deps

    def gen_code(self, idl_detail):
        idl_detail
        return [], [], []


class LowCCodeGen(CodeGen):
    def gen_code(self, idl_detail):
        file_dir = self.get_source_file_dir(idl_detail.package)
        sources = []
        interface_name, _, _, service_name, driver_name, types_name = self.get_file_names(idl_detail)
        if idl_detail.idl_type == IdlType.TYPES:
            header_file = self.header_file(file_dir, types_name)
            sources.append(header_file)
        if idl_detail.idl_type == IdlType.INTERFACE:
            header_file = self.header_file(file_dir, interface_name)
            service_header_file = self.header_file(file_dir, service_name)
            service_source_file = self.c_source_file(file_dir, service_name)
            driver_source_file = self.c_source_file(file_dir, driver_name)
            sources.extend([header_file, service_header_file, service_source_file, driver_source_file])
        return sources, [], []


class LowCppCodeGen(CodeGen):
    def gen_code(self, idl_detail):
        file_dir = self.get_source_file_dir(idl_detail.package)
        sources = []
        interface_name, _, _, service_name, driver_name, types_name = self.get_file_names(idl_detail)
        if idl_detail.idl_type == IdlType.TYPES:
            header_file = self.header_file(file_dir, types_name)
            sources.append(header_file)
        if idl_detail.idl_type == IdlType.INTERFACE:
            header_file = self.header_file(file_dir, interface_name)
            service_header_file = self.header_file(file_dir, service_name)
            service_source_file = self.cpp_source_file(file_dir, service_name)
            driver_source_file = self.cpp_source_file(file_dir, driver_name)
            sources.extend([header_file, service_header_file, service_source_file, driver_source_file])
        return sources, [], []


# generate kernel c code file info of hdi
class KernelCodeGen(CodeGen):
    def gen_code(self, idl_detail):
        file_dir = self.get_source_file_dir(idl_detail.package)
        sources = []
        proxy_sources = []
        stub_sources = []
        interface_name, proxy_name, stub_name, service_name, driver_name, types_name = self.get_file_names(
            idl_detail)
        if idl_detail.idl_type == IdlType.TYPES:
            header_file = self.header_file(file_dir, types_name)
            source_file = self.c_source_file(file_dir, types_name)
            sources.extend([header_file, source_file])
            proxy_sources.append(source_file)
            stub_sources.append(source_file)
            return sources, proxy_sources, stub_sources

        if idl_detail.idl_type == IdlType.INTERFACE:
            iface_header_file = self.header_file(file_dir, interface_name)
            proxy_source_file = self.c_source_file(file_dir, proxy_name)
            stub_header_file = self.header_file(file_dir, stub_name)
            stub_source_file = self.c_source_file(file_dir, stub_name)
            service_header_file = self.header_file(file_dir, service_name)
            service_source_file = self.c_source_file(file_dir, service_name)
            driver_source_file = self.c_source_file(file_dir, driver_name)
            sources.extend([
                iface_header_file, proxy_source_file, stub_header_file,
                stub_source_file, service_header_file, service_source_file,
                driver_source_file
            ])
            proxy_sources.append(proxy_source_file)
            stub_sources.append(stub_source_file)
        return sources, proxy_sources, stub_sources


# generate passthrough c code file info of hdi
class PassthroughCCodeGen(CodeGen):

    def gen_code(self, idl_detail):
        file_dir = self.get_source_file_dir(idl_detail.package)
        sources = []
        proxy_sources = []
        stub_sources = []
        interface_name, proxy_name, _, service_name, _, types_name = self.get_file_names(
            idl_detail)

        iface_header_file = self.header_file(file_dir, interface_name)
        proxy_source_file = self.c_source_file(file_dir, proxy_name)
        service_header_file = self.header_file(file_dir, service_name)
        service_source_file = self.c_source_file(file_dir, service_name)
        types_header_file = self.header_file(file_dir, types_name)

        if idl_detail.idl_type == IdlType.INTERFACE:
            sources.extend(
                [iface_header_file, proxy_source_file, service_source_file])
            proxy_sources.append(proxy_source_file)
        elif idl_detail.idl_type == IdlType.CALL_INTERFACE:
            sources.extend(
                [iface_header_file, service_header_file, service_source_file])
        elif idl_detail.idl_type == IdlType.CALLBACK:
            sources.extend(
                [iface_header_file, service_header_file, service_source_file])
        else:
            sources.append(types_header_file)
        return sources, proxy_sources, stub_sources


# generate passthrough cpp code file info of hdi
class PassthroughCppCodeGen(CodeGen):

    def gen_code(self, idl_detail):
        file_dir = self.get_source_file_dir(idl_detail.package)
        sources = []
        proxy_sources = []
        stub_sources = []
        interface_name, proxy_name, _, service_name, _, types_name = self.get_file_names(
            idl_detail)
        iface_header_file = self.header_file(file_dir, interface_name)
        proxy_source_file = self.cpp_source_file(file_dir, proxy_name)
        service_header_file = self.header_file(file_dir, service_name)
        service_source_file = self.cpp_source_file(file_dir, service_name)
        types_header_file = self.header_file(file_dir, types_name)

        if idl_detail.idl_type == IdlType.INTERFACE:
            sources.extend([
                iface_header_file, proxy_source_file, service_header_file,
                service_source_file
            ])
            proxy_sources.append(proxy_source_file)
        elif idl_detail.idl_type == IdlType.CALL_INTERFACE:
            sources.extend(
                [iface_header_file, service_header_file, service_source_file])
        elif idl_detail.idl_type == IdlType.CALLBACK:
            sources.extend(
                [iface_header_file, service_header_file, service_source_file])
        else:
            sources.append(types_header_file)
        return sources, proxy_sources, stub_sources


# generate ipc c code file information of hdi
class IpcCCodeGen(CodeGen):

    def gen_code(self, idl_detail):
        file_dir = self.get_source_file_dir(idl_detail.package)
        sources = []
        proxy_sources = []
        stub_sources = []
        interface_name, proxy_name, stub_name, service_name, driver_name, types_name = self.get_file_names(
            idl_detail)
        iface_header_file = self.header_file(file_dir, interface_name)
        proxy_source_file = self.c_source_file(file_dir, proxy_name)
        stub_header_file = self.header_file(file_dir, stub_name)
        stub_source_file = self.c_source_file(file_dir, stub_name)
        service_header_file = self.header_file(file_dir, service_name)
        service_source_file = self.c_source_file(file_dir, service_name)
        driver_source_file = self.c_source_file(file_dir, driver_name)
        types_header_file = self.header_file(file_dir, types_name)
        types_source_file = self.c_source_file(file_dir, types_name)

        if idl_detail.idl_type == IdlType.INTERFACE:
            sources.extend([
                iface_header_file, proxy_source_file, stub_header_file,
                stub_source_file, service_source_file, driver_source_file
            ])
            proxy_sources.append(proxy_source_file)
            stub_sources.append(stub_source_file)
        elif idl_detail.idl_type == IdlType.CALL_INTERFACE:
            sources.extend([
                iface_header_file, proxy_source_file, stub_header_file,
                stub_source_file, service_header_file, service_source_file
            ])
            proxy_sources.append(proxy_source_file)
            stub_sources.append(stub_source_file)
        elif idl_detail.idl_type == IdlType.CALLBACK:
            sources.extend([
                iface_header_file, proxy_source_file, stub_header_file,
                stub_source_file, service_header_file, service_source_file
            ])
            proxy_sources.append(stub_source_file)
            stub_sources.append(proxy_source_file)
        else:
            sources.extend([types_header_file, types_source_file])
            proxy_sources.append(types_source_file)
            stub_sources.append(types_source_file)
        return sources, proxy_sources, stub_sources


# generate ipc cpp code file information of hdi
class IpcCppCodeGen(CodeGen):

    def gen_code(self, idl_detail):
        file_dir = self.get_source_file_dir(idl_detail.package)
        sources = []
        proxy_sources = []
        stub_sources = []
        interface_name, proxy_name, stub_name, service_name, driver_name, types_name = self.get_file_names(
            idl_detail)
        iface_header_file = self.header_file(file_dir, interface_name)
        proxy_header_file = self.header_file(file_dir, proxy_name)
        proxy_source_file = self.cpp_source_file(file_dir, proxy_name)
        stub_header_file = self.header_file(file_dir, stub_name)
        stub_source_file = self.cpp_source_file(file_dir, stub_name)
        service_header_file = self.header_file(file_dir, service_name)
        service_source_file = self.cpp_source_file(file_dir, service_name)
        driver_source_file = self.cpp_source_file(file_dir, driver_name)
        types_header_file = self.header_file(file_dir, types_name)
        types_source_file = self.cpp_source_file(file_dir, types_name)

        if idl_detail.idl_type == IdlType.INTERFACE:
            sources.extend([
                iface_header_file, proxy_header_file, proxy_source_file,
                stub_header_file, stub_source_file, service_header_file,
                service_source_file, driver_source_file
            ])
            proxy_sources.append(proxy_source_file)
            stub_sources.append(stub_source_file)
        elif idl_detail.idl_type == IdlType.CALL_INTERFACE:
            sources.extend([
                iface_header_file, proxy_header_file, proxy_source_file,
                stub_header_file, stub_source_file, service_header_file,
                service_source_file
            ])
            proxy_sources.append(proxy_source_file)
            stub_sources.append(stub_source_file)
        elif idl_detail.idl_type == IdlType.CALLBACK:
            sources.extend([
                iface_header_file, proxy_header_file, proxy_source_file,
                stub_header_file, stub_source_file, service_header_file,
                service_source_file
            ])
            proxy_sources.append(stub_source_file)
            stub_sources.append(proxy_source_file)
        else:
            sources.extend([types_header_file, types_source_file])
            proxy_sources.append(types_source_file)
            stub_sources.append(types_source_file)
        return sources, proxy_sources, stub_sources


class CodeGenFactory(object):
    action_config = {
        "mini": {
            "low": {
                "c": LowCCodeGen(),
                "cpp": LowCppCodeGen()
            }
        },
        "lite": {
            "kernel": {
                "c": KernelCodeGen()
            },
            "passthrough": {
                "c": PassthroughCCodeGen(),
                "cpp": PassthroughCppCodeGen()
            }
        },
        "full": {
            "kernel": {
                "c": KernelCodeGen()
            },
            "passthrough": {
                "c": PassthroughCCodeGen(),
                "cpp": PassthroughCppCodeGen()
            },
            "ipc": {
                "c": IpcCCodeGen(),
                "cpp": IpcCppCodeGen()
            }
        }
    }

    @staticmethod
    def create_code_generate():
        if Option.system not in CodeGenFactory.action_config:
            raise Exception("the '{}' system is not supported".format(
                Option.system))
        system_action = CodeGenFactory.action_config.get(
            Option.system)
        if Option.mode not in system_action:
            raise Exception(
                "the '{}' mode is not supported by '{}' system".format(
                    Option.mode, Option.system))
        mode_action = system_action.get(Option.mode)
        if Option.language not in mode_action:
            raise Exception(
                "the '{}' language is not support by '{}' mode of '{}' system"
                .format(Option.language, Option.mode, Option.system))
        return mode_action.get(Option.language)


def check_python_version():
    if sys.version_info < (3, 0):
        raise Exception("Please run with python version >= 3.0")


if __name__ == "__main__":
    check_python_version()
    option_parser = argparse.ArgumentParser(
        description="Tools for generating compilation infomation of idl files",
    )

    option_parser.add_argument("-s",
                               "--system",
                               choices=["mini", "lite", "full"],
                               default="full",
                               help="system: mini, lite, full")

    option_parser.add_argument(
        "-m",
        "--mode",
        choices=["ipc", "passthrough", "kernel", "low"],
        default="ipc",
        help="generate code of ipc, passthrough or kernel mode")

    option_parser.add_argument("-l",
                               "--language",
                               required=True,
                               choices=["c", "cpp"],
                               help="language of generating code")

    option_parser.add_argument("-o",
                               "--out",
                               required=True,
                               default=".",
                               help="direstory of generate file")

    option_parser.add_argument("-r",
                               "--root",
                               required=True,
                               help="mapping path: <root package>:<path>")

    option_parser.add_argument("-f",
                               "--file",
                               required=True,
                               action="append",
                               help="the idl file")

    option_parser.add_argument("--imports",
                               action="append",
                               help="the imports")

    Option.load(option_parser.parse_args())
    idl_parser = IdlParser()
    idl_parser.parse()
    sys.stdout.write(ModuleInfo.json_info())
    sys.stdout.flush()
