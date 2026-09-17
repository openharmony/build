# prebuilts 裁剪方案（wifiiot_hispark_pegasus + XTS acts）

## 1. 目标

当前 `build/prebuilts_download.sh` 会下载全量 prebuilts（本机实测 **23 GB**），
但目标场景只有两条命令：

```bash
python3 build.py -p wifiiot_hispark_pegasus@hisilicon -f -b release
rm -rf out && mkdir out && ./test/xts/tools/lite/build.sh product=wifiiot xts=acts
```

本方案给出**只保留这两条命令所需工具**的裁剪机制（`--build-level`），
`--build-level=L0` 实测下载约 **9.1 GB（约 -60%）**；其中 clang 桶内
跨架构 entry 约 6.6 G 本机不可执行（见 6.0 说明，当前仅做工具级裁剪）。

> `libcxx-ndk`（492 M）编译本身并不需要。原先走 `prebuilts_download.sh`
> 入口时须保留它（脚本结尾的 `update_llvm_ndk()` 在 `set -e` 下强依赖），
> 现已给该函数加了存在性守卫（见 6.0.1），`build_level` 标注可安全不含它。

> 注：XTS 那条命令内部循环调用的仍是
> `python build.py -p wifiiot_hispark_pegasus@hisilicon -f --test xts <module> --gn-args build_xts=true`
> （见 `test/xts/tools/lite/buildFun.sh:build_wifiiot`），
> 与第一条命令的工具链依赖完全一致，因此二者可合并为同一份依赖集。

## 2. 产品形态决定了依赖面

`vendor/hisilicon/hispark_pegasus/config.json`：

| 字段 | 值 |
| --- | --- |
| `type` | `mini` |
| `kernel_type` | `liteos_m` |
| `board` | `hispark_pegasus` (Hi3861, RISC-V) |

`device/board/hisilicon/hispark_pegasus/liteos_m/config.gni`：

```gni
board_toolchain      = "riscv32-unknown-elf"
board_toolchain_type = "gcc"
board_toolchain_path = ""          # ← 空：走系统 PATH
```

`build/config/BUILDCONFIG.gn:906` 对 `liteos_m` 置 `use_board_toolchain = true`，
于是 `set_default_toolchain("//build/lite/toolchain:riscv32-unknown-elf")`，
目标码编译器**完全来自 board 配置**，不走 `prebuilts/clang`。

**关键结论：RISC-V 交叉编译器来自系统 PATH（本机 `/home/tools/gcc_riscv32/bin`），
不在 prebuilts 内。`prebuilts/gcc` 是 ARM/AArch64 Linaro，与本产品无关。**

## 3. 必须保留的组件

| 组件 | 保留路径 | 依据 |
| --- | --- | --- |
| **python** | `prebuilts/python/linux-x86` | `build_scripts/build.py:52` 找不到即 `sys.exit()`；`hb/services/gn.py:105` 用它作 `--script-executable`；所有 action 脚本由它执行 |
| **gn** | `prebuilts/build-tools/linux-x86/bin/gn` | `hb/services/gn.py:88` |
| **ninja** | `prebuilts/build-tools/linux-x86/bin/ninja` | `hb/services/ninja.py:102` |
| **clang（仅 linux-x86_64/llvm）** | `prebuilts/clang/ohos/linux-x86_64/llvm` | host 侧 `clang_x64` toolchain 编译 `syscap_tool`；并提供 `libclang_rt.builtins.a` |

对应 `prebuilts_config.json` 中 `tag`：只需 **`base`**，且 `base` 内部还要按平台再裁。

### 3.1 python 第三方包

`prebuilts/python/.../site-packages` 中实际被 import 的：

| 包 | 使用点 |
| --- | --- |
| `prompt_toolkit` | `hb/services/menu.py`（`hb set` 交互菜单） |
| `pyyaml` | `hb/util/io_util.py:63`（`importlib` 动态导入） |
| `requests` | `build/prebuilts_service/pool_downloader.py:32`（下载器自身） |
| `psutil` | `build/dfx/build_tracker.py:192` |
| `json5` | `build/scripts/compile_app.py:23` |
| `networkx` / `packageurl` / `license-expression` | `build/ohos/sbom/*`（仅 `--sbom`） |

`jinja2` 来自 `third_party/jinja2`（`hb/util/loader/generate_targets_gn.py:26` 手动插 `sys.path`），
**不需要 pip 安装**。

