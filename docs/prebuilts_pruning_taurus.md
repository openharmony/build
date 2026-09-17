# prebuilts 裁剪方案（ipcamera_hispark_taurus + ipcamera_hispark_taurus_linux）

## 1. 目标

两条编译命令：

```bash
# cmd1: liteos_a 内核，带 XTS 测试
python3 build.py -p ipcamera_hispark_taurus@hisilicon -f -c clang --gn-args build_xts=true

# cmd2: linux-5.10 内核
python3 build.py -p ipcamera_hispark_taurus_linux@hisilicon -f -c clang --gn-args linux_kernel_version=linux-5.10
```

对 `build/prebuilts_download.sh` 做裁剪，只保留上述命令依赖的组件。

## 2. 产品形态

| 字段 | cmd1 | cmd2 |
| --- | --- | --- |
| 产品 | `ipcamera_hispark_taurus` | `ipcamera_hispark_taurus_linux` |
| 类型 | `small` | `small` |
| 内核 | `liteos_a` | `linux` |
| 板级 | `hispark_taurus` (cortex-a7) | 同左 |
| 工具链 | `clang`（默认 ohos-clang） | `clang` + `gcc` binutils |
| 额外驱动 | `sdk_liteos/mpp`（预编译 .so 拷贝） | `sdk_linux/drv`（需 gcc 交叉编译） |

## 3. 必须保留的组件

### 3.1 两条命令共享

| 组件 | 保留路径 | 原因 |
| --- | --- | --- |
| **python** | `prebuilts/python/linux-x86` | `build_scripts/build.py:52`；`--script-executable`；所有 action 脚本 |
| **gn** | `prebuilts/build-tools/linux-x86/bin/gn` | `hb/services/gn.py:88` |
| **ninja** | `prebuilts/build-tools/linux-x86/bin/ninja` | `hb/services/ninja.py:102` |
| **clang/llvm** | `prebuilts/clang/ohos/linux-x86_64/llvm` | host 侧 clang_x64 toolchain + 目标侧 clang |
| **packing_tool** | `prebuilts/packing_tool` | `developtools/packing_tool/haptobin.sh` 编译 Java 工具时引用 `fastjson` 等 jar 包 |

> `libcxx-ndk`（492 M）原先因 `prebuilts_download.sh` 结尾 `update_llvm_ndk()`
> 在 `set -e` 下强依赖而被迫保留；该函数已加存在性守卫（见 wifiiot 方案
> 6.0.1 节），`build_level` 标注不含它。

### 3.2 cmd2 额外需要

| 组件 | 保留路径 | 原因 |
| --- | --- | --- |
| **gcc (ARM Linaro)** | `prebuilts/gcc/linux-x86/arm/gcc-linaro-7.5.0-arm-linux-gnueabi` | `kernel/linux/build/kernel.mk:38` 用 `arm-linux-gnueabi-` 做 `CROSS_COMPILE`（`CC` 是 clang，但 `as`/`ar`/`ld` 等 binutils 用 gcc 工具链）；`device/soc/hisilicon/hi3516dv300/sdk_linux/drv/mpp/Makefile.linux.param:129` 在 `OHOS_LITE=y` 时走裸 `CROSS_COMPILE=arm-linux-gnueabi-` |
| | | 实测：移除此项后内核编译失败 `scripts/Kconfig.include:40: linker not found`；补回后通过 |

### 3.3 cmd1 不需要 gcc 的实证

`device/board/hisilicon/hispark_taurus/BUILD.gn:11-13` 显示 liteos_a 走 `sdk_liteos/mpp:copy_mpp_libs`（纯预编译 `.so` 拷贝），只有 `ohos_kernel_type=="linux"` 才拉 `sdk_linux`（其 Makefile 引用 gcc）。

实测：将 `prebuilts/gcc` 整个移出后，`rm -rf out` 重新编译，cmd1 仍 **EXIT=0, 9247/9247**，产出 `OHOS_Image.bin`（6.6 MB）。

## 4. 可裁组件

与 wifiiot 方案相同（见 `prebuilts_pruning_wifiiot.md` 第 4 节），再加以下用于 taurus 但**已验证不依赖**的组件：

| 组件 | 体积 | 理由 |
| --- | --- | --- |
| `prebuilts/gcc`（对 cmd1） | 1.4 G | 实测移出后 liteos_a 全量编译通过 |
| clang 非 x86_64 变体 | ~8.1 G | 只用了 linux-x86_64 |
| `build-tools/common/{js-framework,ts2abc,nodejs}` | 757 M | 无 JS/HAP 构建 |
| `build-tools/{linux-aarch64,ohos,windows-x86}` | ~5 M | 非本机架构 |

## 5. 实测验证

### 5.1 环境前提

修复了目标环境两类问题（均与 prebuilts 裁剪无关）：

