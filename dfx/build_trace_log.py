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
        # User related information
        self.user_id = None                  # User ID
        self.git_user_email = None           # Git user email
        self.code_repo = None                # Code repository
        self.user_source = None              # User source

        # Host information
        self.host_cpu_info = None            # Host CPU information
        self.host_mem_info = None            # Host memory information
        self.host_ip = None                  # Host IP address

        # Build time information
        self.build_start_time = None         # Build start time
        self.build_end_time = None           # Build end time
        self.build_trace_id = None           # Build trace ID

        # Build configuration information
        self.build_type = None               # Build type
        self.build_args = None            # Build arguments
        self.build_target = None           # Build target
        self.build_command = None          # Build command
        self.build_product_type = None       # Build product type

        # Build resource usage
        self.build_cpu_usage = None          # Average CPU usage during build
        self.build_mem_usage = None          # Average memory usage during build (MB)
        self.build_time_cost = None          # Build time cost
        self.build_time_cost_detail = None   # Detailed build time cost

        # Build result information
        self.build_result = None             # Build result
        self.build_error_log = None          # Build error log
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
        """Convert TraceLog object to dictionary format"""
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
            # Parse log file
            build_success_flag, parsed_data = self._parse_build_traces(log_file_path)

            if not build_success_flag:
                dfx_info(
                    f"Build failed, stop parsing build_traces log file {log_file_path}"
                )
                if log_file_path:
                    os.remove(log_file_path)
                return False

            # Fill basic information
            if parsed_data['trace_id']:
                self.build_trace_id = parsed_data['trace_id']

            # Extract build start and end times
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

            # Extract build resource usage - keep average values only
            self.build_cpu_usage = parsed_data['cpu_avg']
            self.build_mem_usage = parsed_data['mem_avg_mb']

            # Extract detailed execution times for each function
            self.build_time_cost_detail = parsed_data['execution_times']

            # Determine build result (assume build failed if there are error events)
            has_error = any(event.get("status") == "failed" for event in events)
            self.build_result = 'success' if not has_error else 'failed'

            # Extract error information if there are error events
            if has_error:
                error_events = [event for event in events if event.get("status") == "failed"]
                self.build_error_log = json.dumps(error_events, ensure_ascii=False, default=str)

            # Extract build configuration information from args_info
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
                        # Try to parse args_info
                        self.build_args = (
                            json.loads(event["args_info"])
                            if isinstance(event["args_info"], str)
                            else event["args_info"]
                        )

                        # Extract build product type
                        if "product_name" in self.build_args[0] and not self.build_product_type:
                            self.build_product_type = self.build_args[0][
                                "product_name"
                            ].replace("product_name=", "")

                    except (json.JSONDecodeError, TypeError):
                        continue
                
                if "build_type" in event and not self.build_type:
                    self.build_type = event["build_type"]
                
                # Exit early if required information has been extracted
                if self.build_type and self.build_product_type and self.build_command and self.build_target:
                    break

        except Exception as e:
            dfx_info(f"Failed to parse build_traces log file {log_file_path}: {str(e)}")
            # Set error log
            self.build_error_log = str(e)
            self.build_result = 'failed'
            return False

        return True

    def _get_user_info_from_git(self):
        # Get git username (user.name) as user_id
        user_name = subprocess.check_output(['git', 'config', 'user.name'], 
                                         stderr=subprocess.STDOUT, 
                                         universal_newlines=True).strip()
        self.user_id = user_name

        # Get git user email
        email = subprocess.check_output(['git', 'config', 'user.email'], 
                                      stderr=subprocess.STDOUT, 
                                      universal_newlines=True).strip()
        self.git_user_email = email

        return self

    def _get_code_repo(self):
        # Get repository information using repo info | grep "Manifest branch" command
        # Use shell=True to support pipe commands
        result = subprocess.check_output('repo info -o | grep "Manifest branch"', 
                                       shell=True, 
                                       stderr=subprocess.STDOUT, 
                                       universal_newlines=True).strip()

        # Extract Manifest branch information
        if result:
            # Example: Manifest branch: refs/heads/master
            self.code_repo = result
        else:
            raise Exception("Failed to get Manifest branch information: empty result")
        return self

    def _get_cpu_info(self):
        # Get CPU model
        cpu_model = subprocess.check_output("cat /proc/cpuinfo | grep 'model name' | head -n 1 | cut -d: -f2 | tr -s ' '",
                                          shell=True,
                                          stderr=subprocess.STDOUT,
                                          universal_newlines=True).strip()

        # Get CPU core count
        cpu_cores = subprocess.check_output("nproc",
                                          shell=True,
                                          stderr=subprocess.STDOUT,
                                          universal_newlines=True).strip()

        self.host_cpu_info = f"CPU Model: {cpu_model}, Cores: {cpu_cores}"
        return self

    def _get_memory_info(self):
        # Get memory information using free command
        free_output = subprocess.check_output("free -h",
                                            shell=True,
                                            stderr=subprocess.STDOUT,
                                            universal_newlines=True)

        # Parse total memory information
        for line in free_output.split('\n'):
            if line.startswith('Mem:'):
                # Example: Mem:          15Gi       1.2Gi       9.4Gi        50Mi       4.4Gi        13Gi
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
            min_match_frags=2,  # Can be adjusted to 1 (more lenient) or 3 (stricter)
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
            'cpu_avg': 0.0,  # CPU usage average
            'mem_avg_mb': 0.0  # Memory usage average (MB)
        }

        # Temporary variables for calculating averages
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
            # Use hostname -I command to directly get all IPv4 addresses
            result = subprocess.check_output("hostname -I",
                                           shell=True,
                                           stderr=subprocess.STDOUT,
                                           universal_newlines=True).strip()

            # Extract first non-loopback IP address
            ip_addresses = result.split()
            if ip_addresses:
                # Prefer first IP that is not 127.0.0.1
                for ip in ip_addresses:
                    if not ip.startswith('127.'):
                        self.host_ip = ip
                        break
                # If no non-loopback address found, use first IP
                if not self.host_ip and ip_addresses:
                    self.host_ip = ip_addresses[0]
            else:
                raise Exception("Failed to get host IP address: empty result")
        except Exception as e:
            raise Exception(f"Failed to get host IP address: {str(e)}")

        return self


