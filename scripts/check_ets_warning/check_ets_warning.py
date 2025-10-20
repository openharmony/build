#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Huawei Device Co., Ltd.
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
import yaml
import os
import argparse
from pathlib import Path
path = Path(__file__).resolve()
sys.path.append(os.path.join(path.parents[3], 'build/hb'))
sys.path.append(os.path.join(path.parents[3], 'build'))
from util.log_util import LogUtil

# 白名单多一层测试套的路径
def count_str_in_log_xts_static(log_path:str, warningMessage:str, kind:str, gen_whitelist=False):
    """
    统计日志文件中包含字符串 target 的行
        log_path: 日志文件路径
        target: 匹配字符串
        kind: 构建类型
        gen_whitelist: 是否生成白名单
    """
    fileList = {}           # 每个测试套中存在warningMessage的文件名
    ctw_raw_message = {}    # warning原始信息
    hashFileList = {}       # 每个测试套都有唯一uuid的哈希值，以哈希值作为匹配测试套warning的键
    hashDirList = {}        # {哈希值：测试套路径}
    try:
        with open(log_path, 'r', encoding='utf-8') as file:
            projectDir = "none"
            for line in file:
                hashValue = extract_hash_value(line)
                # xts_static的warning不提供文件路径，需要单独提取project dir
                if "project dir" in line:
                    projectDir = extract_dir_name(line, gen_whitelist)
                    if projectDir != "none":
                        hashDirList[hashValue] = projectDir
                elif warningMessage in line:
                    fileList = hashFileList.get(hashValue, {})
                    # xts_staitc warning的文件名和warning信息在同一行
                    fileName = extract_file_name(line)
                    if fileName is None:
                        continue
                    fileList[fileName] = fileList.get(fileName, 0) + 1
                    hashFileList[hashValue] = fileList

                    raw_message = line
                    if hashValue not in ctw_raw_message:
                        ctw_raw_message[hashValue] = {}
                    if fileName not in ctw_raw_message[hashValue]:
                        ctw_raw_message[hashValue][fileName] = [raw_message]
                    else:
                        ctw_raw_message[hashValue][fileName].append(raw_message)
        return hashFileList, hashDirList, ctw_raw_message
    except FileNotFoundError:
        print(f"warning: '{log_path}' not found")
        return 0
    except Exception as e:
        print(f"An error occurred while processing the file: {str(e)}")
        return -1

def extract_dir_name(text:str, gen_whitelist):
    # 本地的路径和流水线的路径不一样
    if gen_whitelist == True:
        target = "/srv/workspace/1119xts_a56861365/code/"
        # target = "harmony_code/codearts_workspace/"
    else:
        target = "harmony_code/codearts_workspace/"
    start = text.find(target)
    if start == -1:
        dirName = "none"
    else:
        dirName = text[start+len(target):].strip()
    return dirName

def extract_hash_value(text:str):
    target = "[0/0] ["
    start = text.find(target)
    end = text.find(']',start+len(target))
    hash_value = text[start+len(target):end]
    if start == -1:
        target = "[1/1] ["
        start = text.find(target)
        end = text.find(']',start+len(target))
        hash_value = text[start+len(target):end]
        if start == -1:
            return None
    return hash_value

def extract_file_name(text:str):
    target = "Hvigor info: ["
    start = text.rfind(target)
    end = text.find(':',start+len(target))
    fileName = text[start+len(target):end]
    if fileName.endswith('.ets'):
        return fileName
    if fileName.endswith('.ts'):
        return fileName
    return None

