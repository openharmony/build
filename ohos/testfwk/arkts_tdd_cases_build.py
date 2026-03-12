#!/usr/bin/env python3
# coding=utf-8
#
# Copyright (c) 2025 Huawei Device Co., Ltd.
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
import logging
import os
import shutil
import sys
import json
import subprocess
import argparse
from typing import Dict, List
import re
from pathlib import Path


# ==========================
# Constants
# ==========================
ES2PANDAPATH = "arkcompiler/runtime_core/static_core/out/bin/es2panda"
ARKLINKPATH = "arkcompiler/runtime_core/static_core/out/bin/ark_link"
CONFIGPATH = "arkcompiler/runtime_core/static_core/out/bin/arktsconfig.json"
TOOLSPATH = "test/testfwk/developer_test/libs/arkts1.2"
HYPIUMPATH = "test/testfwk/arkxtest/jsunit/src_static/"


# ==========================
# Utility Functions
# ==========================
def get_path_code_directory(after_dir):
    """
    Concatenate absolute path based on current script location.
    """
    current_path = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_path)
    root_path = current_path.split("/build/ohos/testfwk")[0]
    full_path = os.path.join(root_path, after_dir)
    logging.debug(f"Resolved path: {after_dir} -> {full_path}")
    return full_path


# ==========================
# Build Tools
# ==========================
def build_tools(compile_filelist, output_dir, arktsconfig):
    """
    Compile ETS files into ABC format.
    """
    logging.info(f"Starting compilation, output directory: {output_dir}")
    abs_es2panda_path = get_path_code_directory(ES2PANDAPATH)

    # Create output directory
    output_dir = os.path.join(output_dir, "out")
    os.makedirs(output_dir, exist_ok=True)
    logging.info(f"Output directory created or exists: {output_dir}")

    # Compile each file
    for ets_file in compile_filelist:
        try:
            file_name = os.path.basename(ets_file)
            base_name = os.path.splitext(file_name)[0]
            output_filepath = os.path.join(output_dir, f"{base_name}.abc")

            if arktsconfig == CONFIGPATH:
                command = [abs_es2panda_path, ets_file, f"--output={output_filepath}"]
            else:
                arktsconfig_path = get_path_code_directory(arktsconfig)
                command = [abs_es2panda_path, ets_file, f"--output={output_filepath}",
                           f"--arktsconfig={arktsconfig_path}"]
            logging.info(f"Executing compile command: {' '.join(command)}")

            result = subprocess.run(
                command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logging.info(f"Successfully compiled '{ets_file}' → '{output_filepath}'")
            if result.stdout.strip():
                logging.debug(f"Compile output: {result.stdout.strip()}")

        except subprocess.CalledProcessError as e:
            logging.error(f"Compilation failed for '{ets_file}'. Error:\n{e.stderr.strip()}")
            raise
        except Exception as e:
            logging.critical(f"Unexpected error during compilation of '{ets_file}': {str(e)}")
            raise


# ==========================
# Main Build Flow
# ==========================
def build_ets_files(target_path, test_files, output_dir, arktsconfig):
    """
    Compile test case ETS files.
    """
    # Parse source file list
    test_files_list = [f.strip() for f in test_files.split(',') if f.strip()]
    test_files = [os.path.join(target_path, file) for file in test_files_list]

    logging.info(f"Files to be compiled: {test_files}")
    build_tools(test_files, output_dir, arktsconfig)


def collect_abc_files(output_dir, target_path, hypium_output_dir, sources):
    """
    Collect all .abc files for linking.
    """
    abs_out_path = os.path.join(output_dir, "out")
    abc_files = []

    # 1. Collect .abc files from 'out' directory
    if os.path.exists(abs_out_path):
        out_files = [
            os.path.join(abs_out_path, f)
            for f in os.listdir(abs_out_path)
            if f.endswith('.abc') and (not f.endswith('_source.abc'))
        ]
        abc_files.extend(out_files)
        logging.info(f"Collected {len(out_files)} .abc files from 'out' directory")
    else:
        logging.warning(f"Output directory does not exist: {abs_out_path}")

    # 2. Add hypium_tools.abc
    hypium_abc = os.path.join(hypium_output_dir, "hypium_tools.abc")
    if os.path.exists(hypium_abc):
        abc_files.append(hypium_abc)
        logging.info(f"Added hypium tool file: {hypium_abc}")
    else:
        logging.error(f"Missing hypium tool file: {hypium_abc}. Please compile hypium first.")
        raise FileNotFoundError(f"Missing hypium tool file: {hypium_abc}")

    # 3. Load additional .abc files from src.json
    abc_files.extend(load_abc_from_src_json(target_path, sources))

    logging.info(f"Total {len(abc_files)} .abc files collected for linking")
    return abc_files


def load_abc_from_src_json(target_path, sources):
    """
    Load extra .abc files from src.json.
    """
    abc_files = []
    sources_list = [f.strip() for f in sources.split(',') if f.strip()]
    if not sources_list:
        logging.warning("src.json filename is empty, skipping loading.")
        return abc_files

    source_file = sources_list[0]
    src_json_path = os.path.join(target_path, source_file)

    if not os.path.exists(src_json_path):
        logging.info(f"Config file not found: {src_json_path}, skipping src.json loading.")
        return abc_files

    try:
        with os.fdopen(os.open(src_json_path, os.O_RDONLY), 'r', encoding='utf-8') as f:
            src_data = json.load(f)
        logging.info(f"Successfully loaded src.json: {src_json_path}")
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON format in {src_json_path}: {e}")
        return abc_files
    except Exception as e:
        logging.error(f"Failed to read src.json {src_json_path}: {e}")
        return abc_files

    for path in src_data.get("src_path", []):
        if path.endswith('.abc'):
            abs_path = get_path_code_directory(path)
            if os.path.isfile(abs_path):
                abc_files.append(abs_path)
                logging.debug(f"Added .abc file: {abs_path}")
        else:
            logging.warning(f"Skipped invalid or non-.abc path: {path}")

    return abc_files


def link_abc_files(output_dir, hap_name, target_path, hypium_output_dir, sources):
    """
    Link all .abc files into final test.abc.
    """
    hypium_abc = os.path.join(hypium_output_dir, "hypium_tools.abc")
    if not os.path.exists(hypium_abc):
        logging.error(f"Missing hypium tool file: {hypium_abc}. Please compile hypium first.")
        sys.exit(1)

    abc_files = collect_abc_files(output_dir, target_path, hypium_output_dir, sources)

    if not abc_files:
        logging.error("No .abc files collected, cannot proceed with linking.")
        sys.exit(1)

    out_path = os.path.join(output_dir, f"{hap_name}.abc")

    execute_abc_link(out_path, abc_files)


def execute_abc_link(out_path, abc_files):
    """ execute abc_link Link all .abc files into final test.abc.  """
    abs_arklink_path = get_path_code_directory(ARKLINKPATH)
    command = [abs_arklink_path, f"--output={out_path}", "--", *abc_files]

    logging.info(f"Starting linking process, output: {out_path}")
    logging.debug(f"Linking command: {' '.join(command)}")

    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logging.info(f"Linking succeeded! Output: {out_path}")
        if result.stdout.strip():
            logging.debug(f"Linking output: {result.stdout.strip()}")

    except subprocess.CalledProcessError as e:
        logging.error(f"Linking failed. Details:\n{e.stderr.strip()}")
        sys.exit(1)


# ==========================
#  Build file_map dictionary
# ==========================
def build_file_map() -> Dict[str, List[str]]:
    file_map = {}

    # 1. Scan tools_path (arkts1.2 tdd)
    tools_path = get_path_code_directory(TOOLSPATH)
    if not os.path.exists(tools_path) or not os.path.isdir(tools_path):
        logging.warning(f"Tools path does not exist: {tools_path}")
        return file_map

    temp_list = [
        "@ohos.app.ability.abilityDelegatorRegistry",
        "AbilityDelegator",
        "AbilityDelegatorArgs",
        "ShellCmdResult",
        "AbilityMonitor",
        "AbilityStageMonitor"
    ]

    for f in os.listdir(tools_path):
        if not f.endswith('.ets'):
            continue
        module_name = os.path.splitext(f)[0]
        if module_name not in temp_list:
            continue
        file_path = os.path.abspath(os.path.join(tools_path, f))
        file_map[module_name] = [file_path]

    # 2. Scan hypium_path (excluding testAbility/testrunner)
    abs_hypium_path = get_path_code_directory(HYPIUMPATH)
    if not os.path.exists(abs_hypium_path) or not os.path.isdir(abs_hypium_path):
        logging.warning(f"Hypium path does not exist: {abs_hypium_path}")
        return file_map

    for root, dirs, files in os.walk(abs_hypium_path):
        if "testAbility" in dirs:
            dirs.remove("testAbility")
        if "testrunner" in dirs:
            dirs.remove("testrunner")

        for f in files:
            if not f.endswith(".ets"):
                continue
            module_name = os.path.splitext(f)[0]
            file_path = os.path.abspath(os.path.join(root, f))
            file_map.setdefault(module_name, []).append(file_path)

    return file_map


def scan_and_add_test_files(args: argparse.Namespace, config: dict) -> None:
    """Scan the target HAP directory for .ets files that are not yet in compileFiles,
       and extend config['compileFiles'] with them."""
    if not args.base_url.endswith("arkui-preprocessed"):
        return

    target_dir = os.path.join(args.base_url, args.hap_name)
    target_path = Path(target_dir)

    # Check if target directory exists and is a directory
    if not target_path.exists() or not target_path.is_dir():
        return
    existing_files = set(config.get("compileFiles", []))
    tested_ets_files = set()
    for file_path in target_path.rglob("*.ets"):
        if file_path.name.startswith("."):
            continue
        abs_path = str(file_path.resolve())
        if abs_path not in existing_files:
            tested_ets_files.add(abs_path)
    if tested_ets_files:
        config["compileFiles"].extend(tested_ets_files)


# ==========================
# Get testrunner filepath
# ==========================
def write_test_runner_path_file(args: argparse.Namespace, config: dict) -> None:
    target_dir = os.path.join(args.output_dir, "out")
    file_path = os.path.join(target_dir, f"{args.hap_name}_testRunnerPath.txt")
    if os.path.exists(file_path):
        os.remove(file_path)
    # Find the matching test runner file
    matching_files = [
        file for file in config["compileFiles"]
        if file.endswith("OpenHarmonyTestRunner.ets")
    ]

    if len(matching_files) == 1:
        result = matching_files[0]
        path_without_file = os.path.dirname(result)

        # Remove the base_url prefix
        relative_path = ''
        if args.base_url in path_without_file:
            relative_path = path_without_file.split(args.base_url, 1)[1]

        # Construct the target directory and file path
        if relative_path:
            relative_path = relative_path.lstrip('/')
            os.makedirs(target_dir, exist_ok=True)
            # write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(relative_path)


# ==========================
# Build driver configuration
# ==========================
def build_driver_config(args: argparse.Namespace) -> None:
    paths = {}
    if args.paths_keys and args.paths_values:
        if len(args.paths_keys) != len(args.paths_values):
            raise ValueError(
                "paths_keys and paths_values must have the same length"
            )
        for key, value in zip(args.paths_keys, args.paths_values):
            paths[key] = [os.path.abspath(value)]

    # Build the file_map dictionary by scanning .ets files from: TOOLS path and HYPIUM path
    file_map = build_file_map()
    paths.update(file_map)

    config = {
        "plugins": {},
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
        "externalApiPaths": args.scan_path
    }

    plugins = {}
    config["pathsKeys"] = []
    config["pathsValues"] = []
    config["compileFiles"] = []
    if args.memo_plugin is not None:
        plugins["memo_plugin"] = args.memo_plugin
    if plugins:
        config["plugins"] = plugins

    if args.paths_keys:
        config["pathsKeys"] = args.paths_keys
    if args.paths_values:
        config["pathsValues"] = args.paths_values
    if args.files:
        if not os.path.exists(args.files):
            print(f"[IO ERROR] File not found: {args.files}", file=sys.stderr)
            sys.exit()
        fd = os.open(args.files, os.O_RDONLY)
        with os.fdopen(fd, 'r') as f:
            config["compileFiles"] = [line.strip() for line in f.readlines()]
    config["pathsKeys"].extend(list(file_map.keys()))
    all_paths = [path for sublist in file_map.values() for path in sublist]
    config["pathsValues"].extend(all_paths)
    # Scan and add the target HAP directory for .ets files that are not yet in compileFiles
    scan_and_add_test_files(args, config)
    # Get testrunner filepath
    write_test_runner_path_file(args, config)

    os.makedirs(os.path.dirname(args.arktsconfig), exist_ok=True)
    fd = os.open(args.arktsconfig, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o777)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def run_subprocess(cmd: List[str], timeout: str, env: Dict[str, str]) -> str:
    """Execute a subprocess with timeout and environment settings."""
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
            raise subprocess.TimeoutExpired(
                f"Command '{' '.join(cmd)}' timed out after {timeout_sec} seconds")

        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                f"Command '{' '.join(cmd)}' failed with return code {process.returncode}\n"
                f"Standard Error:\n{stderr}\n"
                f"Standard Output:\n{stdout}"
            )

        return stdout

    except ValueError as e:
        raise ValueError(f"Invalid timeout value: {e}")
    except OSError as e:
        raise OSError(f"OS error occurred: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error: {e}")


