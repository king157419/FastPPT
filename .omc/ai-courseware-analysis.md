# AI备课/PPT生成开源项目调研分析 - 最终推荐方案

## 执行摘要

本报告基于对GitHub上20个AI备课/PPT生成开源项目的深度调研，针对FastPPT项目提出具体的改进建议和实施路径。

**核心发现**:
- **DeepTutor** (18.4k stars) 是最受欢迎的教育AI项目，但偏重学习助手
- **Presenton** (4.7k stars) 是最成熟的开源PPT生成器，可直接使用
- **OpenMAIC** (11.5k stars) 拥有最先进的两阶段生成架构
- **PPTAgent** (4.1k stars) 提供反思式生成框架

---

## Top 3 推荐项目

### 🥇 第一名: Presenton (4.7k stars)

**推荐理由**:
1. ✅ **开箱即用**: Docker一键部署，无需复杂配置
2. ✅ **API支持**: 提供REST API，可批量生成
3. ✅ **多模型**: 支持OpenAI/Gemini/Ollama
4. ✅ **多平台**: Web + Electron桌面版
5. ✅ **活跃开发**: 2026年4月仍在持续更新
6. ✅ **导出格式**: PPTX + PDF

**技术栈**:
- 前端: Next.js + TypeScript + React
- 后端: FastAPI + Python
- 数据库: SQLite
- 部署: Docker + Electron

**适用场景**:
- 需要快速部署一个可用的PPT生成服务
- 需要API接口进行批量生成
- 需要本地运行保护数据隐私

**与FastPPT对比**:
| 功能 | Presenton | FastPPT |
|------|-----------|---------|
| PPT生成 | ✅ | ✅ |
| 教案生成 | ❌ | ✅ |
| 文件解析 | ❌ | ✅ (4种格式) |
| RAG检索 | ❌ | ✅ (TF-IDF) |
| 多轮对话 | ❌ | ✅ (5轮) |
| API支持 | ✅ | ❌ |
| 多模型 | ✅ | ❌ (仅DeepSeek) |

**实施建议**: 
- **不建议直接替换FastPPT**（缺少教案、RAG、对话功能）
- **建议参考其API设计**，为FastPPT添加API接口
- **建议参考其多模型支持**，扩展FastPPT的LLM选择

---

### 🥈 第二名: OpenMAIC (11.5k stars)

**推荐理由**:
1. ✅ **架构最先进**: 两阶段生成（大纲→内容）
2. ✅ **质量最高**: 精确坐标系、LaTeX原生支持
3. ✅ **功能最丰富**: 交互式场景、PBL、Action系统
4. ✅ **学术背景**: 清华大学开源
5. ✅ **并发生成**: Promise.all并发所有页面

**核心架构**:
```
Stage 1: 大纲生成
  输入: 用户需求 + PDF + 图片
  输出: SceneOutline[] (每页3-5个具体keyPoints)
  
Stage 2: 逐页内容生成
  输入: 单个SceneOutline + 全部上下文
  输出: 完整页面元素（坐标+内容）
  策略: Promise.all并发生成
```

**与FastPPT的核心差异**:
| 维度 | OpenMAIC | FastPPT |
|------|----------|---------|
| 生成阶段 | **两阶段** | 单阶段 |
| 并发策略 | **Promise.all并发** | 单次调用 |
| 坐标系 | **像素坐标** (1000×562.5) | em相对单位 |
| LaTeX | **原生公式**（可编辑） | 文本近似 |
| 元素类型 | **6种自由组合** | 9种固定模板 |

**实施建议**:
- **不建议直接使用**（需要深度集成，学习成本高）
- **强烈建议参考架构**，改造FastPPT为两阶段生成
- **建议参考提示词**（大纲200行+内容983行）

**FastPPT改进路径**（基于OpenMAIC）:

