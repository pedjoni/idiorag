"""Default sentence-based chunking strategy.

This is the standard chunker used when no custom chunker is specified.
It uses LlamaIndex's SentenceSplitter for general-purpose text chunking.
"""

from typing import List, Optional

from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import BaseNode, Document as LlamaDocument, TextNode

from .base import DocumentChunker
from ...config import get_settings


class DefaultChunker(DocumentChunker):
    """Default sentence-based chunking using LlamaIndex SentenceSplitter.
    
    This chunker is suitable for general text documents like articles, notes,
    plain text logs, etc. It splits text by sentences while respecting
    configured chunk_size and chunk_overlap.
    
    Configuration:
        - chunk_size: Controlled by CHUNK_SIZE env var (default: 512)
        - chunk_overlap: Controlled by CHUNK_OVERLAP env var (default: 50)
    """
    
    def __init__(self):
        """Initialize the default chunker with settings from config."""
        settings = get_settings()
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        self.splitter = SentenceSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
    
    def chunk_document(
        self,
        content: str,
        document_id: str,
        user_id: str,
        metadata: Optional[dict] = None,
    ) -> List[BaseNode]:
        """Chunk document using sentence-based splitting.
        
        Args:
            content: The document text to chunk
            document_id: Unique document identifier
            user_id: User identifier for isolation
            metadata: Additional metadata to attach
            
        Returns:
            List of TextNode objects with proper metadata
        """
        # Prepare metadata
        node_metadata = {
            "document_id": document_id,
            "user_id": user_id,
        }
        if metadata:
            node_metadata.update(metadata)
        
        # Create LlamaIndex document
        llama_doc = LlamaDocument(
            text=content,
            metadata=node_metadata,
            id_=document_id,
        )
        
        # Split into nodes
        nodes = self.splitter.get_nodes_from_documents([llama_doc])
        
        # Ensure each node has proper ref_doc_id for deletion
        for node in nodes:
            node.ref_doc_id = document_id
            # Ensure user_id is present (critical for isolation)
            if "user_id" not in node.metadata:
                node.metadata["user_id"] = user_id
        
        # Validate nodes meet IdioRAG requirements
        self.validate_nodes(nodes, user_id, document_id)
        
        return nodes
