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
build_variant=root
while test $# -gt 0; do
    case "$1" in
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
start_time=$(date +%s)
cd "${TOPDIR}"
if [ -d out.a ]; then
    if [ -d out ]; then
        mv out out.n
    fi
    mv out.a out
fi
sed -i.bak '2s/.*/9437184/' build/ohos/images/mkimage/ramdisk_image_conf.txt
sed -i.bak '2s/.*/67108864/' build/ohos/images/mkimage/updater_ramdisk_image_conf.txt
sed -i.bak '2s/.*/2516582400/' build/ohos/images/mkimage/system_image_conf.txt
${no_build+echo skip} ./build_m40musl.sh "$@" --gn-args is_asan=true --gn-args asan_detector=true --build-variant ${build_variant} --nopkg
step1_time=$(date +%s)
mv out out.a
if [ -d out.n ]; then
    mv out.n out
fi
mv build/ohos/images/mkimage/ramdisk_image_conf.txt.bak build/ohos/images/mkimage/ramdisk_image_conf.txt
mv build/ohos/images/mkimage/updater_ramdisk_image_conf.txt.bak build/ohos/images/mkimage/updater_ramdisk_image_conf.txt
${no_build+echo skip} ./build_m40musl.sh "$@" --gn-args is_asan=false --gn-args asan_detector=true --build-variant ${build_variant} --nopkg
step2_time=$(date +%s)

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
	test -f build/ohos/images/mkimage/ramdisk_image_conf.txt.bak && mv -f build/ohos/images/mkimage/ramdisk_image_conf.txt.bak build/ohos/images/mkimage/ramdisk_image_conf.txt
        test -f build/ohos/images/mkimage/updater_ramdisk_image_conf.txt.bak && mv -f build/ohos/images/mkimage/updater_ramdisk_image_conf.txt.bak build/ohos/images/mkimage/updater_ramdisk_image_conf.txt
        test -f build/ohos/images/mkimage/system_image_conf.txt.bak && mv -f build/ohos/images/mkimage/system_image_conf.txt.bak build/ohos/images/mkimage/system_image_conf.txt
        test -f build/ohos/images/mkimage/dac.txt.bak && mv -f build/ohos/images/mkimage/dac.txt.bak build/ohos/images/mkimage/dac.txt
    fi
}
trap handle_error EXIT

# get make image command
json_data="$(ninja -w dupbuild=warn -C ../../ -t compdb | jq '.[]|select(.output|startswith("packages/phone/images/"))')"
make_system_img_cmd="$(echo "$json_data" | jq -r 'select(.output=="packages/phone/images/system.img")|.command')"
make_vendor_img_cmd="$(echo "$json_data" | jq -r 'select(.output=="packages/phone/images/vendor.img")|.command')"
make_userdata_img_cmd="$(echo "$json_data" | jq -r 'select(.output=="packages/phone/images/userdata.img")|.command')"
make_system_img() { pushd ../../; echo $make_system_img_cmd; $make_system_img_cmd; popd; }
make_vendor_img() { pushd ../../; echo $make_vendor_img_cmd; $make_vendor_img_cmd; popd; }
make_userdata_img() { pushd ../../; echo $make_userdata_img_cmd; $make_userdata_img_cmd; popd; }

add_mkshrc() {
    cat <<EOF >${1:-.}/.mkshrc
dmesg -n1
alias ls='ls --color=auto'
alias ll='ls -al'
remount() {
    mount -o remount,rw \${1:-/}
}
EOF
}

make_mixed_asan_img() {
    echo "make mixed asan system.img and vendor.img ..."
    mkdir -p system/asan/ && cp -a "$asan_dir"/system/{lib*, bin} $_
    mkdir -p vendor/asan/ && cp -a "$asan_dir"/vendor/{lib*, bin} $_

    # prepare asan related files for system image
    cp -a "$asan_dir"/system/etc/asan.options system/etc/
    cp -a "$asan_dir"/system/etc/init/asan.cfg system/etc/init/
    cp -a "$asan_dir"/system/lib/ld-musl-*-asan.so.1 system/lib/
    cp -a "$asan_dir"/system/etc/ld-musl-*-asan.path system/etc/
    test -f system/etc/selinux/config && sed -i 's,enforcing,permissive,g' system/etc/selinux/config
    sed -i '/^\s*namespace.default.asan.lib.paths\s*=/d;s/^\(\s*namespace.default.\)\(lib.paths\s*=.*\)$/&\n\1asan.\2/g' system/etc/ld-musl-namespace-*.ini
    sed -i '/^\s*namespace.default.asan.lib.paths\s*=/s/\/\(system\|vendor\)\/\([^:]*:\?\)/\/\1\/asan\/\2/g' system/etc/ld-musl-namespace-*.ini

    # remove ubsan.cfg
    rm -rf system/etc/init/ubsan.cfg

    add_mkshrc system/
    sed -i.bak '$asystem/asan/bin/*, 00755, 0, 2000, 0\nvendor/asan/bin/*, 00755, 0, 2000, 0' "${TOPDIR}"/build/ohos/images/mkimage/dac.txt
    if [ -f system/lib64/libclang_rt.asan.so ]; then
	if [ "$(md5sum system/lib64/libclang_rt.asan.so|awk '{print $1}')" = "e4ade6eb02f6bbbd7f7faebcda3f0a26" ]; then
            patch_file_nop system/lib64/libclang_rt.asan.so 356872 17 # patch function 'GetThreadStackAndTls'
	fi
    fi
    if [ -f system/asan/lib64/libclang_rt.asan.so ]; then
        if [ "$(md5sum system/asan/lib64/libclang_rt.asan.so|awk '{print $1}')" = "e4ade6eb02f6bbbd7f7faebcda3f0a26" ]; then
            patch_file_nop system/asan/lib64/libclang_rt.asan.so 356872 17 # patch function 'GetThreadStackAndTls'
        fi
    fi
    # make image
    make_system_img
    make_vendor_img

    mv "${TOPDIR}"/build/ohos/images/mkimage/dac.txt.bak "${TOPDIR}"/build/ohos/images/mkimage/dac.txt
}

make_mixed_asan_img
mv "${TOPDIR}"/build/ohos/images/mkimage/system_image_conf.txt.bak "${TOPDIR}"/build/ohos/images/mkimage/system_image_conf.txt

# Collect all necessary artifacts into images directory
if [ -f "$asan_dir"/images/system.img ]; then
    # unstripped binaries
    rm -rf images/unstripped
    mkdir -p images/unstripped/{asan,nonasan}
    mv "$asan_dir"/../../{exe,lib}.unstripped images/unstripped/asan/
    cp "$asan_dir"/../../libclang_rt.asan.so images/unstripped/asan/lib.unstripped/
    mv ../../{exe,lib}.unstripped images/unstripped/nonasan/
    # asan log resolve scripts
    cp "${TOPDIR}"/build/common/asan/{symbolize,resolve_asan_log}.sh images/
    chmod +x images/*.sh
fi
step3_time=$(date +%s)
popd

echo -e "\033[32m==== Done! ====\033[0m"
echo "asan build cost $((${step1_time}-${start_time}))s, nonasan build cost $((${step2_time}-${step1_time}))s, image build cost $((${step3_time}-${step2_time}))s."
