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
from typing import Dict, List, Optional


EXIT_CODE = {
    "SUCCESS": 0,
    "TIMEOUT": 1,
    "EXECUTION_FAILURE": 2,
    "CONFIG_ERROR": 3,
    "FILE_NOT_FOUND": 4,
    "MISSING_KEY": 5,
    "UNKNOWN_ERROR": 6,
    "PERMISSION_ERROR": 7,
    "INVALID_CONFIG": 8,
    "PATHS_LENGTH_MISMATCH": 9,
}


class SubprocessTimeoutError(Exception):
    """Exception raised when subprocess execution times out."""


class SubprocessRunError(Exception):
    """Exception raised when subprocess fails to execute."""


class ConfigValidationError(Exception):
    """Exception raised when configuration validation fails."""


class PathsLengthMismatchError(Exception):
    """Exception raised when paths_keys and paths_values have different lengths."""


def set_environment(env_path: str, node_path: Optional[str] = None) -> Dict[str, str]:
    """Create environment variables with updated LD_LIBRARY_PATH."""
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = env_path
    if node_path is not None:
        env["PATH"] = f"{node_path}:{env['PATH']}"
    return env


def build_es2panda_command(es2panda_path: str, arktsconfig: str) -> List[str]:
    """Construct es2panda command arguments."""
    return [es2panda_path, "--arktsconfig", arktsconfig, "--ets-module"]


def build_driver_command(entry_path: str, build_config_path: str) -> List[str]:
    """Construct driver command arguments."""
    return ["node", entry_path, build_config_path]


def execute_driver(
    entry_path: str, build_config_path: str, env_path: str, node_path: str, timeout: str
) -> str:
    """Execute es2panda compilation process."""
    cmd = build_driver_command(entry_path, build_config_path)
    env = set_environment(env_path, node_path)
    return run_subprocess(cmd, timeout, env)


def build_es2panda_command_stdlib(
    es2panda_path: str, arktsconfig: str, dst_path: str
) -> List[str]:
    """Construct es2panda command arguments."""
    return [
        es2panda_path,
        "--arktsconfig",
        arktsconfig,
        "--ets-module",
        "--gen-stdlib=true",
        "--output=" + dst_path,
        "--extension=ets",
        "--opt-level=2",
    ]


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
            cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
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


def execute_es2panda(
    es2panda_path: str, arktsconfig: str, env_path: str, timeout: str
) -> str:
    """Execute es2panda compilation process."""
    cmd = build_es2panda_command(es2panda_path, arktsconfig)
    env = set_environment(env_path)
    return run_subprocess(cmd, timeout, env)


def execute_es2panda_stdlib(
    es2panda_path: str, arktsconfig: str, env_path: str, timeout: str, dst_path: str
) -> str:
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


def build_ark_link_command(
    ark_link_path: str, output_path: str, abc_files: List[str]
) -> List[str]:
    """Construct ark_link command arguments."""
    return [ark_link_path, f"--output={output_path}", "--", *abc_files]


def execute_ark_link(
    ark_link_path: str, output_path: str, output_dir: str, env_path: str, timeout: str
) -> str:
    """Execute ark_link process to bundle ABC files."""
    abc_files = collect_abc_files(output_dir)
    cmd = build_ark_link_command(ark_link_path, output_path, abc_files)
    env = set_environment(env_path)
    return run_subprocess(cmd, timeout, env)


def create_base_parser() -> argparse.ArgumentParser:
    """Create and configure the base argument parser."""
    parser = argparse.ArgumentParser()
    add_required_arguments(parser)
    add_optional_arguments(parser)
    add_ui_arguments(parser)
    return parser


def add_required_arguments(parser: argparse.ArgumentParser) -> None:
    """Add required arguments to the parser."""
    parser.add_argument("--dst-file", type=str, required=True,
                      help="Path for final dst file")
    parser.add_argument("--env-path", type=str, required=True,
                      help="Value for LD_LIBRARY_PATH environment variable")
    parser.add_argument("--bootpath-json-file", type=str, required=True,
                      help="bootpath.json file records the path in device for boot abc files")


