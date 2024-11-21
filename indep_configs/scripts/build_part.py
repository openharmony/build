#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 Huawei Device Co., Ltd.
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

import requests
import json
import os
import subprocess
import shutil
import glob
import sys
import argparse
import stat

CURRENT_DIRECTORY = os.getcwd()


def replace_part_sofile(part_name, old_folder, new_folder):
    components_json = _get_components_json(os.path.join(old_folder, 'out', 'rk3568'))
    parts_path_info = _get_parts_path_info(components_json)
    part_path = _get_parts_path(parts_path_info, part_name)
    _source_list = _get_system_module_info(old_folder, part_name)
    copy_component_sofile(_source_list, part_name, old_folder, new_folder)


def copy_component_sofile(_source_list, part_name, old_folder, new_folder):
    for source_info in _source_list:
        so_path = source_info.get("source")
        indep_so_path = os.path.join(new_folder, 'out', 'default', 'src', so_path)
        so_dir = os.path.dirname(so_path)
        old_so_folder = os.path.join(old_folder, 'out', 'rk3568', so_dir)
        if os.path.exists(indep_so_path):
            try:
                shutil.copy(indep_so_path, old_so_folder)
            except shutil.SameFileError:
                print(f"Cannot copy '{indep_so_path}' to '{old_so_folder}' because they are the same file.")
            print(f'{part_name}:{so_path} done')


def _get_system_module_info(folder, part_name):
    _part_system_module_path = os.path.join(folder, 'out', 'rk3568', 'packages', 'phone',
                                            'system_module_info.json')
    _source_list = []
    with os.fdopen(os.open(_part_system_module_path, os.O_RDWR | os.O_CREAT, stat.S_IWUSR | stat.S_IRUSR),
                   'r', encoding='utf-8') as f:
        jsondata = json.load(f)
    for _dict in jsondata:
        for k, v in _dict.items():
            if v == part_name:
                _source_list.append(_dict)

    return _source_list


def _get_subsystem_name(folder, part_name):
    _part_subsystem_json_path = os.path.join(folder, 'out', 'rk3568', 'build_configs', 'parts_info',
                                             'part_subsystem.json')
    with os.fdopen(os.open(_part_subsystem_json_path, os.O_RDWR | os.O_CREAT, stat.S_IWUSR | stat.S_IRUSR),
                   'r', encoding='utf-8') as f:
        jsondata = json.load(f)
        subsystem_name = jsondata.get(part_name)
    return subsystem_name


def _get_components_json(out_path):
    jsondata = ""
    json_path = os.path.join(out_path + "/build_configs/parts_info/components.json")
    with os.fdopen(os.open(json_path, os.O_RDWR | os.O_CREAT, stat.S_IWUSR | stat.S_IRUSR),
                   'r', encoding='utf-8') as f:
        try:
            jsondata = json.load(f)
        except Exception as e:
            print(f"--_get_components_json parse json error--: {e}")
    return jsondata


def _get_parts_path_info(components_json):
    jsondata = dict()
    try:
        for component, v in components_json.items():
            jsondata[component] = v.get('path')
    except Exception as e:
        print(f"--_get_part_subsystem parse json error--: {e}")
    return jsondata


def _get_parts_path(json_data, part_name):
    parts_path = None
    if json_data.get(part_name) is not None:
        parts_path = json_data[part_name]
    return parts_path


def _get_export_project(export):
    if export != 'project_list':
        print(f"Unsupported export key: {export}. Expected 'project_list'.")
        return []
    export_button = os.getenv(export)
    if export_button is None or export_button.strip() == '':
        print(f"The environment variable {export} is not set or is empty.")
        return []
    list_export = export_button.split(',')
    return list_export


def _get_export_files(export):
    if export == 'PR_FILE_PATHS':
        export_button = os.getenv(export)
        if export_button is None:
            print('The environment variable PR_FILE_PATHS is not set')
            return None
        return export_button
    else:
        print(f"Unsupported export type: {export}")
        return None


def _handle_successful_response(ret):
    try:
        mkdirs_text = json.loads(ret.text)
        print("The request was successful:", mkdirs_text)
        return mkdirs_text
    except json.JSONDecodeError:
        print("The response is not in valid JSON format.")
        return None


