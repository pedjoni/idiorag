"""LlamaIndex RAG integration with user isolation."""

from typing import List, Optional

from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.schema import BaseNode
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.llms import CustomLLM, CompletionResponse, LLMMetadata
from llama_index.vector_stores.postgres import PGVectorStore
import httpx
from typing import Any
from sqlalchemy import select, func as sql_func
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..logging_config import get_logger
from ..database import Document, async_session_factory

logger = get_logger(__name__)

# Global instances
_embedding_model: Optional[HuggingFaceEmbedding] = None
_llm: Optional[CustomLLM] = None
_vector_store: Optional[PGVectorStore] = None


class OpenAICompatibleLLM(CustomLLM):
    """Custom LLM for OpenAI-compatible APIs (like Qwen, Ollama, etc)."""
    
    api_base: str
    api_key: str
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 2048
    context_window: int = 32768  # Default context window
    
    @property
    def metadata(self) -> LLMMetadata:
        """Get LLM metadata."""
        return LLMMetadata(
            context_window=self.context_window,
            num_output=self.max_tokens,
            model_name=self.model_name,
        )
    
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        """Complete synchronously - not used in async app."""
        raise NotImplementedError("Use acomplete for async operations")
    
    async def acomplete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        """Complete asynchronously."""
        # Stop sequences can be overridden via kwargs or use empty list
        stop_sequences = kwargs.get("stop", [])
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self.api_base}/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "temperature": kwargs.get("temperature", self.temperature),
                    "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                    "stop": stop_sequences,
                },
            )
            response.raise_for_status()
            result = response.json()
            return CompletionResponse(text=result["choices"][0]["text"])
    
    def stream_complete(self, prompt: str, **kwargs: Any):
        """Stream complete synchronously - not used in async app."""
        raise NotImplementedError("Use astream_complete for async operations")
    
    async def astream_complete(self, prompt: str, **kwargs: Any):
        """Stream complete asynchronously.
        
        Yields completion response deltas as they arrive from the LLM.
        """
        import json
        
        # Stop sequences can be overridden via kwargs or use empty list
        stop_sequences = kwargs.get("stop", [])
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                f"{self.api_base}/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "temperature": kwargs.get("temperature", self.temperature),
                    "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                    "stream": True,
                    "stop": stop_sequences,
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or line == "data: [DONE]":
                        continue
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("text", "")
                                if delta:
                                    yield CompletionResponse(text=delta, delta=delta)
                        except json.JSONDecodeError:
                            continue



def get_embedding_model() -> HuggingFaceEmbedding:
    """Get or initialize the embedding model.
    
    Returns:
        HuggingFaceEmbedding: Configured embedding model
    """
    global _embedding_model
    
    if _embedding_model is None:
        settings = get_settings()
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        
        _embedding_model = HuggingFaceEmbedding(
            model_name=settings.embedding_model,
            cache_folder=".cache/embeddings",
        )
        
        # Configure LlamaIndex settings
        Settings.embed_model = _embedding_model
        Settings.chunk_size = settings.chunk_size
        Settings.chunk_overlap = settings.chunk_overlap
    
    return _embedding_model


def get_llm() -> OpenAICompatibleLLM:
    """Get or initialize the LLM client.
    
    Returns:
        OpenAICompatibleLLM: Configured LLM client
    """
    global _llm
    
    if _llm is None:
        settings = get_settings()
        logger.info(f"Initializing LLM client: {settings.llm_model_name} at {settings.llm_api_url}")
        
        _llm = OpenAICompatibleLLM(
            api_base=settings.llm_api_url,
            api_key=settings.llm_api_key or "dummy-key",
            model_name=settings.llm_model_name,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )
        
        Settings.llm = _llm
    
    return _llm


def get_vector_store(user_id: str) -> PGVectorStore:
    """Get vector store with user isolation.
    
    Note: Each user's vectors are stored with user_id metadata for isolation.
    
    Args:
        user_id: User identifier for data isolation
    
    Returns:
        PGVectorStore: Configured vector store
    """
    settings = get_settings()
    
    # Parse DATABASE_URL for pgvector connection
    # asyncpg format: postgresql+asyncpg://user:password@host:port/database
    from urllib.parse import urlparse
    
    parsed = urlparse(settings.database_url)
    
    vector_store = PGVectorStore.from_params(
        database=parsed.path.lstrip("/").split("?")[0],
        host=parsed.hostname or "localhost",
        password=parsed.password or "",
        port=parsed.port or 5432,
        user=parsed.username or "postgres",
        table_name="vector_embeddings",
        embed_dim=settings.embedding_dimension,
        schema_name=settings.database_schema,
    )
    
    return vector_store


