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

import sys
import os
import json
import argparse
from collections import Counter

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from third_party.PyYAML.lib import yaml  # noqa: E402

_DUPLICATE_KEY_DEF = "duplicate key definition"
_EMPTY_YAML = "empty yaml file input"
_INVALID_YAML = "invalid yaml format"
_DUPLICATE_DOMAIN = "duplicate domain"
_INVALID_DOMAIN_NUMBER = "invalid domain number"
_INVALID_DOMAIN_LENGTH = "invalid domain length"
_INVALID_DOMAIN_CHAR = "invalid domain character"
_INVALID_DOMAIN_CHAR_HEAD = "invalid domain character head"
_INVALID_EVENT_NUMBER = "invalid event number"
_INVALID_EVENT_LENGTH = "invalid event length"
_INVALID_EVENT_CHAR = "invalid event character"
_INVALID_EVENT_CHAR_HEAD = "invalid event character head"
_MISSING_EVENT_BASE = "missing event base"
_MISSING_EVENT_TYPE = "missing event type"
_INVALID_EVENT_TYPE = "invalid event type"
_MISSING_EVENT_LEVEL = "missing event level"
_INVALID_EVENT_LEVEL = "invalid event level"
_MISSING_EVENT_DESC = "missing event desc"
_INVALID_EVENT_DESC_LENGTH = "invalid event desc length"
_INVALID_EVENT_TAG_NUM = "invalid event tag number"
_INVALID_EVENT_TAG_LEN = "invalid event tag length"
_INVALID_EVENT_TAG_CHAR = "invalid event tag character"
_DUPLICATE_EVENT_TAG = "duplicate event tag"
_INVALID_EVENT_BASE_KEY = "invalid event base key"
_INVALID_EVENT_PARAM_NUM = "invalid event param number"
_INVALID_EVENT_PARAM_LEN = "invalid event param length"
_INVALID_EVENT_PARAM_CHAR = "invalid event param character"
_INVALID_EVENT_PARAM_CHAR_HEAD = "invalid event param character head"
_MISSING_EVENT_PARAM_TYPE = "missing event param type"
_INVALID_EVENT_PARAM_TYPE = "invalid event param type"
_INVALID_EVENT_PARAM_ARRSIZE = "invalid event param arrsize"
_MISSING_EVENT_PARAM_DESC = "missing event param desc"
_INVALID_EVENT_PARAM_DESC_LEN = "invalid event param desc length"
_INVALID_EVENT_PARAM_KEY = "invalid event param key"
_DEPRECATED_EVENT_NAME_PREFIX = "deprecated event name prefix"
_DEPRECATED_PARAM_NAME_PREFIX = "deprecated param name prefix"
_DEPRECATED_TAG_NAME = "deprecated tag name"
_DEPRECATED_EVENT_DESC_NAME = "deprecated event desc name"
_DEPRECATED_PARAM_DESC_NAME = "deprecated param desc name"
_INVALID_DOMAIN_DEF = "invalid definition type for domain"
_INVALID_EVENT_DEF = "invalid definition type for event"
_INVALID_EVENT_BASE_DEF = "invalid definition type for event base"
_INVALID_EVENT_TYPE_DEF = "invalid definition type for event type"
_INVALID_EVENT_LEVEL_DEF = "invalid definition type for event level"
_INVALID_EVENT_DESC_DEF = "invalid definition type for event desc"
_INVALID_EVENT_TAG_DEF = "invalid definition type for event tag"
_INVALID_EVENT_PARAM_DEF = "invalid definition type for event param"
_INVALID_PARAM_TYPE_DEF = "invalid definition type for param type"
_INVALID_PARAM_ARRSIZE_DEF = "invalid definition type for param arrsize"
_INVALID_PARAM_DESC_DEF = "invalid definition type for param desc"
_WARNING_MAP = {
    _EMPTY_YAML :
        "The yaml file list is empty.",
    _INVALID_YAML :
        "Invalid yaml file, error message: <<%s>>.",
    _DUPLICATE_DOMAIN :
        "Domain <<%s>> is already defined in <<%s>>.",
    _INVALID_DOMAIN_NUMBER :
        "The domain definition is missing in the yaml file.",
    _INVALID_DOMAIN_LENGTH :
        "The length of the domain must be between [1, 16], "\
        "but the actual length of the domain <<%s>> is <<%d>>.",
    _INVALID_DOMAIN_CHAR :
        "The character of the domain must be in [A-Z0-9_], "\
        "but the domain <<%s>> actually has <<%c>>.",
    _INVALID_DOMAIN_CHAR_HEAD :
        "The header of the domain must be in [A-Z], "\
        "but the actual header of the domain <<%s>> is <<%c>>.",
    _INVALID_EVENT_NUMBER :
        "The number of the events must be between [1, 4096], ."\
        "but there are actually <<%d>> events.",
    _INVALID_EVENT_LENGTH :
        "The length of the event must be between [1, 32], "\
        "but the actual length of the event <<%s>> is <<%d>>.",
    _INVALID_EVENT_CHAR :
        "The character of the event must be in [A-Z0-9_], "\
        "but the event <<%s>> actually has <<%c>>.",
    _INVALID_EVENT_CHAR_HEAD :
        "The header of the event must be in [A-Z], "\
        "but the actual header of the event <<%s>> is <<%c>>.",
    _MISSING_EVENT_BASE :
        "Event <<%s>> is missing __BASE definition.",
    _MISSING_EVENT_TYPE :
        "__BASE for event <<%s>> is missing type definition.",
    _INVALID_EVENT_TYPE :
        "The type of the event <<%s>> must be in "\
        "[FAULT, STATISTIC, SECURITY, BEHAVIOR], "\
        "but the actual event type is <<%s>>.",
    _MISSING_EVENT_LEVEL :
        "__BASE for event <<%s>> is missing level definition.",
    _INVALID_EVENT_LEVEL :
        "The level of the event <<%s>> must be in [CRITICAL, MINOR], "\
        "but the actual event level is <<%s>>.",
    _MISSING_EVENT_DESC :
        "__BASE for event <<%s>> is missing desc definition.",
    _INVALID_EVENT_DESC_LENGTH :
        "The length of the event desc must be between [3, 128], "\
        "but the actual length of the event <<%s>> desc <<%s>> is <<%d>>.",
    _INVALID_EVENT_TAG_NUM :
        "The number of the event tags must be between [0, 5], "\
        "but actually the event <<%s>> tag <<%s>> has <<%d>> tags.",
    _INVALID_EVENT_TAG_LEN :
        "The length of the event tag must be between [1, 16], "\
        "but the actual length of the event <<%s>> tag <<%s>> is <<%d>>.",
    _INVALID_EVENT_TAG_CHAR :
        "The character of the event tag must be in [A-Za-z0-9], "\
        "but the event <<%s>> tag <<%s>> actually has <<%c>>.",
    _DUPLICATE_EVENT_TAG :
        "Event tag should not be duplicated, "\
        "but tag <<%s>> for event <<%s>> has multiple identical.",
    _INVALID_EVENT_BASE_KEY :
        "Event <<%s>> __BASE key should be [type, level, tag, desc], "\
        "but actually has an invalid key <<%s>>.",
    _INVALID_EVENT_PARAM_NUM :
        "The number of the event param must be between [0, 128], "\
        "but actually the event <<%s>> has <<%d>> params.",
    _INVALID_EVENT_PARAM_LEN :
        "The length of the event param must be between [1, 32], "\
        "but the actual length of the event <<%s>> param <<%s>> is <<%d>>.",
    _INVALID_EVENT_PARAM_CHAR :
        "The character of the event param must be in [A-Z0-9_], "\
        "but the event <<%s>> param <<%s>> actually has <<%c>>.",
    _INVALID_EVENT_PARAM_CHAR_HEAD:
        "The header of the event param must be in [A-Z], "\
        "but the actual header of the event <<%s>> param <<%s>> is <<%c>>.",
    _MISSING_EVENT_PARAM_TYPE :
        "Event <<%s>> param <<%s>> is missing type definition.",
    _INVALID_EVENT_PARAM_TYPE :
        "The type of the event <<%s>> param <<%s>> must be in "\
        "[BOOL, INT8, UINT8, INT16, UINT16, INT32, UINT32, INT64, UINT64, "\
        "FLOAT, DOUBLE, STRING], but the actual type is <<%s>>.",
    _INVALID_EVENT_PARAM_ARRSIZE :
        "The arrsize of the event param must be between [1, 100], "\
        "but the actual arrsize of the event <<%s>> param <<%s>> is <<%d>>.",
    _MISSING_EVENT_PARAM_DESC :
        "Event <<%s>> param <<%s>> is missing desc definition.",
    _INVALID_EVENT_PARAM_DESC_LEN :
        "The length of the event param desc must be between [3, 128], "\
        "but the actual length of the event <<%s>> param <<%s>> "\
        "desc <<%s>> is <<%d>>.",
    _INVALID_EVENT_PARAM_KEY :
        "Event <<%s>> param <<%s>> key should be [type, arrsize, desc], "\
        "but actually has an invalid key <<%s>>.",
    _DEPRECATED_EVENT_NAME_PREFIX :
        "Event <<%s>> should not start with domain <<%s>>.",
    _DEPRECATED_PARAM_NAME_PREFIX :
        "Event param <<%s>> should not start with event <<%s>>.",
    _DEPRECATED_TAG_NAME :
        "Event tag <<%s>> should not be same as %s <<%s>>.",
    _DEPRECATED_EVENT_DESC_NAME :
        "Event desc <<%s>> should not be same as event <<%s>> and "\
        "should be more detailed.",
    _DEPRECATED_PARAM_DESC_NAME :
        "Event param desc <<%s>> should not be same as event <<%s>> "\
        "param <<%s>> and should be more detailed.",
    _INVALID_DOMAIN_DEF :
        "The definition type of the domain must be string.",
    _INVALID_EVENT_DEF :
        "The definition type of the event <<%s>> must be dictionary.",
    _INVALID_EVENT_BASE_DEF :
        "The definition type of the event <<%s>> __BASE must be dictionary.",
    _INVALID_EVENT_TYPE_DEF :
        "The definition type of the event <<%s>> type must be string.",
    _INVALID_EVENT_LEVEL_DEF :
        "The definition type of the event <<%s>> level must be string.",
    _INVALID_EVENT_DESC_DEF :
        "The definition type of the event <<%s>> desc must be string.",
    _INVALID_EVENT_TAG_DEF :
        "The definition type of the event <<%s>> tag must be string.",
    _INVALID_EVENT_PARAM_DEF :
        "The definition type of the event <<%s>> param <<%s>> "\
        "must be dictionary.",
    _INVALID_PARAM_TYPE_DEF :
        "The definition type of the event <<%s>> param <<%s>> "\
        "type must be string.",
    _INVALID_PARAM_ARRSIZE_DEF :
        "The definition type of the event <<%s>> param <<%s>> "\
        "arrsize must be integer.",
    _INVALID_PARAM_DESC_DEF :
        "The definition type of the event <<%s>> param <<%s>> "\
        "desc must be string.",
    _DUPLICATE_KEY_DEF :
        "Duplicate key <<%s>> exists%s.",
}


