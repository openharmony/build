## 编译构建框架简介
编译构建框架以gn+ninja作为基础构建系统，针对产品需要和部件化功能，在gn阶段前增加了preloader和loader的预加载过程。

1. preloader: 产品信息预加载。根据编译产品名称，加载对应的配置文件(config.json)并解析,将解析结果以文本方式输出到指定目录下。
2. loader：子系统、部件和模块信息加载。以编译产品名称和preloader的输出作为输入，加载对应的subsystem、component、module/part等配置信息，以文本文件方式输出结果文件和gn的编译任务。
3. gn: gn是一种编译构建工具，用于产生编译目标之间的图状编译依赖。在编译流程中，编译文件生成阶段负责构建参数赋值，执行gn gen编译命令，产生的build.ninja文件可以类比与makefile文件。
4. ninja：ninja是一种接近汇编级的编译构建工具。语法规则简单，构建速度快。在编译流程中，根据编译规则完成对所有编译目标的编译过程。


## 新增编译选项
当前的编译参数通过统一的文本文件管理，保证参数功能独立，并一一映射对应的参数实现函数。
在编译过程中，为了明确参数具体的作用时间，根据编译的preloader，loader，gn，ninja四个基础过程，人为划分了9个编译阶段。分别为：
    ```

    PRE_BUILD                   # 编译预处理相关参数，如--full-compilation，--log-level

    PRE_LOAD                    # preloader前置设置参数

    LOAD                        # loader前置设置参数，如--scalable-build，--build-xts

    PRE_TARGET_GENERATE         # gn前置设置参数，如--gn-args

    TARGET_GENERATE             # gn阶段参数

    POST_TARGET_GENERATE        # gn后置设置参数

    PRE_TARGET_COMPILATION      # ninja前置设置参数，如--ninja-arg
    
    TARGET_COMPILATION          # ninja阶段参数

    POST_TARGET_COMPILATION     # ninja后置设置参数，如--generate-ninja-trace

    POST_BUILD                  # 编译后处理参数，如--clean-args
    ```

为编译框架添加一个编译选项主要分为两步：

1. 在参数管理的json文件中对参数进行注册
2. 针对参数的实际使能方式为参数添加参数实现函数。

## 示例
### 新增一个--ccache选项，默认为false，用于调用ccache编译缓存，加快编译速度。
1. 参数注册：
该参数在编译前开启，在build/hb/resources/args/default/buildargs.json中进行注册，文件添加以下配置：
```
    "ccache": {
    "arg_name": "--ccache",
    "argDefault": false,
    "arg_help": "Default:True. Help:Enable ccache, this option could improve compilation speed. --stat-ccache can summary the cache data",
    "arg_phase": "prebuild",
    "arg_type": "gate",
    "arg_attribute": {},
    "resolve_function": "resolve_ccache",
    "testFunction": "testCCache"
  },
```

2. 参数实现：
在build/hb/resolver/build_args_resolver.py中添加相应的实现函数(代码仅为简单示例)：
```
    @staticmethod
    def resolve_ccache(target_arg: Arg, build_module: BuildModuleInterface):
        """resolve '--ccache' arg
        :param target_arg: arg object which is used to get arg value.
        :param build_module [maybe unused]: build module object which is used to get other services.
        :phase: prebuild.
        """
        if target_arg.arg_value:
            config = Config()
            cmd = ['ccache', '-M', ccache_max_size]
            SystemUtil.exec_command(cmd, log_path=config.log_path)
```

3. 参数使用：在编译命令中添加--ccache即可通过在指定编译阶段调用resolve_ccache()实现参数使能。


## 注意事项
1. 为gn传递专用变量，请勿注册参数。
例如需要增加一个gn变量为enable_cxx,只需要在build/ohos_var.gni中通过declare声明:
```
declare_args() {
  enable_cxx = true
}
```
并在编译命令中添加下面命令即可完成使能。
```
--gn-args enable_cxx=false
```


2. 为ninja传递编译命令，请勿注册参数。
例如需要在ninja编译命令中传递-v参数，在编译命令中添加下面命令即可完成使能。
```
--ninja-args=-v
```
