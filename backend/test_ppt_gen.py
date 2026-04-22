"""Tests for PPT generation fallback behavior."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from core.ppt_gen import (
    _generate_pptx_pythonpptx,
    call_pptxgenjs_service,
    generate_pptx,
)


TEST_INTENT = {
    "topic": "Python基础编程",
    "audience": "初学者",
    "key_points": ["变量与数据类型", "控制流程", "函数定义"],
    "duration": "45分钟",
    "subject": "计算机科学",
    "teacher": "测试教师",
}

TEST_SLIDE_CONTENTS = [
    {
        "key_point": "变量与数据类型",
        "bullets": ["整数", "浮点数", "字符串", "布尔值"],
        "tip": "变量命名应清晰可读",
    },
    {
        "key_point": "控制流程",
        "bullets": ["if-elif-else", "for 循环", "while 循环", "break/continue"],
        "tip": "注意缩进层级",
    },
    {
        "key_point": "函数定义",
        "bullets": ["def 关键字", "参数传递", "返回值", "文档字符串"],
        "tip": "函数职责单一",
    },
]


def _output_path(name: str) -> str:
    output_dir = Path(__file__).resolve().parent / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    return str(output_dir / name)


def test_pythonpptx_fallback():
    output_path = _output_path("test_pythonpptx.pptx")
    result = _generate_pptx_pythonpptx(TEST_INTENT, TEST_SLIDE_CONTENTS, output_path)
    assert os.path.exists(result), f"python-pptx fallback did not create file: {result}"


def test_pptxgenjs_service():
    output_path = _output_path("test_pptxgenjs.pptx")
    result = call_pptxgenjs_service(TEST_INTENT, TEST_SLIDE_CONTENTS, output_path)
    if not result:
        pytest.skip("PptxGenJS service is unavailable in current environment.")
    assert os.path.exists(result), f"PptxGenJS returned path but file not found: {result}"


def test_generate_pptx_with_fallback():
    output_path = _output_path("test_complete.pptx")
    result = generate_pptx(TEST_INTENT, TEST_SLIDE_CONTENTS, output_path)
    assert os.path.exists(result), f"generate_pptx did not create file: {result}"


if __name__ == "__main__":
    # Keep a manual entrypoint for local debugging.
    test_pythonpptx_fallback()
    try:
        test_pptxgenjs_service()
    except pytest.skip.Exception:
        pass
    test_generate_pptx_with_fallback()
    print("All ppt_gen tests passed.")
