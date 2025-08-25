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

    def convert(self, sbom_format: SBOMFormat) -> Dict[str, Any]:
        """
        Convert the SBOM metadata to the specified format.

        Args:
            sbom_format: Target format (from SBOMFormat enum)

        Returns:
            Dictionary containing the converted SBOM data
        """
        return SBOMConverterFactory.create(sbom_format).convert(self.sbom_meta)

    @staticmethod
    def register_format(sbom_format: SBOMFormat, converter: Type['ISBOMConverter']) -> None:
        """
        Register a new converter for a specific SBOM format.

        Args:
            sbom_format: Format to register (from SBOMFormat enum)
            converter: Converter class implementing ISBOMConverter interface
        """
        SBOMConverterFactory.register(sbom_format, converter)
