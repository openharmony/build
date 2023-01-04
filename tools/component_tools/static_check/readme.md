# OpenHarmony部件编译构建规范指导

## OpenHarmony部件编译构建规范本地检查脚本使用指导

### 介绍

部件编译构建规范本地检查脚本用于检查openharmony编译构建中不规范的问题，详细检查问题见[OpenHarmony部件编译构建规范修改指导](#openharmony部件编译构建规范修改指导)
### 使用方法

```shell
python3 csct.py  [-p path] 
```

#### 示例

若要检查openharmony全量的不规范问题，可以在openharmony根目录使用以下命令。

```shell
python3 build/tools/component_tools/static_check/csct.py
```

若要检查某个目录下的不规范问题，可以在openharmony根目录使用以下命令。

```shell
python3 build/tools/component_tools/static_check/csct.py -p [要检查的目录]

example：
python3 build/tools/component_tools/static_check/csct.py -p base/global
```

## OpenHarmony部件编译构建规范修改指导

关于完整的OpenHarmony部件编译构建规范，请点击
[这里](https://gitee.com/openharmony/docs/blob/master/zh-cn/device-dev/subsystems/subsys-build-component-building-rules.md)
### 规则2.1 部件描述文件中字段须准确。

- name

  类型：string。部件的HPM（鸿蒙包管理器）包名称，必填。命名规则：@{organization}/{component_name}。“component_name“为部件的名称，须满足规则1.1。


- version

  类型：string。部件版本号，必填，命名和升级跟随OpenHarmony版本号。

- destPath

  类型：string。部件源码的根目录，必填。部件的根目录须独立唯一，不允许存在多个根目录。


- component:name

  类型：string。部件名，必填。须满足规则1.1。


- component:subsystem

  类型：string。部件归属的子系统名称，必填，子系统名为小写英文字母组合、不使用下划线。


- component:syscap

  类型：string list。可选。命名规则：大驼峰，“SystemCapability.Subsystem.部件能力.子能力（可选）”，如SystemCapability.Media.Camera ,  SystemCapability.Media.Camera.Front。

- component:features

  类型：string list，部件可配置的特性，可选，命名须满足规则1.2。


- component:adapted_system_type

  类型：string list。部件适用的系统类型，必填，值为“mini、small和standard"，可同时支持多种。


- component:rom

  类型：string。ROM基线值，必填，单位默认为KByte。


- component:ram

  类型：string。RAM基线值，必填，单位默认为KByte。


- component:deps

  类型：string list。deps对象描述了部件的外部依赖，必填，包括其他部件和三方开源软件，应该与部件编译脚本中依赖一致。


  #### 修改指导：

  以一个错误 bundle.json 为例：

  ```python
  {
    "name": "sensor_lite",      # 部件的HPM名，规则为 @{organization}/{component_name}
    "description": "Sensor services",	
    "version": "3.1",           # 版本号，版本号与OpenHarmony版本号一致
    "license": "MIT",
    "publishAs": "code-segment",
    "segment": {
        "destPath": ""          # 部件源码根目录，不能为空
    },		
    "scripts": {},
    "component": {
        "name": "SensorLite",   # 部件名应该与 HPM 名的 component_name 部分一样，并且为内核命名风格。
        "subsystem": "Sensors", # 必须全小写字母，且不含有下划线
        "syscap": [
          "SystemCapability.Sensors.sensor.lite" # 必须大驼峰风格
        ],
        "features": [],
        "adapted_system_type": [ "liteos_m" ],	 # 轻量(mini)小型(small)和标准(standard)，可以是多个
        "rom": "",             # 部件ROM值, 不能为空
        "ram": "",             # 部件RAM估值, 不能为空     
        "deps": {                      
          "components": [
            "samgr_lite",
            "ipc_lite"
          ],
      }         
        "build": {
            "sub_component": [
                "//base/sensors/sensor_lite/services:sensor_service",
            ],
            "inner_kits": [],
            "test": []
        }
    }
  }
  ```

  根据上面的错误标记，应该修改为如下：
  ```python
  {
    "name": "@ohos/sensor_lite",     # 添加前缀 '@ohos/'
    "description": "Sensor services",	
    "version": "3.2",                # 目前 OpenHarmony 版本号为 3.2
    "license": "MIT",
    "publishAs": "code-segment",
    "segment": {
        "destPath": "base/sensors/sensor_lite"  # 部件源码根目录(相对路径)
    },		
    "scripts": {},
    "component": {
        "name": "sensor_lite",      # 前后统一，内核命名风格
        "subsystem": "sensors",     # 全小写字母组合
        "syscap": [
          "SystemCapability.Sensors.Sensor.Lite" # 大驼峰风格
        ],
        "features": [],
        "adapted_system_type": [ "small" ],	 # 该部件仅支持小型（small）系统
        "rom": "92KB",             # 根据实际情况填写
        "ram": "~200KB",           # 根据实际情况估算，'~'表示大概
        "deps": {                      
          "components": [
            "samgr_lite",
            "ipc_lite"
          ],
      }         
        "build": {
            "sub_component": [
                "//base/sensors/sensor_lite/services:sensor_service",
            ],
            "inner_kits": [],
            "test": []
        }
    }
  }
  ```


### 规则3.1 部件编译脚本中只允许引用本部件的路径，禁止引用其他部件的绝对或相对路径。

部件间的依赖都必须使用“externel_deps”，部件编译目标的变量sources、include_dirs、configs、public_configs、deps、public_deps引用其他部件的相对和绝对路径属于非法引入依赖：

- sources

  sources只允许包含本部件的源码，包含其他部件的源码破坏了部件源码目录独立的原则。

- include_dirs

  include_dirs只允许引用本部件的头文件搜索路径，编译单元对其他部件的接口的依赖都通过externel_deps自动导入。

- configs

  configs只允许引用本部件的配置路径，引用其他部件的configs可能会引入接口依赖。

- pulic_configs

  同configs，引用其他部件的configs可能会引入接口依赖。

- deps

  deps只允许用于部件内模块的依赖，直接引用其他部件的模块可能会导致依赖其他部件的内部模块和接口。

  例：

  base/foos/foo_a/BUILD.gn

  ```c
  deps = [ "//base/foo/foo_b:b" ] // Bad, 绝对路径依赖其他部件
  deps = [ "../../foo_b:b" ] // Bad, 相对路径依赖其他部件
  ```

  例外：对三方开源软件和build目录下的引用除外。

- public_deps

  同deps，public_deps只允许用于部件内模块的依赖。
  


#### 修改建议：

1.若绝对路径引用的是本部件的内容，则应改为使用相对路径。

例如foundation/systemabilitymgr/samgr/services/samgr/native/BUILD.gn中

```c
config("distributed_store_config") {
  visibility = [ ":*" ]
  include_dirs =
      [ "//foundation/systemabilitymgr/samgr/services/samgr/native/include" ]
}
```

以上include_dirs中的引用自己的内容使用了绝对路径是错误的，建议修改为：

```c
    [ "include" ]
```

2.若绝对引用的是其他部件的内用，则应改为external_deps的方式。

例如foundation/bundlemanager/bundle_framework_lite/services/bundlemgr_lite/tools/BUILD.gn中

```c
  deps = [
    "${appexecfwk_lite_path}/frameworks/bundle_lite:bundle",
    "//base/hiviewdfx/hilog_lite/frameworks/featured:hilog_shared",
    "//base/security/permission_lite/services/pms_client:pms_client",
    "//base/startup/init/interfaces/innerkits:libbegetutil",
    "//build/lite/config/component/cJSON:cjson_shared",
    "//foundation/communication/ipc/interfaces/innerkits/c/ipc:ipc_single",
    "//foundation/systemabilitymgr/samgr_lite/samgr:samgr",
  ]
```

以上deps中的引用其他部件的内容使用了绝对路径是错误的（build仓忽略），建议修改为：

```c
  deps = [
    "${appexecfwk_lite_path}/frameworks/bundle_lite:bundle",
    "//build/lite/config/component/cJSON:cjson_shared",
  ]

  external_deps = [
      "hilog_lite:hilog_shared",
      "permission_lite:pms_client",
      "init:libbegetutil",
      "ipc:ipc_single",
      "samgr_lite:samgr",
    ]
```

### 规则3.2 部件编译目标必须指定部件和子系统名。

部件的编译单元ohos_shared_library、ohos_static_library、ohos_executable_library、ohos_source_set都必须指定“part_name”和“subsystem_name”。


#### 修改建议：

例如base/account/os_account/services/accountmgr/src/appaccount/BUILD.gn中

```c
ohos_shared_library("app_account_service_core") {
  sources = [
    "app_account_event_proxy.cpp",
    "app_account_stub.cpp",
  ]

  defines = [
    "ACCOUNT_LOG_TAG = \"AppAccountService\"",
    "LOG_DOMAIN = 0xD001B00",
  ]

  configs = [
    ":app_account_service_core_config",
    "${account_coverage_config_path}:coverage_flags",
  ]

  public_configs = [ ":app_account_service_core_public_config" ]

  deps = [ "${app_account_innerkits_native_path}:app_account_innerkits" ]

  external_deps = [
    "ability_base:want",
    "c_utils:utils",
    "hiviewdfx_hilog_native:libhilog",
    "ipc:ipc_core",
  ]

  subsystem_name = "account" //原本没有，应该添加的内容！
  part_name = "os_account"
}
```


### 规则4.1 部件编译脚本中禁止使用产品名称变量。

部件是通用的系统能力，与特定产品无关。编译脚本中使用产品名称，将导致部件功能与产品绑定，不具备通用性。部件不同产品形态上的差异应抽象为特性或者运行时的插件。

**例外：** vendor和device目录下三方厂商部件的编译脚本例外。


#### 修改建议：
例如：

```c
    if(product_name =="rk3568"){  //Bad,根据产品形态定义宏
        defines += ["NON_SEPERATE_P2P]
    }
```

以上编译脚本中存在产品名称"rk3568"是不合理的，建议修改为：

```c
    declares_args(){ //将产品差异抽象为部件特性开关
        wifi_non_seperate_p2p = true
    }

    if(wifi_non_seperate_p2p){ // 根据开关特性定义宏，而不是跟固定产品绑定
        defines += ["NON_SEPERATE_P2P]
    }
```

## OpenHarmony部件编译构建规范白名单仓库

OpenHarmony部件编译构建规范存在白名单仓库（仅对部件编译脚本生效（.gn .gni文件）），这些源码仓或代码目录不在检查范围内，具体如下：

1. [manifest](https://gitee.com/openharmony/manifest/blob/master/ohos/ohos.xml) 文件中group字段标记为 ohos:mini 或 ohos:small的源码仓或代码目录。
2. device、vendor开头的三方厂商源码仓。
3. build仓。
4. 全部third_party仓。

## OpenHarmony部件编译构建规范门禁拦截逃生通道

OpenHarmony部件编译构建规范门禁拦截结果会在format check中体现出来，请按照指导修改，如有特殊情况需要屏蔽，须特定人员评论component-static-check-ignore屏蔽。
