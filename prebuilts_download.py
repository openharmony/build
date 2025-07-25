#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2022 Huawei Device Co., Ltd.
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

import os
import sys
import argparse
import subprocess
import ssl
import shutil
import importlib
import time
import pathlib
import re
from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from urllib.request import urlopen
import urllib.error
from scripts.util.file_utils import read_json_file


def _run_cmd(cmd: str):
    res = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    sout, serr = res.communicate()
    return sout.rstrip().decode('utf-8'), serr, res.returncode


def _check_sha256(check_url: str, local_file: str) -> bool:
    check_sha256_cmd = 'curl -s -k ' + check_url + '.sha256'
    local_sha256_cmd = 'sha256sum ' + local_file + "|cut -d ' ' -f1"
    check_sha256, err, returncode = _run_cmd(check_sha256_cmd)
    local_sha256, err, returncode = _run_cmd(local_sha256_cmd)
    if check_sha256 != local_sha256:
        print('remote file {}.sha256 is not found, begin check SHASUMS256.txt'.format(check_url))
        check_sha256 = _obtain_sha256_by_sha_sums256(check_url)
    return check_sha256 == local_sha256


def _check_sha256_by_mark(args, check_url: str, code_dir: str, unzip_dir: str, unzip_filename: str) -> bool:
    check_sha256_cmd = 'curl -s -k ' + check_url + '.sha256'
    check_sha256, err, returncode = _run_cmd(check_sha256_cmd)
    mark_file_dir = os.path.join(code_dir, unzip_dir)
    mark_file_name = check_sha256 + '.' + unzip_filename + '.mark'
    mark_file_path = os.path.join(mark_file_dir, mark_file_name)
    args.mark_file_path = mark_file_path
    return os.path.exists(mark_file_path)


def _obtain_sha256_by_sha_sums256(check_url: str) -> str:
    sha_sums256 = 'SHASUMS256.txt'
    sha_sums256_path = os.path.join(os.path.dirname(check_url), sha_sums256)
    file_name = os.path.basename(check_url)
    cmd = 'curl -s -k ' + sha_sums256_path
    data_sha_sums256, err, returncode = _run_cmd(cmd)
    check_sha256 = None
    for line in data_sha_sums256.split('\n'):
        if file_name in line:
            check_sha256 = line.split(' ')[0]
    return check_sha256


def _config_parse(config: dict, tool_repo: str, glibc_version: str) -> dict:
    parse_dict = dict()
    parse_dict['unzip_dir'] = config.get('unzip_dir')
    file_path = config.get('file_path')
    if 'python' in file_path and glibc_version is not None:
        file_path = re.sub(r'GLIBC[0-9]\.[0-9]{2}', glibc_version, file_path)
    parse_dict['huaweicloud_url'] = tool_repo + file_path
    parse_dict['unzip_filename'] = config.get('unzip_filename')
    md5_huaweicloud_url_cmd = 'echo ' + parse_dict.get('huaweicloud_url') + "|md5sum|cut -d ' ' -f1"
    parse_dict['md5_huaweicloud_url'], err, returncode = _run_cmd(md5_huaweicloud_url_cmd)
    parse_dict['bin_file'] = os.path.basename(parse_dict.get('huaweicloud_url'))
    return parse_dict


def _uncompress(args, src_file: str, code_dir: str, unzip_dir: str, unzip_filename: str, mark_file_path: str):
    dest_dir = os.path.join(code_dir, unzip_dir)
    if src_file[-3:] == 'zip':
        cmd = 'unzip -o {} -d {};echo 0 > {}'.format(src_file, dest_dir, mark_file_path)
    elif src_file[-6:] == 'tar.gz':
        cmd = 'tar -xvzf {} -C {};echo 0 > {}'.format(src_file, dest_dir, mark_file_path)
    else:
        cmd = 'tar -xvf {} -C {};echo 0 > {}'.format(src_file, dest_dir, mark_file_path)
    _run_cmd(cmd)


