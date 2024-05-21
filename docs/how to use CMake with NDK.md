# 使用CMake与OHOS NDK编译三方库

OHOS NDK支持通过工具链使用CMake编译C/C++代码，工具链文件是用于自定义交叉编译工具链行为的 CMake 文件。OHOS NDK使用的编译工具链在OHOS SDK目录下的位置：`native/build/cmake/ohos.toolchain.cmake`。
使用命令行进行CMake编译时，需要指定工具链文件ohos.toolchain.cmake所在路径。
本文介绍CMake与OHOS NDK搭配如何使用。

## OpenHarmony NDK获取方式

1. 获取已发布版本，参考：[OpenHarmony Release Notes](https://gitee.com/openharmony/docs/tree/master/zh-cn/release-notes#openharmony-release-notes)，选择对应版本，在“从镜像站点获取”小节下载对应版本SDK包，NDK包含在SDK包中。  
2. 获取每日构建版本，每日构建地址：[OpenHarmony dailybuilds](http://ci.openharmony.cn/workbench/cicd/dailybuild/dailylist)，在每日构建形态组件中选择"ohos-sdk"，下载对应SDK包，NDK包含在SDK包中。

3. 获取源码构建版本，参考：[sourcecode acquire](https://gitee.com/openharmony/docs/blob/master/zh-cn/device-dev/get-code/sourcecode-acquire.md)，下载OpenHarmony源码，执行以下命令编译SDK：  
（1）若首次编译OpenHarmony源码，需要安装依赖：`./build/build_scripts/env_setup.sh`， 完成后执行：`source ~/.bashrc`  
   （2）下载预编译工具链：`./build/prebuilts_download.sh`  
   （3）编译SDK：`./build.sh --product-name ohos-sdk`  
   （4）生成SDK所在路径：`out/sdk/packages`  

## OpenHarmony NDK说明

SDK包中native所在目录即是NDK，目录如下：

```
native
   ├── build
   │   └── cmake
   │   ├── ohos.toolchain.cmake         # 编译的工具链
   │   └── sdk_native_platforms.cmake  
   ├── build-tools                      # cmake编译工具所在目录
   ├── docs
   ├── llvm                             # llvm编译器工具链
   ├── nativeapi_syscap_config.json     # NDK提供的SystemCapability的相关头文件
   ├── ndk_system_capability.json       # NDK提供的SystemCapability的描述文件
   ├── oh-uni-package.json              # 版本信息
   ├── NOTICE.txt
   └── sysroot
```

* build目录
  build目录下的ohos.toolchain.cmake是工具链文件，使用CMake编译时，需要指定工具链文件ohos.toolchain.cmake所在路径。cmake编译时需要读取该文件中的默认值，比如编译器的选择、编译平台。
* build-tools
  build-tools目录下是NDK自带的cmake编译工具，配置编译环境时需要添加cmake路径
* llvm
  llvm目录是OHOS NDK提供的编译器工具


## 环境配置

### linux

将OHOS NDK自带的build-tools目录下cmake工具添加到环境变量

```
# 打开.bashrc文件
vim ~/.bashrc
# 在文件最后添加cmake路径，该路径是自己的放置文件的路径，之后保存退出
export PATH=${OHOS SDK路径}/ohos-sdk/linux/native/build-tools/cmake/bin:$PATH
# 在命令行执行source ~/.bashrc使环境变量生效
source ~/.bashrc
```

使用`which cmake`和`cmake --version`验证是否生效。

### windows

右键点击我的电脑，在下拉框中选择我的电脑，点击高级系统设置，点击环境变量，点击Path后点编辑，点击新建，将路径添加进去。


使用`cmake --version`验证是否生效。


## CMake编译

使用CMake编译时，需要指定工具链文件，同时还需要指定OHOS平台的参数
常用参数如下：

| 参数                   | 类型                    | 备注              |
| ------------------------ | ------------------------- | ------------------- |
| OHOS_STL              | c++_shared/c++_static | 默认是c++_shared |
| OHOS_ARCH             | armeabi-v7a             | 设置ABI           |
| OHOS_PLATFORM         | OHOS                    | 平台选择          |
| CMAKE_TOOLCHAIN_FILE | 工具链文件              | -                 |

### linux

#### 创建demo工程

工程目录

```
├── CMakeLists.txt
└── src
    ├── CMakeLists.txt
    └── hello.cpp
```

外部 CMakeLists.txt内容：

```
#cmake的版本
CMAKE_MINIMUM_REQUIRED(VERSION 3.16)
#工程名称
PROJECT(HELLO)
#添加一个子目录并构建该子目录。
ADD_SUBDIRECTORY(src bin)
```

src目录下源码文件hello.cpp内容：

```cpp
#include <iostream>

int main(int argc,const char **argv)
{
    std::cout<< "hello world!" <<std::endl;
    return 0;
}
```

src目录下CMakeLists.txt内容：

```
SET(LIBHELLO_SRC hello.cpp)

#添加静态库
ADD_LIBRARY(hello_static STATIC ${LIBHELLO_SRC})
#将静态库的名字hello_static修改为hello
SET_TARGET_PROPERTIES(hello_static PROPERTIES OUTPUT_NAME "hello")

#添加动态库
ADD_LIBRARY(hello SHARED ${LIBHELLO_SRC})
#将动态库的名字修改为hello
SET_TARGET_PROPERTIES(hello PROPERTIES OUTPUT_NAME "hello")

#生成可执行程序
ADD_EXECUTABLE(Hello ${LIBHELLO_SRC})
```

#### 编译

使用OHOS_STL=c++_shared动态编译：

```
# 在demo工程目录下创建build目录，用于存放cmake构建过程中的中间文件
step1：mkdir build && cd build
# 传递参数给CMake
step2：cmake -DOHOS_STL=c++_shared -DOHOS_ARCH=armeabi-v7a -DOHOS_PLATFORM=OHOS -DCMAKE_TOOLCHAIN_FILE=${OHOS SDK路径}/ohos-sdk/linux/native/build/cmake/ohos.toolchain.cmake ..
# 执行cmake构建命令
step3：cmake --build .
```

构建成功build/bin目录下的产物

```
build/bin
├── CMakeFiles
├── cmake_install.cmake
├── Hello
├── libhello.a
├── libhello.so
└── Makefile
```

### windows

#### 创建demo

源码hello.cpp内容：

```cpp
#include <iostream>

int main(int argc,const char **argv)
{
    std::cout<< "hello world!" <<std::endl;
    return 0;
}
```

源码同级目录下CMakeLists.txt内容：

```
#cmake的版本
CMAKE_MINIMUM_REQUIRED(VERSION 3.16)

#工程名称
PROJECT(HELLO)

#生成可执行程序
ADD_EXECUTABLE(Hello hello.cpp)
```

#### 编译

在windows下使用cmake进行编译，通过`-G`参数选择使用的生成器，这点和linux有区别。

```
step1:在demo工程CMakeList.txt的同级目录创建build目录，然后再build目录下打开powerShell
step2:传递cmake参数
${OHOS NDK所在路径}\native\build-tools\cmake\bin\cmake.exe -G "Ninja" -DOHOS_STL=c++_shared -DOHOS_ARCH=armeabi-v7a -DOHOS_PLATFORM=OHOS   -DCMAKE_TOOLCHAIN_FILE=D:\develop\OHOS-NDK\native\build\cmake\ohos.toolchain.cmake ..
step3:cmake --build .
```

执行成功后生成的产物中build.ninja文件是根据指定的ninja生成器生成的目标文件，Hello是生成的可执行程序。

## OHOS平台相关参数说明

CMake与OHOS NDK搭配使用自定义OHOS交叉工具链，涉及一些OHOS平台的工具链参数。一般在使用CMake编译时，常用OHOS_STL，OHOS_ARCH，OHOS_PLATFORM参数。

| OHOS平台参数 | 说明 |
| --- | ------ | 
| OHOS_AR |  指定构建过程中处理静态库的归档工具，默认设置为NDK中提供的归档工具llvm-ar | 
| OHOS_ARCH |设置目标ABI，默认arm64-v8a，可选armeabi-v7a，x86_64   | 
| OHOS_ARM_NEON | 指定ARM架构目标二进制文件生成指令集类型，默认 thumb| 
| OHOS_ASM_COMPILER_FLAGS | 设置ASM编译器flags | 
|OHOS_COMMON_LINKER_FLAGS  |设置通用链接器flags  | 
|  OHOS_C_COMPILER_FLAGS| 设置C编译器flags |
| OHOS_DEBUG_COMPILER_FLAGS |  编译器在debug模式的flags,默认启用-O0 -g -fno-limit-debug-info| 
| OHOS_EXE_LINKER_FLAGS | 设置传递给链接可执行文件的链接器的flags  | 
| OHOS_LLVM | 指定OHOS平台使用的llvm版本，如arm-linux-ohos ，根据设置的OHOS_ARCH决定 |  
| OHOS_PIE | 指定是否在构建过程中启用PIE编译选项，默认设置为true，为应用程序启用PIE | 
| OHOS_PLATFORM | 指定构建时使用的平台，仅支持OHOS | 
| OHOS_PLATFORM_LEVEL | 指定目标OHOS平台的级别，默认为1  | 
|OHOS_RANLIB| 指定在交叉编译过程中用来生成静态库索引表的工具ranlib的路径 | 
| OHOS_RELEASE_COMPILER_FLAGS | 指定release构建模式下编译器的flags |  
| OHOS_SDK_NATIVE | 指定OHOS SDK中native所在的路径| 
| OHOS_SDK_NATIVE_PLATFORM |  指定ohos sdk中native平台，如ohos-1 | 
| OHOS_SDK_NATIVE_PLATFORM_LEVEL |  指定ohos sdk中native平台级别 | 
| OHOS_SDK_NATIVE_TOOLCHAIN_DEFINED |  定义ohos sdk中native下的交叉编译工具链 |  
| OHOS_STL | 指定构建时使用的STL类型，默认c++_shared，可选c++_static | 
| OHOS_TOOLCHAIN | 指定CMake构建中交叉编译工具链，默认clang  | 
| OHOS_TOOLCHAIN_NAME | 指定交叉编译工具链名称，默认根据OHOS_ARCH决定 |