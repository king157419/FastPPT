# FastPPT 协作开发任务规划

## 📊 当前状态（Codex已完成）

### ✅ 已完成模块
- `backend/core/teaching_spec.py` - 教学规格编译器
- `backend/core/slide_blocks.py` - 可插拔信息块系统
- `backend/api/chat.py` - 意图识别接口（已重构）
- `backend/api/generate.py` - PPT生成接口（已重构）

### 📝 Codex正在做
- 补充文档
- 前后端验证
- 最小可运行验证

---

## 🎯 下一阶段任务分工（Codex完成后）

### 🔵 Claude任务清单（优先级排序）

#### P0 - 核心集成（立即开始，2-3小时）

**任务1: RAGFlow集成模块**
- 文件: `backend/integrations/ragflow_client.py`
- 功能: 
  - 文档上传API封装
  - 语义检索接口
  - 引用溯源
  - 错误处理和重试
- 工具: 使用`executor` agent并行实现
- 交付: 完整可测试的Python模块

**任务2: LangChain Agent实现**
- 文件: `backend/integrations/langchain_agent.py`
- 功能:
  - 教学Agent（理解意图→检索知识→生成PPT）
  - 工具注册（检索/生成/预览）
  - 多轮对话管理
  - 流式输出
- 工具: 使用`architect` agent设计，`executor` agent实现
- 交付: 完整Agent系统

**任务3: 检索接口**
- 文件: `backend/api/retrieval.py`
- 功能:
  - POST /api/retrieval/upload - 文档上传
  - POST /api/retrieval/search - 知识检索
  - GET /api/retrieval/documents - 文档列表
- 工具: 直接实现
- 交付: FastAPI路由

#### P1 - PptxGenJS服务（并行开始，2小时）

**任务4: Node.js微服务**
- 目录: `services/pptxgenjs/`
- 文件:
  - `package.json` - 依赖配置
  - `server.js` - Express服务器
  - `generators/teaching.js` - 教学PPT生成器
  - `generators/templates.js` - 模板系统
- 功能:
  - POST /generate - 接收JSON生成PPTX
  - GET /health - 健康检查
  - 中文字体支持
  - 错误处理
- 工具: 使用`executor` agent实现
- 交付: 可独立运行的Node.js服务

#### P2 - 部署配置（并行开始，1小时）

**任务5: Docker配置**
- 文件:
  - `docker/docker-compose.yml` - 完整编排
  - `docker/Dockerfile.pptxgenjs` - PptxGenJS镜像
  - `docker/Dockerfile.ragflow` - RAGFlow镜像
  - `.env.example` - 环境变量模板
- 功能:
  - 一键启动所有服务
  - 网络配置
  - 数据持久化
- 工具: 直接实现
- 交付: 可运行的Docker Compose配置

#### P3 - 测试和文档（最后，1小时）

**任务6: 集成测试**
- 文件: `tests/integration/test_ragflow.py`
- 功能: RAGFlow集成测试
- 工具: 使用`test-engineer` agent

**任务7: API文档**
- 文件: `docs/API.md`
- 功能: 完整API文档
- 工具: 使用`writer` agent

---

### 🟢 Codex任务清单（建议）

#### P0 - 前端集成（Codex擅长）

**任务8: 前端RAG调用**
- 文件: `frontend/src/api/retrieval.js`
- 功能: 调用检索接口
- 预计: 30分钟

**任务9: 前端流式输出**
- 文件: `frontend/src/components/ChatPanel.vue`
- 功能: WebSocket流式显示
- 预计: 1小时

**任务10: 前端预览优化**
- 文件: `frontend/src/components/PreviewPanel.vue`
- 功能: 实时预览增强
- 预计: 1小时

---

## 🚀 执行策略（使用OMC工具）

### 阶段1: 并行启动（Codex完成后立即开始）

使用`ultrawork`并行执行多个任务：

```bash
/oh-my-claudecode:ultrawork
```

