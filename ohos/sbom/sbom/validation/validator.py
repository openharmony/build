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

from typing import List
from typing import Tuple, Any, Callable

# Type alias for field-level validation: (field_name, field_value, is_required_predicate)
FieldRequirement = Tuple[str, Any, Callable[[], bool]]


class Validator:
    """A utility class for performing field-level and object-level validations."""

    @staticmethod
    def has_value(value: Any) -> bool:
        """
        Checks if a value exists and is non-empty.

        Args:
            value: The value to check

        Returns:
            bool: False if the value is None, empty string, or empty collection; True otherwise
        """
        if value is None:
            return False
        if isinstance(value, str):
            return value.strip() != ""
        if isinstance(value, (list, tuple, dict, set)):
            return len(value) > 0
        return True

    @staticmethod
    def validate_fields(requirements: List[FieldRequirement]) -> None:
        """
        Validates that all required fields have values.

        Args:
            requirements: List of field requirements where each element is a tuple of:
                         (field_name, field_value, is_required_predicate)

        Raises:
            ValueError: If any required field is missing or empty

        Example:
            requirements = [
                ("serial_number", serial_number, lambda: True),  # required
                ("lifecycles", lifecycles, lambda: False)  # optional
            ]
            Validator.validate_fields(requirements)
        """
        missing = [name
                   for name, value, is_required in requirements
                   if is_required() and not Validator.has_value(value)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
