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
import sys
import time
from typing import Dict, List


EXIT_CODE = {
    "SUCCESS": 0,
    "TIMEOUT": 1,
    "EXECUTION_FAILURE": 2,
    "CONFIG_ERROR": 3,
    "FILE_NOT_FOUND": 4,
    "MISSING_KEY": 5,
    "UNKNOWN_ERROR": 6,
    "PERMISSION_ERROR": 7,
    "INVALID_CONFIG": 8
}


class SubprocessTimeoutError(Exception):
    """Exception raised when subprocess execution times out."""


class SubprocessRunError(Exception):
    """Exception raised when subprocess fails to execute."""


class ConfigValidationError(Exception):
    """Exception raised when configuration validation fails."""


def set_environment(env_path: str) -> Dict[str, str]:
    """Create environment variables with updated LD_LIBRARY_PATH."""
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = env_path
    return env


def build_es2panda_command(es2panda_path: str, arktsconfig: str) -> List[str]:
    """Construct es2panda command arguments."""
    return [es2panda_path, "--arktsconfig", arktsconfig, "--ets-module"]


def build_es2panda_command_stdlib(es2panda_path: str, arktsconfig: str, dst_path: str) -> List[str]:
    """Construct es2panda command arguments."""
    return [es2panda_path, "--arktsconfig", arktsconfig, "--ets-module", 
        "--gen-stdlib=true", "--output=" + dst_path, "--extension=sts", "--opt-level=2"]


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
        timeout_sec = int(timeout)
        if timeout_sec <= 0:
            raise ValueError("Timeout must be a positive integer")

        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        try:
            stdout, stderr = process.communicate(timeout=timeout_sec)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate(timeout=timeout_sec)
            raise SubprocessTimeoutError(
                f"Command '{' '.join(cmd)}' timed out after {timeout_sec} seconds"
            )

        if process.returncode != 0:
            raise SubprocessRunError(
                f"Command '{' '.join(cmd)}' failed with return code {process.returncode}\n"
                f"Standard Error:\n{stderr}\n"
                f"Standard Output:\n{stdout}"
            )

        return stdout

    except ValueError as e:
        raise SubprocessRunError(f"Invalid timeout value: {e}")
    except OSError as e:
        raise SubprocessRunError(f"OS error occurred: {e}")
    except Exception as e:
        raise SubprocessRunError(f"Unexpected error: {e}")


def execute_es2panda(es2panda_path: str, arktsconfig: str, env_path: str, timeout: str) -> str:
    """Execute es2panda compilation process."""
    cmd = build_es2panda_command(es2panda_path, arktsconfig)
    env = set_environment(env_path)
    return run_subprocess(cmd, timeout, env)


def execute_es2panda_stdlib(es2panda_path: str, arktsconfig: str, env_path: str, timeout: str, dst_path: str) -> str:
    """Execute es2panda compilation process."""
    cmd = build_es2panda_command_stdlib(es2panda_path, arktsconfig, dst_path)
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
    parser.add_argument("--dst-file", type=str, required=True,
                        help="Path for final dst file")
    parser.add_argument("--env-path", type=str, required=True,
                        help="Value for LD_LIBRARY_PATH environment variable")
    parser.add_argument("--timeout-limit", type=str, default="12000",
                        help="Process timeout in seconds (default: 12000)")
    parser.add_argument("--cache-path", type=str, default=None,
                        help="Path to cache directory (optional)")
    parser.add_argument("--bootpath-json-file", type=str, required=True,
                        help="bootpath.json file records the path in device for boot abc files.")
    parser.add_argument("--is-boot-abc", type=bool, default=False,
                        help="Flag indicating if the file is a boot abc")
    parser.add_argument("--device-dst-file", type=str, default=None,
                        help="Path for device dst file. If 'is-boot-abc' is True, this parameter is required.")
    parser.add_argument("--is-stdlib", type=bool, default=False,
                        help="Flag indicating if the compile target is etsstdlib")

    return parser.parse_args()


def validate_arktsconfig(config: Dict) -> None:
    """Validate the structure and content of arktsconfig."""
    if "compilerOptions" not in config:
        raise ConfigValidationError("Missing 'compilerOptions' in config")
    if "outDir" not in config["compilerOptions"]:
        raise ConfigValidationError("Missing 'outDir' in compilerOptions")


