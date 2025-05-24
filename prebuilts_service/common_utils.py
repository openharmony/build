#!/usr/bin/env python3
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

import os
import shutil
import subprocess
import pathlib
import time
import json
import importlib


def get_code_dir():
    current_dir = os.path.dirname(__file__)
    while True:
        check_path = os.path.join(current_dir, "build", "ohos.gni")
        if os.path.exists(check_path):
            return current_dir
        else:
            new_dir = os.path.dirname(current_dir)
            if new_dir == current_dir:
                raise Exception(f"file {__file__} not in ohos source directory")
            else:
                current_dir = new_dir


def import_rich_module():
    module = importlib.import_module("rich.progress")
    progress = module.Progress(
        module.TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
        module.BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        module.DownloadColumn(),
        "•",
        module.TransferSpeedColumn(),
        "•",
        module.TimeRemainingColumn(),
    )
    return progress


def load_config(config_file: str):
    with open(config_file, "r", encoding="utf-8") as r:
        config = json.load(r)
        return config


def copy_file(src: str, dest: str):
    if not os.path.exists(dest):
        os.makedirs(dest)
    shutil.copy(src, dest)


def remove_dest_path(dest_path: str):
    if os.path.exists(dest_path) or os.path.islink(dest_path):
        if os.path.islink(dest_path):
            os.unlink(dest_path)
        elif os.path.isdir(dest_path):
            shutil.rmtree(dest_path)
        else:
            os.remove(dest_path)


def copy_folder(src: str, dest: str):
    remove_dest_path(dest)
    shutil.copytree(src, dest)


def symlink_src2dest(src_dir: str, dest_dir: str):
    remove_dest_path(dest_dir)
    os.makedirs(os.path.dirname(dest_dir), exist_ok=True)
    os.symlink(src_dir, dest_dir)
    print("symlink {} ---> {}".format(src_dir, dest_dir))


def run_cmd_live(cmd: list):
    cmd_str = " ".join(cmd)
    print(f"run command: {cmd_str}\n")
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())

        return_code = process.poll()
        if return_code != 0:
            print(f"命令执行失败，返回码: {return_code}")
        return return_code, ""
    except Exception as e:
        print(f"执行命令时出错: {e}")
        return 1, ""


def run_cmd(cmd: list) -> tuple:
    res = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    sout, serr = res.communicate()
    return sout.rstrip().decode("utf-8"), serr, res.returncode


def is_system_component() -> bool:
    root_dir = get_code_dir()
    return any(
        pathlib.Path(root_dir, *components).exists()
        for components in [
            ("interface", "sdk-js"),
            ("foundation", "arkui"),
            ("arkcompiler",)
        ]
    )


def install_hpm_in_other_platform(name: str, operate: dict):
    download_dir = operate.get("download_dir")
    package_path = operate.get("package_path")
    package_lock_path = operate.get("package_lock_path")
    hash_value = (
        subprocess.run(
            ["sha256sum", package_lock_path], capture_output=True, text=True
        )
        .stdout.strip()
        .split(" ")[0]
    )
    hash_dir = os.path.join(download_dir, hash_value)
    copy_file(package_path, hash_dir)
    copy_file(package_lock_path, hash_dir)

    if not os.path.exists(os.path.join(hash_dir, "npm-install.js")):
        npm_install_script = os.path.join(
            os.path.dirname(package_path), "npm-install.js"
        )
        if os.path.exists(npm_install_script):
            shutil.copyfile(
                npm_install_script, os.path.join(hash_dir, "npm-install.js")
            )

    result = subprocess.run(
        ["npm", "install", "--prefix", hash_dir], capture_output=True, text=True
    )
    if result.returncode == 0:
        print("npm install completed in the {} directory.".format(hash_dir))
    else:
        print("npm dependency installation failed:", result.stderr)

    symlink_src = os.path.join(hash_dir, "node_modules")
    symlink_dest = operate.get("symlink")

    if name == "legacy_bin":
        for link in operate.get("symlink", []):
            symlink_src2dest(symlink_src, link)
        return

    if name in ["parse5"]:
        copy_folder(symlink_src, symlink_dest)
        return

    copy_folder(symlink_src, symlink_dest)

    for copy_entry in operate.get("copy", []):
        copy_folder(
            copy_entry["src"], copy_entry["dest"]
        )

    for copy_ext_entry in operate.get("copy_ext", []):
        copy_folder(
            copy_ext_entry["src"], copy_ext_entry["dest"]
        )


