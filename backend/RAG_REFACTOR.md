# RAG模块重构说明

## 概述

`backend/core/rag.py` 已重构为支持多层级混合检索策略，集成RAGFlow向量检索、ChromaDB语义检索和TF-IDF关键词检索。

## 架构改进

### 1. 三层检索策略

```
优先级1: RAGFlow向量检索 (如果配置)
    ↓ (失败)
优先级2: ChromaDB + DashScope语义检索
    ↓ (失败)
优先级3: TF-IDF关键词检索 (始终可用)
```

### 2. Redis缓存机制

- 自动缓存检索结果
- 可配置TTL（默认1小时）
- 失败时优雅降级，不影响检索功能

### 3. 向后兼容

保持原有API签名不变：
- `add_document(file_id: str, chunks: list[str])`
- `search(query: str, top_k: int = 5) -> list[str]`
- `remove_document(file_id: str)`
- `get_file_ids() -> list[str]`

## 环境变量配置

### 必需配置（至少一项）

```bash
# DashScope (阿里云) - ChromaDB embeddings
DASHSCOPE_API_KEY=your_dashscope_key

# 或使用 RAGFlow
RAGFLOW_BASE_URL=https://your-ragflow-instance.com
RAGFLOW_API_KEY=your_ragflow_api_key
RAGFLOW_KB_ID=your_kb_id
```

### 可选配置

```bash
# Redis缓存
REDIS_URL=redis://localhost:6379/0
RAG_CACHE_TTL=3600  # 秒
```

## 使用示例

### 基本使用（无需修改现有代码）

```python
from core import rag

# 添加文档
chunks = ["文本片段1", "文本片段2", "文本片段3"]
rag.add_document("doc_001", chunks)

# 检索
results = rag.search("查询内容", top_k=5)
for result in results:
    print(result)

# 删除文档
rag.remove_document("doc_001")
```

### 检索行为

1. **有RAGFlow配置**：使用RAGFlow API进行向量检索
2. **有DashScope配置**：使用ChromaDB + DashScope embeddings
3. **无配置**：自动降级到TF-IDF关键词检索

### 缓存行为

- **有Redis配置**：自动缓存检索结果
- **无Redis配置**：直接执行检索，无缓存

## 日志输出

模块使用Python标准logging，输出示例：

```
[RAG] Redis cache enabled
[RAG] Cache hit for query: 人工智能的应用
[RAG] RAGFlow search succeeded: 5 results
[RAG] RAGFlow search failed (Connection timeout), fallback to ChromaDB
[RAG] ChromaDB search succeeded: 3 results
[RAG] TF-IDF search returned 2 results
```

## 错误处理

- 所有检索层级失败时，返回空列表 `[]`
- Redis连接失败时，自动禁用缓存
- RAGFlow/ChromaDB失败时，自动降级到下一层
- 不会抛出异常，保证服务可用性

## 性能优化

1. **懒加载**：Redis/ChromaDB客户端按需初始化
2. **连接池**：RAGFlow使用httpx连接池
3. **缓存**：减少重复检索的API调用
4. **降级策略**：快速失败，自动切换到备用方案

## 测试

运行测试脚本验证功能：

```bash
cd backend
python test_rag_refactor.py
```

测试覆盖：
- ✓ 向后兼容性
- ✓ TF-IDF降级模式
- ✓ 错误处理
- ✓ 配置检查
- ✓ RAGFlow配置检测

## 依赖项

已添加到 `requirements.txt`：
- `redis>=5.0.0` - Redis缓存
- `tenacity>=8.2.0` - 重试机制（RAGFlow客户端使用）

## 迁移指南

### 从旧版本迁移

无需修改代码！现有调用完全兼容：

```python
# 旧代码 - 无需修改
from core import rag
results = rag.search("查询", top_k=5)
```

### 启用RAGFlow

1. 设置环境变量：
```bash
export RAGFLOW_BASE_URL=https://your-instance.com
export RAGFLOW_API_KEY=your_key
export RAGFLOW_KB_ID=your_kb_id
```

2. 重启应用，自动使用RAGFlow

### 启用Redis缓存

1. 启动Redis服务
2. 设置环境变量：
```bash
export REDIS_URL=redis://localhost:6379/0
```

3. 重启应用，自动启用缓存

## 故障排查

### 问题：检索结果为空

**检查**：
1. 是否已添加文档？`rag.get_file_ids()`
2. 查看日志确认使用的检索层级
3. TF-IDF模式下，查询词是否在文档中出现

### 问题：RAGFlow不生效

**检查**：
1. 环境变量是否正确设置
2. RAGFlow服务是否可访问
3. 查看日志中的错误信息

### 问题：Redis缓存不生效

**检查**：
1. Redis服务是否运行
2. REDIS_URL是否正确
3. 查看日志中的连接错误

## 未来扩展

可能的改进方向：
- [ ] 支持更多向量数据库（Milvus, Pinecone等）
- [ ] 实现混合检索（向量+关键词融合排序）
- [ ] 添加检索结果重排序（Reranker）
- [ ] 支持多模态检索（图片+文本）
- [ ] 添加检索性能监控指标
