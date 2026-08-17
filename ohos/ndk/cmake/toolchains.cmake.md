# ohos.toolchain.cmake 详解

## 1. 基本信息

| 项目 | 内容 |
| --- | --- |
| **文件路径** | `build/ohos/ndk/cmake/ohos.toolchain.cmake` |
| **文件行数** | 430 行 |
| **版权** | Copyright (c) 2021 Huawei Device Co., Ltd. |
| **许可证** | Apache License, Version 2.0 |
| **依赖文件** | `sdk_native_platforms.cmake`（同目录，`include` 引入） |
| **文件类型** | CMake 工具链文件（Toolchain File） |

## 2. 文件作用概述

该文件是 **OpenHarmony NDK（Native Development Kit）提供给 CMake 使用的交叉编译工具链配置文件**（Toolchain File）。它的核心作用是：

- 告诉 CMake **"我要为 OpenHarmony 操作系统编译代码，而不是为本机编译"**；
- 指定交叉编译要使用的 **编译器（clang/clang++）、工具（llvm-ar、llvm-ranlib）和 sysroot**；
- 配置目标平台相关的信息（ABI 架构、目标三元组、SDK 平台版本等）；
- 为 C/C++/ASM 语言设置编译、链接、调试、发布等各类 flag；
- 提供一组 `OHOS_*` 变量，使用户可以在命令行通过 `-DOHOS_xxx=...` 定制编译行为。

它的文件头注释（第 14~16 行）也说明了这一点：

> The configuration of toolchain file supplied to cmake, which specifies locations for compilers and toolchain utilities, and other target platform and compiler related information.
> （提供给 cmake 的工具链文件配置，用于指定编译器和工具链工具的位置，以及其他目标平台和编译器相关信息。）

---

## 3. 文件整体结构（按功能分区）

| 行号区间 | 功能分区 | 说明 |
| --- | --- | --- |
| 1~16 | 版权声明与文件描述 | Apache 2.0 许可、文件用途说明 |
| 18~25 | 最小 CMake 版本与防重复加载 | 版本要求、`OHOS_SDK_NATIVE_TOOLCHAIN_DEFINED` 哨兵变量 |
| 27~34 | SDK Native 路径与版本探测 | 定位 `OHOS_SDK_NATIVE`，读取 `oh-uni-package.json` 版本号 |
| 36~70 | 公共默认设置 | 平台名、平台等级、工具链、STL、PIE、NEON、ABI、未定义符号 |
| 72~75 | ccache 支持 | 若定义了 `SDK_NATIVE_CCACHE` 则启用 ccache |
| 77~84 | SDK Native 平台 | include `sdk_native_platforms.cmake`，确定平台等级 |
| 86~91 | 查找根路径模式 | 设置 `CMAKE_FIND_ROOT_PATH_*_MODE` |
| 93~111 | 架构到工具链名映射 | `arm64-v8a` / `armeabi-v7a` / `x86_64` |
| 113~137 | 兼容 SDK 版本格式化 | `OHOS_COMPATIBLE_SDK_VERSION` 的四种格式处理 |
| 139~148 | 编译器 target 与 try_compile | 设置 `CMAKE_*_COMPILER_TARGET` 和试编译变量导出 |
| 150~215 | C 编译器 flags | 通用、安全、ASAN/HWASAN/TSAN/UBSAN 等 |
| 217~232 | C++ 与 ASM flags、Debug/Release flags | 复用与变体 flag |
| 234~263 | 链接 flags | 通用、可执行、STL 相关 |
| 265~298 | 全局 C/C++/ASM flags 写入 cache | `CMAKE_C_FLAGS` 等 |
| 300~403 | 链接 flags 的持久化管理 | 标记（Marker）机制，重配置时保留用户 flags |
| 405~409 | 可执行后缀 | Windows 下加 `.exe` |
| 411~428 | 工具链与编译器路径配置 | sysroot、编译器、ar、ranlib 等 |

---

## 4. 关键实现逻辑详解

