# HB构建工具使用指导<a name="ZH-CN_TOPIC_0000001130006475"></a>

-   [简介](#section11660541593)
-   [说明](#section1312121216216)
    -   [使用说明](#section129654513264)

-   [相关仓](#section1371113476307)

## 简介<a name="section11660541593"></a>

在开发编译构建前，应了解如下基本概念：

-   hb

    一款基于python开发的编译构建脚本工具，提供了编译环境检查与依赖安装、图形化界面编译引导、编译目标依赖检查、编译产物清理等特性。

-   gn

    Generate ninja的缩写，一种元构建系统，用于产生ninja文件。

-   ninja

    ninja是一个专注于速度的小型构建系统。

-   部件

    可复用的软件单元，它可包含源码、配置文件、资源文件和编译脚本等。


使用hb启动编译构建任务流程如下：

1.  hb set: 设置源码目录和要编译的产品。
2.  hb build: 编译产品、开发板或者组件。解决方案编译实现如下：
    -   读取开发板配置：主要包括开发板使用的编译工具链、编译链接命令和选项等。
    -   调用gn: 调用gn gen命令，读取产品配置\(主要包括开发板、内核、选择的组件等\)生成解决方案out目录和ninja文件。
    -   调用ninja：调用ninja -C out/company/product启动编译。
    -   系统镜像打包：将组件编译产物打包，制作文件系统镜像。


## 说明<a name="section1312121216216"></a>

### 使用说明<a name="section129654513264"></a>

1.  **前提条件**
    -   Linux服务器，Ubuntu16.04及以上64位系统版本。
    -   Python 3.7.4及以上。
    -   源码下载成功。

2.  **安装hb**
    -   在源码根目录下执行：

        ```
        python3 -m pip install --user build/hb
        ```

    -   执行hb help有相关帮助信息，有打印信息即表示安装成功，当前hb 主要提供了hb set，hb build，hb tool，hb env，hb clean五个选项。


    -   卸载方法：

        ```
        python3 -m pip uninstall ohos-build
        ```


3.  **编译命令**
    1.  **hb set**

        ```
        hb set -h
        usage: hb set [option]
     
        options:
            -h, --help              show this help message and exit
            -p PRODUCT_NAME, --product-name PRODUCT_NAME
                                    Default:''. Help:Build a specified product. You could use this option like this: 1.'hb set --product-name rk3568@hihope' 2.'hb set'[graphical ui]
            --all                   Default:False. Help:Use a graphical interface to customize most compile-time parameters
        ```

        -   hb set 后无参数，进入默认设置流程
        -   hb set -root \[ROOT\_PATH\] 直接设置代码根目录
        -   hb set -p --product 设置要编译的产品
        -   hb set --all 选择自定义的产品配置，如产品芯片架构、release/debug版本、日志级别等

    2.  **hb env**

        提供编译环境依赖检查和安装

        ```
        hb env -h
        usage: hb env [option]
     
        options:
            -h, --help              show this help message and exit
            --check                 Default:True. Help:check that the current running environment contains all dependencies
            --install               Default:False. Help:install all dependent software for compiling  products
        ```

    3.  **hb build**

        ```
        hb build -h
        usage: hb build [option]
        options:
            -h, --help              show this help message and exit
            -p PRODUCT_NAME, --product-name PRODUCT_NAME
                                    Default:''. Help:Build a specified product. If you have executed 'hb set', execute 'hb build' directly. Or you could use this option like this: 1.'hb build --product-name rk3568@hihope' 2.'hb build --product-name rk3568'
            --target-cpu {arm,arm64,x86_64,x64}
                                    Default:''. Help:Specifies the desired cpu architecture for the build, each may support different cpu architectures, run 'hb set --all' to list product all supported cpu
                                    architectures
            --rename-last-log {True,False,true,false}
                                    Default:True. Help:You can use it to decide whether to keep the last build log
            --ccache                Default:True. Help:Enable ccache, this option could improve compilation speed. --stat-ccache can summary the cache data
            --enable-pycache {True,False,true,false}
                                    Default:False. Help:Enable pycache, This option can improve the execution speed of python files
            --jobs JOBS             Deprecated, please do not use this option
            --disable-part-of-post-build [DISABLE_PART_OF_POST_BUILD ...]
                                    Deprecated, please do not use this option
            --build-target [BUILD_TARGET ...]
                                    Default:[]. Help:You use this option to specify a single compilation target, and use 'hb tool --ls' to list all build target
            --ninja-args [NINJA_ARGS ...]
                                    Default:[]. Help:You can use it to pass parameters for the ninja phase, but you need to follow the specified command format. eg. --ninja-args=-dkeeprsp
            -f, --full-compilation
                                    Default:[]. Help:You can use it to start full code compilation. The default compilation target is images. Use this option to add 'make_all' and 'make_test' to the build
                                    process.
            --strict-mode {True,False,true,false}
                                    Default:False. Help:Check all produce of each phase to early terminates a potentially problematic compilation.
            --scalable-build {True,False,true,false}
                                    Default:False. Help:Select whether to read information from parts.json generate by preload
            --build-example {True,False,true,false}
                                    Default:False. Help:Select whether to read information from subsystem_config_example.json
            --build-platform-name BUILD_PLATFORM_NAME
                                    Default:'phone'. Help:Name of the compilation platform. The current optional value is 'phone'
            --build-xts {True,False,true,false}
                                    Default:False. Help:Select whether to load the components included in the subsystem xts
            --ignore-api-check [IGNORE_API_CHECK ...]
                                    Default:[]. Help:Skip the check of some subsystems
            --load-test-config {True,False,true,false}
                                    Default:True. Help:Select whether to load the test field in bundle.json, that is, whether to call the test case
            --build-type {release,debug}
                                    Default:'release'. Help:Specify compile release or debug version
            --log-level {info,debug}
                                    Default:'INFO'. Help:Specify the log level during compilation. you can select two levels: debug, info. In debug mode, it show all command lines while building, including
                                    cxx, link, solink, etc.
            --export-para [EXPORT_PARA ...]
                                    Deprecated, please do not use this option
            --test [TEST ...]     Default:[]. Help:You can use it to choose test type. eg. --test xts
            --gn-args [GN_ARGS ...]
                                    Default:[]. Help:Specify gn build arguments, you could use this option like this 'hb build --gn-args is_debug=true'
            -c COMPILER, --compiler COMPILER
                                    Deprecated, please do not use this option
            --fast-rebuild          Default:False. Help:You can use it to skip prepare, preloader, gn_gen steps so we can enable it only when there is no change for gn related script
            --keep-ninja-going      Default:False. Help:When you need to debug one specific target, you can use this option to keep ninja going to skip some possible error until 1000000 jobs fail
            --build-only-gn         Default:False. Help:Stop build until gn phase ends
            --build-variant {user,root}
                                    Default:'root'. Help:specifies device operating mode
            --device-type DEVICE_TYPE
                                    Default:'default'. Help:specifies device type
            --disable-package-image
                                    deprecated, please do not use this option
            --archive-image         Default:False. Help:archive image when build product complete
            --rom-size-statistics
                                    Default:False. Help:statistics on the actual rom size for each compiled component
            --stat-ccache           Default:True. Help:summary ccache hitrate, and generate ccache.log in ${HOME}/.ccache dir
            --get-warning-list      Default:True. Help:You can use it to collect the build warning and generate WarningList.txt in output dir
            --generate-ninja-trace {True,False,true,false}
                                    Default:True. Help:Count the duration of each ninja thread and generate the ninja trace file(build.trace.gz)
            --compute-overlap-rate
                                    Default:True. Help:Compute overlap rate during the post build
            --clean-args            Default:True. Help:clean all args that generated by this compilation while compilation finished
            --deps-guard            Default:True. Help:simplify code, remove concise dependency analysis, and speed up rule checking
        
        ```

        -   hb build后无参数，会按照设置好的代码路径、产品进行编译，编译选项使用与之前保持一致。
        -   hb build component：基于设置好的产品对应的单板、内核，单独编译组件（e.g.：hb build kv\_store\)。
        -   hb build component_test: 基于设置好的产品对应的单板、内核，单独编译组件的测试用例。
        -   hb build -p PRODUCT：免set编译产品，该命令可以跳过set步骤，直接编译产品。
        -   在device/device\_company/board下单独执行hb build会进入内核选择界面，选择完成后会根据当前路径的单板、选择的内核编译出仅包含内核、驱动的镜像。
        -   hb build在部件目录下执行，会检测当前目录下是否存在bundle.json，如果存在，则会将当前部件作为编译目标单独编译，而无须切换至源码根目录下执行。

    4.  **hb clean**

        清除out目录对应产品的编译产物，仅剩下args.gn、build.log。清除指定路径可输入路径参数：hb clean xxx/out/xxx，否则将清除hb set的产品对应out路径

        ```
        hb clean -h
        usage: hb clean [option]
     
        options:
            -h, --help              show this help message and exit
            --clean-all             Default:False. Help:clean all producer
            --clean-args            Default:True. Help:clean all args that generated by last compilation
            --clean-out-product     Default:False. Help:clean out/{product} directory that generated by last compilation
            --clean-ccache          Default:False. Help:clean .ccache directory which is in OHOS root
        ```
    
    5.  **hb tool**
        
        该选项可以用于：
        1. 查看所有构建目标；
        2. .gn文件格式化；
        3. 查看构建目标之间的依赖关系路径；
        4. gn构建文件清理。
        ```
        hb tool -h
        usage: hb tool [option]
        
        options:
        -h, --help                  show this help message and exit
        --ls [LS ...]               Default:[]. Help:Lists all targets matching the given pattern for the given build directory. You could use this option like this: 1.'hb tool --ls <out_dir> [<label_pattern>]
                                [<options>]'
        --desc [DESC ...]           Default:[]. Help:Displays information about a given target or config. You could use this option like this: 1.'hb tool --desc <out_dir> <component_module> [<what to show>]
                                [<options>]'
        --path [PATH ...]           Default:[]. Help:Finds paths of dependencies between two targets. You could use this option like this: 1.'hb tool --path <out_dir> <component1_module1> <component2_module2>
                                [<options>]'
        --refs [REFS ...]           Default:[]. Help:Finds reverse dependencies (which targets reference something). You could use this option like this: 1.'hb tool --refs <out_dir> [<component_module>|<file>]
                                [<options>]'
        --format [FORMAT ...]
                                    Default:[]. Help:Formats .gn file to a standard format. You could use this option like this: 1.'hb tool --format /abspath/some/BUILD.gn [<options>]'
        --clean CLEAN               Default:[]. Help:Deletes the contents of the output directory except for args.gn. You could use this option like this: 1.'hb tool --clean <out_dir>'
        ```


## 相关仓<a name="section1371113476307"></a>
**[编译构建子系统](https://gitee.com/openharmony/docs/blob/master/zh-cn/readme/编译构建子系统.md)**
