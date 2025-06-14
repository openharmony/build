#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 Huawei Device Co., Ltd.
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

import sys
import argparse
import os

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from scripts.util.file_utils import write_json_file  # noqa: E402


def get_source_name(module_type, name, prefix_override, suffix,
                    alternative_suffix):
    """Generate source file name by type."""
    if (module_type == 'lib'
            or module_type == 'lib64') and not prefix_override:
        if not name.startswith('lib'):
            name = 'lib' + name
    alias = ''
    if module_type == 'java_library' and alternative_suffix:
        alias = '%s%s' % (name, alternative_suffix)
    if suffix:
        name = '%s%s' % (name, suffix)
    if module_type == 'none':
        name = ''
    return name, alias


def get_type_dir(module_type):
    """Get the install directory by type."""
    return module_type


def _gen_install_dest(base_dir, module_install_dir, relative_install_dir,
                      module_type):
    """Generate module install dir by user config."""
    if module_install_dir != '':
        _install_dir = os.path.join(base_dir, module_install_dir)
    elif relative_install_dir != '':
        _install_dir = os.path.join(base_dir, get_type_dir(module_type),
                                    relative_install_dir)
    else:
        _install_dir = os.path.join(base_dir, get_type_dir(module_type))
    return _install_dir


def gen_install_dests(system_base_dir, ramdisk_base_dir, vendor_base_dir, updater_base_dir,
                      updater_vendor_base_dir, sys_prod_base_dir, chip_prod_base_dir,
                      eng_system_base_dir, eng_chipset_base_dir, cloud_rom_base_dir, source_file_name, 
                      install_images, module_install_dir, relative_install_dir, module_type):
    """Generate module install dir by user config."""
    dests = []
    if module_type == "none":
        return dests
    dest = ''
    for image in install_images:
        if image == 'system':
            dest = _gen_install_dest(system_base_dir, module_install_dir,
                                     relative_install_dir, module_type)
        elif image == 'ramdisk':
            dest = _gen_install_dest(ramdisk_base_dir, module_install_dir,
                                     relative_install_dir, module_type)
        elif image == 'vendor':
            dest = _gen_install_dest(vendor_base_dir, module_install_dir,
                                     relative_install_dir, module_type)
        elif image == 'updater':
            dest = _gen_install_dest(updater_base_dir, module_install_dir,
                                     relative_install_dir, module_type)
        elif image == 'updater_vendor':
            dest = _gen_install_dest(updater_vendor_base_dir, module_install_dir,
                                     relative_install_dir, module_type)
        elif image == 'sys_prod':
            dest = _gen_install_dest(sys_prod_base_dir, module_install_dir,
                                     relative_install_dir, module_type)
        elif image == 'chip_prod':
            dest = _gen_install_dest(chip_prod_base_dir, module_install_dir,
                                     relative_install_dir, module_type)
        elif image == 'eng_system':
            dest = _gen_install_dest(eng_system_base_dir, module_install_dir,
                                     relative_install_dir, module_type)
        elif image == 'eng_chipset':
            dest = _gen_install_dest(eng_chipset_base_dir, module_install_dir,
                                     relative_install_dir, module_type)
        elif image == 'cloud_rom':
            dest = _gen_install_dest(cloud_rom_base_dir, module_install_dir,
                                     relative_install_dir, module_type)
        dests.append(os.path.join(dest, source_file_name))
    return dests


