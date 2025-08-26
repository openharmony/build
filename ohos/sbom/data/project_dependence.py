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

from typing import List, Dict, Any, Optional

from ohos.sbom.data.file_dependence import File
from ohos.sbom.data.manifest import Project
from ohos.sbom.sbom.metadata.sbom_meta_data import RelationshipType


class ProjectDependence:
    __slots__ = ('_source_project', '_dependencies')

    def __init__(self, source: Project):
        self._source_project = source
        self._dependencies = {
            type: set()
            for type in RelationshipType
        }

    @property
    def source_project(self) -> Project:
        return self._source_project

    def add_dependency(self, dep_type: RelationshipType, other) -> None:
        if dep_type not in self._dependencies:
            raise ValueError(f"Invalid dependency type: {dep_type}")
        self._dependencies[dep_type].add(other)

    def add_dependency_list(self, dep_type: RelationshipType, others: List) -> None:
        for other in others:
            self.add_dependency(dep_type, other)

    def get_dependencies(self, dep_type: Optional[RelationshipType] = None):
        if dep_type:
            return self._dependencies.get(dep_type, set())
        return self._dependencies

    def to_dict(self) -> Dict[str, Any]:
        deps_dict = {}

        for rel_type in RelationshipType:
            items = []
            for obj in self._dependencies[rel_type]:
                if isinstance(obj, File):
                    items.append(obj.relative_path)
                else:
                    items.append(getattr(obj, "name", str(obj)))
            deps_dict[rel_type.value] = sorted(set(items))

        return {
            "source_project": self.source_project.name,
            "dependencies": deps_dict
        }
