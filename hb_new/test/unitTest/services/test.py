#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
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

A_CONST = 1


class StatusCode():

    def __init__(self, status=True, info=''):
        self.status = status
        self.info = info


def check_status(func):
    status = func()
    if not status.status:
        raise Exception("ERROR")
    return StatusCode


@check_status
def func_1() -> StatusCode:
    if A_CONST == 1:
        return StatusCode()
    else:
        return StatusCode(False, "error")


def main():
    func_1()
    print(func_1)


if __name__ == "__main__":
    sys.exit(main())
