"""RAG 知识库：RAGFlow向量检索 + ChromaDB + TF-IDF混合检索

检索策略：
1. 优先使用RAGFlow向量检索（如果配置）
2. 降级到ChromaDB + DashScope语义检索
3. 最终降级到TF-IDF关键词检索

缓存策略：使用Redis缓存检索结果（可选）
"""
import os
import uuid
import json
import hashlib
import logging
from typing import Optional, List
from functools import wraps
import numpy as np

logger = logging.getLogger(__name__)

# ==================== 配置 ====================
RAGFLOW_BASE_URL = os.environ.get("RAGFLOW_BASE_URL", "")
RAGFLOW_API_KEY = os.environ.get("RAGFLOW_API_KEY", "")
RAGFLOW_KB_ID = os.environ.get("RAGFLOW_KB_ID", "")
REDIS_URL = os.environ.get("REDIS_URL", "")
CACHE_TTL = int(os.environ.get("RAG_CACHE_TTL", "3600"))  # 默认1小时

# ==================== Redis缓存 ====================
_redis_client = None


def _get_redis():
    """获取Redis客户端（懒加载）- 已禁用"""
    return None  # Redis已禁用


def _cache_key(query: str, top_k: int) -> str:
    """生成缓存键"""
    key_str = f"rag:search:{query}:{top_k}"
    return hashlib.md5(key_str.encode()).hexdigest()


def cache_search(func):
    """缓存装饰器"""
    @wraps(func)
    def wrapper(query: str, top_k: int = 5) -> List[str]:
        redis_client = _get_redis()
        if redis_client:
            try:
                cache_key = _cache_key(query, top_k)
                cached = redis_client.get(cache_key)
                if cached:
                    logger.info(f"[RAG] Cache hit for query: {query[:50]}")
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"[RAG] Cache read failed: {e}")

        # 执行实际检索
        result = func(query, top_k)

        # 写入缓存
        if redis_client and result:
            try:
                cache_key = _cache_key(query, top_k)
                redis_client.setex(cache_key, CACHE_TTL, json.dumps(result))
            except Exception as e:
                logger.warning(f"[RAG] Cache write failed: {e}")

        return result
    return wrapper


# ==================== 内存存储（TF-IDF 降级用）====================
_tfidf_store: dict[str, list[str]] = {}  # {file_id: [chunks]}
_tfidf_vectorizer = None
_tfidf_matrix = None
_tfidf_all_chunks: list[tuple[str, str]] = []

# ==================== ChromaDB 客户端 ====================
_chroma_client = None
_chroma_collection = None
COLLECTION_NAME = "teachmind_kb"


def _use_vector() -> bool:
    return bool(os.environ.get("DASHSCOPE_API_KEY", ""))


def _use_ragflow() -> bool:
    """检查是否启用RAGFlow"""
    return bool(RAGFLOW_BASE_URL and RAGFLOW_API_KEY and RAGFLOW_KB_ID)


def _get_collection():
    global _chroma_client, _chroma_collection
    if _chroma_collection is not None:
        return _chroma_collection
    import chromadb
    persist_dir = os.path.join(os.path.dirname(__file__), "../../chroma_db")
    os.makedirs(persist_dir, exist_ok=True)
    _chroma_client = chromadb.PersistentClient(path=persist_dir)
    _chroma_collection = _chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    return _chroma_collection


# ==================== RAGFlow 向量检索 ====================

async def _ragflow_search(query: str, top_k: int = 5) -> List[str]:
    """使用RAGFlow进行向量检索"""
    try:
        from integrations.ragflow_client import RAGFlowClient, RAGFlowConfig

        config = RAGFlowConfig(
            base_url=RAGFLOW_BASE_URL,
            api_key=RAGFLOW_API_KEY,
        )

        async with RAGFlowClient(config) as client:
            result = await client.search(
                question=query,
                kb_ids=[RAGFLOW_KB_ID],
                top_k=top_k,
                similarity_threshold=0.7,
                rerank=True,
            )

            chunks = result.get("chunks", [])
            texts = [chunk.get("content", "") for chunk in chunks if chunk.get("content")]
            logger.info(f"[RAG] RAGFlow search returned {len(texts)} chunks")
            return texts
    except Exception as e:
        logger.error(f"[RAG] RAGFlow search failed: {e}")
        raise


# ==================== 向量模式 ====================

