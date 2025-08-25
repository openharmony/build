from copy import deepcopy
from typing import List, Optional, Literal, Union, Tuple

from ohos.sbom.sbom.builder.base_builder import ConfigurableBuilder
from ohos.sbom.sbom.metadata.sbom_meta_data import Package, Hash


class PackageBuilder(ConfigurableBuilder):
    """
    Builder class for creating Package metadata in SBOM documents.

    Implements fluent interface pattern for easy configuration of package properties.
    Uses 'package' configuration from FieldConfigManager by default.
    """

    CONFIG_NAME = "package"

    def __init__(self):
        """Initialize a new PackageBuilder with all fields set to None/empty."""
        super().__init__()
        self._type: Optional[str] = None
        self._supplier: Optional[str] = None
        self._group: Optional[str] = None
        self._name: Optional[str] = None
        self._version: Optional[str] = None
        self._purl: Optional[str] = None
        self._license_concluded: Optional[str] = None
        self._license_declared: Optional[str] = None
        self._com_copyright: Optional[str] = None
        self._bom_ref: Optional[str] = None
        self._download_location: Optional[str] = None
        self._hashes: List[Hash] = []
        self._comp_platform: Optional[str] = None

    @property
    def bom_ref(self) -> str:
        """
        Get the current BOM reference identifier.

        Returns:
            str: The BOM reference string or None if not set
        """
        return self._bom_ref

    def with_type(self, type_: Literal["library", "application", "framework"]) -> 'PackageBuilder':
        """
        Set the package type.

        Args:
            type_: Package type, one of:
                  - "library": Software library/dependency
                  - "application": Executable application
                  - "framework": Development framework

        Returns:
            PackageBuilder: self for method chaining
        """
        self._type = type_
        return self

    def with_supplier(self, supplier: str) -> 'PackageBuilder':
        """
        Set the package supplier information.

        Args:
            supplier: Supplier identification string in SPDX format

        Returns:
            PackageBuilder: self for method chaining
        """
        self._supplier = supplier
        return self

    def with_group(self, group: str) -> 'PackageBuilder':
        """
        Set the package group/namespace.

        Args:
            group: Group identifier

        Returns:
            PackageBuilder: self for method chaining
        """
        self._group = group
        return self

    def with_name(self, name: str) -> 'PackageBuilder':
        """
        Set the package name.

        Args:
            name: Package name

        Returns:
            PackageBuilder: self for method chaining
        """
        self._name = name
        return self

    def with_version(self, version: str) -> 'PackageBuilder':
        """
        Set the package version.

        Args:
            version: Version string

        Returns:
            PackageBuilder: self for method chaining
        """
        self._version = version
        return self

    def with_purl(self, purl: str) -> 'PackageBuilder':
        """
        Set the package URL (purl).

        Args:
            purl: Package URL identifier

        Returns:
            PackageBuilder: self for method chaining

        See:
            https://github.com/package-url/purl-spec
        """
        self._purl = purl
        return self

    def with_license_concluded(self, license_concluded: str) -> 'PackageBuilder':
        """
        Set the concluded license for the package.

        Args:
            license_concluded: SPDX license identifier

        Returns:
            PackageBuilder: self for method chaining
        """
        self._license_concluded = license_concluded
        return self

    def with_license_declared(self, license_declared: str) -> 'PackageBuilder':
        """
        Set the declared license for the package.

        Args:
            license_declared: SPDX license identifier

        Returns:
            PackageBuilder: self for method chaining
        """
        self._license_declared = license_declared
        return self

    def with_com_copyright(self, com_copyright: str) -> 'PackageBuilder':
        """
        Set the copyright notice for the package.

        Args:
            com_copyright: Copyright declaration text

        Returns:
            PackageBuilder: self for method chaining
        """
        self._com_copyright = com_copyright
        return self

    def with_bom_ref(self, bom_ref: str) -> 'PackageBuilder':
        """
        Set the BOM reference identifier for the package.

        Args:
            bom_ref: Unique reference string

        Returns:
            PackageBuilder: self for method chaining
        """
        self._bom_ref = bom_ref
        return self

    def with_download_location(self, location: str) -> 'PackageBuilder':
        """
        Set the package download location.

        Args:
            location: Download URL

        Returns:
            PackageBuilder: self for method chaining
        """
        self._download_location = location
        return self

    def with_hash(self, alg: str, content: str) -> 'PackageBuilder':
        """
        Add a single cryptographic hash for the package.

        Args:
            alg: Hash algorithm
            content: Hexadecimal hash value

        Returns:
            PackageBuilder: self for method chaining
        """
        self._hashes.append(Hash(alg=alg, content=content))
        return self

    def with_hashes(self, hashes: List[Union[Tuple[str, str], 'Hash']]) -> 'PackageBuilder':
        """
        Add multiple cryptographic hashes for the package.

        Args:
            hashes: List of hashes where each can be:
                   - Tuple of (algorithm, hash_value)
                   - Hash object

        Returns:
            PackageBuilder: self for method chaining
        """
        self._hashes = [
            h if isinstance(h, Hash) else Hash(alg=h[0], content=h[1])
            for h in hashes
        ]
        return self

    def with_comp_platform(self, platform: str) -> 'PackageBuilder':
        """
        Set the target platform for the package.

        Args:
            platform: Platform identifier

        Returns:
            PackageBuilder: self for method chaining
        """
        self._comp_platform = platform
        return self

    def _build_instance(self) -> Package:
        """
        Construct the Package instance with current configuration.

        Returns:
            Package: A new Package instance with all configured values

        Note:
            Uses deepcopy for all collection-type and string fields to prevent reference sharing
        """
        return Package(
            type=self._type,
            supplier=self._supplier,
            group=self._group,
            name=self._name,
            version=self._version,
            purl=self._purl,
            license_concluded=self._license_concluded,
            license_declared=self._license_declared,
            bom_ref=self._bom_ref,
            comp_platform=self._comp_platform,
            com_copyright=deepcopy(self._com_copyright),
            download_location=deepcopy(self._download_location),
            hashes=deepcopy(self._hashes),
        )