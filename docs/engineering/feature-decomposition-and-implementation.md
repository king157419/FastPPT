# 步骤 3：功能拆解与实现路径

本页把“产品定位”拆成工程模块，并标注当前进度。

## 1. 模块拆解（从需求到代码）

1. 需求结构化层（Intent -> TeachingSpec）
   - 作用：把对话结果变成稳定字段
   - 代码：`backend/core/teaching_spec.py`
   - 状态：已落地（P0 完成）
   - 必含字段：教学目标、学生类型、重点难点（生成前强确认）

2. 检索与证据层（RAG）
   - 作用：从资料库召回支持内容
   - 代码：`backend/core/rag.py`
   - 状态：已有基础实现（TF-IDF + 向量模式入口）

3. 内容规划层（Outline）
   - 作用：先生成页级大纲，再逐页展开
   - 状态：未完整落地（当前仍偏单阶段）

4. 页面生成层（Page Generation）
   - 作用：按页生成内容，支持并发
   - 状态：未完整落地（当前单次生成所有 pages）

5. 块协议层（Page -> Blocks）
   - 作用：把页面内容标准化为可插拔块
   - 代码：`backend/core/slide_blocks.py`
   - 状态：已落地（P0 完成）

6. 渲染与导出层（Preview + PPTX）
   - 作用：前端预览、PPTX 输出
   - 代码：`frontend/src/components/SlideRenderer.vue`, `PreviewPanel.vue`
   - 状态：运行中，但仍以 `page.type` 为主，尚未吃 `blocks[]`

7. 课程记忆层（Course Memory）
   - 作用：保存课程常用教材、案例、图表、风格偏好、修订记录
   - 状态：需求已确认，待实现

## 2. 可插拔信息块方案（你提的方向）

### 2.1 当前已实现的块协议（后端）

`slide_blocks.v1` 结构（简化）：

```json
{
  "id": "p01-b01",
  "type": "CodeBlock",
  "payload": { "language": "python", "code": "..." },
  "anchors": [],
  "layoutHints": { "slot": "body" },
  "styleHints": {},
  "renderStrategy": "code-panel",
  "validationRules": ["non_empty_payload", "max_lines_soft_limit"]
}
```

已覆盖的块类型：

- `TextBlock`
- `BulletBlock`
- `CodeBlock`
- `FormulaBlock`
- `CaseBlock`
- `TableBlock`
- `ImageBlock`
- `FlowchartBlock`

### 2.2 下一步要做的“真可插拔”

1. 前端渲染器改为 `BlockRenderer`（按 block.type 分发）
2. 导出器改为 `BlockExportRegistry`（按 block.type 导出）
3. 新块只需注册，不改主流程（例如 `QuizBlock`、`TimelineBlock`）
4. 每种块增加最小验证器，降低渲染崩溃概率

## 3. P0/P1 执行清单

P0（本周）：

1. 完成两阶段最小闭环：`outline -> per-page generation`
2. 前端支持 `blocks[]` 渲染（保留 `page.type` 兼容）
3. 每页输出来源证据（至少段落级引用）
4. 生成前校验“教学目标/学生类型/重点难点”三项是否齐全

P1（下阶段）：

1. 公式 OMML 原生导出
2. 图文相关性评分 + 自动修正
3. 局部重生成（按页/按块）
4. 课程记忆（可开关、可清除、可审计）

## 4. 对“步骤 3 是否完成”的判断

- 已完成：约 70%
  - 拆解基本完整
  - 部分核心骨架已写入代码
- 未完成：关键链路仍在
  - 真正两阶段生成未打通
  - 前端/导出尚未基于 `blocks[]` 全面运行

结论：步骤 3 已进入“工程实现期”，但不能算完全结束。

## 5. 2026-04-22 Progress Update

- Implemented preflight required-field gate end-to-end.
- Backend now validates `teaching_goal`, `audience`, `difficulty_focus` in both `POST /generate` and `POST /generate/start`.
- Missing required fields return `422` with readable field labels.
- Frontend `GenerateBtn.vue` now includes a preflight form and disables generation until required fields are completed.
- Current Step3 status: architecture and first enforcement path landed; block-first rendering/export is still pending.