1. **`/bin/sh` → dash**：`kernel/liteos_a/fs/jffs2/BUILD.gn:41` 用 `pushd`（bash 内建），dash 无此命令 → `Returned 127`；`third_party/musl/scripts/build_lite/Makefile:98` 用 `[^p]*` 取反通配，dash 不支持 → 只拷进 `porting` 漏掉 `include/`。已修复：`sudo ln -sf /bin/bash /bin/sh`。

2. **缺失 apt 包**：`kernel/liteos_a/Makefile:40` 通过 `eval` 解析 `hb env` 输出，当系统缺包时 `hb env` 会多输出一行不含 `=` 的提示 → make 报 `missing separator`。本机缺 `gcc-arm-none-eabi mtd-utils mtools scons u-boot-tools` 共 5 包。未安装的情况下，cmd1 仍可绕过此问题编译（该 Makefile 只影响 `hb env` 子命令，不影响 `build.py` 的直接调用）。

3. **`prebuilts/gcc` bin 需在 PATH**：cmd2 的 sdk_linux Makefile 在 `OHOS_LITE=y` 时走裸 `CROSS_COMPILE=arm-linux-gnueabi-`（无路径），若 `$GCCBIN` 不在 PATH 则回退到 `/usr/bin/as`，报 `-EL unrecognized option`。需在编译前执行：

```bash
export GCCBIN=$(pwd)/prebuilts/gcc/linux-x86/arm/gcc-linaro-7.5.0-arm-linux-gnueabi/bin
PATH=$GCCBIN:$PATH python3 build.py ...
```

### 5.2 验证结果

| 命令 | 配置 | 结果 | 产物 |
| --- | --- | --- | --- |
| cmd1 (liteos_a) | `config_taurus.json`，`prebuilts/gcc` 移出 | **EXIT=0, 9247/9247** | `OHOS_Image.bin` (6.6 MB) |
| cmd2 (linux) | `config_taurus_linux.json`，含 gcc | **EXIT=0, 2480/2480** | `uImage_hispark_taurus_smp` (5.4 MB), `rootfs_ext4.img`, `userfs_ext4.img` |

### 5.3 未验证项

- XTS 测试命令（`./test/xts/tools/lite/build.sh product=ipcamera xts=acts`）未验证——该脚本逻辑与 wifiiot 不同，可执行 `build_common` 路径，但需额外的 apt 包（`mtd-utils` 等）支撑镜像打包。
- `prebuilts_download.sh` 对 `--build-level` 参数的支持已在 wifiiot 方案中验证；本方案复用同一套代码，无需重复验证。

## 6. 实施方式

### 6.0 完整下载面审计

`build/prebuilts_download.sh` 及其调用的全部下载面，按优先级排序：

| 下载面 | 入口 | 是否受 `--build-level` 控制 | 对 taurus 裁剪方案的影响 |
| --- | --- | --- | --- |
| **`prebuilts_config.py`** 下载 tarball | `prebuilts_download.sh:231`，调用 `prebuilts_config.py` | **是** | 核心裁剪目标。`--build-level=L1` 从 56 项降到 6 项 |
| **`prebuilts_download.py`**（`BUILD_ARKUIX=YES` 时） | `prebuilts_download.sh:233` | **否**（该入口无 `--build-level`） | 不触发。`--build-arkuix` 未使用 |
| **`prebuilts.sh` 钩子**（`--tool-repo` 时） | `prebuilts_download.sh:19-21` | 不适用（整脚本替换） | 不触发。`prebuilts.sh` 不存在 |
| **venv pip 安装**（`rich`、`requests`、`cryptography`） | `prebuilts_download.sh:186/194/229` | **否**，固定执行 | 约 5 MB，idempotent，无需裁剪 |
| **预置 Python pip 安装**（15 个包） | `prebuilts_download.sh` | **是**（L0/L1 时只装精简 7 包） | L1 下约 20 MB（hb CLI / 下载器 / DFx 埋点所需）；`libclang`、SBOM 三件套及无 importer 的包被裁掉（见 wifiiot 方案 6.0.3），idempotent |
| **SDK 下载**（`--download-sdk` 时） | `prebuilts_download.sh:260-263` | 受 `--download-sdk` 开关控制 | 不触发。未传递该参数 |
| **`npm_install` / `node_modules_copy`** | `prebuilts_config.json` 中 `tool_list` 的 handle | **是**（未标注 `build_level` 的工具不执行） | 已排除。`npm_install` 条目无标注 |
| **`hpm_download`** | `prebuilts_config.json` 中 `tool_list` 的 handle | **是**（`build_type=indep` 时才触发） | 已排除。本场景 `build_type=src` |

**结论：`prebuilts_config.py` 是唯一需要裁剪的下载面，本次已覆盖。** 其余固定下载面（pip 安装）累计约 60 MB，与 23G→4.1G 的裁剪幅度相比可忽略，且 idempotent（已有缓存则跳过）。

#### 6.0.1 `npm_install`：`prebuilts/` 之外的最大下载面

