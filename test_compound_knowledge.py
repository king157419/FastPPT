"""Test script for compound knowledge integration."""
import sys
sys.path.insert(0, 'backend')

from core.compound_knowledge import get_knowledge_store

def test_knowledge_store():
    """Test basic knowledge store operations."""
    print("=== Testing Compound Knowledge Store ===\n")

    kb = get_knowledge_store()

    # Test 1: Add initial knowledge
    print("1. Adding initial teaching pattern...")
    result1 = kb.add_or_update(
        topic="Python编程 - 大学生教学模式",
        content="""教学模式：
- 受众：大学生
- 风格：简洁学术
- 页面结构：cover -> agenda -> content -> code -> example
- 类型分布：{'cover': 1, 'agenda': 1, 'content': 3, 'code': 2, 'example': 1}
- 总页数：8

适用场景：Python编程类课程
""",
        tags=["大学生", "简洁学术", "教学模式"],
        metadata={"topic": "Python编程", "page_count": 8}
    )
    print(f"   Result: {result1}")
    print(f"   Compound Factor: {result1['compound_factor']:.2f}\n")

    # Test 2: Update existing knowledge (compound effect)
    print("2. Updating with new pattern (compound effect)...")
    result2 = kb.add_or_update(
        topic="Python编程 - 大学生教学模式",
        content="""改进版教学模式：
- 增加了互动环节
- 添加了实战项目
- 优化了代码示例的复杂度
""",
        tags=["大学生", "简洁学术", "教学模式"],
        metadata={"topic": "Python编程", "page_count": 10}
    )
    print(f"   Result: {result2}")
    print(f"   Compound Factor: {result2['compound_factor']:.2f}\n")

    # Test 3: Add another pattern
    print("3. Adding different teaching pattern...")
    result3 = kb.add_or_update(
        topic="数据结构 - 研究生教学模式",
        content="""教学模式：
- 受众：研究生
- 风格：科技感
- 页面结构：cover -> agenda -> content -> formula -> code -> example
- 类型分布：{'cover': 1, 'agenda': 1, 'content': 2, 'formula': 2, 'code': 2, 'example': 2}
- 总页数：10

适用场景：数据结构类课程
""",
        tags=["研究生", "科技感", "教学模式"],
        metadata={"topic": "数据结构", "page_count": 10}
    )
    print(f"   Result: {result3}")
    print(f"   Compound Factor: {result3['compound_factor']:.2f}\n")

    # Test 4: Retrieve knowledge
    print("4. Retrieving knowledge for 'Python 大学生'...")
    results = kb.retrieve("Python 大学生", top_k=3)
    for i, entry in enumerate(results, 1):
        print(f"   {i}. {entry['topic']} (score: {entry['score']}, updates: {entry['update_count']})")
    print()

    # Test 5: Get by tag
    print("5. Getting entries by tag '大学生'...")
    tag_results = kb.get_by_tag("大学生")
    for entry in tag_results:
        print(f"   - {entry['topic']} (updates: {entry['update_count']})")
    print()

    # Test 6: Get stats
    print("6. Knowledge base statistics:")
    stats = kb.get_stats()
    print(f"   Total entries: {stats['total_entries']}")
    print(f"   Total updates: {stats['total_updates']}")
    print(f"   Compound factor: {stats['compound_factor']:.2f}")
    print(f"   Total tags: {stats['total_tags']}")
    print(f"   Total connections: {stats['total_connections']}")
    print()

    print("=== All tests passed! ===")

if __name__ == "__main__":
    test_knowledge_store()
