#!/usr/bin/env python3
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
#

import argparse

from distutils.util import strtobool


class ArgsFactory():

    def __init__(self) -> None:
        pass

    @staticmethod
    def genenic_add_option(parser: argparse.ArgumentParser, arg: dict) -> argparse.ArgumentParser:
        if arg['argType'] == 'bool':
            return _add_bool_option(parser, arg)
        elif arg['argType'] == 'str':
            return _add_str_option(parser, arg)
        elif arg['argType'] == 'list':
            return _add_list_option(parser, arg)


def _add_bool_option(parser: argparse.ArgumentParser, arg: dict) -> argparse.ArgumentParser:
    if arg['argAttribute'].get('abbreviation'):
        return _add_bool_abbreviation_option(parser, arg)
    else:
        return parser.add_argument(arg['argName'], help=arg['argHelp'],
                                   default=strtobool(arg['argDefault']), choices=['True', 'False'])


def _add_str_option(parser: argparse.ArgumentParser, arg: dict) -> argparse.ArgumentParser:
    if arg['argAttribute'].get('optional'):
        if arg['argAttribute'].get('abbreviation'):
            return _add_str_optional_abbreviation_option(parser, arg)
        else:
            return _add_str_optional_option(parser, arg)
    elif arg['argAttribute'].get('abbreviation'):
        return _add_str_abbreviation_option(parser, arg)
    else:
        return parser.add_argument(arg['argName'], help=arg['argHelp'],
                                   default=arg['argDefault'])


def _add_bool_abbreviation_option(parser: argparse.ArgumentParser, arg: dict) -> argparse.ArgumentParser:
    return parser.add_argument(arg['argAttribute'].get('abbreviation'), arg['argName'], help=arg['argHelp'],
                               default=strtobool(arg['argDefault']),  action="store_true")


def _add_list_option(parser: argparse.ArgumentParser, arg: dict) -> argparse.ArgumentParser:
    return parser.add_argument(arg['argName'], help=arg['argHelp'],
                               nargs='*', default=arg['argDefault'], action='append')


def _add_str_abbreviation_option(parser: argparse.ArgumentParser, arg: dict) -> argparse.ArgumentParser:
    return parser.add_argument(arg['argAttribute'].get('abbreviation'), arg['argName'], help=arg['argHelp'],
                               default=arg['argDefault'])


def _add_str_optional_option(parser: argparse.ArgumentParser, arg: dict) -> argparse.ArgumentParser:
    return parser.add_argument(arg['argName'], help=arg['argHelp'],
                               default=arg['argDefault'], choices=arg['argAttribute'].get('optional'))


def _add_str_optional_abbreviation_option(parser: argparse.ArgumentParser, arg: dict) -> argparse.ArgumentParser:
    return parser.add_argument(arg['argAttribute'].get('abbreviation'), arg['argName'], help=arg['argHelp'],
                               default=arg['argDefault'], choices=arg['argAttribute'].get('optional'))
