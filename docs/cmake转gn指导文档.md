# cmake转gn指导

## 概述
本文档介绍GN构建工具在OpenHarmony中的常见使用方法，指导三方库由cmake构建到GN构建的转换。

## GN常用的内置变量
| 名称                | 描述            |
|-------------------|---------------|
| current_cpu       | 当前工具链的处理器架构   |
| current_os        | 当前工具链的操作系统类型 |
| current_toolchain | 表示当前使用的工具链    |
| default_toolchain | 表示默认使用的工具链    |
| target_cpu        | 表示目标平台的CPU类型  |
| target_os         | 表示目标平台的操作系统类型 |
| root_build_dir    | 表示根目录的构建目录    |
| root_gen_dir      | 表示根目录的生成目录    |
| root_out_dir      | 表示根目录的输出目录    |
| target_out_dir    | 表示目标文件的输出目录 |
| target_gen_dir    | 表示中间文件的生成目录 |
| defines | 表示当前目标的预定义宏列表 |
| include_dirs | 表示当前目标的头文件搜索路径列表 |
| cflags | 表示当前目标的C语言编译选项列表 |
| cxxflags | 表示当前目标的C++语言编译选项列表 |
| ldflags | 表示当前目标的链接选项列表 |
| asmflags | 表示当前目标的汇编语言编译选项列表 |
| libs | 表示当前目标依赖的库文件列表 |

## GN常用的内置函数
| 名称 | 描述 |
|------|-----|
| assert() | 断言函数，如果条件不成立，则会抛出一个异常 |
| defined() | 判断变量是否已经定义 |
| exec_script() | 执行一个Python脚本 |
| get_label_info() | 获取标签信息，例如标签的名称、路径、类型等等 |
| get_path_info() | 获取路径信息，例如路径是否存在、是否是目录、是否是文件等等 |
| group() | 将一组目标文件组合成一个库文件 |
| import() | 导入其他GN构建文件 |
| read_file() | 读取文件内容 |
| read_json() | 读取JSON格式的文件 |
| read_path() | 读取路径中的内容，返回一个字符串列表 |
| rebase_path() | 重新定位路径，将路径中的某个部分替换为新的值 |
| write_file() | 写入文件内容 |
| template() | 处理字符串模板，将模板中的变量替换为实际的值，其功能类似与函数 |
| action() | 定义一个自定义的构建动作，通过action调用python脚本完成期望动作 |
| action_foreach() | 针对每个元素执行一个自定义的构建动作 |
| executable() | 定义一个可执行文件 |
| shared_library() | 定义一个动态库 |
| static_library() | 定义一个静态库 |


## 如何使用GN进行构建
当将一个基于CMake的项目转换为使用GN进行构建时，需要了解如何指定动态库、静态库和可执行文件的构建规则。以下是一个简单的指南，介绍如何在GN中指定这些构建规则：
- **动态库**  

在CMake中，可以使用add_library命令来指定动态库的构建规则。例如：
```
add_library(mylib SHARED
  src/foo.cpp
  src/bar.cpp
)
```
在GN中，可以使用shared_library模板来指定动态库的构建规则，创建BUILD.gn文件，内容如下：
```
# 指定动态库名称
mylib_name = "mylib"

# 指定动态库源文件
mylib_sources = [
  "src/foo.cpp",
  "src/bar.cpp",
]

# 指定动态库编译选项和链接选项
mylib_cflags = [
  "-Wall",
]
mylib_ldflags = [
  "-L/usr/local/lib",
]

# 指定动态库构建规则
shared_library(mylib_name) {
  sources = mylib_sources
  cflags = mylib_cflags
  ldflags = mylib_ldflags
}
```

- **静态库**  

在CMake中，可以使用add_library命令来指定静态库的构建规则。例如：
```
add_library(mylib STATIC
  src/foo.cpp
  src/bar.cpp
)

```

在GN中，可以使用static_library模板来指定静态库的构建规则，创建BUILD.gn文件，内容如下：
```
# 指定静态库名称
mylib_name = "mylib"

# 指定静态库源文件
mylib_sources = [
  "src/foo.cpp",
  "src/bar.cpp",
]

# 指定静态库编译选项
mylib_cflags = [
  "-Wall",
]

# 指定静态库构建规则
static_library(mylib_name) {
  sources = mylib_sources
  cflags = mylib_cflags
}
```

- **可执行文件**

在CMake中，可以使用add_executable命令来指定可执行文件的构建规则。例如：
```
add_executable(myapp
  src/main.cpp
)
```
在GN中，可以使用executable模板来指定可执行文件的构建规则。例如：
```
# 指定可执行文件名称
myapp_name = "myapp"

# 指定可执行文件源文件
myapp_sources = [
  "src/main.cpp",
]

# 指定可执行文件编译选项和链接选项
myapp_cflags = [
  "-Wall",
]
myapp_ldflags = [
  "-L/usr/local/lib",
]

# 指定可执行文件构建规则
executable(myapp_name) {
  sources = myapp_sources
  cflags = myapp_cflags
  ldflags = myapp_ldflags
}
```