`prebuilts_download.sh:241` 里的 `libclang`、`cryptography`、`asn1crypto`、
`idna`、`urllib3`、`typing_extensions`、`uv` 在 build 目录内**搜不到任何 importer**，
属于可裁项（本方案保守保留，仅记录）。

## 4. 可裁组件（已实测验证）

| 组件 | 体积 | 裁剪理由 |
| --- | --- | --- |
| `cangjie_sdk` | 3.5 G | 仓颉；`test_ohos_cangjie_unittest` 仅 `device_name == "rk3568"` |
| `ark_tools` | 1.7 G | ArkCompiler AOT / ark_js；mini 系统无 JS 运行时 |
| `gcc` | 1.4 G | ARM/AArch64 Linaro，非 RISC-V |
| `rustc` | 1.2 G | `test_rust_template` 仅 `device_name == "rk3568"`（`ohos/packages/BUILD.gn:743`） |
| `tool`（hvigor+ohpm） | 1010 M | HAP/应用构建，mini 系统无 HAP |
| `js_rawheap_translator` | 516 M | JS 堆分析 |
| `cmake` | 510 M | Hi3861 用 **scons**（`sdk_liteos/build.sh`），非 cmake |
| `mingw-w64` | 459 M | Windows 交叉编译 |
| `python_llvm` | 110 M | LLVM 自举专用 |
| `develop_tools` | 32 M | bpftool / pahole，liteos_m 无 eBPF |
| `packing_tool` | 6.2 M | HAP 打包 |
| clang 非 x86_64 变体 | ~8.1 G | `linux-aarch64` / `ohos-arm64` / `windows-x86_64` |
| `clang/.../libcxx-ndk` + `llvm_ndk` | ~560 M | NDK/HAP native，`cxx.gni:1321` 仅 `defined(invoker.stl)` 时引用 |
| `build-tools/common/{js-framework,ts2abc}` | 377 M | JS 框架 / ts2abc |
| **`build-tools/common/nodejs`** | 380 M | **实测全量编译无 Node.js 通过** |
| `build-tools/{linux-aarch64,ohos,windows-x86}` | ~5 M | 非本机架构 |

## 5. 实测验证

方法：把候选组件移出 `prebuilts/`，`rm -rf out` 后跑完整命令。

| 轮次 | prebuilts 状态 | 体积 | 结果 |
| --- | --- | --- | --- |
| 基线 | 全量 | 23 G | 1181 目标生成 / 1089 编译，1 处失败：`run_wifiiot_scons` |
| 第 1 轮 | 移除 10 个顶层目录 | ~13 G | 同样 1 处失败，位置一致 |
| 第 2 轮 | 再移除 clang 三变体 / nodejs 16+18 / js-framework / ts2abc / libcxx-ndk / llvm_ndk / tool | ~3 G | **1181/1181 生成，1110 编译**，同样 1 处失败 |
| 第 3 轮 | 再移除 **整个 nodejs** | — | `--build-only-gn` EXIT=0；全量 1089/1181，同样 1 处失败 |
| **终轮** | **手工保留编译最小集（不含 libcxx-ndk）** | **2.7 G** | **1089/1181，与基线逐目标一致，同样 1 处失败** |

> 本表是**手工裁剪的历史实测记录**，证明最小集可编译；当前
> `--build-level=L0` 为工具级裁剪，产物约 9.1 G（见 6.0 的差异说明）。

终轮 `prebuilts/`（编译最小集，实测通过）：

```
2.7G  prebuilts/          ← 对比基线 23 G，-88%
  2.5G  clang/ohos/linux-x86_64/llvm
  202M  python/linux-x86
  3.3M  build-tools/linux-x86/bin  (gn + ninja)
```

（历史上走 `prebuilts_download.sh` 入口时须额外保留 `libcxx-ndk`（492 M），
`update_llvm_ndk()` 加守卫后不再需要，见 6.0.1。）

**唯一失败点在全部 5 轮中完全相同（含全量基线），与 prebuilts 无关：**

```
ModuleNotFoundError: No module named 'tools.nvtool'
  File ".../sdk_liteos/SConstruct", line 36
```

### 5.1 该失败的根因（已定位，非本方案引入）

`SConstruct:29` 用 `sys.path.insert(0, os.getcwd())` 加载仓内 `tools/nvtool`。
仓内 `tools/` 与 `tools/nvtool/` **都没有 `__init__.py`**，只能作为
PEP 420 命名空间包被导入；而本机 `scons` 是
`/home/blueyouth/anaconda3/bin/scons`（shebang 指向 anaconda python），
其 `site-packages/tools/` **有 `__init__.py`**。

