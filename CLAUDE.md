# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

IdioRAG is an API-first Retrieval-Augmented Generation (RAG) framework built with FastAPI. It prioritizes user privacy through JWT-based authentication and strict per-user data isolation at the database level.

## Common Commands

```bash
# Run the server (with auto-reload)
python run.py

# Run tests
pytest tests/

# Verify setup (checks imports, config, JWT)
python tests/test_setup.py

# End-to-end API test
python examples/quickstart.py

# Linting and formatting
black src/
ruff check src/
mypy src/
```

## Architecture

### User Isolation Model
Every request requires a JWT token. The `user_id` from JWT is enforced on all database queries and vector store operations. Documents and vectors are filtered by user_id to ensure complete data isolation.

### Key Components

**Entry Points:**
- `src/idiorag/main.py` - FastAPI app with lifespan management
- `run.py` - Application runner (uvicorn with auto-reload)

**API Layer (`src/idiorag/api/endpoints/`):**
- `documents.py` - Document CRUD with automatic deduplication (creates/updates based on source hash)
- `query.py` - RAG queries including streaming via Server-Sent Events

**RAG Pipeline (`src/idiorag/rag/`):**
- `__init__.py` - Core pipeline: embed → vector search (user-filtered) → LLM → response
- `chunkers/` - Pluggable chunking system with registry pattern

**Infrastructure:**
- `auth.py` - JWT validation and UserContext extraction (supports HS256/RS256)
- `database.py` - SQLAlchemy async models with asyncpg
- `config.py` - Pydantic settings from environment variables

### Pluggable Chunking System

Custom chunkers extend `DocumentChunker` base class:

```python
from src.idiorag.rag.chunkers.base import DocumentChunker
from src.idiorag.rag.chunkers import register_chunker

class MyChunker(DocumentChunker):
    def chunk_document(self, document, user_id: str) -> list:
        nodes = [...]  # Create TextNodes
        self.validate_nodes(nodes, user_id, document.id)  # Required validation
        return nodes

register_chunker("my_chunker", MyChunker)
```

TextNode metadata must include: `user_id`, `document_id`, and `ref_doc_id` (matching document_id).

### Document Deduplication

Documents are deduplicated by source field. On POST:
- New source → `action="created"` (201)
- Same source, different content → `action="updated"` (200)
- Same source, same content → `action="unchanged"` (200)

## API Endpoints

All endpoints except `/health` require `Authorization: Bearer {JWT}`.

- `POST /api/v1/documents` - Create/update document
- `GET /api/v1/documents` - List documents (paginated)
- `DELETE /api/v1/documents/{id}` - Delete document and vectors
- `POST /api/v1/query` - RAG query
- `POST /api/v1/query/chat` - Streaming RAG query (SSE)

Query options: `top_k`, `max_tokens`, `temperature`, `use_cot` (chain-of-thought)

## Configuration

Key environment variables (see `.env.example`):

```
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
LLM_API_URL=https://your-llm-endpoint/v1
LLM_MODEL_NAME=qwen3-14b
JWT_SECRET_KEY=your-secret
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
```

## Development Notes

- Async-first: All database and RAG operations use async/await
- Global state: Embedding model, LLM, and vector store are lazy-initialized singletons
- Test tokens: Use `generate_test_token(user_id, email)` from `src/idiorag/utils.py`
- API docs available at http://localhost:8000/docs when running

## Reference Implementation

The `examples/fishing/` directory contains a complete domain-specific chunker example (FishingLogChunker) demonstrating rich metadata extraction and multiple chunking modes.