def gen_module_info(module_type, module_label, module_name, source_dir,
                    module_source, module_alt_source, install_dests,
                    symlink_target, install_enable, collect, notice, args):
    """Generate module install info."""
    source = os.path.join(source_dir, module_source)
    data = {
        'type': module_type,
        'label': module_label,
        'label_name': module_name,
        'source': source,
        'dest': install_dests,
        'collect': collect,
        'install_enable': install_enable
    }
    if notice:
        data['notice'] = notice
    if args.part_name:
        data['part_name'] = args.part_name
    if args.subsystem_name:
        data['subsystem_name'] = args.subsystem_name
    if args.shlib_type:
        data['shlib_type'] = args.shlib_type
    if args.innerapi_tags:
        data['innerapi_tags'] = args.innerapi_tags
    if args.version_script:
        data['version_script'] = args.version_script
    if module_type == 'java_library':
        data['alternative_source'] = os.path.join(source_dir,
                                                  module_alt_source)
    if args.symlink_ext:
        data['symlink_ext'] = args.symlink_ext
    if args.symlink_path:
        data['symlink_path'] = args.symlink_path
    if symlink_target:
        data['symlink'] = symlink_target
    if args.softlink_create_path:
        data['softlink_create_path'] = args.softlink_create_path
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--system-base-dir', required=True)
    parser.add_argument('--ramdisk-base-dir', required=True)
    parser.add_argument('--vendor-base-dir', required=True)
    parser.add_argument('--updater-base-dir', required=True)
    parser.add_argument('--updater_vendor-base-dir', required=True)
    parser.add_argument('--eng_system-base-dir', required=True)
    parser.add_argument('--eng_chipset-base-dir', required=True)
    parser.add_argument('--sys_prod-base-dir', required=True)
    parser.add_argument('--chip_prod-base-dir', required=True)
    parser.add_argument('--cloud_rom-base-dir', required=True)
    parser.add_argument('--label-name', help='module name', required=True)
    parser.add_argument('--target-label', help='target label', required=True)
    parser.add_argument('--type', help='module type', required=True)
    parser.add_argument('--source-dir', help='', required=True)
    parser.add_argument('--install-images', nargs='+', help='')
    parser.add_argument('--install-name', help='', required=False, default='')
    parser.add_argument('--suffix', help='', required=False)
    parser.add_argument('--alternative-suffix',
                        help='alternative extension for java library targets',
                        required=False)
    parser.add_argument('--symlink-target', nargs='+', help='', required=False)
    parser.add_argument('--output-file', help='', required=True)
    parser.add_argument('--prebuilt', dest='prebuilt', action='store_true')
    parser.add_argument('--no-prebuilt', dest='prebuilt', action='store_false')
    parser.set_defaults(prebuilt=False)
    parser.add_argument('--module-source', help='', required=False)
    parser.add_argument('--install-enable',
                        dest='install_enable',
                        action='store_false')
    parser.set_defaults(install_enable=True)
    parser.add_argument('--collect', dest='collect', action='store_true')
    parser.add_argument('--notice', help='path to notice')
    parser.set_defaults(collect=False)
    parser.add_argument('--module-install-dir', help='', required=False, default='')
    parser.add_argument('--relative-install-dir', help='', required=False, default='')
    parser.add_argument('--part-name', help='', required=False, default='')
    parser.add_argument('--subsystem-name', help='', required=False, default='')
    parser.add_argument('--shlib-type', help='', required=False, default='')
    parser.add_argument('--innerapi-tags', nargs='+', help='', required=False, default='')
    parser.add_argument('--symlink-ext', nargs='+', help='', required=False, default='')
    parser.add_argument('--symlink-path', help='', required=False, default='')
    parser.add_argument('--softlink-create-path', help='', required=False, default='')
    parser.add_argument('--version_script', help='', required=False, default='')
    parser.add_argument('--prefix-override',
                        dest='prefix_override',
                        action='store_true')
    parser.add_argument('--no-prefix-override',
                        dest='prefix_override',
                        action='store_false')
    parser.set_defaults(prefix_override=False)
    args = parser.parse_args()

    module_source = ''
    module_alt_source = ''
    source_file_name = ''
    if args.prebuilt:
        source_file_name = os.path.basename(args.module_source)
        module_source = args.module_source
        if module_source.startswith("//"):
            module_source = module_source[2:]
    # when the app is compiled by hvigor, that means module_type == "app" and suffix == "".
    elif args.type == "app" and not args.suffix:
        source_file_name = ""
        alt_source_file_name = ""
        module_source = args.install_name
        module_alt_source = ""
    else:
        source_file_name, alt_source_file_name = get_source_name(
            args.type, args.install_name, args.prefix_override, args.suffix,
            args.alternative_suffix)
        module_source = source_file_name
        module_alt_source = alt_source_file_name

    install_dests = []
    if args.install_images:
        install_dests = gen_install_dests(
            args.system_base_dir, args.ramdisk_base_dir, args.vendor_base_dir, args.updater_base_dir,
            args.updater_vendor_base_dir, args.sys_prod_base_dir, args.chip_prod_base_dir,
            args.eng_system_base_dir, args.eng_chipset_base_dir, args.cloud_rom_base_dir, source_file_name,
            args.install_images, args.module_install_dir, args.relative_install_dir, args.type)

    module_info_data = gen_module_info(args.type, args.target_label,
                                       args.label_name, args.source_dir,
                                       module_source, module_alt_source,
                                       install_dests, args.symlink_target,
                                       args.install_enable, args.collect,
                                       args.notice, args)

    # write module info file
    write_json_file(args.output_file, module_info_data)
    return 0


if __name__ == '__main__':
    sys.exit(main())
