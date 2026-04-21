"""Compound Knowledge Store - Karpathy式复利RAG系统

核心概念：知识像复利一样累积，每次交互都让系统变得更好
- 每次生成课件后，提取教学模式并存储
- 知识不断精炼和合并
- 跨课程学习和迁移
"""
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Optional
import hashlib

class CompoundKnowledgeStore:
    """持久化知识库，支持知识复利增长"""

    def __init__(self, base_path: str = ".fastppt/knowledge"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.index_file = self.base_path / "index.json"
        self.entries_dir = self.base_path / "entries"
        self.entries_dir.mkdir(exist_ok=True)
        self._load_index()

    def _load_index(self):
        """加载或初始化知识索引"""
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                self.index = json.load(f)
        else:
            self.index = {
                "entries": {},
                "tags": {},
                "connections": {},
                "stats": {
                    "total_entries": 0,
                    "total_updates": 0,
                    "created_at": datetime.now().isoformat()
                }
            }

    def add_or_update(self, topic: str, content: str,
                      tags: List[str] = None,
                      related: List[str] = None,
                      metadata: Dict = None) -> Dict:
        """添加新知识或更新现有条目（复利效应的核心）"""
        entry_id = self._normalize_id(topic)
        entry_path = self.entries_dir / f"{entry_id}.md"

        # 检查是否已存在
        is_update = entry_id in self.index["entries"]

        if is_update:
            # 复利：与现有知识合并
            existing = self._read_entry(entry_id)
            content = self._merge_knowledge(existing, content)
            self.index["entries"][entry_id]["update_count"] += 1
            self.index["entries"][entry_id]["last_updated"] = datetime.now().isoformat()
        else:
            # 新条目
            self.index["entries"][entry_id] = {
                "topic": topic,
                "created_at": datetime.now().isoformat(),
                "update_count": 0,
                "tags": tags or [],
                "related": related or [],
                "metadata": metadata or {}
            }
            self.index["stats"]["total_entries"] += 1

        # 写入内容
        with open(entry_path, 'w', encoding='utf-8') as f:
            f.write(f"# {topic}\n\n")
            f.write(f"**创建时间**: {self.index['entries'][entry_id]['created_at']}\n")
            f.write(f"**更新次数**: {self.index['entries'][entry_id]['update_count']}\n")
            if metadata:
                f.write(f"**元数据**: {json.dumps(metadata, ensure_ascii=False)}\n")
            f.write("\n---\n\n")
            f.write(content)

        # 更新标签和连接
        self._update_tags(entry_id, tags or [])
        self._update_connections(entry_id, related or [])

        self.index["stats"]["total_updates"] += 1
        self._save_index()

        return {
            "entry_id": entry_id,
            "is_update": is_update,
            "path": str(entry_path),
            "compound_factor": self.get_compound_factor()
        }

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """检索相关知识条目"""
        results = []
        query_lower = query.lower()

        for entry_id, meta in self.index["entries"].items():
            score = 0

            # 主题匹配
            if query_lower in meta["topic"].lower():
                score += 10

            # 标签匹配
            for tag in meta.get("tags", []):
                if query_lower in tag.lower():
                    score += 5

            # 内容匹配
            content = self._read_entry(entry_id)
            if query_lower in content.lower():
                score += 1

            # 更新次数加权（精炼过的知识更有价值）
            score += meta["update_count"] * 0.5

            if score > 0:
                results.append({
                    "entry_id": entry_id,
                    "topic": meta["topic"],
                    "score": score,
                    "content": content,
                    "update_count": meta["update_count"],
                    "tags": meta.get("tags", []),
                    "metadata": meta.get("metadata", {})
                })

        # 按分数和更新次数排序（更精炼的条目排名更高）
        results.sort(key=lambda x: (x["score"], x["update_count"]), reverse=True)
        return results[:top_k]

    def _merge_knowledge(self, existing: str, new: str) -> str:
        """合并新知识与现有知识（复利效应）"""
        # 移除旧的元数据头
        lines = existing.split('\n')
        content_start = 0
        for i, line in enumerate(lines):
            if line.strip() == '---' and i > 0:
                content_start = i + 1
                break

        old_content = '\n'.join(lines[content_start:]).strip()

        return f"{old_content}\n\n---\n\n## 更新 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n{new}"

    def _normalize_id(self, topic: str) -> str:
        """将主题转换为有效的条目ID"""
        # 使用hash确保唯一性
        return hashlib.md5(topic.encode()).hexdigest()[:16]

    def _read_entry(self, entry_id: str) -> str:
        """读取条目内容"""
        entry_path = self.entries_dir / f"{entry_id}.md"
        if entry_path.exists():
            with open(entry_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def _update_tags(self, entry_id: str, tags: List[str]):
        """更新标签索引"""
        for tag in tags:
            if tag not in self.index["tags"]:
                self.index["tags"][tag] = []
            if entry_id not in self.index["tags"][tag]:
                self.index["tags"][tag].append(entry_id)

    def _update_connections(self, entry_id: str, related: List[str]):
        """更新连接图"""
        if entry_id not in self.index["connections"]:
            self.index["connections"][entry_id] = []
        for rel in related:
            rel_id = self._normalize_id(rel)
            if rel_id not in self.index["connections"][entry_id]:
                self.index["connections"][entry_id].append(rel_id)

    def _save_index(self):
        """持久化索引到磁盘"""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)

    def get_stats(self) -> Dict:
        """获取知识库统计信息"""
        return {
            **self.index["stats"],
            "compound_factor": self.get_compound_factor(),
            "total_tags": len(self.index["tags"]),
            "total_connections": sum(len(v) for v in self.index["connections"].values())
        }

    def get_compound_factor(self) -> float:
        """计算复利因子（平均每个条目的更新次数）"""
        total_entries = self.index["stats"]["total_entries"]
        if total_entries == 0:
            return 0.0
        return self.index["stats"]["total_updates"] / total_entries

    def get_by_tag(self, tag: str) -> List[Dict]:
        """按标签检索"""
        entry_ids = self.index["tags"].get(tag, [])
        results = []
        for entry_id in entry_ids:
            if entry_id in self.index["entries"]:
                meta = self.index["entries"][entry_id]
                results.append({
                    "entry_id": entry_id,
                    "topic": meta["topic"],
                    "content": self._read_entry(entry_id),
                    "update_count": meta["update_count"]
                })
        return results

    def get_connected(self, topic: str) -> List[Dict]:
        """获取相关联的知识"""
        entry_id = self._normalize_id(topic)
        connected_ids = self.index["connections"].get(entry_id, [])
        results = []
        for conn_id in connected_ids:
            if conn_id in self.index["entries"]:
                meta = self.index["entries"][conn_id]
                results.append({
                    "entry_id": conn_id,
                    "topic": meta["topic"],
                    "content": self._read_entry(conn_id),
                    "update_count": meta["update_count"]
                })
        return results


# 全局单例
_knowledge_store = None

def get_knowledge_store() -> CompoundKnowledgeStore:
    """获取知识库单例"""
    global _knowledge_store
    if _knowledge_store is None:
        _knowledge_store = CompoundKnowledgeStore()
    return _knowledge_store
