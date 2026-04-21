# OpenMAIC 架构深度分析

## 项目概况

- **开发单位**: 清华大学
- **GitHub Stars**: 11,500+ (根据memory记录)
- **核心特点**: 两阶段生成架构，精确坐标系布局

---

## 一、两阶段生成流程

### Stage 1: 大纲生成 (outline-generator.ts)

**输入**:
- 用户自由文本需求
- PDF内容
- 图片

**输出**:
```typescript
interface SceneOutline {
  id: string
  type: 'slide' | 'quiz' | 'interactive' | 'pbl'
  title: string
  keyPoints: string[]   // 3-5个具体知识点
  order: number
  language: 'zh-CN' | 'en-US'
  suggestedImageIds?: string[]
  mediaGenerations?: { type, prompt, elementId, aspectRatio }[]
}
```

**关键特性**:
- 使用 `requirements-to-outlines/system.md` 提示词（约200行）
- keyPoints 必须是具体知识点，不能是模糊标题
- 例如图表类：`"[Chart] 折线图：X轴年份(2020-2023)，Y轴销售额(120-210万)"`

### Stage 2: 逐页内容生成 (scene-generator.ts)

**输入**:
- 单个 SceneOutline
- 全部大纲上下文
- 参考图片

**输出**:
- 完整页面内容（元素坐标、文字、图表等）

**关键特性**:
- **Promise.all 并发生成所有页面**，每页独立调用 LLM
- 使用 `slide-content/system.md` 提示词（983行）
- 每个页面专注展开该页的 keyPoints

---

## 二、坐标系统

### 画布规格
- **尺寸**: 1000 × 562.5 px
- **边距**: ≥50px
- **特点**: 精确像素坐标，非相对单位

### 元素定位示例
```json
{
  "id": "text_001",
  "type": "text",
  "left": 60,
  "top": 80,
  "width": 880,
  "height": 60,
  "content": "<h2>标题</h2>"
}
```

---

## 三、幻灯片元素类型系统

### 1. TextElement
```json
{
  "type": "text",
  "content": "<h2>标题</h2><ul><li>要点1</li></ul>",
  "defaultFontName": "Microsoft YaHei",
  "defaultColor": "#333"
}
```
- 支持 HTML 字符串（h1/h2/p/ul/li）
- 精确坐标定位

### 2. ImageElement
```json
{
  "type": "image",
  "src": "img_1",  // 图片ID或URL
  "fixedRatio": true
}
```

### 3. ShapeElement
```json
{
  "type": "shape",
  "path": "M 0 0 L 1 0 L 1 1 L 0 1 Z",
  "viewBox": [1, 1],
  "fill": "#5b9bd5",
  "fixedRatio": false
}
```
- SVG path 定义形状

### 4. ChartElement
```json
{
  "type": "chart",
  "chartType": "bar",  // bar/line/pie/radar
  "data": {
    "labels": ["2020", "2021", "2022"],
    "datasets": [...]
  },
  "themeColors": ["#5b9bd5"]
}
```

### 5. LaTeXElement
```json
{
  "type": "latex",
  "latex": "E = mc^2",
  "color": "#333",
  "strokeWidth": 2,
  "fixedRatio": true,
  "align": "center"
}
```
- 使用 `latexToOmml()` 转换为 PowerPoint 原生公式
- **可编辑**，不是图片

### 6. LineElement
```json
{
  "type": "line",
  "startX": 100,
  "startY": 200,
  "endX": 900,
  "endY": 200,
  "strokeWidth": 2,
  "color": "#333"
}
```

---

## 四、场景类型系统

### 1. slide（静态PPT页）
- 支持所有元素类型
- 标准演示文稿页面

### 2. quiz（测验）
- 单选题
- 多选题
- 简答题

### 3. interactive（交互式）
- 自包含 HTML iframe
- 物理模拟
- 数学可视化
- 类似 CodePen 嵌入

