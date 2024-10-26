#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2023 Huawei Device Co., Ltd.
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


import requests
import json
import datetime
import os
import sys
import tarfile
import subprocess
import argparse
import shutil

from urllib.request import urlretrieve


def find_top():
    cur_dir = os.getcwd()
    while cur_dir != "/":
        build_scripts = os.path.join(
            cur_dir, 'build/config/BUILDCONFIG.gn')
        if os.path.exists(build_scripts):
            return cur_dir
        cur_dir = os.path.dirname(cur_dir)


def reporthook(data_download, data_size, total_size):
    '''
    display the progress of download
    :param data_download: data downloaded
    :param data_size: data size
    :param total_size: remote file size
    :return:None
    '''
    print("\rdownloading: %5.1f%%" % (data_download * data_size * 100.0 / total_size), end="")


def download(download_url, savepath):
    filename = os.path.basename(download_url)

    if not os.path.isfile(os.path.join(savepath, filename)):
        print('Downloading data form %s' % download_url)
        urlretrieve(download_url, os.path.join(
            savepath, filename), reporthook=reporthook)
        print('\nDownload finished!')
    else:
        print("\nFile exsits!")

    filesize = os.path.getsize(os.path.join(savepath, filename))
    print('File size = %.2f Mb' % (filesize / 1024 / 1024))


def extract_file(filename):

    target_dir = os.path.dirname(filename)

    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
    with tarfile.open(filename, "r:gz") as tar:
        tar.extractall(target_dir)

    if os.path.exists(os.path.join(target_dir, "daily_build.log")):
        os.remove(os.path.join(target_dir, "daily_build.log"))
    if os.path.exists(os.path.join(target_dir, "manifest_tag.xml")):
        os.remove(os.path.join(target_dir, "manifest_tag.xml"))


def unzip_inner_packages(target_dir, api_version):

    sdk_zip_file_dir = os.path.join(target_dir, "ohos-sdk/linux")
    sdk_unzip_dir = os.path.join(sdk_zip_file_dir, api_version)

    if os.path.exists(sdk_unzip_dir):
        shutil.rmtree(sdk_unzip_dir)
    os.makedirs(sdk_unzip_dir, exist_ok=True)
    os.chdir(sdk_zip_file_dir)
    for filename in os.listdir(sdk_zip_file_dir):
        if filename.endswith('.zip'):
            subprocess.run(['mv', filename, sdk_unzip_dir])

    procs = []
    os.chdir(sdk_unzip_dir)
    for filename in os.listdir(sdk_unzip_dir):
        if filename.endswith('.zip'):
            cmd = ['unzip', filename]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            procs.append(proc)
    for proc in procs:
        out, error = proc.communicate(timeout=60)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--branch', default='master', help='OHOS branch name')
    parser.add_argument('--product-name', default='ohos-sdk-full', help='OHOS product name')
    parser.add_argument('--api-version', default='10', help='OHOS sdk api version')
    args = parser.parse_args()
    default_save_path = os.path.join(find_top(), 'prebuilts')
    if not os.path.exists(default_save_path):
        os.makedirs(default_save_path, exist_ok=True)
    print(default_save_path)
    try:
        now_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        last_hour = (datetime.datetime.now() +
                     datetime.timedelta(hours=-72)).strftime('%Y%m%d%H%M%S')

        url = "http://ci.openharmony.cn/api/daily_build/build/tasks"
        myobj = {"pageNum": 1,
                 "pageSize": 1000,
                 "startTime": "",
                 "endTime": "",
                 "projectName": "openharmony",
                 "branch": args.branch,
                 "component": "",
                 "deviceLevel": "",
                 "hardwareBoard": "",
                 "buildStatus": "success",
                 "buildFailReason": "",
                 "testResult": ""}
        myobj["startTime"] = str(last_hour)
        myobj["endTime"] = str(now_time)
        x = requests.post(url, json=myobj)
        data = json.loads(x.text)
    except BaseException:
        Exception("Unable to establish connection with ci.openharmony.cn")

    products_list = data['data']['dailyBuildVos']
    for product in products_list:
        product_name = product['component']
        if product_name == args.product_name:
            if os.path.exists(os.path.join(default_save_path, product_name)):
                print('{} already exists. Please backup or delete it first! Download canceled!'.format(
                    os.path.join(default_save_path, product_name)))
                break

            if product['obsPath'] and os.path.exists(default_save_path):
                download_url = 'http://download.ci.openharmony.cn/{}'.format(product['obsPath'])
                save_path2 = default_save_path

            try:
                download(download_url, savepath=save_path2)
                print(download_url, "done")
            except BaseException:

                # remove the incomplete downloaded files
                if os.path.exists(os.path.join(save_path2, os.path.basename(download_url))):
                    os.remove(os.path.join(
                        save_path2, os.path.basename(download_url)))
                Exception("Unable to download {}".format(download_url))

            extract_file(os.path.join(
                save_path2, os.path.basename(download_url)))
            unzip_inner_packages(save_path2, args.api_version)
            break


if __name__ == '__main__':
    sys.exit(main())