def add_optional_arguments(parser: argparse.ArgumentParser) -> None:
    """Add optional arguments to the parser."""
    parser.add_argument("--arktsconfig", type=str, required=False,
                    help="Path to arktsconfig.json configuration file")
    parser.add_argument("--es2panda", type=str, required=False,
                      help="Path to es2panda executable")
    parser.add_argument("--ark-link", type=str, required=False,
                      help="Path to ark_link executable")
    parser.add_argument("--timeout-limit", type=str, default="12000",
                      help="Process timeout in seconds (default: 12000)")
    parser.add_argument("--cache-path", type=str, default=None,
                      help="Path to cache directory")
    parser.add_argument("--is-boot-abc", type=bool, default=False,
                      help="Flag indicating if the file is a boot abc")
    parser.add_argument("--device-dst-file", type=str, default=None,
                      help="Path for device dst file. Required if 'is-boot-abc' is True")
    parser.add_argument("--target-name", type=str,
                      help="target name")
    parser.add_argument("--is-stdlib", type=bool, default=False,
                      help="Flag indicating if the compile target is etsstdlib")
    parser.add_argument("--root-dir", required=False,
                      help="Root directory for the project")
    parser.add_argument("--base-url", required=False,
                      help="Base URL for the project")
    parser.add_argument("--package", required=False,
                      help="Package name for the project")
    parser.add_argument("--std-path", required=False,
                      help="Path to the standard library")
    parser.add_argument("--escompat-path", required=False,
                      help="Path to the escompat library")
    parser.add_argument("--scan-path", nargs="+", required=False,
                      help="List of directories to scan for target files")
    parser.add_argument("--include", nargs="+", required=False,
                      help="List of file patterns to include in the compilation")
    parser.add_argument("--exclude", nargs="+", required=False,
                      help="List of file patterns to exclude from the compilation")
    parser.add_argument("--files", nargs="+", required=False,
                      help="List of specific files to compile")
    parser.add_argument("--paths-keys", nargs="+", required=False,
                      help="List of keys for custom paths")
    parser.add_argument("--paths-values", nargs="+", required=False,
                      help="List of values for custom paths. Each value corresponds to a key in --paths-keys")


def add_ui_arguments(parser: argparse.ArgumentParser) -> None:
    """Add UI-related arguments to the parser."""
    parser.add_argument("--ui-enable", default=False, required=False,
                      help="Flag indicating if the compile supports ui syntax")
    parser.add_argument("--build-sdk-path", default=None, required=False,
                      help="Path for sdk. Required if 'ui-enable' is True")
    parser.add_argument("--panda-stdlib-path", default=None, required=False,
                      help="Path for stdlib")
    parser.add_argument("--ui-plugin", default=None, required=False,
                      help="Path for ui plugin. Required if 'ui-enable' is True")
    parser.add_argument("--memo-plugin", default=None, required=False,
                      help="Path for memo plugin. Required if 'ui-enable' is True")
    parser.add_argument("--entry-path", default=None, required=False,
                      help="Path for driver entry. Required if 'ui-enable' is True")
    parser.add_argument("--driver-config-path", default=None, required=False,
                    help="Path for driver config. Required if 'ui-enable' is True")
    parser.add_argument("--node-path", default=None, required=False,
                    help="Path for node")


def parse_arguments() -> argparse.Namespace:
    """Configure and parse command line arguments."""
    parser = create_base_parser()
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
    shutil.copy(arktsconfig_path, backup_path)

    try:
        config = {}
        if os.path.exists(arktsconfig_path):
            with open(arktsconfig_path, "r") as f:
                content = f.read()
                config = json.loads(content)
            if "compilerOptions" in config:
                config["compilerOptions"]["outDir"] = cache_path

        if os.path.exists(arktsconfig_path):
            fd = os.open(arktsconfig_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o777)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
    except json.JSONDecodeError as e:
        print(f"{arktsconfig_path} Invalid JSON format (cache): {e}", file=sys.stderr)
        sys.exit()
    except Exception as e:
        restore_arktsconfig(arktsconfig_path)
        raise e


