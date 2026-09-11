#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2026 Huawei Device Co., Ltd.
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
import os
import subprocess
import sys


def main():
    version_script = os.environ.get("RUST_VERSION_SCRIPT")
    original_linker = os.environ.get("RUST_ORIGINAL_LINKER")

    if not original_linker:
        print("RUST_ORIGINAL_LINKER is not set", file=sys.stderr)
        sys.exit(1)

    new_args = []
    for arg in args:
        if arg.startswith("-Wl,--version-script"):
            script_path = arg[len("-Wl,--version-script"): ]
            if version_script and os.path.abspath(script_path) == os.path.abspath(version_script):
                new_args.append(arg)
            continue
        if arg == "-Wl,--no-undefined-version":
            continue
        new_args.append(arg)
    
    if version_script:
        new_args.append(f"-Wl,--version-script={version_script}")

    result = subprocess.run([original_linker] + new_args)
    sys.exit(result.returncode)

if __name__ == '__main__':
    main()
