#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2024 Huawei Device Co., Ltd.
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

import sys
import os
import time
import platform
from datetime import datetime
import re
from pathlib import Path
import subprocess
from collections import defaultdict 

from resources.global_var import ROOT_CONFIG_FILE
from log_util import LogUtil
from io_util import IoUtil

GB_CONSTANT = 1024 ** 3
MEM_CONSTANT = 1024
RET_CONSTANT = 0
MONITOR_TIME_CONSTANT = 30
SNOP_TIME_CONSTANT = 5


class Monitor():
    def __init__(self):
        self.now_times = []
        self.usr_cpus = []
        self.sys_cpus = []
        self.idle_cpus = []
        self.total_mems = []
        self.swap_mems = []
        self.free_mems = []
        self.log_path = ""

    def collect_cpu_info(self):
        if platform.system() != "Linux":
            return RET_CONSTANT, RET_CONSTANT, RET_CONSTANT

        try:
            result = subprocess.check_output(["top", "-bn1", "|", "grep", "'%Cpu(s)'"], universal_newlines=True).strip()
            if result:
                parts = result.split()
                if len(parts) >= 5:
                    usr_cpu_str = parts[1]
                    sys_cpu_str = parts[3]
                    idle_cpu_str = parts[7]

                    usr_cpu_str = usr_cpu_str.split(',')[0].rstrip('%')
                    sys_cpu_str = sys_cpu_str.split(',')[0].rstrip('%')
                    idle_cpu_str = idle_cpu_str.split(',')[0].rstrip('%')

                    usr_cpu = float(usr_cpu_str) if usr_cpu_str.replace('.', '', 1).isdigit() else self.RET_CONSTANT
                    sys_cpu = float(sys_cpu_str) if sys_cpu_str.replace('.', '', 1).isdigit() else self.RET_CONSTANT
                    idle_cpu = float(idle_cpu_str) if idle_cpu_str.replace('.', '', 1).isdigit() else self.RET_CONSTANT

                    self.usr_cpu = usr_cpu
                    self.sys_cpu = sys_cpu
                    self.idle_cpu = idle_cpu
                    return self.usr_cpu, self.sys_cpu, self.idle_cpu
                else:
                    return RET_CONSTANT, self.RET_CONSTANT, self.RET_CONSTANT
            else:
                return self.RET_CONSTANT, self.RET_CONSTANT, self.RET_CONSTANT
        except subprocess.CalledProcessError:
            return self.RET_CONSTANT, self.RET_CONSTANT, self.RET_CONSTANT

    def get_linux_mem_info(self):
        try:
            with open('/proc/meminfo', 'r') as f:
                total_memory = RET_CONSTANT
                swap_memory = RET_CONSTANT
                free_memory = RET_CONSTANT
                for line in f:
                    if line.startswith('MemTotal:'):
                        total_memory = int(re.search(r'\d+', line).group()) * MEM_CONSTANT
                    elif line.startswith('SwapTotal:'):
                        swap_memory = int(re.search(r'\d+', line).group()) * MEM_CONSTANT
                    elif line.startswith('MemFree'):
                        free_memory = int(re.search(r'\d+', line).group()) * MEM_CONSTANT
                return total_memory, swap_memory, free_memory
        except FileNotFoundError:
            return RET_CONSTANT, RET_CONSTANT, RET_CONSTANT
        except Exception as e:
            print(f"Error occurred while getting memory info: {e}")
            return RET_CONSTANT, RET_CONSTANT, RET_CONSTANT

    def collect_linux_mem_info(self):
        total_memory, swap_memory, free_memory = self.get_linux_mem_info()
        total_mem = round(total_memory / GB_CONSTANT, 1)
        free_mem = round(free_memory / GB_CONSTANT, 1)
        swap_mem = round(swap_memory / GB_CONSTANT, 1)
        return total_mem, free_mem, swap_mem
    
    def get_current_time(self):
        now_time = datetime.now().strftime("%H:%M:%S")
        self.now_times.append(now_time)

    def get_current_cpu(self):
        usr_cpu, sys_cpu, idle_cpu = self.collect_cpu_info()
        self.usr_cpus.append(usr_cpu)
        self.sys_cpus.append(sys_cpu)
        self.idle_cpus.append(idle_cpu)
        LogUtil.write_log(self.log_path, f"User Cpu%: {usr_cpu}%", "info")
        LogUtil.write_log(self.log_path, f"System Cpu%: {sys_cpu}%", "info")
        LogUtil.write_log(self.log_path, f"Idle CPU%: {idle_cpu}%", "info")
        
    def get_current_memory(self):
        total_mem, free_mem, swap_mem = self.collect_linux_mem_info()
        self.total_mems.append(total_mem)
        self.free_mems.append(free_mem)
        self.swap_mems.append(swap_mem)
        LogUtil.write_log(self.log_path, f"Total Memory: {total_mem}GB", "info")
        LogUtil.write_log(self.log_path, f"Free Memory: {free_mem}GB", "info")
        LogUtil.write_log(self.log_path, f"Swap Memory: {swap_mem}GB", "info")

    def get_log_path(self):
        count = 0
        config_content = IoUtil.read_json_file(ROOT_CONFIG_FILE)
        while not os.path.exists(ROOT_CONFIG_FILE) or not config_content.get('out_path', None) and count <= 60:
            time.sleep(SNAP_TIME_CONSTANT)
            count += 1
        return config_content.get('out_path', None)

    def get_disk_usage(self):
        result = subprocess.run(['df', '-h'], stdout=subprocess.PIPE, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]
            for line in lines:
                columns = line.split()
                if len(columns) > 5:
                    filesystem, size, used, available, percent, mountpoint = columns[:6]
                    LogUtil.write_log(self.log_path, 
                    f"Filesystem: {filesystem}, "
                    f"Size: {size}, "
                    f"Used: {used}, "
                    f"Available: {available}, "
                    f"Use%: {percent}, "
                    f"Mounted on: {mountpoint}", 
                    "info")
        else:
            LogUtil.write_log(self.log_path, f"Error running df command:{result.stderr}", "info")

    def run(self):
        if platform.system() != "Linux":
            return
        out_path = self.get_log_path()
        self.log_path = os.path.join(out_path, "build.log")
        self.get_current_time()
        self.get_current_cpu()
        self.get_current_memory()
        self.get_disk_usage()