def _get_api_mkdir(params):
    post_url = "http://ci.openharmony.cn/api/sple/external/artifact/repo?projectName=openharmony"
    fails = 0
    while True:
        try:
            if fails >= 5:
                print("The number of failed requests is excessive")
                break
            headers = {'Content-Type': 'application/json'}
            ret = requests.post(post_url, data=json.dumps(params), headers=headers, timeout=10)
            if ret.status_code == 200:
                return _handle_successful_response(ret)
            else:
                print(f"The request failed, and the status code is displayed: {ret.status_code}, message: {ret.text}")
            fails += 1
        except requests.RequestException as e:
            print(f"Request Exception: {e}")
            fails += 1


def _get_part_list():
    list_url = "https://ci.openharmony.cn/api/daily_build/component/check/list"
    fails = 0
    while True:
        try:
            if fails >= 5:
                print("Failed to retrieve the component list after multiple attempts.")
                return None
            ret = requests.get(url=list_url, timeout=10)
            if ret.status_code == 200:
                list_text = json.loads(ret.text)
                return list_text
            else:
                print(f"Received status code {ret.status_code}, retrying...")
                fails += 1
        except requests.RequestException as e:
            print(f"Request error: {e}, attempting to request again...")
            fails += 1
        except json.JSONDecodeError:
            print("Failed to decode JSON response, attempting to request again...")
            fails += 1
        except Exception as e:
            print(f"An unexpected error occurred: {e}, attempting to request again...")
            fails += 1


def _handle_single_component_case(path, component):
    if path not in {'drivers_interface', 'drivers_peripheral'}:
        return list(component.keys())
    return []


def _handle_multiple_component_case(component, files_json):
    all_parts = []
    for driver, driver_path in component.items():
        if driver_path:
            matched_parts = _match_files_with_driver(driver_path, files_json)
            all_parts.extend(matched_parts)
    return all_parts


def _get_dep_parts(mkdirs, files):
    all_parts = []
    files_json = json.loads(files)
    for path, component in mkdirs.items():
        if not component:
            continue
        elif len(component) == 1:
            all_parts.extend(_handle_single_component_case(path, component))
        else:
            all_parts.extend(_handle_multiple_component_case(component, files_json))
    return all_parts


def _match_files_with_driver(driver_path, files_json):
    matched_parts = []
    parts_s = driver_path.split('/')
    remaining_parts = '/'.join(parts_s[2:]) if len(parts_s) > 2 else ''
    for driver_name, files_list in files_json.items():
        for file in files_list:
            if file.startswith(remaining_parts):
                matched_parts.append(driver_name)
                break
    return matched_parts


def symlink_src2dest(src_dir, dest_dir):
    if os.path.exists(dest_dir):
        if os.path.islink(dest_dir):
            os.unlink(dest_dir)
        elif os.path.isdir(dest_dir):
            shutil.rmtree(dest_dir)
        else:
            os.remove(dest_dir)
    else:
        os.makedirs(os.path.dirname(dest_dir), exist_ok=True)

    print("symlink {} ---> {}".format(src_dir, dest_dir))
    os.symlink(src_dir, dest_dir)


def install_hpm(code_path, download_dir, symlink_dir, home_path):
    content = """\
package-lock=true
registry=http://repo.huaweicloud.com/repository/npm
strict-ssl=false
lockfile=false
"""
    with os.fdopen(os.open(os.path.join(home_path, '.npmrc'), os.O_WRONLY | os.O_CREAT, mode=0o640), 'w') as f:
        os.truncate(f.fileno(), 0)
        f.write(content)
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    with os.fdopen(os.open(os.path.join(download_dir, 'package.json'), os.O_WRONLY | os.O_CREAT, mode=0o640), 'w') as f:
        os.truncate(f.fileno(), 0)
        f.write('{}\n')
    npm_path = os.path.join(code_path, "prebuilts/build-tools/common/nodejs/current/bin/npm")
    node_bin_path = os.path.join(code_path, "prebuilts/build-tools/common/nodejs/current/bin")
    os.environ['PATH'] = f"{node_bin_path}:{os.environ['PATH']}"
    subprocess.run(
        [npm_path, 'install', '@ohos/hpm-cli', '--registry', 'https://repo.huaweicloud.com/repository/npm/', '--prefix',
         download_dir])
    symlink_src2dest(os.path.join(download_dir, 'node_modules'), symlink_dir)


