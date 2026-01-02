# Custom Chunking Guide

## Overview

IdioRAG supports **pluggable chunking strategies**, allowing you to customize how documents are split into chunks for retrieval. This is essential for structured data like logs, forms, legal documents, or any domain-specific content.

## Why Custom Chunking?

The default sentence-based chunking works well for general text, but fails for structured data:

**Default Chunking (Generic)**:
- Splits text every ~512 tokens
- May break semantic units
- Ignores document structure

**Custom Chunking (Domain-Specific)**:
- Respects data structure (events, sections, etc.)
- Preserves semantic completeness
- Enables better retrieval

## Architecture

```
┌─────────────────────────────────────┐
│   Document Upload API               │
│   - doc_type: "fishing_log"         │
│   - chunker: "event_level" (optional)│
└──────────────┬──────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│   Chunker Registry                   │
│   - Maps doc_type → chunker          │
│   - Falls back to "default"          │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│   Custom Chunker                     │
│   - Implements DocumentChunker       │
│   - Creates semantically-complete nodes│
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│   Vector Store (pgvector)            │
│   - Stores chunks with user_id       │
│   - Enables semantic search          │
└──────────────────────────────────────┘
```

## Creating a Custom Chunker

### Step 1: Define Your Chunker Class

```python
# my_app/chunkers/custom_chunker.py

from typing import List, Optional
from llama_index.core.schema import BaseNode, Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter
from idiorag.rag.chunkers.base import DocumentChunker


class MyCustomChunker(DocumentChunker):
    """Custom chunker for my specific data format."""
    
    def __init__(self):
        """Initialize with node parser for proper node creation."""
        # Use splitter with large chunk_size to avoid splitting
        self.splitter = SentenceSplitter(chunk_size=100000, chunk_overlap=0)
    
    def chunk_document(
        self,
        content: str,
        document_id: str,
        user_id: str,
        metadata: Optional[dict] = None,
    ) -> List[BaseNode]:
        """Split document according to custom logic."""
        import json
        
        # Parse your structured data
        data = json.loads(content)
        
        nodes = []
        
        # Example: Create one node per "event" in your data
        for i, event in enumerate(data.get("events", [])):
            # Format the chunk text
            chunk_text = self._format_event(event, data)
            
            # Build metadata
            node_metadata = {
                "document_id": document_id,
                "user_id": user_id,  # REQUIRED for isolation
                "event_type": event.get("type"),
                "event_index": i,
                **(metadata or {})
            }
            
            # Create document and use splitter to get node
            # This properly sets ref_doc_id through LlamaIndex's internal mechanisms
            doc = LlamaDocument(
                text=chunk_text,
                metadata=node_metadata,
                id_=document_id
            )
            
            # Get nodes from document (returns one node since chunk_size is large)
            doc_nodes = self.splitter.get_nodes_from_documents([doc])
            nodes.extend(doc_nodes)
        
        # Validate nodes meet IdioRAG requirements
        self.validate_nodes(nodes, user_id, document_id)
        
        return nodes
    
    def _format_event(self, event: dict, parent_data: dict) -> str:
        """Format event with context."""
        return f"""
Event Type: {event['type']}
Date: {parent_data['date']}
Details: {event['details']}
Context: {parent_data.get('context', 'N/A')}
        """.strip()
```

### Step 2: Register Your Chunker

#### Option A: In Application Startup

```python
# my_app/main.py or startup.py

from idiorag.rag.chunkers import register_chunker
from my_app.chunkers.custom_chunker import MyCustomChunker

# Register at application startup (uses class with default parameters)
register_chunker("my_custom", MyCustomChunker)

# Or with custom parameters using lambda:
# register_chunker("my_custom", lambda: MyCustomChunker(param1="value", param2=True))
```

#### Option B: Using Entry Points (Advanced)

```python
# setup.py or pyproject.toml
entry_points={
    'idiorag.chunkers': [
        'my_custom = my_app.chunkers.custom_chunker:MyCustomChunker',
    ]
}
```

### Step 3: Use Your Chunker

#### Method 1: Explicit Chunker Selection

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/documents",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "title": "My Document",
        "content": json.dumps(my_structured_data),
        "source": "my_doc_123",  # Unique identifier for deduplication
        "doc_type": "custom_type",
        "chunker": "my_custom"  # Explicitly specify chunker
    }
)
```

#### Method 2: Auto-Selection by doc_type (Future)

```python
# In .env or config
DOC_TYPE_CHUNKER_MAPPING={
    "fishing_log": "fishing_event",
    "medical_record": "section_based",
    "legal_doc": "paragraph_based"
}

