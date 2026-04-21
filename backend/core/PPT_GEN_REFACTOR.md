# PPT Generation Refactoring

## 概述

重构了 `backend/core/ppt_gen.py`，添加了对 PptxGenJS 服务的支持，同时保留 python-pptx 作为 fallback。

## 主要改进

### 1. PptxGenJS 服务集成

- **新增函数**: `call_pptxgenjs_service()`
  - 调用 Node.js PptxGenJS 微服务生成 PPT
  - 支持自定义服务 URL、超时时间和重试次数
  - 默认服务地址: `http://localhost:3000`（可通过环境变量 `PPTXGENJS_SERVICE_URL` 配置）

- **数据格式转换**: `_convert_to_pptxgenjs_format()`
  - 将现有的 `intent` 和 `slide_contents` 转换为 PptxGenJS 服务所需的 JSON 格式
  - 支持 cover、agenda、content、summary 等幻灯片类型

### 2. Fallback 机制

- **新增函数**: `_generate_pptx_pythonpptx()`
  - 封装原有的 python-pptx 生成逻辑
  - 当 PptxGenJS 服务不可用时自动使用

- **主函数**: `generate_pptx()`
  - 优先尝试 PptxGenJS 服务
  - 失败时自动 fallback 到 python-pptx
  - 保持函数签名不变，完全向后兼容

### 3. 性能监控

- 记录每次生成的耗时
- 计算平均每页生成时间
- 使用 Python logging 模块输出详细日志

### 4. 错误处理和重试

- 支持最多 2 次重试（可配置）
- 处理超时、连接错误等异常
- 详细的错误日志记录

## 配置

### 环境变量

在 `.env` 文件中添加：

```bash
# PptxGenJS Service (Optional)
PPTXGENJS_SERVICE_URL=http://localhost:3000
```

### Docker Compose

PptxGenJS 服务已在 `docker-compose.yml` 中配置：

```yaml
pptxgenjs:
  build:
    context: ../
    dockerfile: docker/Dockerfile.pptxgenjs
  container_name: fastppt-pptxgenjs
  ports:
    - "3000:3000"
```

## 使用方法

### 基本使用（无需修改现有代码）

```python
from core.ppt_gen import generate_pptx

intent = {
    "topic": "Python基础",
    "audience": "初学者",
    "key_points": ["变量", "函数", "类"],
    "duration": "45分钟"
}

slide_contents = [
    {
        "key_point": "变量",
        "bullets": ["整数", "字符串", "列表"],
        "tip": "变量命名要有意义"
    }
]

# 自动选择最佳生成方式
output_path = generate_pptx(intent, slide_contents, "output.pptx")
```

### 高级使用（自定义配置）

```python
from core.ppt_gen import call_pptxgenjs_service

# 自定义服务 URL 和超时
result = call_pptxgenjs_service(
    intent,
    slide_contents,
    "output.pptx",
    service_url="http://custom-server:3000",
    timeout=60,
    max_retries=3
)

if result:
    print("PptxGenJS 生成成功")
else:
    print("需要使用 fallback")
```

## 性能对比

### PptxGenJS 服务
- **目标**: ~2秒/页
- **优势**: 更快的生成速度，更好的样式支持

### python-pptx (Fallback)
- **当前**: ~5-10秒/页
- **优势**: 无需额外服务，稳定可靠

## 测试

运行测试脚本：

```bash
cd backend
python test_ppt_gen.py
```

测试内容：
1. python-pptx fallback 功能
2. PptxGenJS 服务调用
3. 完整流程（带 fallback）

## 向后兼容性

✅ **完全向后兼容**

- `generate_pptx()` 函数签名未改变
- 现有调用代码无需修改
- 如果 PptxGenJS 服务不可用，自动使用 python-pptx

## 依赖

新增依赖（已添加到 `requirements.txt`）：

```
requests>=2.31.0
```

## 日志示例

### 成功使用 PptxGenJS

```
[PptxGenJS] 调用服务生成 PPT (尝试 1/3)
[PptxGenJS] 生成成功: 6 页, 耗时 12.34s (2.06s/页)
[PPT生成] 使用 PptxGenJS 服务成功，总耗时 12.34s
```

### Fallback 到 python-pptx

```
[PptxGenJS] 连接失败 (尝试 1/3)
[PptxGenJS] 连接失败 (尝试 2/3)
[PptxGenJS] 连接失败 (尝试 3/3)
[PptxGenJS] 所有尝试失败，耗时 14.28s
[PPT生成] PptxGenJS 服务不可用，使用 python-pptx fallback
[PPT生成] python-pptx fallback 完成，生成耗时 8.52s，总耗时 22.80s
```

## 未来改进

1. 支持更多幻灯片类型（code, formula, image 等）
2. 添加缓存机制
3. 支持批量生成
4. 性能指标收集和监控
