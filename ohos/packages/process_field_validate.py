#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023 Huawei Device Co., Ltd.
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
PRIVILEGE_HASH = {}
CRITICAL_HASH = {}


class CfgValidateError(Exception):
    """
    When the process list verification fails, throw this exception
    """
    def __init__(self, name, reason):
        super().__init__()
        self.name = name
        self.reason = reason


class CfgItem:
    """
    CfgItem is the value of HASH, representing the interesetd field of a service read from a cfg file
    """

    def __init__(self):
        self.uid = ""
        self.gid = []
        self.need_verified = False
        self.enabled_critical = False
        self.loc = ""
        self.critical = []
        self.related_item = ProcessItem()

    def __init__(self, loc):
        self.uid = ""
        self.gid = []
        self.need_verified = False
        self.enabled_critical = False
        self.loc = loc
        self.critical = []
        self.related_item = ProcessItem()

    @classmethod
    def _is_need_verified_uid(self, uid):
        return uid == "root" or uid == "system"

    @classmethod
    def _is_need_verified_gid(self, gid):
        # To enable gid-root validate, change it to "return gid == "root""
        return False

    @classmethod
    def _is_need_verified_critical(self, critical):
        return critical[0] == 1

    def set_uid(self, uid):
        """
        Set uid and check it at the same time.
        The uid needs to be validated only if _is_need_verified_uid return True
        """
        if CfgItem._is_need_verified_uid(uid):
            self.uid = uid
            self.need_verified = True

    def append_gid(self, gid):
        """
        Append gid and check it at the same time.
        The gid needs to be validated only if _is_need_verified_gid return True
        """
        if CfgItem._is_need_verified_gid(gid) and gid not in self.gid:
            self.gid.append(gid)
            self.need_verified = True

    def set_critical(self, critical):
        if CfgItem._is_need_verified_critical(critical):
            self.critical = critical
            self.enabled_critical = True

    def handle_socket(self, socket):
        """
        Validate possible field "socket" in the field "services"
        """
        for i in socket:
            if ("uid" in i) and CfgItem._is_need_verified_uid(i["uid"]):
                self.need_verified = True
                if self.uid != "" and self.uid != i["uid"]:
                    print("Error: uid and uid in socket is not same!")
                    print("Cfg location: {}".format(self.loc))
                    raise CfgValidateError("Customization Error", "cfgs check not pass")
                self.uid = i["uid"]
            if "gid" in i :
                if isinstance(i["gid"], str) and i["gid"] not in self.gid:
                    self.append_gid(i["gid"])
                    continue
                for item in i["gid"]:
                    self.append_gid(item)


    def record_related_item(self, related_item):
        """
        When its permissions does not match those in process list,
        records the permissions given in process list
        """
        self.related_item = related_item


class ProcessItem:
    """
    Processitem is the data structure of an item read from the process list
    """
    def __init__(self):
        self.name = ""
        self.uid = ""
        self.gid = []
        self.critical = []

    def __init__(self, process_item=None):
        """
        Use the JSON item in the process list to initialize the class
        """
        if process_item is None:
            self.name = ""
            self.uid = ""
            self.gid = []
            self.critical = []
            return

        self.name = process_item["name"]

        if "uid" in process_item:
            self.uid = process_item["uid"]
        else:
            self.uid = ""
        if "gid" in process_item:
            if isinstance(process_item["gid"], str):
                self.gid = []
                self.gid.append(process_item["gid"])
            else:
                self.gid = process_item["gid"]
        else:
            self.gid = []
        if "critical" in process_item:
            self.critical = process_item["critical"]
        else:
            self.critical = []

    def verify(self, cfg_item):
        """
        Returns whether the corresponding CFG (cfg_item) has passed the verification
        """
        if cfg_item.need_verified:
            return self._verify_uid(cfg_item.uid) and self._verify_gid(cfg_item.gid)
        if cfg_item.enabled_critical:
            return self.critical == cfg_item.critical

    def _verify_uid(self, uid):
        return not ((uid == "root" or uid == "system") and (uid != self.uid))

    def _verify_gid(self, gid):
        return not ("root" in gid and "root" not in self.gid)


def print_privilege_hash():
    global PRIVILEGE_HASH
    for i in PRIVILEGE_HASH.items():
        print("Name: {}\nuid: {}\ngiven uid: {}\ngid: ".format(i[0], i[1].uid, i[1].related_item.uid), end="")

        for gid in i[1].gid:
            print(gid, end=" ")
        print("")

        print("given gid: ", end=" ")
        for gid in i[1].related_item.gid:
            print(gid, end=" ")
        print("")
        print("Cfg location: {}".format(i[1].loc))
        print("")