def modify_arktsconfig_with_cache(arktsconfig_path: str, cache_path: str) -> None:
    """
    Modify arktsconfig.json to use cache_path as outDir.
    Backup the original file, modify it, and restore it after use.
    """
    backup_path = arktsconfig_path + ".bak"
    os.rename(arktsconfig_path, backup_path)

    try:
        with open(backup_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        config["compilerOptions"]["outDir"] = cache_path
        with open(arktsconfig_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except json.JSONDecodeError as e:
        raise ConfigValidationError(f"Invalid JSON format: {e}")
    except Exception as e:
        os.rename(backup_path, arktsconfig_path)
        raise e


def restore_arktsconfig(arktsconfig_path: str) -> None:
    """Restore the original arktsconfig.json from backup."""
    backup_path = arktsconfig_path + ".bak"
    if os.path.exists(backup_path):
        os.rename(backup_path, arktsconfig_path)


def add_to_bootpath(device_dst_file: str, bootpath_json_file: str) -> None:
    data = {}
    if os.path.exists(bootpath_json_file):
        with open(bootpath_json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

    current_value = data.get("bootpath", "")
    abc_set = set(current_value.split(":")) if current_value else set()
    abc_set.add(device_dst_file)
    new_value = ":".join(abc_set)
    data["bootpath"] = new_value

    os.makedirs(os.path.dirname(bootpath_json_file), exist_ok=True)

    with open(bootpath_json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def main() -> None:
    """Main compilation workflow."""
    start_time = time.time()
    args = parse_arguments()

    try:
        if args.cache_path is not None:
            modify_arktsconfig_with_cache(args.arktsconfig, args.cache_path)

        with open(args.arktsconfig, "r", encoding="utf-8") as f:
            config = json.load(f)
            validate_arktsconfig(config)

        out_dir = config["compilerOptions"]["outDir"]
        if not os.path.isabs(out_dir):
            base_dir = os.path.dirname(os.path.abspath(args.arktsconfig))
            out_dir = os.path.join(base_dir, out_dir)

        if args.is_stdlib:
            execute_es2panda_stdlib(args.es2panda, args.arktsconfig, args.env_path, args.timeout_limit, args.dst_file)
        else:
            execute_es2panda(args.es2panda, args.arktsconfig, args.env_path, args.timeout_limit)
            execute_ark_link(args.ark_link, args.dst_file, out_dir, args.env_path, args.timeout_limit)

        if args.is_boot_abc:
            add_to_bootpath(args.device_dst_file, args.bootpath_json_file)

        print(f"Compilation succeeded in {time.time() - start_time:.2f} seconds")
        sys.exit(EXIT_CODE["SUCCESS"])

    except SubprocessTimeoutError as e:
        print(f"[FATAL] Process timeout: {e}", file=sys.stderr)
        sys.exit(EXIT_CODE["TIMEOUT"])
    except SubprocessRunError as e:
        print(f"[ERROR] Execution failed: {e}", file=sys.stderr)
        sys.exit(EXIT_CODE["EXECUTION_FAILURE"])
    except json.JSONDecodeError as e:
        print(f"[CONFIG] Invalid JSON in {args.arktsconfig}: {e}", file=sys.stderr)
        sys.exit(EXIT_CODE["CONFIG_ERROR"])
    except FileNotFoundError as e:
        print(f"[IO ERROR] File not found: {e}", file=sys.stderr)
        sys.exit(EXIT_CODE["FILE_NOT_FOUND"])
    except KeyError as e:
        print(f"[CONFIG] Missing required key: {e}", file=sys.stderr)
        sys.exit(EXIT_CODE["MISSING_KEY"])
    except PermissionError as e:
        print(f"[PERMISSION] Access denied: {e}", file=sys.stderr)
        sys.exit(EXIT_CODE["PERMISSION_ERROR"])
    except ConfigValidationError as e:
        print(f"[CONFIG] Invalid configuration: {e}", file=sys.stderr)
        sys.exit(EXIT_CODE["INVALID_CONFIG"])
    except Exception as e:
        print(f"[UNKNOWN] Unexpected error: {e}", file=sys.stderr)
        sys.exit(EXIT_CODE["UNKNOWN_ERROR"])
    finally:
        # Restore the original arktsconfig.json if cache_path was used
        if args.cache_path is not None:
            restore_arktsconfig(args.arktsconfig)


if __name__ == "__main__":
    main()