### 4.1 防重复加载（第 18~25 行）

```cmake
cmake_minimum_required(VERSION 3.6.0)   # 要求 CMake >= 3.6
set(CMAKE_SYSTEM_VERSION 1)              # 目标系统版本（OpenHarmony API level 相关）
set(CMAKE_ASM_COMPILER_VERSION 15.0.4)   # 汇编编译器版本（clang 15.0.4）

if(DEFINED OHOS_SDK_NATIVE_TOOLCHAIN_DEFINED)
  return()                               # 已定义过则直接返回，防止重复处理
endif()
set(OHOS_SDK_NATIVE_TOOLCHAIN_DEFINED true)
```

- `CMAKE_SYSTEM_VERSION` 设置为 1，表示目标系统的 API 级别（默认值）。
- 通过哨兵变量 `OHOS_SDK_NATIVE_TOOLCHAIN_DEFINED` 保证工具链文件只被完整处理一次（例如在多模块/嵌套 project 中）。

### 4.2 定位 SDK 与版本探测（第 27~34 行）

```cmake
get_filename_component(OHOS_SDK_NATIVE "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
file(TO_CMAKE_PATH "${OHOS_SDK_NATIVE}" OHOS_SDK_NATIVE)

file(STRINGS "${OHOS_SDK_NATIVE}/oh-uni-package.json" NATIVE_VER REGEX "\"version\":.*")
string(REGEX REPLACE "\"version\":(.*)$" "\\1" SDK_NATIVE_VERSION "${NATIVE_VER}")
string(STRIP "${SDK_NATIVE_VERSION}" SDK_NATIVE_VERSION)
```

- `OHOS_SDK_NATIVE`：由当前文件所在目录上溯两级得到（`cmake/../..` = NDK 根目录）。
- 从 `oh-uni-package.json` 中正则提取 `"version": ...` 字段得到 `SDK_NATIVE_VERSION`（NDK 版本字符串）。

### 4.3 公共默认设置（第 36~70 行）

| 变量 | 默认值 | 含义 |
| --- | --- | --- |
| `OHOS` | `OHOS` | 标记当前为 OHOS 平台 |
| `CMAKE_SYSTEM_NAME` | `OHOS` | CMake 系统名，触发交叉编译模式 |
| `OHOS_PLATFORM_LEVEL` | `1` | 目标平台（API）等级 |
| `OHOS_TOOLCHAIN` | `clang` | 工具链类型，仅支持 clang |
| `OHOS_STL` | `c++_shared` | C++ 标准库链接方式（`c++_shared` / `c++_static` / `none`） |
| `OHOS_PIE` | `TRUE` | 是否生成位置无关可执行文件（PIE） |
| `OHOS_ARM_NEON` | `thumb` | ARM NEON/Thumb 指令选择 |
| `OHOS_ARCH` | `arm64-v8a` | 目标 ABI 架构 |
| `OHOS_ALLOW_UNDEFINED_SYMBOLS` | 取决于 `OHOS_NO_UNDEFINED` | 是否允许未定义符号 |

> 所有变量均遵循 **"仅当用户未定义时才设置默认值"**（`if(NOT DEFINED ...)`）的模式，因此用户可通过 `-DOHOS_ARCH=x86_64` 等方式覆盖默认值。

### 4.4 ccache（第 72~75 行）

```cmake
if(DEFINED SDK_NATIVE_CCACHE AND NOT DEFINED OHOS_CCACHE)
  set(OHOS_CCACHE "${SDK_NATIVE_CCACHE}")
endif()
```

- 如果构建系统传入了 `SDK_NATIVE_CCACHE`（ccache 可执行文件路径），则记录到 `OHOS_CCACHE`，供后续调用 ccache 加速编译。（本文件中未进一步使用该变量，主要供上层 CMake 逻辑使用。）

### 4.5 SDK Native 平台（第 77~84 行）

