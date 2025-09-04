# SBOM

## 简介

本工具基于 **GN 构建元数据**，遵循 **OpenHarmony SBOM 中间态元数据格式**，生成标准化的中间实例，并输出符合 SPDX 2.3 规范的 SBOM 文件。

无需依赖任何外部服务，满足OH社区**安全治理**、**开源合规治理**、**开源软件管理**述求。

## 目录

```
/sbom                          	  # SBOM工具根目录

├── __pycache__                   
├── analysis/                     # 依赖关系构建，包括依赖图、文件依赖关系和包依赖关系构建
├── common/                       # 工具类
├── converters/                   # 转换器，将SBOM元数据转换为各种标准的JSON格式
├── data/                   	  # `gn_gen`、`manifest`等元数据模型字段集中配置管理
├── extraction/                   # 负责加载构建系统生成的 `gn_gen.json`等关键资源并提取版权许可证信息
├── pipeline/                     # SBOM 生成核心流程控制器，将构建系统信息转化为标准化的SBOM 结构，是 SBOM 生成主入口
├── sbom
│   ├── builder/                  # SBOM建造者，提供SBOM生成工具类
│   └── config/            		  # SBOM 模型字段的集中配置与管理，提供基于 JSON 配置的字段元数据管理
│   └── metadata/                 # 定义 SBOM 元数据的核心数据模型，包括文档信息、软件包、文件、依赖关系等
│   └── vaildation/               # SBOM字段级验证工具，支持通过声明式方式检查必填字段是否具有有效值
├── generate_sbom.py*                
```


## 说明

**代码根目录下执行全量版本的编译命令**

~~~shell
sbom生成默认为关闭

使用如下命令：
```
/build.sh --product-name {product_name} --sbom=true
```

sbom输出在 out/{product_name}/sbom/目录下。
~~~

**输出**

```
out/{product_name}/sbom/	# sbom输出根目录

├── sbom_meta_date.json		# SBOM中间态 json 文件
├── spdx.json				# SPDX格式 SBOM 文件
```

