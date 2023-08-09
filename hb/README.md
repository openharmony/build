# HB Build Tool Usage Guide<a name="ZH-CN_TOPIC_0000001130006475"></a>

-   [Introduction](#section11660541593)
-   [Usage](#section1312121216216)
    -   [Usage Guidelines](#section129654513264)

-   [Repositories Involved](#section1371113476307)

## Introduction<a name="section11660541593"></a>

Before compiling and building, you should understand the following basic concepts:

-   hb

    A compilation and build script tool developed based on python, which provides features such as compilation environment check and dependency installation, graphical interface compilation guidance, compilation target dependency check, and compilation product cleaning.

-   gn

    Gn is the abbreviation of Generate ninja, a meta-building system used to generate ninja files.

-   ninja

    Ninja is a small build system focused on speed.

-   Component

    Reusable software unit, which can include source code, configuration file, resource file, compilation script, etc.


Use hb to start the compilation and construction task flow as follows:

1.  **hb set**: Set the OpenHarmony source code directory and the product to build.
2.  **hb build**: Build the product, development board, or component. The process to build the solution is as follows:
    -   **Reading configuration**: Read the development board configuration, which covers the toolchain, linking commands, and build options.
    -   **Running gn**: Run the  **gn gen**  command to read the product configuration \(related to the development board, kernel, and system components\) and generate the  **out**  directory and  **ninja**  files for the solution.
    -   **Running Ninja**: Run  **ninja -C out/company/product**  to start build.
    -   **Packaging**: Package the build result to create a file system image.


## Usage<a name="section1312121216216"></a>

### Usage Guidelines<a name="section129654513264"></a>

1.  **Prerequisites**
    -   Server and OS version: Linux server running 64-bit Ubuntu 16.04 or later
    -   Python version: 3.7.4 or later
    -   Repository: **build** source code

2.  **Installing hb**
    -   Run the following command in the root directory of the source code:

        ```
        python3 -m pip install --user build/hb
        ```

    -   Run the  **hb help**  command. If some help information is displayed, the installation is successful. Currently, hb mainly provides five options: hb set, hb build, hb tool, hb env, and hb clean.


    -   uninstall：

        ```
        python3 -m pip uninstall ohos-build
        ```


3.  **Build Commands**
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

        -   If you run  **hb set**  with no argument, the default setting process starts.
        -   You can run  **hb set -root** _\[ROOT\_PATH\]_  to set the root directory of the source code.
        -   **hb set -p --product**  is used to set the product to build.
        -   hb set --all Select customized product configurations, such as product chip architecture, release/debug version, log level, etc.

    2.  **hb env**

        Provide compilation environment dependency check and installation

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
            --skip-partlist-check   Default:False. Help:Skip the subsystem and component check in partlist file
        ```

        -   If you run  **hb build**  with no argument, the previously configured code directory, product, and options are used for build.
        -   You can run  **hb build** _\{component\}_  to build product components separately based on the development board and kernel set for the product, for example,  **hb build kv\_store**.
        -   You can run  **hb build** _\{component_test\}_ to build product component tests separately.
        -   You can run  **hb build -p PRODUCT**  to skip the setting step and build the product directly.
        -   You can run  **hb build**  in  **device/device\_company/board**  to select the kernel and start build based on the current development board and the selected kernel to generate an image that contains the kernel and driver only.
        -   When hb build is executed in the component directory, it will detect whether bundle.json exists in the current directory. If it exists, it will compile the current component separately as the compilation target without switching to the source code root directory for execution.

    4.  **hb clean**

        Clear the build result of the product in the  **out**  directory, and leave the  **args.gn**  and  **build.log**  files only. To clear files in a specified directory, add the directory parameter to the command, for example,  **hb clean** _xxx_**/out/**_xxx_.

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

        This option can be used to:
        1. View all construction objectives;
        2. Format .gn file;
        3. View the dependency path between the construction targets;
        4. gn build file cleaning.
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


## Repositories Involved<a name="section1371113476307"></a>
**[build](https://gitee.com/openharmony/docs/blob/master/zh-cn/readme/编译构建子系统.md)**
