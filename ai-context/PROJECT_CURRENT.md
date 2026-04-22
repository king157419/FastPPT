# FastPPT 项目总览（Current / grounded）

## 一句话

FastPPT 当前是一个面向教学场景的 AI 备课系统：支持上传参考资料，通过对话收集教学意图，结合检索生成 PPT 和 DOCX，并提供预览与 revise。

## 当前可验证主链路

上传资料 -> 对话澄清 -> TeachingSpec -> 检索 -> 生成 slides_json -> blocks 归一化 -> 导出 PPTX/DOCX -> 预览与 revise

## 当前公开仓库关键模块

- `backend/api/upload.py`
- `backend/api/chat.py`
- `backend/api/generate.py`
- `backend/api/download.py`
- `backend/core/parser.py`
- `backend/core/rag.py`
- `backend/core/teaching_spec.py`
- `backend/core/slide_pipeline.py`
- `backend/core/ppt_gen.py`
- `backend/core/doc_gen.py`
- `frontend/src/components/FileUpload.vue`
- `frontend/src/components/ChatPanel.vue`
- `frontend/src/components/GenerateBtn.vue`
- `frontend/src/components/PreviewPanel.vue`

## 当前最重要判断

1. 主链路已经能稳定演示，不再是仅有 mock 的空壳。
2. 关键优势在于从资料到可下载课件的一体链路，而不是复杂 agent。
3. 当前短板仍然是：PPT 质量上限、evidence 细粒度、block-first 全链路、revise patch 质量。

## 当前不要误判成 fully-done 的能力

- block-first 导出全量落地
- evidence 全页稳定绑定
- Mode A 深度结构复用
- 课程长期记忆

