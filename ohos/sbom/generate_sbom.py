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

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))

from ohos.sbom.common.utils import write_json
from ohos.sbom.converters.api import SBOMConverter
from ohos.sbom.converters.base import SBOMFormat
from ohos.sbom.extraction.local_resource_loader import LocalResourceLoader
from ohos.sbom.pipeline.sbom_generator import SBOMGenerator


def generate_manifest(args):
    """
    Generate a release manifest using 'python .repo/repo/repo manifest -r -o' command.

    The manifest is saved to:
        <out_dir>/sbom/manifests/manifest_tag_YYYYMMDD_HHMMSS.xml

    Args:
        args: Parsed command-line arguments with output
    """

    source_root = Path(args.source_root_dir).resolve()
    out_dir = Path(args.out_dir).resolve()

    repo_script = source_root / ".repo" / "repo" / "repo"
    if not repo_script.exists():
        raise FileNotFoundError(f"Repo script not found: {repo_script}\n"
                                f"Please make sure you are in a valid repo workspace.")

    manifest_dir = out_dir / "sbom" / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = manifest_dir / f"manifest_tag_{timestamp_str}.xml"

    cmd = [
        "python", str(repo_script),
        "manifest", "-r", "-o", str(output_path)
    ]

    try:
        print(f"[INFO] Generating manifest: {output_path}")
        print(f"[DEBUG] Running command: {' '.join(cmd)}")

        subprocess.run(cmd, check=True, cwd=source_root)
        print(f"[INFO] Manifest generated successfully: {output_path}")
        return output_path

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to generate manifest (command exited with error): {e}")
        raise
    except FileNotFoundError:
        print(f"[ERROR] Python interpreter not found or repo script missing.")
        raise
    except Exception as e:
        print(f"[ERROR] Unexpected error during manifest generation: {e}")
        raise


def set_path(args):
    LocalResourceLoader.set_source_root(args.source_root_dir)
    LocalResourceLoader.set_out_root(args.out_dir)


def generate_sbom(args):
    """
    Generate SBOM (Software Bill of Materials) and clean up temporary files afterward.
    """
    # Define the output directory for SBOM artifacts
    sbom_dir = os.path.join(args.out_dir, "sbom")
    os.makedirs(sbom_dir, exist_ok=True)

    # Paths to temporary files/directories to be cleaned up
    manifests_dir = os.path.join(sbom_dir, "manifests")
    gn_gen_file = os.path.join(sbom_dir, "gn_gen.json")

    try:
        # Generate SBOM metadata using the provided arguments
        sbom_meta_data = SBOMGenerator(args).build_sbom()

        # Convert SBOM metadata to SPDX format
        spdx_data = SBOMConverter(sbom_meta_data).convert(SBOMFormat.SPDX)

        # Define output file paths
        output_file_meta_data = os.path.join(sbom_dir, "sbom_meta_data.json")
        output_file_spdx = os.path.join(sbom_dir, "spdx.json")

        # Write SBOM metadata and SPDX data to JSON files
        write_json(sbom_meta_data.to_dict(), output_file_meta_data)
        write_json(spdx_data, output_file_spdx)

    finally:
        # Ensure cleanup runs regardless of success or failure

        # Remove the 'manifest' directory if it exists
        if os.path.exists(manifests_dir) and os.path.isdir(manifests_dir):
            try:
                shutil.rmtree(manifests_dir)
                print(f"Cleaned up directory: {manifests_dir}")
            except Exception as e:
                print(f"Failed to delete directory {manifests_dir}: {e}")

        # Remove the 'gn_gen.json' file if it exists
        if os.path.exists(gn_gen_file) and os.path.isfile(gn_gen_file):
            try:
                os.remove(gn_gen_file)
                print(f"Cleaned up file: {gn_gen_file}")
            except Exception as e:
                print(f"Failed to delete file {gn_gen_file}: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root-dir", type=str, required=True, help="project source root directory")
    parser.add_argument("--out-dir", type=str, required=True, help="SBOM output directory")
    parser.add_argument("--product", type=str, required=True, help="Product name")
    parser.add_argument("--platform", type=str, required=True, help="Target platform")
    args = parser.parse_args()
    set_path(args)
    generate_manifest(args)
    generate_sbom(args)

    return 0


if __name__ == '__main__':
    sys.exit(main())
