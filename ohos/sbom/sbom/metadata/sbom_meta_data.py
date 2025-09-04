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
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any

from ohos.sbom.common.utils import remove_empty

# SPDX standard value indicating no license assertion
NOASSERTION = "NOASSERTION"


# ---------------------------
# Core Value Objects
# ---------------------------
@dataclass(frozen=True)
class Hash:
    """
    Represents a cryptographic hash value for file/package verification.

    Attributes:
        alg: Hash algorithm (e.g. "SHA256", "MD5")
        content: Hexadecimal hash value
    """
    alg: str
    content: str

    def __json__(self) -> Dict[str, str]:
        """Support JSON module serialization."""
        return self.to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'Hash':
        """Create Hash from dictionary."""
        return cls(
            alg=data.get('alg', ''),
            content=data.get('content', '')
        )

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary representation."""
        return {
            "alg": self.alg,
            "content": self.content
        }


class RelationshipType(Enum):
    """
    Enumeration of standard SBOM relationship types between components.

    Values:
        CONTAINS: The source contains the target
        CONTAINED_BY: The source is contained by the target
        DEPENDS_ON: The source depends on the target
        DEPENDENCY_OF: The source is a dependency of the target
        GENERATES: The source generates the target
        GENERATED_FROM: The source was generated from the target
        VARIANT_OF: The source is a variant of the target
        COPY_OF: The source is a copy of the target
        DYNAMIC_LINK: The source dynamically links to the target
        STATIC_LINK: The source statically links to the target
        OTHER: Other relationship type
    """
    CONTAINS = "CONTAINS"
    CONTAINED_BY = "CONTAINED_BY"
    DEPENDS_ON = "DEPENDS_ON"
    DEPENDENCY_OF = "DEPENDENCY_OF"
    GENERATES = "GENERATES"
    GENERATED_FROM = "GENERATED_FROM"
    VARIANT_OF = "VARIANT_OF"
    COPY_OF = "COPY_OF"
    DYNAMIC_LINK = "DYNAMIC_LINK"
    STATIC_LINK = "STATIC_LINK"
    OTHER = "OTHER"

    @classmethod
    def from_str(cls, value: str) -> 'RelationshipType':
        """Create from string value."""
        try:
            return cls(value)
        except ValueError:
            return cls.OTHER


# ---------------------------
# Document Creation Information
# ---------------------------
@dataclass(frozen=True)
class Document:
    """
    Represents SBOM document metadata and creation information.

    Required fields:
        serial_number: Unique document identifier (typically UUID)
        version: Document version
        bom_format: BOM format specification
        spec_version: Specification version
        data_license: License for the document metadata
        timestamp: Creation timestamp (ISO 8601 format)
        authors: List of document authors

    Optional fields:
        doc_id: SPDX document identifier
        name: Document name
        document_namespace: Unique document namespace URI
        license_list_version: SPDX license list version
        lifecycles: List of lifecycle phases
        properties: Custom key-value properties
        tools: List of tools used to generate the SBOM
        doc_comments: Free-form comments
    """
    # Required fields
    serial_number: str
    version: str
    bom_format: str
    spec_version: str
    data_license: str
    timestamp: str
    authors: List[str]

    # SPDX-specific fields
    doc_id: Optional[str]
    name: Optional[str]
    document_namespace: Optional[str]
    license_list_version: Optional[str]

    # Optional fields
    lifecycles: List[str] = field(default_factory=list)
    properties: Dict[str, str] = field(default_factory=dict)
    tools: List[Dict[str, str]] = field(default_factory=list)
    doc_comments: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """Create Document from dictionary."""
        return cls(
            serial_number=data.get('serialNumber', ''),
            version=data.get('version', ''),
            bom_format=data.get('bomFormat', ''),
            spec_version=data.get('specVersion', ''),
            data_license=data.get('dataLicense', ''),
            timestamp=data.get('timestamp', ''),
            authors=data.get('authors', []),
            doc_id=data.get('docId'),
            name=data.get('name'),
            document_namespace=data.get('documentNamespace'),
            license_list_version=data.get('licenseListVersion'),
            lifecycles=data.get('lifecycles', []),
            properties=data.get('properties', {}),
            tools=data.get('tools', []),
            doc_comments=data.get('docComments')
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to ordered dictionary following standard field order.

        Returns:
            OrderedDict: Document data with empty values removed
        """
        data = OrderedDict([
            ("serialNumber", self.serial_number),
            ("docId", self.doc_id),
            ("name", self.name),
            ("documentNamespace", self.document_namespace),
            ("version", self.version),
            ("bomFormat", self.bom_format),
            ("specVersion", self.spec_version),
            ("dataLicense", self.data_license),
            ("licenseListVersion", self.license_list_version),
            ("timestamp", self.timestamp),
            ("authors", self.authors),
            ("lifecycles", self.lifecycles),
            ("properties", self.properties),
            ("tools", self.tools),
            ("docComments", self.doc_comments)
        ])
        return remove_empty(data)


