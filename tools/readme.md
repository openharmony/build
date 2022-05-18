## 使用product_config_version_convert脚本
  - 在build/tools目录下执行 
 	- python3 product_config_version_convert.py {product_name}.json(productdefine\common\products路径下的json文件名)
## 脚本功能
  - 修改productdefine\common下文件到vendor目录下，并修改文件内容为3.0版本样式
  - Merge_files函数
	- 合并productdefine\common\products与/productdefine/common/device目录下的（{product_name}.json）
	- 把合并内容放进创建的vendor\{product_company}\{product_name}目录下的config.json
  - readjson函数
    - 读取vendor\{product_company}\{product_name}目录下的config.json文件
	- 按照3.0版本进行修改
  - Merge函数
    - 合并字典