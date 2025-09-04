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

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass(frozen=True)
class OpenSource:
    name: str
    license: str
    license_file: str = field(metadata={"source_key": "License File"})
    version_number: str
    owner: str
    upstream_url: str = field(metadata={"source_key": "Upstream URL"})
    description: str
    dependencies: Tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_dict(cls, data: dict):
        mapping = {
            'Name': 'name',
            'License': 'license',
            'License File': 'license_file',
            'Version Number': 'version_number',
            'Owner': 'owner',
            'Upstream URL': 'upstream_url',
            'Description': 'description',
            'Dependencies': 'dependencies'
        }
        init_data = {}
        for json_key, attr_name in mapping.items():
            value = data.get(json_key)
            if isinstance(value, str):
                value = value.strip()
            elif value is None:
                value = ""
            if attr_name == "dependencies":
                if isinstance(value, str):
                    value = tuple(v.strip() for v in value.split(';') if v.strip())
                elif isinstance(value, list):
                    value = tuple(value)
                else:
                    value = ()
            init_data[attr_name] = value
        return cls(**init_data)

    def get_licenses(self) -> List[str]:
        return [lic.strip() for lic in self.license.split(';') if lic.strip()]

    def get_license_files(self) -> List[str]:
        return [f.strip() for f in self.license_file.split(';') if f.strip()]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "license": self.license,
            "license_file": self.license_file,
            "version_number": self.version_number,
            "owner": self.owner,
            "upstream_url": self.upstream_url,
            "description": self.description,
            "dependencies": list(self.dependencies),
            "licenses": list(self.get_licenses()),
            "license_files": list(self.get_license_files())
        }