# ---------------------------
# Package Information
# ---------------------------
@dataclass(frozen=True)
class Package:
    """
    Represents a software package in the SBOM.

    Required fields:
        type: Package type (e.g. "library", "application")
        supplier: Package supplier/originator
        group: Package group/namespace
        name: Package name
        version: Package version
        purl: Package URL identifier
        license_concluded: Concluded license
        license_declared: Declared license
        bom_ref: Unique package reference
        comp_platform: Target platform

    Optional fields:
        com_copyright: Copyright notice
        download_location: Package download URL
        hashes: List of cryptographic hashes
    """
    type: str
    supplier: str
    group: str
    name: str
    version: str
    purl: str
    license_concluded: str
    license_declared: str
    bom_ref: str
    comp_platform: str

    # Optional fields
    com_copyright: Optional[str] = None
    download_location: Optional[str] = None
    hashes: List[Hash] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Package':
        """Create Package from dictionary."""
        return cls(
            type=data.get('type', ''),
            supplier=data.get('supplier', ''),
            group=data.get('group', ''),
            name=data.get('name', ''),
            version=data.get('version', ''),
            purl=data.get('purl', ''),
            license_concluded=data.get('licenseConcluded', ''),
            license_declared=data.get('licenseDeclared', ''),
            bom_ref=data.get('bom-ref', ''),
            comp_platform=data.get('compPlatform', ''),
            com_copyright=data.get('comCopyright'),
            download_location=data.get('downloadLocation'),
            hashes=[Hash.from_dict(h) for h in data.get('hashes', [])]
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to ordered dictionary following standard field order.

        Returns:
            OrderedDict: Package data with empty values removed
        """
        data = OrderedDict([
            ("type", self.type),
            ("supplier", self.supplier),
            ("group", self.group),
            ("name", self.name),
            ("version", self.version),
            ("purl", self.purl),
            ("licenseConcluded", self.license_concluded),
            ("licenseDeclared", self.license_declared),
            ("comCopyright", self.com_copyright),
            ("bom-ref", self.bom_ref),
            ("downloadLocation", self.download_location),
            ("hashes", [h.to_dict() for h in self.hashes]),
            ("compPlatform", self.comp_platform)
        ])
        return remove_empty(data)


# ---------------------------
# File Information
# ---------------------------
@dataclass(frozen=True)
class File:
    """
    Represents a file in the SBOM.

    Required fields:
        file_name: File name with path
        file_id: Unique file identifier
        checksums: List of cryptographic hashes
        license_concluded: Concluded license

    Optional fields:
        file_types: List of file types
        file_author: File author
        license_info_in_files: Licenses found in file
        copyright_text: Copyright notice
    """
    file_name: str
    file_id: str
    checksums: List['Hash']
    license_concluded: str
    file_types: List[str] = field(default_factory=list)
    file_author: Optional[str] = None
    license_info_in_files: List[str] = field(default_factory=list)
    copyright_text: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'File':
        """Create File from dictionary."""
        return cls(
            file_name=data.get('fileName', ''),
            file_id=data.get('fileId', ''),
            checksums=[Hash.from_dict(h) for h in data.get('checksums', [])],
            license_concluded=data.get('licenseConcluded', ''),
            file_types=data.get('fileTypes', []),
            file_author=data.get('fileAuthor'),
            license_info_in_files=data.get('licenseInfoInFiles', []),
            copyright_text=data.get('copyrightText')
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to ordered dictionary following standard field order.

        Returns:
            OrderedDict: File data with empty values removed
        """
        data = OrderedDict([
            ("fileName", self.file_name),
            ("fileAuthor", self.file_author),
            ("fileId", self.file_id),
            ("fileTypes", self.file_types),
            ("checksums", [h.to_dict() for h in self.checksums]),
            ("licenseConcluded", self.license_concluded),
            ("licenseInfoInFiles", self.license_info_in_files),
            ("copyrightText", self.copyright_text)
        ])
        return remove_empty(data)


# ---------------------------
# Relationship Information
# ---------------------------
@dataclass(frozen=True)
class Relationship:
    """
    Represents a relationship between SBOM components.

    Attributes:
        bom_ref: Source component reference
        depends_on: List of target component references
        relationship_type: Type of relationship
    """
    bom_ref: str
    depends_on: List[str]
    relationship_type: RelationshipType

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Relationship':
        """Create Relationship from dictionary."""
        return cls(
            bom_ref=data.get('bom-ref', ''),
            depends_on=data.get('dependsOn', []),
            relationship_type=RelationshipType.from_str(data.get('relationshipType', 'OTHER'))
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to ordered dictionary following standard field order.

        Returns:
            OrderedDict: Relationship data with empty values removed
        """
        data = OrderedDict([
            ("bom-ref", self.bom_ref),
            ("dependsOn", self.depends_on),
            ("relationshipType", self.relationship_type.value)
        ])
        return remove_empty(data)


# ---------------------------
# SBOM Metadata
# ---------------------------
@dataclass(frozen=True)
class SBOMMetaData:
    """
    Complete SBOM document containing all metadata components.

    Attributes:
        document: Document creation information
        packages: List of software packages
        files: List of files
        relationships: List of component relationships
    """
    document: Document
    packages: List[Package] = field(default_factory=list)
    files: List[File] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SBOMMetaData':
        """Create SBOMMetaData from dictionary."""
        return cls(
            document=Document.from_dict(data.get('document', {})),
            packages=[Package.from_dict(p) for p in data.get('packages', [])],
            files=[File.from_dict(f) for f in data.get('files', [])],
            relationships=[Relationship.from_dict(r) for r in data.get('relationships', [])]
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert complete SBOM to ordered dictionary.

        Returns:
            OrderedDict: SBOM data with empty values removed
        """
        data = OrderedDict([
            ("document", self.document.to_dict()),
            ("packages", [pkg.to_dict() for pkg in self.packages]),
            ("files", [file.to_dict() for file in self.files]),
            ("relationships", [rel.to_dict() for rel in self.relationships])
        ])
        return remove_empty(data)
