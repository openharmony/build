# 基于NDK编译三方库

## OpenHarmony NDK获取方式
1. 获取已发布版本，参考：[OpenHarmony Release Notes](https://gitee.com/openharmony/docs/tree/master/zh-cn/release-notes#openharmony-release-notes)，选择对应版本，在“从镜像站点获取”小节下载对应版本SDK包，NDK包含在SDK包中。

2. 获取每日构建版本，每日构建地址：[OpenHarmony dailybuilds](http://ci.openharmony.cn/dailys/dailybuilds)，在每日构建形态组件中选择"ohos-sdk"，下载对应SDK包，NDK包含在SDK包中。

3. 获取源码构建版本，参考：[sourcecode acquire](https://gitee.com/openharmony/docs/blob/master/zh-cn/device-dev/get-code/sourcecode-acquire.md)，下载OpenHarmony源码，执行以下命令编译SDK：  
    （1）若首次编译OpenHarmony源码，需要安装依赖：`./build/build_scripts/env_setup.sh`，完成后执行：`source ~/.bashrc`  
    （2）下载预编译工具链：`./build/prebuilts_download.sh`  
    （3）编译SDK：`./build.sh --product-name ohos-sdk`  
    （4）生成SDK所在路径：`out/sdk/packages`

SDK包目录结构如下图，其中native即为NDK
```
├── linux
│   ├── ets-linux-x64-4.0.6.5-Canary1.zip
│   ├── js-linux-x64-4.0.6.5-Canary1.zip
│   ├── native-linux-x64-4.0.6.5-Canary1.zip
│   ├── previewer-linux-x64-4.0.6.5-Canary1.zip
│   └── toolchains-linux-x64-4.0.6.5-Canary1.zip
└── windows
    ├── ets-windows-x64-4.0.6.5-Canary1.zip
    ├── js-windows-x64-4.0.6.5-Canary1.zip
    ├── native-windows-x64-4.0.6.5-Canary1.zip
    ├── previewer-windows-x64-4.0.6.5-Canary1.zip
    └── toolchains-windows-x64-4.0.6.5-Canary1.zip
```

## OpenHarmony NDK目录
```
native
├── NOTICE.txt
├── build                            # cmake工具链的配置
├── build-tools                      # cmake工具链目录
├── docs
├── llvm                             # llvm编译器工具链
├── nativeapi_syscap_config.json     # NDK提供的SystemCapability的相关头文件
├── ndk_system_capability.json       # NDK提供的SystemCapability的描述文件
├── oh-uni-package.json              # 版本信息
└── sysroot                          # NDK包含的库文件和头文件
```

## 使用OpenHarmony NDK编译三方库
1. 解压NDK压缩包，将cmake工具链添加到环境变量中：`export PATH=${SDK解压路径}/ohos-sdk/linux/native/build-tools/cmake/bin:${PATH}`

2. 安装make：`sudo apt install make`

3. 示例  
- **demo目录**  
```
├── CMakeLists.txt
├── include
│   └── shared
│       └── Hello.h
└── src
    ├── CMakeLists.txt
    ├── Hello.cpp
    └── main.cpp
```

- **CMakeLists.txt**
```
CMAKE_MINIMUM_REQUIRED(VERSION 3.16)

PROJECT(HELLO_LIBRARY)

ADD_SUBDIRECTORY(src)
```

- **src/CMakeLists.txt**
```
SET(EXECUTABLE_OUTPUT_PATH ${PROJECT_BINARY_DIR}/output)
SET(LIBRARY_OUTPUT_PATH ${PROJECT_BINARY_DIR}/output)

############################################################
# Create a library
############################################################

#Generate the shared library from the library sources
ADD_LIBRARY(hello_shared_library SHARED 
        Hello.cpp
        )
ADD_LIBRARY(hello::library ALIAS hello_shared_library)

TARGET_INCLUDE_DIRECTORIES(hello_shared_library
        PUBLIC 
        ${PROJECT_SOURCE_DIR}/include
        )

############################################################
# Create an executable
############################################################

# Add an executable with the above sources
ADD_EXECUTABLE(hello_shared_binary
        main.cpp
        )

# link the new hello_library target with the hello_binary target
TARGET_LINK_LIBRARIES( hello_shared_binary
        PRIVATE 
        hello::library
        )
```

- **Hello.h**
```
#ifndef __HELLO_H__
#define __HELLO_H__

class Hello
{
public:
    void print();
};

#endif
```

- **Hello.cpp**
```
#include <iostream>

#include "shared/Hello.h"

void Hello::print()
{
    std::cout << "Hello Shared Library!" << std::endl;
}
```

- **main.cpp**
```
#include "shared/Hello.h"

int main(int argc, char *argv[])
{
    Hello hi;
    hi.print();
    return 0;
}
```

4. 编译：
```
1. mkdir build && cd build
2. cmake -DOHOS_STL=c++_shared -DOHOS_ARCH=x86_64 -DOHOS_PLATFORM=OHOS -DCMAKE_TOOLCHAIN_FILE=${SDK解压路径}/ohos-sdk/linux/native/build/cmake/ohos.toolchain.cmake .. && make

# 参数解释：
# OHOS_STL：默认c++_shared，可选c++_static
# OHOS_ARCH: 默认arm64-v8a，可选armeabi-v7a、x86_64
# OHOS_PLATFORM：仅支持OHOS
# CMAKE_TOOLCHAIN_FILE：cmake的工具链的配置文件所在路径
```

5. 编译产物：
```
output/
├── hello_shared_binary
└── libhello_shared_library.so
```
