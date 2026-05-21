# bundle.json 条件编译配置指导

## 概述

bundle.json 条件编译功能允许 bundle 开发人员根据构建上下文动态选择要编译的模块、inner_kits 和测试用例。这样可以实现同一份 bundle.json 配置在不同构建场景下产生不同的编译结果，提高配置的复用性和灵活性。

## 功能特性

- 支持多种构建条件属性：compile_mode、target_os、target_cpu、os_level 等
- 可应用于 sub_component、modules、group_type、inner_kits、inner_api、test 等配置项
- 支持单值和列表值匹配
- 提供清晰的警告信息，帮助定位配置问题

## 条件上下文属性

构建系统提供以下条件属性供使用：

| 属性 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| compile_mode | string | 编译模式 | "target", "host" |
| target_os | string | 目标操作系统 | "ohos", "linux" |
| target_cpu | string | 目标CPU架构 | "arm64", "x86_64" |
| os_level | string | 系统级别 | "mini", "small", "standard" |

## 配置格式

在 bundle.json 的 `component.build` 中添加 `conditions` 字段：

```json
{
  "component": {
    "name": "component_name",
    "build": {
      "conditions": {
        "item_name": {
          "attribute": "value"
        }
      }
    }
  }
}
```

### 条件表达式语法

条件表达式是一个键值对对象，支持以下格式：

1. **单值匹配**：属性值必须完全匹配
```json
{
  "compile_mode": "target"
}
```

2. **列表值匹配**：属性值在列表中即匹配
```json
{
  "target_cpu": ["arm64", "arm"]
}
```

3. **多条件组合**：所有条件都必须满足（AND 逻辑）
```json
{
  "compile_mode": "target",
  "target_cpu": ["arm64", "arm"]
}
```

## 应用场景

### 场景1：模块条件编译

仅在目标编译模式下编译特定模块：

```json
{
  "component": {
    "name": "demo_component",
    "build": {
      "conditions": {
        "module_a": {
          "compile_mode": "target"
        },
        "module_b": {
          "compile_mode": "host"
        }
      },
      "sub_component": [
        "module_a",
        "module_b",
        "module_common"
      ]
    }
  }
}
```

### 场景2：inner_kits 条件导出

根据系统级别导出不同的 inner_kits：

```json
{
  "component": {
    "name": "media_component",
    "build": {
      "conditions": {
        "advanced_codec_kit": {
          "os_level": "standard"
        }
      },
      "inner_kits": [
        {
          "name": "basic_codec_kit",
          "header": "./include/basic_codec.h"
        },
        {
          "name": "advanced_codec_kit",
          "header": "./include/advanced_codec.h"
        }
      ]
    }
  }
}
```

### 场景3：CPU 架构相关模块

为不同 CPU 架构提供不同的模块实现：

```json
{
  "component": {
    "name": "hardware_component",
    "build": {
      "conditions": {
        "arm_optimized": {
          "target_cpu": ["arm64", "arm"]
        },
        "x86_optimized": {
          "target_cpu": "x86_64"
        }
      },
      "sub_component": [
        "arm_optimized",
        "x86_optimized",
        "common_code"
      ]
    }
  }
}
```

### 场景4：测试用例条件编译

仅在特定配置下运行测试：

```json
{
  "component": {
    "name": "network_component",
    "build": {
      "conditions": {
        "integration_test": {
          "compile_mode": "target",
          "os_level": "standard"
        },
        "unit_test": {
          "compile_mode": "host"
        }
      },
      "test": [
        "unit_test",
        "integration_test"
      ]
    }
  }
}
```

### 场景5：group_type 条件过滤

在模块组中应用条件：

```json
{
  "component": {
    "name": "graphics_component",
    "build": {
      "group_type": {
        "base": ["module1", "module2"],
        "advanced": [
          "module3",
          "gpu_accelerated"
        ]
      },
      "conditions": {
        "gpu_accelerated": {
          "target_os": "ohos"
        }
      }
    }
  }
}
```

