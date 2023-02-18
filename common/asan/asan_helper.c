/*
 * Copyright (c) 2022 Huawei Device Co., Ltd.
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <stdio.h>
#include <dlfcn.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <link.h>

#if defined (__arm__)
#define ASAN_LINKER "/lib/ld-musl-arm-asan.so.1"
#define LIB "/lib/"
#elif defined (__aarch64__)
#define ASAN_LINKER "/lib/ld-musl-aarch64-asan.so.1"
#define LIB "/lib64/"
#else
#error "unsupported arch"
#endif

static int g_isAsan = false;

static int dl_iterate_phdr_callback(struct dl_phdr_info *info, size_t size, void *args)
{
    return info && info->dlpi_name && (strcmp(info->dlpi_name, ASAN_LINKER) == 0);
}

static void __attribute__((constructor)) init(void)
{
    g_isAsan = dl_iterate_phdr(dl_iterate_phdr_callback, NULL);
}

typedef void* (*dlopen_fn_t)(const char *file, int mode);
static void *trap_dlopen(const char *file, int mode);
static dlopen_fn_t real_dlopen = trap_dlopen;
static void *trap_dlopen(const char *file, int mode)
{
    dlopen_fn_t fn = dlsym(RTLD_NEXT, "dlopen");
    if (fn) {
        real_dlopen = fn;
        return fn(file, mode);
    }
    abort();
}

void *dlopen(const char *file, int mode)
{
    while (g_isAsan && file != NULL) {
        char *p = strstr(file, LIB);
        if (p == NULL) {
            break;
        }

        char *f = NULL;
        asprintf(&f, "%.*s/asan%s", (int)(p - file), file, p);
        if (f == NULL) {
            break;
        }

        void *ret = real_dlopen(f, mode);
        free(f);
        f = NULL;
        if (ret != NULL) {
            return ret;
        }
        break;
    }
    return real_dlopen(file, mode);
}
