from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Type, List

from ohos.sbom.sbom.metadata.sbom_meta_data import SBOMMetaData


class SBOMFormat(Enum):
    """
    Enumeration of supported SBOM formats.

    Currently supported formats:
        - SPDX: Software Package Data Exchange format
    """
    SPDX = "SPDX"


class ISBOMConverter(ABC):
    """
    Abstract base class defining the interface for SBOM format converters.

    All concrete SBOM converters must implement this interface.
    """

    @abstractmethod
    def convert(self, sbom_meta: SBOMMetaData) -> Dict[str, Any]:
        """
        Convert SBOM metadata to the target format.

        Args:
            sbom_meta: Source SBOM metadata to convert

        Returns:
            Dictionary containing the converted SBOM data in target format
        """
        pass


class SBOMConverterFactory:
    """
    Factory class for creating SBOM format converters.

    Implements registry pattern to manage available converters.
    """

    _registry: Dict[SBOMFormat, Type[ISBOMConverter]] = {}

    @classmethod
    def register(cls, sbom_format: SBOMFormat, converter: Type[ISBOMConverter]) -> None:
        """
        Register a converter for a specific SBOM format.

        Args:
            sbom_format: Target format from SBOMFormat enum
            converter: Converter class implementing ISBOMConverter
        """
        if not isinstance(converter, type):
            raise TypeError("Converter must be a class")
        if not issubclass(converter, ISBOMConverter):
            raise ValueError(f"{converter.__name__} must implement ISBOMConverter interface")
        cls._registry[sbom_format] = converter

    @classmethod
    def create(cls, sbom_format: SBOMFormat) -> ISBOMConverter:
        """
        Create an instance of the converter for the specified format.

        Args:
            sbom_format: Target format from SBOMFormat enum

        Returns:
            New converter instance implementing ISBOMConverter
        """
        if sbom_format not in cls._registry:
            raise ValueError(f"Unsupported format: {sbom_format}")
        return cls._registry[sbom_format]()

    @classmethod
    def supported_formats(cls) -> List[SBOMFormat]:
        """
        Get list of currently supported SBOM formats.

        Returns:
            List of registered SBOMFormat enum members
        """
        return list(cls._registry.keys())
