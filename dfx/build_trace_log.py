#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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


import os
import subprocess
import json
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple, Optional, Set
import re
import sys
from dfx import dfx_info, dfx_error

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class BuildTraceLog:
    def __init__(self):
        # 用户相关信息
        self.user_id = None                  # 用户ID
        self.git_user_email = None           # Git用户邮箱
        self.code_repo = None                # 代码仓库
        self.user_source = None              # 用户来源

        # 主机信息
        self.host_cpu_info = None            # 主机CPU信息
        self.host_mem_info = None            # 主机内存信息
        self.host_ip = None                  # 主机IP地址

        # 构建时间信息
        self.build_start_time = None         # 构建开始时间
        self.build_end_time = None           # 构建结束时间
        self.build_trace_id = None           # 构建跟踪ID

        # 构建配置信息
        self.build_type = None               # 构建类型
        self.build_args = None            # 构建参数
        self.build_target = None           # 构建目标
        self.build_command = None          # 构建命令
        self.build_product_type = None       # 构建产品类型

        # 构建资源使用情况
        self.build_cpu_usage = None          # 构建CPU使用率平均值
        self.build_mem_usage = None          # 构建内存使用率平均值(MB)
        self.build_time_cost = None          # 构建耗时
        self.build_time_cost_detail = None   # 构建耗时详情

        # 构建结果信息
        self.build_result = None             # 构建结果
        self.build_error_log = None          # 构建错误日志
        self.initialize_host_info()
        self.initialize_git_info()

    def __str__(self):
        result = []
        result.append("TraceLog Info:")
        result.append(f"User Info: user_id={self.user_id}, git_user_email={self.git_user_email}, code_repo={self.code_repo}")
        result.append(f"Host Info: cpu={self.host_cpu_info}, mem={self.host_mem_info}, ip={self.host_ip}")
        result.append(f"Build Time: start={self.build_start_time}, end={self.build_end_time}, cost={self.build_time_cost}")
        result.append(
            f"Build Config: type={self.build_type}, args={self.build_args}, product={self.build_product_type}"
        )
        result.append(f"Resource Usage: CPU={self.build_cpu_usage}%, Memory={self.build_mem_usage}MB")
        result.append(f"Build Result: {self.build_result}")
        if self.build_error_log:
            result.append(f"Error Log: {self.build_error_log}")
        return "\n".join(result)

    def to_dict(self):
        """将TraceLog对象转换为字典格式"""
        return {
            "user_id": self.user_id,
            "git_user_email": self.git_user_email,
            "code_repo": self.code_repo,
            "user_source": self.user_source,
            "host_cpu_info": self.host_cpu_info,
            "host_mem_info": self.host_mem_info,
            "host_ip": self.host_ip,
            "build_start_time": self.build_start_time,
            "build_end_time": self.build_end_time,
            "build_trace_id": self.build_trace_id,
            "build_type": self.build_type,
            "build_target": self.build_target,
            "build_command": self.build_command,
            "build_args": self.build_args,
            "build_product_type": self.build_product_type,
            "build_cpu_usage": self.build_cpu_usage,
            "build_mem_usage": self.build_mem_usage,
            "build_time_cost": self.build_time_cost,
            "build_time_cost_detail": self.build_time_cost_detail,
            "build_result": self.build_result,
            "build_error_log": self.build_error_log,
        }

    def from_dict(self, data_dict):
        for key, value in data_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self

    def initialize_host_info(self):
        self._get_cpu_info()
        self._get_memory_info()
        self._get_host_ip()
        return self

    def initialize_git_info(self):
        self._get_user_info_from_git()
        self._get_code_repo()
        return self

    def from_build_traces_log(self, log_file_path: str) -> bool:
        try:
            # 解析日志文件
            build_success_flag, parsed_data = self._parse_build_traces(log_file_path)

            if not build_success_flag:
                dfx_info(
                    f"Build failed, stop parsing build_traces log file {log_file_path}"
                )
                if log_file_path:
                    os.remove(log_file_path)
                return False

            # 填充基本信息
            if parsed_data['trace_id']:
                self.build_trace_id = parsed_data['trace_id']

            # 提取构建开始和结束时间
            events = parsed_data['events']
            if events:
                for event in events:
                    if event.get("event_name") == "_build_main":
                        self.build_start_time = datetime.fromtimestamp(
                            event["start_time"]
                        ).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

                        self.build_end_time = datetime.fromtimestamp(
                            event["end_time"]
                        ).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                        break

            # 提取构建资源使用情况 - 只保留平均值
            self.build_cpu_usage = parsed_data['cpu_avg']
            self.build_mem_usage = parsed_data['mem_avg_mb']

            # 提取各函数执行时间详情
            self.build_time_cost_detail = parsed_data['execution_times']

            # 判断构建结果（假设如果有error类型的事件，则构建失败）
            has_error = any(event.get("status") == "failed" for event in events)
            self.build_result = 'success' if not has_error else 'failed'

            # 如果有错误事件，提取错误信息
            if has_error:
                error_events = [event for event in events if event.get("status") == "failed"]
                self.build_error_log = json.dumps(error_events, ensure_ascii=False, default=str)

            # 从args_info中提取构建配置信息
            for event in events:
                if "raw_args" in event and event["raw_args"] and not self.build_command:
                    raw_args = event.get("raw_args", [])
                    if raw_args:
                        self.build_command = "./build.sh " + " ".join(raw_args)
                    else:
                        self.build_command = "unknown command"
                    self.build_target = self._parse_build_target()

                if 'args_info' in event and event['args_info']:
                    try:
                        # 尝试解析args_info
                        self.build_args = (
                            json.loads(event["args_info"])
                            if isinstance(event["args_info"], str)
                            else event["args_info"]
                        )

                        # 提取构建产品类型
                        if "product_name" in self.build_args[0] and not self.build_product_type:
                            self.build_product_type = self.build_args[0][
                                "product_name"
                            ].replace("product_name=", "")

                    except (json.JSONDecodeError, TypeError):
                        continue
                
                if "build_type" in event and not self.build_type:
                    self.build_type = event["build_type"]
                
                # 如果已经提取了所需信息，可以提前退出
                if self.build_type and self.build_product_type and self.build_command and self.build_target:
                    break

        except Exception as e:
            dfx_info(f"Failed to parse build_traces log file {log_file_path}: {str(e)}")
            # 设置错误日志
            self.build_error_log = str(e)
            self.build_result = 'failed'
            return False

        return True

    def _get_user_info_from_git(self):
        # 获取git用户名 (user.name) 作为user_id
        user_name = subprocess.check_output(['git', 'config', 'user.name'], 
                                         stderr=subprocess.STDOUT, 
                                         universal_newlines=True).strip()
        self.user_id = user_name

        # 获取git用户邮箱
        email = subprocess.check_output(['git', 'config', 'user.email'], 
                                      stderr=subprocess.STDOUT, 
                                      universal_newlines=True).strip()
        self.git_user_email = email

        return self

    def _get_code_repo(self):
        # 使用repo info | grep "Manifest branch"命令获取仓库信息
        # 使用shell=True来支持管道命令
        result = subprocess.check_output('repo info -o | grep "Manifest branch"', 
                                       shell=True, 
                                       stderr=subprocess.STDOUT, 
                                       universal_newlines=True).strip()

        # 提取Manifest branch信息
        if result:
            # 例如：Manifest branch: refs/heads/master
            self.code_repo = result
        else:
            raise Exception("Failed to get Manifest branch information: empty result")
        return self

    def _get_cpu_info(self):
        # 获取CPU型号
        cpu_model = subprocess.check_output("cat /proc/cpuinfo | grep 'model name' | head -n 1 | cut -d: -f2 | tr -s ' '",
                                          shell=True,
                                          stderr=subprocess.STDOUT,
                                          universal_newlines=True).strip()

        # 获取CPU核心数
        cpu_cores = subprocess.check_output("nproc",
                                          shell=True,
                                          stderr=subprocess.STDOUT,
                                          universal_newlines=True).strip()

        self.host_cpu_info = f"CPU Model: {cpu_model}, Cores: {cpu_cores}"
        return self

    def _get_memory_info(self):
        # 使用free命令获取内存信息
        free_output = subprocess.check_output("free -h",
                                            shell=True,
                                            stderr=subprocess.STDOUT,
                                            universal_newlines=True)

        # 解析总内存信息
        for line in free_output.split('\n'):
            if line.startswith('Mem:'):
                # 例如: Mem:          15Gi       1.2Gi       9.4Gi        50Mi       4.4Gi        13Gi
                parts = line.split()
                if len(parts) > 1:
                    self.host_mem_info = f"Total Memory: {parts[1]}"
                    break

        if not self.host_mem_info:
            raise Exception("Failed to get memory information")

        return self

    def _parse_build_target(self) -> str:
        pattern = r'--build-target\s+([^"\'\s]+)'
        match = re.search(pattern, self.build_command)

        if not match:
            return "all"

        target_str = match.group(1).strip()
        target_list = [item.strip() for item in target_str.split(",") if item.strip()]

        MANIFEST_PATH = Path(__file__).parent.parent.parent / ".repo" / "manifests" / "ohos" / "ohos.xml"
        if not MANIFEST_PATH.exists():
            return "all"

        name_path_dict = get_name_path_dict(MANIFEST_PATH)

        match_result, all_matched_names = approx_match_target_to_names(
            target_list=target_list,
            name_path_dict=name_path_dict,
            min_match_frags=2,  # 可调整为1（更宽松）或3（更严格）
        )
        dfx_info(f"target_list: {target_list}")
        dfx_info(f"match_result: {match_result}")

        if len(all_matched_names) == 0:
            return target_str

        return ", ".join(sorted(all_matched_names))

    def _parse_build_traces(self, log_file_path: str) -> Tuple[bool, Dict]:

        build_success = False

        result = {
            'trace_id': None,
            'events': [],
            'execution_times': {},
            'cpu_avg': 0.0,  # CPU使用率平均值
            'mem_avg_mb': 0.0  # 内存使用量平均值(MB)
        }

        # 用于计算平均值的临时变量
        cpu_values = []
        mem_values_mb = []
        mem_values_percent = []

        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        event = json.loads(line)
                        result['events'].append(event)

                        if result['trace_id'] is None and 'trace_id' in event:
                            result['trace_id'] = event['trace_id']

                        if event.get('event_name') == 'monitor_current_process':
                            if "cpu_usage" in event:
                                cpu_values.append(event.get("cpu_usage"))
                            if "memory_mb" in event:
                                mem_values_mb.append(event.get("memory_mb"))
                            if "memory_percent" in event:
                                mem_values_percent.append(event.get("memory_percent"))
                        else:
                            if event.get('status') == 'success' and 'execution_time' in event and 'event_name' in event:
                                event_name = event["event_name"]
                                if event_name == '_build_main':
                                    build_success = True
                                    self.build_start_time = event.get("start_time")
                                    self.build_end_time = event.get("end_time")
                                    self.build_time_cost = event.get("execution_time")
                                else:
                                    if event_name not in result["execution_times"]:
                                        result["execution_times"][event_name] = []
                                    result["execution_times"][event_name].append(
                                        event["execution_time"]
                                    )

                    except json.JSONDecodeError:
                        continue

            if cpu_values:
                result['cpu_avg'] = sum(cpu_values) / len(cpu_values)
            if mem_values_mb:
                result['mem_avg_mb'] = sum(mem_values_mb) / len(mem_values_mb)
            if mem_values_percent:
                result['mem_avg_percent'] = sum(mem_values_percent) / len(mem_values_percent)

            for func_name, times in result['execution_times'].items():
                if times:
                    result["execution_times"][func_name] = sum(times) / len(times)

        except FileNotFoundError:
            dfx_info(f"Warning: Log file not found: {log_file_path}")
        except Exception as e:
            dfx_info(f"Parsing build_traces log file {log_file_path} failed: {str(e)}")

        return build_success, result

    def _get_host_ip(self):
        try:
            # 使用hostname -I命令直接获取所有IPv4地址
            result = subprocess.check_output("hostname -I",
                                           shell=True,
                                           stderr=subprocess.STDOUT,
                                           universal_newlines=True).strip()

            # 提取第一个非回环地址的IP
            ip_addresses = result.split()
            if ip_addresses:
                # 优先选择第一个不是127.0.0.1的IP
                for ip in ip_addresses:
                    if not ip.startswith('127.'):
                        self.host_ip = ip
                        break
                # 如果没有找到非回环地址，使用第一个IP
                if not self.host_ip and ip_addresses:
                    self.host_ip = ip_addresses[0]
            else:
                raise Exception("Failed to get host IP address: empty result")
        except Exception as e:
            raise Exception(f"Failed to get host IP address: {str(e)}")

        return self


