# FastPPT 开发导航

本页只保留当前有效的开发入口，不再引用旧 Step 文件名。

## 开发前先读

1. `../ai-context/PROJECT.md`
2. `../ai-context/REPO_MAP.md`
3. `../ai-context/CAPABILITY_INDEX.yaml`

## 常见任务的最短阅读路径

### 调整生成前意图收集

- `../ai-context/capabilities/teaching-spec.md`
- `../ai-context/capabilities/chat-clarification.md`
- `../backend/core/README.md`

### 调整检索与来源追溯

- `../ai-context/capabilities/rag-evidence.md`
- `../backend/core/README.md`

### 调整预览和页面结构

- `../ai-context/capabilities/slide-blocks.md`
- `../ai-context/capabilities/preview-renderer.md`
- `../frontend/src/components/README.md`

### 调整导出

- `../ai-context/capabilities/export-pptx.md`
- `../ai-context/capabilities/export-docx.md`
- `../backend/core/README.md`

## 约束

- 默认先维护稳定主链路：上传 -> 对话澄清 -> 生成 -> 预览 -> 修改 -> 导出
- 比赛安全运行时默认走 plain chat path
- 变更行为时，同时更新能力卡或局部 README，避免代码与文档再次分叉

