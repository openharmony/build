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


import subprocess
import os
import sys
import inspect
import pytest

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
build_sh_path = os.path.join(CURRENT_OHOS_ROOT, 'build.sh')

template_source_path = config.get("template_source_path")
result_build_file = config.get("result_build_file")
build_res_path = CURRENT_OHOS_ROOT + result_build_file
result_obj_file = config.get("result_obj_file")
result_path = CURRENT_OHOS_ROOT + result_obj_file
rust_path = config.get("rust_path")
result_rust_file = config.get("result_rust_file")
rust_result_idl_path = CURRENT_OHOS_ROOT + result_rust_file


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
    cmd = [build_sh_path, '--product-name', 'rk3568', '--build-target', cmd_path]
    print(cmd)
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


class TestModuleBuild:

    def test_ohos_shared_library(self):
        """
        ...
        """
        res_def_name = inspect.currentframe().f_code.co_name
        cmd_path = template_source_path + res_def_name
        res_path = build_res_path + "/libtest_ohos_shared_library.z.so"
        result = exec_command_communicate(cmd_path, res_path, res_def_name)
        assert result, "build test_ohos_shared_library failed"

    '''

    def test_ohos_shared_library_output_dir(self):
        """
        定义编译产物路径,内部默认 不生效
        """
        shell_flag = False
        timeout = 600
        res_def_name = inspect.currentframe().f_code.co_name
        cmd_path = template_source_path + res_def_name
        cmd = [build_sh_path, '--product-name', 'rk3568', '--build-target', cmd_path]
        print(cmd)
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
                flag = False
                c = "[OHOS INFO] output_dir is not allowed to be defined."
                if c in out_res:
                    flag = True
                assert flag == False, "build test_ohos_shared_library_output_dir failed"
            else:
                for row in enumerate(out_res):
                    logger(row)
                assert proc.returncode == 0, "build test_ohos_shared_library_output_dir failed"
        except Exception as e:
            logger("An error occurred: {}".format(e))


    def test_ohos_shared_library_testonly(self):
        """
        调试模式，默认false，true不生效
        """
        shell_flag = False
        timeout = 600
        res_def_name = "test_ohos_shared_library_output_dir"
        cmd_path = template_source_path + res_def_name
        cmd = [build_sh_path, '--product-name', 'rk3568', '--build-target', cmd_path]
        print(cmd)
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
                # a = "[OHOS INFO] ERROR at //build/ohos/ohos_part.gni:54:3: Test-only dependency not allowed."
                # for error_res in list_res:
                #     if error_res in out_res:
                #         continue
                #     else:
                #         assert proc.returncode == 0, "build test_ohos_shared_library failed"
            if proc.returncode != 0:
                flag = False
                c = "[OHOS INFO] ERROR at //build/ohos/ohos_part.gni:54:3: Test-only dependency not allowed."
                if c in out_res:
                    flag = True
                assert flag, "build test_ohos_shared_library failed"
            else:
                for row in enumerate(out_res):
                    logger(row)
                assert proc.returncode == 0, "build test_ohos_shared_library failed"
        except Exception as e:
            logger("An error occurred: {}".format(e))
    '''

    def test_ohos_shared_library_output_name(self):
        """
        看护输出文件name
        """
        function_name = "test_ohos_shared_library_output_dir"
        cmd_path = template_source_path + function_name
        res_path = build_res_path + "lib{}.{}".format(function_name, function_name)
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, " ohos_shared_library  template output_name and output_extension invalid"

    def test_ohos_shared_library_output_extension(self):
        """
        看护输出格式
        """
        function_name = "test_ohos_shared_library_output_dir"
        cmd_path = template_source_path + function_name
        res_path = build_res_path + "lib{}.{}".format(function_name, function_name)
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, " ohos_shared_library  template output_name and output_extension invalid"

    def test_ohos_shared_library_install_enable(self):
        """
        看护开启安装
        """
        pass

    def test_ohos_shared_library_module_install_dir(self):
        """
        看护依赖安装路径
        """
        pass

    def test_ohos_shared_library_relative_install_dir(self):
        """
        看护lib路径
        """
        pass

    def test_ohos_static_library(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        common_res_def = template_source_path + function_name
        res_path = result_path + function_name + "/src/" + function_name + "/hello.o"
        result = exec_command_communicate(common_res_def, res_path, function_name)
        assert result, "build test_ohos_static_library failed"

    def test_ohos_source_set(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        common_res_def = template_source_path + function_name
        res_path = result_path + function_name + "/src/" + function_name + "/main.o"
        result = exec_command_communicate(common_res_def, res_path, function_name)
        assert result, "build test_ohos_source_set failed"

    def test_ohos_executable(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        common_res_def = template_source_path + function_name
        res_path = build_res_path + function_name
        result = exec_command_communicate(common_res_def, res_path, function_name)
        assert result, "build test_ohos_executable failed"


class TestPrecompiledBuild:

    def test_ohos_prebuilt_executable(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_common = template_source_path + function_name
        res_path = result_path + function_name + "/test_ohos_prebuilt_executable.stamp"
        result = exec_command_communicate(cmd_common, res_path, function_name)
        assert result, "build test_ohos_prebuilt_executable failed"

    def test_ohos_prebuilt_shared_library(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        common_res_def = template_source_path + function_name
        res_path = result_path + function_name + "/test_ohos_prebuilt_shared_library.stamp"
        result = exec_command_communicate(common_res_def, res_path, function_name)
        assert result, "build test_ohos_prebuilt_shared_library failed"

    def test_ohos_prebuilt_static_library(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        common_res_def = template_source_path + function_name
        res_path = result_path + function_name + "/test_ohos_prebuilt_static_library.stamp"
        result = exec_command_communicate(common_res_def, res_path, function_name)
        assert result, "build test_ohos_prebuilt_static_library failed"


class TestHapBuild:

    def test_ohos_app(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        example_name = 'MyApplication3'
        common_res_def = template_source_path + example_name
        res_path = result_path + function_name + "/" + function_name + "/{}.hap".format(function_name)
        result = exec_command_communicate(common_res_def, res_path, function_name)
        assert result, "build test_ohos_app failed"


class OtherPrebuilt:

    def test_ohos_sa_profile(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = template_source_path + function_name
        profile_result_path = result_path + function_name
        result = exec_command_communicate(cmd_path, profile_result_path, function_name)
        assert result, "build test_ohos_sa_profile failed"

    def test_ohos_prebuilt_etc(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = template_source_path + function_name
        rebuilt_result_path = result_path + function_name
        result = exec_command_communicate(cmd_path, rebuilt_result_path, function_name)
        assert result, "build test_ohos_prebuilt_etc failed"


class TestRustBuild:

    def test_bin_cargo_crate(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = rust_path + function_name
        res_path = os.path.join(build_res_path, function_name)
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_bin_cargo_crate failed"

    def test_bin_crate(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = rust_path + function_name
        res_path = os.path.join(build_res_path, function_name)
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_bin_crate failed"

    def test_extern_c(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = rust_path + "/test_bindgen_test/test_for_extern_c:test_extern_c"
        res_path = os.path.join(build_res_path, function_name)
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_extern_c failed"

    def test_for_h(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = rust_path + "/test_bindgen_test/test_for_h:bindgen_test_for_h"
        res_path = os.path.join(build_res_path, 'bindgen_test_for_h')
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build bindgen_test_for_h failed"

    def test_for_hello_world(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = rust_path + "/test_bindgen_test/test_for_hello_world:bindgen_test"
        res_path = os.path.join(build_res_path, 'bindgen_test')
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_for_hello_world failed"

    def test_for_hpp(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = rust_path + "/test_bindgen_test/test_for_hpp:bindgen_test_hpp"
        res_path = os.path.join(build_res_path, 'bindgen_test_hpp')
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build bindgen_test_hpp failed"

    def test_cdylib_crate(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = rust_path + function_name
        res_path = os.path.join(build_res_path, function_name)
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_cdylib_crate failed"

    def test_cxx_exe(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = rust_path + "test_cxx" + ":" + function_name
        res_path = os.path.join(build_res_path, function_name)
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_cxx_exe failed"

    def test_cxx_rust(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = rust_path + function_name
        res_path = os.path.join(build_res_path, function_name)
        result = exec_command_communicate(cmd_path, res_path, function_name)

        assert result, "build test_cxx_rust failed"

    def test_dylib_crate(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = rust_path + function_name
        res_path = os.path.join(build_res_path, function_name)
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_cxx_rust failed"

    def test_idl(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = rust_path + "/test_idl"
        res_path = os.path.join(rust_result_idl_path, function_name, 'test_idl.stamp')
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_idl failed"

    def test_rlib_cargo_crate(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = rust_path + function_name + ':' + 'test_rlib_crate_associated_bin'
        res_path = os.path.join(build_res_path, 'test_rlib_crate_associated_bin')
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_rlib_cargo_crate failed"

    def test_rlib_crate(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = rust_path + function_name
        res_path = os.path.join(build_res_path, function_name)
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_rlib_crate failed"

    def test_rust_st(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = rust_path + function_name
        res_path = os.path.join(build_res_path, 'libtest_rust_st_add.dylib.so')
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_rust_st failed"

    def test_rust_ut(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = rust_path + function_name
        res_path = os.path.join(build_res_path, 'libtest_rust_ut_add.dylib.so')
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_rust_ut failed"

    def test_static_link(self):
        """
        ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = rust_path + function_name
        res_path = os.path.join(build_res_path, function_name)
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_static_link failed"

    def test_staticlib_crate(self):
        """
         ...
        """
        function_name = inspect.currentframe().f_code.co_name
        cmd_path = rust_path + function_name
        res_path = os.path.join(build_res_path, function_name)
        result = exec_command_communicate(cmd_path, res_path, function_name)
        assert result, "build test_staticlib_crate failed"
