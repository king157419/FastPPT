---
name: OpenMAIC 架构分析笔记
description: 清华 OpenMAIC（11.5k star）AI课件生成系统核心架构分析，用于指导 FastPPT 改进
type: reference
---

## OpenMAIC 核心架构

### 两阶段生成流程

**Stage 1 — 大纲生成（outline-generator.ts）**
- 输入：用户自由文本需求 + PDF内容 + 图片
- 输出：`SceneOutline[]`，每项只有 `{ id, type, title, keyPoints[], order }`
- 使用 `requirements-to-outlines/system.md` 提示词（约200行）

**Stage 2 — 逐页内容生成（scene-generator.ts）**
- 输入：单个 `SceneOutline` + 全部大纲上下文 + 参考图片
- 输出：完整页面内容（元素坐标、文字、图表等）
- **关键**：`Promise.all` 并发生成所有页面，每页独立调用 LLM
- 使用 `slide-content/system.md` 提示词（983行）

### SceneOutline 结构
```typescript
interface SceneOutline {
  id: string
  type: 'slide' | 'quiz' | 'interactive' | 'pbl'
  title: string
  keyPoints: string[]   // 3-5个具体知识点，Stage 2 据此展开
  order: number
  language: 'zh-CN' | 'en-US'
  suggestedImageIds?: string[]
  mediaGenerations?: { type, prompt, elementId, aspectRatio }[]
}
```

### 幻灯片元素类型（element-types）
- **text**：HTML字符串（支持h1/h2/p/ul/li），坐标系 1000×562.5px
- **image**：src为图片ID或URL，fixedRatio
- **shape**：SVG path + fill
- **chart**：bar/line/pie/radar，含data和themeColors
- **latex**：LaTeX字符串 → SVG path（latexToOmml转OOXML原生公式）
- **line**：起止坐标+样式

### Action 系统（action-types）
- speech：语音旁白
- spotlight：聚焦元素
- laser：激光笔
- discussion：互动讨论
- 共15+种

### 场景类型
- **slide**：静态PPT页，支持所有元素类型
- **quiz**：单选/多选/简答题
- **interactive**：自包含HTML iframe（物理模拟、数学可视化）
- **pbl**：项目制学习模块，15-30分钟，含角色/问题/协作流程

### PDF图片处理（PdfImage系统）
```typescript
interface PdfImage {
  id: string      // "img_1"
  src: string     // base64或URL
  pageNumber: number
  description: string  // VLM理解结果
}
```
大纲生成时，suggestedImageIds 指定每页使用哪些图片，Stage 2 直接嵌入。

---

## OpenMAIC vs FastPPT 差距

| 能力 | OpenMAIC | FastPPT 现状 |
|---|---|---|
| 生成阶段 | 两阶段（大纲→逐页内容） | **一阶段直出**（内容稀薄根本原因）|
| 坐标系 | 像素坐标 1000×562.5，精确布局 | em相对单位，CSS流式 |
| LaTeX导出 | latexToOmml()→PowerPoint原生公式（可编辑）| Georgia斜体文本近似 |
| 幻灯片元素 | text/image/shape/chart/latex/line 自由组合 | 9种固定模板 |
| 动作系统 | speech/spotlight/whiteboard等15种 | 无 |
| 并发生成 | Promise.all 并发所有页面 | 单次调用返回全部 |
| keyPoints精度 | 大纲阶段确定每页3-5个具体知识点 | LLM自由发挥，经常空洞 |

---

## FastPPT 改进方向（按优先级）

### P0：改为两阶段生成（解决内容空洞根本问题）
1. Stage 1：LLM生成大纲（页数+每页title+type+keyPoints[3-5条]）
2. Stage 2：并发逐页生成，每页专注展开该页的keyPoints

### P1：改进提示词
- 大纲阶段：keyPoints必须是具体知识点，不能是模糊标题
- 内容阶段：每页传入完整课程上下文+当前页keyPoints，专注展开

### P2：LaTeX 公式导出用 OMML
- 用 `latex-to-ooxml` 库将 LaTeX → PowerPoint 原生公式
- 目前用Georgia斜体，复杂公式如 \\frac、\\sum 会显示原始字符串

### P3：interactive 类型（自包含HTML）
- 类似 OpenMAIC 的 interactive scene
- 物理模拟、数学可视化等用 iframe 嵌入
- FastPPT 已有 animation 模板雏形（bar_chart/flowchart等）

---

## OpenMAIC Slide Content System Prompt 核心规则（slide-content/system.md）

**设计哲学**：幻灯片是视觉辅助，不是讲稿。
- ✅ 关键词、短语、要点、数据、公式
- ❌ 完整句子、口语化段落、过渡语（"现在我们来看..."）
- 每个 bullet ≤20词 / ≤30中文字

**画布坐标系**：1000 × 562.5 px，边距≥50px

**元素类型（JSON格式）**：
```json
// TextElement
{"id":"text_001","type":"text","left":60,"top":80,"width":880,"height":60,
 "content":"<h2>标题</h2>","defaultFontName":"Microsoft YaHei","defaultColor":"#333"}

// ShapeElement（矩形）
{"id":"shape_001","type":"shape","left":60,"top":200,"width":400,"height":100,
 "path":"M 0 0 L 1 0 L 1 1 L 0 1 Z","viewBox":[1,1],"fill":"#5b9bd5","fixedRatio":false}

// LaTeXElement
{"id":"latex_001","type":"latex","left":100,"top":200,"width":300,"height":80,
 "latex":"E = mc^2","color":"#333","strokeWidth":2,"fixedRatio":true,"align":"center"}

// ChartElement
{"id":"chart_001","type":"chart","left":100,"top":150,"width":500,"height":300,
 "chartType":"bar","data":{"labels":[...],"datasets":[...]},"themeColors":["#5b9bd5"]}
```

## 大纲生成 keyPoints 示例（requirements-to-outlines/system.md）

图表类 keyPoints 写法：
```
"keyPoints": [
  "展示四年销售增长趋势",
  "[Chart] 折线图：X轴年份(2020-2023)，Y轴销售额(120-210万)",
  "分析增长因素和关键里程碑"
]
```

场景时长：每个 slide 场景 1-3 分钟，PBL 15-30 分钟。

## 两阶段 Prompt 策略对比

| | Stage 1（大纲）| Stage 2（内容）|
|---|---|---|
| 输入 | 用户需求+PDF摘要 | 单页大纲+全部大纲标题+参考图片 |
| 输出 | SceneOutline[] | 单页elements[]（坐标+内容）|
| Token消耗 | 低 | 中（每页独立）|
| 质量 | 结构清晰 | 内容详实（专注一页）|
