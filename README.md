# 🎓 TeachMind · FastPPT — AI 智能备课系统

> 上传参考资料 → 多轮对话收集教学意图 → 一键生成 PPT + Word 教案

## 📚 文档导航（新人先看）

- `docs/README.md`：项目摘要层索引（10 分钟上手）
- `docs/00-START-HERE.md`：代码入口、启动方式、当前系统事实
- `docs/10-Step1-Problem-And-Needs.md`：痛点与需求结论
- `docs/20-Step2-Product-Positioning.md`：产品定位与三档模式
- `docs/30-Step3-Feature-Decomposition-And-Implementation.md`：功能拆解与可插拔信息块方案
- `.omc/README-INDEX.md`：技术研究深度索引

## ✨ 功能特性

- **文件解析**：支持 PDF / Word / PPT / TXT，自动提取文本并分块入库
- **RAG 检索**：TF-IDF 关键词检索，无需 Embedding API
- **多轮对话**：5 轮预设追问，结构化收集教学意图
- **PPT 生成**：深色主题，封面 + 目录 + 知识点页 + 总结页（python-pptx）
- **Word 教案**：含教学目标、重难点、步骤、知识点详解（python-docx）
- **PPT 预览**：后端渲染缩略图，前端实时预览翻页

## 🛠 技术栈

| 层次 | 技术 |
|------|------|
| 后端 | FastAPI + uvicorn |
| 文件解析 | pdfplumber / python-docx / python-pptx |
| 检索 | scikit-learn TF-IDF |
| PPT生成 | python-pptx |
| Word生成 | python-docx |
| 预览渲染 | Pillow |
| 前端 | Vue 3 + Vite + Element Plus |

## 🚀 快速启动

### Windows 一键启动

```bat
start.bat
```

### 手动启动

**后端**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**前端**
```bash
cd frontend
npm install
npm run dev
```

打开浏览器访问：**http://localhost:5173**

## 📁 项目结构

```
FastPPT/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── requirements.txt
│   ├── api/
│   │   ├── upload.py        # POST /api/upload
│   │   ├── chat.py          # POST /api/chat
│   │   ├── generate.py      # POST /api/generate
│   │   └── download.py      # GET  /api/download|preview
│   └── core/
│       ├── parser.py        # 文件文本提取
│       ├── rag.py           # TF-IDF 检索
│       ├── intent.py        # Mock 意图提取
│       ├── teaching_spec.py # 教学意图标准化
│       ├── slide_blocks.py  # 可插拔信息块归一化
│       ├── ppt_gen.py       # PPT 生成
│       └── doc_gen.py       # Word 生成
└── frontend/
    ├── vite.config.js
    └── src/
        ├── App.vue
        ├── api/index.js
        └── components/
            ├── FileUpload.vue
            ├── ChatPanel.vue
            ├── GenerateBtn.vue
            └── PreviewPanel.vue
```

## 📋 API 文档

启动后访问：http://localhost:8000/docs

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/upload | POST | 上传文件，返回 file_id + chunk_count |
| /api/chat | POST | 多轮对话，返回 reply + intent_ready |
| /api/generate | POST | 生成 PPT + Word，返回文件名 |
| /api/download/{fn} | GET | 下载文件 |
| /api/preview/{fn} | GET | 获取 PPT 缩略图列表 |

## 📝 使用流程

1. （可选）上传参考资料（PDF/Word 等）
2. 在对话框中依次回答 5 个问题（主题、受众、重点、难点、课时）
3. 点击「生成课件」按钮
4. 右侧预览 PPT，点击下载按钮获取文件

---

> Mock 模式：当前 AI 对话为预设问答流程，无需配置 LLM API Key 即可完整运行。
