#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
# Description: lcache help main entry

HELP_TEXT = f"""\
lcache - Link cache wrapper(version 1.0.0)

USAGE:
  python3 link_cache.py [options] [linker arguments...]

OPTIONAL:
  -h, --help                         Show this help and exit
  -v, --version                      Show lcache version and exit
  --metadata-load-key=<hash>         Show metadata by result hash value and exit.
  --work-dir=<path>                  Base directory for path normalization (recommended)
  --real-linker=<path>               Path to the real linker executable (e.g. g++)
  --lcache-dir=<path>                Cache root directory. (default: ~/.link-cache)
  --lcache-mode=<str>                Cache execution mode, SEARCH | UPDATE | ALL (default: ALL)
  --lcache-max-size=<number>         Max cache size in GB. (default: 20)
  --lcache-max-rsp-depth=<number>    Max rsp file depth. (default: 10)
  --lcache-logfile=<file>            Log file path. (default:  ~/.link-cache/link_cache.log)
  --lcache-config-file=<file>        Config file path. (default:  ~/.link-cache/link_cache.cfg)
  --lcache-log-level=<str>           Log level, QUIET | INFO | DEBUG (default: INFO)
  --lcache-allow-env=<str>           Environment variables that need to be included in hash calculation.
  --lcache-compiler-check=<str>      Hash mode of the compiler, which includes content, mtime and none. (default: mtime)


ENVIRONMENT:
  LCACHE_DIR                Cache root directory. (default: ~/.link-cache)
  LCACHE_MODE               Cache execution mode, SEARCH | UPDATE | ALL (default: ALL)
  LCACHE_LOGFILE            Log file path. (default:  ~/.link-cache/link_cache.log)
  LCACHE_MAX_SIZE           Max cache size in GB. (default: 20)
  LCACHE_LOG_LEVEL          QUIET | INFO | DEBUG (default: INFO)
  LCACHE_ALLOW_ENV          Environment variables that need to be included in hash calculation.
  LCACHE_CONFIG_FILE        Config file path. (default:  ~/.link-cache/link_cache.cfg)
  LCACHE_MAX_RSP_DEPTH      Max rsp file depth. (default: 10)
  LCACHE_COMPILER_CHECK     Hash mode of the compiler, which includes content, mtime and none. (default: mtime)

EXAMPLES:
  python3 link_cache.py \\
    --work-dir=$(pwd) \\
    g++ foo.o bar.o @link.rsp -Llib -lmylib -o demo
"""


def print_help():
    print(HELP_TEXT.strip())