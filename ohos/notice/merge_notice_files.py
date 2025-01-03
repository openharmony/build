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

from collections import defaultdict
import argparse
import hashlib
import os
import os.path
import sys
import gzip
import shutil
import glob
import re
import subprocess

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from scripts.util import build_utils  # noqa: E402
from scripts.util.file_utils import write_json_file, read_json_file  # noqa: E402

xml_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
}


def move_static_library_notices(options):
    files = []
    dest = os.path.join(options.notice_root_dir, 'libs')
    os.makedirs(dest, exist_ok=True)
    static_dir = os.path.join(options.notice_root_dir, "static")
    static_subdir = os.path.join(options.static_library_notice_dir, "libs")
    if os.path.exists(static_dir):
        files = build_utils.get_all_files(static_dir)
        files.sort()
    if os.path.exists(static_subdir):
        other_files = build_utils.get_all_files(static_subdir)
        other_files.sort()
        files.extend(other_files)
    if files:
        for file in files:
            file_name = os.path.basename(file)
            if not file_name.startswith("lib"):
                dest_file = os.path.join(dest, f"lib{file_name}")
            else:
                dest_file = os.path.join(dest, file_name)
            shutil.copyfile(file, dest_file)
            if os.path.isfile("{}.json".format(dest_file)):
                os.makedirs(os.path.dirname("{}.json".format(dest_file)), exist_ok=True)
                shutil.copyfile("{}.json".format(file), "{}.json".format(dest_file))
        shutil.rmtree(static_dir)
        shutil.rmtree(static_subdir)
    

def copy_static_library_notices(options, depfiles: list):
    valid_notices = []
    basenames = []
    # add sort method
    files = build_utils.get_all_files(options.static_library_notice_dir)
    files.sort()
    for file in files:
        if os.stat(file).st_size == 0:
            continue
        if not options.lite_product:
            if not file.endswith('.a.txt'):
                continue
        elif not file.endswith('.txt'):
            continue
        notice_file_name = os.path.basename(file)
        if options.lite_product:
            if not notice_file_name.startswith("lib"):
                file_dir = os.path.dirname(file)
                lib_file = os.path.join(file_dir, f"lib{notice_file_name}")
                os.rename(file, lib_file)
                file = lib_file
        if file not in basenames:
            basenames.append(notice_file_name)
            valid_notices.append(file)
            depfiles.append(file)

    for file in valid_notices:
        if options.image_name == "system":
            if options.target_cpu == "arm64" or options.target_cpu == "x64":
                install_dir = "system/lib64"
            elif options.target_cpu == "arm":
                install_dir = "system/lib"
            else:
                continue
        elif options.image_name == "sdk":
            install_dir = "toolchains/lib"
        elif options.image_name == "ndk":
            install_dir = "sysroot/usr/lib"
        else:
            continue
        dest = os.path.join(options.notice_root_dir, install_dir,
                            os.path.basename(file))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copyfile(file, dest)
        if os.path.isfile("{}.json".format(file)):
            os.makedirs(os.path.dirname("{}.json".format(dest)), exist_ok=True)
            shutil.copyfile("{}.json".format(file), "{}.json".format(dest))


def write_file(file: str, string: str):
    print(string, file=file)


def compute_hash(file: str):
    sha256 = hashlib.sha256()
    with open(file, 'rb') as file_fd:
        for line in file_fd:
            sha256.update(line)
    return sha256.hexdigest()


def get_entity(text: str):
    return "".join(xml_escape_table.get(c, c) for c in text)


