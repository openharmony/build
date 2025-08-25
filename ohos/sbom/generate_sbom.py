import argparse
import os
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))

from ohos.sbom.common.utils import write_json
from ohos.sbom.converters.api import SBOMConverter
from ohos.sbom.converters.base import SBOMFormat
from ohos.sbom.extraction.local_resource_loader import LocalResourceLoader
from ohos.sbom.pipeline.sbom_generator import SBOMGenerator


def set_path(args):
    LocalResourceLoader.set_source_root(args.source_root_dir)
    LocalResourceLoader.set_out_root(args.out_dir)

def generate_sbom(args):
    sbom_meta_data = SBOMGenerator(args).build_sbom()
    spdx_data = SBOMConverter(sbom_meta_data).convert(SBOMFormat.SPDX)
    sbom_dir = os.path.join(args.out_dir, "sbom")
    os.makedirs(sbom_dir, exist_ok=True)
    output_file_meta_data = os.path.join(sbom_dir, "sbom_meta_data.json")
    output_file_spdx = os.path.join(sbom_dir, "spdx.json")
    write_json(sbom_meta_data.to_dict(), output_file_meta_data)
    write_json(spdx_data, output_file_spdx)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root-dir", type=str, required=True, help="project source root directory")
    parser.add_argument("--out-dir", type=str, required=True, help="SBOM output directory")
    parser.add_argument("--product", type=str, required=False, help="Product name")
    parser.add_argument("--platform", type=str, required=False, help="Target platform")
    args = parser.parse_args()
    set_path(args)
    generate_sbom(args)
    return 0


if __name__ == '__main__':
    sys.exit(main())
