
## Bazel、Soong、GN构建规则对比
| 规则 | bazel | android.bp | gn | openharmony高级模板 |
| --- | --- | --- | --- | --- |
| 可执行文件 | cc_binary | cc_binary | executable | ohos_executable |
| 静态库 | cc_library(linkstatic=1) | cc_library_static | static_library | ohos_static_library |
| 动态库 | cc_shared_library | cc_library_shared | shared_library | ohos_shared_library |
| 目标名 | name | name | target_name |  |
| 依赖 | deps | shared_libs、static_libs | deps |  |
| 源码文件 | srcs | src | sources |  |
| 编译选项 | copts | cflags, cppflags | cflags, ccflags |  |
| 宏定义 | defines | cflags = [ "-DXXX" ] | defines |  |
| 头文件路径 | includes | include_dirs | include_dirs |  |
| 链接选项 | linkopts | ldflags | ldflags |  |

## 构建示例
源码文件为main.cpp，动态库和静态库的源码文件为lib.cpp, 使用下面文件，将分别生成一个可执行文件hello_world，一个动态库libhello.so和一个静态库libhello.a。
### Bazel：
在项目的根目录下创建一个名为BUILD的文件，内容如下：
```go
cc_library(
    name = "hello_lib",
    srcs = ["lib.cpp"],
    hdrs = ["lib.h"],
    linkstatic=1
)
cc_shared_library(
    name = "hello_shlib",
    srcs = ["lib.cpp"],
    hdrs = ["lib.h"],
)
cc_binary(
    name = "hello_world",
    srcs = ["main.cpp"],
    deps = [":hello_lib"，":hello_shlib"],
)
```
### Android.bp：
创建一个名为Android.bp的文件，内容如下：
```go
cc_library_shared {
    name: "libhello",
    srcs: ["lib.cpp"],
}

cc_library_static {
    name: "libhello_static",
    srcs: ["lib.cpp"],
}

cc_binary {
    name: "hello_world",
    srcs: ["main.cpp"],
    shared_libs: ["libhello"],
    static_libs: ["libhello_static"],
}
```

### Android.mk：
创建一个名为Android.mk的文件，内容如下：
```makefile
LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)

LOCAL_MODULE    := libhello
LOCAL_SRC_FILES := lib.cpp

include $(BUILD_SHARED_LIBRARY)

include $(CLEAR_VARS)

LOCAL_MODULE    := libhello_static
LOCAL_SRC_FILES := lib.cpp

include $(BUILD_STATIC_LIBRARY)

include $(CLEAR_VARS)

LOCAL_MODULE    := hello_world
LOCAL_SRC_FILES := main.cpp
LOCAL_SHARED_LIBRARIES := libhello
LOCAL_STATIC_LIBRARIES := libhello_static

include $(BUILD_EXECUTABLE)
```

### GN：
创建一个名为BUILD.gn的文件，内容如下：
```go
shared_library("libhello") {
  sources = [ "lib.cpp" ]
}

static_library("libhello_static") {
  sources = [ "lib.cpp" ]
}

executable("hello_world") {
  sources = [ "main.cpp" ]
  deps = [ ":libhello", ":libhello_static" ]
}
```


