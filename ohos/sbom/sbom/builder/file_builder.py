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

from copy import deepcopy
from typing import Optional, List, Literal, Union, Tuple

from ohos.sbom.sbom.builder.base_builder import ConfigurableBuilder
from ohos.sbom.sbom.metadata.sbom_meta_data import Hash, File


class FileBuilder(ConfigurableBuilder):
    """
    Builder class for creating File metadata in SBOM documents.

    Implements fluent interface pattern for easy configuration of file properties.
    Uses 'file' configuration from FieldConfigManager by default.
    """

    CONFIG_NAME = "file"

    def __init__(self):
        """Initialize a new FileBuilder with all fields set to None/empty."""
        super().__init__()
        self._file_name: Optional[str] = None
        self._file_author: Optional[str] = None
        self._file_id: Optional[str] = None
        self._file_types: List[str] = []
        self._checksums: List[Hash] = []
        self._license_concluded: Optional[str] = None
        self._license_info_in_files: List[str] = []
        self._copyright_text: Optional[str] = None

    @property
    def file_id(self) -> str:
        """
        Get the current file identifier.

        Returns:
            str: The file ID string or None if not set
        """
        return self._file_id

    def with_file_name(self, file_name: str) -> 'FileBuilder':
        """
        Set the file name or path.

        Args:
            file_name: File name with relative path

        Returns:
            FileBuilder: self for method chaining
        """
        self._file_name = file_name
        return self

    def with_file_author(self, file_author: str) -> 'FileBuilder':
        """
        Set the file author information.

        Args:
            file_author: Author identification string in SPDX format

        Returns:
            FileBuilder: self for method chaining
        """
        self._file_author = file_author
        return self

    def with_file_id(self, file_id: str) -> 'FileBuilder':
        """
        Set the unique file identifier.

        Args:
            file_id: Unique identifier string

        Returns:
            FileBuilder: self for method chaining
        """
        self._file_id = file_id
        return self

    def with_file_type(self, file_type: Literal[
        "SOURCE", "BINARY", "TEXT", "IMAGE", "AUDIO", "VIDEO",
        "APPLICATION", "ML_MODEL", "SBOM", "OTHER"]) -> 'FileBuilder':
        """
        Add a file type classification.

        Args:
            file_type: One of the predefined file type constants:
                      - "SOURCE": Source code file
                      - "BINARY": Compiled binary
                      - "TEXT": Documentation or plain text
                      - "IMAGE": Image file
                      - "AUDIO": Audio file
                      - "VIDEO": Video file
                      - "APPLICATION": Executable application
                      - "ML_MODEL": Machine learning model
                      - "SBOM": SBOM document
                      - "OTHER": Other file type

        Returns:
            FileBuilder: self for method chaining
        """
        self._file_types.append(file_type)
        return self

    def with_checksum(self, alg: str, content: str) -> 'FileBuilder':
        """
        Add a single checksum for the file.

        Args:
            alg: Hash algorithm
            content: Hexadecimal hash value

        Returns:
            FileBuilder: self for method chaining
        """
        self._checksums.append(Hash(alg=alg, content=content))
        return self

    def with_checksums(self, checksums: List[Union[Tuple[str, str], 'Hash']]) -> 'FileBuilder':
        """
        Add multiple checksums for the file.

        Args:
            checksums: List of checksums where each can be:
                      - Tuple of (algorithm, hash_value)
                      - Hash object

        Returns:
            FileBuilder: self for method chaining
        """
        self._checksums = [
            h if isinstance(h, Hash) else Hash(alg=h[0], content=h[1])
            for h in checksums
        ]
        return self

    def with_license_concluded(self, license_concluded: str) -> 'FileBuilder':
        """
        Set the concluded license for the file.

        Args:
            license_concluded: SPDX license identifier

        Returns:
            FileBuilder: self for method chaining
        """
        self._license_concluded = license_concluded
        return self

    def with_license_info_in_files(self, license_info: List[str]) -> 'FileBuilder':
        """
        Set all license information found in the file.

        Args:
            license_info: List of SPDX license identifiers

        Returns:
            FileBuilder: self for method chaining
        """
        self._license_info_in_files = license_info
        return self

    def add_license_info_in_file(self, license_info: str) -> 'FileBuilder':
        """
        Add a single license information entry for the file.

        Args:
            license_info: SPDX license identifier

        Returns:
            FileBuilder: self for method chaining
        """
        self._license_info_in_files.append(license_info)
        return self

    def with_copyright_text(self, copyright_text: str) -> 'FileBuilder':
        """
        Set the copyright notice for the file.

        Args:
            copyright_text: Copyright declaration text

        Returns:
            FileBuilder: self for method chaining
        """
        self._copyright_text = copyright_text
        return self

    def _build_instance(self) -> File:
        """
        Construct the File instance with current configuration.

        Returns:
            File: A new File instance with all configured values

        Note:
            Uses deepcopy for all collection-type fields to prevent reference sharing
        """
        return File(
            file_name=self._file_name,
            file_author=deepcopy(self._file_author),
            file_id=self._file_id,
            file_types=deepcopy(self._file_types),
            checksums=deepcopy(self._checksums),
            license_concluded=self._license_concluded,
            license_info_in_files=deepcopy(self._license_info_in_files),
            copyright_text=deepcopy(self._copyright_text)
        )
