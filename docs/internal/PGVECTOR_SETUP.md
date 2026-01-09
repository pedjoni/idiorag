# PostgreSQL and pgvector Setup Guide

## 1. Install pgvector Extension

Since you're running PostgreSQL locally, you need to install the pgvector extension.

### On Ubuntu/WSL (Debian-based)

```bash
# Install PostgreSQL development files (if not already installed)
sudo apt update
sudo apt install postgresql-server-dev-all

# Clone and build pgvector
cd /tmp
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

### On Windows (if running PostgreSQL natively)

Download the pre-built binary from:
https://github.com/pgvector/pgvector/releases

Follow the installation instructions in the release.

## 2. Enable pgvector in Your Database

Connect to your PostgreSQL database:

```bash
psql -U postgres -d atbnet
```

Run these commands:

```sql
-- Create the vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT * FROM pg_extension WHERE extname = 'vector';

-- You should see output showing the vector extension is installed
```

## 3. Create IdioRAG Schema

To keep IdioRAG tables separate from your fishing app tables:

```sql
-- Create a separate schema for IdioRAG
CREATE SCHEMA IF NOT EXISTS idiorag;

-- Grant permissions (adjust as needed)
GRANT ALL ON SCHEMA idiorag TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA idiorag TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA idiorag GRANT ALL ON TABLES TO postgres;

-- Verify schema was created
\dn

-- Set search path to include idiorag schema
-- (Optional, or specify schema in table definitions)
```

## 4. Verify Setup

Test that everything works:

```sql
-- Test vector operations
SELECT '[1,2,3]'::vector;

-- Should return: [1,2,3]

-- Test vector similarity (cosine distance)
SELECT '[1,2,3]'::vector <=> '[4,5,6]'::vector;

-- Should return a numeric similarity score
```

## 5. IdioRAG Tables

The application will automatically create these tables in the `idiorag` schema:

1. **documents** - Stores document metadata
   - Indexed by user_id for fast user-specific queries
   
2. **vector_embeddings** (via pgvector) - Stores vector embeddings
   - Each vector includes user_id in metadata for isolation
   - Supports similarity search with user filtering

## Connection String

Your connection string is now configured as:
```
postgresql+asyncpg://postgres:123qwe@localhost:5432/atbnet
```

The application will use schema `idiorag` for all tables.

## Quick Verification

After setup, run this to test:

```bash
# In your IdioRAG directory
python test_setup.py
```

## Troubleshooting

### pgvector installation fails
- Make sure PostgreSQL development headers are installed
- Check PostgreSQL version compatibility (pgvector supports 11+)
- Try installing from package manager if available

### Permission errors
```sql
-- Grant all permissions to your user
GRANT ALL ON SCHEMA idiorag TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA idiorag TO postgres;
```

### Cannot connect to database
- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Check connection details in `.env` file
- Test connection: `psql -U postgres -d atbnet`

## Environment-Specific Databases

For testing/production, you can create separate databases:

```sql
-- Create testing database
CREATE DATABASE atbnet_test;
\c atbnet_test
CREATE EXTENSION vector;
CREATE SCHEMA idiorag;

-- Create production database (on production server)
CREATE DATABASE atbnet;
CREATE EXTENSION vector;
CREATE SCHEMA idiorag;
```

Then configure in `.env`:
```env
# Development
DATABASE_URL=postgresql+asyncpg://postgres:123qwe@localhost:5432/atbnet

# Testing (uncomment for test environment)
# DATABASE_URL=postgresql+asyncpg://postgres:123qwe@localhost:5432/atbnet_test

# Production (uncomment for production)
# DATABASE_URL=postgresql+asyncpg://user:pass@prod-host:5432/atbnet
```
