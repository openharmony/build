#!/usr/bin/env python
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

import os
import sys
import platform


def check_linux_cpu() -> int:
    if sys.platform == 'linux' and platform.machine().lower() == 'aarch64':
        print("host cpu is aarch64")
    return 0


def main():
    if sys.argv[1] == "cpu":
        return check_linux_cpu()
    else:
        return 0


if __name__ == '__main__':
    sys.exit(main())