_domain_dict = {}
_warning_dict = {}
_warning_file_path = ""
_yaml_file_path = ""
_warning_file = None
_hisysevent_parse_res = True
_deprecated_dict = {}


class _UniqueKeySafeLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        mapping = []
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if (key in mapping):
                _build_warning_info(_DUPLICATE_KEY_DEF,
                    (key, key_node.start_mark))
                global _hisysevent_parse_res
                _hisysevent_parse_res = False
                continue
            mapping.append(key)
        return super().construct_mapping(node, deep)


def _build_header(info_dict):
    table_header = "HiSysEvent yaml file: <<%s>>" % _yaml_file_path
    info_dict[_yaml_file_path] = [table_header]
    table_boundary = "-".rjust(100, '-')
    info_dict[_yaml_file_path].append(table_boundary)
    table_title = "Failed Item".ljust(50) + "|    " + "Failed Reason"
    info_dict[_yaml_file_path].append(table_title)
    info_dict[_yaml_file_path].append(table_boundary)


def _build_warning_header():
    global _warning_dict
    _build_header(_warning_dict)


def _build_deprecated_header():
    global _deprecated_dict
    _build_header(_deprecated_dict)


def _build_warning_info(item, values):
    detail = _WARNING_MAP[item] % values
    content = item.ljust(50) + "|    " + detail
    global _warning_dict
    _warning_dict[_yaml_file_path].append(content)