# Then just specify doc_type
response = requests.post(
    "http://localhost:8000/api/v1/documents/",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "title": "My Document",
        "content": json.dumps(my_data),
        "doc_type": "fishing_log"  # Auto-uses fishing_event chunker
    }
)
```

## Best Practices

### 1. Semantic Completeness

Each chunk should be understandable in isolation:

```python
# ❌ BAD - Incomplete context
chunk = "Used green pumpkin senko. Caught 3 bass."

# ✅ GOOD - Complete context
chunk = """
Fishing Event - Lake Michigan - Jan 15, 2024, 8:30 AM
Weather: Sunny, 65°F
Lure: Green Pumpkin Senko
Result: Caught 3 largemouth bass (2.5 lbs avg)
Location: Weed edge, 8ft depth
"""
```

### 2. Rich Metadata

More metadata = better filtering and relevance:

```python
node.metadata = {
    # REQUIRED
    "document_id": document_id,
    "user_id": user_id,
    
    # RECOMMENDED
    "doc_type": "fishing_log",
    "created_date": "2024-01-15",
    
    # DOMAIN-SPECIFIC (enable filtering)
    "location": "Lake Michigan",
    "event_type": "catch",
    "species": "largemouth_bass",
    "lure_type": "senko",
    "time_of_day": "morning",
    "water_temp_f": 68,
}
```

### 3. Validation

Always validate your nodes:

```python
def chunk_document(self, content, document_id, user_id, metadata):
    nodes = [...]
    
    # This will raise ValueError if nodes are invalid
    self.validate_nodes(nodes, user_id, document_id)
    
    return nodes
```

### 4. Error Handling

Handle malformed data gracefully:

```python
def chunk_document(self, content, document_id, user_id, metadata):
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # Fall back to treating as plain text
        return self._chunk_as_plain_text(content, document_id, user_id, metadata)
    
    # ... custom logic
```

## Testing Your Chunker

```python
# test_my_chunker.py

from my_app.chunkers.custom_chunker import MyCustomChunker
import json

def test_chunker():
    chunker = MyCustomChunker()
    
    test_data = {
        "date": "2024-01-15",
        "events": [
            {"type": "catch", "details": "Bass on senko"},
            {"type": "follow", "details": "Pike on spoon"},
        ]
    }
    
    nodes = chunker.chunk_document(
        content=json.dumps(test_data),
        document_id="test_doc_123",
        user_id="test_user",
        metadata={"test": True}
    )
    
    # Verify
    assert len(nodes) == 2
    assert nodes[0].metadata["user_id"] == "test_user"
    assert nodes[0].ref_doc_id == "test_doc_123"
    assert "Bass on senko" in nodes[0].text
    
    print("✅ Chunker test passed!")

if __name__ == "__main__":
    test_chunker()
```

## Example: Event-Level Chunker

See `examples/fishing/` for a complete implementation that:
- Chunks fishing logs by event
- Creates summary + event nodes
- Extracts rich metadata
- Preserves full context in each chunk

## Troubleshooting

### Common Issues:

**"Chunker 'xyz' not found"**
- Solution: Register your chunker before use
- Check: `get_chunker_registry().list_chunkers()`

**"Node validation failed: missing user_id"**
- Solution: Ensure every node has `user_id` in metadata
- This is critical for user isolation

**"Poor retrieval quality"**
- Solution: Add more metadata fields
- Ensure chunks have complete context
- Test different chunking granularities

**"Memory issues with large documents"**
- Solution: Consider streaming chunking
- Limit chunk size appropriately

## Advanced Topics

### Dynamic Chunking

Adjust chunking based on content:

```python
def chunk_document(self, content, document_id, user_id, metadata):
    data = json.loads(content)
    
    # Use different strategies based on data size
    if len(data["events"]) > 100:
        return self._chunk_by_session(data, ...)
    else:
        return self._chunk_by_event(data, ...)
```

### Hierarchical Chunking

Create parent-child relationships:

```python
# Parent node (summary)
parent = TextNode(text=summary, metadata={...})

# Child nodes (details)
for detail in details:
    child = TextNode(text=detail, metadata={...})
    child.relationships[NodeRelationship.PARENT] = parent
```

### Hybrid Strategies

Combine multiple chunking approaches:

```python
def chunk_document(self, content, document_id, user_id, metadata):
    # Create both full-text and event-level chunks
    full_text_chunk = self._create_summary(...)
    event_chunks = self._create_event_chunks(...)
    
    return [full_text_chunk] + event_chunks
```

## Additional Resources

- [LlamaIndex Node Documentation](https://docs.llamaindex.ai/en/stable/module_guides/loading/documents_and_nodes/)
- [Base Chunker API](../src/idiorag/rag/chunkers/base.py)
- [Default Chunker Reference](../src/idiorag/rag/chunkers/default.py)

## Getting Help

- Open an issue on GitHub
- Check existing chunker implementations in `examples/`
- Review test cases for patterns
