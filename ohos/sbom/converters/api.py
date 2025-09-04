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

from typing import Dict, Any, Type

from ohos.sbom.converters.base import SBOMFormat, SBOMConverterFactory, ISBOMConverter
from ohos.sbom.sbom.metadata.sbom_meta_data import SBOMMetaData


class SBOMConverter:
    """
    Main entry point for converting SBOM metadata between different formats.

    This class provides:
    1. On-demand conversion of SBOM metadata to various formats
    2. Registration mechanism for new format converters
    3. Factory-based converter instantiation
    """

    def __init__(self, sbom_meta: SBOMMetaData):
        """
        Initialize converter with SBOM metadata.

        Args:
            sbom_meta: The SBOM metadata object to be converted
        """
        self.sbom_meta = sbom_meta

    @staticmethod
    def register_format(sbom_format: SBOMFormat, converter: Type['ISBOMConverter']) -> None:
        """
        Register a new converter for a specific SBOM format.

        Args:
            sbom_format: Format to register (from SBOMFormat enum)
            converter: Converter class implementing ISBOMConverter interface
        """
        SBOMConverterFactory.register(sbom_format, converter)

    def convert(self, sbom_format: SBOMFormat) -> Dict[str, Any]:
        """
        Convert the SBOM metadata to the specified format.

        Args:
            sbom_format: Target format (from SBOMFormat enum)

        Returns:
            Dictionary containing the converted SBOM data
        """
        return SBOMConverterFactory.create(sbom_format).convert(self.sbom_meta)
