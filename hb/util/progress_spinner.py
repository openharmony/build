#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) 2026 Huawei Device Co., Ltd.
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

import sys
import time
import itertools
from functools import wraps
from multiprocessing import Process, Event

def _spinner_worker(stop_event, message):
    """
    Independent worker function for the spinner process.
    This runs in a separate process with its own GIL.
    """
    frames = itertools.cycle(['|', '/', '-', '\\'])
    try:
        while not stop_event.is_set():
            # \033[K clears the line from the cursor to the end
            sys.stdout.write(f"\r{message} {next(frames)}\033[K")
            sys.stdout.flush()
            time.sleep(0.08)
    finally:
        # Final cleanup: clear the line before exiting the process
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()


def _cleanup_spinner_process(p, stop_event):
    stop_event.set()
    p.join(timeout=0.5)
    if p.is_alive():
        p.terminate()


def progress_spinner(message="Process..."):
    """
    A multiprocess-based spinner decorator to prevent stuttering
    during CPU-intensive tasks.
    Only shows progress when output is to a terminal.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if output is to a terminal (not redirected to file)
            is_terminal = sys.stdout.isatty()

            # If not terminal, just execute function without spinner
            if not is_terminal:
                return func(*args, **kwargs)

            # Event for inter-process communication
            stop_event = Event()

            # Initialize the spinner process
            # Using a separate process bypasses the GIL limitations
            p = Process(target=_spinner_worker, args=(stop_event, message))
            p.daemon = True
            p.start()

            try:
                # Execute the heavy function in the main process
                return func(*args, **kwargs)
            finally:
                # Signal the process to stop and wait for cleanup
                _cleanup_spinner_process(p, stop_event)
        return wrapper
    return decorator
