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

# OHOS Lite Wearable Specific Flags
#
# This file is included by ohos.toolchain.cmake when building for lite wearable
# architectures (armv8m, riscv32).
#
# Usage: This file should NOT be used directly. It is auto-included.

#------------------------------------------------------------------------------
# Architecture-specific settings
#------------------------------------------------------------------------------
if(OHOS_ARCH STREQUAL "armv8m")
  set(OHOS_TOOLCHAIN_NAME arm-liteos-ohos)
  set(OHOS_LLVM arm-liteos-ohos)
  set(CMAKE_SYSTEM_PROCESSOR arm)

elseif(OHOS_ARCH STREQUAL "riscv32")
  set(OHOS_TOOLCHAIN_NAME riscv32-linux-ohos)
  set(OHOS_LLVM riscv32-unknown-elf)
  set(CMAKE_SYSTEM_PROCESSOR riscv32)

else()
  message(FATAL_ERROR "OHOS_ARCH ${OHOS_ARCH} is not supported for lite")
endif()

#------------------------------------------------------------------------------
# Compiler Target
#------------------------------------------------------------------------------
set(CMAKE_C_COMPILER_TARGET   ${OHOS_LLVM})
set(CMAKE_CXX_COMPILER_TARGET ${OHOS_LLVM})
set(CMAKE_ASM_COMPILER_TARGET ${OHOS_LLVM})

set(CMAKE_TRY_COMPILE_PLATFORM_VARIABLES
  OHOS_SDK_NATIVE OHOS_TOOLCHAIN OHOS_ARCH OHOS_PLATFORM)

#------------------------------------------------------------------------------
# C Compiler Flags
#------------------------------------------------------------------------------
set(OHOS_C_COMPILER_FLAGS
  -ffunction-sections
  -fdata-sections
  -fstack-protector-strong
  -no-canonical-prefixes
  -fno-addrsig
  -Wa,--noexecstack
  -fno-unwind-tables
  -nostdlibinc)

if(OHOS_ARCH STREQUAL "armv8m")
  list(APPEND OHOS_C_COMPILER_FLAGS -mcpu=cortex-m55)
  list(APPEND OHOS_C_COMPILER_FLAGS -march=armv8m.main+fp)
  list(APPEND OHOS_C_COMPILER_FLAGS -mthumb)
  list(APPEND OHOS_C_COMPILER_FLAGS -mfloat-abi=hard)
  list(APPEND OHOS_C_COMPILER_FLAGS -I"${OHOS_SDK_NATIVE}/sysroot_lite/usr/include")
  list(APPEND OHOS_C_COMPILER_FLAGS -I"${OHOS_SDK_NATIVE}/sysroot_lite/usr/include/arm-liteos-ohos")
elseif(OHOS_ARCH STREQUAL "riscv32")
  list(APPEND OHOS_C_COMPILER_FLAGS -march=rv32imafdc)
  list(APPEND OHOS_C_COMPILER_FLAGS -mabi=ilp32d)
  list(APPEND OHOS_C_COMPILER_FLAGS -I"${OHOS_SDK_NATIVE}/sysroot_lite/usr/include")
  list(APPEND OHOS_C_COMPILER_FLAGS -I"${OHOS_SDK_NATIVE}/sysroot_lite/usr/include/riscv32-linux-ohos")
endif()

string(REPLACE ";" " " OHOS_C_COMPILER_FLAGS "${OHOS_C_COMPILER_FLAGS}")

#------------------------------------------------------------------------------
# C++ Compiler Flags
#------------------------------------------------------------------------------
set(OHOS_CXX_COMPILER_FLAGS
  -fno-exceptions
  -fno-unwind-tables
  -fno-rtti
  -fno-use-cxa-atexit)

string(REPLACE ";" " " OHOS_CXX_COMPILER_FLAGS "${OHOS_CXX_COMPILER_FLAGS}")

#------------------------------------------------------------------------------
# Linker Flags
#------------------------------------------------------------------------------
if(OHOS_ARCH STREQUAL "armv8m")
  set(OHOS_SDK_NATIVE_LIB_PATH "${OHOS_SDK_NATIVE}/sysroot_lite/usr/lib/arm-liteos-ohos")
