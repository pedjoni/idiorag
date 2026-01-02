# Using the Fishing Log Chunker

This guide shows how to use the `FishingLogChunker` with IdioRAG.

## Quick Start

### 1. Register the Chunker

In your application startup (e.g., [main.py](../../src/idiorag/main.py)):

```python
from idiorag.rag.chunkers import register_chunker
from examples.fishing.fishing_chunker import FishingLogChunker

# Register with default parameters (hybrid mode, include_weather=True)
register_chunker("fishing_log", FishingLogChunker)

# Or register with custom configuration using lambda
register_chunker(
    "fishing_log_events_only",
    lambda: FishingLogChunker(mode="event_only", include_weather=False)
)
```

### 2. Upload Documents

Send enriched fishing logs to the `/documents` endpoint:

```bash
curl -X POST "http://localhost:8000/documents" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Detroit River - June 15 2024",
    "content": "{\"session\": {...}, \"location\": {...}, \"events\": [...]}",
    "chunker": "fishing_log"
  }'
```

### 3. Query the System

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What lures work best for smallmouth bass on Detroit River in June?"
  }'
```

## Chunking Modes

### Hybrid Mode (Recommended)

Creates both session summary and event-level chunks:

```python
FishingLogChunker(mode="hybrid")
```

**Use when:**
- Users ask both high-level ("What were my best sessions?") and detail-level ("What lure caught the 18\" bass?") questions
- You want comprehensive coverage

**Produces:**
- 1 session summary chunk per log
- 1 chunk per event (catch/follow/strike)

### Event Only Mode

Creates only event-level chunks:

```python
FishingLogChunker(mode="event_only")
```

**Use when:**
- Users primarily ask about specific catches or techniques
- You want to minimize chunk count
- Session-level questions are rare

**Produces:**
- 1 chunk per event (no session summary)

### Session Only Mode

Creates only session summaries:

```python
FishingLogChunker(mode="session_only")
```

**Use when:**
- Users ask high-level pattern questions
- Detailed event data is less important
- You want maximum compression

**Produces:**
- 1 session summary per log (no event details)

## Weather Data

Control whether weather is included:

```python
# Include weather (default)
FishingLogChunker(include_weather=True)

# Exclude weather (reduces chunk size)
FishingLogChunker(include_weather=False)
```

## Example Queries

The chunker enables these types of questions:

### Pattern Analysis
- "What lures work best on Detroit River in June?"
- "What wind and pressure combination produces the best results?"
- "Show me successful sessions with water temp between 65-70°F"

### Technique Questions
- "What structure produces the most follows vs catches?"
- "What depth range is most productive for jerkbaits?"
- "How does smallmouth activity change with cloud cover?"

### Historical Lookups
- "What was my best session on Lake St. Clair last summer?"
- "Show me all catches over 4 pounds"
- "When did I last use a topwater successfully?"

## Metadata Filtering

The chunker extracts rich metadata for filtering:

```python
# Example: Query only high-rated sessions in summer
query_result = query_engine.query(
    "What techniques work best?",
    filters=MetadataFilters(filters=[
        MetadataFilter(key="local_rating", value=70, operator=FilterOperator.GTE),
        MetadataFilter(key="season", value="summer", operator=FilterOperator.EQ)
    ])
)
```

Available metadata fields:

**Session-level:**
- `date`, `year`, `month`, `season`
- `bow_name`, `target_fish_name`
- `local_rating`, `score`
- `water_temperature`, `hours_fishing`
- `catches`, `follows`, `strikes`, `total_events`
- `weather_mean_temp`, `weather_mean_pressure`, etc.

**Event-level (in addition to session context):**
- `event_type` (catch/follow/strike)
- `fish_type_name`, `fish_length`, `fish_weight`
- `lure_type_name`, `lure_description`
- `structure_type_name`, `depth`, `depth_range`

## Integration with Your Fishing App

### Option 1: Direct API Calls

Your fishing app makes HTTP requests to IdioRAG:

```javascript
// After user finishes a fishing session
async function indexFishingLog(logId) {
  // 1. Fetch enriched log from your database
  const enrichedLog = await fetchEnrichedLog(logId);
  
  // 2. Send to IdioRAG
  const response = await fetch('http://idiorag-server/documents', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      title: `${enrichedLog.location.bow_name} - ${enrichedLog.session.date}`,
      content: JSON.stringify(enrichedLog),
      chunker: 'fishing_log'
    })
  });
  
  return response.json();
}
```

### Option 2: Background Sync

Set up a background job to sync logs periodically:

```python
# Background worker
async def sync_fishing_logs():
    # Get all unsynced logs
    logs = await db.query("SELECT logId FROM logs WHERE indexed = false")
    
    for log_id in logs:
        # Enrich and format
        enriched_log = await prepare_enriched_log(log_id)
        
        # Index in IdioRAG
        await idiorag_client.create_document(
            title=f"{enriched_log['location']['bow_name']} - {enriched_log['session']['date']}",
            content=json.dumps(enriched_log),
            chunker="fishing_log"
        )
        
        # Mark as indexed
        await db.execute("UPDATE logs SET indexed = true WHERE logId = ?", log_id)
```

## Testing and Iteration

### 1. Start with Hybrid Mode

```python
register_chunker("fishing_log", lambda: FishingLogChunker(mode="hybrid"))
```

### 2. Index a Few Sample Logs

```bash
# Index 3-5 representative logs with various event counts
```

### 3. Test Query Quality

```bash
# Ask diverse questions
curl -X POST "http://localhost:8000/query" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "What lures work best for bass in summer?"}'
```

### 4. Iterate

Based on results:
- If too many irrelevant chunks → try `event_only` mode
- If missing session context → stick with `hybrid`
- If weather noise is high → set `include_weather=False`
- If chunks too large → reduce descriptions in input format
- If chunks too small → switch to `session_only`

## Performance Tips

1. **Batch Index Old Logs**: Use background job for historical data
2. **Index New Logs Immediately**: Index after session completion for recency
3. **Prune Low-Value Logs**: Skip logs with rating < 20 or no events
4. **Use Metadata Filters**: Pre-filter by date/location to reduce search space
5. **Monitor Chunk Sizes**: Aim for 200-500 tokens per chunk for optimal retrieval

## Troubleshooting

### "Invalid JSON in fishing log"
- Ensure content is valid JSON
- Check for encoding issues with special characters
- Validate schema matches INPUT_FORMAT.md

### Poor Query Results
- Verify IDs are resolved to human-readable names
- Check that event descriptions are complete
- Try different chunking modes
- Examine retrieved chunks to see what's matching

### Missing Context in Answers
- Switch from `event_only` to `hybrid` mode
- Ensure session-level data is included
- Add more descriptive text to lure/structure descriptions

### Too Many Irrelevant Results
- Use more specific queries
- Add metadata filters (date, location, rating)
- Try `session_only` mode for high-level questions
- Increase `similarity_top_k` to get more candidates

## Next Steps

1. **Implement Data Preparation**: Add enrichment logic to your fishing app
2. **Register Chunker**: Add registration to IdioRAG startup
3. **Test with Samples**: Index 5-10 logs and test queries
4. **Iterate on Mode**: Try different chunking strategies
5. **Production Deployment**: Set up background sync for all logs
6. **Add Features**: Consider weather forecasting, predictive queries, pattern analysis
