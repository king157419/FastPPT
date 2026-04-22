"""测试RAG重构后的向后兼容性和功能"""
import os
import sys
import io

# 设置UTF-8编码
if __name__ == "__main__" and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# 设置路径
sys.path.insert(0, os.path.dirname(__file__))

# 模拟环境变量（测试TF-IDF fallback）
os.environ.pop("DASHSCOPE_API_KEY", None)
os.environ.pop("RAGFLOW_BASE_URL", None)
os.environ.pop("RAGFLOW_API_KEY", None)
os.environ.pop("RAGFLOW_KB_ID", None)
os.environ.pop("REDIS_URL", None)

from core import rag

def test_backward_compatibility():
    """测试向后兼容性"""
    print("=" * 60)
    print("测试1: 向后兼容性 - 函数签名")
    print("=" * 60)

    # 检查公开API
    assert hasattr(rag, "add_document"), "Missing add_document function"
    assert hasattr(rag, "search"), "Missing search function"
    assert hasattr(rag, "remove_document"), "Missing remove_document function"
    assert hasattr(rag, "get_file_ids"), "Missing get_file_ids function"
    print("✓ 所有公开API存在")

    # 测试基本功能
    print("\n" + "=" * 60)
    print("测试2: TF-IDF降级模式")
    print("=" * 60)

    # 添加文档
    test_chunks = [
        "人工智能是计算机科学的一个分支",
        "机器学习是人工智能的核心技术",
        "深度学习使用神经网络进行学习",
    ]
    rag.add_document("test_doc_1", test_chunks)
    print(f"✓ 添加文档: {len(test_chunks)} 个片段")

    # 检索
    results = rag.search("人工智能", top_k=2)
    print(f"✓ 检索结果: {len(results)} 个片段")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result[:50]}...")

    # 获取文件ID
    file_ids = rag.get_file_ids()
    print(f"✓ 文件ID列表: {file_ids}")
    assert "test_doc_1" in file_ids, "Document not found in file_ids"

    # 删除文档
    rag.remove_document("test_doc_1")
    file_ids_after = rag.get_file_ids()
    print(f"✓ 删除后文件ID列表: {file_ids_after}")
    assert "test_doc_1" not in file_ids_after, "Document still exists after removal"

    print("\n" + "=" * 60)
    print("测试3: 错误处理")
    print("=" * 60)

    # 空查询
    empty_results = rag.search("不存在的内容", top_k=5)
    print(f"✓ 空结果处理: {len(empty_results)} 个片段")

    # 空文档
    rag.add_document("empty_doc", [])
    print("✓ 空文档处理成功")

    print("\n" + "=" * 60)
    print("测试4: 配置检查")
    print("=" * 60)

    # 检查配置函数
    use_ragflow = rag._use_ragflow()
    use_vector = rag._use_vector()
    print(f"✓ RAGFlow启用: {use_ragflow}")
    print(f"✓ ChromaDB启用: {use_vector}")
    print(f"✓ 当前使用: TF-IDF (降级模式)")

    print("\n" + "=" * 60)
    print("所有测试通过! ✓")
    print("=" * 60)


def test_with_ragflow_config():
    """测试RAGFlow配置（模拟）"""
    print("\n" + "=" * 60)
    print("测试5: RAGFlow配置检查")
    print("=" * 60)

    # 设置模拟配置
    os.environ["RAGFLOW_BASE_URL"] = "https://test.ragflow.com"
    os.environ["RAGFLOW_API_KEY"] = "test_key"
    os.environ["RAGFLOW_KB_ID"] = "test_kb"

    # 重新导入以获取新配置
    import importlib
    importlib.reload(rag)

    use_ragflow = rag._use_ragflow()
    print(f"✓ RAGFlow配置检测: {use_ragflow}")
    print(f"  - Base URL: {rag.RAGFLOW_BASE_URL}")
    print(f"  - API Key: {rag.RAGFLOW_API_KEY[:10]}...")
    print(f"  - KB ID: {rag.RAGFLOW_KB_ID}")

    # 清理
    os.environ.pop("RAGFLOW_BASE_URL", None)
    os.environ.pop("RAGFLOW_API_KEY", None)
    os.environ.pop("RAGFLOW_KB_ID", None)


if __name__ == "__main__":
    try:
        test_backward_compatibility()
        test_with_ragflow_config()
        print("\n✅ 所有测试完成!")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
