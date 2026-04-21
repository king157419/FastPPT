"""Document management and retrieval API for RAGFlow integration.

This module provides endpoints for:
- Uploading documents to RAGFlow knowledge base
- Searching knowledge with hybrid retrieval
- Listing documents in knowledge base
- Deleting documents from knowledge base
"""
from __future__ import annotations

import os
import tempfile
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from integrations.ragflow_client import RAGFlowClient, RAGFlowConfig, get_ragflow_client

router = APIRouter()

# RAGFlow configuration from environment
RAGFLOW_BASE_URL = os.getenv("RAGFLOW_BASE_URL", "http://localhost:9380")
RAGFLOW_API_KEY = os.getenv("RAGFLOW_API_KEY", "")
RAGFLOW_KB_ID = os.getenv("RAGFLOW_KB_ID", "")


def _get_client() -> RAGFlowClient:
    """Get configured RAGFlow client instance.

    Returns:
        RAGFlow client instance

    Raises:
        HTTPException: If configuration is missing
    """
    if not RAGFLOW_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="RAGFlow API key not configured. Set RAGFLOW_API_KEY environment variable."
        )

    config = RAGFlowConfig(
        base_url=RAGFLOW_BASE_URL,
        api_key=RAGFLOW_API_KEY,
    )
    return get_ragflow_client(config)


class SearchRequest(BaseModel):
    """Request model for knowledge search."""
    query: str = Field(..., description="Search query text")
    kb_ids: list[str] = Field(default_factory=list, description="Knowledge base IDs to search")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to return")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    rerank: bool = Field(default=True, description="Whether to use reranker")


class SearchResponse(BaseModel):
    """Response model for knowledge search."""
    chunks: list[dict]
    total: int
    query: str


class DocumentListResponse(BaseModel):
    """Response model for document listing."""
    documents: list[dict]
    total: int
    kb_id: str


class UploadResponse(BaseModel):
    """Response model for document upload."""
    doc_id: str
    status: str
    message: str


class DeleteResponse(BaseModel):
    """Response model for document deletion."""
    success: bool
    doc_id: str
    message: str


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload"),
    kb_id: Optional[str] = Form(None, description="Knowledge base ID (optional, uses default if not provided)"),
    parser: str = Form("layout_aware", description="Parser type: layout_aware, naive, qa, table"),
) -> UploadResponse:
    """Upload a document to RAGFlow knowledge base.

    Supports multiple file formats: PDF, DOCX, TXT, MD, etc.
    The document will be parsed and indexed for retrieval.

    Args:
        file: Document file to upload (multipart/form-data)
        kb_id: Knowledge base ID (optional, uses default from env)
        parser: Parser type for document processing

    Returns:
        Upload response with document ID and status

    Raises:
        HTTPException: If upload fails or configuration is invalid
    """
    effective_kb_id = kb_id or RAGFLOW_KB_ID
    if not effective_kb_id:
        raise HTTPException(
            status_code=400,
            detail="Knowledge base ID required. Provide kb_id or set RAGFLOW_KB_ID environment variable."
        )

    # Save uploaded file temporarily
    suffix = os.path.splitext(file.filename or "")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_path = temp_file.name

    try:
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Upload to RAGFlow
        client = _get_client()
        async with client:
            result = await client.upload_document(
                file_path=temp_path,
                kb_id=effective_kb_id,
                parser=parser,
            )

        return UploadResponse(
            doc_id=result.get("doc_id", ""),
            status=result.get("status", "uploaded"),
            message=f"文档 {file.filename} 上传成功"
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"文档上传失败: {exc}"
        ) from exc
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/search", response_model=SearchResponse)
async def search_knowledge(req: SearchRequest) -> SearchResponse:
    """Search knowledge base with hybrid retrieval.

    Uses RAGFlow's hybrid search combining:
    - Dense vector search (semantic similarity)
    - Sparse keyword search (BM25)
    - Optional reranking for improved relevance

    Args:
        req: Search request with query and parameters

    Returns:
        Search results with chunks and metadata

    Raises:
        HTTPException: If search fails
    """
    effective_kb_ids = req.kb_ids or [RAGFLOW_KB_ID]
    if not effective_kb_ids or not effective_kb_ids[0]:
        raise HTTPException(
            status_code=400,
            detail="Knowledge base ID required. Provide kb_ids or set RAGFLOW_KB_ID environment variable."
        )

    try:
        client = _get_client()
        async with client:
            result = await client.search(
                question=req.query,
                kb_ids=effective_kb_ids,
                top_k=req.top_k,
                similarity_threshold=req.similarity_threshold,
                rerank=req.rerank,
            )

        chunks = result.get("chunks", [])
        return SearchResponse(
            chunks=chunks,
            total=len(chunks),
            query=req.query
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"知识检索失败: {exc}"
        ) from exc


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    kb_id: Optional[str] = None
) -> DocumentListResponse:
    """List all documents in a knowledge base.

    Returns empty list if RAGFlow not configured (graceful degradation).

    Args:
        kb_id: Knowledge base ID (optional, uses default from env)

    Returns:
        List of documents with metadata
    """
    # Return empty list if RAGFlow not configured
    if not RAGFLOW_API_KEY:
        return DocumentListResponse(documents=[], total=0, kb_id="default")

    effective_kb_id = kb_id or RAGFLOW_KB_ID
    if not effective_kb_id:
        return DocumentListResponse(documents=[], total=0, kb_id="default")

    try:
        client = _get_client()
        async with client:
            documents = await client.list_documents(kb_id=effective_kb_id)

        return DocumentListResponse(
            documents=documents,
            total=len(documents),
            kb_id=effective_kb_id
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"文档列表获取失败: {exc}"
        ) from exc


@router.delete("/documents/{doc_id}", response_model=DeleteResponse)
async def delete_document(doc_id: str) -> DeleteResponse:
    """Delete a document from knowledge base.

    Permanently removes the document and all its chunks from the index.
    This operation cannot be undone.

    Args:
        doc_id: Document ID to delete

    Returns:
        Deletion confirmation

    Raises:
        HTTPException: If deletion fails
    """
    if not doc_id:
        raise HTTPException(
            status_code=400,
            detail="Document ID required"
        )

    try:
        client = _get_client()
        async with client:
            success = await client.delete_document(doc_id=doc_id)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="文档删除失败"
            )

        return DeleteResponse(
            success=True,
            doc_id=doc_id,
            message=f"文档 {doc_id} 删除成功"
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"文档删除失败: {exc}"
        ) from exc
