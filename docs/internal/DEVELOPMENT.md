# Development Guide

This guide covers developer-specific workflows, testing, and debugging. For initial setup, see [README.md](README.md).

## Quick Start for Developers

After completing the setup in [README.md](README.md), you'll have:
- Virtual environment with dependencies installed
- Database with pgvector extension
- `.env` file configured
- Application running at http://localhost:8000

## Testing the API

### Generate Test Token

For local testing without an external auth system:

```bash
python -c "from src.idiorag.utils import generate_test_token; print(generate_test_token())"
```

This generates a JWT with `user_id=test_user_123` valid for 24 hours.

### API Testing with curl

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Create Document
```bash
TOKEN="YOUR_JWT_TOKEN"

curl -X POST "http://localhost:8000/api/v1/documents" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Detroit River - June 15 2024",
    "content": "{\"session\": {...}, \"events\": [...]}",
    "chunker": "fishing_log",
    "metadata": {"session_date": "2024-06-15"}
  }'
```

#### Query (Standard)
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What lures work best for bass?",
    "top_k": 5,
    "use_cot": true
  }'
```

#### Query (Streaming)
```bash
curl -X POST "http://localhost:8000/api/v1/query/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What lures work best for bass?",
    "use_cot": true
  }'
```

#### List Documents
```bash
curl -X GET "http://localhost:8000/api/v1/documents" \
  -H "Authorization: Bearer $TOKEN"
```

#### Delete Document
```bash
curl -X DELETE "http://localhost:8000/api/v1/documents/DOCUMENT_ID" \
  -H "Authorization: Bearer $TOKEN"
```

### End-to-End Testing Script

Use the built-in test script:

```bash
python quickstart.py
```

This tests the complete workflow: document upload → indexing → querying.

## Code Quality Tools

### Formatting

```bash
# Format all code with Black
black src/

# Check formatting without making changes
black --check src/
```

### Linting

```bash
# Lint with Ruff
ruff check src/

# Auto-fix issues
ruff check --fix src/
```

### Type Checking

```bash
# Type check with mypy (optional)
mypy src/
```

## Testing Custom Chunkers

### Test FishingLogChunker

```bash
python examples/fishing/test_chunker.py
```

This shows how documents are chunked with different modes (hybrid/event_only/session_only).

### Create Your Own Chunker

1. Implement `DocumentChunker` interface (see [docs/internal/CUSTOM_CHUNKING.md](docs/internal/CUSTOM_CHUNKING.md))
2. Register in [src/idiorag/main.py](src/idiorag/main.py) startup
3. Test with sample data
4. Iterate on chunking strategy based on query quality

## Debugging

### Enable Debug Logging

In `.env`:
```env
LOG_LEVEL=DEBUG
```

### Check Database Content

```sql
-- View documents
SELECT id, title, user_id, created_at FROM documents ORDER BY created_at DESC;

-- View vector store (requires pgvector)
SELECT COUNT(*) FROM data_llamaindex_vector_store;
```

### Inspect JWT Token

```bash
python -c "from src.idiorag.utils import decode_token; print(decode_token('YOUR_TOKEN'))"
```

### Test Embedding Model

```bash
python -c "
from src.idiorag.rag import get_embedding_model
model = get_embedding_model()
embeddings = model.get_text_embedding('test')
print(f'Embedding dimension: {len(embeddings)}')
"
```

## Troubleshooting

### Database Connection Issues

**Symptom**: `Cannot connect to database` errors

**Solutions**:
- Verify PostgreSQL is running: `pg_isready`
- Check DATABASE_URL credentials in `.env`
- Test connection: `psql $DATABASE_URL`
- Ensure pgvector extension: `CREATE EXTENSION IF NOT EXISTS vector;`

### LLM Connection Issues

**Symptom**: Query endpoint times out or returns errors

**Solutions**:
- Verify LLM_API_URL is accessible: `curl $LLM_API_URL/v1/models`
- Check LLM_API_KEY if required
- Test with simple completion:
  ```bash
  curl -X POST "$LLM_API_URL/v1/completions" \
    -H "Content-Type: application/json" \
    -d '{"model": "qwen3-14b", "prompt": "test", "max_tokens": 10}'
  ```
- Increase timeout in query endpoint if needed

### Embedding Model Download Fails

**Symptom**: First run fails downloading `BAAI/bge-small-en-v1.5`

**Solutions**:
- Check internet connection
- Verify disk space (~100MB needed)
- Try manual download:
  ```bash
  python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"
  ```
- Use alternative model in `.env`: `EMBEDDING_MODEL_NAME=other-model`

### JWT Authentication Fails

**Symptom**: `401 Unauthorized` or `Invalid token` errors

**Solutions**:
- Verify JWT_SECRET_KEY matches your auth system
- Check JWT_ALGORITHM (HS256 vs RS256)
- Decode token to inspect claims: `decode_token(token)`
- Ensure token includes user_id field (or sub, userId, id)
- Check token expiration

### Vector Search Returns No Results

**Symptom**: Query succeeds but no relevant documents found

**Solutions**:
- Verify documents are indexed: Check database `documents` table
- Confirm user_id isolation: Ensure JWT user_id matches document user_id
- Test embedding similarity:
  ```python
  from src.idiorag.rag import get_embedding_model
  model = get_embedding_model()
  query_emb = model.get_text_embedding("your query")
  doc_emb = model.get_text_embedding("your document")
  # Check similarity
  ```
- Try increasing `top_k` parameter
- Check chunking output with test scripts

## Development Workflow

1. **Make changes** to source code
2. **Format code**: `black src/`
3. **Lint**: `ruff check src/`
4. **Test locally**: `python examples/quickstart.py`
5. **Commit changes**
6. **Submit PR**

## Contributing

- Follow existing code style (Black formatting, Ruff linting)
- Add tests for new features (when test suite is ready)
- Update documentation for API changes
- Test with real data before submitting

## Support

- **Issues**: [GitHub Issues](https://github.com/pedjoni/idiorag/issues)
- **Discussions**: [GitHub Discussions](https://github.com/pedjoni/idiorag/discussions)
- **Docs**: Check [docs/internal/](docs/internal/) for implementation details