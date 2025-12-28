# IdioRAG 

**IdioRAG** (from the Greek *idios*, meaning "one's own") is an **API-first** Retrieval-Augmented Generation (RAG) framework built for **private, user-isolated queries**. 

IdioRAG is designed to function as a backend microservice. It treats privacy as a first-class citizen by ensuring that personal documents and queries are tied to specific users through authentication and database-level isolation.

## Core Features

*   **API-Only Architecture**: A headless service built with [FastAPI](fastapi.tiangolo.com) designed to be consumed by other applications—no built-in UI, just pure, documented endpoints.
*   **Identity-Centric Retrieval**: Strict user isolation ensures queries only retrieve context from the specific user's own document namespace.
*   **JWT-Based Authentication**: Seamlessly extracts user identity and permissions directly from JWT keys provided by upstream applications.
*   **LlamaIndex Orchestration**: Leverages [LlamaIndex](www.llamaindex.ai) for data ingestion, indexing, and retrieval logic.
*   **Postgres + pgvector**: Scalable, reliable vector storage using [pgvector](github.com) for efficient similarity searches.
*   **LLM Agnostic**: Communicates with external LLMs (optimized for **Qwen3 14B** in 2025) via OpenAI-compatible APIs, allowing for easy model swapping.

## Tech Stack

- **API Framework:** [FastAPI](fastapi.tiangolo.com)
- **RAG Orchestrator:** [LlamaIndex](www.llamaindex.ai)
- **Database:** PostgreSQL with `pgvector`
- **Identity:** JWT (initial implementation) with extensibility for future methods.
- **LLM:** External Inference (Default: Qwen3-14B)
- **Language:** Python 3.11+

## Getting Started

### 1. Prerequisites
- A running PostgreSQL instance with the `pgvector` extension.
- Access to an external LLM endpoint.
- An upstream application providing valid JWTs for authentication.

### 2. Environment Setup
Create a `.env` file with your configuration:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/idiorag
LLM_API_URL=https://your-external-llm-api/v1
LLM_MODEL_NAME=qwen3-14b
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
```

See [.env.example](.env.example) for all configuration options.

### 3. Install Dependencies

```bash
# Using uv (recommended - faster and more reliable)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
uv sync

# Or traditional pip
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Run the Application

```bash
# Development server with auto-reload
python run.py

# Or using uvicorn directly
uvicorn src.idiorag.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Verify Setup

```bash
# Run setup verification tests
python test_setup.py

# Access the API
# - API: http://localhost:8000
# - Interactive docs: http://localhost:8000/docs
# - Health check: http://localhost:8000/health
```

## Documentation

- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Development setup guide
- **[Interactive API Docs](http://localhost:8000/docs)** - Full API documentation (when running)
- **[ReDoc](http://localhost:8000/redoc)** - Alternative API documentation

## Project Structure

```
idiorag/
├── src/
│   └── idiorag/
│       ├── main.py              # FastAPI application
│       ├── config.py            # Configuration management
│       ├── auth.py              # JWT authentication
│       ├── database.py          # Database models
│       ├── api/
│       │   └── endpoints/       # API endpoints
│       └── rag/
│           └── __init__.py      # LlamaIndex integration
├── .env.example                 # Environment template
├── requirements.txt             # Dependencies
├── DEVELOPMENT.md              # Development guide
└── run.py                      # Application runner
```

## API Endpoints

### Authentication
All endpoints except `/health` require JWT Bearer token authentication.

### Documents
- `POST /api/v1/documents` - Upload a document
- `GET /api/v1/documents` - List user's documents
- `GET /api/v1/documents/{id}` - Get document by ID
- `DELETE /api/v1/documents/{id}` - Delete a document

### Query
- `POST /api/v1/query` - Query the RAG system
- `POST /api/v1/query/chat` - Chat with streaming (coming soon)

## Usage Example

```python
import requests

# Your JWT token from your application
token = "your-jwt-token"
headers = {"Authorization": f"Bearer {token}"}

# Upload a document
response = requests.post(
    "http://localhost:8000/api/v1/documents",
    headers=headers,
    json={
        "title": "Lake Michigan - Bass Fishing",
        "content": "Caught 3 largemouth bass using green pumpkin senko in 8-10ft near weed edges. Morning bite was best between 8-10 AM.",
        "doc_type": "fishing_log",
        "metadata": {
            "location": "Lake Michigan",
            "date": "2025-01-15",
            "species": ["largemouth_bass"],
            "lures": ["senko"]
        }
    }
)

# Query the system
response = requests.post(
    "http://localhost:8000/api/v1/query",
    headers=headers,
    json={
        "query": "What lures work best for bass?",
        "top_k": 5
    }
)
```

## Contributing

This is an early-stage project. The framework is designed to be:
- **Generic**: Usable for various RAG applications
- **Flexible**: Easy to customize chunking and retrieval
- **Private**: Strong user isolation by design

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

## Roadmap

### Phase 1: Core Framework ✅
- [x] FastAPI application
- [x] JWT authentication
- [x] Database with user isolation
- [x] Basic CRUD endpoints
- [x] LlamaIndex integration scaffold

### Phase 2: RAG Implementation 🚧
- [ ] Complete vector store integration
- [ ] Implement query engine
- [ ] Add embedding generation
- [ ] Test end-to-end RAG pipeline

### Phase 3: Advanced Features 📋
- [ ] Implement custom chunking strategies
- [ ] Batch document upload endpoint
- [ ] Sync endpoint with upsert logic (avoid duplicates using source field)
- [ ] Advanced metadata extraction
- [ ] Query optimization for hierarchical data

### Phase 4: Production Ready 📋
- [ ] Comprehensive testing
- [ ] Performance optimization
- [ ] Production deployment guide
- [ ] Monitoring and logging
- [ ] Alembic migrations

## Support

- **Issues**: [GitHub Issues](https://github.com/pedjoni/idiorag/issues)
- **Discussions**: [GitHub Discussions](https://github.com/pedjoni/idiorag/discussions)