def execute_driver(
        entry_path: str, build_config_path: str, env_path: str, node_path: str, timeout: str
) -> str:
    """Execute es2panda compilation process."""
    # Construct driver command arguments
    cmd = ["node", entry_path, build_config_path]
    # Create environment variables with updated LD_LIBRARY_PATH.
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = env_path
    if node_path is not None:
        env["PATH"] = f"{node_path}:{env['PATH']}"
    return run_subprocess(cmd, timeout, env)


def replace_import_paths(file_path):
    """replace arkui-preprocessed test file import path."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = r'from\s*([\'"])((?:\.\./)+)arkui-preprocessed(/?[^\'"]*)([\'"])'

    new_content = re.sub(
        pattern,
        lambda m: f'from {m.group(1)}../{m.group(3).lstrip("/")}{m.group(4)}',
        content
    )

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)


# ==========================
# link hypium abc files
# ==========================
def ui_enable_link_hypium_abc(dst_file, hypium_output_dir) -> None:
    if not dst_file:
        raise ValueError("dst_file is empty or None")

    if not hypium_output_dir:
        raise ValueError("hypium_output_dir is not set")

    hypium_abc = os.path.join(hypium_output_dir, "hypium_tools.abc")

    if not os.path.isfile(hypium_abc):
        logging.error(f"Missing hypium tool file: {hypium_abc}. Please compile hypium first.")
        raise FileNotFoundError(f"Missing hypium tool file: {hypium_abc}")

    abc_files = [dst_file, hypium_abc]
    execute_abc_link(dst_file, abc_files)


def copy_ets_files_to_preprocessed_dir(args, target_dir):
    """
    Copy ETS test files into the arkui-preprocessed directory
    structure, and replace import paths in each file.
    """
    # Parse test files list
    test_files_list = [f.strip() for f in args.test_files.split(',') if f.strip()]
    test_files = [os.path.join(args.target_path, file) for file in test_files_list]

    for ets_file in test_files:
        if not os.path.exists(ets_file):
            logging.info(f"Skip non-existent file: {ets_file}")
            continue

        # Define target path
        relative_filename = os.path.basename(ets_file)
        target_file = os.path.join(target_dir, relative_filename)

        # Ensure target directory exists
        os.makedirs(target_dir, exist_ok=True)

        # Copy file
        try:
            shutil.copy2(ets_file, target_file)
            logging.info(f"Copied: {ets_file} → {target_file}")
        except Exception as e:
            logging.error(f"Failed to copy {ets_file} to {target_file}: {e}")
            continue

        # Replace import paths in the copied file
        try:
            replace_import_paths(target_file)
            logging.info(f"Import paths replaced in: {target_file}")
        except Exception as e:
            logging.error(f"Failed to replace import paths in {target_file}: {e}")


# ==========================
# Main Entry Point
# ==========================
def main():
    parser = argparse.ArgumentParser(description="Compile ETS test cases and link into .abc")
    parser.add_argument("--target_path", required=True, help="Root path of test cases")
    parser.add_argument("--test_files", required=True, help="Name of src.json file")
    parser.add_argument("--output_dir", required=True, help="build output directory")
    parser.add_argument("--hap_name", required=True, help="HAP name")
    parser.add_argument("--hypium_output_dir", required=True, help="Output directory for hypium build")
    parser.add_argument("--sources", required=True, help="List of ETS source files (comma-separated)")
    parser.add_argument("--subsystem_name", required=True, help="subsystem name")
    parser.add_argument("--part_name", required=True, help="part name")
    parser.add_argument("--arktsconfig", required=True, help="arktsconfig file")
    parser.add_argument("--scan_path", nargs="+", required=False, help="List of directories to scan for target files")
    parser.add_argument("--ui_enable", default=True, required=False,
                        help="Flag indicating if the compile supports ui syntax")
    parser.add_argument("--base_url", required=False, help="Base URL for the project")
    parser.add_argument("--build_sdk_path", default=None, required=False,
                        help="Path for sdk. Required if 'ui-enable' is True")
    parser.add_argument("--memo_plugin", default=None, required=False,
                        help="Path for memo plugin. Required if 'ui-enable' is True")
    parser.add_argument("--entry_path", default=None, required=False,
                        help="Path for driver entry. Required if 'ui-enable' is True")
    parser.add_argument("--env_path", type=str, required=False, help="Value for LD_LIBRARY_PATH environment variable")
    parser.add_argument("--node_path", default=None, required=False, help="Path for node")
    parser.add_argument("--files", required=False, help="File containing a list of specific files to compile")
    parser.add_argument("--package", required=False, help="Package name for the project")
    parser.add_argument("--paths_keys", nargs="+", required=False, help="List of keys for custom paths")
    parser.add_argument("--paths_values", nargs="+", required=False,
                        help="List of values for custom paths. Each value corresponds to a key in --paths-keys")
    parser.add_argument("--cache_path", type=str, default=None, help="Path to cache directory")
    parser.add_argument("--dst_file", type=str, required=True, help="Path for final dst file")
    parser.add_argument("--timeout_limit", type=str, default="12000",
                        help="Process timeout in seconds (default: 12000)")

    args = parser.parse_args()
    target_dir = None

    # Start build pipeline
    try:
        if os.path.exists(args.cache_path):
            shutil.rmtree(args.cache_path)
        os.makedirs(args.cache_path, exist_ok=True)

        # Starting build pipeline
        if args.ui_enable == "True":
            if args.base_url.endswith("arkui-preprocessed"):
                target_dir = os.path.join(args.base_url, args.hap_name)
                copy_ets_files_to_preprocessed_dir(args, target_dir)
            build_driver_config(args)
            execute_driver(args.entry_path, args.arktsconfig, args.env_path, args.node_path, args.timeout_limit)
            ui_enable_link_hypium_abc(args.dst_file, args.hypium_output_dir)
        else:
            build_ets_files(args.target_path, args.test_files, args.output_dir, args.arktsconfig)
            link_abc_files(args.output_dir, args.hap_name, args.target_path, args.hypium_output_dir, args.sources)
        # Build completed successfully!

        # arklink source file
        source_abc_dir = os.path.join(args.output_dir, "out", f"{args.hap_name}_source.abc")
        abc_files = load_abc_from_src_json(args.target_path, args.sources)
        execute_abc_link(source_abc_dir, abc_files)
    except Exception as e:
        logging.critical(f"Build process failed unexpectedly: {str(e)}")
        sys.exit(1)
    finally:
        if target_dir and os.path.exists(target_dir) and os.path.isdir(target_dir):
            shutil.rmtree(target_dir)


if __name__ == '__main__':
    sys.exit(main())