```cmake
include(${CMAKE_CURRENT_LIST_DIR}/sdk_native_platforms.cmake)
if(NOT DEFINED OHOS_SDK_NATIVE_PLATFORM)
  set(OHOS_SDK_NATIVE_PLATFORM "ohos-${SDK_NATIVE_MIN_PLATFORM_LEVEL}")
endif()
string(REPLACE "ohos-" "" OHOS_SDK_NATIVE_PLATFORM_LEVEL ${OHOS_SDK_NATIVE_PLATFORM})
```

- 引入 `sdk_native_platforms.cmake`，其中定义了 `SDK_NATIVE_MIN_PLATFORM_LEVEL` 和 `SDK_NATIVE_MAX_PLATFORM_LEVEL`（当前均为 `"1"`）。
- `OHOS_SDK_NATIVE_PLATFORM` 形如 `ohos-1`，`OHOS_SDK_NATIVE_PLATFORM_LEVEL` 则剥去 `ohos-` 前缀得到纯数字等级。

### 4.6 查找根路径模式（第 86~91 行）

```cmake
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)
list(APPEND CMAKE_FIND_ROOT_PATH "${OHOS_SDK_NATIVE}")
```

交叉编译的关键设置：

- `PROGRAM NEVER`：查找可执行程序在本机系统路径（避免错误使用目标机程序）。
- `LIBRARY / INCLUDE / PACKAGE ONLY`：库、头文件、包只在 `CMAKE_FIND_ROOT_PATH`（即 `OHOS_SDK_NATIVE`）内查找，保证链接到 OHOS 的 sysroot 库。

### 4.7 架构到工具链映射（第 93~111 行）

```cmake
set(CMAKE_OHOS_ARCH_ABI ${OHOS_ARCH})
if(OHOS_ARCH STREQUAL arm64-v8a)
  set(OHOS_TOOLCHAIN_NAME aarch64-linux-ohos)
  ...
  set(CMAKE_SYSTEM_PROCESSOR aarch64)
elseif(OHOS_ARCH STREQUAL armeabi-v7a)
  set(OHOS_TOOLCHAIN_NAME arm-linux-ohos)
  ...
elseif(OHOS_ARCH STREQUAL x86_64)
  set(OHOS_TOOLCHAIN_NAME x86_64-linux-ohos)
  ...
else()
  message(FATAL_ERROR "unrecognized ${OHOS_ARCH}")
endif()
```

支持的三种 ABI 及其目标三元组（LLVM target）：

| `OHOS_ARCH` | `OHOS_TOOLCHAIN_NAME` / `OHOS_LLVM` | `CMAKE_SYSTEM_PROCESSOR` |
| --- | --- | --- |
| `arm64-v8a` | `aarch64-linux-ohos` | `aarch64` |
| `armeabi-v7a` | `arm-linux-ohos` | `arm` |
| `x86_64` | `x86_64-linux-ohos` | `x86_64` |

不支持的架构直接 `FATAL_ERROR` 终止。

### 4.8 兼容 SDK 版本格式化（第 113~137 行）

`OHOS_COMPATIBLE_SDK_VERSION` 用于指定目标设备的兼容 SDK 版本，本文件将其统一为标准三元组 `x.y.z` 格式，用于拼接编译 target：

| 输入格式 | 示例 | 转换后 |
| --- | --- | --- |
| `x.y.z(w)` | `6.0.0(21)` | `21.0.0`（提取括号内数字） |
| `w`（纯数字） | `21` | `21.0.0` |
| `x.y.z` | `6.0.0` | 保持不变 |
| 其他 | `abc` | 清空 + WARNING |

转换后：

```cmake
if(DEFINED OHOS_COMPATIBLE_SDK_VERSION AND NOT "${OHOS_COMPATIBLE_SDK_VERSION}" STREQUAL "")
  set(OHOS_LLVM "${OHOS_LLVM}${OHOS_COMPATIBLE_SDK_VERSION}")
endif()
```

即最终 target 形如 `aarch64-linux-ohos21.0.0`。同时该变量还会触发 `-Wunguarded-availability` 编译选项和链接 `deviceinfo_ndk.z` 库（见后文）。

