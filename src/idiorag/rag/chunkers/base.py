"""Base class for document chunking strategies.

This module provides the abstract interface that all custom chunkers must implement.
Users can create their own chunking strategies by extending DocumentChunker.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from llama_index.core.schema import BaseNode


class DocumentChunker(ABC):
    """Abstract base class for document chunking strategies.
    
    Custom chunkers should extend this class and implement the chunk_document method.
    The chunker is responsible for converting raw document content into a list of
    nodes that will be embedded and stored in the vector database.
    
    Example:
        ```python
        from idiorag.rag.chunkers.base import DocumentChunker
        from llama_index.core.schema import TextNode
        
        class MyCustomChunker(DocumentChunker):
            def chunk_document(self, content, document_id, user_id, metadata):
                # Your custom logic here
                nodes = []
                for chunk in my_custom_splitting_logic(content):
                    node = TextNode(
                        text=chunk,
                        metadata={
                            "document_id": document_id,
                            "user_id": user_id,
                            **metadata
                        }
                    )
                    node.ref_doc_id = document_id
                    nodes.append(node)
                return nodes
        ```
    """
    
    @abstractmethod
    def chunk_document(
        self,
        content: str,
        document_id: str,
        user_id: str,
        metadata: Optional[dict] = None,
    ) -> List[BaseNode]:
        """Convert document content into chunks (nodes) for indexing.
        
        This method should split the document into semantically meaningful chunks,
        create TextNode objects for each chunk, and ensure proper metadata is attached
        for user isolation and retrieval.
        
        Args:
            content: The raw document content to chunk
            document_id: Unique identifier for the document (used for ref_doc_id)
            user_id: User identifier for user isolation (must be in metadata)
            metadata: Additional metadata to attach to each chunk (optional)
            
        Returns:
            List of BaseNode objects (typically TextNode) ready for indexing
            
        Note:
            - Each node MUST have user_id in metadata for proper isolation
            - Each node MUST have ref_doc_id set to document_id for deletion
            - Each node should include document_id in metadata for context
            - Additional metadata can enhance retrieval and filtering
        """
        pass
    
    def validate_nodes(self, nodes: List[BaseNode], user_id: str, document_id: str) -> bool:
        """Validate that nodes meet requirements for IdioRAG.
        
        This helper method checks that nodes have required metadata for proper
        functioning within the IdioRAG framework.
        
        Args:
            nodes: List of nodes to validate
            user_id: Expected user_id that should be in all nodes
            document_id: Expected document_id that should be in all nodes
            
        Returns:
            True if all nodes are valid, False otherwise
            
        Raises:
            ValueError: If validation fails with details about the issue
        """
        for i, node in enumerate(nodes):
            # Check metadata exists
            if not hasattr(node, 'metadata') or not node.metadata:
                raise ValueError(f"Node {i} missing metadata")
            
            # Check user_id for isolation
            if node.metadata.get('user_id') != user_id:
                raise ValueError(f"Node {i} missing or incorrect user_id")
            
            # Check document_id for context
            if 'document_id' not in node.metadata:
                raise ValueError(f"Node {i} missing document_id in metadata")
            
            # Check ref_doc_id for deletion
            if not hasattr(node, 'ref_doc_id') or node.ref_doc_id != document_id:
                raise ValueError(f"Node {i} missing or incorrect ref_doc_id")
        
        return True
