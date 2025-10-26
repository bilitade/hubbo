"""Schemas for Knowledge Base API requests and responses."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, UUID4


# ===== Document Schemas =====

class KBDocumentBase(BaseModel):
    """Base schema for KB documents."""
    category: str = Field(default="general", description="Document category")
    description: Optional[str] = Field(None, description="Document description")
    tags: Optional[str] = Field(None, description="Comma-separated tags")


class KBDocumentCreate(KBDocumentBase):
    """Schema for creating a KB document."""
    pass


class KBDocumentUpdate(BaseModel):
    """Schema for updating a KB document."""
    category: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None


class KBDocumentInDB(KBDocumentBase):
    """Schema for KB document in database."""
    id: UUID4
    user_id: UUID4
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    content_type: str
    status: str
    total_chunks: int
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class KBDocumentResponse(KBDocumentInDB):
    """Schema for KB document API response."""
    pass


class KBDocumentListResponse(BaseModel):
    """Schema for list of KB documents."""
    documents: List[KBDocumentResponse]
    total: int
    page: int
    page_size: int


# ===== Upload Schemas =====

class KBUploadResponse(BaseModel):
    """Schema for file upload response."""
    document_id: UUID4
    filename: str
    file_size: int
    status: str
    message: str


# ===== Search Schemas =====

class KBSearchRequest(BaseModel):
    """Schema for KB search request."""
    query: str = Field(..., description="Search query", min_length=1)
    k: int = Field(default=5, description="Number of results to return", ge=1, le=20)
    category: Optional[str] = Field(None, description="Filter by category")
    user_id: Optional[UUID4] = Field(None, description="Filter by user (admin only)")


class KBSearchResultChunk(BaseModel):
    """Schema for a single search result chunk."""
    chunk_id: UUID4
    document_id: UUID4
    content: str
    similarity_score: float
    chunk_index: int
    
    # Document metadata
    filename: str
    category: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class KBSearchResponse(BaseModel):
    """Schema for KB search response."""
    query: str
    results: List[KBSearchResultChunk]
    total_results: int
    processing_time_ms: float


# ===== Statistics Schemas =====

class KBStatsResponse(BaseModel):
    """Schema for KB statistics."""
    total_documents: int
    total_chunks: int
    total_size_bytes: int
    documents_by_category: dict
    documents_by_status: dict
    recent_uploads: List[KBDocumentResponse]


# ===== Chunk Schemas (for internal use) =====

class KBChunkBase(BaseModel):
    """Base schema for KB chunks."""
    document_id: UUID4
    chunk_index: int
    content: str
    char_count: int
    token_count: Optional[int] = None


class KBChunkInDB(KBChunkBase):
    """Schema for KB chunk in database."""
    id: UUID4
    created_at: datetime
    
    class Config:
        from_attributes = True



