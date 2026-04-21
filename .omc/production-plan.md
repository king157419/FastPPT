# FastPPT 生产级开发计划（Team + Ralph）

## 📊 Codex已完成模块分析

### ✅ 高质量核心模块
1. **teaching_spec.py** (137行)
   - 教学规格编译器
   - 字段归一化和验证
   - 向后兼容的intent转换
   - **质量评分**: 9/10（生产就绪）

2. **slide_blocks.py** (237行)
   - 11种可插拔信息块
   - Block归一化系统
   - 布局提示和渲染策略
   - **质量评分**: 9/10（架构优秀）

3. **api/chat.py** (127行)
   - SSE流式对话
   - Intent解析和归一化
   - 错误处理完善
   - **质量评分**: 8/10（可用）

4. **api/generate.py** (181行)
   - 同步/异步双模式
   - 进度追踪（SSE）
   - Block自动附加
   - **质量评分**: 8/10（可用）

### 🔧 现有基础设施
- **core/llm.py**: 多模型支持（DeepSeek/Qwen/Claude）
- **core/rag.py**: TF-IDF检索（需升级）
- **core/ppt_gen.py**: PPT生成（需优化）
- **core/doc_gen.py**: Word教案生成

---

## 🎯 生产级改进计划

### 阶段1: 核心增强（Claude负责，Ralph模式）

#### P0 - RAG系统升级（2小时）
**目标**: 从TF-IDF升级到向量检索

**任务**:
1. **backend/integrations/ragflow_client.py**
   - RAGFlow API封装
   - 文档上传/检索/引用
   - 错误处理和重试
   - 连接池管理

2. **backend/core/rag.py** (重构)
   - 保留TF-IDF作为fallback
   - 添加向量检索
   - 混合检索策略
   - 缓存机制

3. **backend/api/retrieval.py** (新增)
   - POST /api/retrieval/upload
   - POST /api/retrieval/search
   - GET /api/retrieval/documents
   - DELETE /api/retrieval/documents/{id}

**验收标准**:
- ✅ 检索准确率从60%提升到85%+
- ✅ 支持PDF/Word/PPT上传
- ✅ 引用溯源功能正常
- ✅ API文档完整

---

#### P1 - LangChain Agent（2小时）
**目标**: 智能对话和工具调用

**任务**:
1. **backend/integrations/langchain_agent.py**
   - TeachingAgent类
   - 工具注册（检索/生成/预览）
   - 多轮对话管理
   - Memory持久化

2. **backend/api/chat.py** (增强)
   - 集成LangChain Agent
   - 保留现有SSE流式
   - 添加工具调用日志
   - 会话管理

**验收标准**:
- ✅ 多轮对话上下文正确
- ✅ 工具调用成功率95%+
- ✅ 流式输出正常
- ✅ 会话可恢复

---

#### P2 - PptxGenJS服务（1.5小时）
**目标**: 高性能PPT生成

