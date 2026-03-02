# 独立编译<a name="ZH-CN_TOPIC_0000001124588563"></a>

-   [简介](#section1)
-   [机制](#section2)
-   [环境](#section3)
-   [示例](#section4)
-   [参数](#section5)


## 简介<a name="section1"></a>

独立编译是相对全量源码编译的另一个编译方式，在全量源码编译中，需要准备好编译环境、下载全量源码、执行预编译后才能进行编译，独立编译则不依赖全量源码，独立编译只依赖build仓的源码，以及需要进行独立编译的代码仓的源码，所涉及的对其他部件的依赖，则会以二进制包的形式下载下来，编译时直接进行链接


**独立编译时的代码目录结构如下：**  

```
├──.repo                      # 编译构建主目录
├── build                  
├── foundation\graphic\graphic_2d(这里以graphic_2d部件为例)
├── prebuilts                 # 执行独立编译预下载后自动生成
```

**下载的二进制包本地存放路径：** 
```shell
~/.hpm
```

**二进制包远程仓库：** 
```shell
repo.harmonyos.com
```

**二进制包依赖定义：** 
```shell
独立编译依赖的二进制项在bundle.json中component->deps字段中定义
```

## 机制简介<a name="section2"></a>

-   根据依赖配置下载二进制包

-   将external_deps解析成对二进制包的依赖

-   -i 选项的编译入口是在bundle.json的build字段中，除test字段外定义的所有构建目标
  
-   -t 选项的编译入口是build->test字段中定义的构建目标


## 编译环境准备<a name="section3"></a>

**准备开发环境**

https://gitcode.com/openharmony/docs/blob/master/zh-cn/device-dev/quick-start/quickstart-pkg-prepare.md

ubuntu版本至少为22.04

**安装库和工具集**
https://gitcode.com/openharmony/docs/blob/master/zh-cn/device-dev/quick-start/quickstart-pkg-install-package.md


**安装hb工具**
https://gitcode.com/openharmony/docs/blob/master/zh-cn/device-dev/quick-start/quickstart-pkg-install-tool.md

```
若hb工具安装出现问题可尝试如下步骤:
首先需要保证python以及python3均指向大于等于python3.8的版本
删除旧的hb:
rm -rf ~/.local/lib/python{版本号}/site-packages/hb
rm -rf ~/.local/bin/hb
安装修的hb:
python3 -m pip install --default-timeout=300 --user build/hb --index-url https://mirrors.huaweicloud.com/repository/pypi/simple
python3 -m pip install jinja2 --index-url https://mirrors.huaweicloud.com/repository/pypi/simple
配置环境变量:
在~./bashrc添加PATH=~/.local/bin:$PATH
source ~/.bashrc
```


## 独立编译示例<a name="section4"></a>

以syscap_codec部件为例，进行独立编译，执行如下步骤

**初始化repo**
```
mkdir code
cd code 
repo init -u https://gitcode.com/openharmony/manifest.git -b master --no-repo-verify
```

**拉build仓**
```
repo sync -c build
```

**拉编译仓**
```
repo sync -c developtools_syscap_codec
```

**执行独立编译预下载**
```
bash build/prebuilts_config.sh --download-sdk
```

**进行独立编译**
```
hb build syscap_codec -i
```

## 独立编译常用参数<a name="section5"></a>
```
-t                                      ---只编译bundle.json中声明的测试项
-i                                      ---编译bundle.json中声明的除测试项外其他所有项
--build-target                          ---指定构建目标编译，若在bundle.json中声明的，可以直接指定目标名，否则需要指定路径(相对源码根目录的路径或者gn路径)
--skip-download                         ---跳过二进制包下载
--keep-ninja-going                      ---编译报错后继续编译，直至完成
--gn-flags=--export-compile-commands    ---生成compile_command.json文件
其他更多请通过hb help命令查询usage: hb indep_build [option]中的内容
```