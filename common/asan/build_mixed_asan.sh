#!/bin/bash
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

TOPDIR=$(realpath "$(dirname ${BASH_SOURCE[0]})/../../../")

PATH="${TOPDIR}/prebuilts/build-tools/linux-x86/bin/:${TOPDIR}/prebuilts/python/linux-x86/3.9.2/bin/:${PATH}"

command -v jq &>/dev/null || { echo >&2 "jq command not found, please install by: apt install -y jq"; exit 1; }
command -v ninja &>/dev/null || { echo >&2 "ninja command not found, please install by: apt install -y ninja-build"; exit 1; }

args=()
cfg_groups=()
build_variant=root
while test $# -gt 0; do
    case "$1" in
    -g[0-9]:*)
        cfg_groups+=(${1:2})
        ;;
    --gn-args)
        case "$2" in
        is_asan=*);;
        *)args+=("$1" "$2");;
        esac
        shift
        ;;
    --build-variant)
        build_variant=$2
        shift
        ;;
    --no-build)
        no_build=true
        shift
        ;;
    *)
        args+=("$1")
        ;;
    esac
    shift
done

set -e -- "${args[@]}"

# build both asan and nonasan images
cd "${TOPDIR}"
if [ -d out.a ]; then
    if [ -d out ]; then
        mv out out.n
    fi
    mv out.a out
fi
${no_build+echo skip} ./build.sh "$@" --gn-args is_asan=true --build-variant ${build_variant}
mv out out.a
if [ -d out.n ]; then
    mv out.n out
fi
${no_build+echo skip} ./build.sh "$@" --gn-args is_asan=false --build-variant ${build_variant}


asan_dir=$(ls -d out.a/*/packages/phone/)
nonasan_dir=$(ls -d out/*/packages/phone/)

asan_dir=$(realpath "$asan_dir")
nonasan_dir=$(realpath "$nonasan_dir")

echo "asan dir is $asan_dir"
echo "non-asan dir is $nonasan_dir"

# check directories
for d in {"$asan_dir","$nonasan_dir"}/{system,vendor,data} ; do
    if [ ! -d "$d" ]; then
        echo "directory '$d' does not exist."
        exit 1
    fi
done

# following works should all be done in nonasan dir
pushd "$nonasan_dir"

handle_error() {
    if [ "$?" -ne 0 ]; then
        set +e
        pushd "$nonasan_dir"
        test -d system.bak && rm -rf system && mv system.bak system
        test -d vendor.bak && rm -rf vendor && mv vendor.bak vendor
        test -d images.bak && rm -rf images && mv images.bak images
    fi
}
trap handle_error EXIT

# get make image command
json_data="$(ninja -w dupbuild=warn -C ../../ -t compdb | jq '.[]|select(.output|startswith("packages/phone/images/"))')"
make_system_img_cmd="$(echo "$json_data" | jq -r 'select(.output=="packages/phone/images/system.img")|.command')"
make_vendor_img_cmd="$(echo "$json_data" | jq -r 'select(.output=="packages/phone/images/vendor.img")|.command')"
make_userdata_img_cmd="$(echo "$json_data" | jq -r 'select(.output=="packages/phone/images/userdata.img")|.command')"
make_system_img() { pushd ../../; $make_system_img_cmd; popd; }
make_vendor_img() { pushd ../../; $make_vendor_img_cmd; popd; }
make_userdata_img() { pushd ../../; $make_userdata_img_cmd; popd; }

