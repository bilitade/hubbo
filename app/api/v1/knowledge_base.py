"""Knowledge Base API endpoints."""
import asyncio
from typing import Optional, List
from uuid import UUID
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.knowledge_base import KnowledgeBaseDocument
from app.schemas.knowledge_base import (
    KBDocumentResponse,
    KBDocumentListResponse,
    KBUploadResponse,
    KBSearchRequest,
    KBSearchResponse,
    KBStatsResponse,
    KBDocumentUpdate,
)
from app.ai.kb_service import KBService
from app.ai.storage import FileStorage
from app.config import settings

router = APIRouter(prefix="/knowledge-base", tags=["knowledge-base"])


def get_kb_service(db: Session = Depends(get_db)) -> KBService:
    """Dependency to get KB service."""
    return KBService(db)


@router.post("/upload", response_model=KBUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category: str = Query(default="general", description="Document category"),
    description: Optional[str] = Query(None, description="Document description"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    kb_service: KBService = Depends(get_kb_service),
):
    """
    Upload a document to the knowledge base.
    
    The document will be processed asynchronously to extract text,
    chunk it, and generate embeddings.
    
    Supported formats: PDF, DOCX, TXT, MD, and other text files.
    """
    try:
        # Validate file type
        allowed_types = [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
            "text/plain",
            "text/markdown",
            "text/csv",
            "application/json",
        ]
        
        # Check content type or extension
        file_ext = Path(file.filename).suffix.lower()
        allowed_extensions = [".pdf", ".docx", ".doc", ".txt", ".md", ".csv", ".json"]
        
        if file.content_type not in allowed_types and file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Save file
        storage = FileStorage()
        file_info = await storage.save_file(
            file=file,
            user_id=current_user.id,
            category="kb"
        )
        
        # Create document record
        document = KnowledgeBaseDocument(
            user_id=current_user.id,
            filename=file_info["stored_name"],
            original_filename=file_info["filename"],
            file_path=file_info["filepath"],
            file_size=file_info["size"],
            content_type=file_info["content_type"],
            category=category,
            description=description,
            tags=tags,
            status="pending",
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Process document in background
        background_tasks.add_task(
            kb_service.process_document,
            document.id,
            file_info["filepath"]
        )
        
        return KBUploadResponse(
            document_id=document.id,
            filename=document.original_filename,
            file_size=document.file_size,
            status=document.status,
            message="Document uploaded successfully. Processing in background."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")


@router.get("/documents", response_model=KBDocumentListResponse)
async def list_documents(
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    kb_service: KBService = Depends(get_kb_service),
):
    """
    List all knowledge base documents for the current user.
    
    Supports filtering by category and status, with pagination.
    """
    skip = (page - 1) * page_size
    
    documents, total = kb_service.list_documents(
        user_id=current_user.id,
        category=category,
        status=status,
        skip=skip,
        limit=page_size
    )
    
    return KBDocumentListResponse(
        documents=documents,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/documents/{document_id}", response_model=KBDocumentResponse)
async def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    kb_service: KBService = Depends(get_kb_service),
):
    """Get a specific document by ID."""
    document = kb_service.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check ownership
    if document.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return document


@router.patch("/documents/{document_id}", response_model=KBDocumentResponse)
async def update_document(
    document_id: UUID,
    update_data: KBDocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    kb_service: KBService = Depends(get_kb_service),
):
    """Update document metadata."""
    document = kb_service.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check ownership
    if document.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(document, field, value)
    
    db.commit()
    db.refresh(document)
    
    return document


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    kb_service: KBService = Depends(get_kb_service),
):
    """Delete a document and all its chunks."""
    document = kb_service.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check ownership
    if document.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = kb_service.delete_document(document_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Error deleting document")
    
    return {"message": "Document deleted successfully"}


@router.post("/search", response_model=KBSearchResponse)
async def search_knowledge_base(
    search_request: KBSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    kb_service: KBService = Depends(get_kb_service),
):
    """
    Semantic search in the knowledge base.
    
    Uses vector embeddings to find the most relevant document chunks
    for the given query.
    """
    return await kb_service.search(
        query=search_request.query,
        k=search_request.k,
        category=search_request.category,
        user_id=current_user.id
    )


@router.get("/stats", response_model=KBStatsResponse)
async def get_kb_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    kb_service: KBService = Depends(get_kb_service),
):
    """Get knowledge base statistics for the current user."""
    return kb_service.get_stats(user_id=current_user.id)


@router.post("/reprocess/{document_id}")
async def reprocess_document(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    kb_service: KBService = Depends(get_kb_service),
):
    """
    Reprocess a document (re-extract text, re-chunk, and re-embed).
    
    Useful if processing failed or if you want to update embeddings.
    """
    document = kb_service.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check ownership
    if document.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete existing chunks
    from app.models.knowledge_base import KnowledgeBaseChunk
    from sqlalchemy import delete
    
    db.execute(delete(KnowledgeBaseChunk).where(
        KnowledgeBaseChunk.document_id == document_id
    ))
    db.commit()
    
    # Reset document status
    document.status = "pending"
    document.total_chunks = 0
    db.commit()
    
    # Reprocess in background
    background_tasks.add_task(
        kb_service.process_document,
        document_id,
        document.file_path
    )
    
    return {"message": "Document queued for reprocessing"}


