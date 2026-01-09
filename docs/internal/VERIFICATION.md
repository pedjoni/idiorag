# Phase 1 Verification Checklist

Follow these steps to verify your IdioRAG installation and setup.

## Prerequisites Checklist

- [ ] Python 3.11+ installed
- [ ] PostgreSQL running locally
- [ ] Git repository cloned
- [ ] Virtual environment created

## Step-by-Step Verification

### 1. Environment Setup ✓

```bash
# Navigate to project
cd idiorag

# Activate virtual environment
# If using uv:
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\Activate.ps1  # Windows PowerShell

# If using traditional venv:
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Verify Python version
python --version
# Should show: Python 3.11.x or higher
```

### 2. Install Dependencies ✓

```bash
# Install all dependencies
# With uv (recommended):
uv sync

# Or with pip:
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
uv pip list | grep fastapi  # or: pip list | grep fastapi
uv pip list | grep llama-index
uv pip list | grep sqlalchemy
```

**Expected output:** Should see all packages installed without errors

### 3. Configure Environment ✓

```bash
# Copy example config
cp .env.example .env

# Edit .env with your settings
# Minimum required:
# - DATABASE_URL=postgresql+asyncpg://postgres:123qwe@localhost:5432/idiorag
# - DATABASE_SCHEMA=public
# - LLM_API_URL=https://yyc-130-250-171-122.cloud.denvrdata.com/v1
# - LLM_API_KEY=your-token-here
# - JWT_SECRET_KEY=your-secret-key-here
```

**Action:** Open `.env` and fill in your actual values

### 4. Install pgvector Extension ✓

```bash
# See PGVECTOR_SETUP.md for detailed instructions

# Quick check if already installed:
psql -h localhost -p 5433 -U postgres -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

**Expected output:** If not installed, follow PGVECTOR_SETUP.md

If not yet installed:
```bash
# On Ubuntu/WSL:
cd /tmp
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

# Then in PostgreSQL:
psql -U postgres -d atbnet
CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS idiorag;
\q
```

### 5. Run Setup Verification ✓

```bash
python tests/test_setup.py
```

**Expected output:**
```
=============================================================
IdioRAG Setup Verification
=============================================================

Testing imports...
✓ idiorag version: 0.1.0
✓ config module loaded
✓ auth module loaded
✓ database module loaded
✓ FastAPI app created

✅ All imports successful!

Testing configuration...
✓ App name: IdioRAG
✓ Environment: development
✓ API prefix: /api/v1
✓ Database URL configured: True
✓ LLM URL configured: True
✓ JWT secret configured: True

✅ Configuration test passed!

Testing JWT functionality...
✓ Token created: ...
✓ Token decoded, user_id: test_user_123

✅ JWT test passed!

=============================================================
Summary:
=============================================================
Imports              ✅ PASS
Configuration        ✅ PASS
JWT                  ✅ PASS

🎉 All tests passed! You're ready to run the application.
```

**If any tests fail:** Check error messages and verify:
- `.env` file exists and has required variables
- PostgreSQL is running and accessible
- Virtual environment is activated

### 6. Start the Application ✓

```bash
# Start the server
python run.py
```

**Expected output:**
```
INFO:     Will watch for changes in these directories: ['/path/to/idiorag']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Starting IdioRAG v0.1.0
INFO:     Environment: development
INFO:     Initializing database connections...
INFO:     Application startup complete.
```

**Common issues:**
- Port 8000 already in use: Change port in run.py or kill the process
- Database connection error: Verify DATABASE_URL in .env
- Import errors: Ensure virtual environment is activated

### 7. Verify API Endpoints ✓

Open a new terminal (keep the app running) and test:

```bash
# Test health check
curl http://localhost:8000/health

# Expected output:
# {"status":"healthy","app_name":"IdioRAG","version":"0.1.0","environment":"development"}

# Test root endpoint
curl http://localhost:8000/

