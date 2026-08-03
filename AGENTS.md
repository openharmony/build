# AGENTS.md

面向在 OpenHarmony `build` 编译构建框架仓（`@ohos/build_framework`，子系统
`build`）工作的 OpenCode 智能体。基于 GN + Ninja 的构建系统。

本仓是**全 OpenHarmony 源码树的公共构建 API**：`ohos.gni`、`ohos_*` 模板、
GN 构建参数、`subsystem_config.json`、`version.gni` 被所有其他仓 import。
改动这些公共面会破坏整个 OS 构建，见下方「约束与边界」。

> 嵌套指引：本仓内**无** `CLAUDE.md`/`GEMINI.md`/`.cursorrules` 等嵌套指令
> 文件，也无目录级 `AGENTS.md`。本文件是唯一的 agent 指引。深度知识一律
> 路由到 `docs/`（见「知识路由」）。

## 源码根目录 vs. 本仓

构建从**完整 OpenHarmony 源码树根目录**（`build/` 的父目录）执行，**不**在
`build/` 内部执行。源码根目录通过向上查找 `.gn`（软链到
`build/core/gn/dotfile.gn`）定位。源码根目录下的 `build.sh` 和 `build.py`
软链到 `build/build_scripts/`。下面大多数命令假设 CWD = 源码根目录，而非
`build/`。

## 前置准备（构建前执行一次）

1. `build/prebuilts_download.sh` — 下载工具链、python、node、clang 等到
   `prebuilts/`。若预置 python3 缺失，`build.sh` 会硬报错退出。
2. Node.js **v14.21.1** 硬性锁定：若 `node -v` != `v14.21.1`，
   `build_scripts/build.sh` 直接退出。
3. 安装 `hb` CLI：`python3 -m pip install --user build/hb`（Python >=3.8）。
   卸载：`python3 -m pip uninstall ohos-build`。
4. 主机：Ubuntu 18.04+（独立编译需 22.04+）。

## 构建命令

全量产品构建（在源码根目录执行）：
```
./build.sh --product-name {product_name}
```
镜像输出到 `out/{device_name}/packages/phone/images/`。

`build.sh` 分发到 `build/hb/main.py build`（新 hb，默认）。传入
`--using_hb_new=false` 使用旧路径 `build/scripts/entry.py`。

`hb` 工具子命令：`set`、`build`、`clean`、`env`、`tool`、`install`、
`package`、`publish`、`update`、`push`、`indep_build`。见 `hb help` 和
`hb/README.md`。

常用 `hb build` 选项（默认值与 `build.sh` 不同）：
- `--product-name rk3568`（或 `rk3568@hihope`、`ohos-sdk` 等）
- `--build-target <target>` — 构建单个 ninja 目标；可重复
- `--gn-args is_debug=true` / `--ninja-args=-dkeeprsp`
- `-f` / `--full-compilation` — 添加 `make_all` 和 `make_test`
- `--ccache` — 启用 ccache（需本地安装 ccache）
- `--build-only-gn` / `--build-only-load` — 提前停止以便调试
- `--keep-ninja-going` — 出错后继续构建（调试单个目标）

构建流程（在 `hb/main.py` 中）：preloader -> loader -> `gn gen` -> `ninja`
-> 打包。

## `--build-target` 注意事项

- 子系统名**不是**可构建目标。
- 仅部件名常会失败；使用完整形式：
  `--build-target out/{device}/build_configs/{subsystem}/{part}:{part}`。
- 重名需用完整 `{path}:{target}` 形式。

## GN 模板与配置

- 在 `BUILD.gn` 文件中 `import("//build/ohos.gni")` — 它汇总了所有常用模板
  （cxx、rust、common、prebuilt、bpf、idl、ndk、notice、sa_profile）。除非
  必要，不要直接 import 单个模板文件。
