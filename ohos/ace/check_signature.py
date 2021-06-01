#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 Huawei Device Co., Ltd.
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
import hashlib
import optparse

# remove comment flag
flag = False

# d.ts file list
file_list = []

# stored signature
signatures = set()

# check signature is in
signature_exits = False


def handle_single_comment(lines, i):
    index = lines[i].find("//")
    if index != -1:
        lines[i] = lines[i].replace(lines[i], '', 1)


# @return -1:the line is comment Line,should delete this line
# @return -2:Only begin comment found in this Line
# @return  0:Not find comment
def handle_document_comment(lines, i):
    global flag
    while True:
        if not flag:
            index = lines[i].find("/*")
            if index != -1:
                flag = True
                index2 = lines[i].find("*/", index + 2)
                if index2 != -1:
                    lines[i] = lines[i].replace(lines[i], '', 1)
                    flag = False  # continue look for comment
                else:
                    lines[i] = lines[i].replace(lines[i], '', 1)
                    lines[i] += ''
                    return -2
            else:
                return 0  # not find
        else:
            index2 = lines[i].find("*/")
            if index2 != -1:
                flag = False
                lines[i] = lines[i].replace(lines[i], '', 1)
            else:
                return -1  # should delete this


# At last print the handled result
def remove_comment(file):
    global flag
    f = open(file, "r")
    lines = f.readlines()
    f.close()
    length = len(lines)
    i = 0
    while i < length:
        ret = handle_document_comment(lines, i)
        if ret == -1:
            if flag == False:
                print("There must be some wrong")
            del lines[i]
            i -= 1
            length -= 1
        elif ret == 0:
            handle_single_comment(lines, i)
        else:
            pass
        i += 1
    return lines


# Write signature into file
def write_result(file, lines):
    f = open(file, "w")
    for line in lines:
        if line == '' or line.strip() == "":
            continue
        f.write(line.replace(' ', '').strip())
    f.close()


# traversal all fill in project folder
def find_all_file_name(path):
    global file_list
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if os.path.isdir(file_path):
            find_all_file_name(file_path)
        elif os.path.isfile(file_path) and os.path.splitext(file_path)[1] == '.ts':
            file_list.append(file_path)


def hash_file(path):
    f = open(path)
    thehash = hashlib.md5()
    line = f.readline()
    while (line):
        thehash.update(line.encode('utf-8'))
        line = f.readline()
    f.close()
    return thehash.hexdigest()


def setup_signature(path):
    global signatures
    global signature_exits
    signature_exits = os.path.exists(path)
    if (not signature_exits):
        return
    f = open(path, "r")
    lines = f.readlines()
    f.close()
    length = len(lines)
    for i in range(0, length):
        signatures.add(lines[i])


def compare_signature(value):
    global signatures
    if (value in signatures):
        return 0
    else:
        print(value.strip() + " hasn't signed")
        return -1


def parse_args(args):
    parser = optparse.OptionParser()
    parser.add_option('--input', help='d.ts document path')
    parser.add_option('--signature-path',
                      help='signature path', dest="signature_path")
    parser.add_option('--gen-signature', action="store_true", dest="signature",
                      help='need generate signature or not', default=False)
    options, _ = parser.parse_args(args)
    return options


def main(argv):
    options = parse_args(argv)
    global signature_exits
    setup_signature(os.path.join(options.signature_path, "signature.txt"))
    if (not signature_exits and options.signature == False):
        print("cannot find signature " +
              os.path.join(options.signature_path, "signature.txt"))
        return 0
    find_all_file_name(options.input)
    if (options.signature):
        open_file = open(os.path.join(options.input, "result.txt"), "w")
    ret = 0
    for file in file_list:
        lines = remove_comment(file)
        write_result(file, lines)
        hashvalue = os.path.basename(file) + " " + hash_file(file) + "\n"
        if (options.signature):
            open_file.write(hashvalue)
        else:
            ret = compare_signature(hashvalue)
            if (ret < 0):
                print("d.ts need generate signature")
                return -1
    if (options.signature):
        open_file.close()
    return ret


if __name__ == "__main__":
    exit(main(sys.argv))