def _copy_url(args, task_id: int, url: str, local_file: str, code_dir: str, unzip_dir: str,
              unzip_filename: str, mark_file_path: str, progress):
    retry_times = 0
    max_retry_times = 3
    while retry_times < max_retry_times:
        # download files
        download_buffer_size = 32768
        progress.console.log('Requesting {}'.format(url))
        try:
            response = urlopen(url)
        except urllib.error.HTTPError as e:
            progress.console.log("Failed to open {}, HTTPError: {}".format(url, e.code), style='red')
        progress.update(task_id, total=int(response.info()["Content-length"]))
        with open(local_file, "wb") as dest_file:
            progress.start_task(task_id)
            for data in iter(partial(response.read, download_buffer_size), b""):
                dest_file.write(data)
                progress.update(task_id, advance=len(data))
        progress.console.log("Downloaded {}".format(local_file))

        if os.path.exists(local_file):
            if _check_sha256(url, local_file):
                # decompressing files
                progress.console.log("Decompressing {}".format(local_file))
                _uncompress(args, local_file, code_dir, unzip_dir, unzip_filename, mark_file_path)
                progress.console.log("Decompressed {}".format(local_file))
                break
            else:
                os.remove(local_file)
        retry_times += 1
    if retry_times == max_retry_times:
        print('{}, download failed with three times retry, please check network status. Prebuilts download exit.'.format(local_file))
        # todo, merge with copy_url_disable_rich
        sys.exit(1)


def _copy_url_disable_rich(args, url: str, local_file: str, code_dir: str, unzip_dir: str,
                           unzip_filename: str, mark_file_path: str):
    # download files
    download_buffer_size = 32768
    print('Requesting {}, please wait'.format(url))
    try:
        response = urlopen(url)
    except urllib.error.HTTPError as e:
        print("Failed to open {}, HTTPError: {}".format(url, e.code))
    with open(local_file, "wb") as dest_file:
        for data in iter(partial(response.read, download_buffer_size), b""):
            dest_file.write(data)
    print("Downloaded {}".format(local_file))

    # decompressing files
    print("Decompressing {}, please wait".format(local_file))
    _uncompress(args, local_file, code_dir, unzip_dir, unzip_filename, mark_file_path)
    print("Decompressed {}".format(local_file))


def _is_system_component() -> bool:
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if pathlib.Path(os.path.join(root_dir, 'interface', 'sdk-js')).exists() or pathlib.Path(
            os.path.join(root_dir, 'foundation', 'arkui')).exists() or pathlib.Path(
            os.path.join(root_dir, 'arkcompiler')).exists():
        return True
    else:
        return False


def _hwcloud_download(args, config: dict, bin_dir: str, code_dir: str, glibc_version: str):
    try:
        cnt = cpu_count()
    except Exception as e:
        cnt = 1
    with ThreadPoolExecutor(max_workers=cnt) as pool:
        tasks = dict()
        for config_info in config:
            parse_dict = _config_parse(config_info, args.tool_repo, glibc_version)
            unzip_dir = parse_dict.get('unzip_dir')
            huaweicloud_url = parse_dict.get('huaweicloud_url')
            unzip_filename = parse_dict.get('unzip_filename')
            md5_huaweicloud_url = parse_dict.get('md5_huaweicloud_url')
            bin_file = parse_dict.get('bin_file')
            abs_unzip_dir = os.path.join(code_dir, unzip_dir)
            if not os.path.exists(abs_unzip_dir):
                os.makedirs(abs_unzip_dir, exist_ok=True)
            if _check_sha256_by_mark(args, huaweicloud_url, code_dir, unzip_dir, unzip_filename):
                if not args.disable_rich:
                    args.progress.console.log('{}, Sha256 markword check OK.'.format(huaweicloud_url), style='green')
                else:
                    print('{}, Sha256 markword check OK.'.format(huaweicloud_url))
            else:
                _run_cmd(('rm -rf {}/{}/*.{}.mark').format(code_dir, unzip_dir, unzip_filename))
                _run_cmd(('rm -rf {}/{}/{}').format(code_dir, unzip_dir, unzip_filename))
                local_file = os.path.join(bin_dir, '{}.{}'.format(md5_huaweicloud_url, bin_file))
                if os.path.exists(local_file):
                    if _check_sha256(huaweicloud_url, local_file):
                        if not args.disable_rich:
                            args.progress.console.log('{}, Sha256 check download OK.'.format(local_file), style='green')
                        else:
                            print('{}, Sha256 check download OK. Start decompression, please wait'.format(local_file))
                        task = pool.submit(_uncompress, args, local_file, code_dir, 
                                           unzip_dir, unzip_filename, args.mark_file_path)
                        tasks[task] = os.path.basename(huaweicloud_url)
                        continue
                    else:
                        os.remove(local_file)
                filename = huaweicloud_url.split("/")[-1]
                if not args.disable_rich:
                    task_id = args.progress.add_task("download", filename=filename, start=False)
                    task = pool.submit(_copy_url, args, task_id, huaweicloud_url, local_file, code_dir,
                                    unzip_dir, unzip_filename, args.mark_file_path, args.progress)
                    tasks[task] = os.path.basename(huaweicloud_url)
                else:
                    task = pool.submit(_copy_url_disable_rich, args, huaweicloud_url, local_file, code_dir,
                                        unzip_dir, unzip_filename, args.mark_file_path)

        for task in as_completed(tasks):
            if not args.disable_rich:
                args.progress.console.log('{}, download and decompress completed'.format(tasks.get(task)),
                style='green')
            else:
                print('{}, download and decompress completed'.format(tasks.get(task)))


