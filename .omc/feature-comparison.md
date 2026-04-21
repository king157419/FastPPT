# AI备课/PPT生成项目功能对比矩阵

## 对比时间：2026-04-21

---

## 核心功能对比表

| 项目 | Stars | 文件解析 | RAG检索 | 多轮对话 | PPT生成架构 | 教案生成 | 预览功能 | 导出格式 | 部署方式 | AI模型 | 特色功能 |
|------|-------|---------|---------|---------|------------|---------|---------|---------|---------|--------|---------|
| **FastPPT** | - | PDF/Word/PPT/TXT | ✅ TF-IDF | ✅ 5轮预设 | 单阶段 | ✅ Word | ✅ 缩略图 | PPTX/Word | 本地/Docker | DeepSeek | 9种固定模板 |
| **OpenMAIC** | 11.5k | 未知 | 未知 | 未知 | **两阶段** | ❌ | 未知 | PPTX | 未知 | 未知 | 精确坐标、LaTeX原生、交互式 |
| **DeepTutor** | 18.4k | PDF(MinerU) | ✅ RAG | ✅ 引导式 | N/A | ❌ | ✅ 交互可视化 | N/A | Docker/本地 | OpenAI/Claude/Ollama | 双回路架构、学习助手 |
| **PPTAgent** | 4.1k | 多文档 | 未知 | 未知 | **反思式** | ❌ | 未知 | PPTX | Docker | OpenAI | Agentic框架、PPTEval评分 |
| **Presenton** | 4.7k | 未知 | 未知 | ❌ | 单阶段 | ❌ | ✅ | PPTX/PDF | Docker/Electron | OpenAI/Gemini/Ollama | API支持、本地运行 |
| **Presentation AI** | 2.8k | 未知 | ❌ | ❌ | 单阶段 | ❌ | ✅ | PPTX | Web | OpenAI | 可自定义主题 |
| **SlideTailor** | 51 | 学术论文 | 未知 | 未知 | **个性化** | ❌ | 未知 | PPTX | 本地 | OpenAI | 科研论文专用、AAAI 2026 |
| **AI-PPT-Builder** | 22 | 未知 | ❌ | ❌ | 单阶段 | ❌ | ✅ | PPTX | Web SaaS | OpenAI | 认证、订阅、支付 |
| **EduChat** | 928 | 未知 | 未知 | ✅ | N/A | ✅ 教案 | ❌ | N/A | 本地 | 自研LLM | 教育大模型、作文指导、心理疏导 |
| **AI Lesson Planner** | 3 | 未知 | ✅ RAG | ❌ | N/A | ✅ 教案 | ❌ | JSON | Streamlit | OpenAI | RAG教案生成 |
| **Better Lessons** | 4 | 未知 | ❌ | ❌ | N/A | ✅ 教案 | ❌ | 未知 | Web | OpenAI | 个性化教案 |
| **AI Course Generator** | 47 | 未知 | ❌ | ❌ | N/A | ✅ 课程 | ❌ | 未知 | Web | Gemini | YouTube视频集成 |
| **ACCG** | 未知 | 未知 | ❌ | ❌ | N/A | ✅ 课程 | ❌ | PDF/PPT | Streamlit | OpenAI/LLama-3 | 课程+测验+下载 |

---

## 详细功能分析

### 一、文件解析能力

#### 🏆 最强
- **FastPPT**: PDF/Word/PPT/TXT 全格式支持
- **DeepTutor**: PDF解析（MinerU）

#### ⚠️ 有限
- **SlideTailor**: 仅学术论文
- 其他项目：大多不支持或未明确

### 二、RAG检索

#### ✅ 支持RAG
- **FastPPT**: TF-IDF（无需Embedding API）
- **DeepTutor**: 完整RAG系统
- **AI Lesson Planner**: RAG教案生成

#### ❌ 不支持
- 大多数PPT生成项目不支持RAG

### 三、多轮对话

