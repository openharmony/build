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

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from typing import List

from ohos.sbom.sbom.config.field_config import FieldConfigManager
from ohos.sbom.sbom.validation.validator import Validator


class BaseBuilder(ABC):
    """Abstract base class defining the core builder interface."""

    def build(self, validate: bool = True) -> Any:
        """
        Execute the complete build process.

        Args:
            validate: Whether to perform validation before building

        Returns:
            Any: The constructed object

        Process:
            1. Fill default values
            2. Validate fields (if enabled)
            3. Construct and return the final instance
        """
        self._fill_defaults()
        if validate:
            self._validate()
        return self._build_instance()

    @abstractmethod
    def _fill_defaults(self) -> None:
        """Populate default values for unset fields."""
        pass

    @abstractmethod
    def _validate(self) -> None:
        """Validate that all required fields are properly set."""
        pass

    @abstractmethod
    def _build_instance(self):
        """Construct and return the final instance."""
        pass


class ConfigurableBuilder(BaseBuilder):
    """
    Configurable builder that works with FieldConfigManager.

    Implements default value filling and validation based on configuration.
    Subclasses should define CONFIG_NAME to enable automatic configuration loading.
    """

    CONFIG_NAME: Optional[str] = None

    def __init__(self, config_mgr: Optional[FieldConfigManager] = None):
        """
        Initialize the builder.

        Args:
            config_mgr: Optional FieldConfigManager instance
                       - If provided, uses the given configuration
                       - If None, attempts to load using CONFIG_NAME
                       - If both unavailable, builder operates without configuration
        """
        self._config_mgr = config_mgr
        if self._config_mgr is None and hasattr(self, 'CONFIG_NAME') and self.CONFIG_NAME:
            self._config_mgr = FieldConfigManager.get_instance(self.CONFIG_NAME)

    def build(self, validate: bool = True) -> Any:
        """
        Build with configurable validation.

        Args:
            validate: Whether to perform validation (only if config manager available)

        Returns:
            Any: The constructed instance
        """
        self._fill_defaults()
        if validate and self._config_mgr is not None:
            self._validate()
        return self._build_instance()

    @abstractmethod
    def _build_instance(self):
        """Subclasses must implement actual instance construction."""
        pass

    def get_property_value(self, property_name: str) -> Any:
        """
        Safely get an internal property value.

        Args:
            property_name: The property name (e.g. 'serial_number')

        Returns:
            Any: The property value or None if not set
        """
        return getattr(self, f"_{property_name}", None)

    def _fill_defaults(self) -> None:
        """Fill default values for all unset fields."""
        if self._config_mgr is None:
            return

        for prop in self._config_mgr.all_properties():
            current_value = self.get_property_value(prop)

            # Check if "unset" or empty (excluding False, 0, etc.)
            if not Validator.has_value(current_value):
                default_val = self._config_mgr.get_default(prop)
                if default_val is not None:
                    setattr(self, f"_{prop}", default_val)

    def _validate(self) -> None:
        """Validate all required fields are properly set."""
        if self._config_mgr is None:
            return

        requirements = []
        for prop in self._config_mgr.all_properties():
            value = self.get_property_value(prop)
            required = self._config_mgr.is_required(prop)
            requirements.append((prop, value, lambda req=required: req))

        Validator.validate_fields(requirements)


class CompositeBuilder(BaseBuilder):
    """Builder that composes multiple child builders."""

    def __init__(self):
        """Initialize with empty child builder list."""
        self._children: List[BaseBuilder] = []

    def add_child_builder(self, builder: BaseBuilder) -> None:
        """
        Add a child builder to the composition.

        Args:
            builder: The child builder to add
        """
        self._children.append(builder)

    @abstractmethod
    def _build_instance(self) -> Dict[str, Any]:
        """
        Construct the composite instance.

        Returns:
            Dict[str, Any]: The composite result
        """
        pass

    def _fill_defaults(self):
        """
        Perform hierarchical validation with clear error reporting.

        Raises:
            ValueError: If any child builder validation fails, with detailed messages
        """
        for child in self._children:
            child._fill_defaults()  # pylint: disable=protected-access

    def _validate(self) -> None:
        """
        Perform hierarchical validation with clear error reporting.

        Raises:
            ValueError: If any child builder validation fails, with detailed messages
        """
        errors = []

        for child in self._children:
            try:
                child._validate()  # pylint: disable=protected-access
            except ValueError as e:
                child_name = child.__class__.__name__.replace("BuilderContext", "")
                errors.append(f"{child_name}missing: {str(e)}")

        if errors:
            raise ValueError("\n".join(errors))
