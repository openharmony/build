#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (c) 2023 Huawei Device Co., Ltd.
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

from util.io_util import IoUtil
from exceptions.ohos_exception import OHOSException
from resources.config import Config
from containers.status import throw_exception

from helper.noInstance import NoInstance


class ProductUtil(metaclass=NoInstance):

    @staticmethod
    def get_products():
        config = Config()
        # ext products configuration
        _ext_scan_path = os.path.join(config.root_path,
                                      'out/products_ext/vendor')
        if os.path.exists(_ext_scan_path):
            for company in os.listdir(_ext_scan_path):
                company_path = os.path.join(_ext_scan_path, company)
                if not os.path.isdir(company_path):
                    continue

                for product in os.listdir(company_path):
                    p_config_path = os.path.join(company_path, product)
                    config_path = os.path.join(p_config_path, 'config.json')

                    if os.path.isfile(config_path):
                        info = IoUtil.read_json_file(config_path)
                        product_name = info.get('product_name')
                        if info.get('product_path'):
                            product_path = os.path.join(
                                config.root_path, info.get('product_path'))
                        else:
                            product_path = p_config_path
                        if product_name is not None:
                            subsystem_config_overlay_path = os.path.join(config.product_path,
                                'subsystem_config_overlay.json')
                            if os.path.isfile(subsystem_config_overlay_path):
                                yield {
                                    'company': company,
                                    "name": product_name,
                                    'product_config_path': p_config_path,
                                    'product_path': product_path,
                                    'version': info.get('version', '3.0'),
                                    'os_level': info.get('type', "mini"),
                                    'build_out_path': info.get('build_out_path'),
                                    'subsystem_config_json':
                                    info.get('subsystem_config_json'),
                                    'subsystem_config_overlay_json':
                                    subsystem_config_overlay_path,
                                    'config': config_path,
                                    'component_type': info.get('component_type', '')
                                }
                            else:
                                yield {
                                    'company': company,
                                    "name": product_name,
                                    'product_config_path': p_config_path,
                                    'product_path': product_path,
                                    'version': info.get('version', '3.0'),
                                    'os_level': info.get('type', "mini"),
                                    'build_out_path': info.get('build_out_path'),
                                    'subsystem_config_json':
                                    info.get('subsystem_config_json'),
                                    'config': config_path,
                                    'component_type': info.get('component_type', '')
                                }
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
                            'product_config_path': product_path,
                            'product_path': product_path,
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
                    'product_config_path': bip_path,
                    'product_path': bip_path,
                    'version': info.get('version', '2.0'),
                    'os_level': info.get('type', 'standard'),
                    'config': config_path,
                    'component_type': info.get('component_type', '')
                }

    @staticmethod
    @throw_exception
    def get_device_info(product_json):
        info = IoUtil.read_json_file(product_json)
        config = Config()
        version = info.get('version', '3.0')

        if version == '3.0':
            device_company = info.get('device_company')
            board = info.get('board')
            _board_path = info.get('board_path')
            if _board_path and os.path.exists(
                    os.path.join(config.root_path, _board_path)):
                board_path = os.path.join(config.root_path, _board_path)
            else:
                board_path = os.path.join(config.root_path, 'device',
                                          device_company, board)
                # board and soc decoupling feature will add boards
                # directory path here.
                if not os.path.exists(board_path):
                    board_path = os.path.join(config.root_path, 'device',
                                              'board', device_company, board)
            board_config_path = None
            if info.get('board_config_path'):
                board_config_path = os.path.join(config.root_path,
                                                 info.get('board_config_path'))

            return {
                'board': info.get('board'),
                'kernel': info.get('kernel_type'),
                'kernel_version': info.get('kernel_version'),
                'company': info.get('device_company'),
                'board_path': board_path,
                'board_config_path': board_config_path,
                'target_cpu': info.get('target_cpu'),
                'target_os': info.get('target_os'),
                'support_cpu': info.get('support_cpu'),
            }
        else:
            raise OHOSException(f'wrong version number in {product_json}')

    @staticmethod
    @throw_exception
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
    @throw_exception
    def get_features(product_json):
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

        # Get all features
        features_list = []
        for part, value in all_parts.items():
            if "features" not in value:
                continue
            for key, val in value["features"].items():
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
    @throw_exception
    def get_features_dict(product_json):
        all_parts = ProductUtil.get_all_components(product_json)
        features_dict = {}
        for part, value in all_parts.items():
            if "features" not in value:
                continue
            for key, val in value["features"].items():
                if type(val) in [bool, int, str]:
                    features_dict[key] = val
                else:
                    raise Exception(
                        "part feature '{key}:{val}' type not support.")
        return features_dict

    @staticmethod
    @throw_exception
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
    @throw_exception
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
    @throw_exception
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

    @staticmethod
    def has_component(product_name: str) -> bool:
        pass


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
                    parts.get('{}:{}'.format(ss_name, com_name)).update(key=val)
    return parts


def get_features(features):
    feats = {}
    for feat in features:
        if not feat:
            continue
        match = feat.index("=")
        if match <= 0:
            print("Warning: invalid feature [{}]".format(feat))
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
