# Data Transformation Strategy: Fishing App DB → IdioRAG Vectors

## Overview

You have fishing log data in relational tables (`logs`, `logEvents`, `WeatherData`, etc.) that needs to be transformed into vector embeddings for RAG. This document outlines the recommended approach.

## Two Approaches: API vs Direct DB Access

### Option 1: API-Based (Recommended for Initial Phase)

**How it works:**
1. Your fishing app reads from its database
2. Constructs JSON documents
3. Sends to IdioRAG via REST API
4. IdioRAG handles chunking, embedding, and vector storage

**Pros:**
- ✅ Clean separation of concerns
- ✅ IdioRAG doesn't need access to your main database
- ✅ Easy to test and debug
- ✅ Flexible - can transform data however you want before sending
- ✅ Works across different environments

**Cons:**
- ⚠️ Requires API calls (but can be batched)
- ⚠️ Need to write transformation logic in your fishing app

**Recommended for:** Initial development and MVP

### Option 2: Direct DB Access (For Advanced Phase)

**How it works:**
1. IdioRAG connects to your fishing app database (read-only)
2. Queries tables directly using SQL
3. Transforms rows into documents internally
4. Generates embeddings and stores in vector DB

**Pros:**
- ✅ Automatic sync - can run on schedule
- ✅ No API overhead
- ✅ Can do bulk operations efficiently

**Cons:**
- ⚠️ Tight coupling between apps
- ⚠️ IdioRAG needs read access to your DB
- ⚠️ More complex to set up and maintain
- ⚠️ Harder to debug

**Recommended for:** Production optimization after MVP proves successful

## Recommended Implementation: Hybrid Approach

**Phase 1: API-Based Manual Sync**
- Start with API-based approach
- Manually trigger sync when needed
- Perfect for development and testing

**Phase 2: Scheduled Sync Service**
- Create a background service that runs periodically
- Reads from your DB, sends to IdioRAG API
- Best of both worlds

**Phase 3: Real-Time Integration**
- Hook into your fishing app's create/update events
- Automatically sync to IdioRAG when logs are created/modified

## Data Transformation Pipeline

### Starting Simple (Your Request)

```
Fishing App DB:
┌─────────────────────────┐
│ logs table              │
│ - id                    │
│ - user_id               │
│ - date                  │
│ - body_of_water         │
│ - comments              │
└─────────────────────────┘
            ↓
    Transform to JSON
            ↓
{
  "title": "Fishing Log - Lake Michigan - 2024-01-15",
  "content": "Date: January 15, 2024\nLocation: Lake Michigan\nComments: Great day, caught several bass...",
  "doc_type": "fishing_log",
  "metadata": {
    "log_id": "log_123",
    "date": "2024-01-15",
    "body_of_water": "Lake Michigan",
    "user_id": "user_456"
  }
}
            ↓
    POST to IdioRAG API
            ↓
    IdioRAG processes:
    - Chunks the content
    - Generates embeddings
    - Stores in vector DB
```

### Expanding Gradually

As you add more details:

```
┌─────────────────────────┐
│ logs                    │
│ - id, user_id, date     │
│ - body_of_water         │
│ - comments              │
└─────────────────────────┘
            ↓
┌─────────────────────────┐
│ logEvents               │
│ - log_id                │
│ - event_type            │
│ - species, lure, etc.   │
└─────────────────────────┘
            ↓
┌─────────────────────────┐
│ WeatherData             │
│ - log_id                │
│ - temperature, wind     │
└─────────────────────────┘
            ↓
    Join tables + Transform
            ↓
More detailed document with all events and weather
```

## Implementation Code Examples

### Option 1: API-Based Transform (Python in Your Fishing App)

```python
import requests
import psycopg2
from datetime import datetime

def sync_log_to_idiorag(log_id: int, idiorag_url: str, jwt_token: str):
    """Sync a single fishing log to IdioRAG."""
    
    # 1. Read from your database
    conn = psycopg2.connect(
        host="localhost",
        database="atbnet",
        user="postgres",
        password="123qwe"
    )
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, user_id, date, body_of_water, comments
        FROM logs
        WHERE id = %s
    """, (log_id,))
    
    row = cursor.fetchone()
    if not row:
        return
    
    log_id, user_id, date, body_of_water, comments = row
    
    # 2. Transform to IdioRAG format
    document = {
        "title": f"Fishing Log - {body_of_water} - {date}",
        "content": f"""
Date: {date}
Location: {body_of_water}

Comments:
{comments or 'No comments'}
        """.strip(),
        "doc_type": "fishing_log",
        "metadata": {
            "log_id": str(log_id),
            "date": date.isoformat() if isinstance(date, datetime) else str(date),
            "body_of_water": body_of_water,
        },
        "source": "fishing_app_sync"
    }
    
    # 3. Send to IdioRAG
    response = requests.post(
        f"{idiorag_url}/api/v1/documents",
        headers={
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        },
        json=document
    )
    
    if response.status_code == 201:
        print(f"✅ Synced log {log_id} to IdioRAG")
        return response.json()
    else:
        print(f"❌ Failed to sync log {log_id}: {response.text}")
        return None
    
    cursor.close()
    conn.close()

# Usage
sync_log_to_idiorag(
    log_id=123,
    idiorag_url="http://localhost:8000",
    jwt_token="your-jwt-token"
)
```