Python 导入规则：**常规包（有 `__init__.py`）优先于命名空间包**，
且常规包一旦命中就固定 `__path__`，不再合并其他目录。
因此 `tools` 被解析成 anaconda 那个无关的包，`tools.nvtool` 自然找不到。

实测对照（同一目录、同一 `sys.path` 前缀）：

```bash
cd device/soc/hisilicon/hi3861v100/sdk_liteos

# anaconda python：被 site-packages/tools 抢占
/home/blueyouth/anaconda3/bin/python -c "import importlib.util,sys; \
  sys.path.insert(0,'.'); print(importlib.util.find_spec('tools').origin)"
# -> /home/blueyouth/anaconda3/lib/python3.12/site-packages/tools/__init__.py
#    → ModuleNotFoundError: No module named 'tools.nvtool'

# 预置 python：正确解析为命名空间包
<repo>/prebuilts/python/linux-x86/3.12.10/bin/python3 -c "import importlib.util,sys; \
  sys.path.insert(0,'.'); print(importlib.util.find_spec('tools').origin)"
# -> None  (namespace package, 指向仓内 tools/)
#    → import tools.nvtool.build_nv  →  OK
```

**结论：环境问题（anaconda 的 `scons` + `tools` 包污染 `PATH`/`sys.path`），
与 prebuilts 裁剪无关。** 规避方式（任选其一，本方案不代为修改）：

- 让 `PATH` 中预置 python 优先，并用它安装/调用 scons；
- 或在构建 shell 中屏蔽 anaconda（`conda deactivate` / 移出 `PATH`）；
- 或给仓内 `tools/` 与 `tools/nvtool/` 补 `__init__.py`（改动 vendor 代码，需另行评审）。

## 6. 实施方式

### 6.0 `--build-level` 参数 + `build_level` 字段

**架构：仿照 `build_type` 的三件套模式（配置字段 + 命令行参数 + Filter 方法），
直接在共享配置 `prebuilts_config.json` 内标注，无独立配置文件、无外部过滤脚本。**

方案演进：最初每产品一份完整 `prebuilts_config_*.json`（与全量配置同构，
重复大）→ 中间版"共享配置 + 三份工具列表 json + `prebuilts_tools_filter.py`
过滤脚本"→ 最终收敛为本方案（三份 json 与过滤脚本均已删除）。

三层机制：

1. **配置标注**（`build/prebuilts_config.json`）：**工具级**标注
   `build_level` 字段，多形态用逗号分隔（如 `"L0,L1"`）；
   **未标注 = 仅全量下载**。当前标注：L0 = gn / ninja / clang / python（wifiiot）；
   L1 = 追加 packaging_tool、gcc（taurus 两形态合并，
   见 `prebuilts_pruning_taurus.md`）。
2. **命令行参数**：`prebuilts_download.sh --build-level=(L0|L1)`
   （大小写不敏感，空格/等号双形式；非法值报错退出 1），透传给
   `prebuilts_config.py --build-level`。
3. **过滤实现**（`prebuilts_service/config_parser.py`）：
   `Filter.filter_build_level` / `Filter.level_match` 与 `filter_tag` /
   `filter_build_type` 并链。**不带参数时不介入**，全量行为逐字节不变
   （实测 56 项与基线一致）。

**过滤语义（当前仅工具级；entry 级机制保留、由配置驱动）**：

| 层级 | 状态 | 行为 |
| --- | --- | --- |
| 工具门禁 | **生效** | `get_operate` → `_apply_filters`：工具自身字段不含目标形态（或无字段）→ 整个工具跳过 |
| entry 筛选 | **配置未启用** | 工具过门禁后，其当前 host 桶内**全部 entry** 下载。`filter_build_level` 对 merge 后配置恒真（entry 未标注时继承工具级值，而该值已通过门禁） |

> entry 级裁剪的机制仍然保留：`Filter` 对 merge 后配置的 `build_level`
> 过滤链并未移除，将来若给某个 entry 标注 `build_level`，该 entry 的
> 按形态筛选立即生效（配置驱动，零代码改动）。

**当前仅工具级裁剪的代价**：上游配置把跨架构 entry（"全家桶"分发策略）
混在本机桶里——clang 的 `linux/x86_64` 桶含 ohos-arm64 / windows /
linux-aarch64 共约 6.6 G，本机无法执行但仍会下载。实测 `--build-level=L0`
产物约 9.1 G（对比第 5 节手工最小集 2.7 G）；若需回到最小集，
给本机 entry 标注 `build_level` 即可（见上表机制说明）。