def create_text_nodes(
    content: str,
    document_id: str,
    user_id: str,
    metadata: Optional[dict] = None,
    chunker_name: str = "default",
) -> List[BaseNode]:
    """Create text nodes from content with user isolation.
    
    Uses the pluggable chunking system to support custom chunking strategies.
    
    Args:
        content: Document content to chunk
        document_id: Document identifier
        user_id: User identifier for isolation
        metadata: Additional metadata
        chunker_name: Name of chunker to use (default: "default")
    
    Returns:
        List[BaseNode]: List of text nodes
    """
    from .chunkers import get_chunker
    
    # Get appropriate chunker
    chunker = get_chunker(chunker_name)
    
    # Create nodes using the chunker
    nodes = chunker.chunk_document(
        content=content,
        document_id=document_id,
        user_id=user_id,
        metadata=metadata,
    )
    
    # CRITICAL: Ensure user_id is always stored as string for consistent PostgreSQL queries
    # This ensures compatibility regardless of which chunker is used
    for node in nodes:
        if "user_id" in node.metadata:
            node.metadata["user_id"] = str(node.metadata["user_id"])
    
    logger.info(f"Created {len(nodes)} nodes for document {document_id} using '{chunker_name}' chunker")
    return nodes


async def index_document(
    document_id: str,
    content: str,
    user_id: str,
    metadata: Optional[dict] = None,
    chunker_name: str = "default",
) -> None:
    """Index a document for RAG with user isolation.
    
    Args:
        document_id: Document identifier
        content: Document content
        user_id: User identifier
        metadata: Additional metadata
        chunker_name: Name of chunker to use (default: "default")
    """
    try:
        logger.info(f"Indexing document {document_id} for user {user_id} using '{chunker_name}' chunker")
        
        # Initialize embedding model
        get_embedding_model()
        
        # Create nodes with user isolation using specified chunker
        nodes = create_text_nodes(content, document_id, user_id, metadata, chunker_name)
        
        # Get vector store
        vector_store = get_vector_store(user_id)
        
        # Create index from vector store
        index = VectorStoreIndex.from_vector_store(vector_store)
        
        # Insert nodes into the index
        index.insert_nodes(nodes)
        
        logger.info(f"Successfully indexed {len(nodes)} nodes for document {document_id}")
        
    except Exception as e:
        logger.error(f"Error indexing document {document_id}: {e}", exc_info=True)
        raise


async def delete_document_from_index(document_id: str, user_id: str) -> None:
    """Delete a document from the vector index.
    
    Args:
        document_id: Document identifier
        user_id: User identifier
    """
    try:
        logger.info(f"Deleting document {document_id} from index for user {user_id}")
        
        # Get vector store
        vector_store = get_vector_store(user_id)
        
        # PGVectorStore.delete() requires ref_doc_id (the document_id we set in metadata)
        # We need to delete by ref_doc_id, not filters
        vector_store.delete(ref_doc_id=document_id)
        
        logger.info(f"Successfully deleted document {document_id} from index")
        
    except Exception as e:
        logger.error(f"Error deleting document {document_id} from index: {e}", exc_info=True)
        # Don't raise - allow deletion to proceed even if vector deletion fails
        pass


async def _get_total_documents_count(user_id: str) -> int:
    """Get total document count for a user.
    
    Args:
        user_id: User identifier
    
    Returns:
        int: Total number of documents in the user's index
    """
    try:
        async with async_session_factory() as session:
            result = await session.execute(
                select(sql_func.count(Document.id))
                .where(Document.user_id == user_id)
            )
            return result.scalar_one()
    except Exception as e:
        logger.warning(f"Error counting documents for user {user_id}: {e}")
        return 0