def get_name_path_dict(manifest_path: str) -> Optional[Dict[str, str]]:
    """读取 manifest.xml，返回 {name: path} 字典（复用稳定逻辑）"""
    try:
        tree = ET.parse(manifest_path)
        root = tree.getroot()
        name_path_dict = {}
        for project in root.findall("project"):
            project_name = project.get("name")
            project_path = project.get("path")
            if project_name and project_path:
                name_path_dict[project_name] = project_path
            else:
                missing_attr = "name" if not project_name else "path"
                dfx_info(f"警告：跳过缺失 {missing_attr} 的 project")
        return name_path_dict
    except Exception as e:
        dfx_info(f"读取 manifest 失败：{e}")
        return None


def _split_path_to_fragments(path: str) -> List[str]:
    """拆解路径为纯净的路径片段（过滤空值、.、..、文件后缀）"""
    # 分割路径（兼容 / 开头或结尾的情况）
    fragments = [f.strip() for f in path.split("/") if f.strip()]
    # 过滤无效片段（.、..）
    valid_fragments = []
    for frag in fragments:
        if frag in (".", "..", ""):
            continue
        valid_fragments.append(frag)  # 统一小写，忽略大小写
    return valid_fragments


def _calc_path_similarity(target_frags: List[str], path_frags: List[str]) -> int:
    """计算路径片段的重合度（返回公共连续片段数，核心近似匹配逻辑）"""
    max_match = 0
    # 遍历 target 片段，找与 path 片段的最长连续重合
    for i in range(len(target_frags)):
        match_count = 0
        for j in range(len(path_frags)):
            # 从 target[i] 和 path[j] 开始比对连续片段
            if target_frags[i] == path_frags[j]:
                match_count = 1
                # 继续比对后续连续片段
                k = 1
                while (i + k < len(target_frags)) and (j + k < len(path_frags)):
                    if target_frags[i + k] == path_frags[j + k]:
                        match_count += 1
                        k += 1
                    else:
                        break
                # 更新最大连续重合数
                if match_count > max_match:
                    max_match = match_count
    return max_match