#### ✅ 支持
- **FastPPT**: 5轮预设追问
- **DeepTutor**: 引导式对话
- **EduChat**: 教育对话大模型

#### ❌ 不支持
- 大多数PPT生成项目是单次生成

### 四、PPT生成架构（核心差异）

#### 🌟 两阶段/反思式（高质量）
- **OpenMAIC**: 大纲→逐页内容，并发生成
- **PPTAgent**: 反思式生成，PPTEval评分
- **SlideTailor**: 个性化生成

#### 📝 单阶段（快速但可能空洞）
- **FastPPT**: 一次调用生成全部
- **Presenton**: 单次生成
- **Presentation AI**: 单次生成
- **AI-PPT-Builder**: 单次生成

### 五、教案生成

#### ✅ 支持
- **FastPPT**: Word教案（教学目标、重难点、步骤）
- **EduChat**: 教案生成+作文指导
- **AI Lesson Planner**: RAG教案
- **Better Lessons**: 个性化教案
- **AI Course Generator**: 课程生成
- **ACCG**: 课程+测验

#### ❌ 不支持
- 所有纯PPT生成项目

### 六、预览功能

#### ✅ 支持
- **FastPPT**: 后端渲染缩略图
- **DeepTutor**: 交互式可视化
- **Presenton**: 预览支持
- **Presentation AI**: 预览支持
- **AI-PPT-Builder**: 预览支持

### 七、导出格式

#### 多格式
- **FastPPT**: PPTX + Word
- **Presenton**: PPTX + PDF
- **ACCG**: PDF + PPT

#### 单格式
- 大多数项目：仅PPTX

### 八、部署方式

#### 🐳 Docker一键部署
- **FastPPT**: ✅
- **DeepTutor**: ✅
- **PPTAgent**: ✅
- **Presenton**: ✅

#### 🌐 Web SaaS
- **AI-PPT-Builder**: 完整SaaS（认证+订阅+支付）
- **Presentation AI**: Web应用

#### 💻 本地部署
- **EduChat**: 本地LLM
- **SlideTailor**: 本地运行

#### 📱 Electron桌面应用
- **Presenton**: 支持桌面版

### 九、AI模型支持

#### 🔓 多模型支持
- **DeepTutor**: OpenAI/Claude/Ollama/vLLM/LM Studio
- **Presenton**: OpenAI/Gemini/Ollama
- **FastPPT**: DeepSeek（可扩展）

#### 🔒 单一模型
- 大多数项目：仅OpenAI或Gemini

#### 🏠 自研模型
- **EduChat**: 自研教育大模型（7B/13B）

### 十、特色功能对比

#### FastPPT 独有
- ✅ 9种固定模板
- ✅ TF-IDF检索（无需Embedding）
- ✅ 5轮预设对话
- ✅ PPT+Word双输出

#### OpenMAIC 独有
- ✅ 精确坐标系（1000×562.5px）
- ✅ LaTeX原生公式（可编辑）
- ✅ 交互式场景（iframe）
- ✅ PBL项目制学习
- ✅ 15+种Action系统

#### DeepTutor 独有
- ✅ 双回路架构（分析+求解）
- ✅ 交互式可视化
- ✅ 引导式教学（不直接给答案）
- ✅ Telegram集成

#### PPTAgent 独有
- ✅ Agentic反思框架
- ✅ PPTEval评分系统
- ✅ 环境感知反思

#### Presenton 独有
- ✅ API批量生成
- ✅ 本地运行（隐私）
- ✅ Electron桌面版

#### AI-PPT-Builder 独有
- ✅ 完整SaaS架构
- ✅ 用户认证（Clerk）
- ✅ 订阅管理（Lemon Squeezy）

---

## FastPPT 优势分析

### ✅ 相比其他项目的优势