### 4.9 编译器 target 与 try_compile（第 139~148 行）

```cmake
set(CMAKE_C_COMPILER_TARGET   ${OHOS_LLVM})
set(CMAKE_CXX_COMPILER_TARGET ${OHOS_LLVM})
set(CMAKE_ASM_COMPILER_TARGET ${OHOS_LLVM})

set(CMAKE_TRY_COMPILE_PLATFORM_VARIABLES
  OHOS_SDK_NATIVE
  OHOS_TOOLCHAIN
  OHOS_ARCH
  OHOS_PLATFORM)
```

- 给 C/C++/ASM 编译器统一指定 `--target=<OHOS_LLVM>`。
- 导出部分 `OHOS_*` 变量到 `CMAKE_TRY_COMPILE_PLATFORM_VARIABLES`，使 `try_compile()` 子工程也能继承这些平台变量。

### 4.10 编译 flags（第 150~232 行）

**C 编译器通用 flags（`OHOS_C_COMPILER_FLAGS`）：**

```cmake
-fdata-sections
-ffunction-sections
-funwind-tables
-fstack-protector-strong        # 栈保护
-no-canonical-prefixes
-fno-addrsig
-Wa,--noexecstack               # 栈不可执行
```

按条件追加：

| 条件 | 追加 flags | 说明 |
| --- | --- | --- |
| `OHOS_DISABLE_FORMAT_STRING_CHECKS` | `-Wno-error=format-security` | 关闭格式串安全检查报错 |
| 否则（默认） | `-Wformat -Werror=format-security` | 启用并将格式安全告警视为错误 |
| `OHOS_ARCH == armeabi-v7a` | `-march=armv7a` | 32 位 ARM 架构 |
| `CMAKE_BUILD_TYPE == normal` | `-g` | 生成调试信息 |
| `OHOS_ENABLE_ASAN == ON` | `-shared-libasan -fsanitize=address -fno-omit-frame-pointer -fsanitize-recover=address`（可选 `-fsanitize-blacklist=`） | AddressSanitizer 内存检测 |
| `OHOS_ENABLE_HWASAN == ON` 且 `arm64-v8a` | `-shared-libasan -fsanitize=hwaddress -mllvm -hwasan-globals=0 -fno-emulated-tls -fno-omit-frame-pointer` | HWAddressSanitizer |
| `OHOS_ENABLE_TSAN == ON` 且 `arm64-v8a` | `-shared-libasan -fsanitize=thread -fno-omit-frame-pointer` | ThreadSanitizer 线程检测 |
| `OHOS_ENABLE_UBSAN` | `-shared-libasan -fsanitize=undefined -fno-omit-frame-pointer` | UndefinedBehaviorSanitizer |
| `DEFINED OHOS_COMPATIBLE_SDK_VERSION` | `-Wunguarded-availability` | 兼容 SDK 检查 |

**C++ 编译 flags（`OHOS_CXX_COMPILER_FLAGS`）：** 初始为空，仅 `OHOS_STL == none` 时追加 `-nostdinc++`。

**ASM 编译 flags（`OHOS_ASM_COMPILER_FLAGS`）：** 直接复制 C 编译 flags。

**Debug flags（`OHOS_DEBUG_COMPILER_FLAGS`）：** `-O0 -g -fno-limit-debug-info`

**Release flags（`OHOS_RELEASE_COMPILER_FLAGS`）：** `-O2 -DNDEBUG`

> 所有列表型 flags 最终通过 `string(REPLACE ";" " ")` 转为空格分隔的字符串。

### 4.11 链接 flags（第 234~263 行）

**通用链接 flags（`OHOS_COMMON_LINKER_FLAGS`）：**

```cmake
--rtlib=compiler-rt            # 使用 compiler-rt 运行时
-fuse-ld=lld                   # 使用 lld 链接器
```

STL 相关：

