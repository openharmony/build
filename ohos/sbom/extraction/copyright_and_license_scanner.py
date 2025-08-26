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

import logging
import re
from pathlib import Path
from typing import Dict, List, Union, Tuple

from license_expression import get_spdx_licensing, LicenseSymbol

from ohos.sbom.extraction.local_resource_loader import LocalResourceLoader
from ohos.sbom.sbom.metadata.sbom_meta_data import NOASSERTION

logger = logging.getLogger(__name__)


class CopyrightDetector:

    @classmethod
    def find_copyrights(cls, texts: List[str]) -> List[Dict]:
        """
        Extract complete copyright information, preserving the original output format.
        Returns list of dicts with keys: statement, year, holder.
        """
        results = []
        seen = set()

        for text in texts:
            if not text or not isinstance(text, str):
                continue

            for block in cls._find_copyright_blocks(text):
                year_str_output = cls._extract_years(block)
                holder_str_output = cls._extract_holder(block)

                if not year_str_output and not holder_str_output:
                    continue

                full_statement = block.strip()
                if full_statement in seen:
                    continue
                seen.add(full_statement)

                results.append({
                    "statement": full_statement,
                    "year": year_str_output,
                    "holder": holder_str_output
                })

        return results

    @classmethod
    def _find_copyright_blocks(cls, text: str) -> List[str]:
        """Find potential copyright blocks in text."""
        potential_pattern = r'(?i)\b(?:Copyright\s*(?:\(C\))?|\(C\)|©)[^\r\n]*(?:\r\n?|\n|$)'
        matches = re.findall(potential_pattern, text)
        return [block.strip() for block in matches if block.strip() and re.search(r'\b\d{4}\b', block)]

    @classmethod
    def _extract_years(cls, block: str) -> str:
        """Extract and format years from copyright block."""
        year_range_pattern = re.compile(r'\b(\d{4})\s*[-–]\s*(\d{4})\b')
        year_single_pattern = re.compile(r'\b\d{4}\b')

        years = set()
        all_ranges = year_range_pattern.findall(block)
        all_single_years = year_single_pattern.findall(block)

        # Add year ranges
        for match in year_range_pattern.finditer(block):
            years.add(match.group(0).strip())

        # Add single years not already in ranges
        for year_str in all_single_years:
            try:
                year_val = int(year_str)
            except ValueError:
                continue
            in_range = any(
                int(start) <= year_val <= int(end)
                for start, end in all_ranges
            )
            if not in_range:
                years.add(year_str)

        return ", ".join(sorted(years, key=lambda y: ('-' not in y, y)))

    @classmethod
    def _extract_holder(cls, block: str) -> str:
        """Extract and format copyright holder from block."""
        holder_text = cls._clean_copyright_markers(block)
        holder_text = cls._clean_years(holder_text)
        holder_text = cls._clean_urls_and_references(holder_text)
        holder_text = cls._normalize_text(holder_text)

        holders = cls._split_and_filter_holders(holder_text)
        unique_holders = sorted(set(h for h in holders if h))

        return cls._format_final_holder(", ".join(unique_holders) if unique_holders else "")

    @classmethod
    def _clean_copyright_markers(cls, text: str) -> str:
        """Remove copyright markers from text."""
        text = re.sub(r'(?i)\bCopyright\s*(?:\(C\))?\b', '', text)
        text = re.sub(r'\(C\)', '', text)
        return re.sub(r'©', '', text)

    @classmethod
    def _clean_years(cls, text: str) -> str:
        """Remove year information from text."""
        text = re.sub(r'\b\d{4}\s*[-–]\s*\d{4}\b', '', text)
        return re.sub(r'\b\d{4}\b', '', text)

    @classmethod
    def _clean_urls_and_references(cls, text: str) -> str:
        """Remove URLs and reference statements from text."""
        text = re.sub(r'\(\s*https?://[^\s)]+\s*\)', '', text)  # ( http://... )
        text = re.sub(r'\(\s*[a-z][a-z0-9\-]*\s*\)', '', text)  # (minizip), (project)
        text = re.sub(r'\(\s*(?:Inc|Ltd|Co|Corp|LLC|GmbH|Foundation)\.?\s*\)', '', text, flags=re.I)
        text = re.sub(r'https?://[^\s]+', '', text)
        return re.sub(r'\b[\w.-]+@[\w.-]+\b', '', text)

    @classmethod
    def _normalize_text(cls, text: str) -> str:
        """Normalize text by removing special characters and extra spaces."""
        text = re.sub(r'[^\w\s\-.,&()]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'\(\s*\)', '', text)
        return re.sub(r'\s+', ' ', text).strip()

    @classmethod
    def _split_and_filter_holders(cls, text: str) -> List[str]:
        """Split holder text and filter out invalid parts."""
        holders = []
        parts = re.split(r'[,;]|\s+and\s+|&', text, flags=re.I)

        for part in parts:
            part = re.sub(r'^\s*(?:and|&|,|\.)\s*|\s*(?:and|&|,|\.)\s*$', '', part, flags=re.I)
            part = re.sub(r'\(\s*\)', '', part)
            part = part.strip()

            if part and not cls._is_invalid_holder_part(part):
                holders.append(part)

        return holders

    @classmethod
    def _is_invalid_holder_part(cls, part: str) -> bool:
        """Check if a holder part should be filtered out."""
        return bool(re.search(
            r'\b(?:modification|project|info|read|support|unzip|zip|license|version|'
            r'part of|conditions|distribution|use|see|notice|rights reserved|developer|'
            r'maintainer|author|team)\b',
            part, re.I
        ))

    @classmethod
    def _format_final_holder(cls, holder: str) -> str:
        """Apply final formatting to holder string."""
        holder = re.sub(r'\s*[-–—]\s*$', '', holder)
        holder = re.sub(r'\s*[-–—]\s*http\S*$', '', holder)
        holder = re.sub(r'\s+http\S+', '', holder)
        holder = re.sub(r'\s*,\s*$', '', holder).strip()
        return re.sub(r'\s+and\s+$', '', holder, flags=re.I).strip()


class LicenseDetector:
    LICENSE_PATTERNS = {
        'Apache-2.0': [
            r'Apache License[\s,]+Version 2\.0',
            r'http://www\.apache\.org/licenses/LICENSE-2\.0',
            r'ASF 2\.0'
        ],
        'MIT': [
            r'\bMIT (?:License|Permission)\b',
            r'Permission is hereby granted,? free of charge',
            r'THE SOFTWARE IS PROVIDED "AS IS"'
        ],
        'GPL-3.0': [
            r'GNU GENERAL PUBLIC LICENSE[\s,]+Version 3',
            r'\bGPLv3\b',
            r'https?://www\.gnu\.org/licenses/gpl-3\.0'
        ],
        'BSD-3-Clause': [
            r'Redistribution and use in source and binary forms',
            r'BSD 3-Clause(?: License)?'
        ],
        'ISC': [
            r'\bISC License\b',
            r'Permission to use, copy, modify, and distribute this software'
        ],
        'MPL-2.0': [
            r'http://mozilla\.org/MPL/2\.0/',
            r'Mozilla Public License[\s,]+Version\s+2\.0',
            r'This Source Code Form is subject to the terms of the Mozilla Public License.*?Version.*?2\.0'
        ]
    }

    LICENSE_FILE_NAMES = {
        "license", "copying", "notice",
        "license.txt", "copying.txt", "notice.txt",
        "license.md", "copying.md", "notice.md"
    }

    def __init__(self):
        self.licensing = get_spdx_licensing()

    def detect_licenses(self, texts: List[str]) -> List[str]:
        found_licenses = set()

        spdx_pattern = re.compile(r'SPDX-License-Identifier:\s*([^\n]+)', re.IGNORECASE)
        for text in texts:
            match = spdx_pattern.search(text)
            if match:
                try:
                    parsed_license = self.licensing.parse(match.group(1))
                    found_licenses.update(str(s) for s in parsed_license.objects if isinstance(s, LicenseSymbol))
                except Exception as e:
                    logger.debug(
                        f"Failed to parse SPDX license identifier: "
                        f"'{match.group(1)}' in text snippet: '{text[:50]}...'",
                        exc_info=True
                    )

        for license_type, patterns in self.LICENSE_PATTERNS.items():
            if any(re.search(pattern, text, re.IGNORECASE) for text in texts for pattern in patterns):
                found_licenses.add(license_type)

        return sorted(found_licenses)

    def identify_license(self, text: str) -> Tuple[str, float]:
        spdx_match = re.search(r'SPDX-License-Identifier:\s*([^\n]+)', text, re.IGNORECASE)
        if spdx_match:
            try:
                parsed_license = self.licensing.parse(spdx_match.group(1))
                if parsed_license:
                    return str(parsed_license), 1.0
            except (AttributeError, ValueError, SyntaxError) as e:
                print(f"[Debug] License parse failed: {e}")
                pass
            except Exception as e:
                print(f"[Warning] Unexpected error during license parsing: {type(e).__name__}: {e}")
                pass

        best_match = (NOASSERTION, 0.0)
        for license_id, patterns in self.LICENSE_PATTERNS.items():
            matched = sum(1 for pattern in patterns if re.search(pattern, text, re.IGNORECASE))
            if matched > 0:
                confidence = matched / len(patterns)
                if confidence > best_match[1]:
                    best_match = (license_id, confidence)

        return best_match


class FileScanner:

    def __init__(self):
        self.license_detector = LicenseDetector()

    def scan(self, file_path: Union[str, Path]) -> Dict:
        path = Path(file_path)
        real_path = LocalResourceLoader.to_local_path(file_path)
        if not Path(real_path).is_file():
            return {
                "path": str(real_path),
                "licenses": [],
                "copyrights": [],
                "content_type": "NOASSERTION",
                "content": ""
            }
        content = LocalResourceLoader.load_text_file(real_path, max_bytes=8192)
        licenses = self.license_detector.detect_licenses([content])
        copyrights = CopyrightDetector.find_copyrights([content])

        return {
            "path": str(path),
            "licenses": licenses,
            "copyrights": copyrights,
            "content_type": "Text",
            "content": content
        }


class LicenseFileScanner:

    def __init__(self):
        self.license_detector = LicenseDetector()

    def scan(self, directory: Union[str, Path]) -> List[Dict]:
        directory = Path(LocalResourceLoader.to_local_path(directory))
        if not directory.is_dir():
            return []

        license_files = []

        for item in directory.iterdir():
            if item.is_file() and item.name.lower() in LicenseDetector.LICENSE_FILE_NAMES:
                result = self.scan_license_file(item)
                license_files.append(result)
        return license_files

    def scan_license_file(self, file_path: Union[str, Path]) -> Dict:
        path = Path(file_path)
        if not path.is_file():
            return {
                "path": str(path),
                "license_type": "NOASSERTION",
                "license_text": "",
                "copyrights": [],
                "confidence": 0.0
            }

        try:
            content = LocalResourceLoader.load_text_file(file_path)
        except OSError as e:
            logger.debug("Skipping file '%s': read failed (%s)", file_path, e)
            return {
                "path": str(path),
                "license_type": "NOASSERTION",
                "license_text": "",
                "copyrights": [],
                "confidence": 0.0
            }

        license_type, confidence = self.license_detector.identify_license(content)
        copyrights = CopyrightDetector.find_copyrights([content])

        return {
            "path": str(path),
            "license_type": license_type,
            "license_text": content,
            "copyrights": copyrights,
            "confidence": confidence
        }
