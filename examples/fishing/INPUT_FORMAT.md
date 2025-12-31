# Fishing Log Input Format

This document describes the expected format for fishing logs that will be processed by the `FishingLogChunker`.

## Overview

**IMPORTANT**: The chunker expects **enriched/resolved** fishing log data where all IDs have been replaced with human-readable names. Your fishing app should prepare this format before sending documents to IdioRAG.

## Required Structure

Each fishing log document should be a JSON object with the following structure:

```json
{
  "session": {
    "log_id": 123456,
    "date": "2024-06-15T08:00:00Z",
    "local_rating": 75,
    "score": 150,
    "hours_fishing": 4.5,
    "water_temperature": 68,
    "water_temp_unit": "F",
    "number_of_anglers": 2,
    "fished_with": "John Smith",
    "comments": "Great morning bite, water clarity improving"
  },
  "location": {
    "bow_id": 42,
    "bow_name": "Detroit River - Fighting Island",
    "target_fish_name": "Smallmouth Bass"
  },
  "weather": {
    "mean_temperature": 22.5,
    "mean_pressure": 1013.2,
    "mean_wind_speed": 12.3,
    "dominant_wind_direction": 180,
    "mean_cloud_cover": 25
  },
  "events": [
    {
      "event_id": 7890,
      "event_type": "catch",
      "event_time": "08:45:00",
      "fish_type_id": 15,
      "fish_type_name": "Smallmouth Bass",
      "length": 18.5,
      "length_unit_name": "in",
      "weight": 3.2,
      "weight_unit_name": "lbs",
      "lure_type_id": 23,
      "lure_type_name": "Jerkbait",
      "lure_description": "Silver/blue shad pattern, suspending",
      "structure_type_id": 8,
      "structure_type_name": "Rocky Point",
      "structure_description": "Shallow rock pile near channel",
      "depth": 8,
      "depth_range": 2,
      "comments": "Hit on pause, aggressive strike"
    },
    {
      "event_id": 7891,
      "event_type": "follow",
      "event_time": "09:15:00",
      "fish_type_id": 15,
      "fish_type_name": "Smallmouth Bass",
      "lure_type_id": 12,
      "lure_type_name": "Topwater",
      "lure_description": "Popper, white",
      "structure_type_id": 8,
      "structure_type_name": "Rocky Point",
      "depth": 6,
      "comments": "Large fish followed to boat but didn't commit"
    }
  ]
}
```

## Field Descriptions

### Session Object (Required)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `log_id` | integer | Yes | Unique identifier for this log session |
| `date` | string (ISO 8601) | Yes | Start date/time of fishing session |
| `local_rating` | integer (0-100) | Yes | User's rating of session quality |
| `score` | integer | No | Calculated success score |
| `hours_fishing` | float | Yes | Duration in hours |
| `water_temperature` | float | Yes | Water temp at session start |
| `water_temp_unit` | string | Yes | "F" or "C" |
| `number_of_anglers` | integer | Yes | Number of people fishing |
| `fished_with` | string | No | Names of other anglers |
| `comments` | string | No | Session-level notes |

### Location Object (Required)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `bow_id` | integer | Yes | Body of water ID (for reference) |
| `bow_name` | string | Yes | **Human-readable location name** |
| `target_fish_name` | string | Yes | **Resolved target species name** |

### Weather Object (Optional)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mean_temperature` | float | No | Average air temperature (°C) |
| `mean_pressure` | float | No | Average barometric pressure (hPa) |
| `mean_wind_speed` | float | No | Average wind speed (km/h) |
| `dominant_wind_direction` | integer | No | Wind direction in degrees (0-360) |
| `mean_cloud_cover` | integer | No | Cloud cover percentage (0-100) |

### Events Array (Optional but recommended)

