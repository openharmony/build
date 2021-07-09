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
toybox_symlinks="chmod chown chroot chrt chvt cksum clear cmp comm count cp cpio crc32 cut date devmem df diff dirname dmesg dnsdomainname dos2unix du echo egrep eject env expand factor fallocate
  false fgrep file find flock fmt free freeramdisk fsfreeze fstype fsync ftpget ftpput getconf grep groups gunzip halt head help hexedit hostname hwclock i2cdetect i2cdump i2cget
  i2cset iconv id ifconfig inotifyd insmod install ionice iorenice iotop kill killall killall5 link ln logger login logname losetup ls lsattr lsmod lspci lsusb makedevs mcookie
  md5sum microcom mix mkdir mkfifo mknod mkpasswd mkswap mktemp modinfo more mount mountpoint mv nbd-client nc netcat netstat nice nl nohup nproc nsenter od oneit partprobe
  passwd paste patch pgrep pidof ping ping6 pivot_root pkill pmap poweroff printenv printf prlimit ps pwd pwdx readahead readlink realpath renice reset rev rfkill
  rm rmdir rmmod sed seq setfattr setsid shalsum shred sleep sntp sort split stat strings su swapoff swapon switch_root sync sysctrl tac tail tar taskset tee test time timeout
  top touch true truncate tty tunctl ulimit umount uname uniq unix2dos unlink unshare uptime usleep uudecode uuencode uuidgen vconfig vmstat w watch wc which who whoami
  xargs xxd yes zcat mdev telnetd route"
for link in ${toybox_symlinks}
do
    ln -sf toybox ${link}
done
cd ${curr}
