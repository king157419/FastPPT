# AI备课/PPT生成开源项目清单

## 搜索时间：2026-04-21
## 数据来源：GitHub + Tavily搜索

---

## 一、综合型AI备课系统（教案+PPT）

### 1. OpenMAIC
- **GitHub**: https://github.com/ICALK/OpenMAIC (推测，需验证)
- **Stars**: 11,500+ (根据memory记录)
- **描述**: 清华大学开源的AI课件生成系统，采用两阶段生成架构
- **核心功能**: 
  - Stage 1: 大纲生成（SceneOutline）
  - Stage 2: 逐页内容生成（并发生成）
  - 支持多种场景类型：slide/quiz/interactive/pbl
  - 精确坐标系布局（1000×562.5px）
  - LaTeX公式原生支持
- **技术栈**: TypeScript, Node.js
- **分类**: 综合备课系统

### 2. DeepTutor
- **GitHub**: https://github.com/HKUDS/DeepTutor
- **Stars**: 6,100+
- **描述**: 香港大学数据智能实验室开源的AI个人学习助手
- **核心功能**:
  - Interactive Visualization（交互式学习可视化）
  - Dual-Loop架构（分析回路+求解回路）
  - 引导式教学，避免直接给答案
- **技术栈**: Python, FastAPI, React
- **分类**: 学习助手（偏重教学过程）

### 3. EduChat
- **GitHub**: https://github.com/ECNU-ICALK/EduChat
- **Stars**: 未知
- **描述**: 华东师范大学开源的教育对话大模型
- **核心功能**:
  - 教育垂直领域LLM
  - 支持作文指导、教案生成、心理疏导
  - EduChat-R1具备"教育思维链"
- **技术栈**: Python, LLM
- **分类**: 教育大模型基座

### 4. EduSpark
- **GitHub**: https://github.com/Azure12355/edu-spark
- **Stars**: 未知
- **描述**: 基于多模态大模型+Next.js+SpringAI的AI教学实训平台
- **核心功能**: 为教师和学生双向赋能
- **技术栈**: Next.js, Spring AI, 多模态LLM
- **分类**: 综合教学平台

---

## 二、专注PPT生成的项目

### 5. PPTAgent
- **GitHub**: https://github.com/icip-cas/pptagent
- **Stars**: 4,100+
- **描述**: 中科院开源的反思式PPT生成框架
- **核心功能**:
  - Agentic框架，支持反思和迭代
  - PPTEval评分系统（设计、流程、质量）
  - Docker一键部署
- **技术栈**: Python, MCP, OpenClaw
- **分类**: PPT生成

### 6. Presenton
- **GitHub**: https://github.com/presenton/presenton
- **Stars**: 未知
- **描述**: 开源AI演示文稿生成器（Gamma替代品）
- **核心功能**:
  - 本地运行，数据隐私
  - 支持OpenAI、Gemini、Ollama
  - API支持批量生成
  - 导出PPTX/PDF
- **技术栈**: FastAPI, Next.js, Python
- **分类**: PPT生成

### 7. Presentation AI (ALLWEONE)
- **GitHub**: https://github.com/allweonedev/presentation-ai
- **Stars**: 未知
- **描述**: 开源AI演示文稿生成器，Gamma替代品
- **核心功能**:
  - 可自定义主题
  - AI生成内容
  - 快速创建专业幻灯片
- **技术栈**: TypeScript, Next.js
- **分类**: PPT生成

### 8. SlideTailor
- **GitHub**: https://github.com/nusnlp/SlideTailor
- **Stars**: 未知
- **描述**: 新加坡国立大学开源的个性化学术论文PPT生成器
- **核心功能**:
  - 针对科研论文生成演示文稿
  - 个性化设计
  - AAAI 2026论文
- **技术栈**: Python, vLLM
- **分类**: 学术PPT生成

### 9. AI PPT Builder
- **GitHub**: https://github.com/be-a-guptaji/AI-PPT-Builder
- **Stars**: 未知
- **描述**: AI演示文稿SaaS平台
- **核心功能**:
  - 用户认证（Clerk）
  - 订阅管理（Lemon Squeezy）
  - 在线编辑和管理
- **技术栈**: Next.js, OpenAI, Prisma, Clerk
- **分类**: PPT SaaS平台

### 10. SlideDeck AI
- **GitHub**: 未找到具体链接
- **Stars**: 未知
- **描述**: 将任何主题转换为精美PPT
- **核心功能**:
  - AI生成内容
  - 智能图片搜索
  - 模板选择
