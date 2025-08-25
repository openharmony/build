import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, NamedTuple
from uuid import uuid4


class FieldConfig(NamedTuple):
    """
    A configuration tuple representing a field's metadata.

    Attributes:
        property: Internal property name used in code
        json_key: Corresponding JSON key name for serialization
        required: Whether this field is mandatory
        default: Default value for the field (supports special tokens)
        type: Expected data type of the field
        description: Description of the field
        example: Example value for documentation purposes
    """
    property: str
    json_key: str
    required: bool
    default: Any
    type: str
    description: str
    example: Any


class FieldConfigManager:
    """
    A manager class for handling field configurations with singleton pattern support.

    Features:
    - Loads configuration from JSON files
    - Provides bidirectional mapping between property names and JSON keys
    - Handles special default value tokens (timestamps, UUIDs)
    - Implements singleton pattern for configuration instances
    """

    _instances: Dict[str, 'FieldConfigManager'] = {}

    def __init__(self, config_path: str):
        """
        Initialize a configuration manager from a JSON file.

        Args:
            config_path: Path to the JSON configuration file

        Raises:
            FileNotFoundError: If the configuration file doesn't exist
        """

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        self._by_property: Dict[str, FieldConfig] = {}
        self._by_json_key: Dict[str, FieldConfig] = {}

        for item in raw_data.get("fields", []):
            field = FieldConfig(
                property=item["property"],
                json_key=item["json_key"],
                required=item.get("required", False),
                default=item.get("default"),
                type=item.get("type", "string"),
                description=item.get("description", ""),
                example=item.get("example")
            )
            self._by_property[field.property] = field
            self._by_json_key[field.json_key] = field

    @classmethod
    def get_instance(cls, config_name: str = "default") -> 'FieldConfigManager':
        """
        Get a singleton instance of the configuration manager.

        Args:
            config_name: Name of the configuration (corresponds to filename without extension)

        Returns:
            FieldConfigManager: The singleton instance

        Note:
            Configuration files are expected to be in a 'configs' subdirectory
            with naming pattern '{config_name}.config.json'
        """
        if config_name not in cls._instances:
            config_dir = os.path.join(os.path.dirname(__file__), "configs")
            config_path = os.path.join(config_dir, f"{config_name}.config.json")
            cls._instances[config_name] = cls(config_path)
        return cls._instances[config_name]

    def is_required(self, property_name: str) -> bool:
        """
        Check if a field is required.

        Args:
            property_name: Internal property name to check

        Returns:
            bool: True if the field is required, False otherwise
        """
        field = self._by_property.get(property_name)
        return field.required if field else False

    def get_default(self, property_name: str) -> Any:
        """
        Get the default value for a field with special token handling.

        Supported special tokens in default values:
        - "{now_utc_iso}": Replaced with current UTC time in ISO 8601 format (Z suffix)
        - "{uuid}": Replaced with a new UUID4 string
        - Lists/Dictionaries: Returns a deep copy to prevent reference sharing

        Args:
            property_name: Internal property name to lookup

        Returns:
            Any: The processed default value or None if not found/specified
        """
        field = self._by_property.get(property_name)
        if not field:
            return None

        default = field.default
        if default is None:
            return None

        if isinstance(default, str):
            if default == "{now_utc_iso}":
                return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            elif "{uuid}" in default:
                return default.format(uuid=str(uuid4()))
        elif isinstance(default, list):
            return [item.copy() if isinstance(item, (dict, list)) else item for item in default]
        elif isinstance(default, dict):
            return default.copy()

        return default

    def all_properties(self) -> List[str]:
        """
        Get all available property names.

        Returns:
            List[str]: List of all internal property names
        """
        return list(self._by_property.keys())
