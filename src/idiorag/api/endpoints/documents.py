"""Document ingestion endpoints."""

import hashlib
import json
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...auth import CurrentUser
from ...database import Document, get_db
from ...logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


def _deserialize_metadata(metadata_str: str | None) -> Dict[str, Any] | None:
    """Deserialize metadata JSON string to dict."""
    if metadata_str is None:
        return None
    try:
        return json.loads(metadata_str)
    except (json.JSONDecodeError, TypeError):
        return None


class DocumentCreate(BaseModel):
    """Request model for document creation."""
    
    title: str = Field(..., min_length=1, max_length=500, description="Document title")
    content: str = Field(..., min_length=1, description="Document content")
    metadata: Dict[str, Any] | None = Field(default=None, description="Additional metadata")
    doc_type: str | None = Field(default=None, max_length=100, description="Document type (can auto-select chunker)")
    source: str | None = Field(default=None, max_length=500, description="Document source")
    chunker: str | None = Field(default=None, max_length=50, description="Chunking strategy to use (default: auto-detect from doc_type)")


class DocumentResponse(BaseModel):
    """Response model for document."""
    
    id: str
    user_id: str
    title: str
    content: str
    metadata: Dict[str, Any] | None
    doc_type: str | None
    source: str | None
    created_at: str
    updated_at: str
    action: str | None = Field(default=None, description="Action taken: 'created', 'updated', or 'unchanged'")


class DocumentListResponse(BaseModel):
    """Response model for document list."""
    
    documents: List[DocumentResponse]
    total: int


