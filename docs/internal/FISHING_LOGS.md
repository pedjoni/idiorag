# Fishing Log Integration Guide

This guide explains how to integrate fishing logs from your app with IdioRAG's flexible RAG system.

## Understanding Fishing Log Structure

Based on your description, fishing logs have a hierarchical structure:

```
Fishing Log (Session)
├── Basic Info
│   ├── Date/Time
│   ├── Location
│   ├── Weather Data
│   └── Comments
├── Event 1 (Catch/Follow/Strike)
│   ├── Event Type
│   ├── Fish Species
│   ├── Lure Type
│   ├── Time of Day
│   ├── Structure
│   └── Additional Details
├── Event 2
│   └── ...
└── Event N
```

## Chunking Strategies

IdioRAG supports multiple chunking strategies that you can test and iterate on:

### Strategy 1: Full Log as Single Document (Simple)

**Best for:** Small logs, general queries about fishing sessions

```python
{
    "title": "Fishing Session - Lake Michigan - 2024-01-15",
    "content": """
    Fishing Log: January 15, 2024
    Location: Lake Michigan, North Shore
    Weather: Sunny, 65°F, Wind 5-10 mph NW
    
    Comments: Great day on the water. Fish were active in the morning.
    
    Events:
    1. CATCH - 8:30 AM
       - Species: Largemouth Bass
       - Size: 3.5 lbs
       - Lure: Green Pumpkin Senko
       - Structure: Weed edge, 8ft depth
       - Details: Hit on the fall
    
    2. FOLLOW - 9:15 AM
       - Species: Northern Pike
       - Lure: Silver spoon
       - Structure: Open water
    
    3. CATCH - 10:00 AM
       - Species: Largemouth Bass
       - Size: 2.1 lbs
       - Lure: Chatterbait
       - Structure: Rocky point
    """,
    "doc_type": "fishing_log",
    "metadata": {
        "log_id": "log_123",
        "date": "2024-01-15",
        "location": "Lake Michigan",
        "weather_temp": 65,
        "weather_conditions": "sunny",
        "event_count": 3,
        "catches": 2
    }
}
```

### Strategy 2: Event-Level Chunking (Recommended)

**Best for:** Detailed queries about specific events, patterns, lure effectiveness

Create separate documents for each event with rich context:

```python
# Log metadata document
{
    "title": "Fishing Log Summary - Lake Michigan - 2024-01-15",
    "content": "Fishing session on Lake Michigan North Shore. Weather: Sunny, 65°F, wind 5-10mph NW. 3 events total, 2 catches. Great morning bite.",
    "doc_type": "fishing_log_summary",
    "metadata": {
        "log_id": "log_123",
        "date": "2024-01-15",
        "location": "Lake Michigan"
    }
}

# Event documents (one per event)
{
    "title": "Catch Event - Largemouth Bass - 2024-01-15 08:30",
    "content": """
    Event Type: CATCH
    Session: Lake Michigan North Shore, January 15, 2024, 8:30 AM
    Weather: Sunny, 65°F, Wind 5-10 mph NW
    
    Fish Details:
    - Species: Largemouth Bass
    - Size: 3.5 lbs
    - Quality: Trophy fish
    
    Presentation:
    - Lure: Green Pumpkin Senko
    - Technique: Weightless, slow fall
    - Structure: Weed edge at 8ft depth
    - Hit on the fall
    
    Context: First catch of the day during morning feeding period. Weed edges were productive.
    """,
    "doc_type": "fishing_event",
    "metadata": {
        "log_id": "log_123",
        "event_id": "event_456",
        "event_type": "catch",
        "species": "largemouth_bass",
        "lure_type": "senko",
        "structure": "weed_edge",
        "time_of_day": "morning",
        "date": "2024-01-15",
        "location": "Lake Michigan",
        "weight_lbs": 3.5
    }
}
```

### Strategy 3: Hybrid Approach (Most Flexible)

Combine both strategies:
1. Full log document for context
2. Individual event documents for detailed analysis

