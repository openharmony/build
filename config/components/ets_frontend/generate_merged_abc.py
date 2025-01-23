#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Huawei Device Co., Ltd.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional


class SubprocessTimeoutError(Exception):
    """Exception raised when subprocess execution times out."""


class SubprocessRunError(Exception):
    """Exception raised when subprocess fails to execute."""


def generate_arktsconfig(output_path: str, args: argparse.Namespace) -> None:
    """
    Generate arktsconfig.json configuration file.

    Args:
        output_path: Output file path for arktsconfig.json
        args: An argparse.Namespace object containing configuration parameters.
    """
    config = {
        "compilerOptions": {
            "baseUrl": "." if args.base_url is None else args.base_url,
            "paths": {
                "std": args.std.split(','),
                "escompat": args.escompat.split(',')
            }
        }
    }

    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)


def set_environment(env_path: str) -> Dict[str, str]:
    """Set the environment variable LD_LIBRARY_PATH."""
    return {"LD_LIBRARY_PATH": str(env_path)}


def build_es2panda_command(es2panda_path: str, arktsconfig: str) -> List[str]:
    """Build the es2panda command."""
    return [es2panda_path, "--arktsconfig", arktsconfig, "--ets-module"]


def run_subprocess(cmd: List[str], timeout: int, env: Dict[str, str]) -> str:
    """
    Run a subprocess with the given command, timeout, and environment.
    
    Args:
        cmd: Command to execute
        timeout: Timeout in seconds
        env: Environment variables
    
    Returns:
        Standard output from command execution
    
    Raises:
        SubprocessTimeoutError: If command execution times out
        SubprocessRunError: If command returns non-zero exit code
    """
    try:
        process = subprocess.run(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=True,
            text=True
        )
        return process.stdout
    except subprocess.TimeoutExpired as exc:
        raise SubprocessTimeoutError(f"Command '{' '.join(cmd)}' timed out") from exc
    except subprocess.CalledProcessError as exc:
        raise SubprocessRunError(
            f"Command '{' '.join(cmd)}' failed with code {exc.returncode}\n"
            f"STDERR: {exc.stderr}"
        ) from exc


def es2panda(es2panda_path: str, arktsconfig: str, env_path: str, timeout: int) -> str:
    """Run es2panda subprocess."""
    cmd = build_es2panda_command(es2panda_path, arktsconfig)
    env = set_environment(env_path)
    return run_subprocess(cmd, timeout, env)


def collect_abc_files(folder: str) -> List[str]:
    """Collect all .abc files in the given folder."""
    abc_files = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith(".abc"):
                abc_files.append(os.path.join(root, file))
    return abc_files


def build_ark_link_command(ark_link_path: str, output_path: str, abc_files: List[str]) -> List[str]:
    """Build the ark_link command."""
    return [ark_link_path, f"--output={output_path}", "--", *abc_files]


def ark_link(ark_link_path: str, output_path: str, arktsconfig: str, env_path: str, timeout: int) -> str:
    """Run ark_link subprocess."""
    arktsconfig_dir = os.path.dirname(arktsconfig)
    abc_files = collect_abc_files(arktsconfig_dir)
    cmd = build_ark_link_command(ark_link_path, output_path, abc_files)
    env = set_environment(env_path)
    return run_subprocess(cmd, timeout, env)


def move_intermediate_abc_files_to_cache(output_path: str, arktsconfig: str, cache_path: str) -> None:
    """
    Move intermediate abc files to the cache folder while preserving the original path structure.
    Excludes the specified output_path even if it resides within the directory structure.

    Args:
        output_path: Absolute path to the final output file (should not be moved)
        arktsconfig: Path to arktsconfig.json
        cache_path: Path to cache directory
    """
    arktsconfig_dir = os.path.dirname(os.path.normpath(arktsconfig))
    normalized_output = os.path.normpath(os.path.normcase(output_path))

    for root, _, files in os.walk(arktsconfig_dir):
        for file in files:
            if not file.endswith(".abc"):
                continue

            file_path = os.path.normpath(os.path.join(root, file))
            normalized_file = os.path.normcase(file_path)

            if normalized_file == normalized_output:
                continue
            try:
                relative_path = os.path.relpath(file_path, arktsconfig_dir)
                destination_path = os.path.join(cache_path, relative_path)
                destination_dir = os.path.dirname(destination_path)
                os.makedirs(destination_dir, exist_ok=True)    
                shutil.move(file_path, destination_path)
            except OSError as e:
                print(f"Failed to move {file_path} to {destination_path}: {e.strerror}")


def move_intermediate_arktsconfig_json_to_cache(arktsconfig_path: str, cache_path: str) -> None:
    """Move arktsconfig.json to cache directory."""
    os.makedirs(cache_path, exist_ok=True)
    file_name = os.path.basename(arktsconfig_path)
    destination_path = os.path.join(cache_path, file_name)
    shutil.move(arktsconfig_path, destination_path)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--es2panda", help="path to es2panda", required=True)
    parser.add_argument("--ark-link", help="path to ark_link", required=True)
    parser.add_argument("--input-dir", help="path to input dir", required=True)
    parser.add_argument("--std", help="paths in arktsconfig.json std", required=True)
    parser.add_argument("--escompat", help="paths in arktsconfig.json escompat", required=True)
    parser.add_argument("--base-url", help="path to arktsconfig.json baseUrl")
    parser.add_argument("--output", help="expect file", required=True)
    parser.add_argument("--env-path", help="env path", required=True)
    parser.add_argument("--cache-path", help="cache path")
    parser.add_argument("--timeout-limit", help="timeout limit")
    return parser.parse_args()


def main() -> None:
    """Main function to run the process."""
    start_time = time.time()
    args = parse_args()
    timeout = int(args.timeout_limit) if args.timeout_limit else 1200  # units: s

    try:
        arktsconfig_path = os.path.join(args.input_dir, "arktsconfig.json")
        generate_arktsconfig(arktsconfig_path, args)
        es2panda(args.es2panda, arktsconfig_path, args.env_path, timeout)
        ark_link(args.ark_link, args.output, arktsconfig_path, args.env_path, timeout)

        if args.cache_path:
            move_intermediate_abc_files_to_cache(args.output, arktsconfig_path, args.cache_path)
            move_intermediate_arktsconfig_json_to_cache(arktsconfig_path, args.cache_path)

        print("Run success!")
        print("used: %.5f seconds" % (time.time() - start_time))
    except SubprocessTimeoutError as e:
        print(f"Timeout error: {e}")
    except SubprocessRunError as e:
        print(f"Run error: {e}")


if __name__ == "__main__":
    main()
