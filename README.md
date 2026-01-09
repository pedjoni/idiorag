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
*   **Streaming Responses**: Real-time token streaming with Server-Sent Events for responsive UX.
*   **Pluggable Chunking**: Extensible architecture for domain-specific document processing strategies.
*   **Chain-of-Thought**: Optional reasoning mode for more detailed, step-by-step answers.

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
python tests/test_setup.py

# Access the API
# - API: http://localhost:8000
# - Interactive docs: http://localhost:8000/docs
# - Health check: http://localhost:8000/health
```

## Architecture

### User Isolation

IdioRAG enforces strict user isolation at multiple levels:
- **JWT-based**: User ID extracted from JWT token on every request
- **Database-level**: All queries filtered by `user_id`
- **Vector store**: Metadata includes `user_id` for isolation
- **No cross-user access**: Users can only see/query their own data

### Data Flow

```
User Request (with JWT)
    ↓
JWT Middleware (extract user_id)
    ↓
API Endpoint
    ↓
┌─────────────────────┬──────────────────────┐
│   Document Upload   │    Query Request     │
└─────────────────────┴──────────────────────┘
         ↓                        ↓
    1. Store in DB         1. Embed query
    2. Create chunks       2. Search vectors (filtered by user_id)
    3. Generate embeddings 3. Retrieve context
    4. Store in vector DB  4. Send to LLM
    5. Return success      5. Return answer + context
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
│           ├── __init__.py      # LlamaIndex integration
│           └── chunkers/        # Pluggable chunking strategies
├── tests/
│   ├── test_setup.py            # Installation verification
│   └── test_streaming.py        # Streaming endpoint tests
├── examples/
│   ├── quickstart.py            # Quick start API demo
│   └── fishing/                 # FishingLogChunker reference implementation
├── docs/
│   └── internal/                # Internal documentation
├── .env.example                 # Environment template
├── requirements.txt             # Dependencies
├── pyproject.toml              # Project metadata (uv)
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
- `POST /api/v1/query` - Query with LLM-generated answers
  - Supports `use_cot` parameter for Chain-of-Thought reasoning
  - Returns answer with source documents and retrieval metadata
- `POST /api/v1/query/chat` - Streaming query with Server-Sent Events
  - Real-time token streaming
  - Same CoT support as `/query`
  - Includes retrieval metadata in initial context event

## Usage Example

```python
import requests

# Your JWT token from your application
token = "your-jwt-token"
headers = {"Authorization": f"Bearer {token}"}

# Upload a document with custom chunker
response = requests.post(
    "http://localhost:8000/api/v1/documents",
    headers=headers,
    json={
        "title": "Detroit River - June 15 2024",
        "content": '{"session": {...}, "location": {...}, "events": [...]}',  # Enriched JSON
        "source": "fishing_log_12345",  # Unique identifier for deduplication
        "chunker": "fishing_log",  # Uses FishingLogChunker
        "metadata": {"session_date": "2024-06-15"}
    }
)

# Query with response metadata
response = requests.post(
    "http://localhost:8000/api/v1/query",
    headers=headers,
    json={
        "query": "What lures work best for smallmouth bass in June?",
        "use_cot": False
    }
)
result = response.json()

# Access retrieval quality metadata
print(f"Total documents in index: {result['metadata']['total_documents_in_index']}")
print(f"Documents retrieved: {result['metadata']['documents_retrieved']}")
print(f"Avg relevance score: {result['metadata']['avg_relevance_score']}")

# Your app can use this to provide user feedback:
# - If total_documents_in_index < 10: "Add more logs for better insights"
# - If documents_retrieved == 0: "No matching logs found"
# - If avg_relevance_score < 0.7: "Low confidence answer"

# Query with streaming
import sseclient

response = requests.post(
    "http://localhost:8000/api/v1/query/chat",
    headers=headers,
    json={
        "query": "What lures work best for smallmouth bass in June?",
        "use_cot": True  # Enable Chain-of-Thought reasoning
    },
    stream=True
)

client = sseclient.SSEClient(response)
for event in client.events():
    # First event includes metadata
    if event.event == "context":
        data = json.loads(event.data)
        print(f"Retrieved {data['metadata']['documents_retrieved']} docs")
    print(event.data, end='', flush=True)
```

## Retrieval Metadata

Every query response includes metadata about retrieval quality to help client applications provide better user experience:

- **`total_documents_in_index`**: Total number of documents in the user's index
  - Use this to determine if the user has enough data for meaningful results
  - Example: Show "Add more documents" prompt if count is low
  
- **`documents_retrieved`**: Number of documents actually retrieved for this query
  - Indicates how many relevant matches were found
  - A value of 0 means no relevant context was found
  
- **`avg_relevance_score`**: Average similarity score of retrieved documents (0.0-1.0)
  - Higher scores indicate better matches
  - Use to show confidence levels or disclaimers for low-quality matches

This metadata empowers your application to make domain-specific decisions about when to prompt users for more data or when to display confidence warnings.

## Contributing

This is an early-stage project. The framework is designed to be:
- **Generic**: Usable for various RAG applications
- **Flexible**: Easy to customize chunking and retrieval
- **Private**: Strong user isolation by design

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/pedjoni/idiorag/issues)
- **Discussions**: [GitHub Discussions](https://github.com/pedjoni/idiorag/discussions)