elseif(OHOS_ARCH STREQUAL "riscv32")
  set(OHOS_SDK_NATIVE_LIB_PATH "${OHOS_SDK_NATIVE}/sysroot_lite/usr/lib/riscv32-linux-ohos")
endif()
set(OHOS_COMMON_LINKER_FLAGS
  -shared
  -nostdlib
  -Wl,-z,noexecstack
  -Wl,-z,relro
  -Wl,-z,now
  -Wl,--gc-sections
  -Wl,--fatal-warnings
  -L"${OHOS_SDK_NATIVE_LIB_PATH}"
  -Wl,--no-undefined
  -Wl,-lc
  )

string(REPLACE ";" " " OHOS_COMMON_LINKER_FLAGS "${OHOS_COMMON_LINKER_FLAGS}")

set(OHOS_EXE_LINKER_FLAGS "")
string(REPLACE ";" " " OHOS_EXE_LINKER_FLAGS "${OHOS_EXE_LINKER_FLAGS}")

#------------------------------------------------------------------------------
# ASM Compiler Flags
#------------------------------------------------------------------------------
set(OHOS_ASM_COMPILER_FLAGS "${OHOS_C_COMPILER_FLAGS}")
string(REPLACE ";" " " OHOS_ASM_COMPILER_FLAGS "${OHOS_ASM_COMPILER_FLAGS}")

#------------------------------------------------------------------------------
# Debug/Release Flags
#------------------------------------------------------------------------------
set(OHOS_DEBUG_COMPILER_FLAGS "-O0 -g -fno-limit-debug-info")
string(REPLACE ";" " " OHOS_DEBUG_COMPILER_FLAGS "${OHOS_DEBUG_COMPILER_FLAGS}")

set(OHOS_RELEASE_COMPILER_FLAGS "-O2 -DNDEBUG")
string(REPLACE ";" " " OHOS_RELEASE_COMPILER_FLAGS "${OHOS_RELEASE_COMPILER_FLAGS}")

#------------------------------------------------------------------------------
# Apply CMake Flags
#------------------------------------------------------------------------------
set(CMAKE_C_FLAGS "" CACHE STRING "Flags for all build types.")
set(CMAKE_C_FLAGS "${OHOS_C_COMPILER_FLAGS} ${CMAKE_C_FLAGS} -D__MUSL__")
set(CMAKE_C_FLAGS_DEBUG "${OHOS_DEBUG_COMPILER_FLAGS}" CACHE STRING "" FORCE)
set(CMAKE_C_FLAGS_RELEASE "${OHOS_RELEASE_COMPILER_FLAGS}" CACHE STRING "")

set(CMAKE_CXX_FLAGS "" CACHE STRING "Flags for all build types.")
set(CMAKE_CXX_FLAGS "${OHOS_C_COMPILER_FLAGS} ${OHOS_CXX_COMPILER_FLAGS} ${CMAKE_CXX_FLAGS} -D__MUSL__")
set(CMAKE_CXX_FLAGS_DEBUG "${OHOS_DEBUG_COMPILER_FLAGS}" CACHE STRING "")
set(CMAKE_CXX_FLAGS_RELEASE "${OHOS_RELEASE_COMPILER_FLAGS}" CACHE STRING "")

set(CMAKE_ASM_FLAGS "" CACHE STRING "Flags for all build types.")
set(CMAKE_ASM_FLAGS "${OHOS_ASM_COMPILER_FLAGS} ${CMAKE_ASM_FLAGS} -D__MUSL__")
set(CMAKE_ASM_FLAGS_DEBUG "${OHOS_DEBUG_COMPILER_FLAGS}" CACHE STRING "")
set(CMAKE_ASM_FLAGS_RELEASE "${OHOS_RELEASE_COMPILER_FLAGS}" CACHE STRING "")