全量配置里 `npm_install` 条目会对 **16 个目录**逐个执行真实的 `npm install`
（`build/prebuilts_service/common_utils.py:291-326`）：

```
developtools/ace_ets2bundle/compiler        third_party/jsframework
developtools/ace_js2bundle/ace-loader       third_party/parse5/packages/parse5
third_party/weex-loader                     interface/sdk-js/build-tools
arkcompiler/ets_frontend/legacy_bin/api8    arkcompiler/ets_frontend/arkguard
... 另有 8 个 ets2panda / koala-wrapper / arkui-plugins 等目录
```

这里有三点值得注意：

1. **产物不落在 `prebuilts/` 里**，而是散落在各源码目录的 `node_modules/`。
   本机实测已存在的 7 个目录合计 **756 MB**，另有 `~/.npm` 缓存 **381 MB**、
   `~/.hvigor` **36 MB**。所以只看 `du -sh prebuilts` 会**低估**全量下载的真实成本。

 2. **强依赖 `prebuilts/build-tools/common/nodejs`**（`common_utils.py:293` 硬编码
    `nodejs/current/bin/npm`）。而 taurus/wifiiot 的 `build_level` 标注都不含
    `node` —— 两者是自洽的：不装 nodejs 就不该跑 npm_install。

 3. **`--build-level=L1` 已自动排除它**。实测解析结果对比：

    | 配置 | download 项 | handle 类型 |
    | --- | --- | --- |
    | `prebuilts_config.json`（全量） | 56 | `move`, `symlink`, `remove`, **`npm_install`**, **`node_modules_copy`**, **`shell`** |
    | `--build-level=L1`（taurus 两形态合并） | 15 | `move`, `symlink`, `remove` |

    L1 的 handle 里**没有** `npm_install` / `node_modules_copy` / `shell`，
    即这三类副作用完全不会发生。

> 补充：全量配置中 `python` 与 `hvigor` 的 `shell` handle 都带
> `"when": "current_build_type.strip() != 'src'"` 守卫，`src` 构建下本就不执行；
> `rust` 的 `install.sh` 则随 `rust` 条目一起被裁掉。

### 6.1 文件

无独立配置文件——`build_level` 标注直接写在共享配置
`build/prebuilts_config.json` 中（**工具级**）：L1 = `packaging_tool` 与
`gcc`（各 `"L1"`，gcc 含 ARM/AArch64 两个交叉工具链 entry，桶内全下）；
其余 L0 部分（gn/ninja/clang/python）与 wifiiot 共用。

过滤实现与 `build/prebuilts_download.sh` 的 `--build-level` 参数
与 wifiiot 方案共用（见 `prebuilts_pruning_wifiiot.md` 第 6.0 节）。

### 6.2 修改既有文件

与 wifiiot 方案共用同一批代码改动：`prebuilts_config.json`（标注）、
`prebuilts_config.py`（参数）、`config_parser.py`（Filter）、
`prebuilts_download.sh`（参数解析）
（见 `prebuilts_pruning_wifiiot.md` 第 6.0 节与第 7 节）。

### 6.3 策略选择：合并为单形态 L1

早期方案曾按 liteos_a / linux 分成两份配置（差 1.4 G 的 gcc）；
`--build-level` 方案下**两者合并为同一形态 L1**（取并集）：

```bash
# cmd1 (liteos_a) 与 cmd2 (linux) 共用 — 约 10.5 G
#（clang 桶内跨架构 entry 约 6.6 G 本机不可执行，见 wifiiot 方案 6.0 说明）
./build/prebuilts_download.sh --build-level=L1

# cmd2 编译时需将 prebuilts/gcc/bin 加入 PATH（见 5.1）
```

取舍：cmd1 场景多下约 1.4 G 无用的 gcc，换取"一个形态管两个内核形态"的
运维简洁性。若后续需要拆分，可为 gcc 单独引入更细的形态值（如 `L1L`），
机制无需改动。

### 6.4 注意事项

1. **cmd2 需要 `prebuilts/gcc/bin` 在 PATH 中**，否则 sdk_linux 的 Makefile 会回退到 `/usr/bin/as`（报 `-EL unrecognized option`）。建议在编译脚本中显式设置：

```bash
export GCCBIN=$(pwd)/prebuilts/gcc/linux-x86/arm/gcc-linaro-7.5.0-arm-linux-gnueabi/bin
PATH=$GCCBIN:$PATH python3 build.py -p ipcamera_hispark_taurus_linux@hisilicon -f -c clang --gn-args linux_kernel_version=linux-5.10
```

2. 预置 python 的 scons 安装（`tools.nvtool` 遮蔽问题，见 `prebuilts_pruning_wifiiot.md` 5.1 节）对 taurus 的 liteos_a 内核无影响，但 cmd2 的 sdk_linux 不使用 scons，无需处理。

### 6.5 回退

```bash
./build/prebuilts_download.sh   # 不带参数＝全量下载
```