def get_name_path_dict(manifest_path: str) -> Optional[Dict[str, str]]:
    """Read manifest.xml and return {name: path} dictionary (reuse stable logic)"""
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
                dfx_info(f"Warning: Skipping project missing {missing_attr}")
        return name_path_dict
    except Exception as e:
        dfx_info(f"Failed to read manifest: {e}")
        return None


def _split_path_to_fragments(path: str) -> List[str]:
    """Split path into clean path fragments (filter empty values, ., .., file extensions)"""
    # Split path (compatible with / at beginning or end)
    fragments = [f.strip() for f in path.split("/") if f.strip()]
    # Filter invalid fragments (., ..)
    valid_fragments = []
    for frag in fragments:
        if frag in (".", "..", ""):
            continue
        valid_fragments.append(frag)  # Convert to lowercase, ignore case
    return valid_fragments


def _calc_path_similarity(target_frags: List[str], path_frags: List[str]) -> int:
    """Calculate path fragment overlap (returns common consecutive fragment count, core approximate matching logic)"""
    max_match = 0
    # Iterate through target fragments to find longest consecutive overlap with path fragments
    for i, target_frag in enumerate(target_frags):
        match_count = 0
        for j, path_frag in enumerate(path_frags):
            # Start comparing consecutive fragments from target[i] and path[j]
            if target_frag == path_frag:
                match_count = 1
                # Continue comparing subsequent consecutive fragments
                k = 1
                while (i + k < len(target_frags)) and (j + k < len(path_frags)):
                    if target_frags[i + k] == path_frags[j + k]:
                        match_count += 1
                        k += 1
                    else:
                        break
                # Update maximum consecutive overlap count
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
        dfx_info("Warning: target array is empty")
        return match_result, all_matched_names

    # Preprocess all targets, split into path fragments (ignore filenames and extensions)
    target_frags_map = {
        target: _split_path_to_fragments(target) for target in target_list
    }

    # Iterate through each target for matching
    for target, target_frags in target_frags_map.items():
        target = target.strip()
        if not target or len(target_frags) < 1:
            continue

        # Iterate through each project's path, calculate path overlap
        for name, path in name_path_dict.items():
            path_frags = _split_path_to_fragments(path)
            if len(path_frags) < 1:
                continue

            # Calculate maximum consecutive fragment overlap
            max_match = _calc_path_similarity(target_frags, path_frags)

            # Reached minimum fragment overlap, determine as approximate match
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

        # If upload API is configured, perform upload
        if is_upload_configured():
            # Import upload_build_trace_log function
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
            # Output text format
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


# Check if upload API is configured
def is_upload_configured():
    from .dfx_config_manager import get_config_manager

    try:
        config_manager = get_config_manager()
        api_url = config_manager.trace_log_upload_api
        return bool(api_url)
    except Exception:
        return False


if __name__ == '__main__':
    import argparse
    
    def main():
        # Create command line argument parser
        parser = argparse.ArgumentParser(description='Parse build trace log file and output build information')

        # Add log file path parameter
        parser.add_argument('-d', '--dir',
                            default=Path(__file__).parent.parent.parent / 'out' /'dfx',
                            help='Path to build_traces log folder (default: %(default)s)')

        # Add output format parameter
        parser.add_argument('-o', '--output',
                            choices=['text', 'json'],
                            default='text',
                            help='Output format (text or json, default: %(default)s)')

        # Add optional log file name parameter
        parser.add_argument('-f', '--file',
                            help='Path to specific build_traces log file (default: %(default)s)')

        # Parse command line arguments
        args = parser.parse_args()

        # Call common method to process logs
        process_build_trace_log(args.dir, args.output, args.file)

    # Call main function
    main()