def _npm_install(args):
    node_path = 'prebuilts/build-tools/common/nodejs/current/bin'
    os.environ['PATH'] = '{}/{}:{}'.format(args.code_dir, node_path, os.environ.get('PATH'))
    npm = os.path.join(args.code_dir, node_path, 'npm')
    if args.skip_ssl:
        skip_ssl_cmd = '{} config set strict-ssl false;'.format(npm)
        out, err, retcode = _run_cmd(skip_ssl_cmd)
        if retcode != 0:
            return False, err.decode()
    npm_clean_cmd = '{} cache clean -f'.format(npm)
    npm_package_lock_cmd = '{} config set package-lock true'.format(npm)
    out, err, retcode = _run_cmd(npm_clean_cmd)
    if retcode != 0:
        return False, err.decode()
    out, err, retcode = _run_cmd(npm_package_lock_cmd)
    if retcode != 0:
        return False, err.decode()
    install_cmds = []
    full_code_paths = []
            
    print('start npm install, please wait.')
    for install_info in args.npm_install_config:
        full_code_path = os.path.join(args.code_dir, install_info)
        if full_code_path in args.success_installed:
            print('{} has been installed, skip'.format(full_code_path))
            continue
        basename = os.path.basename(full_code_path)
        node_modules_path = os.path.join(full_code_path, "node_modules")
        npm_cache_dir = os.path.join('~/.npm/_cacache', basename)
        if os.path.exists(node_modules_path):
            print('remove node_modules %s' % node_modules_path)
            _run_cmd(('rm -rf {}'.format(node_modules_path)))
        if os.path.exists(full_code_path):
            cmd = ['timeout', '-s', '9', '90s', npm, 'install', '--registry', args.npm_registry, '--cache', npm_cache_dir]
            if args.host_platform == 'darwin':
                cmd = [npm, 'install', '--registry', args.npm_registry, '--cache', npm_cache_dir]
            if args.unsafe_perm:
                cmd.append('--unsafe-perm')
            install_cmds.append(cmd)
            full_code_paths.append(full_code_path)
        else:
            raise Exception("{} not exist, it shouldn't happen, pls check...".format(full_code_path))
    
    if args.parallel_install:
        procs = []
        for index, install_cmd in enumerate(install_cmds):
            proc = subprocess.Popen(install_cmd, cwd=full_code_paths[index], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print('run npm install in {}'.format(full_code_paths[index]))
            time.sleep(0.1)
            procs.append(proc)
        for index, proc in enumerate(procs):
            out, err = proc.communicate()
            if proc.returncode:
                print("in dir:{}, executing:{}".format(full_code_paths[index], ' '.join(install_cmds[index])))
                return False, err.decode()
            args.success_installed.append(full_code_paths[index])

    else:
        for index, install_cmd in enumerate(install_cmds):
            proc = subprocess.Popen(install_cmd, cwd=full_code_paths[index], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print('run npm install in {}'.format(full_code_paths[index]))
            time.sleep(0.1)
            out, err = proc.communicate()
            if proc.returncode:
                print("in dir:{}, executing:{}".format(full_code_paths[index], ' '.join(install_cmds[index])))
                return False, err.decode()
            args.success_installed.append(full_code_paths[index])
    return True, None


def _node_modules_copy(config: dict, code_dir: str, enable_symlink: bool):
    for config_info in config:
        src_dir = os.path.join(code_dir, config_info.get('src'))
        if not os.path.exists(src_dir):
            print(f"{src_dir} not exist, skip node_modules copy.")
            continue
        dest_dir = os.path.join(code_dir, config_info.get('dest'))
        use_symlink = config_info.get('use_symlink')
        if os.path.exists(os.path.dirname(dest_dir)):
            shutil.rmtree(os.path.dirname(dest_dir))
        if use_symlink == 'True' and enable_symlink == True:
            os.makedirs(os.path.dirname(dest_dir), exist_ok=True)
            os.symlink(src_dir, dest_dir)
        else:
            shutil.copytree(src_dir, dest_dir, symlinks=True)


def _do_rename(config_info: dict, code_dir: str, host_platform: str, host_cpu: str):
    src_dir = code_dir + config_info.get('src')
    dest_dir = code_dir + config_info.get('dest')
    symlink_src = config_info.get('symlink_src')
    symlink_dest = config_info.get('symlink_dest')
    if os.path.exists(dest_dir) and dest_dir != src_dir:
        shutil.rmtree(dest_dir)
    shutil.move(src_dir, dest_dir)
    if symlink_src and symlink_dest and os.path.exists(src_dir + symlink_src):
        if os.path.exists(dest_dir + symlink_dest) and os.path.islink(dest_dir + symlink_dest):
            os.unlink(dest_dir + symlink_dest)
        if os.path.exists(dest_dir + symlink_dest) and os.path.isfile(dest_dir + symlink_dest):
            os.remove(dest_dir + symlink_dest)
        if os.path.exists(dest_dir + symlink_dest) and os.path.isdir(dest_dir + symlink_dest):
            shutil.rmtree(dest_dir + symlink_dest)
        os.symlink(os.path.basename(symlink_src), dest_dir + symlink_dest)


def _handle_tmp(tmp_dir: str, src_dir: str, dest_dir: str):
    shutil.move(src_dir, tmp_dir)
    cmd = 'mv {}/*.mark {}'.format(dest_dir, tmp_dir)
    _run_cmd(cmd)
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    shutil.move(tmp_dir, dest_dir)


def _file_handle(config: dict, code_dir: str, host_platform: str, host_cpu: str):
    for config_info in config:
        src_dir = code_dir + config_info.get('src')
        dest_dir = code_dir + config_info.get('dest')
        tmp_dir = config_info.get('tmp')
        rename = config_info.get('rename')
        if os.path.exists(src_dir):
            if tmp_dir:
                tmp_dir = code_dir + tmp_dir
                _handle_tmp(tmp_dir, src_dir, dest_dir)
            elif rename:
                _do_rename(config_info, code_dir, host_platform, host_cpu)
            else:
                _run_cmd('chmod 755 {} -R'.format(dest_dir))


def _import_rich_module():
    module = importlib.import_module('rich.progress')
    progress = module.Progress(
        module.TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
        module.BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        module.DownloadColumn(),
        "•",
        module.TransferSpeedColumn(),
        "•",
        module.TimeRemainingColumn(),
    )
    return progress


def _install(config: dict, code_dir: str):
    for config_info in config:
        install_dir = '{}/{}'.format(code_dir, config_info.get('install_dir'))
        script = config_info.get('script')
        cmd = '{}/{}'.format(install_dir, script)
        args = config_info.get('args')
        for arg in args:
            for key in arg.keys():
                cmd = '{} --{}={}'.format(cmd, key, arg[key])
        dest_dir = '{}/{}'.format(code_dir, config_info.get('destdir'))
        cmd = '{} --destdir={}'.format(cmd, dest_dir)
        _run_cmd(cmd)


def _build_copy_config(config_info: dict, host_platform: str, host_cpu: str):
    copy_config = config_info.get(host_platform).get(host_cpu).get('copy_config')
    node_config = config_info.get(host_platform).get('node_config')
    if node_config is None:
        node_config = config_info.get(host_platform).get(host_cpu).get('node_config')
    copy_config.extend(node_config)
    if host_platform == 'linux':
        linux_copy_config = config_info.get(host_platform).get(host_cpu).get('linux_copy_config')
        copy_config.extend(linux_copy_config)
    elif host_platform == 'darwin':
        darwin_copy_config = config_info.get(host_platform).get(host_cpu).get('darwin_copy_config')
        copy_config.extend(darwin_copy_config)
    return copy_config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip-ssl', action='store_true', help='skip ssl authentication')
    parser.add_argument('--unsafe-perm', action='store_true', help='add "--unsafe-perm" for npm install')
    parser.add_argument('--disable-rich', action='store_true', help='disable the rich module')
    parser.add_argument('--enable-symlink', action='store_true', help='enable symlink while copying node_modules')
    parser.add_argument('--build-arkuix', action='store_true', help='build ArkUI-X SDK')
    parser.add_argument('--tool-repo', default='https://repo.huaweicloud.com', help='prebuilt file download source')
    parser.add_argument('--npm-registry', default='https://repo.huaweicloud.com/repository/npm/',
                        help='npm download source')
    parser.add_argument('--host-cpu', help='host cpu', required=True)
    parser.add_argument('--host-platform', help='host platform', required=True)
    parser.add_argument('--glibc-version', help='glibc version', required=False)
    parser.add_argument('--config-file', help='prebuilts download config file')
    args = parser.parse_args()
    args.code_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if args.skip_ssl:
        ssl._create_default_https_context = ssl._create_unverified_context

    host_platform = args.host_platform
    host_cpu = args.host_cpu
    glibc_version = args.glibc_version
    tool_repo = args.tool_repo
    if args.build_arkuix:
        config_file = os.path.join(args.code_dir, 'build_plugins/prebuilts_download_config.json')
    elif args.config_file:
        config_file = args.config_file
    else:
        config_file = os.path.join(args.code_dir, 'build/prebuilts_download_config.json')
    config_info = read_json_file(config_file)
    if _is_system_component():
        args.npm_install_config = config_info.get('npm_install_path')
        node_modules_copy_config = config_info.get('node_modules_copy')
    else:
        args.npm_install_config = []
        node_modules_copy_config = []
    file_handle_config = config_info.get('file_handle_config')

    args.bin_dir = os.path.join(args.code_dir, config_info.get('prebuilts_download_dir'))
    if not os.path.exists(args.bin_dir):
        os.makedirs(args.bin_dir, exist_ok=True)
    copy_config = _build_copy_config(config_info, host_platform, host_cpu)
    if args.disable_rich:
        _hwcloud_download(args, copy_config, args.bin_dir, args.code_dir, glibc_version)
    else:
        args.progress = _import_rich_module()
        with args.progress:
            _hwcloud_download(args, copy_config, args.bin_dir, args.code_dir, glibc_version)

    _file_handle(file_handle_config, args.code_dir, args.host_platform, host_cpu)
    install_config = config_info.get(host_platform).get(host_cpu).get('install')
    retry_times = 0
    max_retry_times = 2
    args.success_installed = []
    args.parallel_install = True
    while retry_times <= max_retry_times:
        result, error = _npm_install(args)
        if result:
            break
        print("npm install error, error info: %s" % error)
        args.parallel_install = False
        if retry_times == max_retry_times:
            for error_info in error.split('\n'):
                if error_info.endswith('debug.log'):
                    log_path = error_info.split()[-1]
                    cmd = ['cat', log_path]
                    process_cat = subprocess.Popen(cmd)
                    process_cat.communicate(timeout=60)
                    raise Exception("npm install error with three times, prebuilts download exit")
        retry_times += 1
    _node_modules_copy(node_modules_copy_config, args.code_dir, args.enable_symlink)
    if install_config:
        _install(install_config, args.code_dir)

    # delete uninstalled tools
    uninstalled_tools = config_info.get('uninstalled_tools')
    for tool_path in uninstalled_tools:
        subprocess.run(['rm', '-rf', tool_path])

if __name__ == '__main__':
    sys.exit(main())