def approx_match_target_to_names(
    target_list: List[str],
    name_path_dict: Dict[str, str],
    min_match_frags: int = 2,
) -> Tuple[Dict[str, List[str]], Set[str]]:
    
    match_result: Dict[str, List[str]] = {target: [] for target in target_list}
    all_matched_names: Set[str] = set()

    if not target_list:
        dfx_info("警告：target 数组为空")
        return match_result, all_matched_names

    # 预处理所有 target，拆解为路径片段（忽略文件名和后缀）
    target_frags_map = {
        target: _split_path_to_fragments(target) for target in target_list
    }

    # 遍历每个 target 进行匹配
    for target, target_frags in target_frags_map.items():
        target = target.strip()
        if not target or len(target_frags) < 1:
            continue

        # 遍历每个 project 的 path，计算路径重合度
        for name, path in name_path_dict.items():
            path_frags = _split_path_to_fragments(path)
            if len(path_frags) < 1:
                continue

            # 计算最大连续重合片段数
            max_match = _calc_path_similarity(target_frags, path_frags)

            # 达到最小重合片段数，判定为近似匹配
            if max_match >= min_match_frags:
                match_result[target].append(name)
                all_matched_names.add(name)

    return match_result, all_matched_names


def process_build_trace_log(log_dir=None, output_format='text', log_file=None):
    try:
        trace_log = BuildTraceLog()

        if log_file:
            latest_log_file = log_file
            if not os.path.exists(latest_log_file):
                dfx_info(
                    f"Warning: Specified log file does not exist: {latest_log_file}"
                )
                return None
        else:
            log_files = [os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.startswith('build_traces_') and f.endswith('.log')]
            if not log_files:
                dfx_info(
                    f"Warning: No build_traces log file found in directory {log_dir}"
                )
                return None
            latest_log_file = max(log_files, key=os.path.getmtime)
            
        dfx_info(f"Processing log file: {latest_log_file}")

        # 如果配置了上传API，执行上传
        if is_upload_configured():
            # 导入upload_build_trace_log函数
            from dfx.build_trace_uploader import upload_build_trace_log
            ret = upload_build_trace_log(log_file=latest_log_file)
            dfx_info(f"Upload build trace log: {ret.get('message', 'Success')}")
        elif output_format == 'json':
            trace_log.from_build_traces_log(latest_log_file)
            result_dict = trace_log.to_dict()
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            default_output_dir = Path(__file__).parent.parent.parent / "out" / "dfx"
            output_dir = (
                log_dir
                or (Path(log_file).parent if log_file else None)
                or default_output_dir
            )
            json_file_path = output_dir / f"build_trace_result_{timestamp}.json"
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=2, default=str)

            dfx_info(f"JSON result saved to: {json_file_path}")
            return result_dict
        else:
            # 输出文本格式
            dfx_info(trace_log)
            dfx_info("\nBuild trace log processing completed!")
            return None

    except Exception as e:
        dfx_error(f"Build trace log processing failed: {str(e)}")
        return None
    finally:
        if log_file:
            dfx_info(f"Removing log file: {log_file}")
            try:
                os.remove(latest_log_file)
            except:
                pass


