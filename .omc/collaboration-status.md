# FastPPT 协作计划（Claude + Codex via CLI）

## 协作方式
通过 `omc ask codex` 命令进行协作

## 第一轮任务分配

### Claude（我）负责：
1. ✅ BE-001: RAG系统升级（已完成）
2. 🔄 BE-002: LangChain Agent集成（进行中）
3. ⏳ BE-003: PptxGenJS服务
4. ⏳ BE-004: Docker部署

### Codex 负责：
1. 前端 RAG 文档上传 UI
2. 前端流式对话优化
3. 前端预览面板增强
4. 全链路测试

## 当前进度
- BE-001: ✅ 完成
  - ragflow_client.py: ✅
  - core/rag.py: ✅ 三层检索策略
  - api/retrieval.py: ✅ 4个API端点
  
- BE-002: 🔄 进行中
  - langchain_agent.py: ✅ 已存在
  - api/chat.py: ✅ 已重构，支持 Agent 模式
  - 需要测试验证

## 下一步
1. 完成 BE-002 验证
2. 开始 BE-003 (PptxGenJS)
3. 然后请 Codex 审视并规划前端任务