#### P0: 实现两阶段生成（解决内容空洞根本问题）
```python
# Stage 1: 大纲生成
def generate_outline(user_input, pdf_content):
    prompt = """
    根据用户需求生成PPT大纲：
    - 确定页数（建议10-20页）
    - 每页标题
    - 每页3-5个具体知识点（不能是模糊标题）
    """
    return outline  # List[{title, keyPoints[]}]

# Stage 2: 并发逐页生成
async def generate_slides(outline):
    tasks = [
        generate_single_slide(page, outline_context)
        for page in outline
    ]
    return await asyncio.gather(*tasks)
```

#### P1: 改进提示词
- 大纲阶段：keyPoints必须具体（如"展示2020-2023销售增长趋势"）
- 内容阶段：传入完整上下文+当前页keyPoints

#### P2: LaTeX原生支持
- 使用 `latex-to-ooxml` 库
- 将LaTeX转为PowerPoint原生公式

---

### 🥉 第三名: PPTAgent (4.1k stars)

**推荐理由**:
1. ✅ **反思式框架**: 生成→评估→改进
2. ✅ **评分系统**: PPTEval（设计、流程、质量）
3. ✅ **学术背景**: EMNLP 2025论文
4. ✅ **Docker部署**: 一键启动
5. ✅ **MCP支持**: Model Context Protocol

**核心特性**:
- Agentic框架：自主规划、执行、反思
- 环境感知反思：根据生成结果调整策略
- 多文档支持：处理复杂输入

**与FastPPT对比**:
- PPTAgent: 反思式，质量高但速度慢
- FastPPT: 直接生成，速度快但质量不稳定

**实施建议**:
- **建议参考反思机制**，为FastPPT添加质量评估
- **建议参考PPTEval**，实现自动评分系统
- **可选集成**：将PPTAgent作为FastPPT的"高质量模式"

---

## 针对FastPPT的具体改进方案

### 方案A: 渐进式改进（推荐）

#### 阶段1: 快速增强（1-2周）
1. **添加API接口**（参考Presenton）
   - POST /api/generate - 生成PPT
   - GET /api/status/{id} - 查询状态
   - GET /api/download/{id} - 下载文件

2. **多模型支持**（参考Presenton）
   - 支持OpenAI、Claude、Gemini
   - 配置文件选择模型

3. **改进提示词**（参考OpenMAIC）
   - 要求LLM输出具体知识点
   - 增加示例和约束

#### 阶段2: 架构升级（2-4周）
1. **实现两阶段生成**（参考OpenMAIC）
   ```python
   # 第一阶段：生成大纲
   outline = llm.generate_outline(user_input)
   
   # 第二阶段：并发生成内容
   slides = await asyncio.gather(*[
       llm.generate_slide(page, outline)
       for page in outline
   ])
   ```

2. **添加质量评估**（参考PPTAgent）
   - 生成后自动评分
   - 低分自动重试

#### 阶段3: 功能扩展（4-8周）
1. **LaTeX原生支持**（参考OpenMAIC）
2. **交互式元素**（参考OpenMAIC）
3. **更多模板**（参考Presenton）

### 方案B: 直接替换（不推荐）

**原因**:
- 没有单一项目能完全替代FastPPT的全栈功能
- FastPPT的优势（教案+RAG+对话）是其他项目没有的
- 重新部署和迁移成本高

### 方案C: 混合架构（可选）

**架构**:
```
FastPPT (主系统)
  ├─ 文件解析
  ├─ RAG检索
  ├─ 多轮对话
  └─ 调用外部PPT生成服务
      ├─ Presenton (快速模式)
      ├─ PPTAgent (高质量模式)
      └─ 自研两阶段生成 (默认)
```

**优势**:
- 保留FastPPT的核心功能
- 灵活选择PPT生成引擎
- 逐步迁移，风险低

---

## 功能模块借鉴清单

### 从Presenton借鉴
- ✅ API设计模式
- ✅ 多模型支持架构
- ✅ Electron桌面版打包
- ✅ PPTX模板系统