| `OHOS_STL` | 追加 flags |
| --- | --- |
| `c++_static` | `-static-libstdc++` |
| `none` | CXX 加 `-nostdinc++`，链接加 `-nostdlib++` |
| `c++_shared`（默认） | 无额外操作 |
| 其他 | `FATAL_ERROR` |

固定追加：

```cmake
-Wl,--build-id=sha1            # 生成 build-id
-Wl,--warn-shared-textrel
-Wl,--fatal-warnings           # 警告视为致命错误
-lunwind                       # 链接 libunwind
```

- 若 `NOT OHOS_ALLOW_UNDEFINED_SYMBOLS`（默认），追加 `-Wl,--no-undefined`（禁止未定义符号）。
- 追加 `-Qunused-arguments -Wl,-z,noexecstack`。

**可执行文件链接 flags（`OHOS_EXE_LINKER_FLAGS`）：** `-Wl,--gc-sections`（垃圾回收无用 section）。

### 4.12 全局 flags 写入 cache（第 265~298 行）

```cmake
set(CMAKE_C_STANDARD_LIBRARIES_INIT "-lm")   # 标准库初始
set(CMAKE_CXX_STANDARD_LIBRARIES_INIT "-lm")
set(CMAKE_POSITION_INDEPENDENT_CODE TRUE)    # PIC

set(CMAKE_C_FLAGS "" CACHE STRING "Flags for all build types.")
set(CMAKE_C_FLAGS "${OHOS_C_COMPILER_FLAGS} ${CMAKE_C_FLAGS} -D__MUSL__")
```

- 定义 `-D__MUSL__` 宏（OHOS 使用 musl libc）。
- 按 Debug/Release 变体分别写入 `CMAKE_{C,CXX,ASM}_FLAGS[_DEBUG|_RELEASE]`。
- 这些 `CMAKE_*_FLAGS` 以 `CACHE STRING` 形式存在，允许用户命令行覆盖。

### 4.13 链接 flags 的持久化管理（第 300~403 行）

这是本文件最复杂、最具技巧性的部分，核心目标：**在 CMake 重新配置（reconfigure）时，既保留 OHOS 默认链接 flags，又不丢失用户通过 `-D` 或 `set_target_properties` 追加的自定义链接 flags。**

**背景问题：** 每次 configure，工具链文件都会用 `CACHE ... FORCE` 重新覆盖 `CMAKE_*_LINKER_FLAGS`。如果直接 `FORCE` 覆盖，用户自定义 flags 会丢失；如果拼接时出错，又可能导致 OHOS 默认 flags 被重复累积。

**实现思路：**

1. 将 "OHOS 默认链接 flags" 定义为 `_OHOS_{SHARED,MODULE,EXE}_LINKER_BASE`。
2. 若定义了 `OHOS_COMPATIBLE_SDK_VERSION`，额外追加 `-ldeviceinfo_ndk.z` 库（避免重复累积，只链接一次）。
3. 通过 `_OHOS_{...}_LINKER_FLAGS_META`（INTERNAL cache）记录带标记的元数据：
   ```
   "_OHOS_BASE_MARKER_BEGIN_ <base> _OHOS_BASE_MARKER_END_ <user flags>"
   ```
4. 每次 configure：
   - 若存在 `_META` 且检测到外部修改（`_EXPECTED` 与当前值不符），用 `string(REPLACE ...)` 提取用户 flags；
   - 否则用正则 `.*_OHOS_BASE_MARKER_END_` 从 `_META` 中截取用户 flags；
   - 首次 configure（无 `_META`）则直接在当前值中去掉 `_BASE` 部分得到用户 flags。
5. 重新拼装 `user + base`，用 `CACHE UNINITIALIZED ... FORCE` 写回，并记录新的 `_EXPECTED` 与 `_META`。

这样即使修改了 `OHOS_STL` / `OHOS_ALLOW_UNDEFINED_SYMBOLS` / `OHOS_COMPATIBLE_SDK_VERSION`（导致 base 变化），用户 flags 也能被正确提取和保留。

### 4.14 可执行后缀（第 405~409 行）