def _prebuild_build():
    script_path = 'build/prebuilts_download.sh'
    try:
        result = subprocess.run(['bash', script_path], check=True, text=True)
        print("Script completed successfully with return code:", result.returncode)
    except subprocess.CalledProcessError as e:
        print("Script failed with return code:", e.returncode)
        print(e.stderr)
    commands = [
        ["pip3", "install", "--upgrade", "pip", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"],
        ["pip3", "install", "--upgrade", "jinja2", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"],
        ["pip3", "install", "--upgrade", "markupsafe", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"]
    ]
    for cmd in commands:
        try:
            result = subprocess.run(cmd, check=True)
            print(f"Command '{cmd}' completed successfully with return code {result.returncode}")
        except subprocess.CalledProcessError as e:
            print(f"Command '{cmd}' failed with return code {e.returncode}")
    paths_to_remove = [
        "/usr/local/lib/python3.8/dist-packages/hb",
        "/usr/local/bin/hb"
    ]
    install_command = ["python3", "-m", "pip", "install", "--user", "./build/hb"]
    for path in paths_to_remove:
        try:
            subprocess.run(["rm", "-rf", path], check=True)
            print(f"Successfully removed {path}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to remove {path} with return code {e.returncode}")
    try:
        subprocess.run(install_command, check=True)
        print("hb installation completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"hb installation failed with return code {e.returncode}")
    install_hpm('./', '/root/.prebuilts_cache/hpm/', './prebuilts/hpm/node_modules', '/root')


def _hb_build(part):
    new_path = os.path.expanduser('/root/.prebuilts_cache/hpm/node_modules/.bin')
    if new_path not in os.environ['PATH'].split(os.pathsep):
        os.environ['PATH'] = f"{new_path}{os.pathsep}{os.environ['PATH']}"
    try:
        subprocess.run(['hb', 'build', part, '-i'], check=True, text=True)
        print("hb build successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error: The command 'hb build {part} -i' failed with return code {e.returncode}.")
    command = [
        'python',
        './build/templates/common/generate_component_package.py',
        '-rp', './',
        '-op', './out/default/src',
        '-lt', '1',
        '-cl', part
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Command '{e.cmd}' returned non-zero exit status {e.returncode}.")
        print(f"Error output: {e.stderr}")


def _get_subsystem_names(part, parts_info_path):
    with open(parts_info_path, 'r', encoding='utf-8') as info_json:
        parts_info_json = json.load(info_json)
    for part_list in parts_info_json.values():
        for part_info in part_list:
            if part_info['part_name'] == part:
                return part_info['subsystem_name']
    return None


def _get_publicinfo_paths(subsystem_name, current_directory):
    publicinfo_path = os.path.join(current_directory, 'out', 'default', 'src', subsystem_name, '*', 'publicinfo')
    publicinfo_files = glob.glob(os.path.join(publicinfo_path, '*.json'), recursive=True)
    all_publicinfo_paths = set()
    for publicinfo_file in publicinfo_files:
        with open(publicinfo_file, 'r', encoding='utf-8') as f:
            publicinfo_json = json.load(f)
            all_publicinfo_paths.update(_process_public_configs(publicinfo_json))
    return all_publicinfo_paths


def _process_public_configs(publicinfo_json):
    publicinfo_paths = set()
    if 'public_configs' in publicinfo_json and isinstance(publicinfo_json['public_configs'], list):
        base_path = publicinfo_json.get('path', '').rstrip('/') + '/'
        for public_config in publicinfo_json['public_configs']:
            if 'include_dirs' in public_config and isinstance(public_config['include_dirs'], list):
                for include_dir in public_config['include_dirs']:
                    if include_dir.startswith(base_path):
                        publicinfo_paths.add(include_dir[len(base_path):])
    return publicinfo_paths


def _check_if_file_modifies_inner_api(change_file, publicinfo_paths):
    for publicinfo_path in publicinfo_paths:
        if change_file.startswith(publicinfo_path):
            return True
    return False


def _check_inner_api(part, files, current_directory):
    parts_info_path = os.path.join(current_directory, 'out', 'rk3568', 'build_configs', 'parts_info', 'parts_info.json')
    subsystem_name = _get_subsystem_names(part, parts_info_path)
    if not subsystem_name:
        print(f"The subsystem name for '{part}' is not found.")
        return False
    print(f"The subsystem name for '{part}' is: {subsystem_name}")

    publicinfo_paths = _get_publicinfo_paths(subsystem_name, current_directory)
    if not publicinfo_paths:
        print("No publicinfo paths found.")
        return False
    print(f"The publicinfo paths are: {publicinfo_paths}")

    files_json = json.loads(files)
    for parts_p, change_files in files_json.items():
        if any(_check_if_file_modifies_inner_api(change_file, publicinfo_paths) for change_file in change_files):
            print('The modification involves the inner API.')
            return True
    return False


def _create_datapart_json(alternative, changed):
    data = {
        'build.type': alternative,
        'innerAPI.changed': changed
    }
    json_str = json.dumps(data, indent=4)
    output_dir = os.path.join(CURRENT_DIRECTORY, 'out')
    output_file = 'dataPart.json'
    output_path = os.path.join(output_dir, output_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    with open(output_path, 'w') as f:
        f.write(json_str)


def _remove_directories(directory, exclude_pattern):
    try:
        result = subprocess.run(['ls', directory], check=True, capture_output=True, text=True)
        contents = result.stdout.strip().split('\n')
        for content in contents:
            full_path = os.path.join(directory, content)
            if os.path.isdir(full_path) and exclude_pattern not in content:
                subprocess.run(['rm', '-rf', full_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command '{e.cmd}' returned non-zero exit status {e.returncode}.")


def _build_pre_compile():
    pr_list = os.getenv('pr_list')
    if not pr_list:
        _remove_prebuilts()
    _install_dependencies()
    if os.path.exists('out'):
        _clean_out_directory(exclude_pattern='kernel')
    else:
        print("'out' directory does not exist, skipping cleanup.")
    _remove_tar_gz_files_in_prebuilts()
    print("Pre-compile step completed successfully.")


def _remove_prebuilts():
    subprocess.run(['rm', '-rf', 'prebuilts/ohos-sdk'], check=True)
    subprocess.run(['rm', '-rf', 'prebuilts/build-tools/common/oh-command-line-tools'], check=True)


def _install_dependencies():
    subprocess.run(
        ['sudo', 'apt-get', 'install', '-y', 'libxinerama-dev', 'libxcursor-dev', 'libxrandr-dev', 'libxi-dev'],
        check=True)
    subprocess.run(['sudo', 'apt-get', 'install', '-y', 'gcc-multilib'], check=True)


def _clean_out_directory(exclude_pattern):
    _remove_directories('out', exclude_pattern)


def _remove_tar_gz_files_in_prebuilts():
    subprocess.run(['rm', '-rf', './prebuilts/*.tar.gz'], check=True)


def _build_dayu200():
    _build_pre_compile()
    current_env = os.environ.copy()
    current_env['CCACHE_BASE'] = os.getcwd()
    current_env['NO_DEVTOOL'] = '1'
    current_env['CCACHE_LOG_SUFFIX'] = 'dayu200-arm32'
    current_env['CCACHE_NOHASHDIR'] = 'true'
    current_env['CCACHE_SLOPPINESS'] = 'include_file_ctime'
    gn_args_dict = {
        'ohos_components_checktype': '3',
        'use_thin_lto': 'false',
        'load_test_config': 'false',
        'enable_lto_O0': 'true',
        'enable_notice_collection': 'false',
        'skip_generate_module_list_file': 'true'
    }
    gn_args_list = [f'{key}={value}' if value else key for key, value in gn_args_dict.items()]
    gn_args_correct = f'--gn-args {" ".join(gn_args_list)}'
    cmd = [
        './build.sh',
        '--product-name', 'rk3568',
        '--ccache',
        '--build-target', 'make_all',
        gn_args_correct,
        '--disable-package-image',
        '--disable-part-of-post-build', 'output_part_rom_status',
        '--disable-part-of-post-build', 'get_warning_list',
        '--disable-part-of-post-build', 'compute_overlap_rate'
    ]
    result = subprocess.run(cmd, env=current_env, check=True, text=True)
    print("Return compile cmd:", result.returncode)
    _build_after_compile()


def _build_after_compile():
    work_dir = os.getcwd()
    command1 = [
        "python",
        os.path.join(work_dir, "developtools/integration_verification/tools/deps_guard/deps_guard.py"),
        "-i",
        os.path.join(work_dir, "./out/rk3568")
    ]
    subprocess.run(command1, check=True)
    command2 = ["rm", "-rf", os.path.join(work_dir, "out/rk3568/exe.unstripped/tests")]
    subprocess.run(command2, check=True)
    command3 = ["rm", "-rf", os.path.join(work_dir, "screenshot")]
    subprocess.run(command3, check=True)
    command4 = ["cp", "-r",
                os.path.join(work_dir, "developtools/integration_verification/cases/smoke/basic/screenshot32"),
                os.path.join(work_dir, "screenshot")]
    subprocess.run(command4, check=True)
    command5 = ["rm", "-rf", os.path.join(work_dir, "DeployDevice")]
    subprocess.run(command5, check=True)
    command6 = ["cp", "-r", os.path.join(work_dir, "developtools/integration_verification/DeployDevice"),
                os.path.join(work_dir, "DeployDevice")]
    subprocess.run(command6, check=True)
    print("Return after compile: success")


def images_cmmands(depfile, image_name, input_path, image_config_file, deviceimage_config_file, output_image):
    images_command = ["../../build/ohos/images/build_image.py"]
    images_command.append("--depfile")
    images_command.append(depfile)
    images_command.append("--image-name")
    images_command.append(image_name)
    images_command.append("--input-path")
    images_command.append(input_path)
    images_command.append("--image-config-file")
    images_command.append(image_config_file)
    images_command.append("--device-image-config-file")
    images_command.append(deviceimage_config_file)
    images_command.append("--output-image")
    images_command.append(output_image)
    images_command.append("--target-cpu")
    images_command.append("arm")
    images_command.append("--build-variant")
    images_command.append("root")
    images_command.append("--build-image-tools-path")
    images_command.append("clang_x64/thirdparty/e2fsprogs")
    images_command.append("clang_x64/thirdparty/f2fs-tools")
    images_command.append("../../third_party/e2fsprogs/prebuilt/host/bin")
    images_command.append("../../build/ohos/images/mkimage")
    return images_command


def get_images_commands():
    images_commands = [
        {
            "echo": "update chip_ckm.img in packages/phone/images",
            "cmd": [
                "../../build/ohos/images/mkimage/mkchip_ckm.py",
                "--src-dir", "packages/phone/chip_ckm",
                "--device-name", "packages/phone/images/chip_ckm.img",
                "--config-file-path", "../../build/ohos/images/mkimage/chip_ckm.txt",
                "--mkextimage-tools-path", "../../build/ohos/images/mkimage/mkextimage.py",
                "--build-image-tools-path", "clang_x64/thirdparty/f2fs-tools",
                "clang_x64/thirdparty/e2fsprogs",
                "../../third_party/e2fsprogs/prebuilt/host/bin"
            ]
        },
        {
            "echo": "update chip_prod.img in packages/phone/images",
            "cmd": images_cmmands("gen/build/ohos/images/phone_chip_prod_image.d", "chip_prod",
                                  "packages/phone/chip_prod",
                                  "../../build/ohos/images/mkimage/chip_prod_image_conf.txt",
                                  "packages/imagesconf/chip_prod_image_conf.txt", "packages/phone/images/chip_prod.img")
        },
        {
            "echo": "update ramdisk.img in packages/phone/images",
            "cmd": images_cmmands("gen/build/ohos/images/phone_ramdisk_image.d", "ramdisk", "packages/phone/ramdisk",
                                  "../../build/ohos/images/mkimage/ramdisk_image_conf.txt",
                                  "packages/imagesconf/ramdisk_image_conf.txt", "ramdisk.img")
        },
        {
            "echo": "update eng_chipset.img in packages/phone/images",
            "cmd": images_cmmands("gen/build/ohos/images/phone_eng_chipset_image.d", "eng_chipset",
                                  "packages/phone/eng_chipset",
                                  "../../build/ohos/images/mkimage/eng_chipset_image_conf.txt",
                                  "packages/imagesconf/eng_chipset_image_conf.txt",
                                  "packages/phone/images/eng_chipset.img")
        },
        {
            "echo": "update eng_system.img in packages/phone/images",
            "cmd": images_cmmands("gen/build/ohos/images/phone_eng_system_image.d", "eng_system",
                                  "packages/phone/eng_system",
                                  "../../build/ohos/images/mkimage/eng_system_image_conf.txt",
                                  "packages/imagesconf/eng_system_image_conf.txt",
                                  "packages/phone/images/eng_system.img")
        },
        {
            "echo": "update sys_prod.img in packages/phone/images",
            "cmd": images_cmmands("gen/build/ohos/images/phone_sys_prod_image.d", "sys_prod", "packages/phone/sys_prod",
                                  "../../build/ohos/images/mkimage/sys_prod_image_conf.txt",
                                  "packages/imagesconf/sys_prod_image_conf.txt", "packages/phone/images/sys_prod.img")
        },
        {
            "echo": "update system.img in packages/phone/images",
            "cmd": images_cmmands("gen/build/ohos/images/phone_system_image.d", "system", "packages/phone/system",
                                  "../../build/ohos/images/mkimage/system_image_conf.txt",
                                  "packages/imagesconf/system_image_conf.txt", "packages/phone/images/system.img")
        },
        {
            "echo": "update updater_ramdisk.img in packages/phone/images",
            "cmd": images_cmmands("gen/build/ohos/images/phone_updater_ramdisk_image.d", "updater_ramdisk",
                                  "packages/phone/updater",
                                  "../../build/ohos/images/mkimage/updater_ramdisk_image_conf.txt",
                                  "packages/imagesconf/updater_ramdisk_image_conf.txt", "updater_ramdisk.img")
        },
        {
            "echo": "update userdata.img in packages/phone/images",
            "cmd": images_cmmands("gen/build/ohos/images/phone_userdata_image.d", "userdata", "packages/phone/data",
                                  "../../build/ohos/images/mkimage/userdata_image_conf.txt",
                                  "packages/imagesconf/userdata_image_conf.txt", "packages/phone/images/userdata.img")
        },
        {
            "echo": "update vendor.img in packages/phone/images",
            "cmd": images_cmmands("gen/build/ohos/images/phone_vendor_image.d", "vendor", "packages/phone/vendor",
                                  "../../build/ohos/images/mkimage/vendor_image_conf.txt",
                                  "packages/imagesconf/vendor_image_conf.txt", "packages/phone/images/vendor.img")
        }
    ]
    return images_commands


def regenerate_packages_images():
    work_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(work_dir, 'out', 'rk3568')
    os.chdir(out_dir)
    current_dir = os.getcwd()
    print(f"The current dir is {current_dir}")
    print("The third step: begin to regenerate img files, please wait ...")
    images_commands = get_images_commands()
    for cmd_info in images_commands:
        print(cmd_info["echo"])
        try:
            result = subprocess.run(cmd_info["cmd"], check=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {cmd_info['cmd']}")
            print(f"Return code: {e.returncode}")
            print(f"Error output: {e.stderr}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    print("The third step finished successfully")
    os.chdir(os.path.dirname(os.path.dirname(work_dir)))


def build_trees(part, list_text, files, paths):
    if not part:
        _build_dayu200()
        print('Prebuilt build')
    indep_components = list_text['data']['indep_list']
    if len(part) == 1 and part[0] in indep_components:
        print('Independent compilation')
        _prebuild_build()
        _hb_build(part[0])
        if _check_inner_api(part[0], files, CURRENT_DIRECTORY):
            _create_datapart_json(1, True)
            _build_dayu200()
        else:
            _create_datapart_json(1, False)
            replace_part_sofile(part[0], './', './')
            regenerate_packages_images()
    elif len(part) > 1 and all(item in indep_components for item in other_list) and len(part) == len(paths):
        _build_dayu200()
        print('Multiple independent components being compiled together')
    else:
        _create_datapart_json(3, True)
        print('Inherited dayu200 result or dependent compilation')


if __name__ == '__main__':
    # request_param = _get_export_project('project_list')
    request_param = ['account_os_account']
    if not request_param:
        subprocess.run(['./build/prebuilts_download.sh'], check=True, text=True)
        _build_dayu200()
        print('Prebuilt build')
    else:
        mkdir_text = _get_api_mkdir(request_param)
        # file_list = _get_export_files('PR_FILE_PATHS')
        file_list = "{\"account_os_account\":[\"crypto/src/napi_asy_key_generator.cpp\"]}"
        parts = _get_dep_parts(mkdir_text, file_list)
        whitelist_parts = _get_part_list()
        build_trees(parts, whitelist_parts, file_list, request_param)
