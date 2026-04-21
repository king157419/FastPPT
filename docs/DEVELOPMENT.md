# FastPPT 开发者指南

> 本文档面向新加入项目的开发者，帮助快速理解架构、搭建环境、添加功能。

## 目录

- [1. 项目结构](#1-项目结构)
- [2. 本地开发环境](#2-本地开发环境)
- [3. 核心模块说明](#3-核心模块说明)
- [4. 添加新功能](#4-添加新功能)
- [5. 测试指南](#5-测试指南)
- [6. 代码规范](#6-代码规范)

---

## 1. 项目结构

### 1.1 目录树

```
FastPPT/
├── backend/                    # Python 后端
│   ├── main.py                # FastAPI 应用入口
│   ├── requirements.txt       # Python 依赖
│   ├── api/                   # API 路由层
│   │   ├── upload.py         # 文件上传接口
│   │   ├── chat.py           # 多轮对话接口
│   │   ├── generate.py       # 课件生成接口
│   │   ├── download.py       # 文件下载/预览接口
│   │   ├── asr.py            # 语音识别接口
│   │   └── agent.py          # LangChain Agent 接口
│   ├── core/                  # 核心业务逻辑
│   │   ├── parser.py         # 文件解析（PDF/Word/PPT/视频）
│   │   ├── rag.py            # RAG 检索（RAGFlow/ChromaDB/TF-IDF）
│   │   ├── teaching_spec.py  # 教学规格标准化
│   │   ├── slide_blocks.py   # 可插拔信息块归一化
│   │   ├── llm.py            # LLM 调用封装
│   │   ├── ppt_gen.py        # PPT 生成（python-pptx）
│   │   ├── doc_gen.py        # Word 教案生成
│   │   ├── video_parser.py   # 视频解析（OCR/ASR）
│   │   └── monitoring.py     # 监控与日志
│   ├── integrations/          # 第三方集成
│   │   ├── langchain_agent.py    # LangChain 教学 Agent
│   │   └── ragflow_client.py     # RAGFlow 客户端
│   ├── uploads/               # 上传文件存储
│   └── outputs/               # 生成文件输出
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── App.vue           # 主应用组件
│   │   ├── main.js           # 入口文件
│   │   ├── api/index.js      # API 请求封装
│   │   └── components/       # UI 组件
│   │       ├── FileUpload.vue      # 文件上传
│   │       ├── ChatPanel.vue       # 对话面板
│   │       ├── GenerateBtn.vue     # 生成按钮
│   │       ├── PreviewPanel.vue    # 预览面板
│   │       └── SlideRenderer.vue   # 幻灯片渲染器
│   ├── package.json          # Node.js 依赖
│   └── vite.config.js        # Vite 配置
├── docker/                     # Docker 相关
│   └── pptxgenjs-server.js   # PptxGenJS 服务（可选）
├── docs/                       # 文档
└── start.bat                   # Windows 一键启动脚本
```

### 1.2 各模块职责

| 模块 | 职责 |
|------|------|
| **api/** | HTTP 接口层，处理请求/响应，参数验证 |
| **core/parser.py** | 文件解析，提取文本内容（支持 PDF/Word/PPT/视频） |
| **core/rag.py** | 知识检索，三级降级策略（RAGFlow → ChromaDB → TF-IDF） |
| **core/teaching_spec.py** | 教学意图标准化，统一多轮对话收集的字段 |
| **core/slide_blocks.py** | 页面信息块归一化，支持可插拔渲染 |
| **core/llm.py** | LLM 调用封装（DeepSeek API），生成课件 JSON |
| **core/ppt_gen.py** | 使用 python-pptx 生成 .pptx 文件 |
| **core/doc_gen.py** | 使用 python-docx 生成 Word 教案 |
| **integrations/langchain_agent.py** | LangChain Agent，支持工具调用和多轮对话 |
| **frontend/components/** | Vue 组件，实现上传、对话、预览、导出 |

### 1.3 代码组织原则

1. **分层清晰**：API 层 → 业务逻辑层 → 数据层
2. **单一职责**：每个模块只负责一件事
3. **依赖注入**：通过参数传递依赖，避免全局状态
4. **错误处理**：使用 try-except 捕获异常，返回友好错误信息
5. **日志记录**：关键操作记录日志，便于调试和监控

---

## 2. 本地开发环境

### 2.1 系统要求

- **Python**: 3.9+ （推荐 3.11+）
- **Node.js**: 16+ （推荐 18+）
- **操作系统**: Windows / macOS / Linux

### 2.2 Python 环境设置

**创建虚拟环境（推荐）**

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

**安装依赖**

```bash
pip install -r requirements.txt
```

**核心依赖说明**

| 依赖 | 版本 | 用途 |
|------|------|------|
| fastapi | 0.115.0 | Web 框架 |
| uvicorn | 0.30.6 | ASGI 服务器 |
| python-pptx | 1.0.2 | PPT 生成 |
| python-docx | 1.1.2 | Word 生成 |
| pdfplumber | 0.11.4 | PDF 解析 |
| scikit-learn | 1.5.2+ | TF-IDF 检索 |
| chromadb | 0.5.15+ | 向量数据库 |
| langchain | 0.3.0+ | LLM 应用框架 |
| redis | 5.0.0+ | 缓存和会话存储 |

### 2.3 Node.js 环境设置

**安装依赖**

```bash
cd frontend
npm install
```

**核心依赖说明**

| 依赖 | 版本 | 用途 |
|------|------|------|
| vue | 3.4.31 | 前端框架 |
| vite | 5.3.4 | 构建工具 |
| element-plus | 2.7.6 | UI 组件库 |
| axios | 1.7.2 | HTTP 客户端 |
| pptxgenjs | 4.0.1 | 前端 PPT 导出 |
| katex | 0.16.42 | 数学公式渲染 |
| highlight.js | 11.11.1 | 代码高亮 |

### 2.4 环境变量配置

在 `backend/` 目录创建 `.env` 文件（可选）：

```bash
# LLM API
DEEPSEEK_API_KEY=your_deepseek_api_key
DASHSCOPE_API_KEY=your_dashscope_api_key  # 用于 Embedding

# RAGFlow（可选）
RAGFLOW_BASE_URL=http://localhost:9380
RAGFLOW_API_KEY=your_ragflow_api_key
RAGFLOW_KB_ID=your_kb_id

# Redis（可选）
REDIS_URL=redis://localhost:6379/0

# 日志级别
LOG_LEVEL=INFO

# CORS 配置
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 2.5 启动开发服务器

**方式一：一键启动（Windows）**

```bash
start.bat
```

**方式二：手动启动**

后端：
```bash
cd backend
uvicorn main:app --reload --port 8000
```

前端：
```bash
cd frontend
npm run dev
```

**访问地址**

- 前端：http://localhost:5173
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

---

## 3. 核心模块说明

### 3.1 teaching_spec.py（教学规格）

**作用**：标准化多轮对话收集的教学意图，统一字段命名和默认值。

**核心数据结构**

```python
@dataclass
class TeachingSpec:
    topic: str                          # 课程主题
    audience: str                       # 目标受众
    duration: str                       # 课时时长
    style: str                          # PPT 风格
    key_points: list[str]               # 知识点列表
    difficulty_focus: str               # 难点重点
    must_include_visuals: bool          # 是否需要图表
    must_include_latest_cases: bool     # 是否需要最新案例
    required_sources: list[str]         # 必需参考资料
    optional_sources: list[str]         # 可选参考资料
    unresolved_fields: list[str]        # 未明确的字段
    schema_version: str                 # 版本号
```

**使用示例**

```python
from core.teaching_spec import compile_teaching_spec

# 原始意图（来自多轮对话）
raw_intent = {
    "topic": "Python 面向对象编程",
    "audience": "大二学生",
    "key_points": ["类与对象", "继承", "多态"],
    "duration": "90分钟"
}

# 编译为标准化规格
spec = compile_teaching_spec(raw_intent)

# 转换为向后兼容的 intent 格式
effective_intent = spec.to_intent()
```

**设计原则**

1. **容错性**：支持多种字段名（topic/title/course_topic）
2. **默认值**：未提供的字段使用合理默认值
3. **追踪缺失**：记录 `unresolved_fields` 便于后续补充

### 3.2 slide_blocks.py（可插拔信息块）

**作用**：将页面类型（cover/content/code 等）转换为标准化的信息块列表，支持灵活渲染。

**Block 类型**

| Block 类型 | 用途 | Payload 字段 |
|-----------|------|-------------|
| TextBlock | 文本内容 | text, role (title/subtitle/quote) |
| BulletBlock | 列表项 | items[] |
| CodeBlock | 代码片段 | language, code, explanation |
| FormulaBlock | 数学公式 | formulas[], explanation |
| CaseBlock | 案例分析 | problem, steps[], answer |
| TableBlock | 表格/对比 | left{}, right{} |
| ImageBlock | 图片 | image_base64, image_url, caption |
| FlowchartBlock | 流程图 | template, template_data |

**Block 结构**

```python
{
    "id": "p01-b01",                    # 唯一标识
    "type": "TextBlock",                # Block 类型
    "payload": {                        # 实际内容
        "text": "Python 面向对象编程",
        "role": "title"
    },
    "anchors": [],                      # 锚点（用于关联）
    "layoutHints": {"slot": "header"},  # 布局提示
    "styleHints": {},                   # 样式提示
    "renderStrategy": "default",        # 渲染策略
    "validationRules": ["non_empty_payload"]  # 验证规则
}
```

**使用示例**

```python
from core.slide_blocks import attach_blocks_to_slides_json

# 原始课件 JSON（LLM 生成）
slides_json = {
    "pages": [
        {"type": "cover", "title": "Python OOP", "subtitle": "面向对象编程"},
        {"type": "content", "title": "类与对象", "bullets": ["定义类", "创建对象"]}
    ]
}

# 附加标准化 blocks
slides_json_with_blocks, summary = attach_blocks_to_slides_json(slides_json)

# 每个 page 现在包含 blocks[] 字段
print(slides_json_with_blocks["pages"][0]["blocks"])
# [
#   {"id": "p01-b01", "type": "TextBlock", "payload": {"text": "Python OOP", "role": "title"}},
#   {"id": "p01-b02", "type": "TextBlock", "payload": {"text": "面向对象编程", "role": "subtitle"}}
# ]
```

**扩展性**

- 新增 Block 类型：在 `_PAGE_BUILDERS` 字典添加构建函数
- 自定义渲染策略：修改 `renderStrategy` 字段
- 验证规则：在 `validationRules` 添加自定义规则

### 3.3 RAG 系统架构

**三级降级策略**

```
1. RAGFlow 向量检索（优先）
   ↓ 失败
2. ChromaDB + DashScope Embedding
   ↓ 失败
3. TF-IDF 关键词检索（兜底）
```

**使用示例**

```python
from core import rag

# 添加文档
file_id = "doc_001"
chunks = ["Python 是一种解释型语言", "支持面向对象编程"]
rag.add_document(file_id, chunks)

# 检索（自动选择最佳策略）
results = rag.search("Python 面向对象", top_k=3)
# 返回: ["支持面向对象编程", "Python 是一种解释型语言"]

# 删除文档
rag.remove_document(file_id)
```

**配置 RAGFlow**

```python
# 环境变量
RAGFLOW_BASE_URL=http://localhost:9380
RAGFLOW_API_KEY=your_api_key
RAGFLOW_KB_ID=your_kb_id

# 检查是否启用
from core.rag import _use_ragflow
if _use_ragflow():
    print("RAGFlow enabled")
```

**Redis 缓存**

RAG 检索结果自动缓存到 Redis（如果配置），TTL 默认 1 小时。

```python
# 环境变量
REDIS_URL=redis://localhost:6379/0
RAG_CACHE_TTL=3600  # 秒
```

### 3.4 LangChain Agent 架构

**TeachingAgent 类**

提供多轮对话、工具调用、会话持久化功能。

**可用工具**

| 工具 | 功能 | 参数 |
|------|------|------|
| retrieve_knowledge | 检索知识库 | query, top_k |
| generate_ppt_content | 生成 PPT 内容 | teaching_spec (JSON) |
| get_preview_url | 获取预览链接 | job_id |

**使用示例**

```python
from integrations.langchain_agent import TeachingAgent, AgentConfig

# 初始化 Agent
config = AgentConfig(
    deepseek_api_key="your_key",
    redis_url="redis://localhost:6379/0"
)
agent = TeachingAgent(config)

# 多轮对话
session_id = "user_123"
response = await agent.chat("我想做一个 Python 课件", session_id)
print(response)

# 流式对话
async for chunk in agent.chat_stream("主题是面向对象编程", session_id):
    print(chunk, end="")

# 直接生成 PPT
teaching_spec = {
    "topic": "Python OOP",
    "audience": "大二学生",
    "key_points": ["类", "继承", "多态"]
}
ppt_content = await agent.generate_ppt(teaching_spec)

# 清除会话
await agent.clear_session(session_id)
```

**会话持久化**

对话历史自动存储到 Redis，支持跨请求恢复上下文。

```python
# Redis key 格式
teaching_agent:memory:{session_id}

# 数据结构
[
    {"role": "user", "content": "我想做一个课件"},
    {"role": "assistant", "content": "好的，请问主题是什么？"}
]
```

### 3.5 PptxGenJS 服务（可选）

前端使用 PptxGenJS 导出 PPT，支持两种模式：

1. **浏览器模式**：直接在前端生成（默认）
2. **服务端模式**：通过 Node.js 服务生成（更稳定）

**启动服务端模式**

```bash
cd docker
node pptxgenjs-server.js
```

服务监听 `http://localhost:3001`，前端自动检测并使用。

---

## 4. 添加新功能

### 4.1 添加新的 Block 类型

**场景**：需要支持新的页面元素（如时间轴、思维导图）。

**步骤**

1. 在 `slide_blocks.py` 定义构建函数

```python
def _build_timeline_blocks(page: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _block("TextBlock", {"text": page.get("title", ""), "role": "title"}, 
               layout_slot="header"),
        _block(
            "TimelineBlock",
            {
                "events": page.get("events") or [],
                "orientation": page.get("orientation", "vertical")
            },
            render_strategy="timeline-vertical",
            validation_rules=["non_empty_payload", "min_events_2"]
        ),
    ]
```

2. 注册到 `_PAGE_BUILDERS`

```python
_PAGE_BUILDERS = {
    # ... 现有类型
    "timeline": _build_timeline_blocks,
}
```

3. 在 LLM prompt 中添加新类型说明（`core/llm.py`）

```python
SLIDE_TYPES = """
- timeline: 时间轴页面，包含 events[] 和 orientation
"""
```

4. 前端添加渲染逻辑（`SlideRenderer.vue`）

```vue
<template v-else-if="page.type === 'timeline'">
  <div class="timeline">
    <div v-for="event in page.events" :key="event.time" class="event">
      <span class="time">{{ event.time }}</span>
      <span class="desc">{{ event.description }}</span>
    </div>
  </div>
</template>
```

### 4.2 添加新的 API 接口

**场景**：需要新增一个批量导出接口。

**步骤**

1. 在 `backend/api/` 创建新文件 `batch_export.py`

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class BatchExportRequest(BaseModel):
    job_ids: list[str]
    format: str = "zip"

@router.post("/batch-export")
async def batch_export(req: BatchExportRequest):
    """批量导出多个课件"""
    if not req.job_ids:
        raise HTTPException(400, "job_ids 不能为空")
    
    # 实现导出逻辑
    zip_path = create_zip(req.job_ids)
    
    return {"download_url": f"/api/download/{zip_path}"}
```

2. 在 `main.py` 注册路由

```python
from api.batch_export import router as batch_export_router

app.include_router(batch_export_router, prefix="/api")
```

3. 前端调用（`src/api/index.js`）

```javascript
export const batchExport = (jobIds) => {
  return axios.post('/api/batch-export', {
    job_ids: jobIds,
    format: 'zip'
  })
}
```

### 4.3 集成新的 LLM

**场景**：需要支持 OpenAI GPT-4 或其他模型。

**步骤**

1. 在 `core/llm.py` 添加新的客户端

```python
import openai

def _get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")
    return openai.OpenAI(api_key=api_key)

def generate_slides_json_openai(intent: dict, rag_chunks: list[str]) -> dict:
    """使用 OpenAI 生成课件"""
    client = _get_openai_client()
    
    prompt = _build_prompt(intent, rag_chunks)
    
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)
```

2. 添加模型选择逻辑

```python
def generate_slides_json(intent: dict, rag_chunks: list[str]) -> dict:
    """根据配置选择 LLM"""
    provider = os.getenv("LLM_PROVIDER", "deepseek")
    
    if provider == "openai":
        return generate_slides_json_openai(intent, rag_chunks)
    elif provider == "deepseek":
        return generate_slides_json_deepseek(intent, rag_chunks)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
```

3. 配置环境变量

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_key
```

### 4.4 添加新的工具（LangChain Agent）

**场景**：Agent 需要调用外部 API（如天气查询）。

**步骤**

1. 在 `integrations/langchain_agent.py` 定义工具

```python
from langchain.tools import tool

@tool
def get_weather(city: str) -> str:
    """查询城市天气信息
    
    Args:
        city: 城市名称（如"北京"）
    
    Returns:
        天气信息字符串
    """
    try:
        # 调用天气 API
        response = requests.get(f"https://api.weather.com/v1/{city}")
        data = response.json()
        return f"{city}天气：{data['weather']}，温度：{data['temp']}°C"
    except Exception as e:
        return f"天气查询失败: {str(e)}"
```

2. 注册到 Agent 工具列表

```python
class TeachingAgent:
    def __init__(self, config: Optional[AgentConfig] = None):
        # ... 现有代码
        
        # 添加新工具
        self.tools = [
            retrieve_knowledge,
            generate_ppt_content,
            get_preview_url,
            get_weather,  # 新增
        ]
```

3. 更新系统 prompt

```python
system_message = """你是一位专业的教学设计助手...

可用工具：
- retrieve_knowledge: 检索知识库
- generate_ppt_content: 生成PPT内容
- get_preview_url: 获取预览链接
- get_weather: 查询城市天气（用于案例补充）
"""
```

---

## 5. 测试指南

### 5.1 单元测试

**运行测试**

```bash
cd backend

# 运行所有测试
pytest

# 运行特定测试文件
pytest test_ppt_gen.py

# 显示详细输出
pytest -v -s
```

**编写测试**

在 `backend/` 创建 `test_*.py` 文件：

```python
import pytest
from core.teaching_spec import compile_teaching_spec

def test_compile_teaching_spec():
    """测试教学规格编译"""
    raw_intent = {
        "topic": "Python OOP",
        "audience": "大二学生"
    }
    
    spec = compile_teaching_spec(raw_intent)
    
    assert spec.topic == "Python OOP"
    assert spec.audience == "大二学生"
    assert spec.duration == "45分钟"  # 默认值
    assert "duration" in spec.unresolved_fields

def test_compile_with_missing_topic():
    """测试缺失主题的情况"""
    spec = compile_teaching_spec({})
    
    assert spec.topic == "未命名课程"
    assert "topic" in spec.unresolved_fields
```

**测试覆盖率**

```bash
# 安装 pytest-cov
pip install pytest-cov

# 生成覆盖率报告
pytest --cov=core --cov-report=html

# 查看报告
open htmlcov/index.html
```

### 5.2 集成测试

**测试 API 接口**

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_upload_file():
    """测试文件上传"""
    with open("test.pdf", "rb") as f:
        response = client.post(
            "/api/upload",
            files={"file": ("test.pdf", f, "application/pdf")}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "file_id" in data
    assert data["chunk_count"] > 0

def test_generate_ppt():
    """测试课件生成"""
    intent = {
        "topic": "Python OOP",
        "audience": "大二学生",
        "key_points": ["类", "继承", "多态"]
    }
    
    response = client.post("/api/generate", json={"intent": intent})
    
    assert response.status_code == 200
    data = response.json()
    assert "slides_json" in data
    assert len(data["slides_json"]["pages"]) > 0
```

### 5.3 性能测试

**测试 RAG 检索性能**

```python
import time
from core import rag

def test_rag_performance():
    """测试 RAG 检索性能"""
    # 添加测试数据
    chunks = ["测试文本" + str(i) for i in range(1000)]
    rag.add_document("perf_test", chunks)
    
    # 测试检索速度
    start = time.time()
    results = rag.search("测试", top_k=10)
    elapsed = time.time() - start
    
    print(f"检索耗时: {elapsed:.3f}s")
    assert elapsed < 1.0  # 应在 1 秒内完成
    assert len(results) == 10
```

**压力测试**

```bash
# 安装 locust
pip install locust

# 创建 locustfile.py
from locust import HttpUser, task, between

class FastPPTUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def generate_ppt(self):
        self.client.post("/api/generate", json={
            "intent": {
                "topic": "Test Topic",
                "audience": "Students"
            }
        })

# 运行压力测试
locust -f locustfile.py --host=http://localhost:8000
```

访问 http://localhost:8089 查看测试结果。

---

## 6. 代码规范

### 6.1 Python 代码风格

**遵循 PEP 8**

```bash
# 安装代码检查工具
pip install black flake8 isort

# 格式化代码
black backend/

# 检查代码风格
flake8 backend/

# 排序 import
isort backend/
```

**命名规范**

- 模块/包：小写+下划线 `teaching_spec.py`
- 类：大驼峰 `TeachingSpec`
- 函数/变量：小写+下划线 `compile_teaching_spec()`
- 常量：大写+下划线 `BLOCK_SCHEMA_VERSION`
- 私有函数：前缀下划线 `_build_cover_blocks()`

**类型注解**

```python
from typing import Optional, List, Dict, Any

def search(query: str, top_k: int = 5) -> List[str]:
    """检索知识库
    
    Args:
        query: 检索查询
        top_k: 返回结果数量
    
    Returns:
        检索到的文本片段列表
    """
    pass
```

**文档字符串**

```python
def compile_teaching_spec(raw_intent: dict[str, Any] | None) -> TeachingSpec:
    """编译教学规格
    
    将原始意图字典转换为标准化的 TeachingSpec 对象，
    支持多种字段名，提供默认值，追踪缺失字段。
    
    Args:
        raw_intent: 原始意图字典，可为 None
    
    Returns:
        标准化的 TeachingSpec 对象
    
    Example:
        >>> spec = compile_teaching_spec({"topic": "Python"})
        >>> spec.topic
        'Python'
    """
    pass
```

### 6.2 JavaScript 代码风格

**使用 ESLint + Prettier**

```bash
cd frontend

# 安装工具
npm install -D eslint prettier eslint-plugin-vue

# 创建 .eslintrc.js
module.exports = {
  extends: [
    'plugin:vue/vue3-recommended',
    'prettier'
  ],
  rules: {
    'vue/multi-word-component-names': 'off'
  }
}

# 格式化代码
npx prettier --write src/
```

**命名规范**

- 组件：大驼峰 `ChatPanel.vue`
- 函数/变量：小驼峰 `generatePPT()`
- 常量：大写+下划线 `API_BASE_URL`
- 文件名：小驼峰或短横线 `index.js` 或 `chat-panel.vue`

**Vue 组件规范**

```vue
<template>
  <!-- 使用语义化标签 -->
  <div class="chat-panel">
    <header class="chat-header">
      <h2>{{ title }}</h2>
    </header>
    
    <main class="chat-body">
      <!-- 使用 v-for 时必须加 key -->
      <div v-for="msg in messages" :key="msg.id" class="message">
        {{ msg.content }}
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

// Props 定义
const props = defineProps({
  title: {
    type: String,
    default: '对话面板'
  }
})

// 响应式数据
const messages = ref([])

// 计算属性
const messageCount = computed(() => messages.value.length)

// 方法
const sendMessage = (content) => {
  messages.value.push({
    id: Date.now(),
    content
  })
}
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-header {
  padding: 1rem;
  border-bottom: 1px solid #eee;
}
</style>
```

### 6.3 提交信息规范

**格式**

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 类型**

- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构（不是新功能也不是修复）
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具配置

**示例**

```bash
# 新功能
git commit -m "feat(rag): 添加 RAGFlow 向量检索支持"

# 修复 bug
git commit -m "fix(ppt_gen): 修复公式渲染错误"

# 文档更新
git commit -m "docs: 添加开发者指南"

# 重构
git commit -m "refactor(slide_blocks): 优化 Block 构建逻辑"
```

**详细提交**

```bash
git commit -m "feat(agent): 添加 LangChain Agent 支持

- 实现 TeachingAgent 类
- 支持多轮对话和工具调用
- 集成 Redis 会话持久化
- 添加流式输出支持

Closes #123"
```

---

## 附录

### A. 常见问题

**Q: 如何切换 LLM 模型？**

A: 修改环境变量 `LLM_PROVIDER` 和对应的 API Key。

```bash
# 使用 DeepSeek
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_key

# 使用 OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key
```

**Q: RAG 检索结果不准确怎么办？**

A: 检查以下几点：
1. 确认文档已正确上传和分块
2. 调整 `top_k` 参数增加返回结果数量
3. 如果使用向量检索，确认 Embedding 模型配置正确
4. 查看日志确认使用的检索策略（RAGFlow/ChromaDB/TF-IDF）

**Q: 如何调试 LangChain Agent？**

A: 启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Agent 会输出详细的工具调用和推理过程
```

**Q: 前端如何处理大文件上传？**

A: 使用分片上传：

```javascript
const uploadLargeFile = async (file) => {
  const chunkSize = 1024 * 1024 // 1MB
  const chunks = Math.ceil(file.size / chunkSize)
  
  for (let i = 0; i < chunks; i++) {
    const chunk = file.slice(i * chunkSize, (i + 1) * chunkSize)
    await axios.post('/api/upload-chunk', {
      chunk,
      index: i,
      total: chunks
    })
  }
}
```

### B. 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (Vue 3)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Upload  │  │   Chat   │  │ Generate │  │  Preview │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼─────────────┼─────────────┼─────────────┼──────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                      │ HTTP/JSON
        ┌─────────────┴─────────────────────────────────────┐
        │              Backend (FastAPI)                     │
        │  ┌──────────────────────────────────────────┐     │
        │  │           API Layer                       │     │
        │  │  /upload  /chat  /generate  /download    │     │
        │  └──────────────┬───────────────────────────┘     │
        │                 │                                  │
        │  ┌──────────────┴───────────────────────────┐     │
        │  │         Core Business Logic               │     │
        │  │  ┌────────┐  ┌────────┐  ┌────────┐     │     │
        │  │  │ Parser │  │  RAG   │  │  LLM   │     │     │
        │  │  └────────┘  └────────┘  └────────┘     │     │
        │  │  ┌────────┐  ┌────────┐  ┌────────┐     │     │
        │  │  │Teaching│  │ Slide  │  │  PPT   │     │     │
        │  │  │  Spec  │  │ Blocks │  │  Gen   │     │     │
        │  │  └────────┘  └────────┘  └────────┘     │     │
        │  └──────────────────────────────────────────┘     │
        │                                                    │
        │  ┌──────────────────────────────────────────┐     │
        │  │         Integrations                      │     │
        │  │  ┌────────────┐  ┌────────────┐          │     │
        │  │  │ LangChain  │  │  RAGFlow   │          │     │
        │  │  │   Agent    │  │   Client   │          │     │
        │  │  └────────────┘  └────────────┘          │     │
        │  └──────────────────────────────────────────┘     │
        └────────────────────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────────────────────────────┐
        │              External Services                     │
        │  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
        │  │ DeepSeek │  │  Redis   │  │ RAGFlow  │        │
        │  │   API    │  │  Cache   │  │    KB    │        │
        │  └──────────┘  └──────────┘  └──────────┘        │
        └────────────────────────────────────────────────────┘
```

### C. 相关文档

- [项目摘要](README.md)
- [快速开始](00-START-HERE.md)
- [产品定位](20-Step2-Product-Positioning.md)
- [功能拆解](30-Step3-Feature-Decomposition-And-Implementation.md)
- [API 文档](http://localhost:8000/docs)

---

**文档版本**: v1.0  
**最后更新**: 2026-04-21  
**维护者**: FastPPT 开发团队

