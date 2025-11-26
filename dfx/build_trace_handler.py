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

import json
import os
import queue
import threading
import time
import atexit
from typing import Any, Dict, Optional
from pathlib import Path
from dfx.build_trace_log import process_build_trace_log
from dfx import dfx_info


class AsyncTraceHandler:

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(AsyncTraceHandler, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, log_file_path: Path, max_queue_size: int = 1000):
        if not self._initialized:
            log_dir = os.path.dirname(log_file_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            self.log_file_path = log_file_path
            self.queue = queue.Queue(maxsize=max_queue_size)
            self._stop_event = threading.Event()

            self.worker_thread = threading.Thread(target=self._worker, daemon=True)
            self.worker_thread.start()
            self._initialized = True

    @classmethod
    def get_instance(cls, log_file_path: Path):
        if cls._instance is None:
            cls._instance = cls(log_file_path)
        return cls._instance

    def _worker(self) -> None:
        try:
            with open(self.log_file_path, 'a', encoding='utf-8') as log_file:
                while not self._stop_event.is_set() or not self.queue.empty():
                    try:
                        log_data = self.queue.get(timeout=0.1)
                        try:
                            log_line = json.dumps(log_data, ensure_ascii=False)
                            log_file.write(f"{log_line}\n")
                            log_file.flush()
                        except Exception as e:
                            error_msg = {
                                "timestamp": time.time(),
                                "error": f"Failed to write log: {str(e)}",
                                "original_data": str(log_data)
                            }
                            log_file.write(f"{json.dumps(error_msg)}\n")
                            log_file.flush()
                        finally:
                            self.queue.task_done()
                    except queue.Empty:
                        continue
        except Exception as e:
            dfx_info(f"Async log worker failed: {str(e)}")

    def event_handler(self, data: Dict[str, Any]) -> None:
        try:
            try:
                self.queue.put(data, block=False)
            except queue.Full:
                try:
                    self.queue.put(data, block=True, timeout=0.1)
                except queue.Full:
                    dfx_info(f"Warning: Log queue is full, dropping log data: {data}")
        except Exception as e:
            dfx_info(f"Error: Failed to queue log data: {str(e)}")

    def shutdown(self, wait: bool = True, timeout: Optional[float] = None) -> None:
        self._stop_event.set()

        if wait:
            try:
                self.queue.join()
            except Exception:
                pass

        if self.worker_thread.is_alive():
            self.worker_thread.join(timeout=timeout)


# Exposed event_handler function
def event_handler(data: Dict[str, Any], trace_log_file: Path) -> None:
    _default_handler = AsyncTraceHandler(trace_log_file)
    _default_handler.event_handler(data)


# Shutdown log handler when program exits
def _shutdown_handler():
    try:
        if AsyncTraceHandler._instance:
            # 直接调用process_build_trace_log，它现在会内部处理上传或本地保存的逻辑
            process_build_trace_log(log_file=AsyncTraceHandler._instance.log_file_path)
            AsyncTraceHandler._instance.shutdown()
    except Exception:
        pass

atexit.register(_shutdown_handler)