def install_hpm(npm_tool_path: str, hpm_install_dir: str):
    content = """\
package-lock=true
registry=http://repo.huaweicloud.com/repository/npm
strict-ssl=false
lockfile=false
"""
    with os.fdopen(
            os.open(
                os.path.join(os.path.expanduser("~"), ".npmrc"),
                os.O_WRONLY | os.O_CREAT,
                mode=0o640,
            ),
            "w",
    ) as f:
        os.truncate(f.fileno(), 0)
        f.write(content)
    if not os.path.exists(hpm_install_dir):
        os.makedirs(hpm_install_dir)
    with os.fdopen(
            os.open(
                os.path.join(hpm_install_dir, "package.json"),
                os.O_WRONLY | os.O_CREAT,
                mode=0o640,
            ),
            "w",
    ) as f:
        os.truncate(f.fileno(), 0)
        f.write("{}\n")
    node_bin_path = os.path.dirname(npm_tool_path)
    os.environ["PATH"] = f"{node_bin_path}:{os.environ['PATH']}"
    subprocess.run(
        [
            npm_tool_path,
            "install",
            "@ohos/hpm-cli",
            "--registry",
            "https://repo.huaweicloud.com/repository/npm/",
            "--prefix",
            hpm_install_dir,
        ]
    )


def npm_config(npm_tool_path: str, global_args: object) -> tuple:
    node_path = os.path.dirname(npm_tool_path)
    os.environ["PATH"] = "{}:{}".format(node_path, os.environ.get("PATH"))
    if global_args.skip_ssl:
        skip_ssl_cmd = "{} config set strict-ssl false;".format(npm_tool_path).split()
        _, err, retcode = run_cmd(skip_ssl_cmd)
        if retcode != 0:
            return False, err.decode()
    npm_clean_cmd = "{} cache clean -f".format(npm_tool_path).split()
    npm_package_lock_cmd = "{} config set package-lock true".format(npm_tool_path).split()
    _, err, retcode = run_cmd(npm_clean_cmd)
    if retcode != 0:
        return False, err.decode()
    _, err, retcode = run_cmd(npm_package_lock_cmd)
    if retcode != 0:
        return False, err.decode()
    return True, None


def npm_install(operate: dict, global_args: object, success_installed_npm_config: list) -> tuple:
    install_list = operate.get("npm_install_path")
    npm_tool_path = os.path.join(global_args.code_dir, "prebuilts/build-tools/common/nodejs/current/bin/npm")

    preset_is_ok, err = npm_config(npm_tool_path, global_args)
    if not preset_is_ok:
        return preset_is_ok, err

    print("start npm install, please wait.")
    for install_path in install_list:
        if install_path in success_installed_npm_config:
            continue
        full_code_path = install_path
        basename = os.path.basename(full_code_path)
        node_modules_path = os.path.join(full_code_path, "node_modules")
        npm_cache_dir = os.path.join("~/.npm/_cacache", basename)

        if os.path.exists(node_modules_path):
            print("remove node_modules %s" % node_modules_path)
            run_cmd(("rm -rf {}".format(node_modules_path)).split())

        if os.path.exists(full_code_path):
            cmd = ["timeout", "-s", "9", "90s", npm_tool_path, "install", "--registry", global_args.npm_registry,
                   "--cache", npm_cache_dir]
            if global_args.host_platform == "darwin":
                cmd = [npm_tool_path, "install", "--registry", global_args.npm_registry, "--cache", npm_cache_dir]
            if global_args.unsafe_perm:
                cmd.append("--unsafe-perm")
            proc = subprocess.Popen(
                cmd, cwd=full_code_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            # wait proc Popen with 0.1 second
            time.sleep(0.1)
            _, err = proc.communicate()
            if proc.returncode:
                print("in dir:{}, executing:{}".format(full_code_path, " ".join(cmd)))
                return False, err.decode()
            else:
                success_installed_npm_config.append(install_path)
        else:
            raise Exception(
                "{} not exist, it shouldn't happen, pls check...".format(full_code_path)
            )
        print(f"{node_modules_path} install over!")
    return True, None