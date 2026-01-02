# IdioRAG Quick Reference

## 🚀 Quick Start (5 minutes)

```bash
# 1. Clone and setup
git clone https://github.com/pedjoni/idiorag.git
cd idiorag

# Setup with uv (recommended)
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
uv sync

# Or with pip
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edit .env with your settings

# 4. Verify
python test_setup.py

# 5. Run
python run.py

# 6. Test (in another terminal)
python quickstart.py
```

## 📁 File Structure

```
idiorag/
├── 📄 README.md              ← Start here
├── 📄 DEVELOPMENT.md         ← Full dev guide
├── 📄 FISHING_LOGS.md        ← Chunking strategies
├── 📄 IMPLEMENTATION.md      ← Architecture details
├── 📄 QUICK_REFERENCE.md     ← This file
│
├── 🔧 .env.example           ← Config template
├── 🔧 requirements.txt       ← Dependencies
├── 🔧 pyproject.toml         ← Project metadata
│
├── 🏃 run.py                 ← Start the app
├── tests/
│   ├── test_setup.py        ← Verify setup
│   └── test_streaming.py    ← Test streaming
├── examples/
│   ├── quickstart.py        ← API demo
│   └── fishing/             ← Custom chunker example
│
└── src/idiorag/
    ├── main.py               ← FastAPI app
    ├── config.py             ← Settings
    ├── auth.py               ← JWT auth
    ├── database.py           ← DB models
    ├── utils.py              ← Helpers
    ├── api/
    │   └── endpoints/
    │       ├── documents.py  ← Document CRUD
    │       └── query.py      ← RAG queries
    └── rag/
        └── __init__.py       ← LlamaIndex
```

## 🔑 Environment Variables (Required)

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/idiorag

# LLM
LLM_API_URL=https://your-llm-api.com/v1
LLM_MODEL_NAME=qwen3-14b

# JWT (from your fishing app)
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
```

## 🌐 API Endpoints

### Public
- `GET /` - API info
- `GET /health` - Health check
- `GET /docs` - Interactive API docs

### Protected (require JWT Bearer token)
- `POST /api/v1/documents` - Upload document
- `GET /api/v1/documents` - List user's documents
- `GET /api/v1/documents/{id}` - Get document
- `DELETE /api/v1/documents/{id}` - Delete document
- `POST /api/v1/query` - Query RAG system
- `POST /api/v1/query/chat` - Chat with streaming

## 🔐 Authentication

All protected endpoints require JWT Bearer token:

```bash
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "content": "...", "source": "test_doc_1"}'
```

Generate test token:
```python
from idiorag.utils import generate_test_token
token = generate_test_token()
print(token)
```

## 📦 Key Dependencies

- **FastAPI** - Web framework
- **SQLAlchemy** - Database ORM (async)
- **asyncpg** - PostgreSQL driver
- **pgvector** - Vector storage
- **LlamaIndex** - RAG orchestration
- **python-jose** - JWT handling
- **pydantic** - Data validation

## 🗄️ Database Setup

```sql
-- Create database
CREATE DATABASE idiorag;

-- Install extension
\c idiorag
CREATE EXTENSION vector;
```

## 🧪 Testing

```bash
# Verify setup
python tests/test_setup.py

# Test API (requires app running)
python quickstart.py

# Future: pytest
pytest tests/
```

## 📝 Example Usage

### Python Client

```python
import requests

BASE_URL = "http://localhost:8000"
TOKEN = "your-jwt-token"
headers = {"Authorization": f"Bearer {TOKEN}"}

# Upload document
response = requests.post(
    f"{BASE_URL}/api/v1/documents",
    headers=headers,
    json={
        "title": "Fishing Trip",
        "content": "Caught bass with senko...",
        "doc_type": "fishing_log",
        "metadata": {"location": "Lake Michigan"}
    }
)
doc_id = response.json()["id"]

# Query
response = requests.post(
    f"{BASE_URL}/api/v1/query",
    headers=headers,
    json={
        "query": "What lures work for bass?",
        "top_k": 5
    }
)
answer = response.json()["answer"]
```

### cURL

```bash
# Health check
curl http://localhost:8000/health

