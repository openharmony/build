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

from typing import List, Set, Optional

from ohos.sbom.sbom.builder.base_builder import CompositeBuilder
from ohos.sbom.sbom.builder.document_builder import DocumentBuilder
from ohos.sbom.sbom.builder.file_builder import FileBuilder
from ohos.sbom.sbom.builder.package_builder import PackageBuilder
from ohos.sbom.sbom.builder.relationship_builder import RelationshipBuilder
from ohos.sbom.sbom.metadata.sbom_meta_data import SBOMMetaData


class SBOMMetaDataBuilder(CompositeBuilder):
    """
    Composite builder for constructing complete SBOM metadata documents.

    Coordinates the construction of:
    - Document information
    - Package components
    - File components
    - Relationships between components

    Implements hierarchical validation and reference integrity checking.
    """

    def __init__(self):
        """Initialize a new SBOM metadata builder with empty component lists."""
        super().__init__()
        self._document: Optional[DocumentBuilderContext] = None
        self._packages: List[PackageBuilder] = []
        self._files: List[FileBuilder] = []
        self._relationships: List[RelationshipBuilder] = []

    def start_document(self) -> "DocumentBuilderContext":
        """
        Begin building document metadata using fluent interface.

        Returns:
            DocumentBuilderContext: A document builder for method chaining

        Note:
            Only one document can be created per SBOM
        """
        if self._document is None:
            self._document = DocumentBuilderContext(self)
            self.add_child_builder(self._document)
        return self._document

    def start_package(self) -> "PackageBuilderContext":
        """
        Begin building a package component using fluent interface.

        Returns:
            PackageBuilderContext: A package builder for method chaining
        """
        builder = PackageBuilderContext(self)
        self._packages.append(builder)
        self.add_child_builder(builder)
        return builder

    def start_file(self) -> "FileBuilderContext":
        """
        Begin building a file component using fluent interface.

        Returns:
            FileBuilderContext: A file builder for method chaining
        """
        builder = FileBuilderContext(self)
        self._files.append(builder)
        self.add_child_builder(builder)
        return builder

    def start_relationship(self) -> "RelationshipBuilderContext":
        """
        Begin building a relationship between components.

        Returns:
            RelationshipBuilderContext: A relationship builder for method chaining
        """
        builder = RelationshipBuilderContext(self)
        self._relationships.append(builder)
        self.add_child_builder(builder)
        return builder

    def add_package(self, package: PackageBuilder) -> "SBOMMetaDataBuilder":
        """
        Add a pre-built package component to the SBOM.

        Args:
            package: Pre-configured PackageBuilder instance

        Returns:
            SBOMMetaDataBuilder: self for method chaining
        """
        self._packages.append(package)
        self.add_child_builder(package)
        return self

    def add_file(self, file: FileBuilder) -> "SBOMMetaDataBuilder":
        """
        Add a pre-built file component to the SBOM.

        Args:
            file: Pre-configured FileBuilder instance

        Returns:
            SBOMMetaDataBuilder: self for method chaining
        """
        self._files.append(file)
        self.add_child_builder(file)
        return self

    def add_relationship(self, relationship: RelationshipBuilder) -> "SBOMMetaDataBuilder":
        """
        Add a pre-built relationship to the SBOM.

        Args:
            relationship: Pre-configured RelationshipBuilder instance

        Returns:
            SBOMMetaDataBuilder: self for method chaining
        """
        self._relationships.append(relationship)
        self.add_child_builder(relationship)
        return self

    def _build_instance(self) -> SBOMMetaData:
        """
        Construct the complete SBOM metadata document.

        Returns:
            SBOMMetaData: The fully assembled SBOM metadata

        Raises:
            ValueError: If required document information is missing
        """
        if self._document is None:
            raise ValueError("Document metadata must be provided")

        return SBOMMetaData(
            document=self._document.build(validate=False),
            packages=[p.build(validate=False) for p in self._packages],
            files=[f.build(validate=False) for f in self._files],
            relationships=[r.build(validate=False) for r in self._relationships]
        )

    def _validate(self) -> None:
        """
        Perform hierarchical validation of the SBOM structure.

        Raises:
            ValueError: If any validation rules are violated
        """
        super()._validate()

        errors = []
        errors.extend(self._validate_business_rules())
        errors.extend(self._validate_references())

        if errors:
            raise ValueError("\n".join(errors))

    def _validate_business_rules(self) -> List[str]:
        """
        Validate SBOM business rules.

        Returns:
            List[str]: List of validation error messages

        Rules checked:
        - SBOM must contain at least one component (package or file)
        """
        errors = []
        if not (self._packages or self._files):
            errors.append("SBOM must contain at least one component (package or file)")
        return errors

    def _validate_references(self) -> List[str]:
        """
        Validate all relationship references point to existing components.

        Returns:
            List[str]: List of invalid reference error messages
        """
        errors = []
        valid_refs = self._collect_valid_references()

        for rel in self._relationships:
            for ref in getattr(rel, '_depends_on', []):
                if ref not in valid_refs:
                    errors.append(f"Invalid reference: {ref} (no matching component)")
        return errors

    def _collect_valid_references(self) -> Set[str]:
        """
        Collect all valid component references in the SBOM.

        Returns:
            Set[str]: Set of all valid bom-ref and file-id values
        """
        refs = set()
        for pkg in self._packages:
            if pkg.bom_ref:
                refs.add(pkg.bom_ref)
        for file in self._files:
            if file.file_id:
                refs.add(file.file_id)
        return refs


class BuilderContext:
    """Base class for builder contexts providing parent reference and end() method."""

    def __init__(self, parent: SBOMMetaDataBuilder):
        """
        Initialize a new builder context.

        Args:
            parent: The parent SBOMMetaDataBuilder instance
        """
        self._parent_builder = parent

    @property
    def parent_builder(self) -> 'SBOMMetaDataBuilder':
        """Get the parent SBOM metadata builder."""
        return self._parent_builder

    def end(self) -> 'SBOMMetaDataBuilder':
        """
        Exit the current builder context and return to parent builder.

        Returns:
            SBOMMetaDataBuilder: The parent builder for continued fluent configuration
        """
        return self._parent_builder


class DocumentBuilderContext(DocumentBuilder, BuilderContext):
    """Context manager for document building with fluent interface."""

    def __init__(self, parent):
        DocumentBuilder.__init__(self)
        BuilderContext.__init__(self, parent)


class FileBuilderContext(FileBuilder, BuilderContext):
    """Context manager for file component building with fluent interface."""

    def __init__(self, parent):
        FileBuilder.__init__(self)
        BuilderContext.__init__(self, parent)


class PackageBuilderContext(PackageBuilder, BuilderContext):
    """Context manager for package component building with fluent interface."""

    def __init__(self, parent):
        PackageBuilder.__init__(self)
        BuilderContext.__init__(self, parent)


class RelationshipBuilderContext(RelationshipBuilder, BuilderContext):
    """Context manager for relationship building with fluent interface."""

    def __init__(self, parent):
        RelationshipBuilder.__init__(self)
        BuilderContext.__init__(self, parent)
