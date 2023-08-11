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
    progress = int(0)
    if progress != int(data_download * data_size * 1000 / total_size):
        progress = int(data_download * data_size * 1000 / total_size)
        print("\rDownloading: %5.1f%%" %
              (data_download * data_size * 100.0 / total_size), end="")
        sys.stdout.flush()


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
    print('File size = %.2f Mb' % (filesize/1024/1024))


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


def npm_install(target_dir):

    sdk_dir = os.path.join(target_dir, "ohos-sdk/linux")
    os.chdir(sdk_dir)
    subprocess.run(['ls', '-d', '*/', '|', 'xargs', 'rm', '-rf'])

    for filename in os.listdir(sdk_dir):
        if filename.endswith(".zip"):
            os.system(f"unzip {filename}")

    p1 = subprocess.Popen(
        ["grep", "apiVersion", "toolchains/oh-uni-package.json"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["awk", "{print $2}"],
                          stdin=p1.stdout, stdout=subprocess.PIPE)
    p3 = subprocess.Popen(["sed", "-r", "s/\",?//g"],
                          stdin=p2.stdout, stdout=subprocess.PIPE)
    output = p3.communicate(timeout=5)[0]
    api_version = output.decode("utf-8").strip()

    p4 = subprocess.Popen(
        ["grep", "version", "toolchains/oh-uni-package.json"], stdout=subprocess.PIPE)
    p5 = subprocess.Popen(["awk", "{print $2}"],
                          stdin=p4.stdout, stdout=subprocess.PIPE)
    p6 = subprocess.Popen(["sed", "-r", "s/\",?//g"],
                          stdin=p5.stdout, stdout=subprocess.PIPE)
    output = p6.communicate(timeout=5)[0]
    sdk_version = output.decode("utf-8").strip()

    for dirname in os.listdir("."):
        if os.path.isdir(dirname):
            subprocess.run(['mkdir', '-p', api_version])
            subprocess.run(['mv', dirname, api_version])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--branch', default='master', help='OHOS branch name')
    parser.add_argument('--product-name', default='ohos-sdk-full', help='OHOS product name')
    args = parser.parse_args()
    default_save_path = os.path.join(find_top(), 'prebuilts')
    if not os.path.exists(default_save_path):
        os.makedirs(default_save_path, exist_ok=True)
    print(default_save_path)
    try:
        now_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        last_hour = (datetime.datetime.now() +
                     datetime.timedelta(hours=-12)).strftime('%Y%m%d%H%M%S')

        url = "http://ci.openharmony.cn/api/ci-backend/ci-portal/v1/dailybuilds"
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
        x = requests.post(url, data=myobj)
        data = json.loads(x.text)
    except BaseException:
        Exception("Unable to establish connection with ci.openharmony.cn")

    products_list = data['result']['dailyBuildVos']
    for product in products_list:
        product_name = product['component']
        if product_name == args.product_name:
            if os.path.exists(os.path.join(default_save_path, product_name)):
                print('{} already exists. Please backup or delete it first!'.format(
                    os.path.join(default_save_path, product_name)))
                print("Download canceled!")
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
            npm_install(save_path2)
            break


if __name__ == '__main__':
    sys.exit(main())