# Current set to warning, subsequent set to error.
def _build_deprecated_info(item, values):
    _build_deprecated_header()
    detail = _WARNING_MAP[item] % values
    content = item.ljust(50) + "|    " + detail
    global _deprecated_dict
    _deprecated_dict[_yaml_file_path].append(content)


def _open_warning_file(output_path):
    global _warning_file_path
    _warning_file_path = os.path.join(output_path, 'hisysevent_warning.txt')
    global _warning_file
    _warning_file = open(_warning_file_path, 'w+')


def _close_warning_file():
    if not _warning_file:
        _warning_file.close()


def _output_warning():
    for warning_list in _warning_dict.values():
        if len(warning_list) > 4 or len(warning_list) == 1:
            warning_list.append("")
            for content in warning_list:
                print(content)
                print(content, file=_warning_file)


def _output_deprecated(output_path):
    deprecated_file = open(os.path.join(output_path, 'hisysevent_deprecated.txt'), 'w+')
    for deprecated_list in _deprecated_dict.values():
        deprecated_list.append("")
        for content in deprecated_list:
            print(content, file=deprecated_file)
    if not deprecated_file:
        deprecated_file.close()


def _exit_sys():
    print("Failed to parse the yaml file. For details about the error "\
        "information, see file %s." % (_warning_file_path))
    _output_warning()
    _close_warning_file()
    sys.exit(1)


