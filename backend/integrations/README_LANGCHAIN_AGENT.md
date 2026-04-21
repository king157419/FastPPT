# LangChain Teaching Agent

生产级教学Agent实现，基于LangChain 1.0+，支持多轮对话、工具调用、记忆持久化和流式输出。

## 功能特性

### 1. 多轮对话
- 基于LangChain Agent框架
- 支持上下文理解和连续对话
- 自动收集教学需求（主题、受众、知识点、课时、风格）

### 2. 工具集成
- **retrieve_knowledge**: 调用RAGFlow检索相关知识
- **generate_ppt_content**: 生成PPT课件内容
- **get_preview_url**: 获取预览链接

### 3. 记忆管理
- Redis持久化存储
- 会话级别的对话历史
- 可配置TTL（默认24小时）

### 4. 流式输出
- 支持SSE流式响应
- 实时返回生成内容
- 适配前端EventSource

## 架构设计

```
TeachingAgent
├── LLM (ChatOpenAI with DeepSeek)
├── Tools
│   ├── retrieve_knowledge (RAGFlow)
│   ├── generate_ppt_content (现有生成逻辑)
│   └── get_preview_url (预览URL)
├── Memory (RedisMemoryStore)
│   ├── save_messages
│   ├── load_messages
│   └── delete_session
└── Agent (LangChain create_agent)
```

## 安装依赖

```bash
pip install -r requirements.txt
```

新增依赖：
- langchain>=0.3.0
- langchain-openai>=0.2.0
- langchain-community>=0.3.0
- redis>=5.0.0
- tenacity>=8.2.0

## 配置

### 环境变量

```bash
# DeepSeek API (必需)
DEEPSEEK_API_KEY=your_deepseek_api_key

# Redis (可选，默认localhost:6379)
REDIS_URL=redis://localhost:6379/0

# 前端URL (可选，用于预览链接)
FRONTEND_URL=http://localhost:5173
```

### 配置类

```python
from integrations.langchain_agent import AgentConfig

config = AgentConfig(
    deepseek_api_key="your_key",
    deepseek_base_url="https://api.deepseek.com/v1",
    model_name="deepseek-chat",
    temperature=0.7,
    max_tokens=4096,
    redis_url="redis://localhost:6379/0",
    memory_ttl=86400,  # 24小时
)
```

## 使用示例

### 1. 基础对话

```python
import asyncio
from integrations.langchain_agent import TeachingAgent, AgentConfig

async def basic_chat():
    # 初始化Agent
    config = AgentConfig()
    agent = TeachingAgent(config)
    
    # 多轮对话
    session_id = "user-123"
    
    response1 = await agent.chat(
        "你好，我想制作一个关于Python编程的课件",
        session_id
    )
    print(response1)
    
    response2 = await agent.chat(
        "面向大一本科生，45分钟",
        session_id
    )
    print(response2)

asyncio.run(basic_chat())
```

### 2. 流式对话

```python
async def streaming_chat():
    config = AgentConfig()
    agent = TeachingAgent(config)
    
    session_id = "user-456"
    
    print("Agent: ", end="", flush=True)
    async for chunk in agent.chat_stream(
        "介绍一下机器学习的基本概念",
        session_id
    ):
        print(chunk, end="", flush=True)
    print()

asyncio.run(streaming_chat())
```

### 3. 直接生成PPT

```python
async def generate_ppt():
    config = AgentConfig()
    agent = TeachingAgent(config)
    
    teaching_spec = {
        "topic": "Python基础编程",
        "audience": "大一本科生",
        "key_points": ["变量与数据类型", "控制流程", "函数定义"],
        "duration": "45分钟",
        "style": "简洁学术"
    }
    
    result = await agent.generate_ppt(teaching_spec)
    print(f"生成了 {len(result['pages'])} 页PPT")
    print(f"主题色: {result['theme']}")

asyncio.run(generate_ppt())
```

### 4. 单例模式

```python
from integrations.langchain_agent import get_teaching_agent

# 获取全局单例
agent = get_teaching_agent()

# 使用单例
response = await agent.chat("你好", "session-001")
```

### 5. 清除会话

```python
async def clear_session():
    agent = get_teaching_agent()
    
    # 清除特定会话的历史
    success = await agent.clear_session("session-001")
    print(f"会话清除: {success}")

asyncio.run(clear_session())
```

## FastAPI集成