```cmake
set(HOST_SYSTEM_EXE_SUFFIX)
if(CMAKE_HOST_SYSTEM_NAME STREQUAL Windows)
  set(HOST_SYSTEM_EXE_SUFFIX .exe)
endif()
```

在 Windows 宿主上给编译器/工具路径追加 `.exe` 后缀。

### 4.15 工具链与编译器路径（第 411~428 行）

```cmake
set(TOOLCHAIN_ROOT_PATH "${OHOS_SDK_NATIVE}/llvm")
set(TOOLCHAIN_BIN_PATH  "${OHOS_SDK_NATIVE}/llvm/bin")

set(CMAKE_SYSROOT "${OHOS_SDK_NATIVE}/sysroot")
set(CMAKE_LIBRARY_ARCHITECTURE "${OHOS_TOOLCHAIN_NAME}")
list(APPEND CMAKE_SYSTEM_LIBRARY_PATH "/usr/lib/${OHOS_TOOLCHAIN_NAME}")
set(CMAKE_C_COMPILER_EXTERNAL_TOOLCHAIN   "${TOOLCHAIN_ROOT_PATH}")
set(CMAKE_CXX_COMPILER_EXTERNAL_TOOLCHAIN "${TOOLCHAIN_ROOT_PATH}")
set(CMAKE_ASM_COMPILER_EXTERNAL_TOOLCHAIN "${TOOLCHAIN_ROOT_PATH}")
set(CMAKE_C_COMPILER  "${TOOLCHAIN_BIN_PATH}/clang${HOST_SYSTEM_EXE_SUFFIX}")
set(CMAKE_CXX_COMPILER "${TOOLCHAIN_BIN_PATH}/clang++${HOST_SYSTEM_EXE_SUFFIX}")

set(OHOS_AR "${TOOLCHAIN_BIN_PATH}/llvm-ar${HOST_SYSTEM_EXE_SUFFIX}")
set(OHOS_RANLIB "${TOOLCHAIN_BIN_PATH}/llvm-ranlib${HOST_SYSTEM_EXE_SUFFIX}")
set(CMAKE_AR     "${OHOS_AR}" CACHE FILEPATH "Archiver")
set(CMAKE_RANLIB "${OHOS_RANLIB}" CACHE FILEPATH "Ranlib")
set(UNIX TRUE CACHE BOOL "Unix system" FORCE)
```

最终指定的工具链布局（假设 `OHOS_SDK_NATIVE` = NDK 根目录）：

| 变量 | 值 |
| --- | --- |
| `CMAKE_SYSROOT` | `$NDK/sysroot`（目标系统的头文件与库根目录） |
| `CMAKE_C_COMPILER` | `$NDK/llvm/bin/clang` |
| `CMAKE_CXX_COMPILER` | `$NDK/llvm/bin/clang++` |
| `CMAKE_AR` | `$NDK/llvm/bin/llvm-ar` |
| `CMAKE_RANLIB` | `$NDK/llvm/bin/llvm-ranlib` |
| `CMAKE_*_COMPILER_EXTERNAL_TOOLCHAIN` | `$NDK/llvm`（GCC 兼容工具链根，供 clang 找内建工具） |
| `UNIX` | `TRUE`（声明为 Unix 类系统） |

---

## 5. 变量速查表（全部 `OHOS_*` 及关键变量）

