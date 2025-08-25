from copy import deepcopy
from typing import List, Optional

from ohos.sbom.sbom.builder.base_builder import ConfigurableBuilder
from ohos.sbom.sbom.metadata.sbom_meta_data import RelationshipType, Relationship


class RelationshipBuilder(ConfigurableBuilder):
    """
    Builder class for creating relationship entries in SBOM documents.

    Implements fluent interface pattern for defining dependencies between components.
    Uses 'relationship' configuration from FieldConfigManager by default.
    """

    CONFIG_NAME = "relationship"

    def __init__(self):
        """Initialize a new RelationshipBuilder with all fields set to None/empty."""
        super().__init__()
        self._bom_ref: Optional[str] = None
        self._depends_on: List[str] = []
        self._relationship_type: Optional[RelationshipType] = None

    def with_bom_ref(self, bom_ref: str) -> 'RelationshipBuilder':
        """
        Set the source component reference for this relationship.

        Args:
            bom_ref: Unique reference of the source component
                    (typically matches a package's bom-ref)

        Returns:
            RelationshipBuilder: self for method chaining
        """
        self._bom_ref = bom_ref
        return self

    def with_depends_on(self, depends_on: List[str]) -> 'RelationshipBuilder':
        """
        Set all target components this relationship points to.

        Args:
            depends_on: List of target component references
                       (typically package bom-refs)

        Returns:
            RelationshipBuilder: self for method chaining
        """
        self._depends_on = depends_on
        return self

    def add_depends_on(self, depends_on: str) -> 'RelationshipBuilder':
        """
        Add a single target component to this relationship.

        Args:
            depends_on: Target component reference to add
                       (typically a package bom-ref)

        Returns:
            RelationshipBuilder: self for method chaining
        """
        self._depends_on.append(depends_on)
        return self

    def with_relationship_type(self, relationship_type: RelationshipType) -> 'RelationshipBuilder':
        """
        Set the relationship type using enum value.

        Args:
            relationship_type: RelationshipType enum value
                              (e.g. RelationshipType.DEPENDS_ON)

        Returns:
            RelationshipBuilder: self for method chaining
        """
        self._relationship_type = relationship_type
        return self

    def with_relationship_type_str(self, relationship_type: str) -> 'RelationshipBuilder':
        """
        Set the relationship type using string value.

        Args:
            relationship_type: Relationship type as string
                              (e.g. "DEPENDS_ON", "CONTAINS")

        Returns:
            RelationshipBuilder: self for method chaining

        Raises:
            ValueError: If the string doesn't match any RelationshipType value
        """
        self._relationship_type = RelationshipType(relationship_type)
        return self

    def _build_instance(self) -> Relationship:
        """
        Construct the Relationship instance with current configuration.

        Returns:
            Relationship: A new Relationship instance with all configured values

        Note:
            Uses deepcopy for collection fields to prevent reference sharing
        """
        return Relationship(
            bom_ref=self._bom_ref,
            depends_on=deepcopy(self._depends_on),
            relationship_type=self._relationship_type
        )