- 模板位于 `build/templates/`（`cxx/`、`rust/`、`common/`、`bpf/`、`idl/`、
  `abc/`、`cangjie/`、`kernel/`、`metadata/`、`update/`）。
- 构建参数声明在 `ohos_var.gni`、`common.gni`、`version.gni`。

### 部件模型（四个配置文件）

1. **每个模块的 `BUILD.gn`** — 使用 `ohos_*` 模板
   （`ohos_shared_library`、`ohos_executable`、`ohos_prebuilt_etc` 等）。
2. **每个部件的 `bundle.json`** — 定义 `component.build.sub_component`
   （构建入口）、`inner_kits`（跨部件接口）、`test`（测试目标）。
3. **`vendor/{company}/{product}/config.json`** — 产品配置；列出包含的
   子系统/部件及其特性。
4. **`build/subsystem_config.json`** — 子系统名 -> 路径的注册表。

一个模块只有满足以下条件才会被构建进镜像：有 `part_name`；它（或其依赖）在
部件的 `sub_component` 中；该部件在产品的部件列表中。`ohos_executable` 除非
设置 `install_enable = true`，否则**不会**被安装。

## 测试

编译框架测试位于 `build/test/`，使用 pytest：
```
bash build/test/script/start_env.sh              # 一次性安装 pytest 依赖
bash build/test/script/start_ex.sh option        # 构建选项测试
bash build/test/script/start_ex.sh template      # gn 模板测试
bash build/test/script/start_ex.sh performance    # 性能基准测试
bash build/test/script/start_ex.sh all            # option -> performance -> template（顺序不可变）
```
报告输出到 `out/test_report/`。配置：`build/test/example/build_example.json`。

`hb` 单元测试位于 `build/hb/test/unitTest/`，使用 Python `unittest`。

Rust 测试目标：`//build/rust/tests:tests`。

## 独立编译（indep）

`hb build {component} -i` 无需完整源码树即可构建单个部件 — 只需 `build` 仓 +
该部件的代码仓；其他依赖以二进制包形式下载到 `~/.hpm`。必须在包含
`build/indep_configs/build_indep.sh` 的目录下执行。预下载用
`bash build/prebuilts_config.sh --download-sdk`（与完整的
`prebuilts_download.sh` 不同）。见 `indep_configs/README_zh.md`。

## 目录地图与「去哪找」

| 任务 / 需求 | 去哪看 |
| --- | --- |
| 改 GN 模板（`ohos_shared_library` 等） | `build/templates/{cxx,rust,common,bpf,idl,...}/`；模板汇总入口 `build/ohos.gni` |
| 改构建参数（`declare_args`） | `build/ohos_var.gni`、`build/common.gni`、`build/version.gni` |
| 改子系统注册（名字↔路径） | `build/subsystem_config.json`（示例：`build/subsystem_config_example.json`） |
| 改产品/部件包含关系 | 产品仓 `vendor/{company}/{product}/config.json`；部件 `bundle.json` 的 `component.build.sub_component` |
| 改 `hb` CLI 行为 | `build/hb/`（入口 `hb/main.py`，子命令在 `hb/services/`、`hb/modules/`） |
| 改 GN 生成逻辑 / dotfile | `build/core/gn/`（`.gn` 软链到此）、`build/core/build_scripts/` |
| 改打包 / 镜像 / 镜像分区 | `build/ohos/packages/`、`build/ohos/images/` |
| 改 SDK / NDK 生成 | `build/ohos/sdk/`、`build/ohos/ndk/` |
| 改 Notice / 开源合规 | `build/ohos/notice/`、`build/OAT.xml`、`build/ohos/sbom/` |
| 改 SA profile / syscheck | `build/ohos/sa_profile/`、`build/ohos/hisysevent/` |
| 改工具链（clang/gcc/ld） | `build/toolchain/` |
| 改 lite 系统（小型设备） | `build/lite/` |
| 改独立编译（indep） | `build/indep_configs/` |
| 改测试框架 | `build/test/`（pytest 用例在 `build/test/example/`） |
| 改 Rust 构建支持 | `build/templates/rust/`、`build/rust/tests/` |
| 改 abi/abc/cangjie 内核/metadata/update 模板 | `build/templates/{abc,cangjie,kernel,metadata,update}/` |
| 改预置工具链下载 | `build/prebuilts_download.{sh,py}`、`build/prebuilts_config.{sh,py,json}` |
| 调试一次构建 | `--build-only-gn` / `--build-only-load` 提前停止；`--keep-ninja-going` 出错继续 |
| 查 FAQ / 编译报错 | `build/docs/FAQ.md` |

