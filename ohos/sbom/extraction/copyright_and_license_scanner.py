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
        Extract complete copyright information, preserving the original output format:
        - statement: Full copyright text
        - year: Year string (e.g., "1998-2010, 2014")
        - holder: Holder string (e.g., "Gilles Vollant, Mathias Svensson")

        Supported formats:
          - Copyright (C) 1998-2010 Gilles Vollant
          - (C) 2007-2008 Even Rouault
          - © 2009-2010 Mathias Svensson
        Automatically filter out:
          - URLs: (http://...)
          - Project names: (minizip)
          - Reference statements: "see copyright notice"
        """
        results = []
        seen = set()

        year_range_pattern = re.compile(r'\b(\d{4})\s*[-–]\s*(\d{4})\b')
        year_single_pattern = re.compile(r'\b\d{4}\b')

        for text in texts:
            if not text or not isinstance(text, str):
                continue

            potential_pattern = r'(?i)\b(?:Copyright\s*(?:\(C\))?|\(C\)|©)[^\r\n]*(?:\r\n?|\n|$)'
            matches = re.findall(potential_pattern, text)

            for block in matches:
                block = block.strip()
                if not block:
                    continue

                if not re.search(r'\b\d{4}\b', block):
                    continue

                years = set()

                for match in year_range_pattern.finditer(block):
                    years.add(match.group(0).strip())

                all_single_years = year_single_pattern.findall(block)
                all_ranges = year_range_pattern.findall(block)

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

                year_str_output = ", ".join(sorted(years, key=lambda y: ('-' not in y, y)))

                holder_text = block

                holder_text = re.sub(r'(?i)\bCopyright\s*(?:\(C\))?\b', '', holder_text)
                holder_text = re.sub(r'\(C\)', '', holder_text)
                holder_text = re.sub(r'©', '', holder_text)

                holder_text = re.sub(r'\b\d{4}\s*[-–]\s*\d{4}\b', '', holder_text)
                holder_text = re.sub(r'\b\d{4}\b', '', holder_text)

                holder_text = re.sub(r'\(\s*https?://[^\s)]+\s*\)', '', holder_text)  # ( http://... )
                holder_text = re.sub(r'\(\s*[a-z][a-z0-9\-]*\s*\)', '', holder_text)  # (minizip), (project)
                holder_text = re.sub(r'\(\s*(?:Inc|Ltd|Co|Corp|LLC|GmbH|Foundation)\.?\s*\)', '', holder_text,
                                     flags=re.I)

                holder_text = re.sub(r'https?://[^\s]+', '', holder_text)
                holder_text = re.sub(r'\b[\w.-]+@[\w.-]+\b', '', holder_text)

                holder_text = re.sub(r'[^\w\s\-.,&()]', ' ', holder_text)
                holder_text = re.sub(r'\s+', ' ', holder_text).strip()

                holder_text = re.sub(r'\(\s*\)', '', holder_text)
                holder_text = re.sub(r'\s+', ' ', holder_text).strip()

                holders = []
                parts = re.split(r'[,;]|\s+and\s+|&', holder_text, flags=re.I)
                for part in parts:
                    part = re.sub(r'^\s*(?:and|&|,|\.)\s*|\s*(?:and|&|,|\.)\s*$', '', part, flags=re.I)
                    part = re.sub(r'\(\s*\)', '', part)
                    part = part.strip()
                    if not part:
                        continue
                    if re.search(
                            r'\b(?:modification|project|info|read|support|unzip|zip|license|version|'
                            r'part of|conditions|distribution|use|see|notice|rights reserved|developer|'
                            r'maintainer|author|team)\b',
                            part, re.I
                    ):
                        continue
                    holders.append(part)

                unique_holders = sorted(set(h for h in holders if h))
                holder_str_output = ", ".join(unique_holders) if unique_holders else ""

                holder_str_output = re.sub(r'\s*[-–—]\s*$', '', holder_str_output)
                holder_str_output = re.sub(r'\s*[-–—]\s*http\S*$', '', holder_str_output)
                holder_str_output = re.sub(r'\s+http\S+', '', holder_str_output)
                holder_str_output = re.sub(r'\s*,\s*$', '', holder_str_output).strip()
                holder_str_output = re.sub(r'\s+and\s+$', '', holder_str_output, flags=re.I).strip()

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


class DirectoryScanner:

    def __init__(self):
        self.file_scanner = FileScanner()

    def scan(self, dir_path: Union[str, Path], recursive: bool = False) -> Dict:
        path = Path(dir_path)
        if not path.is_dir():
            raise ValueError(f"Invalid directory: {path}")

        results = {
            "path": str(path),
            "file_count": 0,
            "licenses": {},
            "copyright_holders": {},
            "files": []
        }

        scan_iter = path.rglob('*') if recursive else path.glob('*')

        for item in scan_iter:
            if item.is_file():
                results["file_count"] += 1
                file_result = self.file_scanner.scan(item)

                for lic in file_result["licenses"]:
                    results["licenses"][lic] = results["licenses"].get(lic, 0) + 1

                for cp in file_result["copyrights"]:
                    holder = cp["holder"]
                    if holder:
                        results["copyright_holders"][holder] = results["copyright_holders"].get(holder, 0) + 1

                if not file_result["licenses"] or not file_result["copyrights"]:
                    results["files"].append({
                        "path": str(item),
                        "missing_license": not bool(file_result["licenses"]),
                        "missing_copyright": not bool(file_result["copyrights"])
                    })

        return results


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
