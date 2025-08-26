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

from collections import defaultdict
from typing import Dict, Set, List, Optional, Tuple, Any

from ohos.sbom.data.file_dependence import File
from ohos.sbom.data.manifest import Project
from ohos.sbom.data.opensource import OpenSource
from ohos.sbom.data.project_dependence import ProjectDependence
from ohos.sbom.extraction.local_resource_loader import LocalResourceLoader
from ohos.sbom.sbom.metadata.sbom_meta_data import RelationshipType


class ProjectDependencyAnalyzer:

    def __init__(self):
        self.manifest = LocalResourceLoader.load_manifest()
        self._file_to_target_name: Dict[File, str] = {}
        self._target_to_project: Dict[str, Project] = {}
        self._project_dependency: Dict[str, ProjectDependence] = {}
        self._project_to_upstream: Dict[str, List[OpenSource]] = {}
        self._built = False

    def build(self, all_files: List[File]) -> Dict[str, Dict[str, List[str]]]:
        self._reset()
        self._build_mappings(all_files)
        self._build_project_contains(all_files)
        self._build_project_dependencies(all_files)
        self._build_upstream_dependencies()
        self._built = True
        return self._format_result()

    def get_file_project_mapping(self) -> Dict[str, str]:
        mapping = {}
        for file, target_name in self._file_to_target_name.items():
            project = self._target_to_project.get(target_name)
            if project:
                mapping[file.relative_path] = project.name
        return mapping

    def get_project_files(self) -> Dict[str, List[str]]:
        project_files = defaultdict(list)
        for file, target_name in self._file_to_target_name.items():
            project = self._target_to_project.get(target_name)
            if project:
                project_files[project.name].append(file.relative_path)
        return dict(project_files)

    def get_project_dependence(self) -> Dict[str, ProjectDependence]:
        if not self._built:
            raise RuntimeError("The build() method must be called first to construct the dependency relationships")
        return self._project_dependency

    def to_dict(self) -> Dict[str, Any]:
        if not self._built:
            raise RuntimeError("The build() method must be called first to construct the dependency relationships")

        manifest_info = {
            "remotes": [{"name": r.name, "fetch": r.fetch} for r in self.manifest.remotes],
            "default": self.manifest.default,
            "projects": [p.name for p in self.manifest.projects]
        }

        return {
            "manifest": manifest_info,
            "file_project_mapping": self.get_file_project_mapping(),
            "project_files": self.get_project_files(),
            "project_dependencies": [pd.to_dict() for pd in self._project_dependency.values()],
            "upstream_packages": {
                project_name: [pkg.to_dict() for pkg in pkgs]
                for project_name, pkgs in self._project_to_upstream.items()
            }
        }

    def _reset(self):
        self._file_to_target_name.clear()
        self._target_to_project.clear()
        self._project_dependency.clear()
        self._project_to_upstream.clear()
        self._built = False

    def _build_mappings(self, all_files: List[File]):
        for file in all_files:
            if file.source_target is not None:
                self._file_to_target_name[file] = file.source_target.target_name

        for target_name in set(self._file_to_target_name.values()):
            project = self.manifest.find_project(target_name)
            if project is not None:
                self._target_to_project[target_name] = project

    def _get_or_create_dependency(self, project: Project) -> ProjectDependence:
        if project.name not in self._project_dependency:
            self._project_dependency[project.name] = ProjectDependence(project)
        return self._project_dependency[project.name]

    def _get_file_project(self, file: File) -> Optional[Project]:
        target_name = self._file_to_target_name.get(file)
        if not target_name:
            return None
        return self._target_to_project.get(target_name)

    def _build_project_contains(self, all_files: List[File]):
        for file in all_files:
            project = self._get_file_project(file)
            if not project:
                continue
            pd = self._get_or_create_dependency(project)
            if file.is_library or file.is_intermediate:
                pd.add_dependency(RelationshipType.GENERATES, file)
            else:
                pd.add_dependency(RelationshipType.CONTAINS, file)

    def _build_project_dependencies(self, all_files: List[File]):
        processed_deps: Set[Tuple[str, str]] = set()
        for file in all_files:
            current_project = self._get_file_project(file)
            if not current_project:
                continue
            for relation_type in RelationshipType:
                # skip RelationshipType.OTHER
                if relation_type == RelationshipType.OTHER:
                    continue
                self._process_dependencies_for_relation(file, relation_type, current_project, processed_deps)

    def _build_upstream_dependencies(self):
        for project in self._target_to_project.values():
            upstream_pkgs = LocalResourceLoader.load_opensource(project.path)
            if not upstream_pkgs:
                continue
            pd = self._get_or_create_dependency(project)
            pd.add_dependency_list(RelationshipType.VARIANT_OF, upstream_pkgs)
            self._project_to_upstream[project.name] = upstream_pkgs

    def _process_dependencies_for_relation(self, file, relation_type, current_project, processed_deps):
        for dep_file in file.get_dependencies(relation_type):
            dep_project = self._get_file_project(dep_file)
            if not dep_project or dep_project.name == current_project.name:
                continue

            dep_key = (current_project.name, dep_project.name)
            if dep_key in processed_deps:
                continue

            pd_src = self._get_or_create_dependency(current_project)
            pd_src.add_dependency(RelationshipType.DEPENDS_ON, dep_project)
            processed_deps.add(dep_key)

    def _format_result(self) -> Dict[str, Dict[str, List[str]]]:
        result = {}
        for name, pd in self._project_dependency.items():
            deps = {}
            for dep_type, objs in pd.get_dependencies().items():
                if objs:
                    key = dep_type.value
                    deps[key] = sorted({getattr(obj, "name", str(obj)) for obj in objs})
            result[name] = deps
        return result
