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

import os
import sys
import subprocess
import shutil
import platform
import re
import stat
from containers.arg import Arg
from services.interface.prebuilt_sdk_interface import PrebuiltSdkInterface
from resources.global_var import CURRENT_OHOS_ROOT
from util.log_util import LogUtil


class PrebuiltSdk(PrebuiltSdkInterface):

    def __init__(self, args_dict):
        super().__init__()
        self._args_dict = args_dict
        self.api_version = self._get_api_version()
        self.sdk_prebuilts_path = os.path.join(CURRENT_OHOS_ROOT, 'prebuilts', 'ohos-sdk')

    def should_build_sdk(self, args_dict) -> bool:
        """Determine if SDK needs to be built"""
        if args_dict.get("no_prebuilt_sdk").arg_value is True:
            return False

        if args_dict.get("product_name").arg_value == 'ohos-sdk':
            return False

        sdk_path = os.path.join(self.sdk_prebuilts_path, 'linux', self.api_version)
        if os.path.exists(sdk_path):
            return False

        if args_dict.get("prebuilt_sdk").arg_value is False:
            return False

        return True

    def build_prebuilt_sdk(self, args_dict) -> bool:
        try:
            LogUtil.hb_info('Building the latest ohos-sdk...')
            Arg.clean_args_file()

            self._set_path()

            build_args = self._prepare_build_args(args_dict)
            if not self._execute_sdk_build(build_args):
                return False

            if not self._post_process_sdk(self.api_version):
                return False

            self._migrate_legacy_sdk()

            LogUtil.hb_info('ohos-sdk build completed successfully!')
            return True

        except Exception as e:
            LogUtil.hb_error(f'ohos-sdk build failed! {e}')
            LogUtil.hb_info("Try using '--no-prebuilt-sdk=true' to skip.")
            return False

    def regist_arg(self, arg_name: str, arg_value):
        """Implement ServiceInterface regist_arg method"""
        self._args_dict[arg_name] = arg_value

    def run(self):
        """Implement ServiceInterface run method"""
        return self.build_prebuilt_sdk(self._args_dict)

    def _execute_sdk_build(self, build_args: dict) -> bool:
        """Execute SDK build command"""
        try:
            cmd = [
                sys.executable,
                os.path.join(CURRENT_OHOS_ROOT, 'build', 'hb', 'main.py'),
                'build', '--product-name', 'ohos-sdk',
                f"--ccache={build_args['ccache_args']}",
                f"--xcache={build_args['xcache_args']}",
                '--load-test-config=false',
                '--get-warning-list=false',
                '--stat-ccache=false',
                '--compute-overlap-rate=false',
                '--deps-guard=false',
                '--generate-ninja-trace=false',
                f"--sbom={build_args['generate_sbom']}",
            ]

            # Add SBOM related gn flags
            if build_args['generate_sbom']:
                cmd.extend([
                    '--gn-flags=--ide=json',
                    '--gn-flags=--json-file-name=sbom/gn_gen.json'
                ])

            # Add gn args
            gn_args_str = ' '.join(build_args['gn_args_parts'])
            cmd.extend(['--gn-args', gn_args_str])

            LogUtil.hb_info(f"Executing SDK build: {' '.join(cmd)}")

            result = subprocess.run(cmd, check=True, text=True, cwd=CURRENT_OHOS_ROOT, env=os.environ)
            return result.returncode == 0

        except subprocess.CalledProcessError as e:
            LogUtil.hb_error(f"SDK build command failed: {e}")
            return False
        except Exception as e:
            LogUtil.hb_error(f"Unexpected error during SDK build: {e}")
            return False

    def _prepare_build_args(self, args_dict: dict) -> dict:
        """Prepare SDK build arguments"""
        # Get platform information
        sysname = platform.system().lower()
        current_platform = 'linux' if 'linux' in sysname else ('mac' if 'darwin' in sysname else 'linux')

        # Get cache settings
        ccache_enabled = getattr(args_dict.get('ccache'), 'arg_value', True)
        xcache_enabled = getattr(args_dict.get('xcache'), 'arg_value', False)
        sbom_enabled = getattr(args_dict.get('sbom'), 'arg_value', False)

        # Build gn args
        gn_args_parts = [
            'skip_generate_module_list_file=true',
            f'sdk_platform={current_platform}',
            f'ndk_platform={current_platform}',
            'use_cfi=false',
            'use_thin_lto=false',
            'enable_lto_O0=true',
            'sdk_check_flag=false',
            'enable_ndk_doxygen=false',
            'archive_ndk=false',
            'sdk_for_hap_build=true',
            'enable_archive_sdk=false',
            'enable_notice_collection=false',
            'enable_process_notice=false'
        ]

        prebuilts_arg_obj = args_dict.get('prebuilts_sdk_gn_args')
        if prebuilts_arg_obj and prebuilts_arg_obj.arg_value:
            for v in prebuilts_arg_obj.arg_value:
                if isinstance(v, str):
                    vv = v.strip().strip("'").strip('"')
                    if vv:
                        gn_args_parts.append(vv)

        return {
            'ccache_args': 'true' if ccache_enabled else 'false',
            'xcache_args': 'true' if xcache_enabled else 'false',
            'generate_sbom': sbom_enabled,
            'gn_args_parts': gn_args_parts,
        }

    def _post_process_sdk(self, api_version: str) -> bool:
        """SDK post-processing logic"""
        try:
            root_path = CURRENT_OHOS_ROOT
            sdk_prebuilts_path = self.sdk_prebuilts_path

            # Clean up old SDK directory
            old_sdk_path = os.path.join(root_path, 'prebuilts', 'ohos-sdk', 'linux')
            if os.path.exists(old_sdk_path):
                shutil.rmtree(old_sdk_path)

            # Create new SDK directory
            os.makedirs(sdk_prebuilts_path, exist_ok=True)

            # Move build artifacts
            out_sdk_path = os.path.join(root_path, 'out', 'sdk', 'ohos-sdk', 'linux')
            if os.path.exists(out_sdk_path):
                shutil.move(out_sdk_path, sdk_prebuilts_path)

            # Handle native related files
            native_dirs = [
                os.path.join(root_path, 'out', 'sdk', 'sdk-native', 'os-irrelevant'),
                os.path.join(root_path, 'out', 'sdk', 'sdk-native', 'os-specific', 'linux')
            ]

            native_target = os.path.join(sdk_prebuilts_path, 'linux', 'native')
            os.makedirs(native_target, exist_ok=True)

            for native_dir in native_dirs:
                if os.path.exists(native_dir):
                    for item in os.listdir(native_dir):
                        src = os.path.join(native_dir, item)
                        dst = os.path.join(native_target, item)
                        if os.path.exists(dst):
                            if os.path.isdir(dst):
                                shutil.rmtree(dst)
                            else:
                                os.remove(dst)
                        shutil.move(src, dst)

            # Organize API version directory structure
            linux_sdk_path = os.path.join(sdk_prebuilts_path, 'linux')
            api_dir = os.path.join(linux_sdk_path, api_version)
            os.makedirs(api_dir, exist_ok=True)

            for item in os.listdir(linux_sdk_path):
                item_path = os.path.join(linux_sdk_path, item)
                if os.path.isdir(item_path) and item != api_version:
                    target_path = os.path.join(api_dir, item)
                    shutil.move(item_path, target_path)

            self._create_previewer_package(api_version)

            return True

        except Exception as e:
            LogUtil.hb_error(f"SDK post-processing failed: {e}")
            return False

    def _create_previewer_package(self, api_version: str) -> None:
        try:
            target_dir = os.path.join(self.sdk_prebuilts_path, 'linux', api_version, 'previewer')
            os.makedirs(target_dir, exist_ok=True)

            source_package = os.path.join(self.sdk_prebuilts_path, 'linux', api_version, 'native', 'oh-uni-package.json')
            target_package = os.path.join(target_dir, 'oh-uni-package.json')

            if os.path.exists(source_package):
                shutil.copy2(source_package, target_package)

                # Modify package.json content
                with open(target_package, 'r', encoding='utf-8') as f:
                    content = f.read()

                content = content.replace('Native', 'Previewer')
                content = content.replace('native', 'previewer')

                with os.fdopen(os.open(target_package, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode=0o644),
                                    "w", encoding='utf-8') as f:
                    f.write(content)

        except Exception as e:
            LogUtil.hb_warning(f"Failed to create previewer package: {e}")

    def _migrate_legacy_sdk(self) -> None:
        """Migrate legacy SDK to unified location"""
        try:
            old_sdk_12_path = os.path.join(CURRENT_OHOS_ROOT, 'prebuilts', 'ohos-sdk-12', 'ohos-sdk', 'linux', '12')
            new_sdk_12_path = os.path.join(self.sdk_prebuilts_path, 'linux', '12')

            if os.path.exists(old_sdk_12_path):
                os.makedirs(new_sdk_12_path, exist_ok=True)
                for item in os.listdir(old_sdk_12_path):
                    src = os.path.join(old_sdk_12_path, item)
                    dst = os.path.join(new_sdk_12_path, item)
                    if os.path.exists(dst):
                        if os.path.isdir(dst):
                            shutil.rmtree(dst)
                        else:
                            os.remove(dst)
                    shutil.move(src, dst)
                LogUtil.hb_info('Migrated ohos-sdk-12 to unified location.')

        except Exception as e:
            LogUtil.hb_warning(f"Failed to migrate legacy SDK: {e}")

    def _set_path(self):
        """Set PATH environment variable"""
        prebuilts_cache_path = os.path.join(CURRENT_OHOS_ROOT, 'prebuilts', 'build-tools', 'common', 'ccache')
        nodejs_bin_path = os.path.join(CURRENT_OHOS_ROOT, 'prebuilts', 'build-tools', 'common', 'nodejs', 'current', 'bin')
        os.environ['PATH'] = prebuilts_cache_path + os.pathsep + nodejs_bin_path + os.pathsep + os.environ['PATH']

    def _get_api_version(self) -> str:
        """
        Get API version from version.gni file.
        """
        version_gni_path = os.path.join(CURRENT_OHOS_ROOT, 'build', 'version.gni')

        try:
            with open(version_gni_path, 'r', encoding='utf-8') as f:
                content = f.read()

            pattern = r'api_version\s*=\s*"([^"]+)"'
            match = re.search(pattern, content)

            if match:
                return match.group(1).strip()
            else:
                LogUtil.hb_warning("API version not found in version.gni")
                return "unknown"

        except Exception as e:
            LogUtil.hb_warning(f"Unexpected error while getting API version: {e}")
            return "unknown"