def generate_txt_notice_files(file_hash: str, input_dir: str, output_filename: str,
                              notice_title: str):
    with open(output_filename, "w") as output_file:
        write_file(output_file, notice_title)
        for value in file_hash:
            write_file(output_file, '=' * 60)
            write_file(output_file, "Notices for file(s):")
            for filename in value:
                write_file(
                    output_file, '/{}'.format(
                        re.sub('.txt.*', '',
                               os.path.relpath(filename, input_dir))))
            write_file(output_file, '-' * 60)
            write_file(output_file, "Notices for software(s):")
            software_list = []
            for filename in value:
                json_filename = '{}.json'.format(filename)
                contents = read_json_file(json_filename)
                if contents is not None and contents not in software_list:
                    software_list.append(contents)
            software_dict = {}
            for contents_value in software_list:
                if len(contents_value) > 0:
                    for val in contents_value:
                        if val.get('Software'):
                            software_name = val.get('Software').strip()
                            if software_name not in software_dict:
                                software_dict[software_name] = {"_version": "", "_path": []}
                        else:
                            write_file(output_file, "Software: ")
                        if val.get('Version'):
                            version = val.get('Version').strip()
                            software_dict[software_name]["_version"] = version
                        else:
                            write_file(output_file, "Version: ")
                        if val.get('Path'):
                            notice_source_path = val.get('Path').strip()
                            software_dict[software_name]["_path"].append(notice_source_path)
            for software, software_value in software_dict.items():
                write_file(output_file, f"Software: {software}")
                write_file(output_file, f"Version: {software_value.get('_version')}")
                if software_value.get("_path"):
                    for path in software_value.get("_path"):
                        write_file(output_file, f"Path: {path}")
            write_file(output_file, '-' * 60)
            with open(value[0], errors='ignore') as temp_file_hd:
                write_file(output_file, temp_file_hd.read())


def generate_xml_notice_files(files_with_same_hash: dict, input_dir: str,
                              output_filename: str):
    id_table = {}
    for file_key in files_with_same_hash.keys():
        for filename in files_with_same_hash[file_key]:
            id_table[filename] = file_key
    with open(output_filename, "w") as output_file:
        write_file(output_file, '<?xml version="1.0" encoding="utf-8"?>')
        write_file(output_file, "<licenses>")

        # Flatten the lists into a single filename list
        sorted_filenames = sorted(id_table.keys())

        # write out a table of contents
        for filename in sorted_filenames:
            stripped_filename = re.sub('.txt.*', '',
                                       os.path.relpath(filename, input_dir))
            write_file(
                output_file, '<file-name content_id="%s">%s</file-name>' %
                             (id_table.get(filename), stripped_filename))

        write_file(output_file, '')
        write_file(output_file, '')

        processed_file_keys = []
        # write the notice file lists
        for filename in sorted_filenames:
            file_key = id_table.get(filename)
            if file_key in processed_file_keys:
                continue
            processed_file_keys.append(file_key)

            with open(filename, errors='ignore') as temp_file_hd:
                write_file(
                    output_file,
                    '<file-content content_id="{}"><![CDATA[{}]]></file-content>'
                        .format(file_key, get_entity(temp_file_hd.read())))
            write_file(output_file, '')

        # write the file complete node.
        write_file(output_file, "</licenses>")


def compress_file_to_gz(src_file_name: str, gz_file_name: str):
    with open(src_file_name, mode='rb') as src_file_fd:
        with gzip.open(gz_file_name, mode='wb') as gz_file_fd:
            gz_file_fd.writelines(src_file_fd)


def handle_zipfile_notices(zip_file: str):
    notice_file = '{}.txt'.format(zip_file[:-4])
    with build_utils.temp_dir() as tmp_dir:
        build_utils.extract_all(zip_file, tmp_dir, no_clobber=False)
        files = build_utils.get_all_files(tmp_dir)
        contents = []
        for file in files:
            with open(file, 'r') as fd:
                data = fd.read()
                if data not in contents:
                    contents.append(data)
        with open(notice_file, 'w') as merged_notice:
            merged_notice.write('\n\n'.join(contents))
    return notice_file


