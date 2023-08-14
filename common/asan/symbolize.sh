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

set -e

objdir=${SYSROOT:-.}
symbolizer=${SYMBOLIZER:-addr2line}
help=no
max_count=10000
asan_logs=()

while test -n "${1}"; do
    case "${1}" in
    -o | --objdir)
        objdir="${2}"
        shift
        ;;
    -p | --symbolizer)
        symbolizer="${2}"
        shift
        ;;
    --max-count)
        max_count="${2}"
        shift
        ;;
    -h | --help)
        help=yes
        break
        ;;
    -*)
        echo "$0: Warning: unsupported parameter $1" >&2
        ;;
    *)
        asan_logs+=("$1")
        ;;
    esac
    shift
done

print_help() {
    cat <<-END
Usage: symbolize.sh [OPTION]...
Translate call stack to symbolized forms.

    Options:

    -o,  --objdir  <objects_dir>    dir that contains the call stack binaries.
    -p,  --symbolizer <symbolizer>  symbolizer for translating call stacks, default is addr2line.
    --max-count <max-count>         max calls of symbolizer for translatings, default is 10000.
    -h,  --help                     print help info
END
}

test $help = yes && print_help && exit 0

find_unstripped() {
    file="$(basename $1)"
    shift
    if [ "${file:0:8}" = "ld-musl-" ]; then
        file="libc.so"
    fi
    find "$@" -type f -name "$file" -exec sh -c 'test ${1##*/} = libclang_rt.asan.so -o ${1##*/} = libc++.so || file -bL $1 | grep -q "not stripped"' sh {} \; -print
}

find_file() {
    find_unstripped $1 $objdir
}

declare -A sym_cached
declare -A files_found
declare -A buildid_cache

getsym2() {
    if [ -z "${files_found[$1]}" ]; then
        files_found[$1]=" $(find_file $1)"
    fi
    for file in ${files_found[$1]}; do
        if [ -z "${buildid_cache[$file]}" ]; then
            buildid_cache[$file]=" $(file -bL "${file}"|grep -o BuildID[^\ ,]*)"
        fi
        sym_cached[$1+$2]+=" $($symbolizer -Cfpie "${file}" $2 2>/dev/null)${buildid_cache[$file]}"
    done
    sym_cached[$1+$2]+=" "
}

getsym() {
    if [ $# -gt 0 ]; then
        if [ -z "${sym_cached[$1]}" ]; then
            getsym2 ${1%+*} ${1##*+}
        fi
        echo "${sym_cached[$1]%% }"
    else
        return 1
    fi
}

sym_sed_pattens=(
    's/([^[:space:]([{"]{4,})\s*[[:space:]:+]\s*(0x[0-9a-f]+)\b/>>>:\1+\2:<<</I;s/.*>>>:([^<>]+):<<<.*/\1/p'
    's/\b(0x)?0*([0-9a-f]{4,})\s+([^[:space:]([{"]{4,})\b/>>>:\3+0x\2:<<</I;s/.*>>>:([^<>]+):<<<.*/\1/p'
)

symbolize() {
    while IFS= read -r line || [ -n "$line" ]; do
        echo -n "$line"
        for patten in "${sym_sed_pattens[@]}"; do
            if getsym $(echo "$line" | sed -nE "${patten}"); then
                continue 2
            fi
        done
        echo ""
    done
}

symbolize_file() {
    f="$1"
    echo -n "Resolving $f ... "
    symbolize < "$f" > "${f%${f##*/}}resolved_${f##*/}"
    echo "Done!"
}

symbolize_dir() {
    dir="$1"
    for f in $(find "$dir" -type f -name asan.log.*); do
        symbolize_file "$f"
    done
}

if [ ${#asan_logs[@]} -gt 0 ]; then
    for f in "${asan_logs[@]}"; do
        if [ -d "$f" ]; then
            symbolize_dir "$f"
        else
            symbolize_file "$f"
        fi
    done
else
    symbolize
fi
