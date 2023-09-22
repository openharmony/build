# cflags系列参数使用指导

## cflags系列参数列表
| 支持的参数    | 说明                      |
|----------|-------------------------|
| cflags   | 用于指定工具链编译参数，对c、c++源码均生效 |
| cflags_c | 用于指定工具链编译参数，仅c源码均生效 |
| cflags_cc | 用于指定工具链编译参数，仅c++源码均生效 |

## 支持使用cflags系列参数的模板
| 支持cflags系列参数的模板 |
|---------------------|
| ohos_executable     |
| ohos_shared_library |
| ohos_static_library |
| ohos_source_set     |


## 编译参数覆盖规则
编译参数按配置的先后顺序，后配置的编译参数会覆盖先配置的编译参数

### cflags与cflags_c、cflags_cc
使用cflags_c、cflags_cc配置的编译参数，默认添加到cflags配置的编译参数之后，因此，使用cflags_c、cflags_cc配置的编译参数会覆盖使用cflags配置的编译参数，示例如下：
```
ohos_shared_library("example") {
  ...
  cflags = [ "-fxxx" ]
  cflags_cc = [ "-fno-xxx" ]    # -fno-xxx会覆盖-fxxx，使-fxxx失效
  ...
}
```

### 编译框架与各业务模块
>  **说明：以cflags为例，cflags_c、cflags_cc规则同cflags**   

OpenHarmony编译框架默认全局配置的编译参数与各业务模块自定义的编译参数之间的覆盖规则：
- 若业务模块自定义的cflags配置在模板中，该编译参数会被编译框架的默认编译参数覆盖，示例如下：
```
ohos_shared_library("example") {
  ...
  cflags = [ "-fxxx" ]
  ...
}
```

- 若业务模块自定义的cflags配置在configs中，该编译参数会覆盖编译框架的默认参数，示例如下：
```
config("example_config") {
  cflags = [ "-fxxx" ]
}
        
ohos_shared_library("example") {
  configs = [ ":example_config" ]
}
```

## 如何覆盖编译框架默认编译参数
- 若要覆盖编译框架默认配置的cflags参数，参考[编译参数覆盖规则](#编译参数覆盖规则)：
    1. 可以直接使用cflags_c、cflags_cc进行覆盖
    2. 可以使用configs + cflags进行覆盖
- 若要覆盖编译框架默认配置的cflags_c、cflags_cc参数，参考[编译参数覆盖规则](#编译参数覆盖规则)：
    1. 可以使用configs + cflags_c、cflags_cc进行覆盖

## 如何查看添加的编译参数
以rk3568编译为例，在`out/rk3568/obj`目录下，查找对应编译目标生成的`.ninja`文件，如编译目标example会生成example.ninja，在example.ninja中可以查看配置的编译参数