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

import functools
import json
import time
import random
import threading
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Callable, Any, Optional, Dict
from dfx.build_trace_handler import event_handler
from dfx import dfx_info, dfx_error
import argparse


class BuildTracker:

    _instance = None
    event_handler = event_handler
    config_path = os.path.join(os.path.dirname(__file__), "dfx_config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                TRACE_LOG_DIR = config.get("trace_log_dir",  os.environ.get('TRACE_LOG_DIR', 'out/dfx'))
                BUILD_DFX_ENABLE = config.get("build_dfx_enable")
                if BUILD_DFX_ENABLE in (None, ""):
                    BUILD_DFX_ENABLE = os.environ.get("BUILD_DFX_ENABLE", "").lower() == "true"
        except Exception as e:
            dfx_error(f"Error loading config file: {e}")
            TRACE_LOG_DIR = None
            BUILD_DFX_ENABLE = os.environ.get("BUILD_DFX_ENABLE", "").lower() == "true"
        base_path = Path(__file__).parent.parent.parent
        if TRACE_LOG_DIR:
            trace_log_dir_path = Path(TRACE_LOG_DIR)
            if trace_log_dir_path.is_absolute():
                log_dir = trace_log_dir_path
            else:
                log_dir = base_path / TRACE_LOG_DIR
        else:
            log_dir = base_path / "out" / "dfx"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        BUILD_TRACE_LOG_DIR = log_dir

    def __new__(cls, build_type=""):
        if cls._instance is None:
            cls._instance = super(BuildTracker, cls).__new__(cls)
            cls._instance._initialized = False
            cls._instance._build_type = build_type  # 存储build_type
        else:
            # 如果实例已存在但build_type不同，更新build_type
            cls._instance._build_type = build_type
        return cls._instance

    def __init__(self, build_type=""):
        if not self._initialized:
            self.trace_id = self.generate_trace_id()
            self.trace_log_file = (
                BuildTracker.BUILD_TRACE_LOG_DIR / f"build_traces_{self.trace_id}.log"
            )
            self._initialized = True
            # 只有当 build_type 为 "build" 时才创建并启动监控线程
            if build_type == "build":
                self._monitor_thread = threading.Thread(
                    target=self.monitor_current_process, args=(self.trace_id, self.trace_log_file, 15), daemon=True
                )
                self._monitor_thread.start()
            else:
                self._monitor_thread = None

    @classmethod
    def get_instance(cls, build_type=""):
        if cls._instance is None:
            cls._instance = cls(build_type)
        return cls._instance

    def generate_trace_id(self):
        timestamp_part = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
        random_part = str(random.randint(100, 999))
        return f"{timestamp_part}{random_part}"

    def monitor_current_process(self, trace_id="", trace_log_file=None, interval=2):
        import psutil

        pid = os.getpid()
        process = psutil.Process(pid)
        try:
            while True:
                cpu_usage = psutil.cpu_percent(interval=10, percpu=False)
                memory_info = process.memory_info()
                memory_percent = psutil.virtual_memory().percent
                memory_usage = memory_info.rss / (1024 * 1024)
                tracking_data = {
                    "trace_id": trace_id,
                    "event_name": "monitor_current_process",
                    "cpu_usage": cpu_usage,
                    "memory_mb": memory_usage,
                    "memory_percent": memory_percent,
                    "start_time": time.time(),
                }
                BuildTracker._record_tracking_event(tracking_data=tracking_data, trace_log_file=trace_log_file)
                time.sleep(interval)
        except Exception as e:
            raise Exception(f"Current process monitor thread error: {str(e)}")

    @classmethod
    def get_instance(cls, build_type=""):
        if cls._instance is None:
            cls._instance = cls(build_type)
        return cls._instance

    @staticmethod
    def _record_tracking_event(
        tracking_data: Dict,
        trace_log_file=None
    ):
        try:
            event_handler(tracking_data, trace_log_file)
        except Exception as e:
            dfx_error(f"Error recording tracking event: {str(e)}")

    @staticmethod
    def args_info_parse(args, args_key=None):
        args_list = []
        if isinstance(args, tuple):
            for arg in args:
                if args_key and hasattr(arg, args_key):
                    args_list.append(getattr(arg, args_key))
                    break
                elif isinstance(arg, argparse.Namespace):
                    args_list.append(vars(arg))
                    break
                else:
                    args_list.append(arg)
                    break
        else:
            args_list.append(args)
        dfx_info(args_list)
        args_info = (
            json.dumps(
                args_list,
                default=str,
                ensure_ascii=False,
            )
            if args_list
            else str(args)
        )
        return args_info

    @staticmethod
    def check_build_status(tracking_data: Dict, event_name: str, build_type: str, result: Any) -> Dict:
        tracking_data["status"] = "success"
        if event_name == "_build_main" and build_type == "build":
            if result != 0:
                tracking_data["status"] = "failed"
                tracking_data["error_message"] = f"Build failed with exit code {result}"
        return tracking_data
    
    @staticmethod
    def build_tracker(
        event_name: str,
        build_type: str,
        args_key: Optional[str] = None,
    ):
        def decorator(func: Callable) -> Callable:
            if not BuildTracker.BUILD_DFX_ENABLE:
                return func

            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                # 获取实例时传入build_type
                tracker = BuildTracker.get_instance(build_type)
                start_time = time.time()

                tracking_data = {
                    "trace_id": tracker.trace_id,
                    "event_name": event_name,
                    "function": func.__name__,
                    "start_time": start_time,
                    "build_type": build_type
                }

                args_info = BuildTracker.args_info_parse(args, args_key)
                tracking_data["args_info"] = args_info
                args_list = sys.argv[2:] if len(sys.argv) > 2 else []
                tracking_data["raw_args"] = args_list

                try:
                    result = func(*args, **kwargs)
                    # 使用新方法检查构建状态
                    tracking_data = BuildTracker.check_build_status(tracking_data, event_name, build_type, result)
                    return result
                except Exception as e:
                    tracking_data["status"] = "failed"
                    tracking_data["error_message"] = str(e)
                    raise e
                finally:
                    tracking_data["end_time"] = time.time()
                    tracking_data["execution_time"] = tracking_data["end_time"] - tracking_data["start_time"]
                    BuildTracker._record_tracking_event(tracking_data=tracking_data, trace_log_file=tracker.trace_log_file)

            return wrapper

        return decorator


def build_tracker(
    event_name: str,
    build_type: str,
    args_key: Optional[str] = None,
):
    return BuildTracker.build_tracker(
        event_name, build_type, args_key
    )