### 4. pbl（项目制学习）
- 15-30分钟模块
- 包含角色/问题/协作流程

---

## 五、Action 系统

支持15+种动作类型：
- **speech**: 语音旁白
- **spotlight**: 聚焦元素
- **laser**: 激光笔
- **discussion**: 互动讨论
- **whiteboard**: 白板书写
- 等等

---

## 六、PDF图片处理系统

```typescript
interface PdfImage {
  id: string           // "img_1"
  src: string          // base64或URL
  pageNumber: number
  description: string  // VLM理解结果
}
```

**流程**:
1. 大纲生成时，`suggestedImageIds` 指定每页使用哪些图片
2. Stage 2 直接嵌入图片

---

## 七、设计哲学

### Slide Content System Prompt 核心规则

**原则**: 幻灯片是视觉辅助，不是讲稿

✅ **应该包含**:
- 关键词、短语、要点
- 数据、公式
- 每个 bullet ≤20词 / ≤30中文字

❌ **不应包含**:
- 完整句子
- 口语化段落
- 过渡语（"现在我们来看..."）

---

## 八、与 FastPPT 的核心差异

| 维度 | OpenMAIC | FastPPT |
|------|----------|---------|
| **生成阶段** | 两阶段（大纲→逐页内容） | 一阶段直出 |
| **并发策略** | Promise.all 并发所有页面 | 单次调用返回全部 |
| **坐标系** | 像素坐标 1000×562.5，精确布局 | em相对单位，CSS流式 |
| **元素类型** | text/image/shape/chart/latex/line 自由组合 | 9种固定模板 |
| **LaTeX导出** | latexToOmml()→PowerPoint原生公式（可编辑） | Georgia斜体文本近似 |
| **动作系统** | speech/spotlight/whiteboard等15种 | 无 |
| **keyPoints精度** | 大纲阶段确定每页3-5个具体知识点 | LLM自由发挥，经常空洞 |
| **场景类型** | slide/quiz/interactive/pbl | 仅slide |

---

## 九、FastPPT 改进方向（基于OpenMAIC）

### P0: 改为两阶段生成（解决内容空洞根本问题）
1. Stage 1: LLM生成大纲（页数+每页title+type+keyPoints[3-5条]）
2. Stage 2: 并发逐页生成，每页专注展开该页的keyPoints

### P1: 改进提示词
- 大纲阶段：keyPoints必须是具体知识点，不能是模糊标题
- 内容阶段：每页传入完整课程上下文+当前页keyPoints，专注展开

### P2: LaTeX 公式导出用 OMML
- 用 `latex-to-ooxml` 库将 LaTeX → PowerPoint 原生公式
- 目前用Georgia斜体，复杂公式如 `\frac`、`\sum` 会显示原始字符串

### P3: interactive 类型（自包含HTML）
- 类似 OpenMAIC 的 interactive scene
- 物理模拟、数学可视化等用 iframe 嵌入
- FastPPT 已有 animation 模板雏形（bar_chart/flowchart等）

---

## 十、技术实现要点

### 提示词工程
- **大纲生成**: 200行系统提示词
- **内容生成**: 983行系统提示词
- 包含详细的格式规范、示例、约束条件

### 并发控制
```typescript
const slides = await Promise.all(
  outlines.map(outline => generateSlideContent(outline, context))
)
```

### 质量保证
- 每页独立生成，避免上下文污染
- 传入全部大纲标题作为上下文，保持连贯性
- keyPoints 作为强约束，确保内容聚焦

---

## 结论

OpenMAIC 的核心优势在于：
1. **两阶段架构**：先规划后执行，避免内容空洞
2. **并发生成**：提高效率，每页独立优化
3. **精确布局**：像素级坐标，专业视觉效果
4. **丰富元素**：支持图表、公式、交互等多种类型
5. **强提示词**：1000+行系统提示词，确保输出质量

FastPPT 要达到 OpenMAIC 的水平，最关键的是**实现两阶段生成架构**。