### 添加路由

```python
# backend/api/agent.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from integrations.langchain_agent import get_teaching_agent

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    session_id: str

class GenerateRequest(BaseModel):
    teaching_spec: dict

@router.post("/agent/chat")
async def chat(req: ChatRequest):
    """同步对话接口"""
    try:
        agent = get_teaching_agent()
        response = await agent.chat(req.message, req.session_id)
        return {"response": response}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/agent/chat/stream")
async def chat_stream(req: ChatRequest):
    """流式对话接口"""
    try:
        agent = get_teaching_agent()
        
        async def event_generator():
            async for chunk in agent.chat_stream(req.message, req.session_id):
                yield f"data: {chunk}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/agent/generate")
async def generate(req: GenerateRequest):
    """生成PPT接口"""
    try:
        agent = get_teaching_agent()
        result = await agent.generate_ppt(req.teaching_spec)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))

@router.delete("/agent/session/{session_id}")
async def clear_session(session_id: str):
    """清除会话接口"""
    try:
        agent = get_teaching_agent()
        success = await agent.clear_session(session_id)
        return {"success": success}
    except Exception as e:
        raise HTTPException(500, str(e))
```

### 注册路由

```python
# backend/main.py
from api.agent import router as agent_router

app.include_router(agent_router, prefix="/api", tags=["agent"])
```

## 工具扩展

### 添加自定义工具

```python
from langchain.tools import tool

@tool
def custom_tool(param: str) -> str:
    """自定义工具描述"""
    # 实现工具逻辑
    return f"处理结果: {param}"

# 在TeachingAgent初始化时添加
agent.tools.append(custom_tool)
```

## 错误处理

所有方法都包含完整的错误处理：

```python
try:
    response = await agent.chat(message, session_id)
except RuntimeError as e:
    # 处理运行时错误
    print(f"对话失败: {e}")
except ValueError as e:
    # 处理配置错误
    print(f"配置错误: {e}")
```

## 日志记录

使用Python标准logging模块：

```python
import logging

# 配置日志级别
logging.basicConfig(level=logging.INFO)

# Agent会自动记录关键操作
# - Agent初始化
# - 对话完成
# - 工具调用
# - 错误信息
```

## 性能优化

### 1. Redis连接池
- 使用异步Redis客户端
- 自动管理连接生命周期

### 2. 流式输出
- 减少首字节时间
- 提升用户体验

### 3. 单例模式
- 复用Agent实例
- 减少初始化开销

## 测试

运行测试脚本：

```bash
cd backend/integrations
python test_langchain_agent.py
```

测试覆盖：
- 导入验证
- 基础对话
- 流式对话
- PPT生成
- 会话管理

## 生产部署

### 1. Redis配置

```bash
# 启动Redis
docker run -d -p 6379:6379 redis:7-alpine

# 或使用云服务
# AWS ElastiCache, Azure Cache for Redis, etc.
```

### 2. 环境变量

```bash
# .env
DEEPSEEK_API_KEY=sk-xxx
REDIS_URL=redis://production-redis:6379/0
FRONTEND_URL=https://your-domain.com
```

### 3. 监控

- 监控Redis连接状态
- 监控API调用延迟
- 监控错误率

## 故障排查

### Redis连接失败

```
Error: 远程计算机拒绝网络连接
```

解决方案：
1. 确认Redis服务运行中
2. 检查REDIS_URL配置
3. 检查网络防火墙

### API Key错误

```
ValueError: DEEPSEEK_API_KEY is required
```

解决方案：
1. 设置环境变量DEEPSEEK_API_KEY
2. 或在AgentConfig中显式传入

### 工具调用失败

```
知识检索失败: No module named 'core'
```

解决方案：
1. 确保在backend目录运行
2. 检查Python路径配置
3. 确认core模块存在

## 技术栈

- LangChain 1.0+ (Agent框架)
- LangChain-OpenAI (LLM集成)
- Redis (记忆存储)
- DeepSeek API (LLM提供商)
- FastAPI (Web框架)
- Pydantic (数据验证)

## 参考文档

- [LangChain官方文档](https://python.langchain.com/)
- [DeepSeek API文档](https://platform.deepseek.com/docs)
- [Redis Python客户端](https://redis.readthedocs.io/)
- [FastAPI文档](https://fastapi.tiangolo.com/)

## 许可证

与FastPPT项目保持一致
