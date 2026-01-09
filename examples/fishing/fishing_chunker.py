"""Fishing log chunker for event-level document processing.

This is a reference implementation showing how to create domain-specific chunkers
for structured data like fishing logs. It demonstrates:
- Event-level chunking with full context
- Rich metadata extraction
- Configurable chunking strategies
- ID resolution to human-readable names
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from idiorag.rag.chunkers.base import DocumentChunker
from llama_index.core.schema import BaseNode, TextNode, Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter


class FishingLogChunker(DocumentChunker):
    """Custom chunker for fishing logs with event-level granularity.
    
    This chunker supports multiple strategies:
    - 'hybrid': Session summary + event-level chunks (recommended)
    - 'event_only': Only event-level chunks
    - 'session_only': Only session summary
    
    Args:
        mode: Chunking strategy ('hybrid', 'event_only', 'session_only')
        include_weather: Include weather data in chunks (default: True)
    """
    
    def __init__(self, mode: str = "hybrid", include_weather: bool = True):
        """Initialize fishing log chunker with configuration.
        
        Args:
            mode: Chunking mode - 'hybrid', 'event_only', or 'session_only'
            include_weather: Whether to include weather data in chunks
        """
        if mode not in ["hybrid", "event_only", "session_only"]:
            raise ValueError(f"Invalid mode: {mode}. Must be 'hybrid', 'event_only', or 'session_only'")
        
        self.mode = mode
        self.include_weather = include_weather
        # Use splitter to create nodes properly (even though we don't split)
        self.splitter = SentenceSplitter(chunk_size=100000, chunk_overlap=0)
    
    def chunk_document(
        self,
        content: str,
        document_id: str,
        user_id: str,
        metadata: Optional[dict] = None,
    ) -> List[BaseNode]:
        """Chunk fishing log into semantically complete nodes.
        
        Expected input format: See INPUT_FORMAT.md for details.
        
        Args:
            content: JSON string of enriched fishing log
            document_id: Unique document identifier
            user_id: User identifier for isolation
            metadata: Additional metadata
            
        Returns:
            List of TextNode objects with event-level or session-level chunks
        """
        try:
            log_data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in fishing log: {e}")
        
        nodes = []
        
        # Extract session data
        session = log_data.get("session", {})
        location = log_data.get("location", {})
        weather = log_data.get("weather", {}) if self.include_weather else {}
        events = log_data.get("events", [])
        
        # Create session summary node (if hybrid or session_only)
        if self.mode in ["hybrid", "session_only"]:
            session_node = self._create_session_node(
                session, location, weather, events,
                document_id, user_id, metadata
            )
            nodes.append(session_node)
        
        # Create event nodes (if hybrid or event_only)
        if self.mode in ["hybrid", "event_only"] and events:
            event_nodes = self._create_event_nodes(
                events, session, location, weather,
                document_id, user_id, metadata
            )
            nodes.extend(event_nodes)
        
        # Validate all nodes
        self.validate_nodes(nodes, user_id, document_id)
        
        return nodes
    
    def _create_session_node(
        self,
        session: Dict,
        location: Dict,
        weather: Dict,
        events: List[Dict],
        document_id: str,
        user_id: str,
        metadata: Optional[dict]
    ) -> TextNode:
        """Create session summary node."""
        
        # Format session text
        text = self._format_session_summary(session, location, weather, events)
        
        # Build comprehensive metadata
        node_metadata = self._build_session_metadata(
            session, location, weather, events,
            document_id, user_id, metadata
        )
        
        # Create LlamaDocument and use splitter to get nodes
        # The splitter automatically sets ref_doc_id from the document's id_
        doc = LlamaDocument(
            text=text,
            metadata=node_metadata,
            id_=document_id
        )
        
        # Use splitter to create node (won't actually split due to large chunk_size)
        nodes = self.splitter.get_nodes_from_documents([doc])
        
        # Should return exactly one node
        if len(nodes) != 1:
            raise ValueError(f"Expected 1 node from session, got {len(nodes)}")
        
        return nodes[0]
    
    def _create_event_nodes(
        self,
        events: List[Dict],
        session: Dict,
        location: Dict,
        weather: Dict,
        document_id: str,
        user_id: str,
        metadata: Optional[dict]
    ) -> List[TextNode]:
        """Create one node per event with full context."""
        
        nodes = []
        
        for i, event in enumerate(events):
            # Format event text with context
            text = self._format_event_with_context(
                event, session, location, weather, i
            )
            
            # Build event-specific metadata
            node_metadata = self._build_event_metadata(
                event, session, location, weather, i,
                document_id, user_id, metadata
            )
            
            # Build event-specific metadata
            node_metadata = self._build_event_metadata(
                event, session, location, weather, i,
                document_id, user_id, metadata
            )
            
            # Create LlamaDocument and use splitter
            doc = LlamaDocument(
                text=text,
                metadata=node_metadata,
                id_=document_id
            )
            
            # Use splitter to create node
            doc_nodes = self.splitter.get_nodes_from_documents([doc])
            
            # Should return exactly one node
            if len(doc_nodes) != 1:
                raise ValueError(f"Expected 1 node from event {i}, got {len(doc_nodes)}")
            
            nodes.append(doc_nodes[0])
        
        return nodes
    
    def _format_session_summary(
        self,
        session: Dict,
        location: Dict,
        weather: Dict,
        events: List[Dict]
    ) -> str:
        """Format session as human-readable summary."""
        
        date = session.get("date", "Unknown date")
        bow_name = location.get("bow_name", "Unknown location")
        local_rating = session.get("local_rating", "N/A")
        score = session.get("score", 0)
        hours = session.get("hours_fishing", 0)
        target_fish = location.get("target_fish_name", "Multiple species")
        
        # Count event types
        catches = sum(1 for e in events if e.get("event_type") == "catch")
        follows = sum(1 for e in events if e.get("event_type") == "follow")
        strikes = sum(1 for e in events if e.get("event_type") == "strike")
        
        # Weather summary
        weather_summary = ""
        if weather:
            temp = weather.get("mean_temperature")
            pressure = weather.get("mean_pressure")
            wind_speed = weather.get("mean_wind_speed")
            cloud_cover = weather.get("mean_cloud_cover")
            
            weather_summary = f"\nWeather: {temp}°C, Pressure {pressure} hPa, Wind {wind_speed} km/h, Cloud Cover {cloud_cover}%"
        
        # Session comments
        comments = session.get("comments", "")
        comments_text = f"\n\nSession Notes: {comments}" if comments else ""
        
        text = f"""Fishing Session Summary
