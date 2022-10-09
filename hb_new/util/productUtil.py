#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (c) 2020 Huawei Device Co., Ltd.
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
import re
from collections import defaultdict

from util.ioUtil import IoUtil
from exceptions.ohosException import OHOSException
from resources.config import Config

from helper.noInstance import NoInstance


class ProductUtil(metaclass=NoInstance):

    @staticmethod
    def get_products():
        config = Config()
        for company in os.listdir(config.vendor_path):
            company_path = os.path.join(config.vendor_path, company)
            if not os.path.isdir(company_path):
                continue

            for product in os.listdir(company_path):
                product_path = os.path.join(company_path, product)
                config_path = os.path.join(product_path, 'config.json')

                if os.path.isfile(config_path):
                    info = IoUtil.read_json_file(config_path)
                    product_name = info.get('product_name')
                    if product_name is not None:
                        yield {
                            'company': company,
                            "name": product_name,
                            'path': product_path,
                            'version': info.get('version', '3.0'),
                            'os_level': info.get('type', "mini"),
                            'config': config_path,
                            'component_type': info.get('component_type', '')
                        }
        bip_path = config.built_in_product_path
        for item in os.listdir(bip_path):
            if item[0] in ".":
                continue
            else:
                product_name = item[0:-len('.json')
                                    ] if item.endswith('.json') else item
                config_path = os.path.join(bip_path, item)
                info = IoUtil.read_json_file(config_path)
                yield {
                    'company': 'built-in',
                    "name": product_name,
                    'path': bip_path,
                    'version': info.get('version', '2.0'),
                    'os_level': info.get('type', 'standard'),
                    'config': config_path,
                    'component_type': info.get('component_type', '')
                }

    @staticmethod
    def get_device_info(product_json):
        info = IoUtil.read_json_file(product_json)
        config = Config()
        version = info.get('version', '3.0')

        if version == '2.0':
            device_json = os.path.join(config.built_in_device_path,
                                       f'{info["product_device"]}.json')
            device_info = IoUtil.read_json_file(device_json)
            return {
                'board': device_info.get('device_name'),
                'kernel': device_info.get('kernel_type', 'linux'),
                'kernel_version': device_info.get('kernel_version'),
                'company': device_info.get('device_company'),
                'board_path': device_info.get('device_build_path'),
                'target_cpu': device_info.get('target_cpu'),
                'target_os': device_info.get('target_os')
            }
        elif version == '3.0':
            device_company = info.get('device_company')
            board = info.get('board')
            board_path = os.path.join(config.root_path, 'device',
                                      device_company, board)
            # board and soc decoupling feature will add boards directory path here.
            if not os.path.exists(board_path):
                board_path = os.path.join(config.root_path, 'device', 'board',
                                          device_company, board)

            return {
                'board': info.get('board'),
                'kernel': info.get('kernel_type'),
                'kernel_version': info.get('kernel_version'),
                'company': info.get('device_company'),
                'board_path': board_path,
                'target_cpu': info.get('target_cpu'),
                'target_os': info.get('target_os')
            }
        else:
            raise OHOSException(f'wrong version number in {product_json}')

    @staticmethod
    def get_all_components(product_json):
        if not os.path.isfile(product_json):
            raise OHOSException(f'features {product_json} not found')

        config = Config()
        # Get all inherit files
        files = [os.path.join(config.root_path, file) for file in IoUtil.read_json_file(
            product_json).get('inherit', [])]
        # Add the product config file to last with highest priority
        files.append(product_json)

        # Read all parts in order
        all_parts = {}
        for _file in files:
            if not os.path.isfile(_file):
                continue
            _info = IoUtil.read_json_file(_file)
            parts = _info.get('parts')
            if parts:
                all_parts.update(parts)
            else:
                # v3 config files
                all_parts.update(ProductUtil.get_vendor_parts_list(_info))

        return all_parts

    @staticmethod
    def get_features(product_json):
        all_parts = ProductUtil.get_all_components(product_json)
        # Get all features
        features_list = []
        for part, val in all_parts.items():
            if "features" not in val:
                continue
            for key, val in val["features"].items():
                _item = ''
                if isinstance(val, bool):
                    _item = f'{key}={str(val).lower()}'
                elif isinstance(val, int):
                    _item = f'{key}={val}'
                elif isinstance(val, str):
                    _item = f'{key}="{val}"'
                else:
                    raise Exception(
                        "part feature '{key}:{val}' type not support.")
                features_list.append(_item)
        return features_list

    @staticmethod
    def get_features_dict(product_json):
        all_parts = ProductUtil.get_all_components(product_json)
        features_dict = {}
        for part, val in all_parts.items():
            if "features" not in val:
                continue
            for key, val in val["features"].items():
                if type(val) in [bool, int, str]:
                    features_dict[key] = val
                else:
                    raise Exception(
                        "part feature '{key}:{val}' type not support.")
        return features_dict

    @staticmethod
    def get_components(product_json, subsystems):
        if not os.path.isfile(product_json):
            raise OHOSException(f'{product_json} not found')

        components_dict = defaultdict(list)
        product_data = IoUtil.read_json_file(product_json)
        for subsystem in product_data.get('subsystems', []):
            sname = subsystem.get('subsystem', '')
            if not len(subsystems) or sname in subsystems:
                components_dict[sname] += [
                    comp['component']
                    for comp in subsystem.get('components', [])
                ]

        return components_dict, product_data.get('board', ''),\
            product_data.get('kernel_type', '')

    @staticmethod
    def get_product_info(product_name, company=None):
        for product_info in ProductUtil.get_products():
            cur_company = product_info['company']
            cur_product = product_info['name']
            if company:
                if cur_company == company and cur_product == product_name:
                    return product_info
            else:
                if cur_product == product_name:
                    return product_info

        raise OHOSException(f'product {product_name}@{company} not found')

    @staticmethod
    def get_compiler(config_path):
        config = os.path.join(config_path, 'config.gni')
        if not os.path.isfile(config):
            return ''
        compiler_pattern = r'board_toolchain_type ?= ?"(\w+)"'
        with open(config, 'rt', encoding='utf-8') as config_file:
            data = config_file.read()
        compiler_list = re.findall(compiler_pattern, data)
        if not len(compiler_list):
            raise OHOSException(f'board_toolchain_type is None in {config}')

        return compiler_list[0]

    @staticmethod
    def get_vendor_parts_list(config):
        return _transform(config).get('parts')


