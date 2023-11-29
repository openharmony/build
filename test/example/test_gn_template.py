#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
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
import shutil
import subprocess
import os
import sys
import inspect
import pytest
import json

from mylogger import get_logger, parse_json

sys.path.append(os.path.join(os.getcwd(), "mylogger.py"))
Log = get_logger("build_gn")
print = Log.info
logger = Log.error

config = parse_json().get("gn_template")
if not config:
    logger("config file: build_example.json error")
    sys.exit(0)

CURRENT_OHOS_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BUILD_SH_PATH = os.path.join(CURRENT_OHOS_ROOT, 'build.sh')

TEMPLATE_SOURCE_PATH = config.get("template_source_path")
RESULT_BUILT_FILE = config.get("result_build_file")
BUILD_RES_PATH = CURRENT_OHOS_ROOT + RESULT_BUILT_FILE
RESULT_OBJ_FILE = config.get("result_obj_file")
RESULT_PATH = CURRENT_OHOS_ROOT + RESULT_OBJ_FILE
RUST_PATH = config.get("rust_path")
RESULT_RUST_FILE = config.get("result_rust_file")
RUST_RESULT_IDL_PATH = CURRENT_OHOS_ROOT + RESULT_RUST_FILE
EXCLUDE_LIST = config.get("exclude")
TEST_BUILD = config.get("test_build")
CONFIG_PATH = CURRENT_OHOS_ROOT + TEST_BUILD


def remove_dir():
    """
    ...
    """
    out_dir = os.path.join(CURRENT_OHOS_ROOT, "out")
    try:
        if os.path.exists(out_dir):
            for tmp_dir in os.listdir(out_dir):
                if tmp_dir not in EXCLUDE_LIST:
                    if os.path.isdir(os.path.join(out_dir, tmp_dir)):
                        shutil.rmtree(os.path.join(out_dir, tmp_dir))
                    else:
                        os.remove(os.path.join(out_dir, tmp_dir))
    except Exception as e:
        logger("out file is not exist")


remove_dir()


@pytest.fixture()
def init_build_env():
    def find_top_dir():
        cur_dir = os.getcwd()
        while cur_dir != "/":
            build_scripts = os.path.join(
                cur_dir, 'build/scripts/build_package_list.json')
            if os.path.exists(build_scripts):
                return cur_dir
            cur_dir = os.path.dirname(cur_dir)

    os.chdir(find_top_dir())
    subprocess.run(['repo', 'forall', '-c', 'git reset --hard'],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(['repo', 'forall', '-c', 'git clean -dfx'],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def exec_command_communicate(cmd_path, res_path, res_def_name, shell_flag=False, timeout=600):
    """
    Execute the cmd command to return the terminal output value
    """

    write_bundle_json(res_def_name, cmd_path)
    cmd = [BUILD_SH_PATH, '--product-name', 'rk3568', '--build-target', cmd_path]
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            universal_newlines=True,
            shell=shell_flag
        )
        out, error = proc.communicate(timeout=timeout)
        out_res = out.splitlines() + error.splitlines()
        print(f"*******************returncode:{proc.returncode}*********************")
        if proc.returncode == 0:
            for row in enumerate(out_res):
                print(row)
            if os.path.exists(res_path):
                print('*****************test succeed************************')
                return True
            else:
                print(f"{res_def_name} is not exist")
                return False
        else:
            for row in enumerate(out_res):
                logger(row)
            return False
    except Exception as e:
        logger("An error occurred: {}".format(e))


def exec_command_out_put(cmd_path, res_def_name, c, shell_flag=False, timeout=600):
    """
    Execute the cmd command to return the terminal output value
    """

    write_bundle_json(res_def_name, cmd_path)
    cmd = [BUILD_SH_PATH, '--product-name', 'rk3568', '--build-target', cmd_path]
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            universal_newlines=True,
            shell=shell_flag
        )
        out, error = proc.communicate(timeout=timeout)
        out_res = out.splitlines() + error.splitlines()
        print(f"*******************returncode:{proc.returncode}*********************")
        if proc.returncode != 0:
            for row in enumerate(out_res):
                print(row)
            # print(out_res)
            if c in out_res:
                print('*****************test succeed************************')
                return True
            else:
                print(f"{res_def_name} faile")
                return False
        else:
            for row in enumerate(out_res):
                logger(row)
            return False
    except Exception as e:
        logger("An error occurred: {}".format(e))


def exec_command_isntall_dir(cmd_path, res_def_name, shell_flag=False, timeout=600):
    """
    Execute the cmd command to return the terminal output value
    """

    write_bundle_json(res_def_name, cmd_path)
    cmd = [BUILD_SH_PATH, '--product-name', 'rk3568', '--build-target', cmd_path]
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            universal_newlines=True,
            shell=shell_flag
        )
        out, error = proc.communicate(timeout=timeout)
        out_res = out.splitlines() + error.splitlines()
        print(f"*******************returncode:{proc.returncode}*********************")
        if proc.returncode == 0:
            for row in enumerate(out_res):
                print(row)
            config_path = RESULT_PATH + res_def_name + "/{}_module_info.json".format(res_def_name)
            with open(config_path, "r", encoding="utf-8") as json_file:
                data = json.load(json_file)
                res = str((data.get("dest"))[0])
                moudel_install_dir = res_def_name
            if moudel_install_dir in res:
                print('*****************test succeed************************')
                return True
            else:
                print(f"{res_def_name} is not exist")
                return False
        else:
            for row in enumerate(out_res):
                logger(row)
            return False
    except Exception as e:
        logger("An error occurred: {}".format(e))


