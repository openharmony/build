# 使用方法

## 1. get_subsystem_with_component.py

### 功能
获取子系统，部件，部件路径之间关系的脚本。
输出示例：
```json
{
    "arkui": [
        {  "ace_engine_lite": "foundation/arkui/ace_engine_lite"  }, 
        {  "napi": "foundation/arkui/napi"  }, 
        {  "ace_engine": "foundation/arkui/ace_engine" }
    ], 
    "ai": [
        {  "ai_engine": "foundation/ai/engine"  },
        {  "os_account": "base/account/os_account"  }
    ]
}
```

### 使用
`python get_subsystem_with_component.py project_path [-o output_path]`  

其中 `project_path` 为要分析的工程路径，为必选选项，
`-o output_path` 指定 `output_path` 为输出 json 文件所在目录，省略时默认为脚本所在目录。

使用示例：
```shell
python get_subsystem_with_component.py project/path -o out/path
```
执行后会打印输出的 json 文件的路径。
```
Output path: out/path/subsystem_component_path.json
```  
  
## 2. bundle_json_check.py
  
### 功能
检查 bundle.json 文件的准确性。遵循规则为 OpenHarmony 部件构建规范的**规则 2.1 部件描述文件中字段须准确。**  
默认输出 xlsx 文件格式示例: 
|子系统|部件|文件|违反规则|详细|说明|
|---|---|---|---|---|---|
|arkui|ace_engine_lite|founation/arkui/ace_engine_lite/bundle.json|规则2.1 部件描述文件中字段须准确|component:name|no such field.|  

### 使用
```shell
usage: bundle_json_check.py [-h] [--xls | --json] [-P PROJECT | -p PATH [PATH ...]] [-o OUTPUT]
```
`--xlsx 或 --json` 为可选参数。指定输出结果的格式，默认为 xlsx 格式。  
`-P PROJECT 与 -p PATH [PATH ...]` 为二选一的必选参数。其中 `-P`（大写）指定源码工程的根目录，`-p`（小写）指定一个或一组 bundle.json 文件路径。  
`-o` 为可选参数。指定输出文件的路径，默认为当前目录。

### 注意
- 使用 `-p`（小写）时，脚本直接打印 json 格式字符串在控制台（标准输出）。无法指定格式和路径。
- 如果输出的 line （行号）为 0 时，表示没有找到该行。

使用示例:  
```shell
python bundle_json_check.py -P /path/to/project
python bundle_josn_check.py -p a/bundle.json b/bundle.json
```