def _vector_add(file_id: str, chunks: list[str]):
    from core.llm import embed_texts
    collection = _get_collection()
    # 先删除该 file_id 旧数据
    try:
        existing = collection.get(where={"file_id": file_id})
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
    except Exception:
        pass
    if not chunks:
        return
    embeddings = embed_texts(chunks)
    ids = [f"{file_id}_{i}" for i in range(len(chunks))]
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=[{"file_id": file_id, "chunk_index": i} for i in range(len(chunks))],
    )


def _vector_search(query: str, top_k: int = 5) -> list[str]:
    from core.llm import embed_texts
    collection = _get_collection()
    if collection.count() == 0:
        return []
    q_emb = embed_texts([query])[0]
    results = collection.query(
        query_embeddings=[q_emb],
        n_results=min(top_k, collection.count()),
    )
    return results["documents"][0] if results["documents"] else []


def _vector_remove(file_id: str):
    collection = _get_collection()
    try:
        existing = collection.get(where={"file_id": file_id})
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
    except Exception:
        pass


# ==================== TF-IDF 降级模式 ====================

def _tfidf_rebuild():
    global _tfidf_vectorizer, _tfidf_matrix, _tfidf_all_chunks
    from sklearn.feature_extraction.text import TfidfVectorizer
    _tfidf_all_chunks = []
    for fid, chunks in _tfidf_store.items():
        for c in chunks:
            _tfidf_all_chunks.append((fid, c))
    if not _tfidf_all_chunks:
        _tfidf_vectorizer = None
        _tfidf_matrix = None
        return
    texts = [c for _, c in _tfidf_all_chunks]
    _tfidf_vectorizer = TfidfVectorizer(max_features=5000, token_pattern=r"(?u)\b\w+\b")
    _tfidf_matrix = _tfidf_vectorizer.fit_transform(texts)


def _tfidf_search(query: str, top_k: int = 5) -> list[str]:
    from sklearn.metrics.pairwise import cosine_similarity
    if _tfidf_vectorizer is None or _tfidf_matrix is None:
        return []
    q_vec = _tfidf_vectorizer.transform([query])
    scores = cosine_similarity(q_vec, _tfidf_matrix).flatten()
    indices = np.argsort(scores)[::-1][:top_k]
    return [_tfidf_all_chunks[i][1] for i in indices if scores[i] > 0]


# ==================== 公开接口 ====================

def add_document(file_id: str, chunks: list[str]):
    if _use_vector():
        try:
            _vector_add(file_id, chunks)
            return
        except Exception as e:
            print(f"[RAG] Vector add failed ({e}), fallback TF-IDF")
    _tfidf_store[file_id] = chunks
    _tfidf_rebuild()


def search(query: str, top_k: int = 5) -> list[str]:
    """混合检索策略：RAGFlow -> ChromaDB -> TF-IDF

    Args:
        query: 检索查询
        top_k: 返回结果数量

    Returns:
        检索到的文本片段列表
    """
    # 策略1: RAGFlow向量检索
    if _use_ragflow():
        try:
            import concurrent.futures
            import asyncio

            # Use thread pool to run async function in sync context
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _ragflow_search(query, top_k))
                results = future.result(timeout=30)
                if results:
                    logger.info(f"[RAG] RAGFlow search succeeded: {len(results)} results")
                    return results
        except Exception as e:
            logger.warning(f"[RAG] RAGFlow search failed ({e}), fallback to ChromaDB")

    # 策略2: ChromaDB向量检索
    if _use_vector():
        try:
            results = _vector_search(query, top_k)
            if results:
                logger.info(f"[RAG] ChromaDB search succeeded: {len(results)} results")
                return results
        except Exception as e:
            logger.warning(f"[RAG] ChromaDB search failed ({e}), fallback to TF-IDF")

    # 策略3: TF-IDF关键词检索
    results = _tfidf_search(query, top_k)
    logger.info(f"[RAG] TF-IDF search returned {len(results)} results")
    return results


# 应用缓存装饰器（保持向后兼容的函数签名）
_original_search = search
search = cache_search(_original_search)


def remove_document(file_id: str):
    if _use_vector():
        try:
            _vector_remove(file_id)
        except Exception as e:
            print(f"[RAG] Vector remove failed ({e})")
    if file_id in _tfidf_store:
        del _tfidf_store[file_id]
        _tfidf_rebuild()


def get_file_ids() -> list[str]:
    if _use_vector():
        try:
            col = _get_collection()
            results = col.get()
            ids = set(m["file_id"] for m in results["metadatas"]) if results["metadatas"] else set()
            return list(ids)
        except Exception:
            pass
    return list(_tfidf_store.keys())
