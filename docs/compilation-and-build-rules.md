# 编译构建规范
## gn构建规范
### 规则
1. 在声明编译模块时，应使用OpenHarmony提供的高级模板，如ohos_excutable，ohos_shared_library，ohos_static_library等。
2. 在所有编译模块中需要指定**part_name**和**subsystem_name**，都不应使用**output_dir**来指定编译产物的目录，
3. 模块之间建立依赖应避免使用public_deps，因为public_deps会通过依赖传递隐式配置，导致依赖模块引入多余配置而出现编译问题。
    ```
    # This target can include files from "c" but not from
    # "super_secret_implementation_details".
    executable("a") {
      deps = [ ":b" ]
    }

    shared_library("b") {
      deps = [ ":super_secret_implementation_details" ]
      public_deps = [ ":c" ]
    }
    ```
### 建议
1. gn的宏变量定义主要有三种位置选择：
   | 定义位置 | 作用 |
   | --- | --- |
   | BUILDCONFIG.gn | 对于构建系统全局可见，一般定义工具链，cpu架构等变量，使用时不需要导入该文件 |
   | ohos_var.gni | 常规用于OpenHarmony构建多处使用的相关变量，使用变量需要导入该文件 |
   | xxx.gni | 各业务仓自定义文件，用于使用范围较小的相关变量，一般限制于单个代码仓内。使用变量需要导入该文件 |

   以上文件定义均采用下列方式：
   ```
    declare_args() {
      enable_test_var = true
    }
   ```
2. gn中声明的代码宏可以通过**defines**或"-D"选项来进行定义，参考如下：
   ```
   config("common") {
    defines = [ "ENABLE_BYTECODE_OPT" ]
    cflags_cc = [ "-DARK_GC_SUPPORT" ]
   }
   ```
3. 声明编译目标或者配置要关注其可见性，使用visibility来对可见范围进行限制。部件内模块若不对外提供接口，应将visibility字段设置为所在部件目录内。三方部件内模块可以将可见范围进一步扩大。visibility的使用有如下几种形式：
   ```
   config("common") {
    visibility = [

    ]
   }

   ohos_shared_library("test_shared_library") {
    visibility = [
      ":*",   # 对当前文件可见
      "//a/b/c/*",   # 通过绝对路径指定范围
      "./a/b/c/*",   # 通过相对路径指定范围
    ]
   }
   ```