用法：

```bash
# 全量（原行为，逐字节不变）
./build/prebuilts_download.sh

# 精简（wifiiot，约 9.1 G）
./build/prebuilts_download.sh --build-level=L0
```

### 6.0.1 `update_llvm_ndk()` 已加存在性守卫（`libcxx-ndk` 可裁）

`prebuilts_download.sh` 结尾在 `set -e` 下无条件调用 `update_llvm_ndk()`，
其中 `cp -rfp "${llvm_dir}/libcxx-ndk/include" ...` 在缺包时直接导致脚本非零退出——
这是历史上工具列表被迫保留 `libcxx-ndk`（492 M）的原因。

现已给该函数加了存在性守卫：

```bash
function update_llvm_ndk(){
if [ ! -d "${llvm_dir}/libcxx-ndk" ];then
    echo "skip update llvm ndk: libcxx-ndk not found"
    return 0
fi
...
}
```

- **标准系统（有包）行为不变**：正常执行 merge，产出 `llvm_ndk/`；
- **精简场景（无包）**：打印 skip 提示后跳过，脚本正常退出。

wifiiot **编译过程本身不需要** `libcxx-ndk`（第 4 节已实测），
故 `build_level` 标注不含它（L0/L1 下不下载）。

> 注意：若后续要切回标准系统/HAP native 构建（`llvm_ndk` 被
> `cxx.gni` 在 `defined(invoker.stl)` 时引用），需重跑全量下载补回。

### 6.0.2 nodejs 会被脚本无条件删除

`prebuilts_download.sh:217` 在下载前无条件执行：

```bash
if [ -d "${code_dir}/prebuilts/build-tools/common/nodejs" ];then
    rm -rf "${code_dir}/prebuilts/build-tools/common/nodejs"
fi
```

`node` 工具未标注 `build_level`，`--build-level` 模式下不会下载，且脚本仍会
无条件删除已存在的 `nodejs` 目录。对本场景无影响（第 5 节已实测：无 Node.js
全量编译通过），但若之后要切回标准系统/HAP 构建，需重跑全量下载恢复。

`--build-level=L0` 解析结果（实测，x86_64 / linux / build_type=src）：

```
download items : 12     → gn(2), ninja(4), clang(4), python(2)，桶内全部 entry
other operates : 3      → clang:move×4, clang:symlink×4, python:symlink
```

arm64 host 亦已验证可正确解析到 `linux-aarch64` / `linux-arm64` 桶；
darwin + L0 下载 darwin 桶 entry（4 项），mac 构建机可用。

### 6.0.3 预置 python 的 pip 包按形态裁剪

`prebuilts_download.sh` 安装进**预置 python** 的 pip 包（原 15 个，带版本 pin）
也按 `--build-level` 裁剪：

```bash
case "${BUILD_LEVEL}" in
    L0|L1)
    prebuilt_pip_packages="idna>=3.7 urllib3>=1.26.29 pyyaml>=6.0.2 \
requests>=2.32.1 prompt_toolkit==1.0.14 json5==0.9.6 psutil"   # 7 个
    ;;
    *)
    prebuilt_pip_packages="<原 15 包全量>"
    ;;
esac
```

裁剪依据（importer 全仓复核）：L0/L1（mini/small 系统）**不需要**
`libclang`（55 M，仅 rust bindgen）、SBOM 三件套 `networkx` /
`packageurl-python` / `license-expression`（17.4 M，`--sbom` 标准系统特性）、
以及无 importer 的 `cryptography` / `asn1crypto` / `typing_extensions` /
`uv`——共省约 78 M 与首装时间。保留 7 个为构建框架公共依赖
（hb CLI、下载器、DFx 埋点所需）。

> venv 内给下载器自身的安装（`requests` `cryptography`）不随形态变化：
> venv 是临时的（脚本退出即删，零持久占用），`requests` 是
> `pool_downloader` 的硬依赖。

已用**真实脚本入口**端到端跑通（prebuilts 从零开始）：

```bash
./build/prebuilts_download.sh --build-level=L0 --disable-rich
# EXIT=0；输出 "start download prebuilts, total 12"
#              "======copy inside cxx finished!======"
#              "skip update llvm ndk: libcxx-ndk not found"
```

### 6.1 为什么不用 `--part-names` / tag 过滤

`--part-names` 走 `get_parts_tag_config()`（`part_prebuilts_config.py`），
是**独立编译（indep）**用的部件→tag 映射，`build_type` 为 `indep`；
本场景是 `src` 全量编译，二者过滤链不同，用独立 config 文件更直接、副作用最小。

另外 `tag` 粒度不够：`node`/`cmake`/`gcc`/`mingw`/`bpftool`/`pahole`/
`ark_tools_llvm_aot`/`python_llvm`/`libcxx-ndk` 与 `gn`/`ninja`/`clang`/`python`
**同属 `tag=base`**，无法只靠 tag 把它们分开，必须落到工具/entry 级裁剪。
`build_type` 也无法复用：它是"集合交集"语义（命中即取）且无字段=保留，
而 `build_level` 需要"未标注=排除"的层级语义（见 6.0 过滤语义表）。

### 6.2 注意事项

1. **`build.sh` 与 `build.py` 是两条不同入口。**
   `build.py`（本场景使用）直接 `exec` `build/hb/main.py`（`build_scripts/build.py:84`），
   **不经过** `build_scripts/build.sh`，因此
   `build.sh:117-121` 的 Node.js 版本校验、`chmod hvigorw`、`init_ohpm`
   在本场景**不会触发**，无需为裁剪打补丁。
   若改用 `./build.sh`，则删掉 `prebuilts/tool` 后需同步处理这几行。

2. **`hb` 的自动重下只在 indep 路径。**
   `PreuiltsService`（`hb/services/prebuilts.py`）只在
   `_init_indep_build_module()` 中实例化（`hb/main.py:238`），
   `src` 全量编译不会触发；`--skip-prebuilts` 也只对 indep 生效。

3. **完整性以 `.mark` 文件为准，不是目录名。**
   `pool_downloader` 通过 `<remote_sha256>.<unzip_filename>.mark` 判断是否已解压
   （`download_util.py:46`）。手工挪动/解压后若缺 mark，下次会重下并
   **先 `rm -rf` 目标目录**（`pool_downloader.py:118-122`）——
   这会静默覆盖手工放回的内容，务必连 mark 一起处理。

4. **本地缓存独立于 `prebuilts/`。**
   压缩包缓存在 `download_root`（`src` → `../openharmony_prebuilts`）。
   删除 `prebuilts/` 子目录不会删缓存，重新下载时命中缓存、无需走网络。

### 6.3 回退

```bash
./build/prebuilts_download.sh            # 不带 --build-level＝原全量行为，补齐所有缺失项
```

已存在的条目靠 `.mark` 跳过，只补缺失项；压缩包命中本地缓存，通常无需走网络。

若要彻底移除本方案：清除 `prebuilts_config.json` 中的 `build_level` 标注，
并回滚 `--build-level` 相关代码改动（`prebuilts_download.sh` /
`prebuilts_config.py` / `config_parser.py`，见 6.0）即可。

## 7. 交付物

| 文件 | 改动类型 | 说明 |
| --- | --- | --- |
| `build/prebuilts_config.json` | **修改** | 6 工具标注 `build_level`（+6 行纯插入：L0 = gn/ninja/clang/python，L1 追加 packaging_tool/gcc） |
| `build/prebuilts_config.py` | **修改** | argparse 新增 `--build-level` 参数 |
| `build/prebuilts_download.sh` | **修改** | 新增 `--build-level` 参数解析与校验（`L0|L1`，大小写不敏感）；预置 python pip 包按形态裁剪（L0/L1 装精简 7 包，其余全量 15 包）；`update_llvm_ndk()` 加存在性守卫（缺 `libcxx-ndk` 时跳过而非退出） |
| `build/prebuilts_service/config_parser.py` | **修改** | `Filter.filter_build_level` / `level_match`；`_apply_filters` 链挂载（工具级门禁） |
| `build/docs/prebuilts_pruning_wifiiot.md` | **新增** | 本文档 |

已删除（早期方案产物）：三份工具列表 json
（`prebuilts_config_{wifiiot,taurus,taurus_linux}.json`）与
`prebuilts_tools_filter.py` 过滤脚本。

### 兼容性影响

- **不带 `--build-level` 时行为逐字节不变**：全量解析实测 56 项、15 个
  pip 包，与基线一致。
- `--build-level` 只做"减法"（过滤未标注/不含形态的工具，精简 pip 包集），
  不改任何下载地址、handle 逻辑与后处理；entry 级过滤机制保留但未启用
  （见 6.0）。
- 未触碰 `ohos.gni`、GN 模板、`declare_args()`、`subsystem_config.json`、
  `version.gni`、`OAT.xml`、`toolchain/**`，不涉及 ABI / SDK / NDK / Notice / SBOM 输出。