## 知识路由

编辑前按任务/路径/术语加载对应文档；并在最终回复中声明「已读文档 + 命中约束」
（见「编辑前自检」）。`docs/` 为中文权威文档；下面给出触发条件。

### 任务路由

| 任务 | 先读 |
| --- | --- |
| 新增一个模块到构建 | `docs/标准系统如何添加一个模块.md`、`docs/部件化编译最佳实践.md` |
| 新增/修改构建参数 | `docs/how-to-add-a-build-parameter.md`、`docs/编译选项规范.md` |
| 改 `bundle.json` / 条件编译 | `docs/bundle.json条件编译配置指导.md`、`docs/部件化编译最佳实践.md` |
| 改产品配置 | `docs/product-configuration.md` |
| 改 cflags / 编译选项 | `docs/cflags系列参数使用指导.md`、`docs/编译选项规范.md` |
| deps / external_deps 用法 | `docs/关于deps及external_deps的使用.md` |
| 改镜像打包参数 | `docs/标准系统如何修改镜像文件的打包参数.md` |
| 调试构建 | `docs/编译构建调试文档.md`、`docs/FAQ.md` |
| 性能分析 / 编译耗时 | `docs/编译性能分析工具使用.md` |
| 开源 Notice / 合规 | `docs/开源软件Notice收集策略说明.md`、`docs/生成开源软件包.md` |
| 独立编译 | `docs/部件独立编译使用指南.md`、`indep_configs/README_zh.md` |
| CMake 转 GN | `docs/cmake转gn指导文档.md` |
| NDK 工具使用 | `docs/how-to-use-the-ndk-tools.md`、`docs/how to use CMake with NDK.md` |
| 编译扫描检查 | `docs/编译扫描说明.md` |
| 构建 HAP / 应用 | `docs/how-to-build-a-hap.md`、`docs/how-to-build-a-app.md` |
| 全局规则索引 | `docs/compilation-and-build-rules.md`、`docs/build_rules_map.md` |
| docs 仓外链目录 | `docs/docs仓编译构建指导文档目录.md` |

### 路径路由

| 改动路径 | 先读 |
| --- | --- |
| `build/templates/**` | `docs/编译选项规范.md`；模板对应 `templates/<x>/` 既有同类型实现 |
| `build/ohos_var.gni` / `common.gni` / `version.gni` | `docs/how-to-add-a-build-parameter.md` |
| `build/ohos/notice/**` 或 `OAT.xml` | `docs/开源软件Notice收集策略说明.md` |
| `build/ohos/sdk/**` | `docs/how-to-build-linux-arm64-sdk.md`、`docs/how-to-use-the-ndk-tools.md` |
| `build/indep_configs/**` | `docs/部件独立编译使用指南.md` |
| `build/hb/**` | `hb/README.md`（或 `README_zh.md`） |

### 术语路由