1. **SBOM中间态文件**

   包含以下四个字段

   - document

     本 SBOM 文档的元数据，包含标识、版本、时间戳、作者、工具等核心信息。

     | 字段名               | 类型   | 是否必选            | 说明                     |
     | -------------------- | ------ | ------------------- | ------------------------ |
     | `serialNumber`       | 字符串 | 必选                | 文档的唯一标识符         |
     | `docId`              | 字符串 | SPDX 必选，其他可选 | 文档的唯一 ID            |
     | `name`               | 字符串 | SPDX 必选，其他可选 | 文档所描述的软件名称     |
     | `documentNamespace`  | 字符串 | SPDX 必选，其他可选 | 文档的全局唯一命名空间   |
     | `version`            | 字符串 | 必选                | 文档的版本号             |
     | `bomFormat`          | 字符串 | 必选                | SBOM 的格式标识          |
     | `specVersion`        | 字符串 | 必选                | 所遵循规范的版本号       |
     | `dataLicense`        | 字符串 | 必选                | SBOM 数据的许可声明      |
     | `licenseListVersion` | 字符串 | SPDX 必选，其他可选 | 许可证列表的版本号       |
     | `timestamp`          | 字符串 | 必选                | 文档生成的时间戳         |
     | `authors`            | 数组   | 必选                | 文档创建者的标识         |
     | `lifecycles`         | 数组   | 可选                | 覆盖的软件生命周期阶段   |
     | `properties`         | 数组   | 可选                | 用户自定义的附加属性     |
     | `tools`              | 数组   | 可选                | 生成文档所使用的工具信息 |
     | `docComments`        | 字符串 | 可选                | 对文档的整体说明或注释   |

   - files

     记录构成软件的各个文件的路径、校验和、许可证结论及版权声明等详细信息。

     | 字段名               | 类型   | 是否必选           | 说明                       |
     | -------------------- | ------ | ------------------ | -------------------------- |
     | `fileName`           | 字符串 | 必选               | 文件名称或路径             |
     | `fileAuthor`         | 字符串 | 团标必选，其他可选 | 文件作者                   |
     | `fileId`             | 字符串 | 必选               | 文件标识符                 |
     | `fileTypes`          | 数组   | 可选               | 文件类型数组               |
     | `checksums`          | 数组   | 必选               | 文件的校验和信息           |
     | `licenseConcluded`   | 字符串 | 必选               | 许可证结论                 |
     | `licenseInfoInFiles` | 数组   | 可选               | 文件中声明的许可证信息数组 |
     | `copyrightText`      | 字符串 | 可选               | 版权声明                   |

   - packages

     描述软件包的基本属性，包括名称、版本、供应商、许可证、唯一标识及哈希值等元数据。

     | 字段名             | 类型   | 是否必选                 | 说明                            |
     | ------------------ | ------ | ------------------------ | ------------------------------- |
     | `type`             | 字符串 | CycloneDX 必选，其他可选 | 组件类型                        |
     | `supplier`         | 字符串 | 必选                     | 供应商                          |
     | `group`            | 字符串 | 必选                     | 组件的组标识                    |
     | `name`             | 字符串 | 必选                     | 组件的名称                      |
     | `version`          | 字符串 | 必选                     | 组件的版本号                    |
     | `purl`             | 字符串 | 必选                     | 组件的唯一标识                  |
     | `licenseConcluded` | 字符串 | 必选                     | 实际许可证                      |
     | `licenseDeclared`  | 字符串 | 必选                     | 作者声明的许可证                |
     | `comCopyright`     | 字符串 | 可选                     | 版权声明                        |
     | `bom-ref`          | 字符串 | 必选                     | 文档内部唯一标识符，可复用 purl |
     | `downloadLocation` | 字符串 | 可选                     | 下载来源                        |
     | `hashes`           | 数组   | 必选                     | hash 值                         |
     | `compPlatform`     | 字符串 | 团标必选，其他可选       | 组件平台架构                    |

   -  relationships

     定义组件与文件或其他组件之间的依赖或关联关系，明确软件结构与组成逻辑。

     | 字段名             | 类型   | 是否必选 | 说明                                                 |
     | ------------------ | ------ | -------- | ---------------------------------------------------- |
     | `bom-ref`          | 字符串 | 必选     | 当前组件或服务的引用标识符                           |
     | `dependsOn`        | 数组   | 必选     | 当前组件或服务所依赖的其他组件或服务的引用标识符列表 |
     | `relationshipType` | 字符串 | 必选     | 依赖类型                                             |

