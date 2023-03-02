#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

import tempfile
import platform
import re
import subprocess
import io
import argparse
import os
import sys
import stat

# Set up path to be able to import build_utils
sys.path.append(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
from scripts.util import build_utils


RUSTC_VERSION_LINE = re.compile(r"(\w+): (.*)")
RUSTC_CFG_LINE = re.compile("cargo:rustc-cfg=(.*)")


def host_triple(rustc_path):
    """ Works out the host rustc target. """
    known_vars = dict()
    args = [rustc_path, "-vV"]
    proc = subprocess.Popen(args, stdout=subprocess.PIPE)
    for lines in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        match = RUSTC_VERSION_LINE.match(lines.rstrip())
        if match:
            known_vars[match.group(1)] = match.group(2)
    return known_vars.get("host")


def main():
    parser = argparse.ArgumentParser(description='Run Rust build script.')
    parser.add_argument('--build-script',
                        required=True,
                        help='build script needed to run')
    parser.add_argument('--target', help='rust target triple')
    parser.add_argument('--features', help='features', nargs='+')
    parser.add_argument('--env', help='environment variable', nargs='+')
    parser.add_argument('--output',
                        required=True,
                        help='where to write output rustc flags')
    parser.add_argument('--rust-prefix', required=True,
                        help='rust path prefix')
    parser.add_argument('--generated-files', nargs='+',
                        help='any generated file')
    parser.add_argument('--out-dir', required=True, help='ohos target out dir')
    parser.add_argument('--src-dir', required=True,
                        help='ohos target source dir')

    args = parser.parse_args()
    if platform.system() == "Windows":
        rustc_path = os.path.join(args.rust_prefix, "rustc.exe")
    else:
        rustc_path = os.path.join(args.rust_prefix, "rustc")

    with tempfile.TemporaryDirectory() as tempdir:
        env = {}  # try to avoid build scripts depending on other things
        env["RUSTC"] = os.path.abspath(rustc_path)
        env["HOST"] = host_triple(rustc_path)
        env["CARGO_MANIFEST_DIR"] = os.path.abspath(args.src_dir)
        env["OUT_DIR"] = tempdir

        if args.target is not None:
            env["TARGET"] = args.target
        else:
            env["TARGET"] = env.get("HOST")

        target_components = env.get("TARGET").split("-")
        env["CARGO_CFG_TARGET_ARCH"] = target_components[0]
        if args.env:
            for environment in args.env:
                (key, value) = environment.split("=")
                env[key] = value
        if args.features:
            for feature in args.features:
                feature_name = feature.upper().replace("-", "_")
                env["CARGO_FEATURE_%s" % feature_name] = "1"

        # Pass through a couple which are useful for diagnostics
        if os.environ.get("RUST_LOG"):
            env["RUST_LOG"] = os.environ.get("RUST_LOG")
        if os.environ.get("RUST_BACKTRACE"):
            env["RUST_BACKTRACE"] = os.environ.get("RUST_BACKTRACE")

        process = subprocess.run([os.path.abspath(args.build_script)],
                                 env=env,
                                 cwd=args.src_dir,
                                 encoding='utf8',
                                 capture_output=True)

        if process.stderr.rstrip():
            print(process.stderr.rstrip(), file=sys.stderr)
        process.check_returncode()

        flags = ""
        for line in process.stdout.split("\n"):
            match = RUSTC_CFG_LINE.match(line.rstrip())
            if match:
                flags = "%s--cfg\n%s\n" % (flags, match.group(1))

        with build_utils.atomic_output(args.output) as output:
            output.write(flags.encode("utf-8"))

        if args.generated_files:
            for generated_file in args.generated_files:
                input_path = os.path.join(tempdir, generated_file)
                output_path = os.path.join(args.out_dir, generated_file)
                out_dir = os.path.dirname(output_path)
                if not os.path.exists(out_dir):
                    os.makedirs(out_dir)
                with os.fdopen(os.open(input_path,
                               os.O_RDWR | os.O_CREAT, stat.S_IWUSR | stat.S_IRUSR),
                               'rb') as inputs:
                    with build_utils.atomic_output(output_path) as output:
                        content = inputs.read()
                        output.write(content)


if __name__ == '__main__':
    sys.exit(main())
