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


import os
import re
import shutil
import sys
import subprocess
import time
import copy
import queue
import select
import pty
import pytest

from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "mylogger.py"))
from mylogger import get_logger, parse_json

Log = get_logger("build_option")
current_file_path = os.path.abspath(__file__)
script_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
log_info = Log.info
log_error = Log.error

config = parse_json()
if not config:
    log_error("config file: build_example.json not exist")
    sys.exit(0)

out_dir = os.path.join(script_path, "out")
exclude = config.get("build_option").get("exclude")
try:
    if os.path.exists(out_dir):
        for tmp_dir in os.listdir(out_dir):
            if tmp_dir in exclude:
                continue
            if os.path.isdir(os.path.join(out_dir, tmp_dir)):
                shutil.rmtree(os.path.join(out_dir, tmp_dir))
            else:
                os.remove(os.path.join(out_dir, tmp_dir))
except Exception as err:
    log_error(err)


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


class TestBuildOption:
    FLAGS = {"gn": {"pattern": r"Excuting gn command", "flag": False},
             "done": {"pattern": r"Done\. Made \d+ targets from \d+ files in \d+ms", "flag": False},
             "ninja": {"pattern": r"Excuting ninja command", "flag": False},
             "success": {"pattern": r"=====build  successful=====", "flag": False}
             }

    try:
        LOG_PATH = script_path + config.get("build_option").get("log_path")
        CMD = script_path + config.get("build_option").get("common_cmd")
        NINJIA_CMD = script_path + config.get("build_option").get("ninjia_cmd")
        TIMEOUT = int(config.get("build_option").get("exec_timeout"))
        TIME_OVER = int(config.get("build_option").get("file_time_intever"))
        COMMAND_TYPE = config.get("build_option").get("cmd_type")
        PTYFLAG = True if config.get("build_option").get("ptyflag").lower() == "true" else False
        select_timeout = float(config.get("build_option").get("select_timeout"))
        log_info("TIMEOUT:{}".format(TIMEOUT))
        log_info("COMMAND_TYPE:{}".format(COMMAND_TYPE))
        log_info("TIME_OVER:{}".format(TIME_OVER))
        log_info("PTYFLAG:{}".format(PTYFLAG))
        log_info("select_timeout:{}".format(select_timeout))
    except Exception as err:
        log_error("build_example.json has error")
        log_error(err)
        raise err

    @staticmethod
    def exec_command_communicate(cmd, timeout=60):
        try:
            log_info("communicate_exec cmd is :{}".format(" ".join(cmd)))
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding="utf-8",
                universal_newlines=True,
                errors='ignore',
                cwd=script_path
            )
            out, err_ = proc.communicate(timeout=timeout)
            out_res = out.splitlines() + err_.splitlines()
            return out_res, proc.returncode
        except Exception as errs:
            log_error("An error occurred: {}".format(errs))
            raise Exception("exec cmd time out,communicate")

    @staticmethod
    def resolve_res(cmd_res, flag_res):
        for line_count, line in enumerate(cmd_res):
            for flag_name, value in flag_res.items():
                re_match = re.search(value["pattern"], line)
                if re_match:
                    log_info("【match success {}】:{}\n".format(line_count, line))  # 输出命令终端的显示
                    if len(re_match.groups()) > 0:
                        if isinstance(flag_res[flag_name]["flag"], bool):
                            flag_res[flag_name]["flag"] = [re_match.group(1)]
                        else:
                            data = flag_res[flag_name]["flag"]
                            data.append(re_match.group(1))
                            flag_res[flag_name]["flag"] = data
                    else:
                        flag_res[flag_name]["flag"] = True
        return flag_res

    @staticmethod
    def check_flags(flags, expect_dict=None, returncode=0):
        new_dict = copy.deepcopy(flags)
        if returncode != 0:
            log_error("returncode != 0")
            return 1
        if expect_dict:
            error_count = 0
            for k in expect_dict.keys():
                flags.pop(k)
                if k in new_dict and new_dict[k]["flag"] != expect_dict[k]:
                    error_count += 1
            if error_count != 0:
                log_error("【actual_result】:{}\n".format(new_dict))
                return 1
        check_li = [item for item in flags.values() if not item["flag"]]
        log_info("【expect_result】:{}\n".format(expect_dict))
        log_info("【actual_result】:{}\n".format(new_dict))
        if len(check_li) > 0:
            return 1
        return 0

    @staticmethod
    def is_exist(path):
        if os.path.exists(path):
            return True
        return False

    @staticmethod
    def same_element(list1, list2):
        for el in list1:
            if el not in list2:
                return False
        return True

    @staticmethod
    def print_error_line(cmd_res, is_success=False):
        if is_success:
            for ind, line in enumerate(cmd_res):
                log_info("【{}】:{}".format(ind, line))
        else:
            for ind, line in enumerate(cmd_res):
                log_error("【{}】:{}".format(ind, line))

    @staticmethod
    def get_build_only_gn_flags(para_value):
        flags = copy.deepcopy(TestBuildOption.FLAGS)
        expect_dict = {}

        if para_value.lower() == "true":
            expect_dict["ninja"] = False
        else:
            expect_dict["ninja"] = True

        return flags, expect_dict

    @staticmethod
    def get_ccache_flags(para_value):
        flags = copy.deepcopy(TestBuildOption.FLAGS)
        expect_dict = {}
        flags["ccache"] = {"pattern": r"Excuting gn command.*ohos_build_enable_ccache=true", "flag": False}

        if para_value.lower() == "true":
            expect_dict["ccache"] = True
        else:
            expect_dict["ccache"] = False

        return flags, expect_dict

    @staticmethod
    def get_target_cpu_flags(para_value):
        flags = copy.deepcopy(TestBuildOption.FLAGS)
        expect_dict = {"loader": True}

        flags["loader"] = {"pattern": r"loader args.*'target_cpu={}".format(para_value), "flag": False}

        return flags, expect_dict

    @staticmethod
    def get_rename_last_log_flags(para_value):
        flags = copy.deepcopy(TestBuildOption.FLAGS)
        expect_dict = {}
        return flags, expect_dict

    @staticmethod
    def get_enable_pycache_flags(para_value):
        flags = copy.deepcopy(TestBuildOption.FLAGS)
        expect_dict = {}
        if para_value.lower() == "true":
            expect_dict["pycache"] = True
        else:
            expect_dict["pycache"] = False
        flags["pycache"] = {"pattern": r"Starting pycache daemon at", "flag": False}
        flags["os_level"] = {"pattern": r"loader args.*os_level=([a-zA-Z]+)\'", "flag": False}
        flags["root_dir"] = {"pattern": r"""loader args.*source_root_dir="([a-zA-Z\d/\\_]+)""""", "flag": False}
        flags["gn_dir"] = {"pattern": r"""loader args.*gn_root_out_dir="([a-zA-Z\d/\\_]+)""""", "flag": False}
        flags["start_end_time"] = {"pattern": r"(\d+-\d+-\d+ \d+:\d+:\d+)", "flag": False}
        flags["cost_time"] = {"pattern": r"Cost time:.*(\d+:\d+:\d+)", "flag": False}
        return flags, expect_dict

    @staticmethod
    def get_build_target_flags(para_value):
        flags = copy.deepcopy(TestBuildOption.FLAGS)
        flags["use_thin"] = {"pattern": r"Excuting gn command.*use_thin_lto=false.*", "flag": False}
        flags["ninja_build_target"] = {"pattern": r"Excuting ninja command.*{}$".format(para_value), "flag": False}
        expect_dict = {}
        test_target_list = ['build_all_test_pkg', 'package_testcase', 'package_testcase_mlf']

        if para_value.endswith('make_test') or para_value.split(':')[-1] in test_target_list:
            expect_dict["use_thin"] = True
            expect_dict["ninja_build_target"] = True
        else:
            expect_dict["use_thin"] = False
            expect_dict["ninja_build_target"] = True
        return flags, expect_dict

    @staticmethod
    def get_ninja_args_flags(para_value):
        flags = copy.deepcopy(TestBuildOption.FLAGS)
        expect_dict = {"ninja_args": True}
        flags["ninja_args"] = {"pattern": r"Excuting ninja command.*{}".format(para_value), "flag": False}

        return flags, expect_dict

    @staticmethod
    def get_full_compilation_flags(para_value):
        flags = copy.deepcopy(TestBuildOption.FLAGS)
        flags["full_compilation_gn"] = {"pattern": r"Excuting gn command.*use_thin_lto=false.*", "flag": False}
        flags["full_compilation_ninja"] = {"pattern": r"Excuting ninja command.*make_all make_test$", "flag": False}
        expect_dict = {}

        if para_value in ["", "True"]:
            expect_dict["full_compilation_gn"] = True
            expect_dict["full_compilation_ninja"] = True
        else:
            expect_dict["full_compilation_gn"] = False
            expect_dict["full_compilation_ninja"] = False

        return flags, expect_dict

    @staticmethod
    def get_strict_mode_flags(para_value):
        flags = copy.deepcopy(TestBuildOption.FLAGS)
        expect_dict = {}

        return flags, expect_dict

    @staticmethod
    def get_scalable_build_flags(para_value):
        flags = copy.deepcopy(TestBuildOption.FLAGS)
        expect_dict = {}

        return flags, expect_dict

    @staticmethod
    def get_build_example_flags(para_value):
        flags = copy.deepcopy(TestBuildOption.FLAGS)
        build_example_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "subsystem_config_example.json")
        flags["build_example"] = {
            "pattern": r"loader args.*example_subsystem_file=.*{}.*".format(build_example_file_path), "flag": False}
        expect_dict = {}

        if para_value.lower() == "true":
            expect_dict["build_example"] = True
        else:
            expect_dict["build_example"] = False

        return flags, expect_dict

    @staticmethod
    def get_build_platform_name_flags(para_value):
        flags = copy.deepcopy(TestBuildOption.FLAGS)
        expect_dict = {}

        if para_value == "phone":
            flags["build_platform"] = {
                "pattern": r"loader args.*build_platform_name=phone", "flag": False}
            expect_dict["build_platform"] = True

        return flags, expect_dict

    @staticmethod
    def get_build_xts_flags(para_value):
        flags = copy.deepcopy(TestBuildOption.FLAGS)
        expect_dict = {}

        flags["build_xts"] = {"pattern": r"loader args.*build_xts={}.*".format(para_value.capitalize()), "flag": False}

        return flags, expect_dict

    @staticmethod
    def get_ignore_api_check_flags(para_value):
        flags = copy.deepcopy(TestBuildOption.FLAGS)
        expect_dict = {}

        if para_value == "":
            flags["ignore_api_check"] = {"pattern": r"loader args.*ignore_api_check=\['xts', 'common', 'testfwk'\]",
                                         "flag": False}
        else:
            flags["ignore_api_check"] = {
                "pattern": r"loader args.*ignore_api_check=(.*)\",",
                "flag": False}

        return flags, expect_dict

    @staticmethod
    def get_load_test_config_flags(para_value):
        flags = copy.deepcopy(TestBuildOption.FLAGS)
        expect_dict = {}

        flags["load_test"] = {"pattern": r"loader args.*load_test_config={}.*".format(para_value.capitalize()),
                              "flag": False}

        return flags, expect_dict

    @staticmethod
    def get_build_type_flags(para_value):
        flags = copy.deepcopy(TestBuildOption.FLAGS)
        expect_dict = {}
        flags["build_type_debug"] = {"pattern": r"Excuting gn command.*is_debug=true",
                                     "flag": False}
        flags["build_type_profile"] = {"pattern": r"Excuting gn command.*is_profile=true",
                                       "flag": False}
        flags["build_type_none"] = {
            "pattern": r'Excuting gn command.*ohos_build_type=\\"debug\\"',
            "flag": False}

        if para_value == "debug":
            expect_dict["build_type_debug"] = True
            expect_dict["build_type_profile"] = False
            expect_dict["build_type_none"] = True
        elif para_value == "profile":
            expect_dict["build_type_debug"] = False
            expect_dict["build_type_profile"] = True
            expect_dict["build_type_none"] = True
        else:
            expect_dict["build_type_debug"] = False
            expect_dict["build_type_profile"] = False
            expect_dict["build_type_none"] = True

        return flags, expect_dict

    @staticmethod
    def get_log_level_flags(para_value):
        flags = copy.deepcopy(TestBuildOption.FLAGS)

        flags["tracelog"] = {"pattern": r"Excuting gn command.*--tracelog=.*/gn_trace.log.*--ide=json", "flag": False}
        flags["ninja_v"] = {"pattern": r"Excuting ninja command.*-v.*", "flag": False}
        expect_dict = {}

        if para_value == "info":
            expect_dict["tracelog"] = False
            expect_dict["ninja_v"] = False
        elif para_value == "debug":
            expect_dict["tracelog"] = True
            expect_dict["ninja_v"] = True

        return flags, expect_dict

    @staticmethod
    def get_test_flags(para_value):
        flags = copy.deepcopy(TestBuildOption.FLAGS)
        expect_dict = {}
        flags["notest"] = {"pattern": r'Excuting gn command.*ohos_test_args=\\"notest\\"',
                           "flag": False}
        flags["xts"] = {"pattern": r'Excuting gn command.*ohos_xts_test_args=\\"xxx\\"',
                        "flag": False}

        if para_value == "":
            expect_dict["notest"] = False
            expect_dict["xts"] = False
        elif para_value == "notest xxx":
            expect_dict["notest"] = True
            expect_dict["xts"] = False
        elif para_value in ["xts xxx", "xxx xts"]:
            expect_dict["notest"] = False
            expect_dict["xts"] = True
        elif para_value == "xxx ccc":
            expect_dict["notest"] = False
            expect_dict["xts"] = False

        return flags, expect_dict

    @staticmethod
    def get_gn_args_flags(para_value):
        flags = copy.deepcopy(TestBuildOption.FLAGS)
        expect_dict = {}

        flags["device_type"] = {
            "pattern": r'Excuting gn command.*device_type=\\"default\\"', "flag": False}
        flags["build_variant"] = {
            "pattern": r'Excuting gn command.*build_variant=\\"root\\"', "flag": False}
        flags["para"] = {
            "pattern": r'Excuting gn command.*{}'.format(para_value), "flag": False}

        return flags, expect_dict

    @staticmethod
    def get_fast_rebuild_flags(para_value):
        flags = copy.deepcopy(TestBuildOption.FLAGS)
        expect_dict = {}

        if para_value.lower() == "true" or para_value == "":
            expect_dict["gn"] = False
            expect_dict["done"] = False
        return flags, expect_dict

    @staticmethod
    def get_skip_partlist_check_flags(para_value):
        flags = copy.deepcopy(TestBuildOption.FLAGS)
        expect_dict = {}
        partlist_flag = True if para_value.lower() == "true" else False
        flags["partlist"] = {"pattern": r"loader args.*skip_partlist_check={}".format(partlist_flag), "flag": False}
        return flags, expect_dict

    @staticmethod
    def get_deps_guard_flags(para_value):
        flags = copy.deepcopy(TestBuildOption.FLAGS)
        expect_dict = {}
        flags["os_level"] = {"pattern": r"loader args.*os_level=([a-zA-Z]+)\'", "flag": False}
        return flags, expect_dict

    @staticmethod
    def get_compute_overlap_rate_flags(para_value):
        flags = copy.deepcopy(TestBuildOption.FLAGS)
        flags["c_targets"] = {"pattern": r"c targets overlap rate statistics", "flag": False}
        flags["c_overall"] = {"pattern": r"c overall build overlap rate", "flag": False}
        expect_dict = {}

        if para_value.lower() in ("true", ""):
            expect_dict["c_targets"] = True
            expect_dict["c_overall"] = True
        else:
            expect_dict["c_targets"] = False
            expect_dict["c_overall"] = False
        return flags, expect_dict

    @staticmethod
    def get_stat_ccache_flags(para_value):
        flags = copy.deepcopy(TestBuildOption.FLAGS)
        expect_dict = {}
        flags["ccache_dir"] = {"pattern": r"ccache_dir =.*, ccache_exec =.*", "flag": False}
        flags["ccache_summary"] = {"pattern": r"ccache summary", "flag": False}

        if para_value.lower() in ("true", ""):
            expect_dict["ccache_dir"] = True
            expect_dict["ccache_summary"] = True
        else:
            expect_dict["ccache_dir"] = False
            expect_dict["ccache_summary"] = False

        return flags, expect_dict

    @staticmethod
    def get_keep_ninja_going_flags(para_value):
        flags = copy.deepcopy(TestBuildOption.FLAGS)
        expect_dict = {}
        if para_value.lower() == "true":
            flags.setdefault("ninja", {}).setdefault("pattern", r"Excuting ninja command.*-k1000000.*")

        return flags, expect_dict

    @staticmethod
    def get_common_flags(para_value, check_file=False):
        flags = copy.deepcopy(TestBuildOption.FLAGS)
        expect_dict = {}
        if check_file:
            flags["os_level"] = {"pattern": r"loader args.*os_level=([a-zA-Z]+)\'", "flag": False}
            flags["root_dir"] = {"pattern": r"""loader args.*source_root_dir="([a-zA-Z\d/\\_]+)""""", "flag": False}
            flags["gn_dir"] = {"pattern": r"""loader args.*gn_root_out_dir="([a-zA-Z\d/\\_]+)""""", "flag": False}
            flags["start_end_time"] = {"pattern": r"(\d+-\d+-\d+ \d+:\d+:\d+)", "flag": False}
            flags["cost_time"] = {"pattern": r"Cost time:.*(\d+:\d+:\d+)", "flag": False}
        return flags, expect_dict

    @staticmethod
    def check_file_res(resolve_result, file_list, is_real_path=False, time_over=TIME_OVER):
        root_dir = resolve_result["root_dir"]["flag"][0]
        gn_dir = resolve_result["gn_dir"]["flag"][0]
        start_time_str = resolve_result["start_end_time"]["flag"][0]
        end_time_str = resolve_result["start_end_time"]["flag"][-1]

        start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")

        start_timestamp = int(datetime.timestamp(start_time))
        end_timestamp = int(datetime.timestamp(end_time))

        file_list_new = []
        for tmp_file in file_list:
            real_path = tmp_file if is_real_path else os.path.join(root_dir, gn_dir, tmp_file)
            if os.path.exists(real_path):
                file_list_new.append(real_path)
        if not file_list_new:
            log_info("all file {} not exist".format(file_list))
            return True
        file_timestamp_li = {tmp_file: int(os.stat(tmp_file).st_mtime) for tmp_file in file_list_new}

        cost_time_str = resolve_result["cost_time"]["flag"][0]
        cost_time = datetime.strptime(cost_time_str, "%H:%M:%S")
        cost_time_int = timedelta(hours=cost_time.hour, minutes=cost_time.minute, seconds=cost_time.second)
        total_seconds = int(cost_time_int.total_seconds())
        new_start_timestamp = end_timestamp - total_seconds
        log_info("log_cost_time:{}s".format(total_seconds))
        log_info("start_timestamp:{}".format(start_timestamp))
        log_info("new_start_timestamp:{}".format(new_start_timestamp))
        log_info("end_timestamp:{}".format(end_timestamp))
        file_flag = False
        file_tmp_flag_li = []

        for file_tmp, file_timestamp in file_timestamp_li.items():
            log_info("{}:{}".format(file_tmp, file_timestamp))
            file_tmp_flag = new_start_timestamp - time_over <= file_timestamp <= end_timestamp + time_over
            file_tmp_flag_li.append(file_tmp_flag)

        if all(file_tmp_flag_li):
            file_flag = True

        return file_flag

    @pytest.mark.parametrize('cpu_para', ['arm', 'arm64', 'x86_64'])
    def test_target_cpu(self, cpu_para):
        """
        test target_cpu parameter
        """
        cmd = self.CMD.format('--target-cpu', cpu_para).split()

        result = self.get_match_result(cmd, "target_cpu", cpu_para)

        assert result == 0, "target cpu para {} failed".format(cpu_para)

    @pytest.mark.parametrize('ccache_para', ['True', 'False'])
    def test_ccache(self, ccache_para):
        """
        test ccache_para parameter
        """
        cmd = self.CMD.format('--ccache', ccache_para).split()

        result = self.get_match_result(cmd, "ccache", ccache_para)

        assert result == 0, "ccache para {} failed".format(ccache_para)

    @pytest.mark.parametrize('rename_last_log_para', ['True', 'False'])
    def test_rename_last_log(self, rename_last_log_para):
        """
        test rename_last_log parameter
        """
        cmd = self.CMD.format('--rename-last-log', rename_last_log_para).split()
        mtime = ""
        file_name = ""

        if self.is_exist(self.LOG_PATH):
            mtime = os.stat(self.LOG_PATH).st_mtime
            file_name = '{}/build.{}.log'.format(self.LOG_PATH, mtime)
        log_info("test_rename_last_log,file name is {}".format(file_name))
        result = self.get_match_result(cmd, "rename_last_log", rename_last_log_para)
        new_path = os.path.join(os.path.dirname(self.LOG_PATH), "build.{}.log".format(mtime))
        log_info("test_rename_last_log,new path is {}".format(new_path))

        if rename_last_log_para == 'True':
            assert self.is_exist(new_path) and result == 0, "rename_last_log para {} failed".format(
                rename_last_log_para)
        elif rename_last_log_para == 'False':
            assert not self.is_exist(new_path) and result == 0, "rename_last_log para {} failed".format(
                rename_last_log_para)

    @pytest.mark.parametrize('build_target', ['', 'package_testcase'])
    def test_build_target(self, build_target):
        """
        test build_target parameter
        """
        cmd = self.CMD.format('--build-target', build_target).split()

        result = self.get_match_result(cmd, "build_target", build_target)

        assert result == 0, "build target para {} failed".format(build_target)

    @pytest.mark.parametrize('ninja_args', ['-dkeeprsp'])
    def test_ninja_args(self, ninja_args):
        """
        test ninja_args parameter
        """
        cmd = self.NINJIA_CMD.format(ninja_args).split()

        result = self.get_match_result(cmd, "ninja_args", ninja_args)

        assert result == 0, "ninja args para {} failed".format(ninja_args)

    @pytest.mark.parametrize('full_compilation', ['True', 'False', ''])
    def test_full_compilation(self, full_compilation):
        """
        test full_compilation parameter
        """
        cmd = self.CMD.format('--full-compilation', full_compilation).split()

        result = self.get_match_result(cmd, "full_compilation", full_compilation)

        assert result == 0, "full compilation para {} failed".format(full_compilation)

    @pytest.mark.parametrize('strict_mode', ['True', 'False', 'false'])
    def test_strict_mode(self, strict_mode):
        """
        test strict_mode parameter
        """
        cmd = self.CMD.format('--strict-mode', strict_mode).split()

        result = self.get_match_result(cmd, "strict_mode", strict_mode)

        assert result == 0, "strict mode para {} failed".format(strict_mode)

    @pytest.mark.parametrize('scalable_build', ['True', 'False', 'false'])
    def test_scalable_build(self, scalable_build):
        """
        test scalable_build parameter
        """
        cmd = self.CMD.format('--scalable-build', scalable_build).split()

        result = self.get_match_result(cmd, "scalable_build", scalable_build)

        assert result == 0, "scalable build para {} failed".format(scalable_build)

    @pytest.mark.parametrize('build_example', ['True', 'False', 'true', 'false'])
    def test_build_example(self, build_example):
        """
        test build_example parameter
        """
        cmd = self.CMD.format('--build-example', build_example).split()

        result = self.get_match_result(cmd, "build_example", build_example)

        assert result == 0, "build example para {} failed".format(build_example)

    @pytest.mark.parametrize('build_platform_name', ['phone'])
    def test_build_platform_name(self, build_platform_name):
        """
        test build_platform_name parameter
        """
        cmd = self.CMD.format('--build-platform-name', build_platform_name).split()

        result = self.get_match_result(cmd, "build_platform_name", build_platform_name)

        assert result == 0, "build platform name para {} failed".format(build_platform_name)

    @pytest.mark.parametrize('build_xts', ['True', 'False', 'true', 'false'])
    def test_build_xts(self, build_xts):
        """
        test build_xts parameter
        """
        cmd = self.CMD.format('--build-xts', build_xts).split()

        result = self.get_match_result(cmd, "build_xts", build_xts)

        assert result == 0, "build xts para {} failed".format(build_xts)

    @pytest.mark.parametrize('ignore_api_check', ['common xts', ''])
    def test_ignore_api_check(self, ignore_api_check):
        """
        test ignore_api_check parameter
        """
        para_list = ignore_api_check.split()
        cmd = self.CMD.format('--ignore-api-check', ignore_api_check).split()
        resolve_result, result, _ = self.get_common_spec_result(ignore_api_check, cmd,
                                                                para_type="ignore_api_check")
        if result != 0:
            assert result == 0, "ignore api check para {} failed".format(ignore_api_check)
        else:
            if ignore_api_check:
                ignore_str = resolve_result["ignore_api_check"]["flag"][0]  # ['xts', 'common']
                log_info("ignore_str is {}".format(ignore_str))
                ignor_li = eval(ignore_str)
                log_info("ignor_li is {0},type is {1}".format(ignor_li, type(ignor_li)))
                assert self.same_element(para_list, ignor_li) and result == 0, "ignore api check para {} failed".format(
                    ignore_api_check)

    @pytest.mark.parametrize('load_test_config', ['True', 'False', 'true', 'false'])
    def test_load_test_config(self, load_test_config):
        """
        test load_test_config parameter
        """
        cmd = self.CMD.format('--load-test-config', load_test_config).split()

        result = self.get_match_result(cmd, "load_test_config", load_test_config)

        assert result == 0, "load test config para {} failed".format(load_test_config)

    @pytest.mark.parametrize('build_type', ['debug', 'release', 'profile'])
    def test_build_type(self, build_type):
        """
        test build_type parameter
        """
        cmd = self.CMD.format('--build-type', build_type).split()
        result = self.get_match_result(cmd, "build_type", build_type)

        assert result == 0, "build type para {} failed".format(build_type)

    @pytest.mark.parametrize('log_level', ['info', 'debug'])
    def test_log_level(self, log_level):
        """
        test log_level parameter
        """
        cmd = self.CMD.format('--log-level', log_level).split()

        result = self.get_match_result(cmd, "log_level", log_level)

        assert result == 0, "log level para {} failed".format(log_level)

    @pytest.mark.parametrize('build_only_gn', ['True', 'False'])
    def test_build_only_gn(self, build_only_gn):
        """
        test build_only_gn parameter
        """
        cmd = self.CMD.format('--build-only-gn', build_only_gn).split()

        result = self.get_match_result(cmd, "build_only_gn", build_only_gn)

        assert result == 0, "build only gn para {} failed".format(build_only_gn)

    @pytest.mark.parametrize('test', ['', 'notest xxx', 'xts xxx', 'xxx xts'])
    def test_test(self, test):
        """
        test test parameter
        """
        cmd = self.CMD.format('--test', test).split()

        result = self.get_match_result(cmd, "test", test)

        assert result == 0, "test para {} failed".format(test)

    @pytest.mark.parametrize('gn_args', ['', 'is_debug=true'])
    def test_gn_args(self, gn_args):
        """
        test gn_args parameter
        """
        cmd = self.CMD.format('--gn-args', gn_args).split()

        result = self.get_match_result(cmd, "gn_args", gn_args)

        assert result == 0, "gn args para {} failed".format(gn_args)

    @pytest.mark.parametrize('fast_rebuild', ['True', 'False', ''])
    def test_fast_rebuild(self, fast_rebuild):
        """
        test fast_rebuild parameter
        """
        cmd = self.CMD.format('--fast-rebuild', fast_rebuild).split()

        result = self.get_match_result(cmd, "fast_rebuild", fast_rebuild)

        assert result == 0, "fast rebuild para {} failed".format(fast_rebuild)

    @pytest.mark.parametrize('going_option', ['True', 'False'])
    def test_keep_ninja_going(self, going_option):
        """
        test keep_ninja_going parameter
        """
        cmd = self.CMD.format('--keep-ninja-going', going_option).split()

        result = self.get_match_result(cmd, "keep_ninja_going", going_option)

        assert result == 0, "keep_ninja_going para {} failed".format(going_option)

    @pytest.mark.parametrize('variant_option', ['user', 'root'])
    def test_build_variant(self, variant_option):
        """
        test build_variant parameter
        """
        cmd = self.CMD.format('--build-variant', variant_option).split()

        resolve_result, result, _ = self.get_common_spec_result(variant_option, cmd)
        if result != 0:
            assert result == 0, "build_variant para {} failed".format(variant_option)
        else:
            root_dir = resolve_result["root_dir"]["flag"][0]
            gn_dir = resolve_result["gn_dir"]["flag"][0]

            ohos_para_path = "packages/phone/system/etc/param/ohos.para"
            if os.path.exists(os.path.join(root_dir, gn_dir, ohos_para_path)):
                check_file_li = [ohos_para_path]
                check_file_flag = self.check_file_res(resolve_result, check_file_li)
                assert result == 0 and check_file_flag, "build_variant para {} failed".format(variant_option)
            else:
                assert result == 0, "build_variant para {} failed".format(variant_option)

    @pytest.mark.parametrize('device_option', ['default', 'unkown'])
    def test_device_type(self, device_option):
        """
        test device_type parameter
        """
        cmd = self.CMD.format('--device-type', device_option).split()

        resolve_result, result, _ = self.get_common_spec_result(device_option, cmd)
        if result != 0:
            if device_option == "unkown":
                assert result == 1, "device_type para {} failed".format(device_option)
            else:
                assert result == 0, "device_type para {} failed".format(device_option)

        else:
            if device_option == "default":
                assert result == 0, "device_type para {} failed".format(device_option)
            else:
                check_file_li = ["packages/phone/system/etc/param/ohos.para"]
                check_file_flag = self.check_file_res(resolve_result, check_file_li)
                assert result == 0 and check_file_flag, "device_type para {} failed".format(device_option)

    @pytest.mark.parametrize('archive_option', ['True', 'False'])
    def test_archive_image(self, archive_option):
        """
        test archive_image parameter
        """
        cmd = self.CMD.format('--archive-image', archive_option).split()

        resolve_result, result, cmd_res = self.get_common_spec_result(archive_option, cmd)
        if result != 0:
            assert result == 0, "archive_image para {} failed".format(archive_option)
        else:
            root_dir = resolve_result["root_dir"]["flag"][0]
            gn_dir = resolve_result["gn_dir"]["flag"][0]
            image_path = os.path.join("packages", "phone", "images")
            if archive_option.lower() == "true":
                if os.path.exists(os.path.join(root_dir, gn_dir, image_path)):
                    check_file_li = ["images.tar.gz"]
                    check_file_flag = self.check_file_res(resolve_result, check_file_li)
                    assert result == 0 and check_file_flag, "archive_image para {} failed".format(
                        archive_option)
                else:
                    archive_flags = {"archive_image": {"pattern": r'"--archive-image" option not work', "flag": False}}
                    archive_resolve_result = self.resolve_res(cmd_res, archive_flags)
                    archive_result = self.check_flags(archive_resolve_result)
                    assert result == 0 and archive_result == 0, "archive_image para {} failed".format(archive_option)
            else:
                assert result == 0, "archive_image para {} failed".format(archive_option)

    @pytest.mark.parametrize('rom_option', ['True', 'False'])
    def test_rom_size_statistics(self, rom_option):
        """
        test rom_size_statistics parameter
        """
        cmd = self.CMD.format('--rom-size-statistics', rom_option).split()

        resolve_result, result, _ = self.get_common_spec_result(rom_option, cmd, ptyflag=True)
        if result != 0:
            assert result == 0, "rom_size_statistics para {} failed".format(rom_option)
        else:
            os_level = resolve_result["os_level"]["flag"][0]
            log_info("os_level:{}".format(os_level))
            if os_level in ("mini", "small"):
                assert result == 0, "rom_size_statistics para {} failed".format(rom_option)
            else:
                check_file_li = ["rom_statistics_table.json"]
                check_file_flag = self.check_file_res(resolve_result, check_file_li)
                if rom_option.lower() == "false":
                    assert result == 0 and not check_file_flag, "rom_option para {} failed".format(
                        rom_option)
                else:
                    assert result == 0 and check_file_flag, "rom_option para {} failed".format(rom_option)

    @pytest.mark.parametrize('ccache_option', ['True', 'False'])
    def test_stat_ccache(self, ccache_option):
        """
        test stat_ccache parameter
        """
        cmd = self.CMD.format('--stat-ccache', ccache_option).split()

        result = self.get_match_result(cmd, "stat_ccache", ccache_option)

        assert result == 0, "stat_ccache para {} failed".format(ccache_option)

    @pytest.mark.parametrize('warning_option', ['True', 'False'])
    def test_get_warning_list(self, warning_option):
        """
        test get_warning_list parameter
        """
        cmd = self.CMD.format('--get-warning-list', warning_option).split()
        resolve_result, result, _ = self.get_common_spec_result(warning_option, cmd)
        if result != 0:
            assert result == 0, "get_warning_list para {} failed".format(warning_option)
        else:
            check_file_li = ["packages/WarningList.txt"]
            check_file_flag = self.check_file_res(resolve_result, check_file_li)
            if warning_option.lower() == "false":
                assert result == 0 and not check_file_flag, "get_warning_list para {} failed".format(
                    warning_option)
            else:
                assert result == 0 and check_file_flag, "get_warning_list para {} failed".format(warning_option)

    @pytest.mark.parametrize('ninja_option', ["True", "False", "true", "false"])
    def test_generate_ninja_trace(self, ninja_option):
        """
        test generate_ninja_trace parameter
        """
        cmd = self.CMD.format('--generate-ninja-trace', ninja_option).split()
        resolve_result, result, _ = self.get_common_spec_result(ninja_option, cmd)
        if result != 0:
            assert result == 0, "generate_ninja_trace para {} failed".format(ninja_option)
        else:
            check_file_li = ["build.trace.gz", "sorted_action_duration.txt"]
            check_file_flag = self.check_file_res(resolve_result, check_file_li)
            if ninja_option.lower() == "false":
                assert result == 0 and not check_file_flag, "generate_ninja_trace para {} failed".format(
                    ninja_option)
            else:
                assert result == 0 and check_file_flag, "generate_ninja_trace para {} failed".format(
                    ninja_option)

    @pytest.mark.parametrize('overlap_option', ['True', 'False'])
    def test_compute_overlap_rate(self, overlap_option):
        """
        test compute_overlap_rate parameter
        """
        cmd = self.CMD.format('--compute-overlap-rate', overlap_option).split()
        result = self.get_match_result(cmd, "compute_overlap_rate", overlap_option)

        assert result == 0, "compute_overlap_rate para {} failed".format(overlap_option)

    @pytest.mark.parametrize('clean_option', ['True', 'False'])
    def test_clean_args(self, clean_option):
        """
        test clean-args parameter
        """
        cmd = self.CMD.format('--clean-args', clean_option).split()
        resolve_result, result, _ = self.get_common_spec_result(clean_option, cmd)
        if result != 0:
            assert result == 0, "clean_args para {} failed".format(clean_option)
        else:
            root_dir = resolve_result["root_dir"]["flag"][0]
            json_path = os.path.join(root_dir, "out", "hb_args")
            json_file_li = [file for file in os.listdir(json_path) if os.path.splitext(file)[-1] == ".json"]
            log_info("test_clean_args, json_file_li:{}".format(json_file_li))
            if clean_option.lower() == "false":
                exist_flag = bool(json_file_li)
            else:
                exist_flag = not json_file_li

            assert result == 0 and exist_flag, "clean_args para {} failed".format(clean_option)

    @pytest.mark.parametrize('deps_guard_option', ['True', 'False'])
    def test_deps_guard(self, deps_guard_option):
        """
        test deps-guard parameter
        """
        cmd = self.CMD.format('--deps-guard', deps_guard_option).split()
        resolve_result, result, cmd_res = self.get_common_spec_result(deps_guard_option, cmd,
                                                                      para_type="deps_guard")
        if result != 0:
            assert result == 0, "deps_guard para {}failed.".format(deps_guard_option)
        else:
            os_level = resolve_result["os_level"]["flag"][0]
            log_info("test_deps_guard,os_level:{}".format(os_level))
            if deps_guard_option.lower() == "false" and os_level == "standard":
                standard_flags = {"Scanning": {"pattern": r"Scanning.*ELF files now", "flag": False},
                                  "rules": {"pattern": r"All rules passed", "flag": False}}
                standard_resolve_result = self.resolve_res(cmd_res, standard_flags)
                log_info("continue match Scanning and rules ...")
                standard_result = self.check_flags(standard_resolve_result)
                assert result == 0 and standard_result == 0, "deps_guard para {},os_level {} failed.".format(
                    deps_guard_option, os_level)
            else:
                assert result == 0, "deps_guard para {},os_level {} failed.".format(deps_guard_option, os_level)

    @pytest.mark.parametrize('partlist_option', ['True', 'False'])
    def test_skip_partlist_check(self, partlist_option):
        """
        test skip-partlist-check parameter
        """
        cmd = self.CMD.format('--skip-partlist-check', partlist_option).split()
        result = self.get_match_result(cmd, "skip_partlist_check", partlist_option)
        assert result == 0, "skip_partlist_check para {} failed".format(partlist_option)

    @pytest.mark.parametrize('enable_pycache', ['True', 'true', 'False', 'false'])
    def test_enable_pycache(self, enable_pycache):
        """
        test enable_pycache parameter
        """
        cmd = self.CMD.format('--enable-pycache', enable_pycache).split()

        pycache_dir = os.environ.get('CCACHE_BASE')
        if not pycache_dir:
            pycache_dir = os.environ.get('HOME')
        pycache_config = os.path.join(pycache_dir, '.pycache', '.config')
        resolve_result, result, _ = self.get_common_spec_result(enable_pycache, cmd,
                                                                para_type="enable_pycache", ptyflag=True)
        if result != 0:
            assert result == 0, "enable pycache para {} failed".format(enable_pycache)
        else:
            check_file_li = [pycache_config]
            check_file_flag = self.check_file_res(resolve_result, check_file_li, is_real_path=True)

            if enable_pycache.lower() == "true":
                assert result == 0 and check_file_flag, "enable pycache para {} failed".format(enable_pycache)
            else:
                assert result == 0 and not check_file_flag, "enable pycache para {} failed".format(enable_pycache)

    def exec_command_select(self, cmd, timeout=60, ptyflag=False):
        out_queue = queue.Queue()
        log_info("select_exec cmd is :{}".format(" ".join(cmd)))
        if not ptyflag:
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    encoding="utf-8",
                    universal_newlines=True,
                    errors='ignore'
                )
                start_time = time.time()
                while True:
                    if timeout and time.time() - start_time > timeout:
                        raise Exception("exec cmd time out,select")
                    ready_to_read, _, _ = select.select([proc.stdout, proc.stderr], [], [], self.select_timeout)
                    for stream in ready_to_read:
                        output = stream.readline().strip()
                        if output:
                            out_queue.put(output)
                    if proc.poll() is not None:
                        break
                returncode = proc.wait()
                out_res = list(out_queue.queue)
                return out_res, returncode
            except Exception as err_:
                log_error("An error occurred: {}".format(err_))
                raise Exception(err_)
        else:
            try:
                master, slave = pty.openpty()
                proc = subprocess.Popen(
                    cmd,
                    stdin=slave,
                    stdout=slave,
                    stderr=slave,
                    encoding="utf-8",
                    universal_newlines=True,
                    errors='ignore'
                )
                start_time = time.time()
                incomplete_line = ""
                while True:
                    if timeout and time.time() - start_time > timeout:
                        raise Exception("exec cmd time out,select")
                    ready_to_read, _, _ = select.select([master, ], [], [], self.select_timeout)
                    for stream in ready_to_read:
                        output_bytes = os.read(stream, 1024)
                        output = output_bytes.decode('utf-8')
                        lines = (incomplete_line + output).split("\n")
                        for line in lines[:-1]:
                            line = line.strip()
                            if line:
                                out_queue.put(line)
                        incomplete_line = lines[-1]
                    if proc.poll() is not None:
                        break
                returncode = proc.wait()
                out_res = list(out_queue.queue)
                return out_res, returncode
            except Exception as err_:
                log_error("An error occurred: {}".format(err_))
                raise Exception(err_)

    def get_match_result(self, cmd, para_type, para_value, ptyflag=PTYFLAG):
        cmd_res, returncode = self.exec_command(cmd, ptyflag=ptyflag)
        before_flags, expect_dict = self.get_match_flags(para_type, para_value)
        flag_res = self.resolve_res(cmd_res, before_flags)
        result = self.check_flags(flag_res, expect_dict, returncode)
        if result == 1:
            self.print_error_line(cmd_res)
        else:
            self.print_error_line(cmd_res, is_success=True)
        return result

    def get_match_flags(self, para_type, para_value):
        method_name = "get_{}_flags".format(para_type)
        if hasattr(self, method_name):
            method = self.__getattribute__(method_name)
            flags, expect_dict = method(para_value)
            return flags, expect_dict
        return None, None

    def get_common_spec_result(self, option, cmd, para_type=None, ptyflag=PTYFLAG):
        if not para_type:
            flag_res, expect_dict = self.get_common_flags(option, check_file=True)
        else:
            flag_res, expect_dict = self.get_match_flags(para_type, option)
        cmd_res, returncode = self.exec_command(cmd, ptyflag=ptyflag)
        resolve_result = self.resolve_res(cmd_res, flag_res)
        result = self.check_flags(resolve_result, expect_dict, returncode)
        if result == 1:
            self.print_error_line(cmd_res)
        else:
            self.print_error_line(cmd_res, is_success=True)
        return resolve_result, result, cmd_res

    def exec_command(self, cmd, ptyflag=PTYFLAG, timeout=TIMEOUT):
        if TestBuildOption.COMMAND_TYPE == "select":
            return self.exec_command_select(cmd, timeout=timeout, ptyflag=ptyflag)
        else:
            return self.exec_command_communicate(cmd, timeout=timeout)