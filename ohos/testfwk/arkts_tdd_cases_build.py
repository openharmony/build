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
import sys
import json
import subprocess
import argparse
import shutil


# ==========================
# Constants
# ==========================
ES2PANDAPATH = "arkcompiler/runtime_core/static_core/out/bin/es2panda"
ARKLINKPATH = "arkcompiler/runtime_core/static_core/out/bin/ark_link"
CONFIGPATH = "arkcompiler/runtime_core/static_core/out/bin/arktsconfig.json"


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
def build_ets_files(target_path, sources, output_dir, arktsconfig):
    """
    Compile test case ETS files.
    """
    # Parse source file list
    test_files_list = [f.strip() for f in sources.split(',') if f.strip()]
    test_files = [os.path.join(target_path, file) for file in test_files_list]

    logging.info(f"Files to be compiled: {test_files}")
    build_tools(test_files, output_dir, arktsconfig)


def collect_abc_files(output_dir, target_path, hypium_output_dir, test_files):
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
            if f.endswith('.abc')
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
    abc_files.extend(load_abc_from_src_json(target_path, test_files))

    logging.info(f"Total {len(abc_files)} .abc files collected for linking")
    return abc_files


def load_abc_from_src_json(target_path, test_files):
    """
    Load extra .abc files from src.json.
    """
    abc_files = []
    test_files_list = [f.strip() for f in test_files.split(',') if f.strip()]
    if not test_files_list:
        logging.warning("src.json filename is empty, skipping loading.")
        return abc_files

    test_file = test_files_list[0]
    src_json_path = os.path.join(target_path, test_file)

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
        if os.path.isfile(path) and path.endswith('.abc'):
            abc_files.append(path)
            logging.debug(f"Added .abc file: {path}")
        else:
            logging.warning(f"Skipped invalid or non-.abc path: {path}")

    return abc_files


def link_abc_files(output_dir, hap_name, target_path, hypium_output_dir, test_files):
    """
    Link all .abc files into final test.abc.
    """
    hypium_abc = os.path.join(hypium_output_dir, "hypium_tools.abc")
    if not os.path.exists(hypium_abc):
        logging.error(f"Missing hypium tool file: {hypium_abc}. Please compile hypium first.")
        sys.exit(1)

    abs_arklink_path = get_path_code_directory(ARKLINKPATH)
    abc_files = collect_abc_files(output_dir, target_path, hypium_output_dir, test_files)

    if not abc_files:
        logging.error("No .abc files collected, cannot proceed with linking.")
        sys.exit(1)

    out_path = os.path.join(output_dir, f"{hap_name}.abc")

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

    args = parser.parse_args()

    # Start build pipeline
    try:
        logging.info("Starting build pipeline")
        build_ets_files(args.target_path, args.sources, args.output_dir, args.arktsconfig)
        link_abc_files(args.output_dir, args.hap_name, args.target_path, args.hypium_output_dir, args.test_files)
        logging.info("Build completed successfully!")
    except Exception as e:
        logging.critical(f"Build process failed unexpectedly: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    sys.exit(main())