def do_merge_notice(args, zipfiles: str, txt_files: str):
    notice_dir = args.notice_root_dir
    notice_txt = args.output_notice_txt
    notice_gz = args.output_notice_gz
    notice_title = args.notice_title

    if not notice_txt.endswith('.txt'):
        raise Exception(
            'Error: input variable output_notice_txt must ends with .txt')
    if not notice_gz.endswith('.xml.gz'):
        raise Exception(
            'Error: input variable output_notice_gz must ends with .xml.gz')

    notice_xml = notice_gz.replace('.gz', '')

    files_with_same_hash = defaultdict(list)
    for file in zipfiles:
        txt_files.append(handle_zipfile_notices(file))

    for file in txt_files:
        if os.stat(file).st_size == 0:
            continue
        file_hash = compute_hash(file)
        files_with_same_hash[file_hash].append(file)

    file_sets = [
        sorted(files_with_same_hash[hash])
        for hash in sorted(files_with_same_hash.keys())
    ]

    if file_sets is not None:
        generate_txt_notice_files(file_sets, notice_dir, notice_txt,
                                  notice_title)

    if files_with_same_hash is not None:
        generate_xml_notice_files(files_with_same_hash, notice_dir, notice_xml)
        compress_file_to_gz(notice_xml, args.output_notice_gz)

    if args.notice_module_info:
        module_install_info_list = []
        module_install_info = {}
        module_install_info['type'] = 'notice'
        module_install_info['source'] = args.output_notice_txt
        module_install_info['install_enable'] = True
        module_install_info['dest'] = [
            os.path.join(args.notice_install_dir,
                         os.path.basename(args.output_notice_txt))
        ]
        module_install_info_list.append(module_install_info)
        write_json_file(args.notice_module_info, module_install_info_list)

    if args.lite_product:
        current_dir_cmd = ['pwd']
        process = subprocess.Popen(current_dir_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(timeout=600)
        current_dir = stdout.decode().strip()
        dest = f"{current_dir}/system/etc/NOTICE.txt"
        if os.path.isfile(notice_txt):
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copyfile(notice_txt, dest)


def parse_args():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--image-name')
    parser.add_argument('--collected-notice-zipfile',
                        action='append',
                        help='zipfile stors collected notice files')
    parser.add_argument('--notice-root-dir', help='where notice files store')
    parser.add_argument('--output-notice-txt', help='output notice.txt')
    parser.add_argument('--output-notice-gz', help='output notice.txt')
    parser.add_argument('--notice-title', help='title of notice.txt')
    parser.add_argument('--static-library-notice-dir',
                        help='path to static library notice files')
    parser.add_argument('--target-cpu', help='cpu arch')
    parser.add_argument('--depfile', help='depfile')
    parser.add_argument('--notice-module-info',
                        help='module info file for notice target')
    parser.add_argument('--notice-install-dir',
                        help='install directories of notice file')
    parser.add_argument('--lite-product', help='', default="")


    return parser.parse_args()


def main():
    """Main function to merge and generate notice files."""
    args = parse_args()

    notice_dir = args.notice_root_dir
    depfiles = []
    if args.collected_notice_zipfile:
        for zip_file in args.collected_notice_zipfile:
            build_utils.extract_all(zip_file, notice_dir, no_clobber=False)
    else:
        depfiles += build_utils.get_all_files(notice_dir)
    # Copy notice of static targets to notice_root_dir
    if args.lite_product:
        move_static_library_notices(args)
    if args.static_library_notice_dir:
        copy_static_library_notices(args, depfiles)

    zipfiles = glob.glob('{}/**/*.zip'.format(notice_dir), recursive=True)

    txt_files = glob.glob('{}/**/*.txt'.format(notice_dir), recursive=True)
    txt_files += glob.glob('{}/**/*.txt.?'.format(notice_dir), recursive=True)

    outputs = [args.output_notice_txt, args.output_notice_gz]
    if args.notice_module_info:
        outputs.append(args.notice_module_info)
    build_utils.call_and_write_depfile_if_stale(
        lambda: do_merge_notice(args, zipfiles, txt_files),
        args,
        depfile_deps=depfiles,
        input_paths=depfiles,
        input_strings=args.notice_title + args.target_cpu,
        output_paths=(outputs))


if __name__ == "__main__":
    main()

