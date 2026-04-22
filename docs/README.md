# FastPPT 文档入口

`docs/` 现在只承担稳定文档层，不再让旧的 Step 命名承担默认入口职责。

## 推荐阅读顺序

1. `../ai-context/PROJECT.md`
2. `../ai-context/CAPABILITY_INDEX.yaml`
3. 按任务读取 1 到 3 张能力卡
4. 再进入本目录的专题文档

## 文档分层

### `product/`

产品与用户理解层，优先从这里理解为什么做这件事。

- `product/problem-needs.md`
- `product/product-positioning.md`
- `product/teacher-feedback.md`
- `product/teacher-interview-form.md`

### `engineering/`

工程拆解与实现状态。

- `engineering/feature-decomposition-and-implementation.md`

### `archive/`

历史材料归档。

- `archive/strategy-history/`

## 迁移说明

- `00-START-HERE.md`、`10-Step1-*`、`20-Step2-*`、`30-Step3-*` 已迁入 `archive/strategy-history/`
- 稳定内容已复制到 `product/` 和 `engineering/`
- 后续新增结论优先更新 `ai-context/` 和稳定专题目录，不再继续扩写新的 Step 文档

