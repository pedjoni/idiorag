# Development Setup Guide

## Prerequisites

1. **Python 3.11+**: Ensure you have Python 3.11 or higher installed
2. **PostgreSQL with pgvector**: You need a PostgreSQL instance with the pgvector extension
3. **External LLM API**: Access to an LLM endpoint (e.g., Qwen3-14B)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/pedjoni/idiorag.git
cd idiorag
```

### 2. Create virtual environment and install dependencies

We recommend using [uv](https://github.com/astral-sh/uv) for faster package management:

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv

# Activate it
source .venv/bin/activate  # Linux/macOS
# Or on Windows: .venv\Scripts\Activate.ps1

# Install dependencies
uv sync
```

### 3. Configure environment

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Database - Update with your PostgreSQL credentials
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/idiorag

# LLM - Update with your LLM endpoint
LLM_API_URL=https://your-llm-api.com/v1
LLM_MODEL_NAME=qwen3-14b
LLM_API_KEY=your-api-key-if-needed

# JWT - Update with your application's JWT secret
JWT_SECRET_KEY=your-application-secret-key
JWT_ALGORITHM=HS256
```

### 4. Set up the database

#### Install pgvector extension

Connect to your PostgreSQL database and run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

#### Run database migrations

The application will create tables automatically on first startup.

## Running the Application

### Development Server

Start the development server:

```bash
python run.py
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Testing the API

#### 1. Health Check

```bash
curl http://localhost:8000/health
```

#### 2. Create a Document (requires JWT token)

First, generate a test token:
```bash
python -c "from src.idiorag.utils import generate_test_token; print(generate_test_token())"
```

Then create a document:
```bash
curl -X POST "http://localhost:8000/api/v1/documents/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Document",
    "content": "This is the content of my document...",
    "doc_type": "text",
    "metadata": {"source": "manual_upload"}
  }'
```

#### 3. Query the RAG System

```bash
curl -X POST "http://localhost:8000/api/v1/query/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What information do you have?",
    "top_k": 5
  }'
```

## Development Workflow

### Project Structure

```
idiorag/
├── src/
│   └── idiorag/
│       ├── __init__.py
│       ├── main.py              # FastAPI application
│       ├── config.py            # Configuration management
│       ├── auth.py              # JWT authentication
│       ├── database.py          # Database models and session
│       ├── logging_config.py    # Logging setup
│       ├── api/
│       │   ├── __init__.py
│       │   └── endpoints/
│       │       ├── documents.py # Document CRUD endpoints
│       │       └── query.py     # RAG query endpoints
│       └── rag/
│           └── __init__.py      # LlamaIndex integration
├── tests/                       # Test files (coming soon)
├── .env.example                 # Environment template
├── requirements.txt             # Python dependencies
├── pyproject.toml              # Project metadata
└── run.py                      # Application runner
```

### Code Quality

```bash
# Format code with Black
black src/

# Lint with Ruff
Format and lint your code:

```bash
# Format code
black src/

# Lint
ruff check src/

# Type check
```bash
# Run tests (coming soon)
pytest
```
## JWT Token Configuration

### Getting JWT from Your Application

Your application needs JWT tokens for authentication. Configure based on your auth provider:

**HS256 (Symmetric - Shared Secret):**

```env
JWT_SECRET_KEY=your-shared-secret-key
JWT_ALGORITHM=HS256
```

**RS256 (Asymmetric - Public Key):**

```env
JWT_ALGORITHM=RS256
JWT_PUBLIC_KEY=-----BEGIN PUBLIC KEY-----
...your public key

## Next Steps

1. **Test Basic Functionality**: Start with health check and document creation
2. **Implement RAG Pipeline**: The core RAG functionality is scaffolded but needs completion
3. **Custom Chunking**: Implement domain-specific chunking strategies for your use case
4. **Testing**: Add comprehensive tests
5. **Production Setup**: Configure for production deployment

## Troubleshooting

### Database Connection Issues

- Verify PostgreSQL is running
- Check DATABASE_URL credentials
- Ensure pgvector extension is installed

###Test basic functionality with the health check endpoint
2. Create your first document via the API
3. Explore the interactive API docs at `/docs`
4. Implement custom RAG features for your use case

### LLM Connection Issues

- Verify LLM_API_URL is accessible
- Check API key if required
- Test with curl: `curl -X POST YOUR_LLM_API_URL/v1/completions`

## Support

For issues or questions:
- GitHub Issues: https://github.com/pedjoni/idiorag/issues
- Check logs in the terminal for detailed error messages
endpoint manually with curl, please open an issue on GitHub.