def _transform(config):
    subsystems = config.get('subsystems')
    if subsystems:
        config.pop('subsystems')
        parts = _from_ss_to_parts(subsystems)
        config['parts'] = parts
    return config


def _from_ss_to_parts(subsystems):
    parts = dict()
    for subsystem in subsystems:
        ss_name = subsystem.get('subsystem')
        components = subsystem.get('components')
        if components:
            for com in components:
                com_name = com.get('component')
                features = com.get('features')
                syscap = com.get('syscap')
                exclusions = com.get('exclusions')
                if features:
                    pairs = get_features(features)
                    parts['{}:{}'.format(ss_name, com_name)] = pairs
                else:
                    parts['{}:{}'.format(ss_name, com_name)] = dict()
                if syscap:
                    pairs = get_syscap(syscap)
                    parts.get('{}:{}'.format(ss_name, com_name)).update(pairs)
                if exclusions:
                    pairs = get_exclusion_modules(exclusions)
                    parts.get('{}:{}'.format(ss_name, com_name)).update(pairs)
                # Copy other key-values
                for key, val in com.items():
                    if key in ['component', 'features', 'syscap', 'exclusions']:
                        continue
                    parts['{}:{}'.format(ss_name, com_name)][key] = val
    return parts


def get_features(features):
    feats = {}
    for feat in features:
        if not feat:
            continue
        match = feat.index("=")
        if match <= 0:
            print("Warning: invalid feature [" + feat + "]")
            continue
        key = feat[:match].strip()
        val = feat[match + 1:].strip().strip('"')
        if val == 'true':
            feats[key] = True
        elif val == 'false':
            feats[key] = False
        elif re.match(r'[0-9]+', val):
            feats[key] = int(val)
        else:
            feats[key] = val.replace('\"', '"')

    pairs = dict()
    pairs['features'] = feats
    return pairs


def get_syscap(syscap):
    feats = {}
    for feat in syscap:
        if not feat:
            continue
        if '=' not in feat:
            raise Exception("Error: invalid syscap [{}]".format(feat))
        match = feat.index("=")
        key = feat[:match].strip()
        val = feat[match + 1:].strip().strip('"')
        if val == 'true':
            feats[key] = True
        elif val == 'false':
            feats[key] = False
        elif re.match(r'[0-9]+', val):
            feats[key] = int(val)
        else:
            feats[key] = val.replace('\"', '"')

    pairs = dict()
    pairs['syscap'] = feats
    return pairs


def get_exclusion_modules(exclusions):
    pairs = dict()
    pairs['exclusions'] = exclusions
    return pairs
