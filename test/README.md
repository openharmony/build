# 测试框架开发指导文档

## 整体目录结构

测试框架所在路径为root_path/build/test目录下（root_path为项目根路径）

## 目录介绍

**example**

build_example.json 配置文件

conftest.py pytest测试框架生成html配置文件，必须跟用例文件同路径

mylogger.py 框架日志配置文件

performance_test.py 性能测试脚本，使用python3 performance_test.py启动

test_build_option.py 构建参数测试脚本，使用pytest命令启动

test_gn_template.py 构建模板测试脚本，使用pytest命令启动

**script**

start_env.sh 框架运行预安装模块文件

start_ex.sh 流水线测试脚本启动文件

**test_example_template**

include .h文件源码

src .cpp文件源码

others 其余均为gn测试用例

## 框架介绍

### 预安装

测试用例脚本启动前，先调用start_env.sh完成框架运行所需模块

### 启动

start_ex.sh option 只执行构建选项测试用例

start_ex.sh template 只执行构建模板测试用例

start_ex.sh performance 只执行性能测试

start_ex.sh all  先执行构建选项测试用例，再执行性能测试，其次再执行构建模板测试用例【顺序不能变】


生成的报告对应在path_to_ohos_root/out/test_report目录下

### 附录

**pytest命令各参数介绍**

pytest -vs --html option_report_path  option_script_path

-vs:生成详细报告

--html option_report_path:在option_report_path路径下生成html文件，其中包括asset目录和对应的html文件，注意：asset和html文件必须在同路径

option_script_path:pytest要执行的测试用例文件








