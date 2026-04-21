# FastPPT 快速启动指南

## 🚀 启动步骤

### 1. 配置环境变量

```bash
# 复制配置模板
cp backend/.env.example backend/.env

# 编辑 backend/.env，填入你的API密钥
# 必需：
DEEPSEEK_API_KEY=your_key_here
DASHSCOPE_API_KEY=your_key_here

# 可选（启用RAGFlow）：
RAGFLOW_BASE_URL=https://your-ragflow.com
RAGFLOW_API_KEY=your_key_here
RAGFLOW_KB_ID=your_kb_id_here
```

### 2. 启动方式

#### 方式A：Docker一键启动（推荐）

```bash
docker-compose up -d
```

访问：
- 前端：http://localhost:5173
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs

#### 方式B：本地开发模式

**终端1 - 后端**：
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**终端2 - 前端**：
```bash
cd frontend
npm install
npm run dev
```

**终端3 - PptxGenJS服务**：
```bash
cd services/pptxgenjs
npm install
node server.js
```

## 🎯 体验新型RAG系统

### 1. 上传文档

```bash
curl -X POST http://localhost:8000/api/retrieval/upload \
  -F "file=@your_document.pdf" \
  -F "kb_id=default"
```

### 2. 检索知识

```bash
curl -X POST http://localhost:8000/api/retrieval/search \
  -H "Content-Type: application/json" \
  -d '{
    "question": "光合作用的过程",
    "kb_ids": ["default"],
    "top_k": 5
  }'
```

### 3. 使用Agent对话

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "帮我生成光合作用的课件"}],
    "use_agent": true
  }'
```

## 📊 监控和调试

- 健康检查：http://localhost:8000/health
- Prometheus指标：http://localhost:8000/metrics
- 错误日志：http://localhost:8000/admin/errors
- 性能统计：http://localhost:8000/admin/performance

## 📚 文档

- API文档：docs/API.md
- 开发指南：docs/DEVELOPMENT.md
- 部署文档：docs/DEPLOYMENT.md
