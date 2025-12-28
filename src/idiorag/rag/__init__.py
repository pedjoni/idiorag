"""LlamaIndex RAG integration with user isolation."""

from typing import List, Optional

from llama_index.core import Document as LlamaDocument
from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import BaseNode, TextNode
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai_like import OpenAILike
from llama_index.vector_stores.postgres import PGVectorStore

from ..config import get_settings
from ..logging_config import get_logger

logger = get_logger(__name__)

# Global instances
_embedding_model: Optional[HuggingFaceEmbedding] = None
_llm: Optional[OpenAILike] = None
_vector_store: Optional[PGVectorStore] = None


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


def get_llm() -> OpenAILike:
    """Get or initialize the LLM client.
    
    Returns:
        OpenAILike: Configured LLM client
    """
    global _llm
    
    if _llm is None:
        settings = get_settings()
        logger.info(f"Initializing LLM client: {settings.llm_model_name}")
        
        _llm = OpenAILike(
            model=settings.llm_model_name,
            api_base=settings.llm_api_url,
            api_key=settings.llm_api_key or "dummy-key",  # Some APIs don't require keys
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            is_chat_model=True,
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
    
    # Extract connection details from DATABASE_URL
    # Convert asyncpg to psycopg2 URL for pgvector
    db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    vector_store = PGVectorStore.from_params(
        database=db_url.split("/")[-1].split("?")[0],
        host=db_url.split("@")[1].split(":")[0],
        password=db_url.split(":")[2].split("@")[0],
        port=int(db_url.split(":")[-1].split("/")[0]),
        user=db_url.split("://")[1].split(":")[0],
        table_name="vector_embeddings",
        embed_dim=settings.embedding_dimension,
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
    logger.info(f"Indexing document {document_id} for user {user_id}")
    
    # Initialize models
    get_embedding_model()
    
    # Create nodes
    nodes = create_text_nodes(content, document_id, user_id, metadata)
    
    # Get vector store
    vector_store = get_vector_store(user_id)
    
    # Create index and add nodes
    index = VectorStoreIndex.from_vector_store(vector_store)
    
    # Add nodes to index
    for node in nodes:
        index.insert_nodes([node])
    
    logger.info(f"Successfully indexed document {document_id}")


async def delete_document_from_index(document_id: str, user_id: str) -> None:
    """Delete a document from the vector index.
    
    Args:
        document_id: Document identifier
        user_id: User identifier
    """
    logger.info(f"Deleting document {document_id} from index")
    
    # TODO: Implement deletion from vector store
    # This requires querying by metadata and deleting matching nodes
    pass
