#!/bin/bash                                                                                                                                                                                
# Copyright (c) 2024 Huawei Device Co., Ltd.
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
for arg in  $*
do
if [[ $(uname -s) == "Darwin" ]]; then
if [[ -f "$arg/CMakeDetermineCCompiler.cmake" ]]; then
sed -i '' '90 a\
if(CMAKE_C_COMPILER_TARGET)\
  set(CMAKE_C_COMPILER_ID_TEST_FLAGS_FIRST "-c --target=${CMAKE_C_COMPILER_TARGET}")\
endif()
' $arg/CMakeDetermineCCompiler.cmake
fi

if [[ -f "$arg/CMakeDetermineCXXCompiler.cmake" ]]; then
sed -i '' '85 a\
if(CMAKE_CXX_COMPILER_TARGET)\
  set(CMAKE_CXX_COMPILER_ID_TEST_FLAGS_FIRST "-c --target=${CMAKE_CXX_COMPILER_TARGET}")\
endif()
' $arg/CMakeDetermineCXXCompiler.cmake
fi
else
if [[ -f "$arg/CMakeDetermineCCompiler.cmake" ]]; then
sed -i '90 a if(CMAKE_C_COMPILER_TARGET)\
  set(CMAKE_C_COMPILER_ID_TEST_FLAGS_FIRST "-c --target=${CMAKE_C_COMPILER_TARGET}")\
endif()' $arg/CMakeDetermineCCompiler.cmake
fi

if [[ -f "$arg/CMakeDetermineCXXCompiler.cmake" ]]; then
sed -i '85 a if(CMAKE_CXX_COMPILER_TARGET)\
  set(CMAKE_CXX_COMPILER_ID_TEST_FLAGS_FIRST "-c --target=${CMAKE_CXX_COMPILER_TARGET}")\
endif()' $arg/CMakeDetermineCXXCompiler.cmake
fi
fi
done