**任务**:
1. **services/pptxgenjs/** (新建)
   - Express服务器
   - 教学PPT生成器
   - 中文字体支持
   - 模板系统

2. **backend/core/ppt_gen.py** (重构)
   - 调用PptxGenJS服务
   - 保留python-pptx作为fallback
   - 性能监控
   - 错误处理

**验收标准**:
- ✅ 生成速度从5秒/页降到2秒/页
- ✅ 中文显示正常
- ✅ 支持复杂布局
- ✅ 服务稳定性99%+

---

#### P3 - 部署和监控（1小时）
**目标**: 生产级部署

**任务**:
1. **docker/docker-compose.yml**
   - FastAPI服务
   - PptxGenJS服务
   - RAGFlow服务
   - PostgreSQL + Redis + Milvus

2. **backend/core/monitoring.py** (新增)
   - 性能监控
   - 错误追踪
   - 日志聚合
   - 健康检查

**验收标准**:
- ✅ 一键启动所有服务
- ✅ 日志集中管理
- ✅ 性能指标可视化
- ✅ 自动重启机制

---

### 阶段2: 前端集成（Codex负责，Ralph模式）

#### P0 - RAG前端调用（1小时）
**任务**:
1. **frontend/src/api/retrieval.js**
   - 文档上传API
   - 检索调用API
   - 错误处理

2. **frontend/src/components/DocumentPanel.vue** (新增)
   - 文档上传UI
   - 文档列表
   - 删除功能

**验收标准**:
- ✅ 可以上传文档
- ✅ 可以查看文档列表
- ✅ 可以删除文档
- ✅ 错误提示友好

---

#### P1 - 流式输出优化（1小时）
**任务**:
1. **frontend/src/components/ChatPanel.vue** (增强)
   - 优化SSE连接
   - 添加打字机效果
   - 工具调用可视化
   - 中断生成功能

**验收标准**:
- ✅ 流式显示流畅
- ✅ 可以中断生成
- ✅ 工具调用有提示
- ✅ 用户体验良好

---

#### P2 - 预览增强（1小时）
**任务**:
1. **frontend/src/components/PreviewPanel.vue** (增强)
   - Block可视化
   - 实时预览
   - 缩略图优化
   - 移动端适配

**验收标准**:
- ✅ 预览清晰
- ✅ 响应速度快
- ✅ 移动端可用
- ✅ Block类型显示正确

---

## 🚀 执行策略

### Team创建
```
Team: fastppt-production
├─ Lead: Claude (后端架构和核心功能)
└─ Member: Codex (前端集成和UI优化)
```

### Ralph任务分配

**Claude的Ralph PRD**:
```json
{
  "projectName": "FastPPT后端生产级改进",
  "stories": [
    {
      "id": "BE-001",
      "title": "RAG系统升级到向量检索",
      "priority": 1,
      "acceptanceCriteria": [
        "RAGFlow客户端可用",
        "检索准确率85%+",
        "API文档完整",
        "单元测试通过"
      ]
    },
    {
      "id": "BE-002",
      "title": "LangChain Agent集成",
      "priority": 2,
      "acceptanceCriteria": [
        "多轮对话正常",
        "工具调用成功率95%+",
        "流式输出正常",
        "会话可恢复"
      ]
    },
    {
      "id": "BE-003",
      "title": "PptxGenJS服务",
      "priority": 3,
      "acceptanceCriteria": [
        "生成速度2秒/页",
        "中文显示正常",
        "服务稳定性99%+",
        "Fallback机制正常"
      ]
    },
    {
      "id": "BE-004",
      "title": "Docker部署和监控",
      "priority": 4,
      "acceptanceCriteria": [
        "一键启动成功",
        "日志集中管理",
        "性能监控可用",
        "健康检查正常"
      ]
    }
  ]
}
```

**Codex的Ralph PRD**:
```json
{
  "projectName": "FastPPT前端生产级改进",
  "stories": [
    {
      "id": "FE-001",
      "title": "RAG前端调用",
      "priority": 1,
      "acceptanceCriteria": [
        "可以上传文档",
        "可以查看列表",
        "可以删除文档",
        "错误提示友好"
      ]
    },
    {
      "id": "FE-002",
      "title": "流式输出优化",
      "priority": 2,
      "acceptanceCriteria": [
        "流式显示流畅",
        "可以中断生成",
        "工具调用可视化",
        "用户体验良好"
      ]
    },
    {
      "id": "FE-003",
      "title": "预览面板增强",
      "priority": 3,
      "acceptanceCriteria": [
        "预览清晰",
        "响应速度快",
        "移动端适配",
        "Block显示正确"
      ]
    }
  ]
}
```

---

## 📈 预期成果

### 性能提升
- 检索准确率: 60% → 85% (+42%)
- PPT生成速度: 5秒/页 → 2秒/页 (+150%)
- 内容质量: 6/10 → 8.5/10 (+42%)
- 系统稳定性: 95% → 99%+ (+4%)

### 功能增强
- ✅ 向量检索（RAGFlow）
- ✅ 智能对话（LangChain Agent）
- ✅ 高性能生成（PptxGenJS）
- ✅ 生产级部署（Docker）
- ✅ 性能监控（Prometheus）

### 代码质量
- ✅ 单元测试覆盖率80%+
- ✅ API文档完整
- ✅ 错误处理完善
- ✅ 日志规范统一

---

## ⏱️ 时间估算

**Claude（后端）**: 6.5小时
- RAG升级: 2小时
- LangChain Agent: 2小时
- PptxGenJS服务: 1.5小时
- 部署监控: 1小时

**Codex（前端）**: 3小时
- RAG前端: 1小时
- 流式优化: 1小时
- 预览增强: 1小时

**总计**: 约9.5小时（考虑并行，实际6-7小时）

---

**规划完成，等待启动指令！**