### 从OpenMAIC借鉴
- ✅ 两阶段生成架构（**最重要**）
- ✅ 并发生成策略
- ✅ 提示词工程（1000+行）
- ✅ LaTeX原生支持
- ✅ 精确坐标系统

### 从PPTAgent借鉴
- ✅ 反思式生成框架
- ✅ PPTEval评分系统
- ✅ Agentic架构

### 从DeepTutor借鉴
- ✅ 双回路架构（分析+求解）
- ✅ 交互式可视化
- ✅ 多模型统一接口

---

## 实施路径对比

### 路径1: 直接替换 ❌
- **时间**: 1周
- **成本**: 低
- **风险**: 高（功能缺失）
- **推荐度**: ⭐

### 路径2: 功能借鉴 ✅
- **时间**: 4-8周
- **成本**: 中
- **风险**: 低
- **推荐度**: ⭐⭐⭐⭐⭐

### 路径3: 架构参考 ✅
- **时间**: 2-4周（仅两阶段生成）
- **成本**: 中
- **风险**: 中
- **推荐度**: ⭐⭐⭐⭐

### 路径4: 混合架构 ⚠️
- **时间**: 6-12周
- **成本**: 高
- **风险**: 中
- **推荐度**: ⭐⭐⭐

---

## 最终推荐

### 🎯 推荐方案: 渐进式改进（方案A）

**第一步**（立即执行）:
1. 参考OpenMAIC，改造FastPPT为两阶段生成
2. 改进提示词，要求输出具体知识点
3. 实现并发生成策略

**第二步**（1个月内）:
1. 参考Presenton，添加API接口
2. 支持多种LLM模型
3. 优化部署流程

**第三步**（2-3个月内）:
1. 参考PPTAgent，添加质量评估
2. 参考OpenMAIC，支持LaTeX原生公式
3. 扩展更多模板和元素类型

**预期效果**:
- ✅ 解决内容空洞问题（两阶段生成）
- ✅ 提升生成速度（并发策略）
- ✅ 提高内容质量（改进提示词）
- ✅ 增强灵活性（多模型支持）
- ✅ 保留现有优势（教案+RAG+对话）

---

## 技术债务警告

### 当前FastPPT的技术债务
1. **单阶段生成**: 导致内容空洞（P0优先级）
2. **固定模板**: 限制表达能力
3. **单一模型**: 依赖DeepSeek
4. **无API接口**: 难以集成
5. **无质量评估**: 输出质量不稳定

### 建议优先解决
1. **P0**: 两阶段生成架构（解决内容空洞）
2. **P1**: 改进提示词（提升质量）
3. **P2**: 多模型支持（降低依赖）
4. **P3**: API接口（提升可用性）

---

## 附录：项目资源链接

### 推荐项目
- Presenton: https://github.com/presenton/presenton
- OpenMAIC: https://github.com/ICALK/OpenMAIC (需验证)
- PPTAgent: https://github.com/icip-cas/pptagent
- DeepTutor: https://github.com/HKUDS/DeepTutor

### 参考文档
- OpenMAIC架构分析: `.omc/openmaic-architecture.md`
- 功能对比矩阵: `.omc/feature-comparison.md`
- GitHub统计数据: `.omc/github-stats.json`
- 项目清单: `.omc/project-inventory.md`

---

## 结论

**没有单一项目可以直接替代FastPPT**，但通过借鉴顶级项目的架构和功能，FastPPT可以在保留现有优势的基础上，大幅提升PPT生成质量。

**最关键的改进是实现两阶段生成架构**（参考OpenMAIC），这将从根本上解决内容空洞问题。

**建议采用渐进式改进策略**，分阶段实施，降低风险，确保每个阶段都有可验证的成果。

---

**报告生成时间**: 2026-04-21  
**调研项目数量**: 20个  
**推荐项目数量**: 3个  
**实施方案数量**: 4个