## 配置规则

### 支持的条件目标位置

`conditions` 中定义的 item_name 可以出现在以下位置：

1. **sub_component** - 子组件列表
2. **modules** - 模块列表
3. **group_type** - 模块组中的模块
4. **inner_kits** - 内部 kits
5. **inner_api** - 内部 API
6. **test** - 测试用例列表

### 条件匹配规则

1. **无条件定义**：如果 item_name 没有在 `conditions` 中定义，则无条件包含
2. **条件匹配**：如果条件表达式求值为 true，则包含该 item
3. **条件不匹配**：如果条件表达式求值为 false，则排除该 item
4. **属性未定义**：如果条件中使用了未定义的属性，输出警告并排除该 item

## 错误处理

### 警告信息

配置错误时会输出警告信息，常见的警告包括：

1. **conditions 格式错误**
```
ignore invalid 'component.build.conditions' in 'bundle.json'
```

2. **条件表达式格式错误**
```
ignore invalid condition for 'item_name' in 'bundle.json'
```

3. **条件属性未定义**
```
condition attribute 'undefined_attr' for 'item_name' in 'bundle.json'
is undefined in current build context
```

4. **条件目标不存在**
```
condition target 'non_existent_item' in 'bundle.json' does not exist in
'sub_component', 'modules', 'group_type', 'inner_kits', 'inner_api' or 'test'
```

### 调试建议

1. 检查 conditions 字段是否在 `component.build` 下
2. 确认条件目标名称与实际模块/kit/test 名称一致
3. 验证使用的条件属性在当前构建上下文中存在
4. 使用编译日志中的警告信息定位问题

## 完整示例

```json
{
  "component": {
    "name": "example_component",
    "subsystem": "example_subsystem",
    "syscap": [],
    "features": [],
    "adapted_system_type": [],
    "rom": "1MB",
    "ram": "2MB",
    "build": {
      "conditions": {
        "target_only_module": {
          "compile_mode": "target"
        },
        "host_only_module": {
          "compile_mode": "host"
        },
        "arm64_module": {
          "target_cpu": ["arm64", "arm"]
        },
        "standard_kit": {
          "os_level": "standard"
        },
        "standard_test": {
          "compile_mode": "target",
          "os_level": "standard"
        }
      },
      "sub_component": [
        "target_only_module",
        "host_only_module",
        "arm64_module",
        "common_module"
      ],
      "inner_kits": [
        {
          "name": "common_kit",
          "header": "./include/common.h"
        },
        {
          "name": "standard_kit",
          "header": "./include/standard.h"
        }
      ],
      "test": [
        "common_test",
        "standard_test"
      ]
    }
  }
}
```

## 常见问题

### Q1: 条件编译会影响构建性能吗？

A: 条件匹配在构建早期进行，性能影响可忽略不计。主要的性能开销在于读取配置文件，这是构建系统的常规操作。

### Q2: 可以嵌套使用条件吗？

A: 当前版本不支持嵌套条件。每个 item 只能有一个独立的条件表达式。

### Q3: 如何调试条件表达式？

A: 查看构建输出的警告信息。系统会报告未定义的属性和不存在的目标名称。

### Q4: 条件编译与 feature 的区别是什么？

A: feature 是产品级的配置机制，由产品配置文件控制；条件编译是 bundle 级的配置机制，由 bundle.json 自身控制，更细粒度且更灵活。

### Q5: 可以在 modules 列表中混合有条件和无条件的模块吗？

A: 可以。没有在 conditions 中定义的模块会被无条件包含。

## 相关文档

- [部件化编译最佳实践](./部件化编译最佳实践.md)
- [bundle.json 配置规范](./编译配置指导文档.md)
- [标准系统如何添加一个模块](./标准系统如何添加一个模块.md)
