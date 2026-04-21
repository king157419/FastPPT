"""Knowledge base API endpoints for compound learning system."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.compound_knowledge import get_knowledge_store

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


@router.get("/knowledge/stats")
def get_stats():
    """获取知识库统计信息"""
    try:
        kb = get_knowledge_store()
        stats = kb.get_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(500, f"获取统计信息失败: {e}") from e


@router.post("/knowledge/search")
def search_knowledge(req: SearchRequest):
    """搜索知识库"""
    try:
        kb = get_knowledge_store()
        results = kb.retrieve(req.query, top_k=req.top_k)
        return {
            "success": True,
            "query": req.query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(500, f"搜索失败: {e}") from e


@router.get("/knowledge/tags")
def get_all_tags():
    """获取所有标签"""
    try:
        kb = get_knowledge_store()
        tags = list(kb.index.get("tags", {}).keys())
        return {
            "success": True,
            "tags": tags,
            "count": len(tags)
        }
    except Exception as e:
        raise HTTPException(500, f"获取标签失败: {e}") from e


@router.get("/knowledge/tags/{tag}")
def get_by_tag(tag: str):
    """按标签查询知识"""
    try:
        kb = get_knowledge_store()
        results = kb.get_by_tag(tag)
        return {
            "success": True,
            "tag": tag,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(500, f"按标签查询失败: {e}") from e


@router.get("/knowledge/entries")
def list_entries():
    """列出所有知识条目"""
    try:
        kb = get_knowledge_store()
        entries = []
        for entry_id, meta in kb.index.get("entries", {}).items():
            entries.append({
                "entry_id": entry_id,
                "topic": meta.get("topic", ""),
                "created_at": meta.get("created_at", ""),
                "update_count": meta.get("update_count", 0),
                "tags": meta.get("tags", [])
            })
        # 按更新次数排序
        entries.sort(key=lambda x: x["update_count"], reverse=True)
        return {
            "success": True,
            "entries": entries,
            "count": len(entries)
        }
    except Exception as e:
        raise HTTPException(500, f"列出条目失败: {e}") from e
