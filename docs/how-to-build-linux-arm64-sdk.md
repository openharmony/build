# Linux ARM64 SDK 交叉编译指南

本文档说明如何在 x86_64 主机上交叉编译 linux-arm64 平台的 OpenHarmony SDK。

## 环境要求

### 硬件要求

- 磁盘可用空间：**40GB 以上**（编译产物较大，建议将源码放在大容量磁盘分区上）
- 内存：16GB 以上
- 如果系统盘空间有限，需设置 `TMPDIR` 环境变量指向大容量磁盘分区

### 操作系统

- Ubuntu 22.04 LTS（推荐）

### 安装交叉编译工具链

编译 linux-arm64 SDK 需要安装 aarch64 交叉编译工具链：

```bash
sudo apt-get install -y gcc-aarch64-linux-gnu g++-aarch64-linux-gnu
```

安装后验证：

```bash
aarch64-linux-gnu-gcc --version
ls /usr/aarch64-linux-gnu/include/c++/
```

> 注意：构建系统会自动检测已安装的 gcc 版本号（如 7、11 等），无需手动配置。

## 编译命令

### 编译 linux-arm64 SDK

```bash
./build.sh --product-name ohos-sdk --build-target ohos_sdk --gn-args sdk_platform=arm64
```

## 产物路径

编译完成后，产物位于：

```
out/sdk/packages/ohos-sdk/linux-arm64/
```

主要目录结构：

```
linux-arm64/
├── native/
│   ├── llvm/              # LLVM 工具链
│   │   ├── bin/           # 编译器等工具
│   │   ├── lib/           # 库文件
│   │   └── include/       # 头文件
│   ├── sysroot/           # 系统根目录
│   └── build-tools/       # 构建工具（cmake, ninja 等）
```


## 相关文件

| 文件路径 | 说明 |
|---------|------|
| `build/ohos_var.gni` | sdk_platform 参数定义 |
| `build/ohos/sdk/sdk.gni` | SDK 平台列表控制 |
| `build/config/sysroot.gni` | 交叉编译 sysroot 配置 |
| `build/config/posix/BUILD.gn` | 交叉编译头文件和库路径 |
| `build/toolchain/linux/BUILD.gn` | 工具链前缀配置 |
| `build/prebuilts_download.sh` | 预置包下载 |
