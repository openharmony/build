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

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any


@dataclass
class Target:
    target_name: str = ""
    type: str = ""
    args: List[str] = field(default_factory=list)
    deps: List[str] = field(default_factory=list)
    depfile: str = ""
    inputs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    outputs: List[str] = field(default_factory=list)
    public: str = ""
    script: str = ""
    testonly: bool = False
    toolchain: str = ""
    visibility: List[str] = field(default_factory=list)
    source_outputs: Dict[str, Any] = field(default_factory=dict)
    sources: List[str] = field(default_factory=list)
    libs: List[str] = field(default_factory=list)
    ldflags: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, target_name: str, d: Dict[str, Any]) -> "Target":
        allowed = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(target_name=target_name,
                   **{k: v for k, v in d.items() if k in allowed})

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_dict_without_name(self) -> Dict[str, Any]:
        data = asdict(self)
        data.pop('target_name', None)
        return data
