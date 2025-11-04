# 预编译工具配置指南
-   [工具下载配置](#section-download-01)
    1. [核心配置说明](#section-download-core-01)
    2. [基础配置示例](#section-download-basic-demo)
    3. [高级配置示例](#section-download-advanced-demo)
-   [处理配置](#advanced-process)
-   [变量处理](#value-search)

## 工具下载配置 <a name="section-download-01"></a>
下载配置用于配置下载和解压参数
### 核心配置项说明 <a name="section-download-core-01"></a>

|参数|描述|
|--|--|
remote_url|远程包下载地址|
unzip_dir|解压目标路径|
unzip_filename|解压后的顶层目录名（用于版本管理和旧文件清理）|

### 基础配置示例 <a name="section-download-basic-demo"></a>
#### 场景1：指定操作系统与CPU架构 <a name="section-download-basic-demo-01"></a>
以 ark_js_prebuilts 工具为例，在 Linux x86_64 环境下的配置如下：
```json
{
    "name": "ark_js_prebuilts",
    "tag": "base",
    "build_type": "src, indep",
    "config": {
        "linux": {
            "x86_64": { 
                "remote_url": "/openharmony/compiler/llvm_prebuilt_libs/ark_js_prebuilts_20230713.tar.gz",
                "unzip_dir": "${code_dir}/prebuilts/ark_tools",
                "unzip_filename": "ark_js_prebuilts"
            }
        }
    }
}
```


#### 场景2：CPU架构无关配置 <a name="section-download-basic-demo-02"></a>
若工具包不依赖CPU架构（如纯脚本工具），可做如下配置：
``` json
{
    "name": "ark_js_prebuilts",
    "tag": "base",
    "build_type": "src, indep",
    "config": {
        "linux": {
            "any": {
                "remote_url": "/openharmony/compiler/llvm_prebuilt_libs/ark_js_prebuilts_20230713.tar.gz",
                "unzip_dir": "${code_dir}/prebuilts/ark_tools",
                "unzip_filename": "ark_js_prebuilts"
            }
            
        }
    }
}
```


#### 场景3：平台无关配置 <a name="section-download-basic-demo-03"></a>
若工具包和平台无关，配置进一步简化：
```json
{
    "name": "ark_js_prebuilts",
    "tag": "base",
    "build_type": "src, indep",
    "config": {
        "any":{
            "any": {
                "remote_url": "/openharmony/compiler/llvm_prebuilt_libs/ark_js_prebuilts_20230713.tar.gz",
                "unzip_dir": "${code_dir}/prebuilts/ark_tools",
                "unzip_filename": "ark_js_prebuilts"
            }
        }
    }
}
```

### 高级配置场景 <a name="section-download-advanced-demo"></a>
#### 多版本并行下载（以LLVM为例）<a name="section-download-advanced-demo-01"></a>
若需在同一平台下安装多个版本，配置项改为列表形式：
```json
{
    "name": "llvm",
    "tag": "base",
    "build_type": "src, indep",
    "config": {
        "linux": {
            "x86_64": [
                {
                    "remote_url": "/openharmony/compiler/clang/15.0.4-3cec00/ohos_arm64/clang_ohos-arm64-3cec00-20250320.tar.gz",
                    "unzip_dir": "${code_dir}/prebuilts/clang/ohos/ohos-arm64",
                    "unzip_filename": "llvm",
                },
                {
                    "remote_url": "/openharmony/compiler/clang/15.0.4-3cec00/windows/clang_windows-x86_64-3cec00-20250320.tar.gz",
                    "unzip_dir": "${code_dir}/prebuilts/clang/ohos/windows-x86_64",
                    "unzip_filename": "llvm",
                },
                {
                    "remote_url": "/openharmony/compiler/clang/15.0.4-3cec00/linux/clang_linux-x86_64-3cec00-20250320.tar.gz",
                    "unzip_dir": "${code_dir}/prebuilts/clang/ohos/linux-x86_64",
                    "unzip_filename": "llvm",
                }
            ]
        }
    }
}
```



#### 使用公共配置 <a name="section-common-var"></a>
当配置中存在值相同的配置项时，可提取公共配置避免冗余：<br>
**原始冗余配置**
```json
{
    "name": "ark_js_prebuilts",
    "tag": "base",
    "build_type": "src, indep",
    "config": {
        "linux": {
            "x86_64": {
                "remote_url": "/openharmony/compiler/llvm_prebuilt_libs/ark_js_prebuilts_20230713.tar.gz",
                "unzip_dir": "${code_dir}/prebuilts/ark_tools",
                "unzip_filename": "ark_js_prebuilts"
            }
        },
        "darwin": {
            "x86_64": {
                "remote_url": "/openharmony/compiler/llvm_prebuilt_libs/ark_js_prebuilts_darwin_x64_20230209.tar.gz",
                "unzip_dir": "${code_dir}/prebuilts/ark_tools",
                "unzip_filename": "ark_js_prebuilts"
            }
        }
    }
}
```

**优化后配置**
```json
{
    "name": "ark_js_prebuilts",
    "tag": "base",
    "build_type": "src, indep",
    "unzip_dir": "${code_dir}/prebuilts/ark_tools",
    "unzip_filename": "ark_js_prebuilts",
    "config": {
        "linux": {
            "x86_64": {
                "remote_url": "/openharmony/compiler/llvm_prebuilt_libs/ark_js_prebuilts_20230713.tar.gz"
            }
        },
        "darwin": {
            "x86_64": {
                "remote_url": "/openharmony/compiler/llvm_prebuilt_libs/ark_js_prebuilts_darwin_x64_20230209.tar.gz"
                
            }
        }
    }
}
```

#### 配置继承规则 <a name="section-inherit"></a>
- 工具配置会继承全局配置
- 平台配置会继承工具配置
- 存在相同配置项时，内部配置会覆盖继承的配置
#### 说明
- 全局配置在工具配置的外层定义
- 平台配置在config里面定义
- 除config和handle，都属于工具配置

## 处理配置 <a name="advanced-process"></a>
部分工具在下载解压完成后需要进行额外的处理，这些处理操作可以在handle中定义，handle会在下载解压完成后执行，若没有下载解压操作，handle则会直接执行。handle是一个列表，其中的每一项都代表一个操作
### handle配置特点 <a name="advanced-process-handle-feature"></a>
- 顺序执行：操作项按配置顺序依次执行
- 使用变量：操作中可使用外部变量
- 灵活控制：平台配置中可通过指定handle_index，定制操作序列
- 容错机制：若操作中的变量解析失败，跳过当前操作

### 公共操作列表 <a name="advanced-process-common-operate"></a>

|操作类型|参数|用途|
|-|-|-|
|symlink| src: 链接源<br>dest: 目的链接地址| 生成符号链接
|copy	| src: 源<br>dest: 目的| 复制文件或文件夹 |
|remove	| path:要删除的路径, 可以是字符串，也可以是一个列表 | 删除文件或文件夹 |
|move	| src: 源路径<br>dest: 目标路径<br>filetype: 该参数默认不填写，若填写，则只会移动src目录中以filetype为后缀的文件	| 移动文件,若dest是个已存在的目录，则会移动到目录中 |
|shell	| cmd: 命令(列表形式) |执行shell命令

### handle配置示例 <a name="advanced-process-demo"></a>
#### 场景： 解压Node工具后创建符号链接: <a name="advanced-process-demo-01"></a>
```json
{
    "name": "node",
    "tag": "base",
    "build_type": "src, indep",
    "unzip_dir": "${code_dir}/prebuilts/build-tools/common/nodejs",
    "config": {
        "linux": {
            "x86_64": [
                {
                    "remote_url": "/nodejs/v14.21.1/node-v14.21.1-linux-x64.tar.gz",
                    "unzip_filename": "node-v14.21.1-linux-x64",
                    "symlink_src": "${code_dir}/prebuilts/build-tools/common/nodejs/node-v14.21.1-linux-x64"
                }
            ]
        }
    },
    "handle": [
        {
            "type": "symlink",
            "src": "${symlink_src}",
            "dest": "${code_dir}/prebuilts/build-tools/common/nodejs/current"
        }
    ]
}
```


## 变量处理 <a name="value-search"></a>
- 变量只能使用${var_name}的方式指定
- 工具配置可以使用自身内部以及全局配置中的变量
- 平台配置可以使用自身内部、工具以及全局配置中的变量
- handl中的操作项可以使用自身内部、平台、工具以及全局配置中的变量
- 变量解析优先级为：自身内部配置 > 平台配置 > 工具配置 > 全局配置