Date: {date}
Location: {bow_name}
Target Species: {target_fish}
Duration: {hours} hours
Local Rating: {local_rating}/100 (Score: {score})
Water Temperature: {session.get('water_temperature')}°{session.get('water_temp_unit', 'F')}
Anglers: {session.get('number_of_anglers', 1)}{f" (Fished with: {session.get('fished_with')})" if session.get('fished_with') else ""}
{weather_summary}

Activity Summary:
- Catches: {catches}
- Follows: {follows}  
- Strikes: {strikes}
- Total Events: {len(events)}{comments_text}
"""
        
        return text.strip()
    
    def _format_event_with_context(
        self,
        event: Dict,
        session: Dict,
        location: Dict,
        weather: Dict,
        event_index: int
    ) -> str:
        """Format single event with full context."""
        
        event_type = event.get("event_type", "unknown").upper()
        event_time = event.get("event_time", "Unknown time")
        fish_name = event.get("fish_type_name", "Unknown species")
        lure_name = event.get("lure_type_name", "Unknown lure")
        lure_desc = event.get("lure_description", "")
        
        # Session context
        date = session.get("date", "Unknown date")
        bow_name = location.get("bow_name", "Unknown location")
        water_temp = session.get("water_temperature")
        local_rating = session.get("local_rating")
        
        # Event-specific details
        length = event.get("length")
        length_unit = event.get("length_unit_name", "in")
        weight = event.get("weight")
        weight_unit = event.get("weight_unit_name", "lbs")
        structure = event.get("structure_type_name", "Unknown structure")
        structure_desc = event.get("structure_description", "")
        depth = event.get("depth")
        depth_range = event.get("depth_range")
        comments = event.get("comments", "")
        
        # Build text
        text_parts = [
            f"Fishing Event #{event_index + 1} - {event_type}",
            f"Date: {date} at {event_time}",
            f"Location: {bow_name}",
            f"Session Rating: {local_rating}/100",
            "",
            f"Fish: {fish_name}",
        ]
        
        if length:
            text_parts.append(f"Size: {length} {length_unit}" + (f", {weight} {weight_unit}" if weight else ""))
        
        text_parts.extend([
            "",
            f"Lure: {lure_name}",
        ])
        
        if lure_desc:
            text_parts.append(f"Lure Description: {lure_desc}")
        
        text_parts.extend([
            "",
            f"Structure: {structure}",
        ])
        
        if structure_desc:
            text_parts.append(f"Structure Details: {structure_desc}")
        
        if depth:
            depth_text = f"Depth: {depth}ft"
            if depth_range:
                depth_text += f" (±{depth_range}ft)"
            text_parts.append(depth_text)
        
        text_parts.append(f"\nWater Temperature: {water_temp}°{session.get('water_temp_unit', 'F')}")
        
        # Weather context
        if weather and self.include_weather:
            temp = weather.get("mean_temperature")
            pressure = weather.get("mean_pressure")
            wind_speed = weather.get("mean_wind_speed")
            wind_dir = weather.get("dominant_wind_direction")
            cloud_cover = weather.get("mean_cloud_cover")
            
            text_parts.extend([
                "",
                f"Weather Conditions:",
                f"- Air Temperature: {temp}°C",
                f"- Pressure: {pressure} hPa",
                f"- Wind: {wind_speed} km/h at {wind_dir}°",
                f"- Cloud Cover: {cloud_cover}%",
            ])
        
        if comments:
            text_parts.extend(["", f"Notes: {comments}"])
        
        return "\n".join(text_parts)
    
    def _build_session_metadata(
        self,
        session: Dict,
        location: Dict,
        weather: Dict,
        events: List[Dict],
        document_id: str,
        user_id: str,
        metadata: Optional[dict]
    ) -> Dict[str, Any]:
        """Build metadata for session node."""
        
        base_metadata = {
            "document_id": document_id,
            "user_id": user_id,
            "chunk_type": "session_summary",
            
            # Temporal
            "date": session.get("date"),
            "year": self._extract_year(session.get("date")),
            "month": self._extract_month(session.get("date")),
            "season": self._extract_season(session.get("date")),
            
            # Location
            "bow_id": location.get("bow_id"),
            "bow_name": location.get("bow_name"),
            "target_fish_name": location.get("target_fish_name"),
            
            # Session metrics
            "local_rating": session.get("local_rating"),
            "score": session.get("score"),
            "hours_fishing": session.get("hours_fishing"),
            "water_temperature": session.get("water_temperature"),
            "number_of_anglers": session.get("number_of_anglers"),
            
            # Event counts
            "total_events": len(events),
            "catches": sum(1 for e in events if e.get("event_type") == "catch"),
            "follows": sum(1 for e in events if e.get("event_type") == "follow"),
            "strikes": sum(1 for e in events if e.get("event_type") == "strike"),
        }
        
        # Add weather if available
        if weather and self.include_weather:
            base_metadata.update({
                "weather_mean_temp": weather.get("mean_temperature"),
                "weather_mean_pressure": weather.get("mean_pressure"),
                "weather_mean_wind_speed": weather.get("mean_wind_speed"),
                "weather_wind_direction": weather.get("dominant_wind_direction"),
                "weather_cloud_cover": weather.get("mean_cloud_cover"),
            })
        
        # Merge with any additional metadata
        if metadata:
            base_metadata.update(metadata)
        
        return base_metadata
    
    def _build_event_metadata(
        self,
        event: Dict,
        session: Dict,
        location: Dict,
        weather: Dict,
        event_index: int,
        document_id: str,
        user_id: str,
        metadata: Optional[dict]
    ) -> Dict[str, Any]:
        """Build metadata for event node."""
        
        base_metadata = {
            "document_id": document_id,
            "user_id": user_id,
            "chunk_type": "fishing_event",
            "event_index": event_index,
            
            # Event specifics
            "event_type": event.get("event_type"),
            "event_id": event.get("event_id"),
            "event_time": event.get("event_time"),
            
            # Fish details
            "fish_type_id": event.get("fish_type_id"),
            "fish_type_name": event.get("fish_type_name"),
            "fish_length": event.get("length"),
            "fish_weight": event.get("weight"),
            
            # Lure details
            "lure_type_id": event.get("lure_type_id"),
            "lure_type_name": event.get("lure_type_name"),
            "lure_description": event.get("lure_description"),
            
            # Structure
            "structure_type_id": event.get("structure_type_id"),
            "structure_type_name": event.get("structure_type_name"),
            "structure_description": event.get("structure_description"),
            "depth": event.get("depth"),
            "depth_range": event.get("depth_range"),
            
            # Session context
            "date": session.get("date"),
            "year": self._extract_year(session.get("date")),
            "month": self._extract_month(session.get("date")),
            "season": self._extract_season(session.get("date")),
            "bow_id": location.get("bow_id"),
            "bow_name": location.get("bow_name"),
            "local_rating": session.get("local_rating"),
            "water_temperature": session.get("water_temperature"),
        }
        
        # Add weather if available
        if weather and self.include_weather:
            base_metadata.update({
                "weather_mean_temp": weather.get("mean_temperature"),
                "weather_mean_pressure": weather.get("mean_pressure"),
                "weather_mean_wind_speed": weather.get("mean_wind_speed"),
                "weather_wind_direction": weather.get("dominant_wind_direction"),
                "weather_cloud_cover": weather.get("mean_cloud_cover"),
            })
        
        # Merge with any additional metadata
        if metadata:
            base_metadata.update(metadata)
        
        return base_metadata
    
    def _extract_year(self, date_str: Optional[str]) -> Optional[int]:
        """Extract year from ISO date string."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00")).year
        except (ValueError, AttributeError):
            return None
    
    def _extract_month(self, date_str: Optional[str]) -> Optional[int]:
        """Extract month from ISO date string."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00")).month
        except (ValueError, AttributeError):
            return None
    
    def _extract_season(self, date_str: Optional[str]) -> Optional[str]:
        """Extract season from date."""
        month = self._extract_month(date_str)
        if not month:
            return None
        
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "fall"