async def query_with_context(
    query: str,
    user_id: str,
    top_k: int = 5,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    use_cot: bool = False,
) -> dict:
    """Query the RAG system with user's context.
    
    Args:
        query: User query
        user_id: User identifier for context isolation
        top_k: Number of context chunks to retrieve
        max_tokens: Maximum tokens in response
        temperature: LLM temperature
        use_cot: Enable chain-of-thought reasoning
    
    Returns:
        dict: Response with answer, context chunks, and metadata
    """
    try:
        logger.info(f"Processing query for user {user_id}: {query[:100]}" + (" (CoT enabled)" if use_cot else ""))
        
        # Initialize models
        get_embedding_model()
        llm = get_llm()
        
        # Get vector store with user isolation
        vector_store = get_vector_store(user_id)
        
        # Create index from vector store
        index = VectorStoreIndex.from_vector_store(vector_store)
        
        # Create query engine with custom prompt
        from llama_index.core import PromptTemplate
        
        if use_cot:
            # Chain-of-thought prompt: reason first, then answer
            qa_prompt_tmpl = PromptTemplate(
                "You are a helpful assistant. Answer the user's question based only on the provided context.\n\n"
                "Context:\n{context_str}\n\n"
                "Question: {query_str}\n\n"
                "Think step-by-step about the information, then provide your final answer after 'Final Answer:'.\\n\\n"
                "Reasoning:"
            )
        else:
            # Direct answer prompt
            qa_prompt_tmpl = PromptTemplate(
                "You are a helpful assistant. Answer the user's question based only on the provided context. Be direct and concise.\n\n"
                "Context:\n{context_str}\n\n"
                "Question: {query_str}\n\n"
                "Provide a brief, direct answer (2-3 sentences maximum):"
            )
        
        # User isolation: filter by user_id in metadata
        # Convert user_id to string to ensure consistent comparison in PostgreSQL
        from llama_index.core.vector_stores import MetadataFilters, MetadataFilter, FilterOperator
        
        filters = MetadataFilters(
            filters=[MetadataFilter(key="user_id", value=str(user_id), operator=FilterOperator.EQ)]
        )
        
        query_engine = index.as_query_engine(
            similarity_top_k=top_k,
            llm=llm,
            text_qa_template=qa_prompt_tmpl,
            filters=filters,
        )
        
        # Override settings if provided
        if temperature is not None:
            llm.temperature = temperature
        if max_tokens is not None:
            llm.max_tokens = max_tokens
        
        # Execute query
        response = await query_engine.aquery(query)
        
        # Extract context chunks
        context_chunks = []
        for node in response.source_nodes:
            context_chunks.append({
                "document_id": node.metadata.get("document_id", "unknown"),
                "content": node.text,
                "score": node.score or 0.0,
                "metadata": node.metadata,
            })
        
        # Collect metadata about retrieval quality
        total_docs = await _get_total_documents_count(user_id)
        documents_retrieved = len(context_chunks)
        avg_relevance_score = (
            sum(chunk["score"] for chunk in context_chunks) / documents_retrieved
            if documents_retrieved > 0 else 0.0
        )
        
        metadata = {
            "total_documents_in_index": total_docs,
            "documents_retrieved": documents_retrieved,
            "avg_relevance_score": round(avg_relevance_score, 3),
        }
        
        logger.info(f"Query completed with {len(context_chunks)} context chunks")
        logger.info(f"Query metadata - Total docs: {total_docs}, Retrieved: {documents_retrieved}, Avg score: {metadata['avg_relevance_score']}")
        logger.info(f"LLM Answer: {str(response)[:200]}...")
        
        return {
            "query": query,
            "answer": str(response),
            "context": context_chunks,
            "tokens_used": None,  # TODO: Track token usage if LLM provides it
            "metadata": metadata,
        }
        
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise


async def query_with_context_stream(
    query: str,
    user_id: str,
    top_k: int = 5,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    use_cot: bool = False,
):
    """Query the RAG system with streaming response.
    
    Yields:
        dict: Events with type 'context', 'token', or 'done'
            - context: {"type": "context", "chunks": [...]}
            - token: {"type": "token", "content": "..."}
            - done: {"type": "done"}
    
    Args:
        query: User query
        user_id: User identifier for context isolation
        top_k: Number of context chunks to retrieve
        max_tokens: Maximum tokens in response
        temperature: LLM temperature
        use_cot: Enable chain-of-thought reasoning
    """
    try:
        logger.info(f"Processing streaming query for user {user_id}: {query[:100]}" + (" (CoT enabled)" if use_cot else ""))
        
        # Initialize models
        get_embedding_model()
        llm = get_llm()
        
        # Override settings if provided
        if temperature is not None:
            llm.temperature = temperature
        if max_tokens is not None:
            llm.max_tokens = max_tokens
        
        # Get vector store with user isolation
        vector_store = get_vector_store(user_id)
        
        # Create index from vector store
        index = VectorStoreIndex.from_vector_store(vector_store)
        
        # User isolation: filter by user_id in metadata
        # Convert user_id to string to ensure consistent comparison in PostgreSQL
        from llama_index.core.vector_stores import MetadataFilters, MetadataFilter, FilterOperator
        
        filters = MetadataFilters(
            filters=[MetadataFilter(key="user_id", value=str(user_id), operator=FilterOperator.EQ)]
        )
        
        # Retrieve context chunks first with user filter
        retriever = index.as_retriever(similarity_top_k=top_k, filters=filters)
        nodes = await retriever.aretrieve(query)
        
        # Format and send context
        context_chunks = []
        for node in nodes:
            context_chunks.append({
                "document_id": node.metadata.get("document_id", "unknown"),
                "content": node.text,
                "score": node.score or 0.0,
                "metadata": node.metadata,
            })
        
        # Collect metadata about retrieval quality
        total_docs = await _get_total_documents_count(user_id)
        documents_retrieved = len(context_chunks)
        avg_relevance_score = (
            sum(chunk["score"] for chunk in context_chunks) / documents_retrieved
            if documents_retrieved > 0 else 0.0
        )
        
        metadata = {
            "total_documents_in_index": total_docs,
            "documents_retrieved": documents_retrieved,
            "avg_relevance_score": round(avg_relevance_score, 3),
        }
        
        logger.info(f"Streaming query metadata - Total docs: {total_docs}, Retrieved: {documents_retrieved}, Avg score: {metadata['avg_relevance_score']}")
        
        context_event = {
            "type": "context",
            "chunks": context_chunks,
            "metadata": metadata
        }
        
        logger.info(f"Yielding context event with {len(context_chunks)} chunks and metadata: {metadata}")
        yield context_event
        
        # Build prompt with context
        context_str = "\n\n".join([
            f"[Source {i+1}] {chunk['content']}"
            for i, chunk in enumerate(context_chunks)
        ])
        
        if use_cot:
            # Chain-of-thought with structured output
            prompt = f"""You are a helpful assistant. Answer the user's question based only on the provided context.

Context:
{context_str}

Question: {query}

You MUST respond using this exact format. Start immediately with the <thinking> tag:

<thinking>
[Your step-by-step analysis here]
</thinking>
<answer>
[Your concise final answer here]
</answer>

Begin your response now with <thinking>:"""
        else:
            # Direct answer with structured output
            prompt = f"""You are a helpful assistant. Answer the user's question based only on the provided context.

Context:
{context_str}

Question: {query}

Provide your answer inside <answer> tags. Be direct and concise (2-3 sentences).

<answer>"""
        
        # Stream the response with parsing for structured tags
        # Add stop sequences to prevent LLM from continuing after closing tags
        # For CoT, only stop after </answer> (not </thinking>, we need the answer section too!)
        settings = get_settings()
        stop_sequences = ["</answer>"]
        
        # Track parsing state
        buffer = ""
        in_thinking = False
        in_answer = False
        
        async for response in llm.astream_complete(prompt, stop=stop_sequences):
            if response.delta:
                buffer += response.delta
                
                # Parse and emit events based on tags
                while buffer:
                    if not in_thinking and not in_answer:
                        # Look for opening tags
                        if "<thinking>" in buffer:
                            idx = buffer.index("<thinking>")
                            # Emit any content before tag as token
                            if idx > 0:
                                yield {"type": "token", "content": buffer[:idx]}
                            buffer = buffer[idx + 10:]  # Skip "<thinking>"
                            in_thinking = True
                            continue
                        elif "<answer>" in buffer:
                            idx = buffer.index("<answer>")
                            if idx > 0:
                                yield {"type": "token", "content": buffer[:idx]}
                            buffer = buffer[idx + 8:]  # Skip "<answer>"
                            in_answer = True
                            continue
                        else:
                            # No tags found, emit what we have except last few chars (might be partial tag)
                            if len(buffer) > 10:
                                emit_len = len(buffer) - 10
                                yield {"type": "token", "content": buffer[:emit_len]}
                                buffer = buffer[emit_len:]
                            break
                    
                    elif in_thinking:
                        # Look for closing tag
                        if "</thinking>" in buffer:
                            idx = buffer.index("</thinking>")
                            if idx > 0:
                                yield {"type": "thinking", "content": buffer[:idx]}
                            buffer = buffer[idx + 11:]  # Skip "</thinking>"
                            in_thinking = False
                            continue
                        else:
                            # Emit thinking content except last few chars
                            if len(buffer) > 12:
                                emit_len = len(buffer) - 12
                                yield {"type": "thinking", "content": buffer[:emit_len]}
                                buffer = buffer[emit_len:]
                            break
                    
                    elif in_answer:
                        # Look for closing tag
                        if "</answer>" in buffer:
                            idx = buffer.index("</answer>")
                            if idx > 0:
                                yield {"type": "answer", "content": buffer[:idx]}
                            buffer = buffer[idx + 9:]  # Skip "</answer>"
                            in_answer = False
                            continue
                        else:
                            # Emit answer content except last few chars
                            if len(buffer) > 10:
                                emit_len = len(buffer) - 10
                                yield {"type": "answer", "content": buffer[:emit_len]}
                                buffer = buffer[emit_len:]
                            break
        
        # Emit any remaining buffer content
        if buffer:
            if in_thinking:
                yield {"type": "thinking", "content": buffer}
            elif in_answer:
                yield {"type": "answer", "content": buffer}
            else:
                yield {"type": "token", "content": buffer}
        
        # Signal completion
        yield {"type": "done"}
        
        logger.info(f"Streaming query completed for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error processing streaming query: {e}", exc_info=True)
        yield {
            "type": "error",
            "message": str(e)
        }
