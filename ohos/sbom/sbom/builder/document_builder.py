from copy import deepcopy
from typing import List, Dict, Optional

from ohos.sbom.sbom.builder.base_builder import ConfigurableBuilder
from ohos.sbom.sbom.metadata.sbom_meta_data import Document


class DocumentBuilder(ConfigurableBuilder):
    """
    Builder class for creating SBOM document metadata.

    Implements fluent interface pattern for easy configuration of document properties.
    Uses 'document' configuration from FieldConfigManager by default.
    """

    CONFIG_NAME = "document"

    def __init__(self):
        """Initialize a new DocumentBuilder with all fields set to None/empty."""
        super().__init__()
        self._version: Optional[str] = None
        self._bom_format: Optional[str] = None
        self._spec_version: Optional[str] = None
        self._data_license: Optional[str] = None
        self._serial_number: Optional[str] = None
        self._timestamp: Optional[str] = None
        self._authors: List[str] = []
        self._doc_id: Optional[str] = None
        self._name: Optional[str] = None
        self._document_namespace: Optional[str] = None
        self._license_list_version: Optional[str] = None
        self._lifecycles: List[str] = []
        self._properties: Dict[str, str] = {}
        self._tools: List[Dict[str, str]] = []
        self._doc_comments: Optional[str] = None

    def _build_instance(self) -> Document:
        """
        Construct the Document instance with current configuration.

        Returns:
            Document: A new Document instance with all configured values

        Note:
            Uses deepcopy for all collection-type fields to prevent reference sharing
        """
        return Document(
            version=self._version,
            bom_format=self._bom_format,
            spec_version=self._spec_version,
            data_license=self._data_license,
            serial_number=self._serial_number,
            timestamp=self._timestamp,
            authors=deepcopy(self._authors),
            doc_id=self._doc_id,
            name=self._name,
            document_namespace=self._document_namespace,
            license_list_version=self._license_list_version,
            lifecycles=deepcopy(self._lifecycles),
            properties=deepcopy(self._properties),
            tools=deepcopy(self._tools),
            doc_comments=deepcopy(self._doc_comments),
        )

    def with_version(self, version: str) -> 'DocumentBuilder':
        """
        Set the document version.

        Args:
            version: Version string

        Returns:
            DocumentBuilder: self for method chaining
        """
        self._version = version
        return self

    def with_bom_format(self, bom_format: str) -> 'DocumentBuilder':
        """
        Set the BOM format specification.

        Args:
            bom_format: Standard specification used

        Returns:
            DocumentBuilder: self for method chaining
        """
        self._bom_format = bom_format
        return self

    def with_spec_version(self, spec_version: str) -> 'DocumentBuilder':
        """
        Set the specification version.

        Args:
            spec_version: Version string of the specification

        Returns:
            DocumentBuilder: self for method chaining
        """
        self._spec_version = spec_version
        return self

    def with_data_license(self, data_license: str) -> 'DocumentBuilder':
        """
        Set the data license for the document.

        Args:
            data_license: License identifier

        Returns:
            DocumentBuilder: self for method chaining
        """
        self._data_license = data_license
        return self

    def with_serial_number(self, serial_number: str) -> 'DocumentBuilder':
        """
        Set the document serial number (typically a UUID).

        Args:
            serial_number: Unique identifier string

        Returns:
            DocumentBuilder: self for method chaining
        """
        self._serial_number = serial_number
        return self

    def with_timestamp(self, timestamp: str) -> 'DocumentBuilder':
        """
        Set the document creation timestamp.

        Args:
            timestamp: ISO 8601 formatted timestamp string

        Returns:
            DocumentBuilder: self for method chaining
        """
        self._timestamp = timestamp
        return self

    def with_author(self, author: str) -> 'DocumentBuilder':
        """
        Add a single author to the document.

        Args:
            author: Author identification string

        Returns:
            DocumentBuilder: self for method chaining
        """
        self._authors.append(author)
        return self

    def with_authors(self, authors: List[str]) -> 'DocumentBuilder':
        """
        Add multiple authors to the document.

        Args:
            authors: List of author identification strings

        Returns:
            DocumentBuilder: self for method chaining
        """
        self._authors.extend(authors)
        return self

    def with_doc_id(self, doc_id: str) -> 'DocumentBuilder':
        """
        Set the document identifier.

        Args:
            doc_id: Unique document ID string

        Returns:
            DocumentBuilder: self for method chaining
        """
        self._doc_id = doc_id
        return self

    def with_name(self, name: str) -> 'DocumentBuilder':
        """
        Set the document name.

        Args:
            name: Descriptive name string

        Returns:
            DocumentBuilder: self for method chaining
        """
        self._name = name
        return self

    def with_document_namespace(self, namespace: str) -> 'DocumentBuilder':
        """
        Set the document namespace URI.

        Args:
            namespace: Unique namespace URI string

        Returns:
            DocumentBuilder: self for method chaining
        """
        self._document_namespace = namespace
        return self

    def with_license_list_version(self, version: str) -> 'DocumentBuilder':
        """
        Set the license list version used.

        Args:
            version: License list version string

        Returns:
            DocumentBuilder: self for method chaining
        """
        self._license_list_version = version
        return self

    def with_lifecycle(self, phase: str) -> 'DocumentBuilder':
        """
        Add a single lifecycle phase.

        Args:
            phase: Lifecycle phase (e.g. "design", "development")

        Returns:
            DocumentBuilder: self for method chaining
        """
        self._lifecycles.append(phase)
        return self

    def with_lifecycles(self, phases: List[str]) -> 'DocumentBuilder':
        """
        Add multiple lifecycle phases.

        Args:
            phases: List of lifecycle phase strings

        Returns:
            DocumentBuilder: self for method chaining
        """
        self._lifecycles.extend(phases)
        return self

    def with_property(self, key: str, value: str) -> 'DocumentBuilder':
        """
        Add a single custom property.

        Args:
            key: Property name
            value: Property value

        Returns:
            DocumentBuilder: self for method chaining
        """
        self._properties[key] = value
        return self

    def with_properties(self, props: Dict[str, str]) -> 'DocumentBuilder':
        """
        Add multiple custom properties.

        Args:
            props: Dictionary of property key-value pairs

        Returns:
            DocumentBuilder: self for method chaining
        """
        self._properties.update(props)
        return self

    def with_tool(self, vendor: str, name: str, version: str) -> 'DocumentBuilder':
        """
        Add a tool used to generate the SBOM.

        Args:
            vendor: Tool vendor/organization
            name: Tool name
            version: Tool version

        Returns:
            DocumentBuilder: self for method chaining
        """
        self._tools.append({
            "vendor": vendor,
            "name": name,
            "version": version
        })
        return self

    def with_tools(self, tools: List[Dict]) -> 'DocumentBuilder':
        """
        Add multiple tools used to generate the SBOM.

        Args:
            tools: List of tool dictionaries (must contain vendor/name/version)

        Returns:
            DocumentBuilder: self for method chaining

        Note:
            Only extracts vendor, name, and version fields from each tool dictionary
        """
        self._tools.extend([
            {k: tool.get(k) for k in ("vendor", "name", "version")}
            for tool in tools
        ])
        return self

    def with_doc_comments(self, comments: str) -> 'DocumentBuilder':
        """
        Set document comments/notes.

        Args:
            comments: Free-form comment text

        Returns:
            DocumentBuilder: self for method chaining
        """
        self._doc_comments = comments
        return self