def _is_valid_length(content, len_min, len_max):
    return len(content) >= len_min and len(content) <= len_max


def _is_valid_header(content):
    return len(content) == 0 or (content[0] >= 'A' and content[0] <= 'Z')


def _is_invalid_char(ch):
    return (ch >= 'A' and ch <= 'Z') or (ch >= '0' and ch <= '9') or ch == '_'


def _check_invalid_char(content):
    for ch in iter(content):
        if not _is_invalid_char(ch):
            return ch
    return None


def _check_domain_duplicate(domain):
    if domain in _domain_dict:
        _build_warning_info(_DUPLICATE_DOMAIN, (domain, _domain_dict[domain]))
        return False
    else:
        _domain_dict[domain] = _yaml_file_path
        return True


def _check_event_domain(yaml_info):
    if not "domain" in yaml_info:
        _build_warning_info(_INVALID_DOMAIN_NUMBER, ())
        return False
    if not isinstance(yaml_info["domain"], str):
        _build_warning_info(_INVALID_DOMAIN_DEF, ())
        return False
    domain = yaml_info["domain"]
    check_res = True
    if not _is_valid_length(domain, 1, 16):
        _build_warning_info(_INVALID_DOMAIN_LENGTH, (domain, len(domain)))
        check_res = False
    if not _is_valid_header(domain):
        _build_warning_info(_INVALID_DOMAIN_CHAR_HEAD, (domain, domain[0]))
        check_res = False
    invalid_ch = _check_invalid_char(domain)
    if invalid_ch:
        _build_warning_info(_INVALID_DOMAIN_CHAR, (domain, invalid_ch))
        check_res = False
    if not _check_domain_duplicate(domain):
        check_res = False
    return check_res


def _check_yaml_format(yaml_info):
    if not yaml_info:
        _build_warning_info(_INVALID_YAML, ("The yaml file is empty"))
        return False
    if not isinstance(yaml_info, dict):
        _build_warning_info(_INVALID_YAML,
            ("The content of yaml file is invalid"))
        return False
    return True


def _check_event_name(domain, event_name):
    check_res = True
    if not _is_valid_length(event_name, 1, 32):
        _build_warning_info(_INVALID_EVENT_LENGTH,
            (event_name, len(event_name)))
        check_res = False
    if len(domain) > 0 and event_name.startswith(domain):
        _build_deprecated_info(_DEPRECATED_EVENT_NAME_PREFIX,
            (event_name, domain))
    if not _is_valid_header(event_name):
        _build_warning_info(_INVALID_EVENT_CHAR_HEAD,
            (event_name, event_name[0]))
        check_res = False
    invalid_ch = _check_invalid_char(event_name)
    if invalid_ch:
        _build_warning_info(_INVALID_DOMAIN_CHAR, (event_name, invalid_ch))
        check_res = False
    return check_res