# Upload document
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Fishing Trip",
    "content": "Caught 3 bass...",
    "source": "fishing_log_123",
    "doc_type": "fishing_log"
  }'

# Query
curl -X POST http://localhost:8000/api/v1/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Best lures for bass?",
    "top_k": 5
  }'
```

## 🎣 Fishing Log Format

```json
{
  "title": "Lake Michigan - Jan 15, 2024",
  "content": "Fishing Log: January 15, 2024\nLocation: Lake Michigan...",
  "doc_type": "fishing_log",
  "metadata": {
    "log_id": "log_123",
    "date": "2024-01-15",
    "location": "Lake Michigan",
    "weather_temp": 65,
    "species": ["largemouth_bass"],
    "lure_types": ["senko", "chatterbait"],
    "event_count": 3
  }
}
```

See [FISHING_LOGS.md](FISHING_LOGS.md) for chunking strategies.

## 🐛 Troubleshooting

### App won't start
- Check `.env` file exists and has required variables
- Verify PostgreSQL is running and accessible
- Check `python tests/test_setup.py` for errors

### Database connection fails
- Verify DATABASE_URL format: `postgresql+asyncpg://...`
- Check PostgreSQL is running: `psql -h localhost -U user`
- Ensure database exists: `CREATE DATABASE idiorag;`

### JWT authentication fails
- Verify JWT_SECRET_KEY matches your fishing app
- Check token format with: `python -c "from idiorag.utils import decode_test_token; print(decode_test_token('YOUR_TOKEN'))"`
- Test with generated token: `python -c "from idiorag.utils import generate_test_token; print(generate_test_token())"`

### Import errors
- Ensure virtual environment is activated
- Reinstall: `pip install -r requirements.txt`
- Check Python version: `python --version` (need 3.11+)

## 📚 Documentation Links

- **README.md** - Project overview
- **DEVELOPMENT.md** - Detailed setup and development workflow
- **FISHING_LOGS.md** - Chunking strategies for fishing logs
- **IMPLEMENTATION.md** - Architecture and design decisions
- **API Docs** - http://localhost:8000/docs (when running)

## 🔧 Common Configuration

### HS256 JWT (symmetric)
```env
JWT_SECRET_KEY=your-shared-secret
JWT_ALGORITHM=HS256
```

### RS256 JWT (asymmetric)
```env
JWT_ALGORITHM=RS256
JWT_PUBLIC_KEY=-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A...
-----END PUBLIC KEY-----
```

### LLM Configuration
```env
LLM_API_URL=http://localhost:8080/v1
LLM_MODEL_NAME=qwen3-14b
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048
```

### Embedding Configuration
```env
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
EMBEDDING_DIMENSION=384
CHUNK_SIZE=512
CHUNK_OVERLAP=50
```

## 🚦 Status Checks

```python
# Health check
import requests
requests.get("http://localhost:8000/health").json()

# Test auth
from idiorag.utils import generate_test_token
token = generate_test_token()

# Test database
from idiorag.database import init_db
import asyncio
asyncio.run(init_db())
```

## 💡 Pro Tips

1. **Development**: Use `python run.py` for auto-reload
2. **Testing**: Generate tokens with `idiorag.utils.generate_test_token()`
3. **Debugging**: Check logs in terminal, set `LOG_LEVEL=DEBUG`
4. **API Docs**: Use http://localhost:8000/docs for interactive testing
5. **JWT Claims**: User ID can be in `sub`, `user_id`, `userId`, or `id` claim

## 🎯 Next Steps

1. ✅ Setup complete - You are here!
2. 🚧 Implement RAG query logic
3. 📋 Create fishing log chunking
4. 📋 Add comprehensive tests
5. 📋 Deploy to production

## 📞 Support

- **GitHub Issues**: https://github.com/pedjoni/idiorag/issues
- **Documentation**: See DEVELOPMENT.md for details
- **API Reference**: http://localhost:8000/docs

---

**Last Updated**: December 26, 2025  
**Version**: 0.1.0  
**Status**: Foundation Complete ✅
