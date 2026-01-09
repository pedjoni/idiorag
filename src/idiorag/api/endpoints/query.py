"""Query endpoints for RAG."""

from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...auth import CurrentUser
from ...database import get_db
from ...logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


class QueryRequest(BaseModel):
    """Request model for RAG query."""
    
    query: str = Field(..., min_length=1, max_length=2000, description="User query")
    max_tokens: int | None = Field(default=256, ge=1, le=32000, description="Maximum tokens in response")
    temperature: float | None = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature")
    top_k: int = Field(default=5, ge=1, le=1000, description="Number of context chunks to retrieve")
    use_cot: bool = Field(default=False, description="Enable chain-of-thought reasoning for complex queries")


class ContextChunk(BaseModel):
    """Context chunk used in RAG response."""
    
    document_id: str
    content: str
    score: float
    metadata: dict | None = None


class QueryResponse(BaseModel):
    """Response model for RAG query."""
    
    query: str
    answer: str
    context: List[ContextChunk]
    tokens_used: int | None = None


@router.post(
    "/",
    response_model=QueryResponse,
    summary="Query the RAG system"
)
async def query_rag(
    request: QueryRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db)
) -> QueryResponse:
    """Query the RAG system with user's private context.
    
    This endpoint:
    1. Embeds the user's query
    2. Retrieves relevant context chunks from the user's documents only
    3. Sends query + context to the LLM
    4. Returns the answer with source context
    
    Args:
        request: Query request with parameters
        user: Current authenticated user
        db: Database session
    
    Returns:
        QueryResponse: Answer with context chunks
    """
    logger.info(f"Processing query for user {user.user_id}: {request.query[:100]}")
    
    try:
        from ...rag import query_with_context
        
        response_data = await query_with_context(
            query=request.query,
            user_id=user.user_id,
            top_k=request.top_k,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            use_cot=request.use_cot,
        )
        
        return QueryResponse(
            query=response_data["query"],
            answer=response_data["answer"],
            context=[
                ContextChunk(
                    document_id=chunk["document_id"],
                    content=chunk["content"],
                    score=chunk["score"],
                    metadata=chunk.get("metadata"),
                )
                for chunk in response_data["context"]
            ],
            tokens_used=response_data.get("tokens_used"),
        )
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        # Return error message as answer
        return QueryResponse(
            query=request.query,
            answer=f"Error processing query: {str(e)}",
            context=[],
            tokens_used=None
        )


@router.post(
    "/chat",
    summary="Chat with streaming response"
)
async def chat_stream(
    request: QueryRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Chat endpoint with streaming response.
    
    Returns a Server-Sent Events stream for real-time responses.
    
    The stream sends events in the following format:
    - context: Initial context chunks retrieved
    - token: Individual tokens as they're generated
    - done: Signals completion
    - error: Error message if something fails
    
    Args:
        request: Query request with parameters
        user: Current authenticated user
        db: Database session
    
    Returns:
        StreamingResponse: SSE stream with answer chunks
    """
    from fastapi.responses import StreamingResponse
    from ...rag import query_with_context_stream
    import json
    
    logger.info(f"Chat stream requested by user {user.user_id}: {request.query[:100]}")
    
    async def generate():
        try:
            async for event in query_with_context_stream(
                query=request.query,
                user_id=user.user_id,
                top_k=request.top_k,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                use_cot=request.use_cot,
            ):
                # Send as Server-Sent Event
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            logger.error(f"Error in chat stream: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