def _check_event_type(event_name, event_base):
    if not "type" in event_base:
        _build_warning_info(_MISSING_EVENT_TYPE, (event_name))
        return False
    else:
        if not isinstance(event_base["type"], str):
            _build_warning_info(_INVALID_EVENT_TYPE_DEF, event_name)
            return False
        type_list = ["FAULT", "STATISTIC", "SECURITY", "BEHAVIOR"]
        if not event_base["type"] in type_list:
            _build_warning_info(_INVALID_EVENT_TYPE,
                (event_name, event_base["type"]))
            return False
    return True


def _check_event_level(event_name, event_base):
    if not "level" in event_base:
        _build_warning_info(_MISSING_EVENT_LEVEL, (event_name))
        return False
    else:
        if not isinstance(event_base["level"], str):
            _build_warning_info(_INVALID_EVENT_LEVEL_DEF, event_name)
            return False
        level_list = ["CRITICAL", "MINOR"]
        if not event_base["level"] in level_list:
            _build_warning_info(_INVALID_EVENT_LEVEL,
                (event_name, event_base["level"]))
            return False
    return True


def _check_event_desc(event_name, event_base):
    if not "desc" in event_base:
        _build_warning_info(_MISSING_EVENT_DESC, (event_name))
        return False
    else:
        event_desc = event_base["desc"]
        if not isinstance(event_desc, str):
            _build_warning_info(_INVALID_EVENT_DESC_DEF, event_name)
            return False
        check_res = True
        if event_desc.lower() == event_name.lower():
            _build_deprecated_info(_DEPRECATED_EVENT_DESC_NAME,
                (event_desc, event_name))
        if not _is_valid_length(event_desc, 3, 128):
            _build_warning_info(_INVALID_EVENT_DESC_LENGTH,
                (event_name, event_desc, len(event_desc)))
            check_res = False
        return check_res


def _check_tag_char(event_tag):
    for ch in iter(event_tag):
        if not ch.isalnum():
            return ch
    return None


def _check_tag_name(event_name, event_base, tag_name):
    check_res = True
    if tag_name.lower() == event_name.lower():
        _build_deprecated_info(_DEPRECATED_TAG_NAME,
            (tag_name, "event", event_name))
    if "type" in event_base and tag_name.lower() == event_base["type"].lower():
        _build_deprecated_info(_DEPRECATED_TAG_NAME,
            (tag_name, "event type", event_base["type"]))
    if not _is_valid_length(tag_name, 1, 16):
        _build_warning_info(_INVALID_EVENT_TAG_LEN,
            (event_name, tag_name, len(tag_name)))
        check_res = False
    invalid_ch = _check_tag_char(tag_name)
    if invalid_ch:
        _build_warning_info(_INVALID_EVENT_TAG_CHAR,
            (event_name, tag_name, invalid_ch))
        check_res = False
    return check_res


def _get_duplicate_tag(tag_list):
    tag_dict = dict(Counter(tag_list))
    for key, value in tag_dict.items():
        if value > 1:
            return key
    return None


def _check_event_tag(event_name, event_base):
    if not "tag" in event_base:
        return True
    event_tag = event_base["tag"]
    if not isinstance(event_tag, str):
        _build_warning_info(_INVALID_EVENT_TAG_DEF, event_name)
        return False
    tag_list = event_tag.split()
    if not _is_valid_length(tag_list, 1, 5):
        _build_warning_info(_INVALID_EVENT_TAG_NUM,
            (event_name, event_tag, len(tag_list)))
        return False
    check_res = True
    for each_tag in tag_list:
        if not _check_tag_name(event_name, event_base, each_tag):
            check_res = False
    dup_tag = _get_duplicate_tag(tag_list)
    if dup_tag:
        _build_warning_info(_DUPLICATE_EVENT_TAG, (dup_tag, event_name))
        check_res = False
    return check_res


