"""TF-IDF 关键词检索，无需 Embedding API"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# 全局知识库：{file_id: [chunks]}
_store: dict[str, list[str]] = {}
_vectorizer: TfidfVectorizer | None = None
_matrix = None
_all_chunks: list[tuple[str, str]] = []  # [(file_id, chunk)]


def add_document(file_id: str, chunks: list[str]):
    global _vectorizer, _matrix, _all_chunks
    _store[file_id] = chunks
    _rebuild_index()


def _rebuild_index():
    global _vectorizer, _matrix, _all_chunks
    _all_chunks = []
    for fid, chunks in _store.items():
        for c in chunks:
            _all_chunks.append((fid, c))
    if not _all_chunks:
        return
    texts = [c for _, c in _all_chunks]
    _vectorizer = TfidfVectorizer(max_features=5000, token_pattern=r"(?u)\b\w+\b")
    _matrix = _vectorizer.fit_transform(texts)


def search(query: str, top_k: int = 5) -> list[str]:
    if _vectorizer is None or _matrix is None or not _all_chunks:
        return []
    q_vec = _vectorizer.transform([query])
    scores = cosine_similarity(q_vec, _matrix).flatten()
    indices = np.argsort(scores)[::-1][:top_k]
    return [_all_chunks[i][1] for i in indices if scores[i] > 0]


def get_file_ids() -> list[str]:
    return list(_store.keys())


def remove_document(file_id: str):
    global _vectorizer, _matrix, _all_chunks
    if file_id in _store:
        del _store[file_id]
        _rebuild_index()