### 5.1 用户可配置变量（可用 `-D` 覆盖）

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `OHOS_ARCH` | `arm64-v8a` | 目标 ABI：`arm64-v8a` / `armeabi-v7a` / `x86_64` |
| `OHOS_PLATFORM_LEVEL` | `1` | 目标平台等级 |
| `OHOS_PLATFORM` | - | 目标平台名（供 try_compile 传递） |
| `OHOS_TOOLCHAIN` | `clang` | 工具链类型（当前仅 clang） |
| `OHOS_STL` | `c++_shared` | C++ 标准库：`c++_shared` / `c++_static` / `none` |
| `OHOS_PIE` | `TRUE` | 位置无关可执行文件 |
| `OHOS_ARM_NEON` | `thumb` | ARM NEON/Thumb 模式 |
| `OHOS_NO_UNDEFINED` | - | 若定义，则映射为 `OHOS_ALLOW_UNDEFINED_SYMBOLS` |
| `OHOS_ALLOW_UNDEFINED_SYMBOLS` | 默认 false | 是否允许链接未定义符号（否则 `-Wl,--no-undefined`） |
| `OHOS_CCACHE` | 取 `SDK_NATIVE_CCACHE` | ccache 可执行文件路径 |
| `OHOS_DISABLE_FORMAT_STRING_CHECKS` | false | 关闭 `-Werror=format-security` |
| `OHOS_ENABLE_ASAN` | - | 开启 AddressSanitizer |
| `OHOS_ENABLE_HWASAN` | - | 开启 HWAddressSanitizer（仅 arm64-v8a） |
| `OHOS_ENABLE_TSAN` | - | 开启 ThreadSanitizer（仅 arm64-v8a） |
| `OHOS_ENABLE_UBSAN` | - | 开启 UndefinedBehaviorSanitizer |
| `OHOS_ASAN_BLACKLIST` | - | ASAN/HWASAN 黑名单文件路径 |
| `OHOS_TSAN_BLACKLIST` | - | TSAN 黑名单文件路径 |
| `OHOS_COMPATIBLE_SDK_VERSION` | - | 兼容 SDK 版本，如 `6.0.0(21)` / `21` / `6.0.0` |

### 5.2 内部计算变量（由文件自动推导）

| 变量 | 说明 |
| --- | --- |
| `OHOS_SDK_NATIVE` | NDK 根目录（本文件上溯两级） |
| `SDK_NATIVE_VERSION` | 从 `oh-uni-package.json` 读取的 NDK 版本 |
| `OHOS_SDK_NATIVE_PLATFORM` | 如 `ohos-1` |
| `OHOS_SDK_NATIVE_PLATFORM_LEVEL` | 如 `1`（剥去 `ohos-` 前缀） |
| `OHOS_TOOLCHAIN_NAME` | 目标三元组，如 `aarch64-linux-ohos` |
| `OHOS_LLVM` | 编译器 target（三元组 + 兼容版本后缀） |
| `OHOS_C_COMPILER_FLAGS` | C 通用编译 flags（空格分隔） |
| `OHOS_CXX_COMPILER_FLAGS` | C++ 通用编译 flags |
| `OHOS_ASM_COMPILER_FLAGS` | ASM 编译 flags |
| `OHOS_DEBUG_COMPILER_FLAGS` | Debug 变体 flags：`-O0 -g -fno-limit-debug-info` |
| `OHOS_RELEASE_COMPILER_FLAGS` | Release 变体 flags：`-O2 -DNDEBUG` |
| `OHOS_COMMON_LINKER_FLAGS` | 通用链接 flags |
| `OHOS_EXE_LINKER_FLAGS` | 可执行文件链接 flags |
| `OHOS_AR` / `OHOS_RANLIB` | llvm-ar / llvm-ranlib 路径 |
| `_OHOS_{SHARED,MODULE,EXE}_LINKER_BASE` | OHOS 默认链接 flags（含可选 deviceinfo_ndk.z） |
| `_OHOS_USER_{...}_LINKER_FLAGS` | 用户自定义链接 flags（自动提取） |
| `_OHOS_{...}_LINKER_FLAGS_META` | 标记持久化元数据（INTERNAL cache） |
| `_OHOS_{...}_LINKER_FLAGS_EXPECTED` | 期望值（用于检测外部修改） |
| `_DEVICEINFO_LIB` | `-ldeviceinfo_ndk.z` 或空 |

### 5.3 写入的 CMake 标准变量

