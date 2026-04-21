"""RAGFlow API client for document upload, search, and citation tracking.

This module provides a production-ready client for RAGFlow API with:
- Connection pooling
- Automatic retry with exponential backoff
- Error handling and logging
- Type hints for better IDE support
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional
from dataclasses import dataclass
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


@dataclass
class RAGFlowConfig:
    """RAGFlow API configuration."""
    base_url: str
    api_key: str
    timeout: int = 30
    max_retries: int = 3
    pool_limits: httpx.Limits = None

    def __post_init__(self):
        if self.pool_limits is None:
            self.pool_limits = httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20
            )


class RAGFlowClient:
    """Production-ready RAGFlow API client with connection pooling and retry."""

    def __init__(self, config: RAGFlowConfig):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            timeout=self.config.timeout,
            limits=self.config.pool_limits,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def upload_document(
        self,
        file_path: str,
        kb_id: str,
        parser: str = "layout_aware",
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Upload a document to RAGFlow knowledge base.

        Args:
            file_path: Path to the document file
            kb_id: Knowledge base ID
            parser: Parser type (layout_aware, naive, qa, table)
            metadata: Optional metadata for the document

        Returns:
            Upload response with document ID and status

        Raises:
            httpx.HTTPError: If upload fails after retries
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        with open(file_path, "rb") as f:
            files = {"file": f}
            data = {
                "kb_id": kb_id,
                "parser": parser,
            }
            if metadata:
                data["metadata"] = metadata

            response = await self._client.post("/v1/documents", files=files, data=data)
            response.raise_for_status()
            result = response.json()

            logger.info(f"Document uploaded: {result.get('doc_id')}")
            return result

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def search(
        self,
        question: str,
        kb_ids: list[str],
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        rerank: bool = True,
    ) -> dict[str, Any]:
        """Search knowledge base with hybrid retrieval.

        Args:
            question: Search query
            kb_ids: List of knowledge base IDs to search
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score (0-1)
            rerank: Whether to use reranker

        Returns:
            Search results with chunks and citations

        Raises:
            httpx.HTTPError: If search fails after retries
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        payload = {
            "question": question,
            "kb_ids": kb_ids,
            "top_k": top_k,
            "similarity_threshold": similarity_threshold,
            "rerank": rerank,
        }

        response = await self._client.post("/v1/retrieval", json=payload)
        response.raise_for_status()
        result = response.json()

        logger.info(f"Search completed: {len(result.get('chunks', []))} chunks found")
        return result

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def get_citations(
        self,
        doc_id: str,
        chunk_ids: list[str],
    ) -> dict[str, Any]:
        """Get citation information for specific chunks.

        Args:
            doc_id: Document ID
            chunk_ids: List of chunk IDs

        Returns:
            Citation information with source locations

        Raises:
            httpx.HTTPError: If request fails after retries
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        payload = {
            "doc_id": doc_id,
            "chunk_ids": chunk_ids,
        }

        response = await self._client.post("/v1/citations", json=payload)
        response.raise_for_status()
        result = response.json()

        logger.info(f"Citations retrieved for {len(chunk_ids)} chunks")
        return result

    async def list_documents(self, kb_id: str) -> list[dict[str, Any]]:
        """List all documents in a knowledge base.

        Args:
            kb_id: Knowledge base ID

        Returns:
            List of documents with metadata

        Raises:
            httpx.HTTPError: If request fails
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        response = await self._client.get(f"/v1/knowledge_bases/{kb_id}/documents")
        response.raise_for_status()
        result = response.json()

        return result.get("documents", [])

    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document from knowledge base.

        Args:
            doc_id: Document ID to delete

        Returns:
            True if deletion successful

        Raises:
            httpx.HTTPError: If deletion fails
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        response = await self._client.delete(f"/v1/documents/{doc_id}")
        response.raise_for_status()

        logger.info(f"Document deleted: {doc_id}")
        return True


# Singleton instance for reuse
_client_instance: Optional[RAGFlowClient] = None


def get_ragflow_client(config: Optional[RAGFlowConfig] = None) -> RAGFlowClient:
    """Get or create RAGFlow client singleton.

    Args:
        config: Optional configuration (required on first call)

    Returns:
        RAGFlow client instance

    Raises:
        ValueError: If config not provided on first call
    """
    global _client_instance

    if _client_instance is None:
        if config is None:
            raise ValueError("Config required for first client initialization")
        _client_instance = RAGFlowClient(config)

    return _client_instance
