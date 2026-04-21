# FastPPT 文档索引（新人入口）

这个目录是给新加入项目的人准备的“10 分钟快速理解层”，基于现有仓库代码、`.omc` 技术调研、以及近期访谈结论整理。

## 先看这 5 份

1. `00-START-HERE.md`：项目目标、目录地图、本地启动、当前系统事实
2. `10-Step1-Problem-And-Needs.md`：步骤 1（痛点与需求）结论
3. `20-Step2-Product-Positioning.md`：步骤 2（产品定位）结论
4. `30-Step3-Feature-Decomposition-And-Implementation.md`：步骤 3（功能拆解与实现路径）
5. `11-Teacher-Interview-Form.md`：可直接用于勾选式访谈/自答
6. `12-Teacher-Feedback-2026-04-22.md`：最新教师补充反馈记录

## 与 `.omc` 的关系

- `docs/`：决策层与执行层摘要（短、能落地）
- `.omc/`：技术研究底稿（长、细、可深挖）

建议阅读顺序：

1. 先读本目录 5 份文档
2. 再按需跳到 `.omc/README-INDEX.md`
3. 需要深挖时再看 `.omc/*-analysis.md`

## 当前阶段结论（2026-04-21）

- 步骤 1（痛点/需求）：已形成可执行结论，核心样本仍偏少，需要持续补教师样本
- 步骤 2（产品定位）：三档模式已定，V1 应优先覆盖“代劳”和“共创”
- 步骤 3（功能拆解）：已拆成模块并开始落地（后端已引入 `TeachingSpec` 与 `slide blocks` 归一化）
- 步骤 4（开发）：已开工，但“已完成 65%”这个判断不成立，仍在骨架搭建阶段

## 2026-04-22 Increment

- Preflight required fields are now enforced in both frontend and backend (`teaching_goal`, `audience`, `difficulty_focus`).
- See implementation status in `30-Step3-Feature-Decomposition-And-Implementation.md` section `2026-04-22 Progress Update`.