# 检查是否配置了上传API
def is_upload_configured():
    # 检查环境变量
    api_url = os.environ.get('DFX_TRACE_LOG_UPLOAD_API')
    if api_url:
        return True
    
    # 检查配置文件
    try:
        config_path = Path(__file__).parent / 'dfx_config.json'
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if config.get('trace_log_upload_api'):
                    return True
    except Exception:
        pass
    
    return False


if __name__ == '__main__':
    import argparse
    
    def main():
        # 创建命令行参数解析器
        parser = argparse.ArgumentParser(description='Parse build trace log file and output build information')
        
        # 添加日志文件路径参数
        parser.add_argument('-d', '--dir', 
                            default=Path(__file__).parent.parent.parent / 'out' /'dfx',
                            help='Path to build_traces log folder (default: %(default)s)')
        
        # 添加输出格式参数
        parser.add_argument('-o', '--output', 
                            choices=['text', 'json'], 
                            default='text', 
                            help='Output format (text or json, default: %(default)s)')
        
        # 添加可选的日志文件名参数
        parser.add_argument('-f', '--file', 
                            help='Path to specific build_traces log file (default: %(default)s)')
        
        # 解析命令行参数
        args = parser.parse_args()
        
        # 调用公共方法处理日志
        process_build_trace_log(args.dir, args.output, args.file)
    
    # 调用主函数
    main()
