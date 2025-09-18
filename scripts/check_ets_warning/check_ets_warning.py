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
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'hb'))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from util.log_util import LogUtil


def count_str_in_log(log_path:str, target:str, kind:str, gen_whitelist=False):
    """
    统计日志文件中包含字符串 target 的行
        log_path: 日志文件路径
        target: 匹配字符串
        kind: 构建类型
        gen_whitelist: 是否生成白名单
    """
    count = 0
    fileList = {}            
    ctw_raw_message = {}
    try:
        with open(log_path, 'r', encoding='utf-8') as file:
            last_line = ''
            last_last_line = '' 
            for line in file:
                if target in line:
                    count += 1
                    # rk3568日志中，warning的文件名在warning信息上一行
                    if kind == 'rk3568' or kind == 'TDDbuild' or kind == 'xts':
                        if gen_whitelist == True:
                            fileName = extract_file_name(last_last_line, kind)
                        else:
                            fileName = extract_file_name(last_line, kind)
                    # xts_staitc warning的文件名和warning信息在同一行
                    else:
                        fileName = extract_file_name(line, kind)
                    if fileName is None:
                        continue
                    fileList[fileName] = fileList.get(fileName, 0) + 1
                    
                    if kind == 'rk3568' or kind == 'TDDbuild' or kind == 'xts':
                        raw_message = last_line
                    else:
                        raw_message = line
                    if fileName not in ctw_raw_message:
                        ctw_raw_message[fileName] = [last_line]
                    else:
                        ctw_raw_message[fileName].append(raw_message)
                last_last_line = last_line
                last_line = line
        return count, fileList, ctw_raw_message
    except FileNotFoundError:
        print(f"warning: '{log_path}' not found")
        return 0
    except Exception as e:
        print(f"An error occurred while processing the file: {str(e)}")
        return -1

def extract_file_name(text:str, kind:str):
    if kind == 'rk3568' or kind == 'TDDbuild' or kind == 'xts':
        start = text.rfind('/')
    elif kind == 'xts_static':
        start = text.rfind('[')
    end = text.find(':',start)
    fileName = text[start+1:end]
    if fileName.endswith('.ets'):
        return fileName
    if fileName.endswith('.ts'):
        return fileName
    return None

def generate_whitelist(warningMessage, log_path, ctw_whitelist_path, kind):
    ctw_count = []
    for warningName, target in warningMessage.items():
        count, fileList, ctw_raw_message = count_str_in_log(log_path, target, kind, gen_whitelist=True)
        if len(fileList) != 0:
            ctw_count.append({warningName: fileList})
    print(ctw_count)
    with open(ctw_whitelist_path, "w", encoding="utf-8") as f:
        yaml_str = yaml.dump(ctw_count, f, sort_keys=False, allow_unicode=True)

def main():
    """
    参考文档
    """
    # {warningName, warningMessage} 测试时没有额外设置warningName
    warningMessage = {
        "'As' expression for cast is deprecated for numeric types.":"'As' expression for cast is deprecated for numeric types.",
        # "IMPROPER_NUMERIC_CAST":"'As' expression for cast is deprecated for numeric types.",
        # '"globalThis" is not supported': '"globalThis" is not supported',
        # "Function may throw error, caller should handle it with 'try-catch' or declare '@throws'": "Function may throw error, caller should handle it with 'try-catch' or declare '@throws'",
        # "'inputEventClient' is system api": "'inputEventClient' is system api",
        # "Function on with this assembly signature already declared": "Function on with this assembly signature already declared",
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

    log_path = args.log_path # build.log的文件路径
    ctw_count = []          # build.log中的ctw数量统计
    ctw_raw = {}            # build.log中的warning信息
    ctw_whitelist_path = args.whitelist_dir # 白名单文件路径
    # kind = args.kind                      # rk3568和xts输出的warning信息格式不同，匹配ctw的代码存在差异
    gen_whitelist = args.gen_whitelist      # 是否生成白名单
    xts_suitetype = args.xts_suitetype      # 生成白名单时会人工添加xts_suitetype参数
    if xts_suitetype is None:               # xts构建时xts_suitetype从环境变量获取
        xts_suitetype = os.environ.get("XTS_SUITETYPE", "")
    
    product_name = args.product_name
    build_target = args.build_target
    gn_args = args.gn_args
    
    # 只有rk3568需要检测新增warning，sdk不需要
    if product_name != "rk3568":
        print("no need to check new warning")
        return 0
    if "build_xts=true" in gn_args:
        if xts_suitetype == "bin,hap_dynamic":
            kind = "xts"
            ctw_whitelist_path += '/xts_whitelist.yaml'
        elif xts_suitetype == "hap_static":
            kind = "xts_static"
            ctw_whitelist_path += '/xts_static_whitelist.yaml'
        else:
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
        generate_whitelist(warningMessage, log_path, ctw_whitelist_path, kind)
        return 0

    # 读取 ctw_whitelist.yaml
    try:
        with open(ctw_whitelist_path, "r", encoding="utf-8") as f:
            whitelist = yaml.safe_load(f)
            # 白名单为空，不需要匹配新增warning
            if whitelist is None:
                print("no need to check new warning")
                return 0
            whitelist = whitelist[0]
    except FileNotFoundError:
        # 白名单不存在，不检测新增warning
        print("whitelist not exist")
        return 0
        
    # 匹配 build.log 的 ctw
    try:
        for warningName, target in warningMessage.items():
            count, fileList, ctw_raw_message = count_str_in_log(log_path, target, kind)
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
    for ctw_file_list in ctw_count:
        for warningName, fileList in ctw_file_list.items():
            add_list = {}
            for file, count in fileList.items():
                white_count = whitelist.get(warningName,{}).get(file, 0)
                if count > white_count:
                    ctw_status = 1
                    add_list[file] = count - white_count
            if len(add_list) > 0:
                ctw_add_list[warningName] = add_list
    if ctw_status == 1:
        for warningName, fileList in ctw_add_list.items():
            for file, count in fileList.items():
                LogUtil.write_log(log_path ,f"{file} has {count} new warning, warning message: {warningName}",'ERROR')
                for warning in ctw_raw[warningName][file]:
                    LogUtil.write_log(log_path ,warning,'ERROR')
        return 1
    else:
        print("no new warning compared with whitelist")
        return 0

if __name__ == "__main__":
    exit(main())
