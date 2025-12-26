# IdioRAG 

**IdioRAG** (from the Greek *idios*, meaning "one's own") is an **API-first** Retrieval-Augmented Generation (RAG) framework built for **private, user-isolated queries**. 

IdioRAG is designed to function as a backend microservice. It treats privacy as a first-class citizen by ensuring that personal documents and queries are cryptographically tied to specific users through JWT authentication and database-level isolation.

## Core Features

*   **API-Only Architecture**: A headless service built with [FastAPI](fastapi.tiangolo.com) designed to be consumed by other applications—no built-in UI, just pure, documented endpoints.
*   **Identity-Centric Retrieval**: Strict user isolation ensures queries only retrieve context from the specific user's own document namespace.
*   **JWT-Based Authentication**: Seamlessly extracts user identity and permissions directly from JWT keys provided by upstream applications.
*   **LlamaIndex Orchestration**: Leverages [LlamaIndex](www.llamaindex.ai) for sophisticated data ingestion, indexing, and retrieval logic.
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
DATABASE_URL=postgresql://user:password@localhost:5432/idiorag
LLM_API_URL=https://your-external-llm-api/v1
LLM_MODEL_NAME=qwen3-14b
