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
    """
    When the process list verification fails, throw this exception
    """
    def __init__(self, name, reason):
        super().__init__()
        self.name = name
        self.reason = reason


class CfgItem:
    """
    CfgItem is the value of CFG_HASH, representing the permissions of a service read from a cfg file
    """

    def __init__(self):
        self.uid = ""
        self.gid = []
        self.need_verified = False
        self.loc = ""
        self.related_item = ProcessItem()

    def __init__(self, loc):
        self.uid = ""
        self.gid = []
        self.need_verified = False
        self.loc = loc
        self.related_item = ProcessItem()

    @classmethod
    def _is_need_verified_uid(self, uid):
        return uid == "root" or uid == "system"

    @classmethod
    def _is_need_verified_gid(self, gid):
        # To enable gid-root validate, change it to "return gid == "root""
        return False

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

    def __init__(self, process_item=None):
        """
        Use the JSON item in the process list to initialize the class
        """
        if process_item is None:
            self.name = ""
            self.uid = ""
            self.gid = []
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

    def verify(self, cfg_item):
        """
        Returns whether the corresponding CFG (cfg_item) has passed the verification
        """
        return self._verify_uid(cfg_item.uid) and self._verify_gid(cfg_item.gid)

    def _verify_uid(self, uid):
        return not ((uid == "root" or uid == "system") and (uid != self.uid))

    def _verify_gid(self, gid):
        return not ("root" in gid and "root" not in self.gid)


def print_cfg_hash():
    global CFG_HASH
    for i in CFG_HASH.items():
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


def validate_cfg_file(process_path, result_path):
    """
    Load the process list file
    For each item in the list, find out whether there is a CfgItem needs validation in CFG_HASH
    """
    global CFG_HASH
    with open(process_path) as fp:
        data = json.load(fp)
        if "high_privilege_process_list" not in data:
            print("Error: {}is not a valid whilelist, it has not a wanted field name".format(process_path))
            raise CfgValidateError("Customization Error", "cfgs check not pass")

        for i in data["high_privilege_process_list"]:
            if i["name"] not in CFG_HASH :
                # no CfgItem in CFG_HASH meet the item in process list
                continue

            temp_item = ProcessItem(i)
            if temp_item.name not in CFG_HASH:
                continue

            if temp_item.verify(CFG_HASH.get(temp_item.name)):
                # Permission check is passed, remove the corresponding service from CFG_HASH
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
    if cfg_item.need_verified:
        # Services that need to check permissions are added to CFG_HASH
        CFG_HASH[key] = cfg_item


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
        'high-privilege-process-list-path=', 'result-path='])

    sys_cfg_folder = opts[0][1]
    if not os.path.exists(sys_cfg_folder):
        print("High-privilege process check skipped: file [{}] not exist".format(sys_cfg_folder))
        return

    vendor_cfg_folder = opts[1][1]
    if not os.path.exists(vendor_cfg_folder):
        print("High-privilege process check skipped: file [{}] not exist".format(vendor_cfg_folder))
        return

    process_path = opts[2][1]
    if not os.path.exists(process_path):
        print("High-privilege process check skipped: file [{}] not exist".format(process_path))
        return

    iterate_cfg_folder(sys_cfg_folder)
    iterate_cfg_folder(vendor_cfg_folder)
    validate_cfg_file(process_path, None)

    return

if __name__ == "__main__":

    main()