def write_bundle_json(res_def_name, cmd_path):
    """
    write bundle.json
    """

    with open(CONFIG_PATH, "r", encoding="utf-8") as json_file:
        data = json.load(json_file)
        res = (data.get("component").get("build").get("sub_component"))
        res.append("//{}:{}".format(cmd_path, res_def_name))
        data["component"]["build"]["sub_component"] = res
    config_res = CURRENT_OHOS_ROOT + "/build/common/bundle.json"
    with open(config_res, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)


class TestModuleBuild:

    def test_ohos_shared_library_output_dir(self):
        """
        ...
        """
        res_def_name = inspect.currentframe().f_code.co_name
        c = "[OHOS INFO] output_dir is not allowed to be defined."
        cmd_path = TEMPLATE_SOURCE_PATH + res_def_name
        result = exec_command_out_put(cmd_path, res_def_name, c)
        assert result, "build test_ohos_shared_library_output_dir failed"

    def test_ohos_shared_library_testonly(self):
        """
        ...
        """
        c = "[OHOS INFO] ERROR at //build/ohos/ohos_part.gni:54:3: Test-only dependency not allowed."
        res_def_name = inspect.currentframe().f_code.co_name
        cmd_path = TEMPLATE_SOURCE_PATH + res_def_name
        result = exec_command_out_put(cmd_path, res_def_name, c)
        assert result, "build test_ohos_shared_library_testonly failed"

    def test_ohos_shared_library(self):
        """
        ...
        """
        res_def_name = inspect.currentframe().f_code.co_name
        cmd_path = TEMPLATE_SOURCE_PATH + res_def_name
        res_path = BUILD_RES_PATH + "/libtest_ohos_shared_library.z.so"
        result = exec_command_communicate(cmd_path, res_path, res_def_name)
        assert result, "build test_ohos_shared_library failed"

    def test_ohos_shared_library_output_name(self):
        """
        ...
        """
        res_def_name = inspect.currentframe().f_code.co_name
        cmd_path = TEMPLATE_SOURCE_PATH + res_def_name
        res_path = BUILD_RES_PATH + "lib{}.{}".format(res_def_name, res_def_name)
        result = exec_command_communicate(cmd_path, res_path, res_def_name)
        assert result, " ohos_shared_library  template output_name and output_extension invalid"

    def test_ohos_shared_library_output_extension(self):
        """
        ...
        """
        res_def_name = "test_ohos_shared_library_output_name"
        cmd_path = TEMPLATE_SOURCE_PATH + res_def_name
        res_path = BUILD_RES_PATH + "lib{}.{}".format(res_def_name, res_def_name)
        result = exec_command_communicate(cmd_path, res_path, res_def_name)
        assert result, " ohos_shared_library  template output_name and output_extension invalid"

    def test_ohos_shared_library_module_install_dir(self):
        """
        ...
        """
        res_def_name = inspect.currentframe().f_code.co_name
        cmd_path = TEMPLATE_SOURCE_PATH + res_def_name
        result = exec_command_isntall_dir(cmd_path, res_def_name)
        assert result, " test_ohos_shared_library_module_install_dir fail"

    def test_ohos_shared_library_relative_install_dir(self):
        res_def_name = inspect.currentframe().f_code.co_name
        cmd_path = TEMPLATE_SOURCE_PATH + res_def_name
        result = exec_command_isntall_dir(cmd_path, res_def_name)
        assert result, " test_ohos_shared_library_relative_install_dir fail"

    def test_ohos_static_library(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = TEMPLATE_SOURCE_PATH + function_name
        res_path = RESULT_PATH + function_name + "/src/" + function_name + "/hello.o"
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_ohos_static_library failed"

    def test_ohos_source_set(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = TEMPLATE_SOURCE_PATH + function_name
        res_path = RESULT_PATH + function_name + "/src/" + function_name + "/main.o"
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_ohos_source_set failed"

    def test_ohos_executable(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        common_res_def = TEMPLATE_SOURCE_PATH + function_name
        res_path = BUILD_RES_PATH + function_name
        result = exec_command_communicate(common_res_def, res_path, function_name)
        assert result, "build test_ohos_executable failed"


class TestPrecompiledBuild:

    def test_ohos_prebuilt_executable(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_common = TEMPLATE_SOURCE_PATH + function_name
        res_path = RESULT_PATH + function_name + "/test_ohos_prebuilt_executable.stamp"
        result = exec_command_communicate(cmd_common, res_path, function_name)
        assert result, "build test_ohos_prebuilt_executable failed"

    def test_ohos_prebuilt_shared_library(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        common_res_def = TEMPLATE_SOURCE_PATH + function_name
        res_path = RESULT_PATH + function_name + "/test_ohos_prebuilt_shared_library.stamp"
        result = exec_command_communicate(common_res_def, res_path, function_name)
        assert result, "build test_ohos_prebuilt_shared_library failed"

    def test_ohos_prebuilt_static_library(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        common_res_def = TEMPLATE_SOURCE_PATH + function_name
        res_path = RESULT_PATH + function_name + "/test_ohos_prebuilt_static_library.stamp"
        result = exec_command_communicate(common_res_def, res_path, function_name)
        assert result, "build test_ohos_prebuilt_static_library failed"


class TestHapBuild:

    def test_ohos_app(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        example_name = 'MyApplication3'
        common_res_def = TEMPLATE_SOURCE_PATH + example_name
        res_path = RESULT_PATH + function_name + "/" + function_name + "/{}.hap".format(function_name)
        result = exec_command_communicate(common_res_def, res_path, function_name)
        assert result, "build test_ohos_app failed"


class OtherPrebuilt:

    def test_ohos_sa_profile(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = TEMPLATE_SOURCE_PATH + function_name
        profile_result_path = RESULT_PATH + function_name
        result = exec_command_communicate(cmd_path, profile_result_path, function_name)
        assert result, "build test_ohos_sa_profile failed"

    def test_ohos_prebuilt_etc(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = TEMPLATE_SOURCE_PATH + function_name
        rebuilt_result_path = RESULT_PATH + function_name
        result = exec_command_communicate(cmd_path, rebuilt_result_path, function_name)
        assert result, "build test_ohos_prebuilt_etc failed"


class TestRustBuild:

    def test_bin_cargo_crate(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = RUST_PATH + function_name
        res_path = os.path.join(BUILD_RES_PATH, function_name)
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_bin_cargo_crate failed"

    def test_bin_crate(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = RUST_PATH + function_name
        res_path = os.path.join(BUILD_RES_PATH, function_name)
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_bin_crate failed"

    def test_extern_c(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = RUST_PATH + "/test_bindgen_test/test_for_extern_c:test_extern_c"
        res_path = os.path.join(BUILD_RES_PATH, function_name)
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_extern_c failed"

    def test_for_h(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = RUST_PATH + "/test_bindgen_test/test_for_h:bindgen_test_for_h"
        res_path = os.path.join(BUILD_RES_PATH, 'bindgen_test_for_h')
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build bindgen_test_for_h failed"

    def test_for_hello_world(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = RUST_PATH + "/test_bindgen_test/test_for_hello_world:bindgen_test"
        res_path = os.path.join(BUILD_RES_PATH, 'bindgen_test')
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_for_hello_world failed"

    def test_for_hpp(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = RUST_PATH + "/test_bindgen_test/test_for_hpp:bindgen_test_hpp"
        res_path = os.path.join(BUILD_RES_PATH, 'bindgen_test_hpp')
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build bindgen_test_hpp failed"

    def test_cdylib_crate(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = RUST_PATH + function_name
        res_path = os.path.join(BUILD_RES_PATH, function_name)
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_cdylib_crate failed"

    def test_cxx_exe(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = RUST_PATH + "test_cxx" + ":" + function_name
        res_path = os.path.join(BUILD_RES_PATH, function_name)
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_cxx_exe failed"

    def test_cxx_rust(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = RUST_PATH + function_name
        res_path = os.path.join(BUILD_RES_PATH, function_name)
        result = exec_command_communicate(cmd_path, res_path, function_name)

        assert result, "build test_cxx_rust failed"

    def test_dylib_crate(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = RUST_PATH + function_name
        res_path = os.path.join(BUILD_RES_PATH, function_name)
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_cxx_rust failed"

    def test_idl(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = RUST_PATH + "/test_idl"
        res_path = os.path.join(RUST_RESULT_IDL_PATH, function_name, 'test_idl.stamp')
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_idl failed"

    def test_rlib_cargo_crate(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = RUST_PATH + function_name + ':' + 'test_rlib_crate_associated_bin'
        res_path = os.path.join(BUILD_RES_PATH, 'test_rlib_crate_associated_bin')
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_rlib_cargo_crate failed"

    def test_rlib_crate(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = RUST_PATH + function_name
        res_path = os.path.join(BUILD_RES_PATH, function_name)
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_rlib_crate failed"

    def test_rust_st(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = RUST_PATH + function_name
        res_path = os.path.join(BUILD_RES_PATH, 'libtest_rust_st_add.dylib.so')
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_rust_st failed"

    def test_rust_ut(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = RUST_PATH + function_name
        res_path = os.path.join(BUILD_RES_PATH, 'libtest_rust_ut_add.dylib.so')
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_rust_ut failed"

    def test_static_link(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = RUST_PATH + function_name
        res_path = os.path.join(BUILD_RES_PATH, function_name)
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_static_link failed"

    def test_staticlib_crate(self):
        """
         ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = RUST_PATH + function_name
        res_path = os.path.join(BUILD_RES_PATH, function_name)
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_staticlib_crate failed"
