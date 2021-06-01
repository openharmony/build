#!/bin/bash
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

set -e
if [ $# -ne 1 ];then
    echo "Invalid argument."
    exit 1
fi

curr=$(pwd -P)
basepath=$1
if [ ! -d "${basepath}" ]; then
    echo "Invalid path."
    exit 1
fi

cd ${basepath}
toybox_symlinks="base64 basename blockdev cal cat chgrp chmod chown chroot clear comm cp cpio cut date dd devmem df diff dirname dmesg  du echo env expr false file find free fsync getconf groups gunzip gzip head hostname id ifconfig insmod install ionice kill killall ln logname losetup ls lsmod lsusb md5sum mkdir mknod mount mountpoint mv nl nohup nproc nsenter patch pgrep pidof pkill pmap printenv printf ps pwd readlink realpath restorecon rm rmdir rmmod runcon sed sendevent seq setsid sha1sum sha224sum sha256sum sha384sum sha512sum sleep sort split stat strings swapoff swapon sync sysctl tac tail taskset tee time timeout top touch tr true truncate tty ulimit umount uname uniq unlink uptime usleep vmstat watch wc which xargs yes zcat"

for link in ${toybox_symlinks}
do
    ln -sf toybox ${link}
done
cd ${curr}

