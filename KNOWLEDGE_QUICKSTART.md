"""
复利知识库快速参考

## 快速开始

### 1. 生成课件时自动学习
无需额外代码，生成课件时自动：
- 检索相关历史模式
- 学习新的教学模式
- 返回复利因子

### 2. 查询知识库
```python
from core.compound_knowledge import get_knowledge_store

kb = get_knowledge_store()

# 获取统计
stats = kb.get_stats()
print(f"复利因子: {stats['compound_factor']}")

# 搜索知识
results = kb.retrieve("Python 大学生", top_k=5)

# 按标签查询
entries = kb.get_by_tag("大学生")
```

### 3. 手动添加知识
```python
kb.add_or_update(
    topic="课程主题",
    content="教学模式描述",
    tags=["标签1", "标签2"],
    metadata={"key": "value"}
)
```

## API端点

### 统计信息
GET /api/knowledge/stats

### 搜索
POST /api/knowledge/search
Body: {"query": "搜索词", "top_k": 5}

### 标签列表
GET /api/knowledge/tags

### 按标签查询
GET /api/knowledge/tags/{tag}

### 所有条目
GET /api/knowledge/entries

## 数据位置

.fastppt/knowledge/
├── index.json          # 索引
└── entries/            # 条目（.md文件）

## 复利因子

compound_factor = total_updates / total_entries

- 1.0: 初始状态
- 2.0+: 知识开始积累
- 5.0+: 高度精炼

## 注意事项

1. 知识库自动创建，无需初始化
2. 所有操作线程安全（单例模式）
3. 知识以Markdown格式存储，可手动编辑
4. 更新次数越多的知识权重越高
5. 支持中文标签和内容

## 测试

运行测试脚本：
```bash
python test_compound_knowledge.py
```
"""
