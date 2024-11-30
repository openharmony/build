## OpenHarmony开源软件Notice收集策略说明



### 背景

### 收集目标

只收集打包到镜像里面的模块对应的License；不打包的都不收集，比如构建过程使用的工具（如clang/python/ninja等）。

静态库本身是不会被打包的，一般是作为动态库或者可执行程序的一部分被打包到系统中的，为了确保完备，静态库的都会收集。

最终合并的NOTICE.txt要体现出镜像中每个文件都是用了哪些License，模块和License要有对应关系。

不同形态的打包位置不同，最终合并的NOTICE.txt文件在镜像的/system/etc/ 目录下，ndk形态的NOTICE.txt文件最终会在native根目录下。



### 收集规则

**按照优先级收集License**

1. 编译脚本会在BUILD.gn所在的当前目录中查找Readme.OpenSource文件，解析该文件，找出该文件中声明的license，将其作为模块的License（文件名称可以为LICENSE|NOTICE|COPYRIGHT|COPYING）。

   如果Readme.OpenSource文件中配置的license文件不存在，会采用步骤2进行收集。

2. 对于系统编译、ndk和sdk编译、瘦设备编译收集notice，各模块在BUILD.gn中通过调用相关模板，通过license_file字段直接声明自己使用的License文件。如下图示例：

3. 如果Readme.OpenSource文件不存在，编译脚本会从当前目录开始，向上层目录寻找（一直找到源码的根目录），默认查找License/Copyright/Notice三个文件，如果找到，则将其作为模块的License。

4. 如果上面三种方式都未找到license，则该software声明信息不会在最终的NOTICE.txt中展示。

**不同产品形态如何配置收集LICENSE**

***对于系统编译、ndk和sdk编译、瘦设备编译时收集notice使用的模板是不相同的，下面列举不同产品形态编译使用的模板***
   
1. rk3568形态可使用ohos_shared_library、ohos_static_library、ohos_executable、ohos_app、ohos_rust_library、ohos_abc、ohos_bpf、ohos_rust_proc_macro模板，这几种模板分别是编译在编译动态库、静态库、可执行文件、app、rust库、abc文件、bpf文件、proc_macro时使用的，在完成编译任务后，会自动收集编译目标所依赖到的三方开源信息。如下图示例：

   ```
   ohos_shared_library("example") {
   	...
   	license_file = "path-to-license-file"
   	...
   }
   ```

2. sdk以及ndk形态除了1中列举的模板可以使用外，还可使用ohos_cargo_crate、ohos_ndk_copy用于在编译sdk时生产rust类型目标，ohos_ndk_copy主要是将prebuilts下的软件直接拷贝到ndk时使用。

   ```
   ohos_ndk_copy("example") {
   	...
   	license_file = "path-to-license-file"
   	...
   }
   ```

3. 瘦设备编译主要是通过lite_library模板实现编译操作，模板只能在非标准形态下使用。
   ```
   lite_library("example") {
   	...
   	license_file = "path-to-license-file"
   	...
   }
   ```
   

**需要注意及检查的问题**

1. 三方的开源软件，比如openssl，icu等，这部分软件基本上在源码目录下都是要求配置README.OpenSource，要检查README.OpenSource文件是否和BUILD.gn文件在同一个目录，以及README.OpenSource文件中配置的License文件是否存在以及有效，其中Name、License File、Version Number字段比较重要，分别对应软件名称、软件开源声明信息所在的文件路径、软件版本号，若License。
   
   ```
   [
	  {
		"Name": "xxx", # Software Name
		"License": "xxx",
		"License File": "LICENSE", # License File Name
		"Version Number": "1.8.0",  # Software Version
		"Owner": "xxx
		"Upstream URL": "xxx",
		"Description": "xxx"
	  }
	]
   ```
   
2. 代码目录下，如果代码使用的不是Apache2.0 License，需要在目录下提供对应的License文件，或者直接在模块中指定license_file。
3. 如果BUILD.gn中添加的源码文件不是当前目录的，需要检查下源码文件所在仓下的license是否和BUILD.gn文件所在仓的一致，不一致的需要处理。
4. 如果README.OpenSource文件中配置了多段software信息，收集时会将所有的software信息都收集处理，但Path字段只会展示一次。
5. 如果README.OpenSource文件中想配置多个License声明，License File对应的字段可以填写多个License文件，前提要确保每个License都存在，且每个License需要以","隔开，例如：
   
   ```
   "License File": "LICENSE,COPYRIGHT"
   ```

