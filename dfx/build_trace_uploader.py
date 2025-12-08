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
from dfx.dfx_config_manager import get_config_manager
from .crypto_utils import create_crypto_utils_from_config

CODE_ROOT = Path(__file__).parent.parent.parent
# Replace os.path.join with pathlib's / operator
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
        # Set default configuration file path
        self.config_file = os.path.join(os.path.dirname(__file__), "dfx_config.json")
        self.upload_api_url = None
        self.timeout = 30  # Default timeout is 30 seconds
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.template_file = os.path.join(os.path.dirname(__file__), "trace_log_request.template")
        self.extra_header_fields = None
        self.extra_header_values = None
        self.crypto_utils = None
        self._load_config()

    def upload_trace_log_from_file(self, log_file_path: str) -> Dict[str, Any]:
        try:
            # Check if file exists
            # Replace os.path.exists with Path.exists()
            if not Path(log_file_path).exists():
                return {
                    "success": False,
                    "message": f"Log file not found: {log_file_path}",
                }

            # Create BuildTraceLog object and parse log file
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
        # Check if upload API is configured
        if not self.upload_api_url:
            return {
                "success": False,
                "message": "Upload API URL is not configured in dfx_config.json or environment variable DFX_TRACE_LOG_UPLOAD_API",
            }

        try:
            # Prepare extra request headers
            self._prepare_extra_headers()
            # Prepare request body
            request_body = self._prepare_request_body(trace_log)
            dfx_info(f"Preparing to upload trace log data to {self.upload_api_url}")
            dfx_info(f"Request body: {request_body}")
            # Record whether template was used
            if self.request_template:
                dfx_info(f"Using template {self.template_file} for request body")
            else:
                dfx_info("Using default request body structure")

            import requests
            # Send POST request
            response = requests.post(
                self.upload_api_url,
                headers=self.headers,
                json=request_body,
                timeout=self.timeout,
            )


            # Parse response result
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
        """Load configuration using DFXConfigManager"""
        try:
            # Use DFXConfigManager to get configuration
            config_manager = get_config_manager()

            # Get upload API URL
            self.upload_api_url = config_manager.trace_log_upload_api

            # Load configuration for crypto utils
            config_for_crypto = {
                "extra_request_header_fields_encrypted": config_manager.extra_request_header_fields_encrypted,
                "extra_request_header_encryption_key": config_manager.extra_request_header_encryption_key,
            }
            self.crypto_utils = create_crypto_utils_from_config(config_for_crypto)

            # Get header fields and values
            raw_header_fields = config_manager.extra_request_header_fields
            raw_header_values = config_manager.extra_request_header_values

            if self.crypto_utils and config_manager.extra_request_header_fields_encrypted:
                self.extra_header_fields, self.extra_header_values = \
                    self.crypto_utils.decrypt_headers(raw_header_fields, raw_header_values)
                dfx_info("Request headers decrypted")
            else:
                self.extra_header_fields = raw_header_fields
                self.extra_header_values = raw_header_values

            dfx_info("Configuration loaded using DFXConfigManager")

        except Exception as e:
            dfx_error(f"Error loading configuration: {str(e)}")
            # Set default values
            self.upload_api_url = ""
            self.extra_header_fields = None
            self.extra_header_values = None
            self.crypto_utils = None

    def _load_template(self):
        # If Jinja2 library is not available, don't use template
        if not JINJA2_AVAILABLE:
            dfx_info(
                "Jinja2 library not available, will use default request body structure."
            )
            self.request_template = None
            return

        # If no template file specified, don't use template
        if not self.template_file:
            dfx_info(
                "No template file specified, will use default request body structure."
            )
            self.request_template = None
            return

        try:
            # Check if template file exists
            # Replace os.path.exists with Path.exists()
            if not Path(self.template_file).exists():
                dfx_info(f"Warning: Template file not found: {self.template_file}")
                self.request_template = None
                return

            # Create Jinja2 environment and load template
            # Replace os.path.dirname and os.path.basename with pathlib's corresponding methods
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
        """Parse and add extra request header information"""
        if not self.extra_header_fields or not self.extra_header_values:
            return

        try:
            # Parse fields and values, use | as separator
            fields = [field.strip() for field in self.extra_header_fields.split('|')]
            values = [value.strip() for value in self.extra_header_values.split('|')]

            # Ensure number of fields matches number of values
            if len(fields) != len(values):
                dfx_info(f"Warning: Number of header fields ({len(fields)}) does not match number of values ({len(values)})")
                return

            # Add to request headers
            for field, value in zip(fields, values):
                if field:
                    self.headers[field] = value
                    dfx_info(f"Added extra header: {field} = {value}")
        except Exception as e:
            dfx_error(f"Error parsing extra headers: {str(e)}")

    def _prepare_request_body(self, trace_log: BuildTraceLog) -> Dict[str, Any]:
        # Use BuildTraceLog's to_dict method to get base data
        trace_data = trace_log.to_dict()

        # Check if template is configured, if yes load template and use template rendering
        if self.template_file:
            # Load template
            self._load_template()
            # If template loaded successfully, use template rendering
            if self.request_template:
                try:
                    # Prepare template data
                    template_data = {
                        **trace_data,
                        "upload_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    # Render template to get JSON string
                    rendered_json = self.request_template.render(**template_data)
                    # Parse and return as dictionary
                    return json.loads(rendered_json, strict=False)
                except Exception as e:
                    dfx_error(f"Error rendering template: {str(e)}")
                    dfx_error("Falling back to default request body structure")

        # If template not configured or template rendering failed, use default request body structure
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
        # Create uploader instance
        uploader = TraceLogUploader()
        _parsed_log_file = None
        # Determine log file to upload
        if log_file:
            # Upload specified log file
            _parsed_log_file = log_file

        elif log_dir:
            # Find latest build trace log file in log directory
            # Replace os.path.join with pathlib's / operator
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

            # Get latest log file
            # Replace os.path.getctime with Path.stat().st_ctime
            _parsed_log_file = max(log_files, key=lambda x: Path(x).stat().st_ctime)
            dfx_info(f"Uploading latest log file: {_parsed_log_file}")
        else:
            # Use default log directory
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
        # Create command line argument parser
        parser = argparse.ArgumentParser(description="Upload build trace log data")

        # Add log file path parameter
        parser.add_argument(
            "-f", "--file", help="Path to specific build_traces log file"
        )

        # Add log directory path parameter
        parser.add_argument("-d", "--dir", help="Path to build_traces log folder")

        # Parse command line arguments
        args = parser.parse_args()

        # Call upload function
        result = upload_build_trace_log(
            log_file=args.file, log_dir=args.dir
        )

        # Output result
        dfx_info(f"Upload result: {json.dumps(result, ensure_ascii=False, indent=2)}")

        # Set exit code based on result
        exit(0 if result.get("success") else 1)

    # Call main function
    main()