def _check_base_key(event_name, event_base):
    key_list = ["type", "level", "tag", "desc"]
    for base_key in event_base.keys():
        if not base_key in key_list:
            _build_warning_info(_INVALID_EVENT_BASE_KEY,
                (event_name, base_key))
            return False
    return True


def _check_event_base(event_name, event_def):
    if not "__BASE" in event_def:
        _build_warning_info(_MISSING_EVENT_BASE, (event_name))
        return False
    event_base = event_def["__BASE"]
    if not isinstance(event_base, dict):
        _build_warning_info(_INVALID_EVENT_BASE_DEF, (event_name))
        return False
    check_res = True
    if not _check_event_type(event_name, event_base):
        check_res = False
    if not _check_event_level(event_name, event_base):
        check_res = False
    if not _check_event_desc(event_name, event_base):
        check_res = False
    if not _check_event_tag(event_name, event_base):
        check_res = False
    if not _check_base_key(event_name, event_base):
        check_res = False
    return check_res


def _check_param_name(event_name, name):
    check_res = True
    if not _is_valid_length(name, 1, 32):
        _build_warning_info(_INVALID_EVENT_PARAM_LEN,
            (event_name, name, len(name)))
        check_res = False
    if len(event_name) > 0 and name.startswith(event_name):
        _build_deprecated_info(_DEPRECATED_PARAM_NAME_PREFIX, (name, event_name))
    if not _is_valid_header(name):
        _build_warning_info(_INVALID_EVENT_PARAM_CHAR_HEAD,
            (event_name, name, name[0]))
        check_res = False
    invalid_ch = _check_invalid_char(name)
    if invalid_ch:
        _build_warning_info(_INVALID_EVENT_PARAM_CHAR,
            (event_name, name, invalid_ch))
        check_res = False
    return check_res


def _check_param_type(event_name, param_name, param_info):
    if not "type" in param_info:
        _build_warning_info(_MISSING_EVENT_PARAM_TYPE,
            (event_name, param_name))
        return False
    else:
        if not isinstance(param_info["type"], str):
            _build_warning_info(_INVALID_PARAM_TYPE_DEF,
                (event_name, param_name))
            return False
        type_list = ["BOOL", "INT8", "UINT8", "INT16", "UINT16", "INT32",
            "UINT32", "INT64", "UINT64", "FLOAT", "DOUBLE", "STRING"]
        if not param_info["type"] in type_list:
            _build_warning_info(_INVALID_EVENT_PARAM_TYPE,
                (event_name, param_name, param_info["type"]))
            return False
    return True


def _check_param_arrsize(event_name, param_name, param_info):
    if not "arrsize" in param_info:
        return True
    arrsize = param_info["arrsize"]
    if not isinstance(arrsize, int):
        _build_warning_info(_INVALID_PARAM_ARRSIZE_DEF,
            (event_name, param_name))
        return False
    if not (arrsize >= 1 and arrsize <= 100):
        _build_warning_info(_INVALID_EVENT_PARAM_ARRSIZE,
            (event_name, param_name, arrsize))
        return False
    return True


def _check_param_desc(event_name, param_name, param_info):
    if not "desc" in param_info:
        _build_warning_info(_MISSING_EVENT_PARAM_DESC,
            (event_name, param_name))
        return False
    else:
        param_desc = param_info["desc"]
        if not isinstance(param_desc, str):
            _build_warning_info(_INVALID_PARAM_DESC_DEF,
                (event_name, param_name))
            return False
        check_res = True
        if param_desc.lower() == param_name.lower():
            _build_deprecated_info(_DEPRECATED_PARAM_DESC_NAME,
                (param_desc, event_name, param_name))
        if not _is_valid_length(param_desc, 3, 128):
            _build_warning_info(_INVALID_EVENT_PARAM_DESC_LEN,
                (event_name, param_name, param_desc, len(param_desc)))
            check_res = False
        return check_res


def _check_param_key(event_name, param_name, param_info):
    key_list = ["type", "arrsize", "desc"]
    for key in param_info.keys():
        if not key in key_list:
            _build_warning_info(_INVALID_EVENT_PARAM_KEY,
                (event_name, param_name, key))
            return False
    return True