OpenHarmony在GN原生模板的基础上进行了功能扩展，提供了ohos_shared_library、ohos_static_library、ohos_executable模板，在BUILD.gn中import("//build/ohos.gni")即可使用，ohos_shared_library示例如下：
```
import("//build/ohos.gni")
ohos_shared_library("helloworld") {
  sources = []
  include_dirs = []
  cflags = []
  cflags_c = []
  cflags_cc = []
  ldflags = []
  configs = []
  deps = []  # 部件内模块依赖

  # 跨部件模块依赖定义，
  # 定义格式为 "部件名:模块名称"
  # 这里依赖的模块必须是依赖的部件声明在inner_kits中的模块
  external_deps = [
    "part_name:module_name",
  ]

  output_name = ""           # 可选，模块输出名
  output_extension = ""      # 可选，模块名后缀
  module_install_dir = ""    # 可选，缺省在/system/lib64或/system/lib下， 模块安装路径，模块安装路径，从system/，vendor/后开始指定
  relative_install_dir = ""  # 可选，模块安装相对路径，相对于/system/lib64或/system/lib；如果有module_install_dir配置时，该配置不生效
  install_images = []        # 可选，缺省值system，指定模块安装到那个分区镜像中，可以指定多个

  part_name = "" # 必选，所属部件名称
}
```

## 简单示例
假设我们有一个简单的CMake项目，包含两个源文件：main.cpp和hello.cpp，以及一个头文件hello.h。CMakeLists.txt文件内容如下：
```
cmake_minimum_required(VERSION 3.10)

project(hello)

add_executable(hello main.cpp hello.cpp hello.h)
```

目录结构如下：
```
hello/
├── include
│   └── hello.h
└── src
    ├── hello.cpp
    └── main.cpp
```

以下介绍如何在OpenHarmony编译框架中使用GN编译上述示例：
1. 在OpenHarmony代码中，增加example目录，将hello示例放在example目录下，在hello目录下新建BUILD.gn文件，示例如下：
```
import("//build/ohos.gni")

config("hello_config") {
    include_dirs = [ "./include" ]
}

ohos_shared_library("hello_so") {
    configs = [ ":hello_config" ]
    sources = [ "./src/hello.cpp" ]
    part_name = "hello"
    subsystem_name = "example"
}

ohos_executable("hello") {
    deps = [ ":hello_so" ]
    configs = [ ":hello_config" ]
    sources = [ "./src/main.cpp" ]
    part_name = "hello"
    subsystem_name = "example"
}
```

2. 在example目录下新建bundle.json文件，示例如下：
```
{
   "name": "@ohos/example",                 
   "description": "",             
   "version": "3.1",                                 
   "license": "MIT",                                 
   "publishAs": "code-segment",                      
   "segment": {
       "destPath": ""
   },                                                 
   "dirs": {},                                       
   "scripts": {},                                    
   "licensePath": "COPYING",
   "readmePath": {
       "en": "README.rst"
   },
   "component": {                                    
       "name": "hello",                                       # 部件名称
       "subsystem": "example",                                # 部件所属子系统             
       "syscap": [],                                 
       "features": [],                               
       "adapted_system_type": [],                    
       "rom": "",
       "ram": "",                               
       "deps": {
           "components": [],                         
           "third_party": []                         
       },
       "build": {                                    
           "group_type": {                                    # 部件编译入口，新增模块在此处配置
               "base_group": [ "//example/hello:hello" ],   
               "fwk_group": [],
               "service_group": []
           },
           "inner_kits": [],                         
           "test": []                                
       }
   }
}
```

3. 在`vendor\产品厂商\产品名\config.json`中配置新增的example子系统和hello组件，以rk3568为例，示例如下：
```
# 以rk3568为例
{
  "product_name": "rk3568",
  "device_company": "rockchip",
  "device_build_path": "device/board/hihope/rk3568",
  "target_cpu": "arm",
  "type": "standard",
  "version": "3.0",
  "board": "rk3568",
  "api_version": 8,
  "enable_ramdisk": true,
  "enable_absystem": false,
  "build_selinux": true,
  "build_seccomp": true,
  "inherit": [ "productdefine/common/inherit/rich.json", "productdefine/common/inherit/chipset_common.json" ],
  "subsystems": [
    {
      "subsystem": "example",
      "components": [
        {
          "component": "hello",
          "features": []
        }
      ]
    },
    ......
  ]
}
```

4. 在build/subsystem_config.json中增加新增的example子系统路径，示例如下：
```
{
  "example": {
    "path": "example",
    "name": "example"
  }
  ......
}
```

5. 执行编译命令，以rk3568为例：
```
./build.sh --product-name rk3568 -T hello

# build.sh是OpenHarmony编译入口脚本
# --product-name用于指定产品名
# -T指定编译目标，单独编译
```

6. 编译产物生成在out/rk3568/example/hello目录下：
```
out/rk3568/example/hello/
├── hello
└── libhello_so.z.so
```