set(CMAKE_SHARED_LINKER_FLAGS "${OHOS_COMMON_LINKER_FLAGS}" CACHE STRING "" FORCE)
set(CMAKE_MODULE_LINKER_FLAGS "${OHOS_COMMON_LINKER_FLAGS}" CACHE STRING "" FORCE)
set(CMAKE_EXE_LINKER_FLAGS "${OHOS_COMMON_LINKER_FLAGS} ${OHOS_EXE_LINKER_FLAGS}" CACHE STRING "" FORCE)

#------------------------------------------------------------------------------
# Standard Libraries
#------------------------------------------------------------------------------
set(CMAKE_C_STANDARD_LIBRARIES_INIT "")
set(CMAKE_CXX_STANDARD_LIBRARIES_INIT "")
set(CMAKE_POSITION_INDEPENDENT_CODE TRUE)

#------------------------------------------------------------------------------
# Executable suffix
#------------------------------------------------------------------------------
set(HOST_SYSTEM_EXE_SUFFIX "")
if(CMAKE_HOST_SYSTEM_NAME STREQUAL Windows)
  set(HOST_SYSTEM_EXE_SUFFIX .exe)
endif()

#------------------------------------------------------------------------------
# Toolchain Paths
#------------------------------------------------------------------------------
set(TOOLCHAIN_ROOT_PATH "${OHOS_SDK_NATIVE}/llvm")
set(TOOLCHAIN_BIN_PATH  "${OHOS_SDK_NATIVE}/llvm/bin")

set(CMAKE_SYSROOT "${OHOS_SDK_NATIVE}/sysroot_lite")
set(CMAKE_LIBRARY_ARCHITECTURE "${OHOS_TOOLCHAIN_NAME}")

if(OHOS_ARCH STREQUAL "armv8m")
  list(APPEND CMAKE_SYSTEM_LIBRARY_PATH "/usr/lib/arm-liteos-ohos")
elseif(OHOS_ARCH STREQUAL "riscv32")
  list(APPEND CMAKE_SYSTEM_LIBRARY_PATH "/usr/lib/riscv32-linux-ohos")
endif()

set(CMAKE_C_COMPILER_EXTERNAL_TOOLCHAIN   "${TOOLCHAIN_ROOT_PATH}")
set(CMAKE_CXX_COMPILER_EXTERNAL_TOOLCHAIN "${TOOLCHAIN_ROOT_PATH}")
set(CMAKE_ASM_COMPILER_EXTERNAL_TOOLCHAIN "${TOOLCHAIN_ROOT_PATH}")
set(CMAKE_C_COMPILER "${TOOLCHAIN_BIN_PATH}/clang${HOST_SYSTEM_EXE_SUFFIX}")
set(CMAKE_CXX_COMPILER "${TOOLCHAIN_BIN_PATH}/clang++${HOST_SYSTEM_EXE_SUFFIX}")

set(OHOS_AR "${TOOLCHAIN_BIN_PATH}/llvm-ar${HOST_SYSTEM_EXE_SUFFIX}")
set(OHOS_RANLIB "${TOOLCHAIN_BIN_PATH}/llvm-ranlib${HOST_SYSTEM_EXE_SUFFIX}")
set(CMAKE_AR "${OHOS_AR}" CACHE FILEPATH "Archiver")
set(CMAKE_RANLIB "${OHOS_RANLIB}" CACHE FILEPATH "Ranlib")
set(UNIX TRUE CACHE BOOL "" FORCE)

#------------------------------------------------------------------------------
# Debug Output
#------------------------------------------------------------------------------
if(OHOS_DEBUG_TOOLCHAIN)
  message(STATUS "OHOS Lite Wearable Toolchain Loaded")
  message(STATUS "  OHOS_ARCH: ${OHOS_ARCH}")
  message(STATUS "  OHOS_TOOLCHAIN_NAME: ${OHOS_TOOLCHAIN_NAME}")
  message(STATUS "  OHOS_LLVM: ${OHOS_LLVM}")
  message(STATUS "  CMAKE_SYSROOT: ${CMAKE_SYSROOT}")
  message(STATUS "  OHOS_C_COMPILER_FLAGS: ${OHOS_C_COMPILER_FLAGS}")
  message(STATUS "  OHOS_COMMON_LINKER_FLAGS: ${OHOS_COMMON_LINKER_FLAGS}")
endif()
