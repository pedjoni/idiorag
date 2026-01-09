"""Test script for FishingLogChunker.

This script tests the fishing log chunker with different modes and
demonstrates the chunking output.
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from examples.fishing.fishing_chunker import FishingLogChunker


def test_chunker_mode(mode: str, include_weather: bool = True):
    """Test a specific chunker configuration."""
    
    print(f"\n{'=' * 80}")
    print(f"Testing FishingLogChunker - Mode: {mode}, Weather: {include_weather}")
    print('=' * 80)
    
    # Load sample data
    sample_file = Path(__file__).parent / "sample_enriched_log.json"
    with open(sample_file, 'r') as f:
        content = f.read()
    
    # Create chunker
    chunker = FishingLogChunker(mode=mode, include_weather=include_weather)
    
    # Chunk the document
    nodes = chunker.chunk_document(
        content=content,
        document_id="test_log_191812",
        user_id="test_user_123",
        metadata={"source": "test_script"}
    )
    
    print(f"\nGenerated {len(nodes)} chunks\n")
    
    # Display each chunk
    for i, node in enumerate(nodes, 1):
        print(f"\n{'─' * 80}")
        print(f"Chunk {i} of {len(nodes)}")
        print(f"{'─' * 80}")
        
        # Show metadata
        print("\nMetadata:")
        key_metadata = {
            "chunk_type": node.metadata.get("chunk_type"),
            "event_type": node.metadata.get("event_type"),
            "fish_type_name": node.metadata.get("fish_type_name"),
            "lure_type_name": node.metadata.get("lure_type_name"),
            "structure_type_name": node.metadata.get("structure_type_name"),
            "date": node.metadata.get("date"),
            "bow_name": node.metadata.get("bow_name"),
            "local_rating": node.metadata.get("local_rating"),
        }
        for key, value in key_metadata.items():
            if value is not None:
                print(f"  {key}: {value}")
        
        # Show text content (truncated if too long)
        print("\nText Content:")
        text = node.text
        if len(text) > 500:
            print(text[:500] + f"\n... [truncated, total {len(text)} chars]")
        else:
            print(text)
        
        print(f"\nToken count (estimated): ~{len(text.split())}")
    
    # Summary statistics
    print(f"\n{'=' * 80}")
    print("Summary Statistics")
    print('=' * 80)
    print(f"Total chunks: {len(nodes)}")
    print(f"Chunk types: {set(n.metadata['chunk_type'] for n in nodes)}")
    
    if mode in ["hybrid", "event_only"]:
        event_types = [n.metadata.get('event_type') for n in nodes if n.metadata.get('event_type')]
        if event_types:
            print(f"Event types: catch={event_types.count('catch')}, "
                  f"follow={event_types.count('follow')}, "
                  f"strike={event_types.count('strike')}")
    
    total_tokens = sum(len(n.text.split()) for n in nodes)
    avg_tokens = total_tokens / len(nodes) if nodes else 0
    print(f"Total tokens (estimated): ~{total_tokens}")
    print(f"Average tokens per chunk: ~{avg_tokens:.0f}")
    print()


def main():
    """Run all test scenarios."""
    
    print("\n" + "=" * 80)
    print("FishingLogChunker Test Suite")
    print("=" * 80)
    
    # Test all modes
    test_chunker_mode("hybrid", include_weather=True)
    test_chunker_mode("event_only", include_weather=True)
    test_chunker_mode("session_only", include_weather=True)
    
    # Test without weather
    test_chunker_mode("hybrid", include_weather=False)
    
    print("\n" + "=" * 80)
    print("All tests completed!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Review the chunk outputs above")
    print("2. Choose the mode that best fits your use case")
    print("3. Register the chunker in your application")
    print("4. Index real fishing logs and test queries")
    print()


if __name__ == "__main__":
    main()