def generate_whitelist(intercept_list, suggestion_list, log_path, ctw_whitelist_path, kind):
    ctw_count = []
    for warningName, warningMessage in intercept_list.items():
        if kind == 'rk3568' or kind == 'TDDbuild' or kind == 'xts':
            return
        else:
            hashFileList, hashDirList, ctw_raw_message = count_str_in_log_xts_static(log_path, warningMessage, kind, gen_whitelist=True)
            if len(hashFileList) != 0:
                fileList = {projectDir: hashFileList[hash] for hash, projectDir in hashDirList.items() if hash in hashFileList}
                fileList = dict(sorted(fileList.items()))
                ctw_count.append({warningName: 
                    {'warningMessage': warningMessage, 
                    'suggestion': suggestion_list[warningName], 
                    'fileList': fileList}
                })
    with open(ctw_whitelist_path, "w", encoding="utf-8") as f:
        yaml_str = yaml.dump(ctw_count, f, sort_keys=False, allow_unicode=True)

def main():
    # {warningName, warningMessage}
    intercept_list = {
        "IMPROPER_NUMERIC_CAST": "'As' expression for cast is deprecated for numeric types.",
    }
    # {warningName, suggestion for editing}
    suggestion_list = {
        "IMPROPER_NUMERIC_CAST": "numeric as for type conversion is deprecated now and will be TypeError later, you should use toDouble(), toFloat() and toInt() to replace as number, as float and as int",
    }
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-path")
    parser.add_argument("--whitelist-dir")
    parser.add_argument("--gen-whitelist")
    parser.add_argument("--from")
    parser.add_argument("--product-name")
    parser.add_argument("--build-target")
    parser.add_argument("--gn-args", nargs="?", action="append", default=[])
    parser.add_argument("--xts_suitetype")
    args, unknown = parser.parse_known_args()

    log_path = args.log_path    # build.log的文件路径
    ctw_count = []              # build.log中的ctw数量统计
    ctw_raw = {}                # build.log中的warning信息
    ctw_whitelist_path = args.whitelist_dir # 白名单文件路径
    # kind = args.kind                      # rk3568和xts输出的warning信息格式不同，匹配ctw的代码存在差异
    gen_whitelist = args.gen_whitelist      # 是否生成白名单
    xts_suitetype = args.xts_suitetype      # 生成白名单时会人工添加xts_suitetype参数
    if xts_suitetype is None:               # xts构建时会设置环境变量xts_suitetype
        xts_suitetype = os.environ.get("XTS_SUITETYPE", "")
    
    product_name = args.product_name
    build_target = args.build_target
    gn_args = args.gn_args
    
    # 只有rk3568需要检测新增warning，sdk不需要
    if product_name != "rk3568":
        print("product_name {} doen't need to check new warning".format(product_name))
        return 0
    else:
        print("product_name {} need to check new warning to intercept deprecated syntax".format(product_name))
    if "build_xts=true" in gn_args:
        if xts_suitetype == "bin,hap_dynamic":
            kind = "xts"
            ctw_whitelist_path += '/xts_whitelist.yaml'
        elif xts_suitetype == "hap_static":
            kind = "xts_static"
            ctw_whitelist_path += '/xts_static_whitelist.yaml'
        else:
            print("build_xts=true, but not find xts_suitetype in environment or params, it won't check new warning")
            return 0
    elif build_target == "TDDbuild":
        kind = "TDDbuild"
        ctw_whitelist_path += '/tdd_whitelist.yaml'
    else:
        kind = "rk3568"
        ctw_whitelist_path += '/rk3568_whitelist.yaml'
    print("Check new warning according to whitelist:", ctw_whitelist_path)

    # 生成白名单
    if gen_whitelist == "true":
        generate_whitelist(intercept_list, suggestion_list, log_path, ctw_whitelist_path, kind)
        print("whitelist generate successfully")
        return 0

    # 读取 ctw_whitelist.yaml
    try:
        with open(ctw_whitelist_path, "r", encoding="utf-8") as f:
            whitelist = yaml.safe_load(f)
            # 白名单为空，不需要匹配新增warning
            if whitelist is None:
                print("whitelist is empty, no need to check new warning")
                return 0
            whitelist = whitelist[0]
    except FileNotFoundError:
        # 白名单不存在，不检测新增warning
        print("whitelist not exist, no need to check new warning")
        return 0
        
    # 匹配 build.log 的 ctw
    try:
        for warningName, warningMessage in intercept_list.items():
            if kind == 'rk3568' or kind == 'TDDbuild' or kind == 'xts':
                return 0
            else:
                hashFileList, hashDirList, ctw_raw_message = count_str_in_log_xts_static(log_path, warningMessage, kind, gen_whitelist=False)
                fileList = {projectDir: hashFileList[hash] for hash, projectDir in hashDirList.items() if hash in hashFileList}
                fileList = dict(sorted(fileList.items()))
                ctw_raw_message = {projectDir: ctw_raw_message[hash] for hash, projectDir in hashDirList.items() if hash in ctw_raw_message}
            if len(fileList) != 0:
                ctw_count.append({warningName: fileList})
                ctw_raw[warningName] = ctw_raw_message
    except Exception as e:
        print(f"An error occurred while processing the file: {str(e)}")
        return 0

    # 比较是否有新增ctw
    # ctw_status：0指ctw数量不变，1指新增ctw，2指ctw减少
    ctw_status = 0
    ctw_add_list = {}
    
    if kind == 'rk3568' or kind == 'TDDbuild' or kind == 'xts':
        for ctw_file_list in ctw_count:
            for warningName, fileList in ctw_file_list.items():
                add_list = {}
                for file, count in fileList.items():
                    white_count = whitelist.get(warningName,{}).get("fileList",{}).get(file, 0)
                    if count > white_count:
                        ctw_status = 1
                        add_list[file] = count - white_count
                if len(add_list) > 0:
                    ctw_add_list[warningName] = add_list
    else:
        for ctw_file_list in ctw_count:
            for warningName, dirFileList in ctw_file_list.items():
                dir_add_list = {}
                for dirName, fileList in dirFileList.items():
                    add_list = {}
                    for file, count in fileList.items():
                        white_count = whitelist.get(warningName,{}).get("fileList",{}).get(dirName,{}).get(file, 0)
                        if count > white_count:
                            ctw_status = 1
                            add_list[file] = count - white_count
                    if len(add_list) > 0:
                        dir_add_list[dirName] = add_list
                if len(dir_add_list) > 0:
                    ctw_add_list[warningName] = dir_add_list

    if ctw_status == 1:
        if kind == 'rk3568' or kind == 'TDDbuild' or kind == 'xts':
            for warningName, fileList in ctw_add_list.items():
                for file, count in fileList.items():
                    LogUtil.write_log(log_path ,f"{file} has {count} new warning, warning message: {intercept_list[warningName]}",'ERROR')
                    LogUtil.write_log(log_path, f"suggestions to solve new warnings: {suggestion_list[warningName]}", 'ERROR')
                    for warning in ctw_raw[warningName][file]:
                        LogUtil.write_log(log_path ,warning,'ERROR')
        else:
            for warningName, dirFileList in ctw_add_list.items():
                for dirName, fileList in dirFileList.items():
                    LogUtil.write_log(log_path ,f"check FAILED: new warnings are treated as error",'ERROR')
                    LogUtil.write_log(log_path ,f"new warning in {dirName}, warning message: {intercept_list[warningName]}",'ERROR')
                    LogUtil.write_log(log_path, f"suggestions to solve new warnings: {suggestion_list[warningName]}", 'ERROR')
                    for file, count in fileList.items():
                        LogUtil.write_log(log_path ,f"{file} has {count} new warning, warning message: {intercept_list[warningName]}",'ERROR')
                        for warning in ctw_raw[warningName][dirName][file]:
                            LogUtil.write_log(log_path ,warning,'WARNING')
        return 1
    else:
        print("no new warning compared with whitelist")
        return 0

if __name__ == "__main__":
    exit(main())
