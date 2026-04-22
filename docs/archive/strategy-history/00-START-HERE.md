# START HERE（10 分钟上手）

## 1. 这是在做什么

FastPPT 面向高校教师备课场景，目标是把“多源资料理解 + 教学意图澄清 + PPT/教案产出”做成一个连续闭环，贴合 A04 赛题中的多模态、RAG、可用性与创新性要求。

## 2. 当前仓库关键目录

- `backend/`：FastAPI 后端与生成逻辑
- `frontend/`：Vue 前端（对话、生成、预览、导出）
- `.omc/`：技术调研和方案分析
- `docs/`：新人摘要层（本目录）

## 3. 3 分钟看代码入口

1. `backend/main.py`：后端路由入口
2. `backend/api/chat.py`：意图收集（含 `[INTENT_READY]` 解析）
3. `backend/api/generate.py`：生成主流程（同步 + 异步）
4. `backend/core/llm.py`：LLM 封装与 JSON 课件生成
5. `backend/core/teaching_spec.py`：教学意图标准化
6. `backend/core/slide_blocks.py`：页面信息块归一化（可插拔架构基础）
7. `frontend/src/components/PreviewPanel.vue`：预览与 PPTX 导出

## 4. 本地启动

后端：

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev
```

访问：`http://localhost:5173`

## 5. 当前系统事实（不要误判）

- 生成链路主体仍是“单次 LLM 产出 pages”
- 已新增：
  - `TeachingSpec`：把多轮对话意图归一成稳定字段
  - `slide blocks`：把 `page.type` 转为标准 `blocks[]`
- 尚未完成：
  - 真正的两阶段生成（大纲 -> 逐页并发展开）
  - 前端按 `blocks[]` 渲染（目前仍按 `page.type`）
  - 公式 OMML 原生导出

## 6. 新人建议动作（第一天）

1. 跑通一次上传/对话/生成/预览全流程
2. 打开 `docs/10`、`20`、`30` 三份文档确认产品与技术边界
3. 用 `backend/core/slide_blocks.py` 看清“可插拔信息块”协议
4. 再决定改造点（优先从步骤 3 的 P0 清单开始）