2. **SPDX文件**

   目前输出SPDX2.3 格式，参考文档[SPDX Specification 2.3.0](https://spdx.github.io/spdx-spec/v2.3/)

**输出示例**

1. **镜像上文件**

    ```json
    # sbom 中间态格式
    # 镜像上文件信息
    # 以镜像上文件 system/app/com.ohos.adminprovisioning/adminprovisioning.hap 作为起点
    {
        "copyrightText": "NOASSERTION",
        "fileAuthor": "NOASSERTION",
        "fileId": "system/app/com.ohos.adminprovisioning/adminprovisioning.hap",
        "fileName": "adminprovisioning.hap"
    }
    # 安装到镜像上文件依赖
    # 此镜像上文件由 //out/rk3568/obj/applications/standard/admin_provisioning/adminprovisioning.hap 拷贝产生
    {
        "bom-ref": "system/app/com.ohos.adminprovisioning/adminprovisioning.hap",
        "dependsOn": [
            "//out/rk3568/obj/applications/standard/admin_provisioning/adminprovisioning.hap"
        ],
        "relationshipType": "COPY_OF"
    }
    # 构建生成文件 
    # 构建文件 //out/rk3568/obj/applications/standard/admin_provisioning/adminprovisioning.hap 信息
    {
        "copyrightText": "NOASSERTION",
        "fileAuthor": "NOASSERTION",
        "fileId": "//out/rk3568/obj/applications/standard/admin_provisioning/adminprovisioning.hap",
        "fileName": "adminprovisioning.hap"
    }
    # 构建文件依赖其他文件
    {
        "bom-ref": "//out/rk3568/obj/applications/standard/admin_provisioning/adminprovisioning.hap",
        "dependsOn": [
            "//out/rk3568/obj/applications/standard/admin_provisioning/adminprovisioning_hap/ResourceTable.h",
            "//out/rk3568/clang_x64/arkcompiler/ets_frontend/es2abc",
            "//out/rk3568/obj/applications/standard/admin_provisioning/adminprovisioning_hap/resources.zip",
            "//out/rk3568/obj/applications/standard/admin_provisioning/adminprovisioning_hap/js_assets.zip",
            "//out/rk3568/gen/applications/standard/admin_provisioning/adminprovisioning_hap.metadata",
            "//out/rk3568/obj/developtools/packing_tool/jar/haptobin_tool.jar",
            "//out/rk3568/obj/developtools/packing_tool/jar/app_unpacking_tool.jar",
            "//out/rk3568/obj/developtools/packing_tool/jar",
            "//out/rk3568/obj/developtools/packing_tool/jar/app_check_tool.jar",
            "//out/rk3568/clang_x64/obj/arkcompiler/ets_frontend/es2panda/ts2abc.js",
            "//out/rk3568/obj/developtools/packing_tool/jar/app_packing_tool.jar"
        ],
        "relationshipType": "GENERATED_FROM"
    }
    # 构建文件来源部件
    # pkg:gitee/OpenHarmony/applications_admin_provisioning@94d3db73c8492ac0ace0b59e76b0c23b6ca6663f
    {
        "bom-ref": "pkg:gitee/OpenHarmony/applications_admin_provisioning@94d3db73c8492ac0ace0b59e76b0c23b6ca6663f",
        "dependsOn": [
            "//out/rk3568/obj/applications/standard/admin_provisioning/adminprovisioning_hap/ResourceTable.h",
            "//out/rk3568/gen/applications/standard/admin_provisioning/adminprovisioning_app_profile.metadata",
            "//out/rk3568/gen/applications/standard/admin_provisioning/adminprovisioning_js_assets.metadata",
            "//out/rk3568/gen/applications/standard/admin_provisioning/adminprovisioning_hap.metadata",
            "//out/rk3568/obj/applications/standard/admin_provisioning/adminprovisioning_hap/resources.zip",
            "//out/rk3568/gen/applications/standard/admin_provisioning/adminprovisioning_resources.metadata",
            "//out/rk3568/gen/applications/standard/admin_provisioning/adminprovisioning_resources/module.json",
            "//out/rk3568/obj/applications/standard/admin_provisioning/adminprovisioning_hap/js_assets.zip",
            "//out/rk3568/obj/applications/standard/admin_provisioning/adminprovisioning.hap",
            "//out/rk3568/gen/applications/standard/admin_provisioning/adminprovisioning_resources/ResourceTable.h"
        ],
        "relationshipType": "GENERATES"
    }
    ```

    ---

    ```json
    # SPDX2.3 格式
    # 镜像上文件信息
    # 以镜像上文件 system/app/com.ohos.adminprovisioning/adminprovisioning.hap 作为起点
    {
        "SPDXID": "system/app/com.ohos.adminprovisioning/adminprovisioning.hap",
        "copyrightText": "NOASSERTION",
        "fileName": "adminprovisioning.hap"
    }
    # 安装到镜像上文件依赖
    # 此镜像上文件由 //out/rk3568/obj/applications/standard/admin_provisioning/adminprovisioning.hap 拷贝产生
    {
        "relatedSpdxElement": "//out/rk3568/obj/applications/standard/admin_provisioning/adminprovisioning.hap",
        "relationshipType": "COPY_OF",
        "spdxElementId": "system/app/com.ohos.adminprovisioning/adminprovisioning.hap"
    }
    # 构建生成文件 
    # 构建文件 //out/rk3568/obj/applications/standard/admin_provisioning/adminprovisioning.hap 信息
    {
        "SPDXID": "//out/rk3568/obj/applications/standard/admin_provisioning/adminprovisioning.hap",
        "copyrightText": "NOASSERTION",
        "fileName": "adminprovisioning.hap"
    }
    # 构建文件依赖其他文件
    {
        "relatedSpdxElement": "//out/rk3568/obj/developtools/packing_tool/jar/app_check_tool.jar",
        "relationshipType": "GENERATED_FROM",
        "spdxElementId": "//out/rk3568/obj/applications/standard/admin_provisioning/adminprovisioning.hap"
    },
    {
        "relatedSpdxElement": "//out/rk3568/gen/applications/standard/admin_provisioning/adminprovisioning_hap.metadata",
        "relationshipType": "GENERATED_FROM",
        "spdxElementId": "//out/rk3568/obj/applications/standard/admin_provisioning/adminprovisioning.hap"
    } ...
    # 构建文件来源部件
    # pkg:gitee/OpenHarmony/applications_admin_provisioning@94d3db73c8492ac0ace0b59e76b0c23b6ca6663f
    {
        "relatedSpdxElement": "//out/rk3568/obj/applications/standard/admin_provisioning/adminprovisioning.hap",
        "relationshipType": "GENERATES",
        "spdxElementId": "pkg:gitee/OpenHarmony/applications_admin_provisioning@94d3db73c8492ac0ace0b59e76b0c23b6ca6663f"
    }
    ```

2. **上游包**

    ```json
    # sbom 中间态格式
    # 以 pkg:gitee/OpenHarmony/third_party_bounds_checking_function@2ae82839ecaaa7d031e66ccbd2076d671acfd615 为例
    {
        "bom-ref": "pkg:gitee/OpenHarmony/third_party_bounds_checking_function@2ae82839ecaaa7d031e66ccbd2076d671acfd615",
        "compPlatform": "Linux",
        "downloadLocation": "https://gitee.com/openharmony/third_party_bounds_checking_function/tree/2ae82839ecaaa7d031e66ccbd2076d671acfd615",
        "group": "OpenHarmony",
        "licenseDeclared": "NOASSERTION",
        "name": "third_party_bounds_checking_function",
        "purl": "pkg:gitee/OpenHarmony/third_party_bounds_checking_function@2ae82839ecaaa7d031e66ccbd2076d671acfd615",
        "supplier": "Organization: OpenHarmony",
        "type": "library",
        "version": "master"
    }
    # 依赖信息
    # 依赖关系是变体，上游包 ref 为 pkg:gitee/upstream/openEuler:libboundscheck@v1.1.16
    {
        "bom-ref": "pkg:gitee/OpenHarmony/third_party_bounds_checking_function@2ae82839ecaaa7d031e66ccbd2076d671acfd615",
        "dependsOn": [
            "pkg:gitee/upstream/openEuler:libboundscheck@v1.1.16"
        ],
        "relationshipType": "VARIANT_OF"
    }
    # 上游包信息
    {
        "bom-ref": "pkg:gitee/upstream/openEuler:libboundscheck@v1.1.16",
        "downloadLocation": "https://gitee.com/openeuler/libboundscheck",
        "licenseConcluded": "Mulan Permissive Software License，Version 2",
        "name": "openEuler:libboundscheck",
        "purl": "pkg:gitee/upstream/openEuler:libboundscheck@v1.1.16",
        "supplier": "NOASSERTION",
        "type": "library",
        "version": "v1.1.16"
    }
    ```

    ---

    ```json
    # SPDX 格式
    # 以 pkg:gitee/OpenHarmony/third_party_bounds_checking_function@2ae82839ecaaa7d031e66ccbd2076d671acfd615 为例
    {
        "SPDXID": "pkg:gitee/OpenHarmony/third_party_bounds_checking_function@2ae82839ecaaa7d031e66ccbd2076d671acfd615",
        "copyrightText": "NOASSERTION",
        "downloadLocation": "https://gitee.com/openharmony/third_party_bounds_checking_function/tree/2ae82839ecaaa7d031e66ccbd2076d671acfd615",
        "externalRefs": [
            {
                "referenceLocator": "pkg:gitee/OpenHarmony/third_party_bounds_checking_function@2ae82839ecaaa7d031e66ccbd2076d671acfd615",
                "referenceType": "purl"
            }
        ],
        "filesAnalyzed": false,
        "licenseDeclared": "NOASSERTION",
        "name": "third_party_bounds_checking_function",
        "originator": "OpenHarmony",
        "primaryPackagePurpose": "LIBRARY",
        "supplier": "Organization: OpenHarmony",
        "versionInfo": "master"
    }
    # 依赖信息
    # 依赖关系是变体，上游包 ref 为 pkg:gitee/upstream/openEuler:libboundscheck@v1.1.16
    {
        "relatedSpdxElement": "pkg:gitee/upstream/openEuler:libboundscheck@v1.1.16",
        "relationshipType": "VARIANT_OF",
        "spdxElementId": "pkg:gitee/OpenHarmony/third_party_bounds_checking_function@2ae82839ecaaa7d031e66ccbd2076d671acfd615"
    }
    # 上游包信息
    {
        "SPDXID": "pkg:gitee/upstream/openEuler:libboundscheck@v1.1.16",
        "copyrightText": "NOASSERTION",
        "downloadLocation": "https://gitee.com/openeuler/libboundscheck",
        "externalRefs": [
            {
                "referenceLocator": "pkg:gitee/upstream/openEuler:libboundscheck@v1.1.16",
                "referenceType": "purl"
            }
        ],
        "filesAnalyzed": false,
        "licenseConcluded": "Mulan Permissive Software License，Version 2",
        "name": "openEuler:libboundscheck",
        "primaryPackagePurpose": "LIBRARY",
        "supplier": "NOASSERTION",
        "versionInfo": "v1.1.16"
    }
    ```

3. **so文件依赖关系**

    ```json
    # sbom 中间态格式
    # so 文件信息
    {
        "copyrightText": "NOASSERTION",
        "fileAuthor": "NOASSERTION",
        "fileId": "//out/rk3568/applications/calendar_data/libcj_calendar_manager_ffi.z.so",
        "fileName": "libcj_calendar_manager_ffi.z.so"
    }
    # 源文件
    {
        "bom-ref": "//out/rk3568/applications/calendar_data/libcj_calendar_manager_ffi.z.so",
        "dependsOn": [
            "//applications/standard/calendardata/calendarmanager/cj/src/cj_native_calendar.cpp",
            "//applications/standard/calendardata/calendarmanager/cj/src/cj_data_share_helper_manager.cpp",
            "//applications/standard/calendardata/calendarmanager/native/src/calendar_env.cpp",
            "//applications/standard/calendardata/calendarmanager/cj/src/cj_calendar_manager.cpp",
            "//applications/standard/calendardata/calendarmanager/native/src/event_filter.cpp",
            "//applications/standard/calendardata/calendarmanager/cj/src/cj_event_filter.cpp",
            "//applications/standard/calendardata/calendarmanager/cj/src/cj_native_calendar_manager.cpp",
            "//applications/standard/calendardata/calendarmanager/cj/src/cj_native_util.cpp",
            "//applications/standard/calendardata/calendarmanager/cj/src/cj_calendar_env.cpp",
            "//applications/standard/calendardata/calendarmanager/cj/src/calendar_manager_ffi.cpp",
            "//applications/standard/calendardata/calendarmanager/cj/src/cj_calendar.cpp"
        ],
        "relationshipType": "GENERATED_FROM"
    }
    # 静态依赖
    {
        "bom-ref": "//out/rk3568/applications/calendar_data/libcj_calendar_manager_ffi.z.so",
        "dependsOn": [
            "libclang_rt.builtins.a",
            "libc++abi.a"
        ],
        "relationshipType": "STATIC_LINK"
    }
    # 动态依赖
    {
        "bom-ref": "//out/rk3568/applications/calendar_data/libcj_calendar_manager_ffi.z.so",
        "dependsOn": [
            "//out/rk3568/distributeddatamgr/data_share/libdatashare_common.z.so",
            "//out/rk3568/ability/ability_runtime/libnapi_base_context.z.so",
            "libc++.so",
            "//out/rk3568/arkui/ace_engine/libace_uicontent.z.so",
            "libc.so",
            "//out/rk3568/arkui/napi/libcj_bind_ffi.z.so",
            "//out/rk3568/distributeddatamgr/data_share/libdatashare_consumer.z.so",
            "//out/rk3568/security/access_token/libprivacy_sdk.z.so",
            "libm.so",
            "//out/rk3568/ability/ability_runtime/libability_context_native.z.so",
            "//out/rk3568/hiviewdfx/hilog/libhilog.so",
            "libunwind.so",
            "//out/rk3568/ability/ability_base/libzuri.z.so",
            "//out/rk3568/ability/ability_runtime/libdata_ability_helper.z.so",
            "//out/rk3568/arkui/napi/libace_napi.z.so",
            "//out/rk3568/ability/ability_runtime/libabilitykit_native.z.so",
            "//out/rk3568/arkui/napi/libcj_bind_native.z.so",
            "//out/rk3568/security/access_token/libaccesstoken_sdk.z.so",
            "//out/rk3568/ability/ability_runtime/libability_manager.z.so",
            "//out/rk3568/ability/ability_base/libwant.z.so",
            "//out/rk3568/commonlibrary/c_utils/libutils.z.so",
            "//out/rk3568/ability/ability_runtime/libability_connect_callback_stub.z.so",
            "//out/rk3568/communication/ipc/libipc_single.z.so",
            "libdl.so"
        ],
        "relationshipType": "DYNAMIC_LINK"
    }
    ```

    ---

    ```json
    # SPDX 格式
    # so 文件信息
    {
        "SPDXID": "//out/rk3568/applications/calendar_data/libcj_calendar_manager_ffi.z.so",
        "copyrightText": "NOASSERTION",
        "fileName": "libcj_calendar_manager_ffi.z.so"
    }
    # 源文件
    {
        "relatedSpdxElement": "//applications/standard/calendardata/calendarmanager/cj/src/cj_calendar.cpp",
        "relationshipType": "GENERATED_FROM",
        "spdxElementId": "//out/rk3568/applications/calendar_data/libcj_calendar_manager_ffi.z.so"
    },
    {
        "relatedSpdxElement": "//applications/standard/calendardata/calendarmanager/cj/src/cj_native_calendar.cpp",
        "relationshipType": "GENERATED_FROM",
        "spdxElementId": "//out/rk3568/applications/calendar_data/libcj_calendar_manager_ffi.z.so"
    },
    {
        "relatedSpdxElement": "//applications/standard/calendardata/calendarmanager/native/src/calendar_env.cpp",
        "relationshipType": "GENERATED_FROM",
        "spdxElementId": "//out/rk3568/applications/calendar_data/libcj_calendar_manager_ffi.z.so"
    },
    {
        "relatedSpdxElement": "//applications/standard/calendardata/calendarmanager/cj/src/cj_event_filter.cpp",
        "relationshipType": "GENERATED_FROM",
        "spdxElementId": "//out/rk3568/applications/calendar_data/libcj_calendar_manager_ffi.z.so"
    } ...
    # 静态依赖
    {
        "relatedSpdxElement": "libclang_rt.builtins.a",
        "relationshipType": "STATIC_LINK",
        "spdxElementId": "//out/rk3568/applications/calendar_data/libcj_calendar_manager_ffi.z.so"
    },
    {
        "relatedSpdxElement": "libc++abi.a",
        "relationshipType": "STATIC_LINK",
        "spdxElementId": "//out/rk3568/applications/calendar_data/libcj_calendar_manager_ffi.z.so"
    }
    # 动态依赖
    {
        "relatedSpdxElement": "//out/rk3568/security/access_token/libaccesstoken_sdk.z.so",
        "relationshipType": "DYNAMIC_LINK",
        "spdxElementId": "//out/rk3568/applications/calendar_data/libcj_calendar_manager_ffi.z.so"
    },
    {
        "relatedSpdxElement": "//out/rk3568/hiviewdfx/hilog/libhilog.so",
        "relationshipType": "DYNAMIC_LINK",
        "spdxElementId": "//out/rk3568/applications/calendar_data/libcj_calendar_manager_ffi.z.so"
    },
    {
        "relatedSpdxElement": "//out/rk3568/ability/ability_runtime/libability_context_native.z.so",
        "relationshipType": "DYNAMIC_LINK",
        "spdxElementId": "//out/rk3568/applications/calendar_data/libcj_calendar_manager_ffi.z.so"
    } ...
    ```

    
