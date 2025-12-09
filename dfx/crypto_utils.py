#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2025 Huawei Device Co., Ltd.
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

import base64
from typing import Optional, Union
from dfx import dfx_info, dfx_error

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.backends import default_backend
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


class CryptoUtils:


    def __init__(self, encryption_key):
        self.encryption_key = encryption_key
        if CRYPTOGRAPHY_AVAILABLE:
            try:
                self.fernet = self._create_fernet()
                self.use_fernet = True
            except Exception as e:
                dfx_info(f"Fallback to simple encoding due to: {e}")
                self.use_fernet = False
        else:
            dfx_info("Cryptography library not available, using simple encoding")
            self.use_fernet = False

    def encrypt_headers(self, fields: str, values: str) -> tuple:
        encrypted_fields = self.encrypt(fields) if fields else ""
        encrypted_values = self.encrypt(values) if values else ""
        return encrypted_fields, encrypted_values

    def decrypt_headers(self, encrypted_fields: str, encrypted_values: str) -> tuple:
        decrypted_fields = self.decrypt(encrypted_fields) if encrypted_fields else ""
        decrypted_values = self.decrypt(encrypted_values) if encrypted_values else ""
        return decrypted_fields, decrypted_values

    def encrypt(self, data: str) -> str:
        try:
            if not data:
                return ""

            if self.use_fernet:
                encrypted_data = self.fernet.encrypt(data.encode())
                return base64.urlsafe_b64encode(encrypted_data).decode()
            else:
                # Simple XOR-based encoding as fallback
                return self._simple_encrypt(data)
        except Exception as e:
            dfx_error(f"Failed to encrypt data: {str(e)}")
            return data

    def decrypt(self, encrypted_data: str) -> str:
        try:
            if not encrypted_data:
                return ""

            if self.use_fernet:
                if not self._is_encrypted_data(encrypted_data):
                    return encrypted_data
                decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
                decrypted_data = self.fernet.decrypt(decoded_data)
                return decrypted_data.decode()
            else:
                # Try simple decryption first
                try:
                    return self._simple_decrypt(encrypted_data)
                except Exception as e:
                    # If simple decryption fails, return as-is (might be already plaintext)
                    return encrypted_data
        except Exception as e:
            dfx_info(f"Failed to decrypt data, returning original: {str(e)}")
            return encrypted_data

    def _create_fernet(self):
        if not CRYPTOGRAPHY_AVAILABLE:
            return None
        # Use encryption_key as salt to maintain consistency
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.encryption_key.encode('utf-8'),
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.encryption_key.encode()))
        return Fernet(key)

    def _is_encrypted_data(self, data: str) -> bool:
        try:
            decoded = base64.urlsafe_b64decode(data)
            return len(decoded) >= 60
        except Exception as e:
            dfx_info(f"Failed to check if data is encrypted: {str(e)}")
            return False

    def _simple_encrypt(self, data: str) -> str:
        """Simple XOR-based encoding for fallback"""
        key_bytes = self.encryption_key.encode('utf-8')
        data_bytes = data.encode('utf-8')
        encrypted = bytearray()

        for i, byte in enumerate(data_bytes):
            key_byte = key_bytes[i % len(key_bytes)]
            encrypted.append(byte ^ key_byte)

        # Add prefix to identify as simple encryption
        result = base64.urlsafe_b64encode(b'SIMPLE:' + encrypted).decode()
        return result

    def _simple_decrypt(self, encrypted_data: str) -> str:
        """Simple XOR-based decoding for fallback"""
        decoded = base64.urlsafe_b64decode(encrypted_data.encode())

        # Check if it's simple encryption
        if decoded.startswith(b'SIMPLE:'):
            encrypted_bytes = decoded[7:]  # Remove 'SIMPLE:' prefix
        else:
            raise ValueError("Not simple encrypted data")

        key_bytes = self.encryption_key.encode('utf-8')
        decrypted = bytearray()

        for i, byte in enumerate(encrypted_bytes):
            key_byte = key_bytes[i % len(key_bytes)]
            decrypted.append(byte ^ key_byte)

        return decrypted.decode('utf-8')


def create_crypto_utils_from_config(config: dict) -> Optional[CryptoUtils]:
    is_encrypted = config.get("extra_request_header_fields_encrypted", False)

    if not is_encrypted:
        return None

    encryption_key = config.get("extra_request_header_encryption_key")
    return CryptoUtils(encryption_key)