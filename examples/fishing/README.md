# Fishing Log Chunker for IdioRAG

This is a reference implementation of a domain-specific chunker for fishing log data. It demonstrates how to build custom chunkers that transform structured data into semantically rich chunks optimized for RAG retrieval.

## What This Does

The `FishingLogChunker` transforms your fishing logs into searchable chunks that enable natural language queries like:

- "What lures work best for smallmouth bass on Detroit River in June?"
- "Show me sessions with water temp between 65-70°F and high ratings"
- "What wind and pressure conditions produce the best results?"
- "What structure types generate the most follows vs catches?"

## Files in This Directory

- **[fishing_chunker.py](fishing_chunker.py)** - The main chunker implementation
- **[INPUT_FORMAT.md](INPUT_FORMAT.md)** - Detailed spec for the expected JSON format
- **[USAGE.md](USAGE.md)** - How to integrate and use the chunker
- **[test_chunker.py](test_chunker.py)** - Test script to see chunking output
- **[sample_enriched_log.json](sample_enriched_log.json)** - Example of properly formatted input

## Quick Test

To see the chunker in action:

```bash
# From WSL Ubuntu terminal
cd /home/ubuntu/workspace/idiorag
python examples/fishing/test_chunker.py
```

This will show you:
- How many chunks are created
- The text content of each chunk
- Metadata extracted for filtering
- Token counts and statistics
- Comparison of different chunking modes

## Key Concepts

### 1. Chunking Modes

**Hybrid (Recommended)**: Creates both a session summary AND individual event chunks
- Best for mixed query types
- Comprehensive coverage
- ~9 chunks per log with 8 events

**Event Only**: One chunk per event (catch/follow/strike)
- Best for technique-focused queries
- Smaller chunk count
- ~8 chunks per log with 8 events

**Session Only**: One summary per log
- Best for high-level pattern questions
- Maximum compression
- 1 chunk per log

### 2. Input Format Requirements

**Critical**: Your fishing app must resolve all IDs to human-readable names before sending to IdioRAG.

```json
{
  "session": {...},
  "location": {
    "bow_id": 42,
    "bow_name": "Detroit River - Fighting Island",  // ✓ Name resolved
    "target_fish_name": "Smallmouth Bass"           // ✓ Name resolved
  },
  "events": [{
    "fish_type_name": "Smallmouth Bass",            // ✓ Not just fishTypeId
    "lure_type_name": "Jerkbait",                   // ✓ Not just lureTypeId
    "structure_type_name": "Rocky Point"            // ✓ Not just structureTypeId
  }]
}
```

See [INPUT_FORMAT.md](INPUT_FORMAT.md) for complete schema.

### 3. Rich Metadata Extraction

Each chunk includes 20+ metadata fields for filtering:

```python
# Session-level metadata
- date, year, month, season
- bow_name, target_fish_name
- local_rating, score
- water_temperature
- weather conditions

# Event-level metadata (in addition to above)
- event_type (catch/follow/strike)
- fish_type_name, fish_length, fish_weight
- lure_type_name, lure_description
- structure_type_name, depth, depth_range
```

## Integration Steps

### Step 1: Prepare Data in Your Fishing App

Create an API endpoint or background job that:

1. Queries a fishing log with all events
2. Joins reference tables (bodies_of_water, fish_types, lure_types, structure_types)
3. Resolves all IDs to human-readable names
4. Includes weather data if available
5. Returns JSON matching the expected format

Example pseudo-SQL:
```sql
SELECT 
  l.*,
  bow.bowName,
  bow.targetFishName,
  -- Event subquery with joins
  (SELECT JSON_AGG(...)
   FROM logEvents e
   JOIN fishTypes ft ON e.fishTypeId = ft.fishTypeId
   JOIN lureTypes lt ON e.lureTypeId = lt.lureTypeId
   JOIN structureTypes st ON e.structureTypeId = st.structureTypeId
   WHERE e.logId = l.logId
  ) as events
FROM logs l
JOIN bodiesOfWater bow ON l.bowId = bow.bowId
WHERE l.logId = ?
```

### Step 2: Register the Chunker

In your IdioRAG application startup ([src/idiorag/main.py](../../src/idiorag/main.py)):

```python
from idiorag.rag.chunkers import register_chunker
from examples.fishing.fishing_chunker import FishingLogChunker

# Register during startup
@app.on_event("startup")
async def startup_event():
    # Register chunker
    register_chunker("fishing_log", FishingLogChunker(mode="hybrid"))
```

### Step 3: Index Logs from Your App

Call IdioRAG's API to index logs:

```bash
curl -X POST "http://localhost:8000/documents" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Detroit River - June 15 2024",
    "content": "<enriched_log_json>",
    "chunker": "fishing_log"
  }'
```

### Step 4: Query and Iterate

Test queries and adjust chunking mode based on results:

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "What lures work best for bass in June?"}'
```

## Testing the Chunker

Run the test script to see chunking output:

```bash
python examples/fishing/test_chunker.py
```

**Can you run this command in your WSL terminal and share the output?** This will help us:
1. Verify the chunker works correctly
2. See the actual chunk content and sizes
3. Compare different chunking modes
4. Decide which mode works best for your use case

## Next Steps After Testing

1. **Review test output** - Look at chunk content and metadata
2. **Choose chunking mode** - Based on your typical queries
3. **Implement data prep** - Add ID resolution to your fishing app
4. **Register chunker** - Add to IdioRAG startup
5. **Index sample logs** - Test with 5-10 real logs
6. **Test queries** - Try various question types
7. **Iterate** - Adjust mode/settings based on quality

## Architecture Benefits

This example demonstrates key architectural principles:

- **Domain-Agnostic Framework**: IdioRAG core doesn't know about fishing
- **Pluggable Extensions**: Chunker registers via clean interface
- **Semantic Completeness**: Each chunk is self-contained with full context
- **Rich Metadata**: Enables both semantic search AND structured filtering
- **Flexible Configuration**: Easy to test different strategies

## Questions?

See detailed documentation:
- [INPUT_FORMAT.md](INPUT_FORMAT.md) - Complete schema specification
- [USAGE.md](USAGE.md) - Integration patterns and examples
- [../../docs/internal/CUSTOM_CHUNKING.md](../../docs/internal/CUSTOM_CHUNKING.md) - General chunker guide

---

**Ready to test?** Run the test script and let me know what you see!
