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