1. **全栈功能**: PPT + Word教案，其他项目大多单一功能
2. **文件解析**: 支持4种格式，覆盖最广
3. **RAG检索**: TF-IDF实现，无需Embedding API，降低成本
4. **多轮对话**: 5轮预设追问，结构化收集意图
5. **预览功能**: 后端渲染缩略图，用户体验好
6. **部署简单**: Docker一键启动

### ⚠️ 相比顶级项目的不足

1. **生成架构**: 单阶段 vs OpenMAIC的两阶段（内容空洞根本原因）
2. **布局系统**: CSS流式 vs OpenMAIC的精确坐标
3. **元素类型**: 9种固定模板 vs OpenMAIC的自由组合
4. **LaTeX支持**: 文本近似 vs OpenMAIC的原生公式
5. **并发策略**: 单次调用 vs OpenMAIC的并发生成
6. **反思机制**: 无 vs PPTAgent的反思框架
7. **评分系统**: 无 vs PPTAgent的PPTEval

---

## 可用性评估

### 🟢 直接可用（开箱即用）

1. **Presenton** (4.7k stars)
   - Docker一键部署
   - API支持
   - 多模型支持
   - **推荐指数**: ⭐⭐⭐⭐⭐

2. **DeepTutor** (18.4k stars)
   - Docker部署
   - 功能完整
   - 文档齐全
   - **推荐指数**: ⭐⭐⭐⭐⭐（但偏重学习助手，非PPT生成）

### 🟡 需要配置（中等难度）

1. **PPTAgent** (4.1k stars)
   - Docker部署
   - 需要配置OpenAI API
   - **推荐指数**: ⭐⭐⭐⭐

2. **AI-PPT-Builder** (22 stars)
   - 需要配置多个服务（Clerk/Prisma/Lemon Squeezy）
   - SaaS架构复杂
   - **推荐指数**: ⭐⭐⭐

### 🔴 需要二次开发（高难度）

1. **OpenMAIC** (11.5k stars)
   - 架构最先进，但需要深度集成
   - TypeScript代码库
   - **推荐指数**: ⭐⭐⭐⭐⭐（仅供参考架构）

2. **EduChat** (928 stars)
   - 需要GPU部署
   - 模型训练复杂
   - **推荐指数**: ⭐⭐（仅供参考）

### 📚 仅供参考（小型项目）

- AI Lesson Planner (3 stars)
- Better Lessons (4 stars)
- AI Course Generator (47 stars)
- **推荐指数**: ⭐⭐

---

## 代码质量评估

### 🏆 优秀（文档完整、代码清晰）

1. **DeepTutor**: 43贡献者，活跃开发，文档完整
2. **Presenton**: 7贡献者，持续更新，架构清晰
3. **PPTAgent**: 23贡献者，学术背景，代码规范

### ✅ 良好

1. **Presentation AI**: TypeScript，代码结构清晰
2. **SlideTailor**: 学术项目，代码规范

### ⚠️ 一般（小型项目）

- AI-PPT-Builder: 单人开发
- AI Lesson Planner: 单人开发
- Better Lessons: 单人开发

---

## 总结

### 按使用场景推荐

#### 场景1: 直接替换FastPPT
**推荐**: 无完美替代品
- **Presenton**: 最接近，但缺少教案生成和RAG
- **建议**: 保留FastPPT，借鉴其他项目优化

#### 场景2: 学习先进架构
**推荐**: OpenMAIC + PPTAgent
- **OpenMAIC**: 两阶段生成架构
- **PPTAgent**: 反思式框架

#### 场景3: 快速部署可用方案
**推荐**: Presenton
- Docker一键部署
- API支持
- 多模型支持

#### 场景4: 构建SaaS平台
**推荐**: AI-PPT-Builder
- 完整SaaS架构
- 认证+订阅+支付

#### 场景5: 教育大模型
**推荐**: EduChat + DeepTutor
- EduChat: 教育垂直LLM
- DeepTutor: 学习助手

---

## 下一步行动建议

见最终推荐方案报告（.omc/ai-courseware-analysis.md）
