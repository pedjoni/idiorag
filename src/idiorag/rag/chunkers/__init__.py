"""Chunker registry and factory for pluggable chunking strategies.

This module manages the registry of available chunkers and provides
a factory for instantiating the appropriate chunker based on configuration.
"""

from typing import Dict, Type, Optional
import importlib

from .base import DocumentChunker
from .default import DefaultChunker
from ...logging_config import get_logger

logger = get_logger(__name__)


class ChunkerRegistry:
    """Registry for managing available document chunkers.
    
    The registry maps chunker names to chunker classes. It comes pre-loaded
    with the default chunker and can be extended with custom chunkers.
    
    Example:
        ```python
        from idiorag.rag.chunkers import get_chunker_registry
        from my_app.custom_chunker import MyChunker
        
        # Register custom chunker
        registry = get_chunker_registry()
        registry.register("my_chunker", MyChunker)
        
        # Use it
        chunker = registry.get_chunker("my_chunker")
        ```
    """
    
    def __init__(self):
        """Initialize registry with default chunker."""
        from typing import Callable, Union
        self._chunkers: Dict[str, Union[Type[DocumentChunker], Callable[[], DocumentChunker]]] = {
            "default": DefaultChunker,
        }
    
    def register(self, name: str, chunker_class: Type[DocumentChunker]) -> None:
        """Register a custom chunker.
        
        Args:
            name: Name to register the chunker under (e.g., "fishing_log")
            chunker_class: The chunker class or factory function that returns a DocumentChunker instance
            
        Raises:
            TypeError: If chunker_class doesn't extend DocumentChunker
        """
        from typing import Callable
        
        # Check if it's a class or callable
        if isinstance(chunker_class, type) and issubclass(chunker_class, DocumentChunker):
            # It's a class
            self._chunkers[name] = chunker_class
            logger.info(f"Registered chunker: {name} -> {chunker_class.__name__}")
        elif callable(chunker_class):
            # It's a factory function - validate by calling it
            try:
                instance = chunker_class()
                if not isinstance(instance, DocumentChunker):
                    raise TypeError(f"Factory function must return a DocumentChunker instance, got {type(instance)}")
                self._chunkers[name] = chunker_class
                logger.info(f"Registered chunker factory: {name}")
            except Exception as e:
                raise TypeError(f"Failed to validate factory function: {e}")
        else:
            raise TypeError(f"{chunker_class} must be a DocumentChunker class or a factory function")
    
    def register_from_path(self, name: str, class_path: str) -> None:
        """Register a chunker from a module path string.
        
        Args:
            name: Name to register the chunker under
            class_path: Full path to class (e.g., "my_app.chunkers.MyChunker")
            
        Raises:
            ImportError: If module or class cannot be imported
            TypeError: If class doesn't extend DocumentChunker
        """
        module_path, class_name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        chunker_class = getattr(module, class_name)
        self.register(name, chunker_class)
    
    def get_chunker(self, name: str = "default") -> DocumentChunker:
        """Get an instance of a registered chunker.
        
        Args:
            name: Name of the chunker to instantiate
            
        Returns:
            Instance of the requested chunker
            
        Raises:
            KeyError: If chunker name is not registered
        """
        if name not in self._chunkers:
            available = ", ".join(self._chunkers.keys())
            raise KeyError(
                f"Chunker '{name}' not found. Available chunkers: {available}"
            )
        
        chunker_class = self._chunkers[name]
        return chunker_class()
    
    def get_chunker_for_doc_type(self, doc_type: Optional[str], doc_type_mapping: Optional[Dict[str, str]] = None) -> DocumentChunker:
        """Get chunker based on document type mapping.
        
        Args:
            doc_type: The document type (e.g., "fishing_log", "article")
            doc_type_mapping: Optional mapping of doc_type -> chunker_name
            
        Returns:
            Instance of the appropriate chunker (defaults to "default" chunker)
        """
        if doc_type and doc_type_mapping and doc_type in doc_type_mapping:
            chunker_name = doc_type_mapping[doc_type]
            logger.info(f"Using chunker '{chunker_name}' for doc_type '{doc_type}'")
            return self.get_chunker(chunker_name)
        
        return self.get_chunker("default")
    
    def list_chunkers(self) -> Dict[str, str]:
        """List all registered chunkers.
        
        Returns:
            Dictionary mapping chunker names to class names
        """
        return {name: cls.__name__ for name, cls in self._chunkers.items()}


# Global registry instance
_chunker_registry: Optional[ChunkerRegistry] = None


def get_chunker_registry() -> ChunkerRegistry:
    """Get the global chunker registry instance.
    
    Returns:
        The global ChunkerRegistry instance
    """
    global _chunker_registry
    if _chunker_registry is None:
        _chunker_registry = ChunkerRegistry()
    return _chunker_registry


def register_chunker(name: str, chunker_class: Type[DocumentChunker]) -> None:
    """Convenience function to register a chunker globally.
    
    Args:
        name: Name to register under
        chunker_class: Chunker class extending DocumentChunker
    """
    registry = get_chunker_registry()
    registry.register(name, chunker_class)


def get_chunker(name: str = "default") -> DocumentChunker:
    """Convenience function to get a chunker instance.
    
    Args:
        name: Name of chunker to instantiate
        
    Returns:
        Chunker instance
    """
    registry = get_chunker_registry()
    return registry.get_chunker(name)
