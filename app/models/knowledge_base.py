"""Knowledge Base models for document storage and vector embeddings."""
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
import uuid

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class KnowledgeBaseDocument(Base):
    """
    Knowledge Base documents with vector embeddings for RAG.
    
    Stores uploaded documents, their chunks, and vector embeddings
    for semantic search and retrieval.
    
    Relationships:
        user: Document owner
        chunks: Document chunks with embeddings
    """
    __tablename__ = "kb_documents"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Owner
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Document Information
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # in bytes
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Metadata
    category: Mapped[str] = mapped_column(
        String(50),
        default="general",
        nullable=False,
        index=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Comma-separated
    
    # Processing Status
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
        index=True
    )  # pending, processing, completed, failed
    
    total_chunks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="kb_documents")
    chunks: Mapped[list["KnowledgeBaseChunk"]] = relationship(
        "KnowledgeBaseChunk",
        back_populates="document",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<KBDocument(id={self.id}, filename='{self.filename}', status='{self.status}')>"


class KnowledgeBaseChunk(Base):
    """
    Document chunks with vector embeddings.
    
    Each document is split into chunks for efficient retrieval.
    Each chunk has its own vector embedding for semantic search.
    """
    __tablename__ = "kb_chunks"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Parent Document
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("kb_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Chunk Information
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Vector Embedding (1536 dimensions for OpenAI text-embedding-ada-002)
    embedding: Mapped[Optional[list]] = mapped_column(
        Vector(1536),
        nullable=True
    )
    
    # Metadata
    char_count: Mapped[int] = mapped_column(Integer, nullable=False)
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    document: Mapped["KnowledgeBaseDocument"] = relationship(
        "KnowledgeBaseDocument",
        back_populates="chunks"
    )
    
    def __repr__(self) -> str:
        return f"<KBChunk(id={self.id}, doc_id={self.document_id}, index={self.chunk_index})>"


# Create index for vector similarity search
Index(
    'kb_chunks_embedding_idx',
    KnowledgeBaseChunk.embedding,
    postgresql_using='ivfflat',
    postgresql_with={'lists': 100},
    postgresql_ops={'embedding': 'vector_cosine_ops'}
)