# Expected output:
# {"app":"IdioRAG","version":"0.1.0","docs":"/docs","health":"/health"}
```

### 8. Check API Documentation ✓

Open your browser and visit:
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

**Expected:** You should see interactive API documentation with all endpoints

### 9. Test Authentication ✓

Generate a test JWT token:

```bash
python -c "from src.idiorag.utils import generate_test_token; print(generate_test_token())"
```

**Expected output:** A long JWT token string

Copy this token and test an authenticated endpoint:

```bash
# Replace YOUR_TOKEN with the token from above
curl -X GET http://localhost:8000/api/v1/documents \
  -H "Authorization: Bearer YOUR_TOKEN"

# Expected output:
# {"documents":[],"total":0}
```

### 10. Run End-to-End Test ✓

```bash
# In a new terminal (with app still running)
python quickstart.py

# Press Enter to continue
```

**Expected output:**
```
🧪 Testing IdioRAG API...
============================================================

1. Testing health check...
✅ Health check passed

2. Generating test JWT token...
✅ Test token generated

3. Creating a test document...
✅ Document created successfully
   Document ID: ...

4. Listing documents...
✅ Documents retrieved successfully
   Total documents: 1

5. Getting specific document...
✅ Document retrieved successfully

6. Testing query endpoint...
✅ Query endpoint responded

7. Deleting test document...
✅ Document deleted successfully

============================================================
✅ API testing completed!
```

### 11. Verify Database Tables ✓

Check that tables were created:

```bash
psql -h localhost -p 5433 -U postgres -d idiorag -c "\dt public.*"
```

**Expected output (Phase 1):**
```
           List of relations
 Schema |   Name    | Type  |  Owner
--------+-----------+-------+----------
 public | documents | table | postgres
```

**Note**: The `vector_embeddings` table will be created in Phase 2 when RAG indexing is implemented. For Phase 1 verification, only the `documents` table should exist.

### 12. Check Logs ✓

Review the application logs in the terminal where `python run.py` is running.

**Look for:**
- No ERROR messages
- Successful database connection
- API endpoints registered
- No warnings about missing dependencies

## Verification Results

| Check | Status | Notes |
|-------|--------|-------|
| Python 3.11+ | ⬜ |  |
| Dependencies installed | ⬜ |  |
| .env configured | ⬜ |  |
| pgvector installed | ⬜ |  |
| test_setup.py passes | ⬜ |  |
| Application starts | ⬜ |  |
| Health check works | ⬜ |  |
| API docs accessible | ⬜ |  |
| JWT auth works | ⬜ |  |
| quickstart.py passes | ⬜ |  |
| Database tables created | ⬜ |  |

## Next Steps After Verification

Once all checks pass:

1. **✅ Phase 1 Complete** - Foundation is solid
2. **📝 Review Documentation** - Read DATA_TRANSFORMATION.md
3. **🎣 Plan Fishing Log Sync** - Decide on transformation approach
4. **🚀 Start Phase 2** - Implement RAG query logic

## Troubleshooting

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -U postgres -d atbnet -c "SELECT version();"

# Check if database is running
sudo systemctl status postgresql  # Linux
# or
pg_ctl status  # Windows
```

### pgvector Not Found

```bash
# Verify pgvector is installed
psql -U postgres -d atbnet -c "SELECT * FROM pg_available_extensions WHERE name = 'vector';"

# If not available, reinstall following PGVECTOR_SETUP.md
```

### Import Errors

```bash
# Make sure virtual environment is activated
which python  # Should point to venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill the process or change port in run.py
```

## Getting Help

If verification fails:
1. Check error messages carefully
2. Review relevant documentation files
3. Verify all prerequisites are met
4. Check that .env file has correct values
5. Ensure PostgreSQL is running and accessible

## Success Criteria

✅ **Phase 1 is verified when:**
- All 12 verification steps pass
- `examples/quickstart.py` completes without errors
- You can view API docs at http://localhost:8000/docs
- `documents` table exists in the public schema (or your configured schema)
- No ERROR messages in application logs

**Note**: Vector embeddings and RAG query functionality will be implemented in Phase 2.

---

**Once verified, you're ready for Phase 2!** 🎉