**并行任务**:
1. RAGFlow集成（executor agent）
2. PptxGenJS服务（executor agent）
3. Docker配置（我直接写）

**预计时间**: 2小时完成3个任务

### 阶段2: 集成验证（阶段1完成后）

使用`team`模式协调：

```bash
/team create fastppt-integration
```

**任务分配**:
- Claude: 后端集成测试
- Codex: 前端集成测试
- 并行验证，快速发现问题

### 阶段3: 优化和文档（最后）

使用`ralph`模式确保完成：

```bash
/oh-my-claudecode:ralph 完成所有文档和测试，确保可部署
```

---

## 📋 详细任务卡片（准备好的）

### 任务1: RAGFlow集成模块

**输入**:
- `.omc/dify-ragflow-analysis.md` - RAGFlow分析文档
- Codex的`teaching_spec.py` - 了解数据结构

**输出**:
```python
# backend/integrations/ragflow_client.py
class RAGFlowClient:
    async def upload_document(self, file, kb_id)
    async def search(self, query, kb_ids, top_k=5)
    async def get_citations(self, doc_id, chunk_ids)
```

**验证**:
```python
# 单元测试
pytest tests/unit/test_ragflow_client.py
```

### 任务2: LangChain Agent

**输入**:
- `.omc/langchain-analysis.md` - LangChain分析文档
- RAGFlow客户端 - 检索工具

**输出**:
```python
# backend/integrations/langchain_agent.py
class TeachingAgent:
    def __init__(self, llm, tools)
    async def chat(self, message, session_id)
    async def generate_ppt(self, teaching_spec)
```

**验证**:
```python
# 集成测试
pytest tests/integration/test_agent.py
```

### 任务3: PptxGenJS服务

**输入**:
- `.omc/pptxgenjs-analysis.md` - PptxGenJS分析文档
- Codex的`slide_blocks.py` - 了解Block结构

**输出**:
```javascript
// services/pptxgenjs/server.js
app.post('/generate', async (req, res) => {
  const { teaching_spec, blocks } = req.body;
  const pptx = await generateTeachingPPT(teaching_spec, blocks);
  res.download(pptx);
});
```

**验证**:
```bash
curl -X POST http://localhost:3000/generate -d @test.json
```

---

## 🎯 成功标准

### 阶段1完成标准（2小时后）
- ✅ RAGFlow客户端可以上传文档和检索
- ✅ LangChain Agent可以多轮对话
- ✅ PptxGenJS服务可以生成PPTX
- ✅ Docker Compose可以一键启动

### 阶段2完成标准（4小时后）
- ✅ 前后端完全打通
- ✅ 可以从上传文档到生成PPT全流程
- ✅ 所有API有文档
- ✅ 核心功能有测试

### 最终交付标准（6小时后）
- ✅ 可部署的完整系统
- ✅ 新人可以10分钟启动
- ✅ 所有核心功能可演示
- ✅ 文档完整（README + API + 部署指南）

---

## 🔧 OMC工具使用计划

### 并行执行工具
- `ultrawork` - 并行执行RAGFlow/PptxGenJS/Docker任务
- `team` - 协调我和Codex的前后端集成
- `ralph` - 确保所有任务完成和验证

### 质量保证工具
- `architect` - 架构设计审查
- `code-reviewer` - 代码质量审查
- `test-engineer` - 测试策略和实现
- `verifier` - 最终验证

### 文档工具
- `writer` - API文档生成
- `document-specialist` - 技术文档整理

---

## 📞 等待Codex完成后的行动

**Codex完成后，你只需说**：
1. "开始" - 我立即启动ultrawork并行执行
2. "创建团队" - 我创建team模式协调
3. "你先做RAGFlow" - 我优先做RAGFlow集成

**我会在5分钟内**：
- 启动对应的OMC工具
- 开始并行执行任务
- 实时报告进度

---

**规划完成，随时待命！**