- **技术栈**: 未知
- **分类**: PPT生成

### 11. Slidev
- **GitHub**: https://github.com/slidevjs/slidev
- **Stars**: 30,000+ (推测)
- **描述**: 面向开发者的Markdown演示文稿工具
- **核心功能**:
  - Markdown编写
  - 代码高亮
  - 主题定制（UnoCSS）
  - 非AI驱动，但支持AI集成
- **技术栈**: Vue, Vite, Markdown
- **分类**: 开发者演示工具

---

## 三、教案/课程生成项目

### 12. AI Lesson Planner (DivanshiJain2005)
- **GitHub**: https://github.com/DivanshiJain2005/AI-lesson-planner
- **Stars**: 未知
- **描述**: 基于RAG的AI教案生成器
- **核心功能**:
  - 自动生成定制化教案
  - 交互式内容生成
  - Streamlit界面
- **技术栈**: Python, Streamlit, OpenAI GPT
- **分类**: 教案生成

### 13. Better Lessons
- **GitHub**: https://github.com/llegomark/betterlessons
- **Stars**: 未知
- **描述**: AI驱动的教案生成器
- **核心功能**:
  - 个性化教案
  - 分析教学风格、班级规模、学生需求
  - 支持多种课程时长
- **技术栈**: TypeScript, Next.js, OpenAI API
- **分类**: 教案生成

### 14. AI Course Generator
- **GitHub**: https://github.com/bhataasim1/ai-course-generator
- **Stars**: 未知
- **描述**: AI课程生成平台
- **核心功能**:
  - 输入课程名称、时长、章节数
  - Gemini AI生成课程结构
  - 自动匹配YouTube视频
- **技术栈**: Next.js, Gemini AI, Drizzle ORM
- **分类**: 课程生成

### 15. Automated Course Content Generator (ACCG)
- **GitHub**: https://github.com/pramodkoujalagi/Automated-Course-Content-Generator
- **Stars**: 未知
- **描述**: 自动化课程内容生成器
- **核心功能**:
  - 生成课程大纲、完整内容、测验
  - 下载为PDF、PPT
  - 支持自定义
- **技术栈**: Python, Streamlit, OpenAI/Meta LLama-3
- **分类**: 课程内容生成

### 16. Lesson Plan Generator (ishitaakolkar)
- **GitHub**: https://github.com/ishitaakolkar/Lesson-Plan-Generator
- **Stars**: 未知
- **描述**: Streamlit教案生成应用
- **核心功能**:
  - 快速生成结构化教案大纲
  - Gemini API驱动
  - 支持SDG 4: 优质教育
- **技术栈**: Python, Streamlit, Gemini API
- **分类**: 教案生成

### 17. AI Study Material Generator
- **GitHub**: https://github.com/Adiaparmar/AI-Study-Material-Generator
- **Stars**: 未知
- **描述**: AI学习材料生成SaaS应用
- **核心功能**:
  - 生成个性化学习材料
  - 测验、摘要生成
  - 用户认证和订阅管理
- **技术栈**: Next.js, Gemini AI, Clerk, Stripe, Neon DB
- **分类**: 学习材料生成

---

## 四、工作流/框架类项目

### 18. n8n
- **GitHub**: https://github.com/n8n-io/n8n
- **Stars**: 40,000+
- **描述**: 开源工作流自动化平台
- **核心功能**:
  - 可视化工作流构建
  - 支持AI集成
  - 可用于构建教育自动化流程
- **技术栈**: TypeScript, Node.js, Vue
- **分类**: 工作流平台

### 19. Dify
- **GitHub**: https://github.com/langgenius/dify
- **Stars**: 50,000+
- **描述**: LLM应用开发平台
- **核心功能**:
  - 可视化AI应用构建
  - RAG支持
  - Agent编排
- **技术栈**: Python, TypeScript, React
- **分类**: AI应用平台

### 20. LangChain
- **GitHub**: https://github.com/langchain-ai/langchain
- **Stars**: 90,000+
- **描述**: LLM应用开发框架
- **核心功能**:
  - Chain构建
  - Agent支持
  - 丰富的集成
- **技术栈**: Python, TypeScript
- **分类**: LLM框架

---

## 项目统计

- **总计**: 20个项目
- **综合备课系统**: 4个
- **专注PPT生成**: 7个
- **教案/课程生成**: 7个
- **工作流/框架**: 3个

## 下一步

需要深入分析每个项目的：
1. 实际GitHub stars数量
2. 最后更新时间和活跃度
3. 详细技术架构
4. 与FastPPT的功能对比
