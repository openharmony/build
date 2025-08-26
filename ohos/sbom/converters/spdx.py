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

from collections import OrderedDict
from typing import Dict, Any

from ohos.sbom.common.utils import remove_empty
from ohos.sbom.converters.api import SBOMConverter
from ohos.sbom.converters.base import SBOMFormat, ISBOMConverter
from ohos.sbom.sbom.metadata.sbom_meta_data import Document, SBOMMetaData, Package, File, Hash, RelationshipType


class SPDX23Converter(ISBOMConverter):
    """
    Converter for SPDX 2.3 format (strictly follows input model and field mapping).

    Implements conversion from OpenHarmony SBOM metadata to SPDX 2.3 JSON format.
    """

    def convert(self, sbom_meta: SBOMMetaData) -> Dict[str, Any]:
        """
        Convert intermediate SBOM data to SPDX 2.3 format.

        Args:
            sbom_meta: Intermediate SBOM data containing document, packages,
                      files and relationships

        Returns:
            OrderedDict: SPDX 2.3 compliant dictionary with empty values removed
        """
        spdx = OrderedDict()

        # Document information
        spdx.update(self._convert_document(sbom_meta.document))

        # Package information
        if sbom_meta.packages:
            spdx["packages"] = [self._convert_package(pkg) for pkg in sbom_meta.packages]

        # File information
        if sbom_meta.files:
            spdx["files"] = [self._convert_file(file) for file in sbom_meta.files]

        # Relationship information
        if sbom_meta.relationships:
            spdx["relationships"] = [
                self._convert_single_relationship(rel.bom_ref, target, rel.relationship_type)
                for rel in sbom_meta.relationships
                for target in rel.depends_on
            ]

        return remove_empty(spdx)

    def _convert_document(self, doc: Document) -> Dict[str, Any]:
        """
        Convert document metadata to SPDX format.

        Args:
            doc: Document metadata object

        Returns:
            OrderedDict: SPDX document section
        """
        return OrderedDict([
            ("SPDXID", doc.doc_id or "SPDXRef-DOCUMENT"),
            ("spdxVersion", "2.3"),
            ("creationInfo", self._build_creation_info(doc)),
            ("name", doc.name or "Unnamed SBOM"),
            ("dataLicense", doc.data_license),
            ("documentNamespace", doc.document_namespace or self._generate_namespace(doc)),
            ("comment", doc.doc_comments)
        ])

    def _build_creation_info(self, doc: Document) -> Dict[str, Any]:
        """
        Build SPDX creationInfo section.

        Args:
            doc: Document metadata object

        Returns:
            OrderedDict: creationInfo section with creators and timestamps
        """
        creators = []
        if doc.tools:
            creators.extend([
                f"Tool: {tool.get('name', '')}-{tool.get('version', '')}"
                for tool in doc.tools
            ])
        creators.append("Organization: OpenHarmony")

        return OrderedDict([
            ("created", doc.timestamp),
            ("creators", creators),
            ("licenseListVersion", doc.license_list_version),
            ("comment", getattr(doc, 'doc_comments', None))
        ])

    def _generate_namespace(self, doc: Document) -> str:
        """
        Generate default document namespace URI.

        Args:
            doc: Document metadata object

        Returns:
            str: Generated namespace URI
        """
        return f"http://spdx.org/spdxdocs/{doc.name}-{doc.serial_number}"

    def _convert_package(self, pkg: Package) -> Dict[str, Any]:
        """
        Convert package metadata to SPDX format.

        Args:
            pkg: Package metadata object

        Returns:
            OrderedDict: SPDX package entry with all required fields

        Note:
            Automatically handles package purpose validation and fallback
        """
        # SPDX 2.3 valid package purposes
        valid_purposes = {
            "SOURCE", "BINARY", "ARCHIVE", "APPLICATION", "FRAMEWORK",
            "LIBRARY", "MODULE", "OPERATING-SYSTEM", "DEVICE", "FIRMWARE",
            "CONTAINER", "FILE", "INSTALL", "OTHER"
        }

        purpose = (pkg.type or "OTHER").upper()
        if purpose not in valid_purposes:
            purpose = "OTHER"

        pkg_data = OrderedDict([
            ("SPDXID", pkg.purl or f"SPDXRef-Package-{pkg.name}"),
            ("name", pkg.name),
            ("versionInfo", pkg.version),
            ("supplier", self._format_supplier(pkg.supplier)),
            ("originator", self._format_supplier(pkg.group) if pkg.group else None),
            ("downloadLocation", pkg.download_location or "NOASSERTION"),
            ("filesAnalyzed", False),  # SPDX recommendation for SBOMs
            ("licenseConcluded", pkg.license_concluded),
            ("licenseDeclared", pkg.license_declared),
            ("copyrightText", pkg.com_copyright or "NOASSERTION"),
            ("externalRefs", [self._build_purl_ref(pkg.purl)] if pkg.purl else []),
            ("checksums", [self._convert_hash(h) for h in pkg.hashes]),
            ("primaryPackagePurpose", purpose)
        ])
        return remove_empty(pkg_data)

    def _convert_file(self, file: File) -> Dict[str, Any]:
        """
        Convert file metadata to SPDX format.

        Args:
            file: File metadata object

        Returns:
            OrderedDict: SPDX file entry with all required fields
        """
        file_data = OrderedDict([
            ("SPDXID", file.file_id),
            ("fileName", file.file_name),
            ("fileTypes", [t.upper() for t in file.file_types]),
            ("checksums", [self._convert_hash(h) for h in file.checksums]),
            ("licenseConcluded", file.license_concluded),
            ("copyrightText", file.copyright_text or "NOASSERTION"),
        ])
        return remove_empty(file_data)

    def _convert_single_relationship(self, subject_id: str, target_id: str, rel_type: RelationshipType) -> Dict[
        str, Any]:
        """
        Convert relationship to SPDX format.

        Args:
            subject_id: Source component ID
            target_id: Target component ID
            rel_type: Relationship type enum

        Returns:
            OrderedDict: SPDX relationship entry
        """
        return OrderedDict([
            ("spdxElementId", subject_id),
            ("relatedSpdxElement", target_id),
            ("relationshipType", rel_type.value)
        ])

    def _format_supplier(self, supplier: str) -> str:
        """
        Format supplier information according to SPDX spec.

        Args:
            supplier: Raw supplier string

        Returns:
            str: Formatted supplier string (with Person: prefix if contains @)
        """
        if not supplier:
            return "NOASSERTION"
        return f"Person: {supplier}" if "@" in supplier else supplier

    def _build_purl_ref(self, purl: str) -> Dict[str, str]:
        """
        Build SPDX external reference for Package URL.

        Args:
            purl: Package URL string

        Returns:
            dict: SPDX external reference structure
        """
        return {
            "referenceType": "purl",
            "referenceLocator": purl
        }

    def _convert_hash(self, hash_obj: Hash) -> Dict[str, str]:
        """
        Convert hash object to SPDX format.

        Args:
            hash_obj: Hash object with algorithm and value

        Returns:
            dict: SPDX checksum structure
        """
        return {
            "algorithm": hash_obj.alg.upper(),
            "checksumValue": hash_obj.content
        }


# Register the converter with the factory
SBOMConverter.register_format(SBOMFormat.SPDX, SPDX23Converter)
