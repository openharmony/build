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
from typing import Dict, List


class SubprocessTimeoutError(Exception):
    """Exception raised when subprocess execution times out."""


class SubprocessRunError(Exception):
    """Exception raised when subprocess fails to execute."""


def set_environment(env_path: str) -> Dict[str, str]:
    """Create environment variables with updated LD_LIBRARY_PATH."""
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = env_path
    return env


def build_es2panda_command(es2panda_path: str, arktsconfig: str) -> List[str]:
    """Construct es2panda command arguments."""
    return [es2panda_path, "--arktsconfig", arktsconfig, "--ets-module"]


def run_subprocess(cmd: List[str], timeout: str, env: Dict[str, str]) -> str:
    """
    Execute a subprocess with timeout and environment settings.
    
    Args:
        cmd: Command sequence to execute
        timeout: Maximum execution time in seconds (as string)
        env: Environment variables dictionary
    
    Returns:
        Captured standard output
    
    Raises:
        SubprocessTimeoutError: When process exceeds timeout
        SubprocessRunError: When process returns non-zero status
    """
    try:
        process = subprocess.run(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=int(timeout),  # Convert timeout to int for subprocess.run
            check=True,
            text=True
        )
        return process.stdout
    except subprocess.TimeoutExpired as exc:
        raise SubprocessTimeoutError(f"Command '{' '.join(cmd)}' timed out") from exc
    except subprocess.CalledProcessError as exc:
        raise SubprocessRunError(
            f"Command '{' '.join(cmd)}' failed (code {exc.returncode})\n"
            f"Error output:\n{exc.stderr}"
        ) from exc


def execute_es2panda(es2panda_path: str, arktsconfig: str, env_path: str, timeout: str) -> str:
    """Execute es2panda compilation process."""
    cmd = build_es2panda_command(es2panda_path, arktsconfig)
    env = set_environment(env_path)
    return run_subprocess(cmd, timeout, env)


def collect_abc_files(output_dir: str) -> List[str]:
    """Recursively collect all .abc files in directory."""
    abc_files = []
    for root, _, files in os.walk(output_dir):
        for file in files:
            if file.endswith(".abc"):
                abc_files.append(os.path.join(root, file))
    return abc_files


def build_ark_link_command(ark_link_path: str, output_path: str, abc_files: List[str]) -> List[str]:
    """Construct ark_link command arguments."""
    return [ark_link_path, f"--output={output_path}", "--", *abc_files]


def execute_ark_link(
    ark_link_path: str,
    output_path: str,
    output_dir: str,
    env_path: str,
    timeout: str
) -> str:
    """Execute ark_link process to bundle ABC files."""
    abc_files = collect_abc_files(output_dir)
    cmd = build_ark_link_command(ark_link_path, output_path, abc_files)
    env = set_environment(env_path)
    return run_subprocess(cmd, timeout, env)


def parse_arguments() -> argparse.Namespace:
    """Configure and parse command line arguments."""
    parser = argparse.ArgumentParser()

    parser.add_argument("--es2panda", type=str, required=True,
                        help="Path to es2panda executable")
    parser.add_argument("--ark-link", type=str, required=True,
                        help="Path to ark_link executable")
    parser.add_argument("--arktsconfig", type=str, required=True,
                        help="Path to arktsconfig.json configuration file")
    parser.add_argument("--output", type=str, required=True,
                        help="Path for final output file")
    parser.add_argument("--env-path", type=str, required=True,
                        help="Value for LD_LIBRARY_PATH environment variable")
    parser.add_argument("--timeout-limit", type=str, default="1200",
                        help="Process timeout in seconds (default: 1200)")

    return parser.parse_args()


def main() -> None:
    """Main compilation workflow."""
    start_time = time.time()
    args = parse_arguments()

    try:
        with open(args.arktsconfig, "r", encoding="utf-8") as f:
            config = json.load(f)

        out_dir = config["compilerOptions"]["outDir"]
        if not os.path.isabs(out_dir):
            base_dir = os.path.dirname(os.path.abspath(args.arktsconfig))
            out_dir = os.path.join(base_dir, out_dir)

        execute_es2panda(args.es2panda, args.arktsconfig, args.env_path, args.timeout_limit)
        execute_ark_link(args.ark_link, args.output, out_dir, args.env_path, args.timeout_limit)

        print("Compilation succeeded!")
        print(f"Total time: {time.time() - start_time:.2f} seconds")

    except SubprocessTimeoutError as e:
        print(f"Timeout Error: {e}")
    except SubprocessRunError as e:
        print(f"Execution Error: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error in {args.arktsconfig}: {e}")
    except FileNotFoundError as e:
        print(f"File Not Found: {e}")
    except KeyError as e:
        print(f"Missing configuration key: {e}")


if __name__ == "__main__":
    main()