def restore_arktsconfig(arktsconfig_path: str) -> None:
    """Restore the original arktsconfig.json from backup."""
    backup_path = arktsconfig_path + ".bak"
    if os.path.exists(backup_path):
        shutil.move(backup_path, arktsconfig_path)


def add_to_bootpath(device_dst_file: str, bootpath_json_file: str, target_name: str) -> None:
    print(f"Received target name {target_name}")
    try:
        directory = os.path.dirname(bootpath_json_file)
        new_json_file = os.path.join(directory, f"{target_name}_bootpath.json")

        data = {}
        if os.path.exists(new_json_file):
            with open(new_json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

        current_value = data.get("bootpath", "")
        abc_set = set(current_value.split(":")) if current_value else set()
        abc_set.add(device_dst_file)
        new_value = ":".join(abc_set)
        data["bootpath"] = new_value

        os.makedirs(os.path.dirname(new_json_file), exist_ok=True)
        fd = os.open(new_json_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o777)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"{target_name}_bootpath.json has been created")
    except json.JSONDecodeError as e:
        print(f"{new_json_file} Invalid JSON format (bootpath): {e}", file=sys.stderr)
        sys.exit()


def is_target_file(file_name: str) -> bool:
    """
    Check if the given file name is a target file.
    """
    target_extensions = [".d.ets", ".ets"]
    return any(file_name.endswith(ext) for ext in target_extensions)


def get_key_from_file_name(file_name: str) -> str:
    """
    Extract the key from the given file name.
    """
    if ".d." in file_name:
        file_name = file_name.replace(".d.", ".")
    return os.path.splitext(file_name)[0]


def scan_directory_for_paths(directory: str) -> Dict[str, List[str]]:
    """
    Scan the specified directory to find all target files and organize their paths by key.
    If the first-level directory is 'arkui' and the second-level directory is 'runtime-api',
    the key is the file name. Otherwise, the key is the relative path with '/' replaced by '.'.
    """
    paths = {}
    for root, _, files in os.walk(directory):
        for file in files:
            if not is_target_file(file):
                continue
            file_path = os.path.abspath(os.path.join(root, file))
            file_name = get_key_from_file_name(file)
            file_abs_path = os.path.abspath(os.path.join(root, file_name))
            file_rel_path = os.path.relpath(file_abs_path, start=directory)
            # Split the relative path into components
            path_components = file_rel_path.split(os.sep)
            first_level_dir = path_components[0] if len(path_components) > 0 else ""
            second_level_dir = path_components[1] if len(path_components) > 1 else ""
            # Determine the key based on directory structure
            if first_level_dir == "arkui" and second_level_dir == "runtime-api":
                key = file_name
            else:
                key = file_rel_path.replace(os.sep, ".")
            if key in paths:
                paths[key].append(file_path)
            else:
                paths[key] = [file_path]
    return paths