This allows queries like:
- "What were my best fishing days?" (uses log summaries)
- "When do largemouth bass bite best on senkos?" (uses event details)

## Custom Chunking Implementation

Create a custom chunking module for fishing logs:

```python
# src/idiorag/rag/fishing_chunker.py

from typing import List, Dict, Any
from datetime import datetime

class FishingLogChunker:
    """Custom chunker for fishing log data."""
    
    @staticmethod
    def chunk_by_event(log_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create one document per event with full context.
        
        Args:
            log_data: Complete fishing log with events
            
        Returns:
            List of document dictionaries
        """
        documents = []
        
        # Create log summary document
        summary = {
            "title": f"Fishing Log - {log_data['location']} - {log_data['date']}",
            "content": format_log_summary(log_data),
            "doc_type": "fishing_log_summary",
            "metadata": extract_log_metadata(log_data)
        }
        documents.append(summary)
        
        # Create event documents
        for event in log_data.get('events', []):
            event_doc = {
                "title": format_event_title(event, log_data),
                "content": format_event_content(event, log_data),
                "doc_type": "fishing_event",
                "metadata": extract_event_metadata(event, log_data)
            }
            documents.append(event_doc)
        
        return documents
```

## Metadata Design for Queries

Rich metadata enables powerful filtering and queries:

```python
{
    # Temporal
    "date": "2024-01-15",
    "time_of_day": "morning",  # morning, afternoon, evening
    "season": "winter",
    "month": 1,
    
    # Location
    "location": "Lake Michigan",
    "region": "North Shore",
    "water_type": "lake",
    
    # Weather
    "weather_temp": 65,
    "weather_conditions": "sunny",
    "wind_speed": "5-10mph",
    "wind_direction": "NW",
    
    # Event-specific
    "event_type": "catch",  # catch, follow, strike
    "species": "largemouth_bass",
    "lure_type": "senko",
    "lure_color": "green_pumpkin",
    "structure": "weed_edge",
    "depth_ft": 8,
    "weight_lbs": 3.5,
    
    # Relationships
    "log_id": "log_123",
    "event_id": "event_456",
    "user_id": "user_789"
}
```

## Example Queries

With proper chunking and metadata, users can ask:

1. **Pattern Analysis**
   - "When do bass bite best on senkos?"
   - "What lures work best in weedy areas?"
   - "What's the best time of day for pike?"

2. **Location Intelligence**
   - "What works at Lake Michigan in summer?"
   - "Best structures for bass at my favorite lake?"

3. **Weather Correlation**
   - "Do fish bite better on cloudy days?"
   - "Best lures in windy conditions?"

4. **Personal History**
   - "What's my best lure for largemouth bass?"
   - "When did I catch my biggest fish?"
   - "What were my most productive days?"

## Implementation Steps

### 1. Create Chunking Module

Create `src/idiorag/rag/fishing_chunker.py` with your custom logic.

### 2. Add Upload Endpoint

Create a specialized endpoint for fishing logs:

```python
@router.post("/fishing-log")
async def upload_fishing_log(
    log_data: FishingLogData,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Upload and index a complete fishing log."""
    from ..rag.fishing_chunker import FishingLogChunker
    
    # Chunk the log
    documents = FishingLogChunker.chunk_by_event(log_data.dict())
    
    # Upload each document
    for doc in documents:
        await create_document_internal(doc, user.user_id, db)
```

### 3. Test and Iterate

1. Upload test logs with different chunking strategies
2. Query and evaluate result quality
3. Adjust chunking, metadata, and prompts
4. Repeat

## Best Practices

1. **Include Context**: Each chunk should be understandable standalone
2. **Rich Metadata**: More metadata = better filtering and relevance
3. **Consistent Format**: Use templates for content formatting
4. **Test Queries**: Create a test set of queries to evaluate chunking
5. **Iterate**: Start simple, add complexity based on query performance

## Next Steps

1. Define your fishing log JSON schema
2. Implement `FishingLogChunker` class
3. Create test logs
4. Upload and query
5. Evaluate and refine

The framework is designed to be flexible - you can change chunking strategies without rebuilding the entire system.
