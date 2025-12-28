#!/usr/bin/env python3
"""Run the IdioRAG application."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "idiorag.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="info",
    )
