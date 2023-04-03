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
asan_in_data=true
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
        ;;
    --no-data-asan)
        asan_in_data=false
        ;;
    --data-asan)
        asan_in_data=true
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
${no_build+echo skip} ./build.sh "$@" --gn-args is_asan=true --build-variant ${build_variant}
step1_time=$(date +%s)
mv out out.a
if [ -d out.n ]; then
    mv out.n out
fi
${no_build+echo skip} ./build.sh "$@" --gn-args is_asan=false --build-variant ${build_variant}
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
    errcode=$?
    trap '' INT HUP
    set +e
    if [ $errcode -ne 0 ]; then
        pushd "$nonasan_dir"
        test -d system.bak && rm -rf system && mv system.bak system
        test -d vendor.bak && rm -rf vendor && mv vendor.bak vendor
        test -d images.bak && rm -rf images && mv images.bak images
        test -f "${TOPDIR}"/build/ohos/images/build_image.py.bak && mv "$_" "${_%.bak}"
        test -f "${TOPDIR}"/build/ohos/images/mkimage/dac.txt.bak && mv "$_" "${_%.bak}"
    fi
    command -v handle_error_hook && handle_error_hook $errcode "$@"
    exit $errcode
}
trap 'handle_error "${args[@]}"' EXIT

# get make image command
json_data="$(ninja -w dupbuild=warn -C ../../ -t compdb | jq '.[]|select(.output|startswith("packages/phone/images/"))')"
make_system_img_cmd="$(echo "$json_data" | jq -r 'select(.output=="packages/phone/images/system.img")|.command')"
make_vendor_img_cmd="$(echo "$json_data" | jq -r 'select(.output=="packages/phone/images/vendor.img")|.command')"
make_userdata_img_cmd="$(echo "$json_data" | jq -r 'select(.output=="packages/phone/images/userdata.img")|.command')"
make_system_img() { pushd ../../; $make_system_img_cmd; popd; }
make_vendor_img() { pushd ../../; $make_vendor_img_cmd; popd; }
make_userdata_img() { pushd ../../; $make_userdata_img_cmd; popd; }

