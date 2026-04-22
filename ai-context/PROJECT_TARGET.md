# FastPPT 项目总览（Target / 蓝图）

## 一句话

FastPPT 的目标不是 casual AI PPT 工具，而是面向教师备课的 AI 课件协作系统：让资料复用、教学规格结构化、来源可追溯、结果可修改、课程资产可沉淀。

## 目标主链路

多源资料接入 -> 对话澄清 -> TeachingSpec -> 检索与 evidence -> SlidePlan -> SlideDraft -> RevisionPatch -> PPTX/DOCX 导出 -> 课程长期记忆

## Target 能力重点

- TeachingSpec：把模糊输入编译为统一教学规格
- evidence binding：每页内容尽量绑定来源
- SlidePlan/SlideDraft：先规划结构再生成页面
- RevisionPatch：页级局部 patch，避免整套重生
- Mode A：旧 PPT / 参考大纲复用
- course memory：课程长期知识沉淀

## 目标状态判断

FastPPT 的长期壁垒不只是“能出一份 PPT”，而是：

- 更懂教学场景
- 更能继承旧资料
- 更能解释结果从哪里来
- 更能围绕一门课持续迭代

