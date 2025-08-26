#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (c) 2025 Northeastern University
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
from collections import defaultdict
from pathlib import Path
from typing import List, Optional, Dict

from ohos.sbom.analysis.depend_graph import DependGraphAnalyzer
from ohos.sbom.data.file_dependence import File, FileType
from ohos.sbom.data.target import Target
from ohos.sbom.sbom.metadata.sbom_meta_data import RelationshipType


class FileDependencyAnalyzer:
    def __init__(self, all_target_depend: DependGraphAnalyzer):
        self._depend_graph = all_target_depend
        self._file_dependencies: Dict[str, File] = {}
        self._target_name_map_file = defaultdict(list)

    def build_start(self, target_name: str):
        self._depend_graph.dfs_downstream(
            start=target_name,
            max_depth=None,
            pre_visit=self._pre_visit_callback,
            post_visit=self._post_visit_callback
        )

    def get_file_dependencies(self) -> Dict[str, File]:
        return self._file_dependencies

    def get_target_name_map_file(self) -> Dict[str, List[str]]:
        return self._target_name_map_file

    def build_all_install_deps_optimized(self, install_targets: List[str]):
        virtual_root = "__ALL_INSTALL_ROOT__"

        try:

            self._depend_graph.add_virtual_root(virtual_root, install_targets)

            print(f"Starting one-time traversal of dependencies for {len(install_targets)} modules...")
            self._depend_graph.dfs_downstream(
                start=virtual_root,
                max_depth=None,
                pre_visit=self._pre_visit_callback,
                post_visit=self._post_visit_callback
            )
            print(f"Completed! Collected {len(self._file_dependencies)} files in total")

        finally:
            self._depend_graph.remove_virtual_root(virtual_root)

    def extract_outputs_and_source_outputs(self, target: Target) -> list:
        raw_outputs = getattr(target, 'outputs', None)
        raw_source_outputs = getattr(target, 'source_outputs', None)

        outputs = raw_outputs if isinstance(raw_outputs, (list, tuple)) else []
        source_outputs = raw_source_outputs if isinstance(raw_source_outputs, dict) else {}

        result = []

        for out in outputs:
            if out and 'unstripped' not in out:
                result.append(out)

        for output_list in source_outputs.values():
            if isinstance(output_list, (list, tuple)) and len(output_list) > 0:
                first_output = output_list[0]
                if first_output and 'unstripped' not in first_output:
                    result.append(first_output)

        return result

    def process_source_output_dependencies(self, target: Target, outputs: list, source_list: list):
        output_by_stem = {Path(out).stem: out for out in outputs}
        matched_outputs = set()

        for source in source_list:
            stem = Path(source).stem
            if stem in output_by_stem:
                output_file = self._file_dependencies.setdefault(
                    output_by_stem[stem], File(output_by_stem[stem], target)
                )
                source_file = self._file_dependencies.setdefault(source, File(source, None))
                output_file.add_dependency(RelationshipType.GENERATED_FROM, source_file)
                matched_outputs.add(output_by_stem[stem])

        remaining_outputs = [out for out in outputs if out not in matched_outputs]
        for out in remaining_outputs:
            output_file = self._file_dependencies.setdefault(out, File(out, target))
            for source in source_list:
                source_file = self._file_dependencies.setdefault(source, File(source, None))
                output_file.add_dependency(RelationshipType.GENERATED_FROM, source_file)

    def process_target(self, target: Target, all_outputs: list):
        try:

            if not all_outputs:
                return

            source_list = self.get_source_list(target)

            self.process_source_output_dependencies(target, all_outputs, source_list)

        except Exception as e:
            print(f"Error processing target '{getattr(target, 'target_name', 'unknown')}': {e}")

    def process_libs_dependencies(self, target: Target, outputs: list):
        """
        Process library dependencies from the target's 'libs' field and link them to output files.
        Handles both static and dynamic libraries with appropriate relationship types.
        """
        try:
            # Extract and normalize the 'libs' list from the target
            lib_list = getattr(target, 'libs', None)
            if not lib_list:
                return
            if isinstance(lib_list, str):
                lib_list = [lib_list]
            elif not isinstance(lib_list, (list, tuple)):
                return

            # Clean up library names (strip whitespace and remove empty entries)
            libs = [lib.strip() for lib in lib_list if isinstance(lib, str) and lib.strip()]

            # Parse dependencies into static and dynamic libraries
            dep_result = self.extract_libs_dependencies(libs)

            # Process each output file
            for out in outputs:
                output_file = self._file_dependencies.get(out)
                if not output_file:
                    continue  # Skip if output file is not tracked

                # Handle static library dependencies
                for static_lib in dep_result.get('static', []):
                    lib_file = self._file_dependencies.setdefault(
                        static_lib,
                        File(static_lib, None, file_type=FileType.STATIC_LIBRARY)
                    )
                    output_file.add_dependency_by_file_type(lib_file)

                # Handle dynamic library dependencies
                for dynamic_lib in dep_result.get('dynamic', []):
                    lib_file = self._file_dependencies.setdefault(
                        dynamic_lib,
                        File(dynamic_lib, None, file_type=FileType.SHARED_LIBRARY)
                    )
                    output_file.add_dependency_by_file_type(lib_file)

        except Exception as e:
            print(f"Error processing libs for target '{getattr(target, 'target_name', 'unknown')}': {e}")

    def process_ldflags_dependencies(self, target: Target, outputs: list):
        """
        Process library dependencies extracted from the target's 'ldflags'.
        Resolves static and dynamic libraries specified via -l, .a/.so paths, or linker flags.
        Links them to output files with appropriate relationship types.
        """
        try:
            # Extract and normalize ldflags from target
            ldflags_list = getattr(target, 'ldflags', None)
            if not ldflags_list:
                return
            if isinstance(ldflags_list, str):
                ldflags_list = [ldflags_list]
            elif not isinstance(ldflags_list, (list, tuple)):
                return

            # Clean up flags: strip and filter valid strings
            ldflags = [flag.strip() for flag in ldflags_list if isinstance(flag, str) and flag.strip()]

            # Parse dependencies from ldflags
            dep_result = self.extract_ldflags_dependencies(ldflags)

            # Process each output file
            for out in outputs:
                output_file = self._file_dependencies.get(out)
                if not output_file:
                    continue  # Skip if output is not tracked

                # Handle static library dependencies
                for static_lib in dep_result.get('static', []):
                    lib_file = self._file_dependencies.setdefault(
                        static_lib,
                        File(static_lib, None, file_type=FileType.STATIC_LIBRARY)
                    )
                    output_file.add_dependency_by_file_type(lib_file)

                # Handle dynamic library dependencies
                for dynamic_lib in dep_result.get('dynamic', []):
                    lib_file = self._file_dependencies.setdefault(
                        dynamic_lib,
                        File(dynamic_lib, None, file_type=FileType.SHARED_LIBRARY)
                    )
                    output_file.add_dependency_by_file_type(lib_file)

        except Exception as e:
            print(f"Error processing libs for executable '{getattr(target, 'target_name', 'unknown')}': {e}")

    def extract_deps(self, target: Target, outputs):
        """
        Extract and process dependencies from the target's 'deps' field.
        For each dependency:
          - Resolve the target in the dependency graph
          - Skip metadata generator targets
          - Link output files using appropriate file types
        All errors are logged but do not block processing of other deps.
        """
        try:
            # Extract and normalize the 'deps' list
            dep_list = getattr(target, 'deps', None)
            if not dep_list:
                return
            if isinstance(dep_list, str):
                dep_list = [dep_list]
            elif not isinstance(dep_list, (list, tuple)):
                return

            # Process each dependency
            for dep in dep_list:
                self._process_single_dep(dep, outputs, target)

        except Exception as e:
            print(f"Error processing deps for executable '{getattr(target, 'target_name', 'unknown')}': {e}")

    def extract_libs_dependencies(self, libs: List[str]) -> Dict[str, List[str]]:
        static_libs = []
        dynamic_libs = []

        for lib in libs:
            if not isinstance(lib, str) or not lib.strip():
                continue
            lib = lib.strip()
            if lib.endswith('.a'):
                basename = os.path.basename(lib)
                static_libs.append(basename)
            else:
                if lib.startswith('lib') and (lib.endswith('.so') or '.so.' in lib):
                    so_name = lib.split('.so')[0] + '.so'
                    dynamic_libs.append(so_name)
                else:
                    dyn_name = f"lib{lib}.so" if not lib.startswith('lib') else f"{lib}.so"
                    dynamic_libs.append(dyn_name)

        def unique(lst):
            seen = set()
            result = []
            for x in lst:
                if x not in seen:
                    seen.add(x)
                    result.append(x)
            return result

        return {
            'static': unique(static_libs),
            'dynamic': unique(dynamic_libs)
        }

    def extract_ldflags_dependencies(self, ldflags: List[str]) -> Dict[str, List[str]]:
        static_libs = []
        dynamic_libs = []
        is_static_mode = False

        i = 0
        while i < len(ldflags):
            flag = ldflags[i].strip()
            if not flag:
                i += 1
                continue

            if flag in ("-Wl,-Bstatic", "-static"):
                is_static_mode = True
            elif flag in ("-Wl,-Bdynamic", "-shared"):
                is_static_mode = False

            elif flag.startswith("-l"):
                self._handle_library_flag(flag[2:], is_static_mode, static_libs, dynamic_libs)

            elif flag == "-l" and i + 1 < len(ldflags):
                lib_name = ldflags[i + 1].strip()
                if lib_name:
                    self._handle_library_flag(lib_name, is_static_mode, static_libs, dynamic_libs)
                i += 1

            elif flag.startswith('-Wl,--exclude-libs='):
                self._handle_exclude_libs(flag, static_libs)

            elif self._is_library_path(flag):
                basename = self._normalize_library_path(flag)
                if basename.endswith('.a'):
                    static_libs.append(basename)
                else:
                    dynamic_libs.append(basename)

            elif flag.startswith("-stdlib="):
                lib_name = flag.split("=", 1)[1]
                self._add_lib(lib_name, is_static_mode, static_libs, dynamic_libs)

            elif flag.startswith("-rtlib="):
                lib_name = flag.split("=", 1)[1]
                self._add_lib(f"{lib_name}_rt", is_static_mode, static_libs, dynamic_libs)

            i += 1

        return {
            "static": self._unique(static_libs),
            "dynamic": self._unique(dynamic_libs)
        }

    def get_source_list(self, target: Target) -> list:
        source_list = getattr(target, 'sources', None) or getattr(target, 'source', None)

        if not source_list:
            return []

        if isinstance(source_list, str):
            source_list = [source_list]
        elif not isinstance(source_list, (list, tuple)):
            source_list = []

        return [src.strip() for src in source_list if isinstance(src, str) and src.strip()]

    def get_remaining_outputs(self, target: Target, outputs: list) -> list:
        source_list = self.get_source_list(target)
        source_stems = {Path(src).stem for src in source_list if src.strip()}
        return [
            out for out in outputs
            if isinstance(out, str) and out.strip() and Path(out).stem not in source_stems
        ]

    def _post_visit_callback(self, node: str, depth: int, parent: Optional[str]) -> None:

        target = self._depend_graph.get_target(node)
        if self._is_metadata_generator_target(target.target_name):
            return
        outputs = self.extract_outputs_and_source_outputs(target)
        target_type = target.type
        if target_type == 'copy':
            self._handle_copy(target, outputs)
        elif target_type == 'group':
            return
        elif target_type == 'source_set':
            self._handle_source_set(target, outputs)
        elif target_type == 'executable':
            self._handle_executable(target, outputs)
        elif target_type == 'shared_library':
            self._handle_shared_library(target, outputs)
        elif target_type == 'action':
            self._handle_action(target, outputs)
        elif target_type == 'action_foreach':
            self._handle_action_foreach(target, outputs)
        elif target_type == 'generated_file':
            self._handle_executable(target, outputs)
        elif target_type == 'rust_library':
            self._handle_rust_library(target, outputs)
        elif target_type == 'rust_proc_macro':
            self._handle_rust_proc_macro(target, outputs)
        elif target_type == 'static_library':
            self._handle_static_library(target, outputs)
        elif target_type == 'virtual_root':
            return
        else:
            print(f"Error: unknown target type '{target_type}' for target '{target.target_name}'")
            return

    def _pre_visit_callback(self, node: str, depth: int, parent: Optional[str]) -> bool:
        target = self._depend_graph.get_target(node)

        if target.target_name in self._target_name_map_file:
            return True

        if self._is_metadata_generator_target(target.target_name):
            return False

        self._target_name_map_file[target.target_name] = []

        outputs = getattr(target, 'outputs', None) or []
        created_any = False

        for output in outputs:
            if not output:
                continue
            if output in self._file_dependencies or 'unstripped' in output:
                continue
            output_file = File(output, target)
            self._file_dependencies[output] = output_file
            self._target_name_map_file[target.target_name].append(output_file)
            created_any = True

        if not created_any and hasattr(target, 'source_outputs') and target.source_outputs:
            for output_list in target.source_outputs.values():
                if not output_list:
                    continue
                primary_output = output_list[0]
                if not primary_output or primary_output in self._file_dependencies or 'unstripped' in primary_output:
                    continue
                output_file = File(primary_output, target)
                self._file_dependencies[primary_output] = output_file
                self._target_name_map_file[target.target_name].append(output_file)
                created_any = True

        return True

    def _link_dependency_outputs(
            self,
            outputs: list,
            dep_out_file_list: list,
            target: Target
    ):
        """Link dependency output files to current target's output files."""
        for out in outputs or []:
            if out not in self._file_dependencies:
                self._file_dependencies[out] = File(out, target)
            file_out = self._file_dependencies[out]
            file_out.add_dependency_list_by_file_type(dep_out_file_list)

    def _process_single_dep(self, dep, outputs, target):
        """Helper to process one dependency, avoids deep nesting."""
        try:
            dep_target = self._depend_graph.get_target(dep)
            if not dep_target:
                return

            if self._is_metadata_generator_target(dep_target.target_name):
                return

            dep_out_file_list = self._target_name_map_file.get(dep_target.target_name, [])
            if not dep_out_file_list:
                return

            self._link_dependency_outputs(outputs, dep_out_file_list, target)

        except Exception as e:
            print(f"Error processing dep '{dep}': {e}")

    def _is_metadata_generator_target(self, target_name: str) -> bool:
        core_name = target_name.split('(', 1)[0]

        metadata_suffixes = (
            '__notice',
            '__check',
            '_info',
            'notice.txt',
            '_notice'
        )

        return core_name.endswith(metadata_suffixes)

    def _get_or_create_file(self, relative_path):
        if relative_path in self._file_dependencies:
            file = self._file_dependencies[relative_path]
        else:
            file = File(relative_path, None)
            self._file_dependencies[relative_path] = file
        return file

    def _handle_library_flag(self, lib_name: str, is_static_mode: bool, static_libs: list, dynamic_libs: list):
        base = lib_name if lib_name.startswith('lib') else f"lib{lib_name}"
        if is_static_mode:
            static_libs.append(f"{base}.a")
        else:
            dynamic_libs.append(f"{base}.so")

    def _handle_exclude_libs(self, flag: str, static_libs: list):
        parts = flag.split('=', 2)
        if len(parts) >= 3:
            lib_path = parts[2]
            basename = os.path.basename(lib_path)
            if basename.endswith('.a'):
                static_libs.append(basename)

    def _is_library_path(self, flag: str) -> bool:
        return flag.endswith('.a') or flag.endswith('.so') or '.so.' in flag

    def _normalize_library_path(self, flag: str) -> str:
        basename = os.path.basename(flag)
        if '.so.' in basename:
            stem = basename.split('.so.')[0]
            return f"{stem}.so"
        return basename

    def _add_lib(self, lib_name: str, is_static_mode: bool, static_libs: list, dynamic_libs: list):
        base = lib_name if lib_name.startswith('lib') else f"lib{lib_name}"
        if is_static_mode:
            static_libs.append(f"{base}.a")
        else:
            dynamic_libs.append(f"{base}.so")

    def _unique(self, lst: list) -> list:
        seen = set()
        result = []
        for x in lst:
            if x not in seen:
                seen.add(x)
                result.append(x)
        return result

    def _handle_copy(self, target: Target, outputs):
        source_list = getattr(target, 'sources', None) or getattr(target, 'source', None)
        if not source_list:
            return

        outputs = outputs or getattr(target, 'outputs', None)
        if not outputs:
            return

        for source, output_path in zip(source_list, outputs):
            if 'unstripped' in source or 'unstripped' in output_path:
                continue

            source_file = self._get_or_create_file(source)

            if output_path not in self._file_dependencies:
                self._file_dependencies[output_path] = File(output_path, target)

            self._file_dependencies[output_path].add_dependency(RelationshipType.COPY_OF, source_file)

    def _handle_source_set(self, target: Target, outputs):
        self.process_target(target, outputs)
        remain_outputs = self.get_remaining_outputs(target, outputs)
        self.process_libs_dependencies(target, remain_outputs)
        self.process_ldflags_dependencies(target, remain_outputs)
        self.extract_deps(target, remain_outputs)

    def _handle_executable(self, target: Target, outputs):
        self.process_target(target, outputs)
        remain_outputs = self.get_remaining_outputs(target, outputs)
        self.process_libs_dependencies(target, remain_outputs)
        self.process_ldflags_dependencies(target, remain_outputs)
        self.extract_deps(target, remain_outputs)

    def _handle_shared_library(self, target: Target, outputs):
        self.process_target(target, outputs)
        remain_outputs = self.get_remaining_outputs(target, outputs)
        self.process_libs_dependencies(target, remain_outputs)
        self.process_ldflags_dependencies(target, remain_outputs)
        self.extract_deps(target, remain_outputs)

    def _handle_static_library(self, target: Target, outputs):
        self.process_target(target, outputs)
        remain_outputs = self.get_remaining_outputs(target, outputs)
        self.process_libs_dependencies(target, remain_outputs)
        self.process_ldflags_dependencies(target, remain_outputs)
        self.extract_deps(target, remain_outputs)

    def _handle_action(self, target: Target, outputs):
        self.process_target(target, outputs)
        remain_outputs = self.get_remaining_outputs(target, outputs)
        self.process_libs_dependencies(target, remain_outputs)
        self.process_ldflags_dependencies(target, remain_outputs)
        self.extract_deps(target, remain_outputs)

    def _handle_action_foreach(self, target: Target, outputs):
        self.process_target(target, outputs)
        remain_outputs = self.get_remaining_outputs(target, outputs)
        self.process_libs_dependencies(target, remain_outputs)
        self.process_ldflags_dependencies(target, remain_outputs)
        self.extract_deps(target, remain_outputs)

    def _handle_rust_library(self, target: Target, outputs):
        self.process_target(target, outputs)
        remain_outputs = self.get_remaining_outputs(target, outputs)
        self.process_libs_dependencies(target, remain_outputs)
        self.process_ldflags_dependencies(target, remain_outputs)
        self.extract_deps(target, remain_outputs)

    def _handle_rust_proc_macro(self, target, outputs):
        self.process_target(target, outputs)
        remain_outputs = self.get_remaining_outputs(target, outputs)
        self.process_libs_dependencies(target, remain_outputs)
        self.process_ldflags_dependencies(target, remain_outputs)
        self.extract_deps(target, remain_outputs)