def build_config(args: argparse.Namespace) -> None:
    """
    Build the configuration dictionary based on command-line arguments.
    """
    paths = {}
    for scan_path in args.scan_path:
        scanned_paths = scan_directory_for_paths(scan_path)
        for key, value in scanned_paths.items():
            if key in paths:
                paths[key].extend(value)
            else:
                paths[key] = value
    paths["std"] = [args.std_path]
    paths["escompat"] = [args.escompat_path]

    if args.paths_keys and args.paths_values:
        if len(args.paths_keys) != len(args.paths_values):
            raise PathsLengthMismatchError(
                "paths_keys and paths_values must have the same length"
            )
        for key, value in zip(args.paths_keys, args.paths_values):
            paths[key] = [os.path.abspath(value)]

    config = {
        "compilerOptions": {
            "rootDir": args.root_dir,
            "baseUrl": args.base_url,
            "paths": paths,
            "outDir": args.cache_path,
            "package": args.package if args.package else "",
            "useEmptyPackage": True
        }
    }

    if args.include:
        config["include"] = args.include
    if args.exclude:
        config["exclude"] = args.exclude
    if args.files:
        config["files"] = args.files

    os.makedirs(os.path.dirname(args.arktsconfig), exist_ok=True)
    fd = os.open(args.arktsconfig, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o777)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def build_driver_config(args: argparse.Namespace) -> None:
    """
    Build the driver configuration dictionary based on command-line arguments.
    """
    paths = {}
    if args.paths_keys and args.paths_values:
        if len(args.paths_keys) != len(args.paths_values):
            raise PathsLengthMismatchError(
                "paths_keys and paths_values must have the same length"
            )
        for key, value in zip(args.paths_keys, args.paths_values):
            paths[key] = [os.path.abspath(value)]

    config = {
        "plugins": {
            "ui_plugin": args.ui_plugin,
            "memo_plugin": args.memo_plugin,
        },
        "compileFiles": args.files,
        "packageName": args.package if args.package else "",
        "buildType": "build",
        "buildMode": "Release",
        "moduleRootPath": args.base_url,
        "sourceRoots": ["./"],
        "paths": paths,
        "loaderOutPath": args.dst_file,
        "cachePath": args.cache_path,
        "buildSdkPath": args.build_sdk_path,
        "dependentModuleList": [],
        "frameworkMode": True,
        "useEmptyPackage": True,
    }

    if args.panda_stdlib_path:
        config["pandaStdlibPath"] = args.panda_stdlib_path
    if args.paths_keys:
        config["pathsKeys"] = args.paths_keys
    if args.paths_values:
        config["pathsValues"] = args.paths_values

    os.makedirs(os.path.dirname(args.arktsconfig), exist_ok=True)
    fd = os.open(args.arktsconfig, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o777)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def handle_configuration(args: argparse.Namespace) -> None:
    """
    Handle the configuration setup based on command-line arguments.
    """
    if args.ui_enable == "True":
        build_driver_config(args)
    elif args.base_url:
        build_config(args)
    else:
        modify_arktsconfig_with_cache(args.arktsconfig, args.cache_path)


def main() -> None:
    """Main compilation workflow."""
    start_time = time.time()
    args = parse_arguments()

    try:
        handle_configuration(args)

        if args.ui_enable == "True":
            execute_driver(args.entry_path, args.arktsconfig, args.env_path, args.node_path, args.timeout_limit)
        elif args.is_stdlib:
            execute_es2panda_stdlib(args.es2panda, args.arktsconfig, args.env_path, args.timeout_limit, args.dst_file)
        else:
            execute_es2panda(args.es2panda, args.arktsconfig, args.env_path, args.timeout_limit)
            execute_ark_link(args.ark_link, args.dst_file, args.cache_path, args.env_path, args.timeout_limit)

        if args.is_boot_abc:
            add_to_bootpath(args.device_dst_file, args.bootpath_json_file, args.target_name)

        print(f"Compilation succeeded in {time.time() - start_time:.2f} seconds")
        sys.exit(EXIT_CODE["SUCCESS"])
    except SubprocessTimeoutError as e:
        print(f"[FATAL] Process timeout: {e}", file=sys.stderr)
        sys.exit(EXIT_CODE["TIMEOUT"])
    except SubprocessRunError as e:
        print(f"[ERROR] Execution failed: {e}", file=sys.stderr)
        sys.exit(EXIT_CODE["EXECUTION_FAILURE"])
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
    except PathsLengthMismatchError as e:
        print(f"[CONFIG] PathsLengthMismatchError: {e}", file=sys.stderr)
        sys.exit(EXIT_CODE["PATHS_LENGTH_MISMATCH"])
    except Exception as e:
        print(f"[UNKNOWN] Unexpected error: {e}", file=sys.stderr)
        sys.exit(EXIT_CODE["UNKNOWN_ERROR"])
    finally:
        if not args.base_url:
            restore_arktsconfig(args.arktsconfig)


if __name__ == "__main__":
    main()
