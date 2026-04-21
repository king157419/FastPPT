"""Test script for ppt_gen.py refactoring"""
import os
import sys
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.ppt_gen import generate_pptx, call_pptxgenjs_service, _generate_pptx_pythonpptx

# Test data
test_intent = {
    "topic": "Python基础编程",
    "audience": "初学者",
    "key_points": ["变量与数据类型", "控制流程", "函数定义"],
    "duration": "45分钟",
    "subject": "计算机科学",
    "teacher": "张老师"
}

test_slide_contents = [
    {
        "key_point": "变量与数据类型",
        "bullets": ["整数类型 (int)", "浮点数类型 (float)", "字符串类型 (str)", "布尔类型 (bool)"],
        "tip": "变量命名要有意义，遵循PEP8规范"
    },
    {
        "key_point": "控制流程",
        "bullets": ["if-elif-else 条件判断", "for 循环遍历", "while 循环", "break 和 continue"],
        "tip": "注意缩进，Python使用缩进表示代码块"
    },
    {
        "key_point": "函数定义",
        "bullets": ["def 关键字定义函数", "参数传递", "返回值", "文档字符串"],
        "tip": "函数应该只做一件事，保持简洁"
    }
]

def test_pythonpptx_fallback():
    """测试 python-pptx fallback 功能"""
    print("\n=== 测试 python-pptx fallback ===")
    output_path = "D:\\desk\\外包\\FastPPT\\backend\\outputs\\test_pythonpptx.pptx"

    try:
        result = _generate_pptx_pythonpptx(test_intent, test_slide_contents, output_path)
        if os.path.exists(result):
            file_size = os.path.getsize(result)
            print(f"✓ python-pptx 生成成功: {result}")
            print(f"  文件大小: {file_size / 1024:.2f} KB")
            return True
        else:
            print(f"✗ 文件未生成: {result}")
            return False
    except Exception as e:
        print(f"✗ python-pptx 生成失败: {e}")
        return False


def test_pptxgenjs_service():
    """测试 PptxGenJS 服务调用"""
    print("\n=== 测试 PptxGenJS 服务 ===")
    output_path = "D:\\desk\\外包\\FastPPT\\backend\\outputs\\test_pptxgenjs.pptx"

    try:
        result = call_pptxgenjs_service(test_intent, test_slide_contents, output_path)
        if result:
            file_size = os.path.getsize(result)
            print(f"✓ PptxGenJS 服务生成成功: {result}")
            print(f"  文件大小: {file_size / 1024:.2f} KB")
            return True
        else:
            print("✗ PptxGenJS 服务不可用（这是预期的，如果服务未启动）")
            return False
    except Exception as e:
        print(f"✗ PptxGenJS 服务调用失败: {e}")
        return False


def test_generate_pptx_with_fallback():
    """测试完整的 generate_pptx 函数（带 fallback）"""
    print("\n=== 测试 generate_pptx (带 fallback) ===")
    output_path = "D:\\desk\\外包\\FastPPT\\backend\\outputs\\test_complete.pptx"

    try:
        result = generate_pptx(test_intent, test_slide_contents, output_path)
        if os.path.exists(result):
            file_size = os.path.getsize(result)
            print(f"✓ 生成成功: {result}")
            print(f"  文件大小: {file_size / 1024:.2f} KB")
            return True
        else:
            print(f"✗ 文件未生成: {result}")
            return False
    except Exception as e:
        print(f"✗ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("PPT 生成功能测试")
    print("=" * 60)

    # 确保输出目录存在
    os.makedirs("D:\\desk\\外包\\FastPPT\\backend\\outputs", exist_ok=True)

    results = []

    # 测试 1: python-pptx fallback
    results.append(("python-pptx fallback", test_pythonpptx_fallback()))

    # 测试 2: PptxGenJS 服务（可能失败，如果服务未启动）
    results.append(("PptxGenJS 服务", test_pptxgenjs_service()))

    # 测试 3: 完整流程（带 fallback）
    results.append(("完整流程", test_generate_pptx_with_fallback()))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name}: {status}")

    passed_count = sum(1 for _, passed in results if passed)
    print(f"\n总计: {passed_count}/{len(results)} 测试通过")

    # 至少 python-pptx fallback 应该通过
    if results[0][1]:
        print("\n✓ 核心功能正常，向后兼容性保持")
        sys.exit(0)
    else:
        print("\n✗ 核心功能异常")
        sys.exit(1)