def _check_param_info(event_name, param_name, param_info):
    check_res = True
    if not _check_param_type(event_name, param_name, param_info):
        check_res = False
    if not _check_param_arrsize(event_name, param_name, param_info):
        check_res = False
    if not _check_param_desc(event_name, param_name, param_info):
        check_res = False
    if not _check_param_key(event_name, param_name, param_info):
        check_res = False
    return check_res


def _check_event_param(event_name, event_def):
    sub_num = (0, 1)["__BASE" in event_def]
    check_res = True
    if not _is_valid_length(event_def, 0 + sub_num, 128 + sub_num):
        _build_warning_info(_INVALID_EVENT_PARAM_NUM,
            (event_name, (len(event_def) - sub_num)))
        check_res = False
    for param_name in event_def.keys():
        if param_name == "__BASE":
            continue
        if not _check_param_name(event_name, param_name):
            check_res = False
        param_info = event_def[param_name]
        if not isinstance(param_info, dict):
            _build_warning_info(_INVALID_EVENT_PARAM_DEF,
                (event_name, param_name))
            check_res = False
            continue
        if not _check_param_info(event_name, param_name, param_info):
            check_res = False
    return check_res


def _check_event_def(event_name, event_def):
    check_res = True
    if not _check_event_base(event_name, event_def):
        check_res = False
    if not _check_event_param(event_name, event_def):
        check_res = False
    return check_res


def _check_event_info(domain, event_info):
    event_name = event_info[0]
    event_def = event_info[1]
    check_res = True
    if not isinstance(event_def, dict):
        _build_warning_info(_INVALID_EVENT_DEF, (event_name))
        return False
    if not _check_event_name(domain, event_name):
        check_res = False
    if not _check_event_def(event_name, event_def):
        check_res = False
    return check_res


def _check_events_info(domain, yaml_info):
    event_num = len(yaml_info)
    if not (event_num >= 1 and event_num <= 4096):
        _build_warning_info(_INVALID_EVENT_NUMBER, (event_num))
        return False
    check_res = True
    for event_info in yaml_info.items():
        if not _check_event_info(domain, event_info):
            check_res = False
    return check_res


def merge_hisysevent_config(yaml_list, output_path):
    if (len(output_path) == 0):
        present_path = os.path.dirname(os.path.abspath(__file__))
        output_path = present_path
    if (len(yaml_list) == 0):
        _build_warning_info(_EMPTY_YAML, ())
        _exit_sys()
    if not os.path.exists(output_path):
        os.makedirs(output_path, exist_ok=True)
    _open_warning_file(output_path)

    yaml_info_dict = {}
    global _hisysevent_parse_res
    for yaml_path in yaml_list:
        global _yaml_file_path
        _yaml_file_path = yaml_path.replace("../", "")
        _build_warning_header()
        yaml_file = open(yaml_path, 'r')
        yaml_info = yaml.load(yaml_file, Loader=_UniqueKeySafeLoader)
        if not _check_yaml_format(yaml_info):
            _hisysevent_parse_res = False
            continue
        if not _check_event_domain(yaml_info):
            _hisysevent_parse_res = False
            continue
        domain = yaml_info["domain"]
        del yaml_info["domain"]
        if not _check_events_info(domain, yaml_info):
            _hisysevent_parse_res = False
            continue
        yaml_info_dict[domain] = yaml_info
    _output_deprecated(output_path)
    if not _hisysevent_parse_res:
        _exit_sys()

    hisysevent_def_file = os.path.join(output_path, 'hisysevent.def')
    with open(hisysevent_def_file, 'w') as j:
        json.dump(yaml_info_dict, j, indent=4)
    print("The hisysevent.def {} is generated successfully."
        .format(hisysevent_def_file))
    _close_warning_file()
    return hisysevent_def_file


def main(argv):
    parser = argparse.ArgumentParser(description='yaml list')
    parser.add_argument("--yaml-list", nargs='+', required=True)
    parser.add_argument("--def-path", required=True)
    args = parser.parse_args(argv)
    hisysevent_def_file = merge_hisysevent_config(args.yaml_list,
        args.def_path)
    print(hisysevent_def_file)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