| 看到这些术语 | 含义 / 去哪读 |
| --- | --- |
| `ohos_*` 模板 | GN 构建模板，定义于 `build/templates/`，经 `build/ohos.gni` 汇总后供各仓 import |
| `part_name` / `sub_component` / `inner_kits` | 部件模型字段，见「部件模型」与 `docs/部件化编译最佳实践.md` |
| `bundle.json` | 部件清单，定义构建入口与跨部件接口 |
| `subsystem_config.json` | 子系统名↔源码路径注册表，全局共享 |
| `install_enable` | `ohos_executable` 是否进镜像的开关（默认不安装） |
| `--build-target` | ninja 目标，**非**子系统名；部件需用 `path:target` 完整形式 |
| indep / 独立编译 | 单部件免全量源码树构建，见「独立编译」段 |
| NDK / SDK | 原生/应用开发包，生成逻辑在 `build/ohos/{ndk,sdk}/` |
| sa_profile | 系统能力 profile，`build/ohos/sa_profile/` |
| SBOM / Notice / OAT | 开源合规产物：SBOM 在 `build/ohos/sbom/`，Notice 在 `build/ohos/notice/`，OAT 规则在 `build/OAT.xml` |
| `.pydeps` | Python 脚本依赖清单，**生成文件**，勿手改 |
| preloader / loader | `hb` 构建流程阶段，见 `hb/main.py` |

## 约束与边界

### 不可破坏（Do not）

- **不要**改 `ohos_*` 模板的名称、参数签名、默认行为或语义。它们是全 OS 公共
  API，被所有仓库 `import("//build/ohos.gni")` 消费。改签名=破坏全量构建。
- **不要**重命名或删除 `ohos_var.gni`/`common.gni`/`version.gni` 中已存在的
  `declare_args()` 参数名；不要静默改变其默认值。新增参数需读
  `docs/how-to-add-a-build-parameter.md`。
- **不要**改变 `build/ohos.gni` 的 import 顺序或条件 import 分支——模板注册依赖
  该顺序。
- **不要**手改生成文件：`*.pydeps`、`build/ohos/generate_part_info.py` 与
  `copy_files.py` 的输出、`build/ohos/sbom/generate_sbom.py` 产物、
  `build/ohos/notice/` 生成的 Notice 文件。生成器是唯一真源。
- **不要**把子系统名当作 `--build-target`（`AGENTS.md`「`--build-target`
  注意事项」）；不要只传部件名。
- **不要**在不设置 `install_enable = true` 的情况下期望 `ohos_executable` 进
  镜像。
- **不要**为绕过报错而修改 `subsystem_config.json` 把外部路径映射进来——它是
  全 OS 子系统注册表。
- **不要**改 `build/version.gni` 的 `api_version`/`sdk_version` 等版本号——版本
  与发布流程绑定。
- **不要**直接 import 单个模板文件；统一走 `import("//build/ohos.gni")`。
- **不要**绕过 `build/prebuilts_download.sh` 自行替换 prebuilts 工具链版本；
  Node 锁 v14.21.1，clang/python/node 版本是构建可复现的前提。

### 改动前必须请示（Ask before）

- 修改 `build/ohos.gni`、`build/templates/**` 的任一模板、`build/ohos_var.gni`
  已有参数的默认值、`build/subsystem_config.json`、`build/version.gni`、
  `build/OAT.xml`、`build/toolchain/**`。
- 任何影响产物 ABI / SDK / NDK / Notice / SBOM 输出格式或内容的改动。
- 任何新增/删除 `declare_args()` 或模板属性。
- 任何 license-sensitive 改动（白名单 `*_whitelist.json`、
  `third_party_allow_list.json`、`compile_*_whitelist.json`）。

### 不变量（Invariants）

- **依赖方向**：业务仓 `import` 本仓；本仓**不**反向 import 业务仓。模板之间
  的依赖须保持 `ohos.gni` 声明的顺序。
- **部件模型**：模块进镜像的三条件不可绕过——有 `part_name`、在部件
  `sub_component`（或被其依赖）、部件在产品部件列表中。
- **可复现构建**：prebuilts 版本、Node v14.21.1、`--gn-args`/`--ninja-args`
  默认值不可在无说明下偏移。
