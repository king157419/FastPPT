"""RAG 知识库：ChromaDB + DashScope text-embedding-v3 语义检索

降级策略：若 DashScope Key 不存在，自动降级到 TF-IDF 关键词检索。
"""
import os
import uuid
import numpy as np

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
    if _use_vector():
        try:
            return _vector_search(query, top_k)
        except Exception as e:
            print(f"[RAG] Vector search failed ({e}), fallback TF-IDF")
    return _tfidf_search(query, top_k)


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
