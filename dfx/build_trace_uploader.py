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

import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from dfx.build_trace_log import BuildTraceLog
from dfx import dfx_info, dfx_error

CODE_ROOT = Path(__file__).parent.parent.parent
# 将 os.path.join 替换为 pathlib 的 / 操作符
third_party_path = str(CODE_ROOT / "third_party")
sys.path.insert(1, third_party_path)

try:

    from jinja2 import Template, FileSystemLoader, Environment, exceptions
    JINJA2_AVAILABLE = True
except ImportError:
    dfx_info("Warning: Jinja2 library not found. Template support will be disabled.")
    JINJA2_AVAILABLE = False

while third_party_path in sys.path:
    sys.path.remove(third_party_path)



class TraceLogUploader:

    def __init__(self):
        # 设置默认配置文件路径
        self.config_file = os.path.join(os.path.dirname(__file__), "dfx_config.json")
        self.upload_api_url = None
        self.timeout = 30  # 默认超时时间为30秒
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.template_file = os.path.join(os.path.dirname(__file__), "trace_log_request.template")
        self.extra_header_fields = None
        self.extra_header_values = None
        self._load_config()

    def upload_trace_log_from_file(self, log_file_path: str) -> Dict[str, Any]:
        try:
            # 检查文件是否存在
            # 将 os.path.exists 替换为 Path.exists()
            if not Path(log_file_path).exists():
                return {
                    "success": False,
                    "message": f"Log file not found: {log_file_path}",
                }

            # 创建BuildTraceLog对象并解析日志文件
            trace_log = BuildTraceLog()
            flag = trace_log.from_build_traces_log(log_file_path)
            
            if flag:
                return self.upload_trace_log(trace_log)
            else:
                return {
                    "success": False,
                    "message": f"Failed to parse log file: {log_file_path}",
                }

        except Exception as e:
            error_msg = f"Failed to process log file: {str(e)}"
            dfx_error(error_msg)
            return {"success": False, "message": error_msg}

    def upload_trace_log(self, trace_log: BuildTraceLog) -> Dict[str, Any]:
        # 检查上传API是否配置
        if not self.upload_api_url:
            return {
                "success": False,
                "message": "Upload API URL is not configured in dfx_config.json or environment variable DFX_TRACE_LOG_UPLOAD_API",
            }

        try:
            # 准备额外请求头
            self._prepare_extra_headers()
            # 准备请求体
            request_body = self._prepare_request_body(trace_log)
            dfx_info(f"Preparing to upload trace log data to {self.upload_api_url}")
            dfx_info(f"Request body: {request_body}")
            # 记录是否使用了模板
            if self.request_template:
                dfx_info(f"Using template {self.template_file} for request body")
            else:
                dfx_info("Using default request body structure")

            import requests
            # 发送POST请求
            response = requests.post(
                self.upload_api_url,
                headers=self.headers,
                json=request_body,
                timeout=self.timeout,
            )


            # 解析响应结果
            result = response.json()
            if result.get("code") == 200:
                return {
                    "success": True,
                    "message": "Trace log uploaded successfully",
                    "response": result,
                }
            else:
                return {
                    "success": False,
                    "message": f"Upload failed: {result.get('data', 'Unknown error')}",
                    "response": result,
                }

        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            dfx_error(error_msg)
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"Upload failed: {str(e)}"
            dfx_error(error_msg)
            return {"success": False, "message": error_msg}

    def _load_config(self):
        """加载配置文件，如果配置文件中没有配置，则从环境变量中读取"""
        config_file_loaded = False
        try:
            # 首先尝试从配置文件加载
            if Path(self.config_file).exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.upload_api_url = config.get("trace_log_upload_api", "")
                    self.extra_header_fields = config.get("extra_request_header_fields", None)
                    self.extra_header_values = config.get("extra_request_header_values", None)
                config_file_loaded = True
            else:
                dfx_info(f"Warning: Config file not found: {self.config_file}")
        except Exception as e:
            dfx_error(f"Error loading config file: {str(e)}")

        # 如果配置文件中没有配置upload_api_url，则尝试从环境变量读取
        if not self.upload_api_url or not config_file_loaded:
            env_upload_api = os.environ.get("DFX_TRACE_LOG_UPLOAD_API", "")
            if env_upload_api:
                self.upload_api_url = env_upload_api
                dfx_info(f"Loaded upload API URL from environment variable")

        # 如果配置文件中没有配置额外请求头，则尝试从环境变量读取
        if (not self.extra_header_fields or not self.extra_header_values) or not config_file_loaded:
            env_header_fields = os.environ.get("DFX_EXTRA_REQUEST_HEADER_FIELDS", None)
            env_header_values = os.environ.get("DFX_EXTRA_REQUEST_HEADER_VALUES", None)
            if env_header_fields and env_header_values:
                self.extra_header_fields = env_header_fields
                self.extra_header_values = env_header_values
                dfx_info(f"Loaded extra request headers from environment variables")

    def _load_template(self):
        # 如果Jinja2库不可用，则不使用模板
        if not JINJA2_AVAILABLE:
            dfx_info(
                "Jinja2 library not available, will use default request body structure."
            )
            self.request_template = None
            return

        # 如果没有指定模板文件，则不使用模板
        if not self.template_file:
            dfx_info(
                "No template file specified, will use default request body structure."
            )
            self.request_template = None
            return

        try:
            # 检查模板文件是否存在
            # 将 os.path.exists 替换为 Path.exists()
            if not Path(self.template_file).exists():
                dfx_info(f"Warning: Template file not found: {self.template_file}")
                self.request_template = None
                return

            # 创建Jinja2环境并加载模板
            # 将 os.path.dirname 和 os.path.basename 替换为 pathlib 的相应方法
            template_path = Path(self.template_file)
            template_dir = str(template_path.parent)
            template_name = template_path.name
            env = Environment(loader=FileSystemLoader(template_dir))
            self.request_template = env.get_template(template_name)
            dfx_info(f"Successfully loaded template: {self.template_file}")
        except Exception as e:
            dfx_error(f"Error loading template: {str(e)}")
            self.request_template = None

    def _prepare_extra_headers(self):
        """解析并添加额外的请求头信息"""
        if not self.extra_header_fields or not self.extra_header_values:
            return

        try:
            # 解析字段和值，使用|分隔
            fields = [field.strip() for field in self.extra_header_fields.split('|')]
            values = [value.strip() for value in self.extra_header_values.split('|')]

            # 确保字段和值的数量匹配
            if len(fields) != len(values):
                dfx_info(f"Warning: Number of header fields ({len(fields)}) does not match number of values ({len(values)})")
                return

            # 添加到请求头
            for field, value in zip(fields, values):
                if field:
                    self.headers[field] = value
                    dfx_info(f"Added extra header: {field} = {value}")
        except Exception as e:
            dfx_error(f"Error parsing extra headers: {str(e)}")

    def _prepare_request_body(self, trace_log: BuildTraceLog) -> Dict[str, Any]:
        # 使用BuildTraceLog的to_dict方法获取基础数据
        trace_data = trace_log.to_dict()

        # 检查是否配置了模板，如果有则加载模板并使用模板渲染
        if self.template_file:
            # 加载模板
            self._load_template()
            # 如果模板加载成功，则使用模板渲染
            if self.request_template:
                try:
                    # 准备模板数据
                    template_data = {
                        **trace_data,
                        "upload_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    # 渲染模板获取JSON字符串
                    rendered_json = self.request_template.render(**template_data)
                    # 解析为字典返回
                    return json.loads(rendered_json, strict=False)
                except Exception as e:
                    dfx_error(f"Error rendering template: {str(e)}")
                    dfx_error("Falling back to default request body structure")

        # 如果未配置模板或模板渲染失败，则使用默认请求体结构
        request_body = {
            "trace_info": {
                "user_info": {
                    "user_id": trace_data.get("user_id"),
                    "git_user_email": trace_data.get("git_user_email"),
                    "code_repo": trace_data.get("code_repo"),
                    "user_source": trace_data.get("user_source"),
                },
                "host_info": {
                    "cpu_info": trace_data.get("host_cpu_info"),
                    "mem_info": trace_data.get("host_mem_info"),
                    "ip": trace_data.get("host_ip"),
                },
                "build_time_info": {
                    "start_time": trace_data.get("build_start_time"),
                    "end_time": trace_data.get("build_end_time"),
                    "trace_id": trace_data.get("build_trace_id"),
                },
                "build_config_info": {
                    "build_type": trace_data.get("build_type"),
                    "build_args": trace_data.get("build_args"),
                    "product_type": trace_data.get("build_product_type"),
                },
                "resource_usage": {
                    "cpu_usage": trace_data.get("build_cpu_usage"),
                    "mem_usage_mb": trace_data.get("build_mem_usage"),
                    "total_time_cost": trace_data.get("build_time_cost"),
                    "time_cost_detail": trace_data.get("build_time_cost_detail"),
                },
                "build_result": {
                    "result": trace_data.get("build_result"),
                    "error_log": trace_data.get("build_error_log"),
                },
                "upload_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        }

        return request_body


def upload_build_trace_log(
    log_file: Optional[str] = None,
    log_dir: Optional[str] = None,
) -> Dict[str, Any]:
    try:
        # 创建上传器实例
        uploader = TraceLogUploader()
        _parsed_log_file = None
        # 确定要上传的日志文件
        if log_file:
            # 上传指定的日志文件
            _parsed_log_file = log_file

        elif log_dir:
            # 在日志目录中查找最新的构建跟踪日志文件
            # 将 os.path.join 替换为 pathlib 的 / 操作符
            log_dir_path = Path(log_dir)
            log_files = [
                str(log_dir_path / f)
                for f in os.listdir(log_dir)
                if f.startswith("build_traces_") and f.endswith(".log")
            ]

            if not log_files:
                return {
                    "success": False,
                    "message": f"No build_traces log file found in directory {log_dir}",
                }

            # 获取最新的日志文件
            # 将 os.path.getctime 替换为 Path.stat().st_ctime
            _parsed_log_file = max(log_files, key=lambda x: Path(x).stat().st_ctime)
            dfx_info(f"Uploading latest log file: {_parsed_log_file}")
        else:
            # 使用默认日志目录
            default_log_dir = Path(__file__).parent.parent.parent / "out" / "dfx"
            return upload_build_trace_log(log_dir=str(default_log_dir))

        return uploader.upload_trace_log_from_file(_parsed_log_file)

    except Exception as e:
        error_msg = f"Upload process failed: {str(e)}"
        dfx_error(error_msg)
        return {"success": False, "message": error_msg}


if __name__ == "__main__":
    import argparse

    def main():
        # 创建命令行参数解析器
        parser = argparse.ArgumentParser(description="Upload build trace log data")

        # 添加日志文件路径参数
        parser.add_argument(
            "-f", "--file", help="Path to specific build_traces log file"
        )

        # 添加日志目录路径参数
        parser.add_argument("-d", "--dir", help="Path to build_traces log folder")

        # 解析命令行参数
        args = parser.parse_args()

        # 调用上传函数
        result = upload_build_trace_log(
            log_file=args.file, log_dir=args.dir
        )

        # 输出结果
        dfx_info(f"Upload result: {json.dumps(result, ensure_ascii=False, indent=2)}")

        # 根据结果设置退出码
        exit(0 if result.get("success") else 1)

    # 调用主函数
    main()