@router.post(
    "",
    response_model=DocumentResponse,
    summary="Create or update a document"
)
async def create_document(
    document: DocumentCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db)
) -> DocumentResponse:
    """Create or update a document with automatic deduplication.
    
    If a document with the same 'source' field exists for this user:
    - If content is identical → Return existing document (200, action='unchanged')
    - If content is different → Update and re-index (200, action='updated')
    
    If no existing document with this source → Create new (201, action='created')
    
    The document will be:
    1. Stored in the database (or updated)
    2. Chunked according to configured strategy
    3. Embedded using the configured model
    4. Stored in the vector database with user_id isolation
    
    Args:
        document: Document creation data
        user: Current authenticated user
        db: Database session
    
    Returns:
        DocumentResponse: Created or updated document with action indicator
    """
    logger.info(f"Processing document for user {user.user_id}: {document.title}")
    
    # Check if document with this source already exists for this user
    existing_doc = None
    if document.source:
        result = await db.execute(
            select(Document).where(
                Document.user_id == user.user_id,
                Document.source == document.source
            )
        )
        existing_doc = result.scalar_one_or_none()
    
    # Calculate content hash for comparison
    content_hash = hashlib.sha256(document.content.encode('utf-8')).hexdigest()
    
    if existing_doc:
        # Document exists - check if content changed
        existing_hash = hashlib.sha256(existing_doc.content.encode('utf-8')).hexdigest()
        
        if existing_hash == content_hash:
            # Content is identical - return existing document
            logger.info(f"Document unchanged (source={document.source}): {existing_doc.id}")
            return DocumentResponse(
                id=existing_doc.id,
                user_id=existing_doc.user_id,
                title=existing_doc.title,
                content=existing_doc.content,
                metadata=_deserialize_metadata(existing_doc.metadata_),
                doc_type=existing_doc.doc_type,
                source=existing_doc.source,
                created_at=existing_doc.created_at.isoformat(),
                updated_at=existing_doc.updated_at.isoformat(),
                action="unchanged"
            )
        else:
            # Content changed - update and re-index
            logger.info(f"Updating document (source={document.source}): {existing_doc.id}")
            
            # Update document fields
            existing_doc.title = document.title
            existing_doc.content = document.content
            existing_doc.metadata_ = json.dumps(document.metadata) if document.metadata else None
            existing_doc.doc_type = document.doc_type
            
            await db.commit()
            await db.refresh(existing_doc)
            
            # Delete old vectors and re-index
            try:
                from ...rag import delete_document_from_index, index_document
                
                # Delete old vectors
                await delete_document_from_index(existing_doc.id, user.user_id)
                logger.info(f"Deleted old vectors for document: {existing_doc.id}")
                
                # Re-index with new content
                chunker_name = document.chunker or "default"
                if not document.chunker and document.doc_type:
                    # TODO: Add DOC_TYPE_CHUNKER_MAPPING to config
                    pass
                
                await index_document(
                    document_id=existing_doc.id,
                    content=document.content,
                    user_id=user.user_id,
                    metadata=document.metadata,
                    chunker_name=chunker_name
                )
                logger.info(f"Document re-indexed successfully using '{chunker_name}' chunker: {existing_doc.id}")
            except Exception as e:
                logger.error(f"Error re-indexing document {existing_doc.id}: {e}")
                # Don't fail the request if indexing fails
            
            return DocumentResponse(
                id=existing_doc.id,
                user_id=existing_doc.user_id,
                title=existing_doc.title,
                content=existing_doc.content,
                metadata=_deserialize_metadata(existing_doc.metadata_),
                doc_type=existing_doc.doc_type,
                source=existing_doc.source,
                created_at=existing_doc.created_at.isoformat(),
                updated_at=existing_doc.updated_at.isoformat(),
                action="updated"
            )
    
    # No existing document - create new
    logger.info(f"Creating new document for user {user.user_id}: {document.title}")
    
    doc_id = str(uuid.uuid4())
    db_document = Document(
        id=doc_id,
        user_id=user.user_id,
        title=document.title,
        content=document.content,
        metadata_=json.dumps(document.metadata) if document.metadata else None,
        doc_type=document.doc_type,
        source=document.source,
    )
    
    db.add(db_document)
    await db.commit()
    await db.refresh(db_document)
    
    # Index document in vector store
    try:
        from ...rag import index_document
        
        chunker_name = document.chunker or "default"
        if not document.chunker and document.doc_type:
            # TODO: Add DOC_TYPE_CHUNKER_MAPPING to config
            pass
        
        await index_document(
            document_id=doc_id,
            content=document.content,
            user_id=user.user_id,
            metadata=document.metadata,
            chunker_name=chunker_name
        )
        logger.info(f"Document indexed successfully using '{chunker_name}' chunker: {doc_id}")
    except Exception as e:
        logger.error(f"Error indexing document {doc_id}: {e}")
        # Don't fail the request if indexing fails - document is still in DB
    
    logger.info(f"Document created successfully: {doc_id}")
    
    response = DocumentResponse(
        id=db_document.id,
        user_id=db_document.user_id,
        title=db_document.title,
        content=db_document.content,
        metadata=_deserialize_metadata(db_document.metadata_),
        doc_type=db_document.doc_type,
        source=db_document.source,
        created_at=db_document.created_at.isoformat(),
        updated_at=db_document.updated_at.isoformat(),
        action="created"
    )
    
    # Set 201 status code for new documents
    return Response(
        content=response.model_dump_json(),
        status_code=status.HTTP_201_CREATED,
        media_type="application/json"
    )


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List user's documents"
)
async def list_documents(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> DocumentListResponse:
    """List all documents for the current user.
    
    Args:
        user: Current authenticated user
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
    
    Returns:
        DocumentListResponse: List of user's documents
    """
    logger.debug(f"Listing documents for user {user.user_id}")
    
    # Query documents for current user
    result = await db.execute(
        select(Document)
        .where(Document.user_id == user.user_id)
        .offset(skip)
        .limit(limit)
        .order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()
    
    # Count total documents
    from sqlalchemy import func as sql_func
    count_result = await db.execute(
        select(sql_func.count(Document.id))
        .where(Document.user_id == user.user_id)
    )
    total = count_result.scalar_one()
    
    return DocumentListResponse(
        documents=[
            DocumentResponse(
                id=doc.id,
                user_id=doc.user_id,
                title=doc.title,
                content=doc.content,
                metadata=_deserialize_metadata(doc.metadata_),
                doc_type=doc.doc_type,
                source=doc.source,
                created_at=doc.created_at.isoformat(),
                updated_at=doc.updated_at.isoformat(),
            )
            for doc in documents
        ],
        total=total
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get a specific document"
)
async def get_document(
    document_id: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db)
) -> DocumentResponse:
    """Get a specific document by ID.
    
    Only returns documents owned by the current user.
    
    Args:
        document_id: Document ID
        user: Current authenticated user
        db: Database session
    
    Returns:
        DocumentResponse: Document details
    
    Raises:
        HTTPException: If document not found or access denied
    """
    result = await db.execute(
        select(Document)
        .where(Document.id == document_id)
        .where(Document.user_id == user.user_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return DocumentResponse(
        id=document.id,
        user_id=document.user_id,
        title=document.title,
        content=document.content,
        metadata=_deserialize_metadata(document.metadata_),
        doc_type=document.doc_type,
        source=document.source,
        created_at=document.created_at.isoformat(),
        updated_at=document.updated_at.isoformat(),
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document"
)
async def delete_document(
    document_id: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a document.
    
    Removes the document from both the database and vector store.
    
    Args:
        document_id: Document ID
        user: Current authenticated user
        db: Database session
    
    Raises:
        HTTPException: If document not found or access denied
    """
    result = await db.execute(
        select(Document)
        .where(Document.id == document_id)
        .where(Document.user_id == user.user_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete from vector store
    try:
        from ...rag import delete_document_from_index
        await delete_document_from_index(document_id, user.user_id)
    except Exception as e:
        logger.warning(f"Error deleting document from vector store: {e}")
        # Continue with DB deletion even if vector deletion fails
    
    await db.delete(document)
    await db.commit()
    logger.info(f"Document deleted: {document_id}")
