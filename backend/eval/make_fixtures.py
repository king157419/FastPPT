"""Generate and cache slides_json fixtures so renderer iteration needs no LLM calls.

Run once: python eval/make_fixtures.py
Writes outputs/_fix_<key>.json = {"intent":..., "slides_json":...} for math/cs/general.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
sys.path.insert(0, BACKEND)


def _load_env() -> None:
    env_path = os.path.join(BACKEND, ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


INTENTS = {
    "math": {
        "topic": "高等数学 - 拉格朗日中值定理",
        "teaching_goal": "理解定理条件与几何意义，会用其证明不等式",
        "audience": "大学本科一年级",
        "difficulty_focus": "定理条件的理解与辅助函数构造",
        "key_points": ["定理表述与条件", "几何意义", "证明思路", "典型应用"],
        "duration": "45分钟",
        "style": "简洁学术",
    },
    "cs": {
        "topic": "数据结构 - 快速排序",
        "teaching_goal": "掌握快排分治思想、能手写实现并分析复杂度",
        "audience": "计算机专业本科二年级",
        "difficulty_focus": "基准选择与最坏情况复杂度",
        "key_points": ["分治思想", "划分过程", "代码实现", "复杂度分析"],
        "duration": "45分钟",
        "style": "简洁学术",
    },
    "general": {
        "topic": "计算机网络 - TCP 三次握手",
        "teaching_goal": "理解三次握手过程与为何需要三次",
        "audience": "计算机专业本科二年级",
        "difficulty_focus": "为何两次握手不够、状态迁移",
        "key_points": ["三次握手过程", "状态迁移", "为何需要三次", "与四次挥手对比"],
        "duration": "45分钟",
        "style": "简洁学术",
    },
}


def main() -> None:
    _load_env()
    os.environ["TWO_STAGE_GEN"] = "1"
    from core.two_stage_gen import generate_slides_json_two_stage

    out_dir = os.path.join(BACKEND, "outputs")
    os.makedirs(out_dir, exist_ok=True)
    for key, intent in INTENTS.items():
        sj = generate_slides_json_two_stage(intent, [])
        path = os.path.join(out_dir, f"_fix_{key}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"intent": intent, "slides_json": sj}, fh, ensure_ascii=False, indent=2)
        types = [p.get("type") for p in sj.get("pages", [])]
        print(f"[{key}] pages={len(types)} types={types} -> {path}")


if __name__ == "__main__":
    main()
