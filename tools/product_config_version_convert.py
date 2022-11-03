#!/usr/bin/env python3
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

import argparse
import os
import sys 
import json


def merge_files(args):
    products_dir = "../../productdefine/common/products"
    device_dir = "../../productdefine/common/device"
    products_path = r'%s/%s' % (products_dir,args )
    with open(products_path,'r+',encoding='utf-8') as f:
        data = json.load(f)
        name = data["product_name"]
        company = data["product_company"]
        device = data["product_device"]
    device_path = r'%s/%s' % (device_dir,device+'.json' )
    path_str = "../../vendor/" + company + "/" + name
    path = os.path.join(path_str)
    new_file_name = os.path.join(path, "config.json")
    if os.path.exists(path):
        pass
    else:
        os.mkdir(path)
    try:
        device_read = open(device_path, "r", encoding='utf-8')
        products_read = open(products_path, "r", encoding='utf-8')
        data_device_read = json.load(device_read)
        data_products_read = json.load(products_read)
        data_all = merge(data_device_read , data_products_read)
        new_json = json.dumps(data_all, indent=4)
        new_write = open(new_file_name,"w")
        new_write.write(new_json)
    finally:
        device_read.close()
        products_read.close()
        new_write.close()
    readjson(new_file_name,device)


def readjson(path,device):
    subsystems_list = list()
    config_dic = {}
    with open(path,'r+',encoding='utf-8') as f:
        data = json.load(f)
        parts = data['parts']
        subsystem_list = list() 
        for key in parts: 
            substr = str(key).split(":")
            if substr[0] not in subsystem_list:
                subsystem_list.append(substr[0])
                components_list = list()
                for key_sub,value_sub in parts.items():
                    features = []
                    for value_fea in value_sub.values():
                        for k,v in value_fea.items():
                            fea = str(k)+" = "+str(v).lower()
                            features.append(fea)
                    if substr[0] == str(key_sub).split(":")[0]:
                        components_list.append({"component":str(key_sub).split(":")[1],"features":features})
                subsystems_list.append({"subsystem":substr[0],"components":components_list})
        config_dic["subsystems"] = subsystems_list
        del data['parts']
        data.update({"version": "3.0"})
        data.update({"board": device})
        data.update(config_dic)
        for datakey in data:
            if "enable_ramdisk" in datakey:
                dict_keys = ["product_name","device_company","device_build_path","target_cpu","type","version","board","enable_ramdisk","enable_absystem","subsystems"]
                break
            else:
                dict_keys = ["product_name","device_company","device_build_path","target_cpu","type","version","board","enable_absystem","subsystems"]
        dict_you_want = { new_key: data[new_key] for new_key in dict_keys }
        json_data = json.dumps(dict_you_want, indent=2)
        f.seek(0)
        f.write(json_data)
        f.truncate()

def merge(dict1, dict2): 
    res = {**dict1, **dict2} 
    return res 

def main(args):
    merge_files(args)

if __name__ == '__main__':
    main(sys.argv[1])