| 变量 | 值 |
| --- | --- |
| `CMAKE_SYSTEM_NAME` | `OHOS` |
| `CMAKE_SYSTEM_VERSION` | `1` |
| `CMAKE_SYSTEM_PROCESSOR` | `aarch64` / `arm` / `x86_64` |
| `CMAKE_SYSROOT` | `$NDK/sysroot` |
| `CMAKE_C/CXX/ASM_COMPILER_TARGET` | `OHOS_LLVM` |
| `CMAKE_C/CXX_COMPILER` | `$NDK/llvm/bin/clang[++]` |
| `CMAKE_AR` / `CMAKE_RANLIB` | `llvm-ar` / `llvm-ranlib` |
| `CMAKE_C/CXX/ASM_FLAGS[_DEBUG|_RELEASE]` | 编译 flags（含 `-D__MUSL__`） |
| `CMAKE_SHARED/MODULE/EXE_LINKER_FLAGS` | 链接 flags（含用户 flags 持久化） |
| `CMAKE_FIND_ROOT_PATH` | 追加 `$NDK` |
| `CMAKE_FIND_ROOT_PATH_MODE_*` | PROGRAM=NEVER，其余 ONLY |
| `CMAKE_POSITION_INDEPENDENT_CODE` | `TRUE` |
| `UNIX` | `TRUE` |

---

## 6. 依赖与关联文件

### 6.1 `sdk_native_platforms.cmake`（被 include）

```cmake
set(SDK_NATIVE_MIN_PLATFORM_LEVEL "1")
set(SDK_NATIVE_MAX_PLATFORM_LEVEL "1")
```

- 仅定义 NDK 支持的最小/最大平台等级。
- 被用于计算默认的 `OHOS_SDK_NATIVE_PLATFORM`。

### 6.2 外部文件引用

| 引用 | 用途 |
| --- | --- |
| `$NDK/oh-uni-package.json` | 读取 NDK 版本号（`SDK_NATIVE_VERSION`） |
| `$NDK/sysroot` | 作为 `CMAKE_SYSROOT` |
| `$NDK/llvm/bin/clang[++]` | C/C++ 编译器 |
| `$NDK/llvm/bin/llvm-ar` / `llvm-ranlib` | 归档与索引工具 |

### 6.3 同目录/相关文件

- `build/ohos/ndk/BUILD.gn`、`ndk.gni`：NDK 构建脚本；
- `build/ohos/ndk/OHOS.cmake`：NDK 面向用户的 cmake 入口/辅助模块。

---

## 7. 典型使用方式

在使用 NDK 的 CMake 工程中，通过 `-DCMAKE_TOOLCHAIN_FILE` 指定本文件：

```bash
cmake .. \
  -DCMAKE_TOOLCHAIN_FILE=$NDK/build/cmake/ohos.toolchain.cmake \
  -DOHOS_ARCH=arm64-v8a \
  -DOHOS_PLATFORM_LEVEL=1 \
  -DOHOS_STL=c++_shared
```

也可通过环境变量 `OHOS_SDK_NATIVE`（本文件自动推导，无需手工指定）。

---

## 8. 设计要点总结

1. **交叉编译核心**：`CMAKE_SYSTEM_NAME=OHOS` + `CMAKE_SYSROOT` + target 三元组 + 查找路径模式限制，将 CMake 引导到 OHOS 交叉编译模式。
2. **可配置性**：几乎全部 `OHOS_*` 采用"未定义才给默认值"策略，方便命令行 `-D` 覆盖；支持多种 Sanitizer、STL 模式、ABI。
3. **健壮的链接 flags 管理**：通过带标记的 `_META` 元数据和 `_EXPECTED` 检测机制，解决重配置时"用户 flags 丢失"与"OHOS 默认 flags 重复累积"两大问题，即使 base flags 因 `OHOS_STL` 等变化也能正确还原用户设置。
4. **版本兼容**：`OHOS_COMPATIBLE_SDK_VERSION` 的多种输入格式统一转换，并联动 target 后缀、`-Wunguarded-availability` 与 `deviceinfo_ndk.z` 库链接。
5. **平台差异处理**：对 Windows 宿主追加 `.exe` 后缀。