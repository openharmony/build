

## 模块依赖分析



### 生成部件依赖



生成步骤：

1. 编译代码生成中间文件，只执行gn阶段，并打开check_deps属性

   ```shell
   ./build.sh --product-name Hi3516DV300 --ccache --gn-args pycache_enable=true --gn-args check_deps=true --build-only-gn 
   ```

2. 运行依赖生成脚本

   ```shell
   # 比如在源码根目录下执行
   build/tools/module_dependence/part_deps.py --deps-files-path out/ohos-arm-release/deps_files
   ```

3. 脚本参数说明

   ```
   --deps-files-path  # 必选  模块依赖数据文件目录，gn执行完成后输出在out/ohos-arm-release/deps_files目录下，如果不在源码目录执行，需要配置到正确的路径。
   --graph            # 可选  生成部件依赖图。使用该选项，需要安装对应的库
   ```

4. 关于依赖图的生成

   如果需要生成部件依赖图，使用--graph参数指定；

   本地机器需要安装依赖库：graphviz

   ```
   # 使用pip安装python3的依赖库
   pip3 install graphviz
   
   # 如果pip3没有安装，请先安装pip3
   sudo apt install python3-pip
   
   # 安装graphviz
   sudo apt install graphviz
   ```

5. 输出

   脚本运行后会在 `--deps-files-path` 指定的deps_files的同级目录下，创建parts_deps_info文件夹输出结果数据。
   parts_deps_info/
   ```
   parts_deps_info/all_deps_data.json       # 生成的模块依赖信息
   parts_deps_info/part_deps_info.json      # 生成的部件依赖
   parts_deps_info/part-deps-grahp.gv.pdf   # 生成的部件依赖图，只有指定--graph参数时才生成
   ```

   
### 生成模块依赖



生成步骤：

1. 编译代码生成中间文件，只执行gn阶段，并打开check_deps属性

   ```shell
   ./build.sh --product-name Hi3516DV300 --ccache --gn-args pycache_enable=true --gn-args check_deps=true --build-only-gn 
   ```

2. 运行依赖生成脚本

   ```shell
   # 比如在源码根目录下执行
   build/tools/module_dependence/module_deps.py --deps-files-path out/ohos-arm-release/deps_files
   ```

3. 脚本参数说明

   ```
   --deps-files-path  # 必选  模块依赖数据文件目录，gn执行完成后输出在out/ohos-arm-release/deps_files目录下，如果不在源码目录执行，需要配置到正确的路径。
   ```

4. 输出

   脚本运行后会在 `--deps-files-path` 指定的deps_files的同级目录下，创建module_deps_info文件夹输出结果数据。
   ```
   module_deps_info/all_deps_data.json        # 生成的模块依赖信息
   module_deps_info/module_deps_info.json     # 生成的部件依赖
   ```

**注意：**
*工具能力在完善中，使用脚本和步骤会随时变化。*