make_mixed_asan_img() {
    cfg_group=(${@:2})

    # backup system and vendor
    mv system system.bak && cp -a system.bak system
    mv vendor vendor.bak && cp -a vendor.bak vendor

    # prepare asan related files for system image
    cp -a "$asan_dir"/system/etc/asan.options system/etc/
    cp -a "$asan_dir"/system/etc/init/asan.cfg system/etc/init/
    cp -a "$asan_dir"/system/lib/ld-musl-*-asan.so.1 system/lib/
    cp -a "$asan_dir"/system/etc/ld-musl-*-asan.path system/etc/
    sed -i 's/LD_PRELOAD\s\+/&libasan_helper.z.so:/g' system/etc/init/faultloggerd.cfg
    sed -i 's,enforcing,permissive,g' system/etc/selinux/config
    sed -i 's,/system/\([^:]*\),/data/\1:&,g' system/etc/ld-musl-*-asan.path
    sed -i '/^\s*namespace.default.asan.lib.paths\s*=/d;s/^\(\s*namespace.default.\)\(lib.paths\s*=.*\)$/&\n\1asan.\2/g' system/etc/ld-musl-namespace-*.ini
    sed -i '/^\s*namespace.default.asan.lib.paths\s*=/s/\/\(system\|vendor\)\/\([^:]*:\?\)/\/data\/\2/g' system/etc/ld-musl-namespace-*.ini

    # make some services run in asan version
    local make_system=false
    local make_vendor=false
    for f in ${cfg_group[@]/%/.cfg}; do
        if [ -f system/etc/init/$f ]; then
            echo "$f is found in /system/etc/init/"
            sed -i 's,/system/bin/,/data/bin/,g' system/etc/init/$f
            sed -i '/"critical"/d' system/etc/init/$f
            for xml in $(sed -n '/\/data\/bin\/sa_main/s/.*"\([^" ]*.xml\)".*/\1/p' system/etc/init/$f); do
                sed -i 's,/system/\(lib[^/]*\)/,/data/\1/,g' ./$xml
            done
            make_system=true
        elif [ -f vendor/etc/init/$f ]; then
            echo "$f is found in /vendor/etc/init/"
            sed -i 's,/vendor/bin/,/data/bin/,g' vendor/etc/init/$f
            sed -i 's,/system/bin/,/data/bin/,g' vendor/etc/init/$f
            sed -i '/"critical"/d' vendor/etc/init/$f
            for xml in $(sed -n '/\/data\/bin\/sa_main/s/.*"\([^" ]*.xml\)".*/\1/p' vendor/etc/init/$f); do
                sed -i 's,/vendor/\(lib[^/]*\)/,/data/\1/,g' ./$xml
                sed -i 's,/system/\(lib[^/]*\)/,/data/\1/,g' ./$xml
            done
            make_vendor=true
        else
            echo -e "\033[33m==== WARNING: $f is not found in /system/etc/init/ nor in /vendor/etc/init/ ====\033[0m"
        fi
    done

    # make image
    if [ "$make_system" = true -o $# -eq 0 ]; then
        make_system_img
        mv images/system.img system${1}.img
    fi
    if [ "$make_vendor" = true ]; then
        make_vendor_img
        mv images/vendor.img vendor${1}.img
    fi

    # restore system and vendor
    rm -rf system && mv system.bak system
    rm -rf vendor && mv vendor.bak vendor
}

add_mkshrc() {
    sed -i '/export HOME /d' "$asan_dir"/system/etc/init/asan.cfg
    sed -i '/export ASAN_OPTIONS /i"export HOME /data",' "$asan_dir"/system/etc/init/asan.cfg
    cat <<EOF >${1:-.}/.mkshrc
dmesg -n1
alias ls='ls --color=auto'
alias ll='ls -al'
remount() {
    mount -o remount,rw \${1:-/}
}
EOF
}

# $1   file that need to be patched
# $2   file offset
# $3   instruction count, 4 bytes per instruction on arm architecture
patch_file_nop() {
    while true; do echo -e -n "\x1F\x20\x03\xD5"; done | dd conv=notrunc bs=1 of=$1 seek=$2 count=$((4*$3))
}

make_data_asan_img() {
    cp -a "$asan_dir"/vendor/{lib*,bin} data/
    cp -a "$asan_dir"/system/{lib*,bin} data/
    add_mkshrc data/
    sed -i.bak 's,shutil.rmtree(userdata_path),return,g' "${TOPDIR}"/build/ohos/images/build_image.py
    sed -i.bak '$adata/bin/*, 00755, 0, 2000, 0' "${TOPDIR}"/build/ohos/images/mkimage/dac.txt
    if [ -f data/lib64/libclang_rt.asan.so ]; then
        if [ "$(md5sum data/lib64/libclang_rt.asan.so|awk '{print $1}')" = "e4ade6eb02f6bbbd7f7faebcda3f0a26" ]; then
            patch_file_nop data/lib64/libclang_rt.asan.so 356872 17 # patch function 'GetThreadStackAndTls'
        fi
    fi
    make_userdata_img
    mv "${TOPDIR}"/build/ohos/images/mkimage/dac.txt.bak "${TOPDIR}"/build/ohos/images/mkimage/dac.txt
    mv "${TOPDIR}"/build/ohos/images/build_image.py.bak "${TOPDIR}"/build/ohos/images/build_image.py
}

make_custom_asan_imgs() {
    # backup images
    mv images images.bak && mkdir images

    # make custom asan images
    for cfg_group in ${cfg_groups[@]}; do
        local OLDIFS="$IFS"
        IFS+=":,"
        make_mixed_asan_img ${cfg_group}
        IFS="$OLDIFS"
    done

    # restore images
    rm -rf images && mv images.bak images
}

make_data_asan_img
make_mixed_asan_img
make_custom_asan_imgs

shopt -s nullglob && mv system*.img vendor*.img images/

echo -e "\033[32m==== Done! ====\033[0m"
popd
