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
import json
import os
import getopt
import sys
import contextlib

# Store the hash table of the services that need to validate
CFG_HASH = {}


class CfgValidateError(Exception):
    def __init__(self, name, reason):
        super().__init__()
        self.name = name
        self.reason = reason


class CfgItem:
    def __init__(self):
        self.need_verified = False
        self.loc = ""
        self.critical = []
        self.related_item = ProcessItem()

    def __init__(self, loc):
        self.need_verified = False
        self.loc = loc
        self.critical = []
        self.related_item = ProcessItem()

    @classmethod
    def _is_need_verified_critical(self, critical):
        return critical[0] == 1

    def set_critical(self, critical):
        if CfgItem._is_need_verified_critical(critical):
            self.critical = critical
            self.need_verified = True

    def record_related_item(self, related_item):
        self.related_item = related_item


class ProcessItem:
    def __init__(self):
        self.name = ""
        self.critical = []

    def __init__(self, process_item=None):
        if process_item is None:
            self.name = ""
            self.critical = []
            return

        self.name = process_item["name"]

        if "critical" in process_item:
            self.critical = process_item["critical"]
        else:
            self.critical = []

    def verify(self, cfg_item):
        return self.critical == cfg_item.critical


def print_cfg_hash():
    global CFG_HASH
    for i in CFG_HASH.items():
        print("Name: {}\ncritical: {}\n".format(i[0], i[1].critical), end="")
        print("given critical: {}\n".format(i[1].related_item.critical), end="")
        print("Cfg location: {}\n".format(i[1].loc))
        print("")


def validate_cfg_file(process_path):
    global CFG_HASH
    with open(process_path) as fp:
        data = json.load(fp)
        if "critical_reboot_process_list" not in data:
            print("Error: {}is not a valid whitelist, it has not a wanted field name".format(process_path))
            raise CfgValidateError("Customization Error", "cfgs check not pass")

        for i in data["critical_reboot_process_list"]:
            if i["name"] not in CFG_HASH:
                continue

            temp_item = ProcessItem(i)
            if temp_item.name not in CFG_HASH:
                continue

            if temp_item.verify(CFG_HASH.get(temp_item.name)):
                CFG_HASH.pop(temp_item.name)
            else:
                CFG_HASH.get(temp_item.name).record_related_item(temp_item)

    if CFG_HASH:
        # The remaining services in CFG_HASH do not pass the validation
        for i in CFG_HASH.items():
            print("Error: some services are not authenticated. Listed as follow:")
            print_cfg_hash()

            raise CfgValidateError("Customization Error", "cfgs check not pass")
    return


def handle_services(filename, field):
    global CFG_HASH
    cfg_item = CfgItem(filename)
    key = field["name"]
    if "critical" in field:
        cfg_item.set_critical(field["critical"])
    if cfg_item.need_verified:
        CFG_HASH[key] = cfg_item


def parse_cfg_file(filename):
    with open(filename) as fp:
        data = json.load(fp)
        if "services" not in data:
            return
        for field in data['services']:
            handle_services(filename, field)
    return


def iterate_cfg_folder(cfg_dir):
    for file in os.listdir(cfg_dir):
        if file.endswith(".cfg"):
            parse_cfg_file("{}/{}".format(cfg_dir, file))
    return


def main():
    opts, args = getopt.getopt(sys.argv[1:], '', ['sys-cfg-folder=', 'vendor-cfg-folder=', \
        'critical-reboot-process-list-path=', 'result-path='])

    sys_cfg_folder = opts[0][1]
    if not os.path.exists(sys_cfg_folder):
        print("Critical-reboot process check skipped: file [{}] not exist".format(sys_cfg_folder))
        return

    vendor_cfg_folder = opts[1][1]
    if not os.path.exists(vendor_cfg_folder):
        print("Critical-reboot process check skipped: file [{}] not exist".format(vendor_cfg_folder))
        return

    process_path = opts[2][1]
    if not os.path.exists(process_path):
        print("Critical-reboot process check skipped: file [{}] not exist".format(process_path))
        return

    iterate_cfg_folder(sys_cfg_folder)
    iterate_cfg_folder(vendor_cfg_folder)
    validate_cfg_file(process_path)


if __name__ == "__main__":

    main()
