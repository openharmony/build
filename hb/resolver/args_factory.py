#!/usr/bin/env python3
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
#

import argparse

from exceptions.ohos_exception import OHOSException
from containers.status import throw_exception


class ArgsFactory():

    @staticmethod
    @throw_exception
    def genetic_add_option(parser: argparse.ArgumentParser, arg: dict) -> argparse.ArgumentParser:
        if arg['arg_type'] == 'bool':
            return _add_bool_option(parser, arg)
        elif arg['arg_type'] == 'str':
            return _add_str_option(parser, arg)
        elif arg['arg_type'] == 'list':
            return _add_list_option(parser, arg)
        elif arg['arg_type'] == 'subparsers':
            return _add_list_option(parser, arg)
        else:
            raise OHOSException('Unknown arg type "{}" for arg "{}"'
                                .format(arg['arg_type'], arg['arg_name']), "0003")


def _add_bool_option(parser: argparse.ArgumentParser, arg: dict) -> argparse.ArgumentParser:
    if arg['arg_attribute'].get('abbreviation'):
        return _add_bool_abbreviation_option(parser, arg)
    else:
        return parser.add_argument(arg['arg_name'], help=arg['arg_help'], action='store_true',
                                   default=arg['argDefault'])


def _add_str_option(parser: argparse.ArgumentParser, arg: dict) -> argparse.ArgumentParser:
    if arg['arg_attribute'].get('optional'):
        if arg['arg_attribute'].get('abbreviation'):
            return _add_str_optional_abbreviation_option(parser, arg)
        else:
            return _add_str_optional_option(parser, arg)
    elif arg['arg_attribute'].get('abbreviation'):
        return _add_str_abbreviation_option(parser, arg)
    else:
        return parser.add_argument(arg['arg_name'], help=arg['arg_help'],
                                   default=arg['argDefault'])


def _add_list_option(parser: argparse.ArgumentParser, arg: dict) -> argparse.ArgumentParser:
    if arg['arg_attribute'].get('abbreviation'):
        return _add_list_abbreviation_option(parser, arg)
    else:
        return parser.add_argument(arg['arg_name'], help=arg['arg_help'],
                                   nargs='*', default=arg['argDefault'], action='append')


def _add_bool_abbreviation_option(parser: argparse.ArgumentParser, arg: dict) -> argparse.ArgumentParser:
    return parser.add_argument(arg['arg_attribute'].get('abbreviation'), arg['arg_name'], help=arg['arg_help'],
                               default=arg['argDefault'],  action="store_true")


def _add_str_abbreviation_option(parser: argparse.ArgumentParser, arg: dict) -> argparse.ArgumentParser:
    return parser.add_argument(arg['arg_attribute'].get('abbreviation'), arg['arg_name'], help=arg['arg_help'],
                               default=arg['argDefault'])


def _add_str_optional_option(parser: argparse.ArgumentParser, arg: dict) -> argparse.ArgumentParser:
    return parser.add_argument(arg['arg_name'], help=arg['arg_help'],
                               default=arg['argDefault'], choices=arg['arg_attribute'].get('optional'))


def _add_str_optional_abbreviation_option(parser: argparse.ArgumentParser, arg: dict) -> argparse.ArgumentParser:
    return parser.add_argument(arg['arg_attribute'].get('abbreviation'), arg['arg_name'], help=arg['arg_help'],
                               default=arg['argDefault'], choices=arg['arg_attribute'].get('optional'))


def _add_list_abbreviation_option(parser: argparse.ArgumentParser, arg: dict) -> argparse.ArgumentParser:
    return parser.add_argument(arg['arg_attribute'].get('abbreviation'), arg['arg_name'], help=arg['arg_help'],
                               nargs='*', default=arg['argDefault'], action='append')
