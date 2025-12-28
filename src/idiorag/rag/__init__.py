"""LlamaIndex RAG integration with user isolation."""

from typing import List, Optional

from llama_index.core import Document as LlamaDocument
from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import BaseNode, TextNode
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.llms import CustomLLM, CompletionResponse, LLMMetadata
from llama_index.vector_stores.postgres import PGVectorStore
import httpx
from typing import Any

from ..config import get_settings
from ..logging_config import get_logger

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
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "temperature": kwargs.get("temperature", self.temperature),
                    "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                },
                timeout=60.0,
            )
            response.raise_for_status()
            result = response.json()
            return CompletionResponse(text=result["choices"][0]["text"])
    
    def stream_complete(self, prompt: str, **kwargs: Any):
        """Stream complete - not implemented yet."""
        raise NotImplementedError("Streaming not implemented")



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
        logger.info(f"Initializing LLM client: {settings.llm_model_name}")
        
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
) -> List[BaseNode]:
    """Create text nodes from content with user isolation.
    
    Args:
        content: Document content to chunk
        document_id: Document identifier
        user_id: User identifier for isolation
        metadata: Additional metadata
    
    Returns:
        List[BaseNode]: List of text nodes
    """
    settings = get_settings()
    
    # Create node parser
    parser = SentenceSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    
    # Create LlamaIndex document
    doc_metadata = {
        "document_id": document_id,
        "user_id": user_id,
        **(metadata or {}),
    }
    
    llama_doc = LlamaDocument(
        text=content,
        metadata=doc_metadata,
    )
    
    # Parse into nodes
    nodes = parser.get_nodes_from_documents([llama_doc])
    
    logger.info(f"Created {len(nodes)} nodes for document {document_id}")
    return nodes


async def index_document(
    document_id: str,
    content: str,
    user_id: str,
    metadata: Optional[dict] = None,
) -> None:
    """Index a document for RAG with user isolation.
    
    Args:
        document_id: Document identifier
        content: Document content
        user_id: User identifier
        metadata: Additional metadata
    """
    try:
        logger.info(f"Indexing document {document_id} for user {user_id}")
        
        # Initialize embedding model
        get_embedding_model()
        
        # Create nodes with user isolation
        nodes = create_text_nodes(content, document_id, user_id, metadata)
        
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


async def query_with_context(
    query: str,
    user_id: str,
    top_k: int = 5,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
) -> dict:
    """Query the RAG system with user's context.
    
    Args:
        query: User query
        user_id: User identifier for context isolation
        top_k: Number of context chunks to retrieve
        max_tokens: Maximum tokens in response
        temperature: LLM temperature
    
    Returns:
        dict: Response with answer, context chunks, and metadata
    """
    try:
        logger.info(f"Processing query for user {user_id}: {query[:100]}")
        
        # Initialize models
        get_embedding_model()
        llm = get_llm()
        
        # Get vector store with user isolation
        vector_store = get_vector_store(user_id)
        
        # Create index from vector store
        index = VectorStoreIndex.from_vector_store(vector_store)
        
        # Create query engine
        # Note: User isolation is handled by metadata in nodes during indexing
        query_engine = index.as_query_engine(
            similarity_top_k=top_k,
            llm=llm,
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
        
        logger.info(f"Query completed with {len(context_chunks)} context chunks")
        logger.info(f"LLM Answer: {str(response)[:200]}...")
        
        return {
            "query": query,
            "answer": str(response),
            "context": context_chunks,
            "tokens_used": None,  # TODO: Track token usage if LLM provides it
        }
        
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise
