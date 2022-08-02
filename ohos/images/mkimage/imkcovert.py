#!/usr/bin/env python
# coding: utf-8
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

import sys
import os
import hashlib
import errno
import stat
import datetime


def usage():
    print('\n Usage: imgcovert.py <cmd> <input> <output>')
    print('         <cmd>: sparse or unsparse')
    print('         <input>: input image file')
    print('         <output>: ouput image file\n')
    return


def get_fill_cnt(inputfile, blocksize):
    flags = os.O_WRONLY
    modes = stat.S_IWUSR | stat.S_IRUSR
    size = os.path.getsize(inputfile)
    fill_cnt = 0
    if size % blocksize != 0:
        fill_cnt = blocksize - size % blocksize
    indata = os.fdopen(os.open(inputfile, flags, modes), 'a')
    for _ in range(fill_cnt):
        indata.write("\0")
    indata.close();
    return fill_cnt


def get_gap_blocksize(length, size):
    if length < size:
        cnt = 2
    elif length < (size * 2):
        cnt = 3
    else:
        cnt = 4
    return cnt


def get_block_cnt(inputfile, blocksize):
    size = os.path.getsize(inputfile)
    if blocksize != 0:
        totalblocks = size / blocksize
    else:
        sys.exit(1)
    if (size % blocksize) != 0:
        print("len is not eq n * blocksize: ", size, totalblocks)
    return totalblocks


def get_crc_value(inputfile, blocksize):
    totalblocks = get_block_cnt(inputfile, blocksize)
    indata = open(inputfile, 'rb')
    ind = 0
    md5 = hashlib.md5()
    while (ind < totalblocks):
        md5.update(indata.read(blocksize))
        ind += 1
    indata.close()
    return md5.hexdigest()


def unsparse(sparseimagefile, imagefile):
    header = open(sparseimagefile, 'r')
    magic_mumber = header.readline()
    version = header.readline()
    blocksize = int(header.readline())
    total_blocks = int(header.readline())
    crc_value = header.readline()
    input_crc_value = header.readline()
    table_numbers = int(header.readline())
    table = []
    flags = os.O_CREAT | os.O_RDWR
    modes = stat.S_IWUSR | stat.S_IRUSR
    i = 0
    while (i < table_numbers):
        start = int(header.readline())
        end = int(header.readline())
        table.append([start, end])
        i += 1
    fill_cnt = int(header.readline())
    length = header.tell()
    header.close()
    inputrow = open(sparseimagefile, 'rb')
    inputrow.seek(get_gap_blocksize(length, blocksize) * blocksize)
    output = os.fdopen(os.open(imagefile, flags, modes), 'wb')
    output.truncate(total_blocks * blocksize)
    md5 = hashlib.md5()
    for block in table:
        cnt = block[1] - block[0]
        output.seek(block[0] * blocksize)
        indata = inputrow.read(cnt * blocksize)
        md5.update(indata)
        output.write(indata)
    output.close()
    inputrow.close()
    print("RawFileCRC: ", get_crc_value(imagefile, blocksize), crc_value)
    print("SparseCRC: ", md5.hexdigest(), input_crc_value)
    output = open(imagefile, 'r+')
    output.truncate(total_blocks * blocksize - fill_cnt)
    output.close()
    return


def is_empty_block(buff, size):
    ind = 0
    while (ind < size):
        if buff[ind] != 0:
            return False
        ind += 1
    return True


def get_raw_datafile(imagefile, blockid, total_blocks, blocksize):
    temp_file = imagefile + ".tempfile"
    ind = 0
    start = -1
    table_numbers = 0
    flags = os.O_CREAT | os.O_RDWR
    modes = stat.S_IWUSR | stat.S_IRUSR

    inputrow = open(imagefile, 'rb')
    outputtemp = os.fdopen(os.open(temp_file, flags, modes), 'wb')
    while (ind < total_blocks):
        indata = inputrow.read(blocksize)
        if len(indata) != blocksize:
            print("error Block", ind, len(indata))
        if is_empty_block(indata, blocksize) == True:
            if start != -1:
                blockid.append([start, ind])
                table_numbers += 1
                start = -1
        else:
            outputtemp.write(indata)
            if start == -1:
                start = ind
        ind += 1
    if start != -1:
        blockid.append([start, ind])
        table_numbers += 1
        start = -1
    inputrow.close()
    outputtemp.close()
    return table_numbers


def sparse(imagefile, sparseimagefile):
    temp_file = imagefile + ".tempfile"
    magic_number = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    version = 1.0
    blocksize = 4096
    table_numbers = 0
    blockid = []
    flags = os.O_CREAT | os.O_RDWR
    modes = stat.S_IWUSR | stat.S_IRUSR

    fill_cnt = get_fill_cnt(imagefile, blocksize)
    total_blocks = get_block_cnt(imagefile, blocksize)
    table_numbers = get_raw_datafile(imagefile, blockid, total_blocks, blocksize)

#   save the header
    outputrow = os.fdopen(os.open(sparseimagefile, flags, modes), 'w')
    outputrow.write("%s\n" % (magic_number))
    outputrow.write("%s\n" % (version))
    outputrow.write("%s\n" % (blocksize))
    outputrow.write("%s\n" % (int(total_blocks)))
    outputrow.write("%s\n" % (get_crc_value(imagefile, blocksize)))
    outputrow.write("%s\n" % (get_crc_value(temp_file, blocksize)))
    outputrow.write("%s\n" % (table_numbers))
    for block in blockid:
        outputrow.write("%s\n" % (block[0]))
        outputrow.write("%s\n" % (block[1]))
    outputrow.write("%s\n" % (int(fill_cnt)))
    outputrow.truncate(get_gap_blocksize(outputrow.tell(), blocksize) * blocksize)
    outputrow.close()

#   append the raw data
    outputrow = os.fdopen(os.open(sparseimagefile, flags, modes), 'ab')
    outputtemp = os.fdopen(os.open(temp_file, flags, modes), 'rb')
    blocknum = get_block_cnt(temp_file, blocksize)
    i = 0
    while (i < blocknum):
        outputrow.write(outputtemp.read(blocksize))
        i += 1
    outputtemp.close()
    outputrow.close()
    os.remove(temp_file)
    output = open(imagefile, 'r+')
    output.truncate(int(total_blocks) * int(blocksize) - int(fill_cnt))
    output.close()


if __name__ == '__main__':
    if len(sys.argv) != 4:
        usage()
        sys.exit()
    CMD = str(sys.argv[1])
    INPUT_FILE = str(sys.argv[2])
    OUTPUT_FILE = str(sys.argv[3])
    if CMD == 'unsparse':
        unsparse(INPUT_FILE, OUTPUT_FILE)
    elif CMD == 'sparse':
        sparse(INPUT_FILE, OUTPUT_FILE)
    else:
        usage()