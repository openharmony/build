# OpenHarmony系统动态库分类及管理规则



## 1. OpenHarmony系统动态库分类定义

OpenHarmony系统采用组件化架构，总体分为系统组件（system.img）和芯片组件（vendor.img），每个组件中有不同类型的进程，每个进程会加载不同的动态库。本文结合组件化架构及进程模型，介绍系统中动态库的分类及管理规则。系统中的进程总体分为以下三类：

- 应用进程：系统及三方应用运行时的进程，每个进程都通过appspawn孵化，有独立的沙箱运行环境。
- 系统组件进程：system.img中的native进程，每个进程都通过init拉起；默认所有系统组件进程都运行在一个共同的系统组件沙箱环境里。
- 芯片组件进程：vendor.img中的native进程，每个进程都通过init拉起；默认所有芯片组件进程也都运行在一个共同的芯片组件沙箱环境里。

每种进程加载的动态库分类如下：

### 1.1 CAPI

CAPI是OpenHarmony对应用开放的C语言接口API，应用进程的native模块都基于CAPI开发。

系统中提供的CAPI的模块集合称之为NDK（Native Development Kit），在[categorized-libraries.json](./categorized-libraries.json)中通过以下类型来标识：

- ndk：应用可直接使用的ndk模块列表。

### 1.2 NAPI

NAPI模块是OpenHarmony对应用开放的ArkTS接口的Native实现模块，其实现遵循了业界Node-API的接口规范。NAPI模块都安装在/system/lib{64}/module目录下，不需要在[categorized-libraries.json](./categorized-libraries.json)中单独标识。

### 1.3 Platform SDK

Platform SDK是指被应用进程通过NAPI模块或NDK模块加载的动态库模块集合，Platform SDK也分为两类，在[categorized-libraries.json](./categorized-libraries.json)中通过以下类型来标识：

- platformsdk: NAPI/NDK模块直接依赖的系统组件模块
- platformsdk_indirect: platform模块间接依赖的系统组件模块

### 1.4 Chipset SDK

Chipset SDK是指允许被芯片组件进程加载的系统组件动态库模块集合。

Chipset SDK集合中的单个模块称之为Chipset SDK模块。Chipset SDK模块分为两类，在[categorized-libraries.json](./categorized-libraries.json)中通过以下类型来标识：

- chipsetsdk: 芯片组件直接依赖的系统组件模块
- chipsetsdk_indirect: chipsetsdk模块间接依赖的系统组件模块

### 1.5 Passthrough SDK

Passthrough SDK是指允许被应用/系统组件进程直接加载的芯片组件模块集合。

Passthrough SDK集合中的单个模块称之为Passthrough SDK模块。Passthrough SDK模块分为两类，在[categorized-libraries.json](./categorized-libraries.json)中通过以下类型来标识：

- passthrough: 应用或系统组件进程直接依赖的芯片组件模块
- passthrough_indirect: passthrough模块间接依赖的模块

### 1.6 动态库模块的类别标识方式

在OH4.1及早期版本，动态库模块都是在BUILD.gn中通过shlib_type和innerapi_tags来区分，示例如下：

```go
ohos_shared_library(sample_chipsetsdk_module) {
    ...
    shlib_type = "ndk"
    innerapi_tags = [ "platformsdk|platformsdk-indirect|chipsetsdk|chipsetsdk_indirect|passthrough|passthrough_indirect" ]
    ...
}
```

OH5.0开始，对各种类型的动态库进行了集中治理，统一通过[categorized-libraries.json](./categorized-libraries.json)文件进行集中管控，其格式内容如下：

```json
{
  "//base/security/access_token/interfaces/innerkits/accesstoken:libaccesstoken_sdk": {
    "so_file_name": "libaccesstoken_sdk.z.so",
    "categories": [ "chipsetsdk", "platformsdk" ]
  },
  "//foundation/resourceschedule/ffrt:libffrt": {
    "so_file_name": "libffrt.so",
    "categories": [ "chipsetsdk" ]
  },
  "//base/security/access_token/frameworks/common:accesstoken_common_cxx": {
    "so_file_name": "libaccesstoken_common_cxx.z.so",
    "categories": [ "platformsdk-indirect" ]
  }
}
```

每个动态库通过其编译标签唯一确定，categories字段标识其具体类型，so_file_name是动态库的最终文件名。

## 2. 动态库分类规则

### 2.1 安装目录及运行时沙盒隔离规则

分类好的动态库，会根据其类型安装到指定的目录；不同类型的进程运行在不同的沙盒环境下，只能访问与进程类型相匹配的动态库目录。详细范围如下：

| 类型                            | 安装路径                          | 应用进程 | 系统组件进程 | 芯片组件进程 | 说明                      |
| ------------------------------- | --------------------------------- | -------- | ------------ | ------------ | ------------------------- |
| ["ndk*",...]                    | /system/lib{64}/ndk/*             | Y        | Y            | Y            | 所有进程都可以访问NDK库。 |
| ["napi"]                        | /system/lib{64}/module/*          | Y        | Y            | N            | 只有应用进程需要访问。    |
| ["platformsdk*"]                | /system/lib{64}/platformsdk/*     | Y        | Y            | N            |                           |
| ["chipsetsdk*"]                 | /system/lib{64}/chipset-sdk/*     | N        | Y            | Y            |                           |
| ["platformsdk*", "chipsetsdk*"] | /system/lib{64}/chipset-pub-sdk/* | Y        | Y            | Y            |                           |
|                                 | /system/lib{64}                   | N        | Y            | Y            |                           |
|                                 | /chipset/lib{64}                  | N        | N            | Y            |                           |
| ["passthrough*"]                | /chipset/lib{64}/chipsetsdk       | Y        | Y            | Y            |                           |

### 2.2 linker的动态库搜索规则