### Batch Sync All Logs

```python
def sync_all_logs(idiorag_url: str, jwt_token: str, batch_size: int = 100):
    """Sync all fishing logs to IdioRAG in batches."""
    
    conn = psycopg2.connect(
        host="localhost",
        database="atbnet",
        user="postgres",
        password="123qwe"
    )
    cursor = conn.cursor()
    
    # Count total logs
    cursor.execute("SELECT COUNT(*) FROM logs")
    total = cursor.fetchone()[0]
    print(f"Syncing {total} logs...")
    
    # Process in batches
    offset = 0
    synced = 0
    failed = 0
    
    while offset < total:
        cursor.execute("""
            SELECT id, user_id, date, body_of_water, comments
            FROM logs
            ORDER BY id
            LIMIT %s OFFSET %s
        """, (batch_size, offset))
        
        rows = cursor.fetchall()
        
        for row in rows:
            log_id, user_id, date, body_of_water, comments = row
            
            # Generate user's JWT token
            user_token = generate_jwt_for_user(user_id)
            
            # Transform and send
            result = sync_log_to_idiorag(log_id, idiorag_url, user_token)
            if result:
                synced += 1
            else:
                failed += 1
        
        offset += batch_size
        print(f"Progress: {offset}/{total} ({synced} synced, {failed} failed)")
    
    cursor.close()
    conn.close()
    
    print(f"\n✅ Sync complete: {synced} succeeded, {failed} failed")
```

### Option 2: Scheduled Sync Service

Create a separate service that runs periodically:

```python
# sync_service.py
import schedule
import time

def sync_job():
    """Run sync job."""
    print(f"Starting sync job at {datetime.now()}")
    sync_all_logs(
        idiorag_url="http://localhost:8000",
        jwt_token="service-account-token"
    )

# Run every hour
schedule.every(1).hours.do(sync_job)

# Or run daily at 2 AM
schedule.every().day.at("02:00").do(sync_job)

print("Sync service started...")
while True:
    schedule.run_pending()
    time.sleep(60)
```

## Recommended Steps

### Step 1: Manual Testing (This Week)
1. Install pgvector (see PGVECTOR_SETUP.md)
2. Create a `.env` file with your settings
3. Start IdioRAG: `python run.py`
4. Manually create a test document via API
5. Test query functionality

### Step 2: Simple Transform (Next Week)
1. Write a Python script in your fishing app to read one log
2. Transform to JSON format
3. POST to IdioRAG API
4. Verify it appears in vector DB
5. Test querying for that log

### Step 3: Batch Sync (Week After)
1. Expand script to sync multiple logs
2. Add error handling and logging
3. Test with 10-20 logs
4. Validate query quality

### Step 4: Production Integration (Later)
1. Create scheduled sync service
2. Add incremental sync (only new/updated logs)
3. Add monitoring and alerts
4. Consider real-time hooks

## Database Schema Evolution

Start simple, expand gradually:

**Week 1: Basic**
```sql
-- Just read from logs table
SELECT id, user_id, date, body_of_water, comments
FROM logs
```

**Week 2: Add Events**
```sql
-- Join with logEvents
SELECT l.*, 
       json_agg(e.*) as events
FROM logs l
LEFT JOIN logEvents e ON e.log_id = l.id
GROUP BY l.id
```

**Week 3: Add Weather**
```sql
-- Join with weather data
SELECT l.*, 
       json_agg(e.*) as events,
       json_agg(w.*) as weather
FROM logs l
LEFT JOIN logEvents e ON e.log_id = l.id
LEFT JOIN WeatherData w ON w.log_id = l.id
GROUP BY l.id
```

## Monitoring Sync Quality

Track these metrics:
- Number of documents synced
- Sync success/failure rate
- Query relevance (user feedback)
- Embedding generation time
- Storage growth

## Best Practices

1. **Incremental Sync**: Track last_synced timestamp, only sync new/updated logs
2. **Error Handling**: Log failures, retry failed syncs
3. **Rate Limiting**: Don't overwhelm IdioRAG with thousands of requests at once
4. **Batch Operations**: Group requests when possible
5. **User Isolation**: Always use the correct user's JWT token
6. **Validation**: Verify data before sending to IdioRAG

## My Recommendation

**Start with Option 1 (API-Based)**:
1. Write a simple Python script in your fishing app
2. Read one log from your database
3. Transform to JSON
4. POST to IdioRAG
5. Verify and iterate

This gives you:
- Quick feedback loop
- Easy debugging
- Flexibility to change format
- Clear understanding of the process

Once this works well, we can optimize with batch operations and scheduling.
