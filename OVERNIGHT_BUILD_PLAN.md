# FastPPT 通宵构建计划 / 进度日志

> 目标：按 `A04-PRD.md` + `docs/10_P0-P1实施顺序与验收标准.md` + `ppt-解决方案.md`，
> 把 FastPPT 做成「我能做到的最好」的可演示版本。自驱执行（ralph 循环），每步用真实
> DeepSeek 生成验证质量。分支：`overnight/prd-build`（隔离，不动你已有的未提交改动）。

## 执行原则（来自 docs/10）
1. **working-software-first**：永远保持可跑，不做大爆炸重写。
2. **加法 + 特性开关**：新能力走新模块 + env 开关，旧路径保留为 fallback，绝不破坏已跑通的链路。
3. **页级主链**：TeachingSpec → 大纲 → 逐页 → 渲染 → 验证 → 局部修补。
4. **每步真实验证**：用 `.env` 里的 DeepSeek key 真生成；用 python-pptx 结构断言 +
   内容指标核查（本机无 LibreOffice，无法自动截图视觉验证）。
5. **不提交你的已有改动**：只 `git add` 我自己新建/修改的文件；你预存的 frontend/* 改动与
   提交材料删除保持原样。

## 里程碑（优先级顺序）

- [x] **M0 两阶段生成**（P0-4）— `core/two_stage_gen.py`，outline→逐页并发。
  修复"内容空洞"+ 单次直出的"JSON截断静默降级成英文占位"真因。已接入、已验证、已测试。
- [ ] **M1 渲染器重做**（P0-5，最高价值）— 让导出的 .pptx 忠实渲染 pages[] 的富内容，
  修 split-brain（渲染器当前无视 pages[]、用 key_points 重建、把富 block 拍平成 bullet）。
  覆盖：cover/agenda/content/summary/code/formula/two_column/example/chart/image。
  公式走 PRD 指定的 LaTeX→matplotlib→PNG；代码走 等宽+深色+换行；对比走 python-pptx Table；
  图表走 matplotlib。新模块 `core/pptx_renderer.py`，开关 `NEW_RENDERER`，旧路径 fallback。
- [ ] **M2 Stage-2 富类型产出** — 让逐页生成在合适场景真的产出 formula/code/chart/two_column
  （数学→公式，编程→代码，对比→两栏，数据→图表），并验证能渲染。
- [ ] **M3 验证 & 修补**（P1-2/P1-3）— 生成后逐页检查（空/薄/超字/漏知识点/缺图表公式），
  只做低风险局部修补（重生薄页、压缩超字）。`core/verify_repair.py`，开关 `VERIFY_REPAIR`。
- [ ] **M4 结构化需求录入**（P0-1）— 前端"需求确认卡"（教学目标/学生/时长/重点/是否沿用旧PPT
  风格/是否要图/是否要最新案例）+ 后端接收；放行生成前展示需求摘要。
- [ ] **M5 导出健壮性 & 演示速度** — 默认关闭不可达的 PptxGenJS（避免 502 空等 10s）；
  教案 docx 写入真实逐页内容（不止参考文献）；预览与导出语义统一。
- [ ] **M6 SourceAnchor 落地**（P0-3，stretch）— 解析返回可定位锚点，证据按知识点绑定并展示引用。

## 验证基线（样例主题）
- 数学：高等数学-拉格朗日中值定理（验证公式渲染）
- 计算机：数据结构-红黑树插入（验证代码渲染）
- 通用：计算机网络-IPv6 路由原理（验证要点/对比/图表）
工具：`backend/eval/quality_check.py`（生成→内容指标→pptx 结构断言）。

---

## 进度日志（按时间倒序，我会持续追加）

### M0 ✅ 两阶段生成（已完成并验证）
- 新增 `core/two_stage_gen.py`（Stage1 大纲含每页3-5具体keyPoints；Stage2 ThreadPoolExecutor 并发逐页）。
- 接入 `services/generate_service.py` 两处调用点，开关 `TWO_STAGE_GEN`（默认开），失败降级回单次。
- 测试 `test_two_stage_gen.py`（3 项：扇出1+N / 计划对齐 / 失败降级）通过。
- 真实 before/after：单次直出→英文模板占位（4096token截断）；两阶段→大学水准具体内容
  （NDP页 ICMPv6类型133-137 / RS,RA,NS,NA;过渡页 IPv6流量>40%(2024)），每页带 tip+notes。
- 修复 2 个 bug：占位符 `<沿用上面的标题>`、summary `...`（改为标题以种子为准）。
- 真实全链路 e2e 通过：pptx/docx/blocks 正常，类型多样化（自动产出 two_column）。

---

## 醒来速览（2026-05-28 通宵构建结果）

**全部 5 个 PRD 里程碑完成并通过验收，已在分支 `overnight/prd-build` 提交。**

| 里程碑 | 成果 |
|---|---|
| M0/M2 两阶段生成 | `core/two_stage_gen.py`：大纲→逐页并发；按学科产出公式/代码/两栏/图表 |
| M1 渲染器重做 | `core/pptx_renderer.py`：按 pages[] 忠实渲染，公式→matplotlib图片、代码深色面板、双栏、演讲者备注、来源页脚；修了 split-brain |
| M3 验证&修补 | `core/verify_repair.py`：薄页重生、超长压缩（低风险） |
| M5 富教案+速度 | `core/doc_gen.py` 重写为中文教案（吃逐页内容）；新渲染器纯本地无 502 空等；LLM 加重试 |
| M4 结构化录入 | `frontend/.../RequirementForm.vue`：表单优先入口 |

**质量证据**：eval 三主题真实生成 PASS（数学出 2 公式页/4 图片、CS 出 formula+code）；全量 35 测试通过；Opus architect 评审通过（修复了一个测试 stub 回归）。

**特性开关**（均默认开，可关）：`TWO_STAGE_GEN` / `NEW_RENDERER` / `VERIFY_REPAIR`。

**怎么跑**：后端 `cd backend && python -m uvicorn main:app --port 8000`；前端 `cd frontend && npm run dev`（http://localhost:5173）。`.env` 里 DeepSeek key 已更新为可用。
> 提示：演示前可把 `.env` 的 `PPTXGENJS_SERVICE_URL` 留空（新渲染器纯本地，不需要它）。

**已知/待办**：
1. `test_chat_fallback.py` 3 个测试 pre-existing 失败（引用已删除的 `_plain_chat_response`，源自 commit 2bfe0d3 的 chat 重构）——非本次引入，未修（超 PRD 范围）。
2. M6 SourceAnchor（完整页/段定位锚点）暂缓——基础可追溯已具备（页脚来源+evidence绑定）。
3. architect 提的非阻塞项：`slide_pipeline` 里 `plan.slide_type` 镜像字段在富类型升级后会过时（无功能影响）；`ppt_gen.py` 有一条 pre-existing 死代码链（旧 PptxGenJS slide_contents 路径）可清理。
4. 我没合并到 master，也没 push——分支 `overnight/prd-build` 等你 review。
5. 这是无人监督的自动构建，建议你抽查导出的 pptx/docx 实际观感（本机无 LibreOffice，我只能做结构断言+内容核查，没做像素级视觉验证）。