Each event object:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_id` | integer | Yes | Unique event identifier |
| `event_type` | string | Yes | "catch", "follow", or "strike" |
| `event_time` | string (HH:MM:SS) | Yes | Time of event |
| `fish_type_id` | integer | Yes | Fish type ID (for reference) |
| `fish_type_name` | string | Yes | **Resolved fish species name** |
| `length` | float | No | Fish length |
| `length_unit_name` | string | No | **Resolved unit** (e.g., "in", "cm") |
| `weight` | float | No | Fish weight |
| `weight_unit_name` | string | No | **Resolved unit** (e.g., "lbs", "kg") |
| `lure_type_id` | integer | Yes | Lure type ID (for reference) |
| `lure_type_name` | string | Yes | **Resolved lure name** |
| `lure_description` | string | No | Color, size, specific model |
| `structure_type_id` | integer | Yes | Structure type ID (for reference) |
| `structure_type_name` | string | Yes | **Resolved structure name** |
| `structure_description` | string | No | Specific location details |
| `depth` | integer | No | Depth in feet |
| `depth_range` | integer | No | Depth range (±) |
| `comments` | string | No | Event-specific notes |

## How to Prepare Data from Your Fishing App

Your fishing app should perform these steps **before** sending data to IdioRAG:

1. **Query the fishing log** with all related events
2. **Resolve all IDs to names:**
   - `bowId` → `bow_name` (from bodies_of_water table)
   - `fishTypeId` → `fish_type_name` (from fish_types table)
   - `lureTypeId` → `lure_type_name` (from lure_types table)
   - `structureTypeId` → `structure_type_name` (from structure_types table)
   - `targetFishId` → `target_fish_name`
   - Unit IDs → unit names
3. **Join weather data** (if available) using log_id
4. **Format as JSON** matching the structure above
5. **Send to IdioRAG's `/documents` endpoint** with `chunker: "fishing_log"`

## Example Transformation

### Raw Data (From Your DB):
```json
{
  "logId": 123,
  "bowId": 42,
  "fishTypeId": 15,
  "lureTypeId": 23
}
```

### Enriched Data (For IdioRAG):
```json
{
  "session": {
    "log_id": 123,
    ...
  },
  "location": {
    "bow_id": 42,
    "bow_name": "Detroit River - Fighting Island",
    ...
  },
  "events": [{
    "fish_type_id": 15,
    "fish_type_name": "Smallmouth Bass",
    "lure_type_id": 23,
    "lure_type_name": "Jerkbait",
    ...
  }]
}
```

## Example SQL Query (Pseudo-code)

```sql
SELECT 
  l.logId,
  l.date,
  l.localRating,
  bow.bowName,
  bow.targetFishName,
  -- Session fields
  ...
  -- Weather join
  w.meanTemperature,
  w.meanPressure,
  ...
  -- Event subquery with joins
  (SELECT JSON_AGG(
    JSON_BUILD_OBJECT(
      'event_id', e.eventId,
      'fish_type_name', ft.fishTypeName,
      'lure_type_name', lt.lureTypeName,
      'structure_type_name', st.structureTypeName,
      ...
    )
  ) FROM logEvents e
  JOIN fishTypes ft ON e.fishTypeId = ft.fishTypeId
  JOIN lureTypes lt ON e.lureTypeId = lt.lureTypeId
  JOIN structureTypes st ON e.structureTypeId = st.structureTypeId
  WHERE e.logId = l.logId
  ) as events
FROM logs l
JOIN bodiesOfWater bow ON l.bowId = bow.bowId
LEFT JOIN weatherData w ON l.logId = w.logId
WHERE l.logId = ?
```

## Why This Format?

1. **Semantic Search Works Better**: LLMs understand "Smallmouth Bass" better than "fishTypeId: 15"
2. **Self-Contained Chunks**: Each chunk has all context needed to answer queries
3. **Preserves Relationships**: IDs are kept for debugging but names enable retrieval
4. **Query-Friendly**: Users ask "What lures work on Detroit River?" not "What lures work on bow_id 42?"

## Next Steps

Once your fishing app can produce this format:

1. Register the chunker (see [USAGE.md](USAGE.md))
2. Test with a few sample logs
3. Iterate on chunking mode (`hybrid` vs `event_only`)
4. Fine-tune based on query quality
