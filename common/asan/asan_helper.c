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

static void* (*real_dlopen)(const char *file, int mode);
static bool g_isAsan = false;
static bool g_enableRandomDelay = false;

static void __attribute__((constructor)) init(void)
{
    real_dlopen = dlsym(RTLD_NEXT, "dlopen");
    FILE *mapsFile = fopen("/proc/self/maps", "r");
    if (mapsFile != NULL) {
        char *line = NULL;
        size_t len = 0;
        while (-1 != getline(&line, &len, mapsFile)) {
            char *p = strstr(line, "/ld-musl-");
            if (p && strstr(p, "-asan.so.1")) {
                g_isAsan = true;
                break;
            }
        }
        free(line);
        fclose(mapsFile);
    }
    char *env = getenv("LD_RANDOM_DELAY");
    if ((env != NULL) && (env[0] == '1')) {
        srand((unsigned)getpid());
        g_enableRandomDelay = true;
    }
}

void *dlopen(const char *file, int mode)
{
    if (g_enableRandomDelay) {
        /* randomly sleep 0-10ms */
        usleep((useconds_t)rand() % 10000);
    }
    if (g_isAsan && file != NULL && file[0] == '/') {
        char *f = NULL;
        char *p = strchr(file + 1, '/');
        asprintf(&f, "/data%s", (p ? p : file));
        if (f == NULL) {
            exit(1);
        }
        mode_t old = umask(0);
        FILE *logFile = fopen("/dev/asan/dlopen.log", "a");
        umask(old);
        if (logFile != NULL) {
            char name[16] = {0};
            prctl(PR_GET_NAME, name);
            fprintf(logFile, "[%d:%d](%s) dlopen %s --> %s\n", getpid(), gettid(), name, file, f);
            fclose(logFile);
        }
        void *ret = real_dlopen(f, mode);
        free(f);
        f = NULL;
        if (ret != NULL) {
            return ret;
        }
    }
    return real_dlopen(file, mode);
}