- **合规闭环**：引入/升级三方依赖须同步更新 Notice 与 OAT；新增源文件须带
  Huawei Device Co., Ltd. Apache-2.0 版权头（多数文件）。

### 常见 agent 失败模式（已知坑）

- 在 `build/` 目录内执行构建（应在源码树根目录）。
- 把子系统名当 `--build-target`，或仅传部件名导致找不到目标。
- 改了模板/参数后只跑单目标构建，未跑 `start_ex.sh template`/`option`，回归
  未被发现。
- 手改 `.pydeps` 等生成文件，下次构建被覆盖且产生 diff 噪声。
- 期望 `ohos_executable` 自动安装而未设 `install_enable = true`。
- 改 GN 参数默认值后未评估全 OS 影响（其他仓隐式依赖旧默认值）。

## 验证闭环

### 最小检查（任何改动后必跑）

1. **语法/导入**：对改动的 `.py` 跑 `python3 -m py_compile <file>`（本仓无
   统一 linter 配置；`hb` 用 `unittest`，至少保证可导入）。
2. **GN 生成**：`./build.sh --product-name rk3568 --build-only-gn`（或
   `hb build --build-only-gn`），确认 `gn gen` 不报错。
3. **相关测试套**：按下方「任务→测试」选择至少一套。

### 任务→测试

| 改动类型 | 验证命令 |
| --- | --- |
| GN 模板 (`build/templates/**`) | `bash build/test/script/start_ex.sh template` |
| 构建参数/选项 | `bash build/test/script/start_ex.sh option` |
| 性能相关 | `bash build/test/script/start_ex.sh performance` |
| `hb` Python 代码 | `build/hb/test/unitTest/` 下 `python3 -m unittest discover` |
| Rust 构建 | `--build-target //build/rust/tests:tests` |
| 端到端构建改动 | `./build.sh --product-name rk3568`（或对应产品）并确认镜像产出 |

### Done 定义

任务完成须满足：
1. 上述最小检查全部通过，且按改动类型跑了对应测试套。
2. 未触碰任何「不可破坏」项，或已获「改动前必须请示」的授权。
3. 未手改任何生成文件。
4. 若改了公共面（模板/参数/`subsystem_config.json`/`version.gni`），已说明
   兼容性影响。

### 最终回复须包含

- 改了什么（文件 + 简述）。
- 跑了哪些验证命令 + 结果。
- 命中了哪些约束（引用本文件「不可破坏/请示/不变量」条目）。
- 兼容性影响评估（若触及公共面）。
- 若无法验证：说明哪些命令已尝试、为何无法运行、建议人工补验什么。

### 验证无法运行时

若环境无法构建/测试（缺 prebuilts、无源码树根、无产品等），**不要**声称完成。
改为：列出已尝试命令与失败原因，明确标注「未验证」，并给出在正确环境应运行的
完整命令清单。

## 编辑前自检（必做）

动手编辑前，agent 须在心里/回复中明确：
1. **任务类别**：这是改模板 / 改参数 / 改 CLI / 改合规 / 改测试 / 还是其他？
2. **已读文档**：按「知识路由」加载了哪些 `docs/` 文件？
3. **命中约束**：本任务触及哪些「不可破坏/请示/不变量」条目？是否需要先请示？
4. **验证计划**：将跑哪些「任务→测试」命令？

## 约定

- 文档主要为中文（`docs/`、`README_zh.md`）；英文 PR 模板在 `.gitee/`。
- 仓库托管于 gitcode.com/openharmony/build（Gitee）。PR 模板（`.gitee/`）
  要求：Issue、Reason、Description、Test（本地测试）、cherry-pick 目标分支。
- 版权头：Huawei Device Co., Ltd.，Apache 2.0（多数文件）。
- API/版本：`build/version.gni`（api 26，sdk 26.0.0.x）。