def print_critical_hash():
    global CRITICAL_HASH
    for i in CRITICAL_HASH.items():
        print("Cfg location: {}\n".format(i[1].loc), end="")
        print("Name: {}\ncritical: {}\n".format(i[0], i[1].critical), end="")
        print("Whitelist-allowed critical: {}\n".format(i[1].related_item.critical))
        print("")


def container_validate(process_path, list_name, item_container):
    with open(process_path) as fp:
        data = json.load(fp)
        if list_name not in data:
            print("Error: {}is not a valid whilelist, it has not a wanted field name".format(process_path))
            raise CfgValidateError("Customization Error", "cfgs check not pass")

        for i in data[list_name]:
            if i["name"] not in item_container :
                # no CfgItem in HASH meet the item in process list
                continue

            temp_item = ProcessItem(i)
            if temp_item.name not in item_container:
                continue

            if temp_item.verify(item_container.get(temp_item.name)):
                # Process field check passed, remove the corresponding service from HASH
                item_container.pop(temp_item.name)
            else:
                item_container.get(temp_item.name).record_related_item(temp_item)


def validate_cfg_file(process_path, critical_process_path, result_path):
    """
    Load the process list file
    For each item in the list, find out whether there is a CfgItem needs validation in HASH
    """
    global PRIVILEGE_HASH
    global CRITICAL_HASH
    container_validate(process_path, "high_privilege_process_list", PRIVILEGE_HASH)
    container_validate(critical_process_path, "critical_reboot_process_list", CRITICAL_HASH)

    if PRIVILEGE_HASH:
        # The remaining services in HASH do not pass the high-privilege validation
        print("Error: some services are not authenticated. Listed as follow:")
        print_privilege_hash()

        raise CfgValidateError("Customization Error", "cfgs check not pass")

    if CRITICAL_HASH:
        # The remaining services in HASH do not pass the critical validation
        print("Error: some services do not match with critical whitelist({}).".format(process_path), end="")
        print(" Directly enable critical or modify enabled critical services are prohibited!", end="")
        print(" Misconfigured services listed as follow:")
        print_critical_hash()

        raise CfgValidateError("Customization Error", "cfgs check not pass")
    return


def handle_services(filename, field):
    global PRIVILEGE_HASH
    global CRITICAL_HASH
    cfg_item = CfgItem(filename)
    key = field['name']
    if "uid" in field:
        cfg_item.set_uid(field["uid"])
    if "gid" in field:
        if isinstance(field["gid"], str):
            cfg_item.append_gid(field["gid"])
        else:
            for item in field["gid"]:
                cfg_item.append_gid(item)
    if "socket" in field:
        cfg_item.handle_socket(field["socket"])
    if "critical" in field:
        cfg_item.set_critical(field["critical"])
    if cfg_item.need_verified:
        # Services that need to check permissions are added to HASH
        PRIVILEGE_HASH[key] = cfg_item
    if cfg_item.enabled_critical:
        # Services that need to check critical are added to HASH
        CRITICAL_HASH[key] = cfg_item


def parse_cfg_file(filename):
    """
    Load the cfg file in JSON format
    """
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
        'high-privilege-process-list-path=', 'critical-reboot-process-list-path=', 'result-path='])

    sys_cfg_folder = opts[0][1]
    if not os.path.exists(sys_cfg_folder):
        print("High-privilege process check skipped: file [{}] not exist".format(sys_cfg_folder))
        return

    vendor_cfg_folder = opts[1][1]
    if not os.path.exists(vendor_cfg_folder):
        print("High-privilege process check skipped: file [{}] not exist".format(vendor_cfg_folder))
        return

    privilege_process_path = opts[2][1]
    if not os.path.exists(privilege_process_path):
        print("High-privilege process check skipped: file [{}] not exist".format(process_path))
        return

    critical_process_path = opts[3][1]
    if not os.path.exists(critical_process_path):
        print("High-privilege process check skipped: file [{}] not exist".format(process_path))
        return

    iterate_cfg_folder(sys_cfg_folder)
    iterate_cfg_folder(vendor_cfg_folder)
    validate_cfg_file(privilege_process_path, critical_process_path, None)

    return

if __name__ == "__main__":

    main()

