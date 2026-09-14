#!/bin/bash
# Copyright (c) Huawei Technologies Co., Ltd. 2024-2024. All rights reserved.
# Description: The script is used to configure, enable, and disable the distributed compilation feature.
set -e

lcache_exec=${hmos_build_dir}/framework/tools/lcache/link_cache.py
lcache_logfile=${source_root_dir}/out/${abi_type}/${device_type}/link_cache.log

calculate_lcache_ratio() {

    if [ ! -f "$lcache_logfile" ]; then
        echo "Can not found file $lcache_logfile ."
        return 0
    fi

    cache_hit_count=$(grep -c "LINK_CACHE_HIT" "$lcache_logfile" 2>/dev/null || echo 0)
    cache_miss_count=$(grep -c "LINK_CACHE_MISS" "$lcache_logfile" 2>/dev/null || echo 0)

    total=$((cache_hit_count + cache_miss_count))

    if [ $total -eq 0 ]; then
        echo "--------------------------------------------"
        echo "link cache summary:"
        echo "cache hit: 0"
        echo "cache miss: 0"
        echo "hit rate: 0.0%"
        echo "--------------------------------------------"
        return 0
    fi

    percentage=$(awk "BEGIN {printf \"%.2f\", ($cache_hit_count/$total)*100}")

    echo "--------------------------------------------"
    echo "link cache summary:"
    echo "cache hit: $cache_hit_count"
    echo "cache miss: $cache_miss_count"
    echo "hit rate: $percentage%"
    echo "--------------------------------------------"
}