make_mixed_asan_img() {
    echo "make mixed asan system$1.img or/and vendor$1.img ..."
    cfg_group=(${@:2})

    # backup system and vendor
    mv system system.bak && cp -a system.bak system
    mv vendor vendor.bak && cp -a vendor.bak vendor

    # prepare asan related files for system image
    cp -a "$asan_dir"/system/etc/asan.options system/etc/
    cp -a "$asan_dir"/system/etc/init/asan.cfg system/etc/init/
    cp -a "$asan_dir"/system/lib/ld-musl-*-asan.so.1 system/lib/
    if grep -qw LD_PRELOAD system/etc/init/faultloggerd.cfg; then
        sed -i '/LD_PRELOAD/d' system/etc/init/asan.cfg
        sed -i 's/LD_PRELOAD\s\+/&libasan_helper.z.so:/g' system/etc/init/faultloggerd.cfg
    fi
    test -f system/etc/selinux/config && sed -i 's,enforcing,permissive,g' $_
    sed -i '/^\s*namespace.default.asan.lib.paths\s*=/d;s/^\(\s*namespace.default.\)\(lib.paths\s*=.*\)$/&\n\1asan.\2/g' system/etc/ld-musl-namespace-*.ini
    sed -i '/^\s*namespace.default.asan.lib.paths\s*=/s/\/\(system\|vendor\)\/\([^:]*:\?\)/\/\1\/asan\/\2/g' system/etc/ld-musl-namespace-*.ini
    if [ $asan_in_data = true ]; then
        for d in data/asan/*; do ln -snf /$d ${d#data/asan/}/asan; done
    else
        mkdir -p system/asan/ && cp -a "$asan_dir"/system/{lib*,bin} $_
        mkdir -p vendor/asan/ && cp -a "$asan_dir"/vendor/{lib*,bin} $_
        sed -i.bak '$asystem/asan/bin/*, 00755, 0, 2000, 0\nvendor/asan/bin/*, 00755, 0, 2000, 0' "${TOPDIR}"/build/ohos/images/mkimage/dac.txt
    fi

    # make some services run in asan version
    local -A make_images
    for f in ${cfg_group[@]}; do
        for cfg in {system,vendor}/etc/init/$f.cfg*; do
            echo -e "\033[35mModifying service cfg: $cfg\033[0m"
            sed -i 's,/bin/,/asan&,g;/"critical"/d' $cfg
            make_images[${cfg::6}]=true
        done
    done

    command -v make_mixed_asan_img_hook && make_mixed_asan_img_hook "$@"

    # make image
    if [ "${make_images[system]}" = true -o $# -eq 0 ]; then
        make_system_img
        mv images/system.img system${1}.img
    fi
    if [ "${make_images[vendor]}" = true -o $# -eq 0 ]; then
        make_vendor_img
        mv images/vendor.img vendor${1}.img
    fi

    # restore dac.txt
    if [ $asan_in_data != true ]; then
        mv "${TOPDIR}"/build/ohos/images/mkimage/dac.txt.bak "${TOPDIR}"/build/ohos/images/mkimage/dac.txt
    fi

    # restore system and vendor
    rm -rf system && mv system.bak system
    rm -rf vendor && mv vendor.bak vendor
}

add_mkshrc() {
    sed -i '/export HOME /d' "$asan_dir"/system/etc/init/asan.cfg
    sed -i '/export ASAN_OPTIONS /i"export HOME /'$1'",' "$asan_dir"/system/etc/init/asan.cfg
    cat <<EOF >${1:-.}/.mkshrc
dmesg -n1
alias ls='ls --color=auto'
alias ll='ls -al'
remount() {
    mount -o remount,rw \${1:-/}
}
EOF
}

make_data_asan_img() {
    test $asan_in_data = true || return 0
    echo "make mixed asan userdata.img ..."
    mkdir -p data/asan/{vendor,system}
    cp -a "$asan_dir"/vendor/{lib*,bin} data/asan/vendor/
    cp -a "$asan_dir"/system/{lib*,bin} data/asan/system/
    chmod +x data/asan/*/bin/*
    add_mkshrc data/
    sed -i.bak 's,shutil.rmtree(userdata_path),return,g' "${TOPDIR}"/build/ohos/images/build_image.py
    sed -i.bak '$adata/asan/*, 00755, 0, 2000, 0' "${TOPDIR}"/build/ohos/images/mkimage/dac.txt
    make_userdata_img
    mv "${TOPDIR}"/build/ohos/images/mkimage/dac.txt.bak "${TOPDIR}"/build/ohos/images/mkimage/dac.txt
    mv "${TOPDIR}"/build/ohos/images/build_image.py.bak "${TOPDIR}"/build/ohos/images/build_image.py
}

make_custom_asan_imgs() {
    # backup images
    mv images images.bak && mkdir images

    # make custom asan images
    for cfg_group in ${cfg_groups[@]}; do
        make_mixed_asan_img $(IFS=:,; echo ${cfg_group})
    done

    # restore images
    rm -rf images && mv images.bak images
}

# Collect all necessary artifacts into images directory
collect_all_artifacts() {
    # uncomment the following three lines if you need full asan images
    #rm -rf images/{system,vendor}F.img
    #cp -l "$asan_dir"/images/system.img images/systemF.img
    #cp -l "$asan_dir"/images/vendor.img images/vendorF.img
    # unstripped binaries
    rm -rf images/unstripped
    mkdir -p images/unstripped/{asan,nonasan}
    cp -al "$asan_dir"/../../{exe,lib}.unstripped images/unstripped/asan/
    cp "$asan_dir"/../../libclang_rt.asan.so images/unstripped/asan/lib.unstripped/
    cp -al ../../{exe,lib}.unstripped images/unstripped/nonasan/
    cp system/lib*/libc++.so images/unstripped/nonasan/lib.unstripped/
    # asan log resolve scripts
    cp "${TOPDIR}"/build/common/asan/{symbolize,resolve_asan_log}.sh images/
    chmod +x images/*.sh
    # mixed asan images
    mv system*.img vendor*.img images/
}

shopt -s nullglob

make_data_asan_img
make_mixed_asan_img
make_custom_asan_imgs
collect_all_artifacts

step3_time=$(date +%s)

echo -e "\033[32m==== Done! ====\033[0m"
echo "asan build cost $((${step1_time}-${start_time}))s, nonasan build cost $((${step2_time}-${step1_time}))s, image build cost $((${step3_time}-${step2_time}))s"
popd
