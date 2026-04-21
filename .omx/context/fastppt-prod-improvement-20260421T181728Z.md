# Ralph Context Snapshot

## task statement
完成 FastPPT 生产级改进：基于赛题与产品定位，打通知识库→对话→生成PPT→修改PPT 全链路，后端 RAG/Agent/PptxGenJS/Docker 与前端集成可验收。

## desired outcome
1. 后端生成接口产出 slides_json + docx + pptx 文件。
2. 前端可下载后端生成的 pptx，并支持按页修改后重新生成（最小闭环）。
3. Docker compose 下 backend 与 pptxgenjs 服务接口一致并健康。
4. 关键功能点有自动化测试与端到端脚本验证。

## known facts/evidence
- generate.py 当前只返回 docx，不落地 pptx 文件。
- backend/core/ppt_gen.py 已有 PptxGenJS + python-pptx fallback，但未接入 generate 主链路。
- docker/pptxgenjs-server.js 暴露 /api/generate-ppt；services/pptxgenjs/server.js 暴露 /generate，存在契约不一致风险。
- 前端 PreviewPanel 使用浏览器端 pptxgenjs 导出，尚未默认走后端产物下载。
- 赛题定位强调：意图确认、资料利用、页级可修改、可追溯与可用四标准。

## constraints
- 不回滚现有脏工作树改动。
- 不新增依赖（除非必须）。
- 优先最小可验收增量，保留向后兼容。

## unknowns/open questions
- docker 路由最终以 /generate 还是 /api/generate-ppt 为准。
- 现有 agent 模式在无外部 key 下的降级策略是否稳定。

## likely codebase touchpoints
- backend/api/generate.py
- backend/core/ppt_gen.py
- backend/main.py
- frontend/src/components/GenerateBtn.vue
- frontend/src/components/PreviewPanel.vue
- frontend/src/api/index.js
- docker/pptxgenjs-server.js
- docker/docker-compose.yml
- 相关测试文件
