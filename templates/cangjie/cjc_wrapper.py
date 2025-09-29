#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import argparse
import json
import os.path
import subprocess
import re


def find_mac_sdk_root():
    child = subprocess.Popen(["xcrun", "--sdk", "macosx", "--show-sdk-path"], stdout=subprocess.PIPE)
    code = child.wait()
    if code != 0:
        raise Exception("failed to detect mac sdk root: 'xcrun --sdk macosx --show-sdk-path'")
    output = child.stdout.read().decode("utf-8").replace("\n", "")
    return output


def build_run_cjc_command(cmd_options):
    config_file = cmd_options.config
    with open(config_file, 'r') as file:
        data = json.load(file)
        (args, cwd) = build_args(data, cmd_options)
        if cmd_options.is_mac:
            macenv = os.environ.copy()
            macenv["SDKROOT"] = find_mac_sdk_root()
            child = subprocess.Popen(args, cwd=cwd, env=macenv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            child = subprocess.Popen(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = child.communicate()
        if child.returncode != 0:
            print(stdout.decode(), stderr.decode())
            raise Exception("failed to run cjc: {}".format(" ".join(args)))


def get_all_components(cmd_options):
    source_file = "{}/build_configs/parts_info/components.json".format(cmd_options.root_out_dir)
    with open(source_file, 'r') as file:
        data = json.load(file)
        return data


def get_external_module_info(depname, part_configs, cmd_options):
    part_component = depname.split(":")
    part_name = part_component[0]
    component_name = part_component[1]
    if part_name in part_configs:
        labels = part_configs[part_name]["innerapis"]
    else:
        labels = part_configs["{}_override".format(part_name)]["innerapis"]
    target_label = ""
    for label_data in labels:
        if (component_name == label_data["name"]):
            target_label = label_data["label"]
            break
    if target_label == "":
        raise Exception("component :{}/{} not found".format(part_name, component_name))
    path_and_component = target_label.split(":")
    pathname = path_and_component[0]
    pathname = pathname.replace("//", "");
    target_outdir = "{}/obj/{}/{}_module_info.json".format(cmd_options.root_out_dir, pathname, path_and_component[1])
    return target_outdir

def get_deps_form_cangjie_deps_config_meta(cangjie_deps_config, cjc_toolchain_config):
    if not os.path.exists(cangjie_deps_config):
        return []
    args = []
    with open(cangjie_deps_config, 'r') as file:
        dep_config = json.load(file)
        args = []
        for dep in dep_config:
            if dep["type"] == "static_library":
                source_file = "{}/lib{}{}".format(dep["out_dir"], dep["output_name"], cjc_toolchain_config["static_extension"])
                args.append("--link-options={}".format(source_file))
            elif dep["type"] == "source_set":
                output_objs = dep["outputs"]
                for obj in output_objs:
                    source_file = "{}/{}".format(dep["out_dir"], obj)
                    args.append("--link-options={}".format(source_file))
    return args

def build_args(config, options):
    args = [options.cjc]
    args += config["args"]

    if "external_deps" in config:
        all_parts = get_all_components(options)
        for external_dep in config["external_deps"]:
            module_info_file = get_external_module_info(external_dep, all_parts, options)
            if not os.path.exists(module_info_file):
                continue
            with open(module_info_file, 'r') as file:
                # link c targets by full path, but cj targets are not, because full path targets must define 'SONAME',
                # otherwise target so be linked by full path, and won't work once moved.
                module_info = json.load(file)
                if module_info["type"] != "unknown":
                    source_file = "{}/{}".format(options.root_out_dir, module_info["source"])
                    args.append("--link-options={}".format(source_file))

    for module_info_file in config["native_deps"]:
        if not os.path.exists(module_info_file):
            continue
        with open(module_info_file, 'r') as file:
            # link c targets by full path, but cj targets are not, because full path targets must define 'SONAME',
            # otherwise target so be linked by full path, and won't work once moved.
            module_info = json.load(file)
            source_file = "{}/{}".format(options.root_out_dir, module_info["source"])
            args.append("--link-options={}".format(source_file))
    for cj_config_file in config["cjc_deps"]:
        with open(cj_config_file, 'r') as file:
            target_config = json.load(file)
            outtype = target_config["output_type"]
            source_file = target_config["outfile"]
            outdir = os.path.dirname(source_file)
            outfile = re.sub(r'^lib', "", os.path.basename(source_file))
            outfile = re.sub(r'\.(so|a|dll)$', "", outfile)
            args.append("--import-path={}".format(target_config["import_path"]))
            if outtype != "macro" and outtype != "test" and outtype != "exe":
                args.append("-L{}".format(outdir))
                args.append("-l{}".format(outfile))

    cangjie_deps_config = config["cangjie_deps_config"]
    cjc_toolchain_config = config["cjc_toolchain_config"]
    args.extend(get_deps_form_cangjie_deps_config_meta(config["cangjie_deps_config"], config["cjc_toolchain_config"]))

    return (args, os.path.dirname(config["outfile"]))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="json config for cj target")
    parser.add_argument("--cjc", required=True, help="cjc executable path")
    parser.add_argument("--root_out_dir", required=True, help="gn root output dir")
    parser.add_argument("--is_mac", required=False, type=bool, default=False, help="is build mac target")
    options = parser.parse_args()
    build_run_cjc_command(options)