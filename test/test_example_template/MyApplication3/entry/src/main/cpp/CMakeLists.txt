# the minimum version of CMake.
cmake_minimum_required(VERSION 3.4.1)
project(MyApplication3)

set(NATIVERENDER_ROOT_PATH ${CMAKE_CURRENT_SOURCE_DIR})

include_directories(${NATIVERENDER_ROOT_PATH}
                    ${NATIVERENDER_ROOT_PATH}/include
                    ${NATIVERENDER_ROOT_PATH}/../../../../hello_world/include)

add_library(entry SHARED hello.cpp)
target_link_libraries(entry PUBLIC libace_napi.z.so ${NATIVERENDER_ROOT_PATH}/../../../libs/${OHOS_ARCH}/libhello_world.z.so)