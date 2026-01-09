#!/usr/bin/env python3
"""Quick start script for testing IdioRAG locally."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import httpx


async def test_api():
    """Test the API endpoints."""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing IdioRAG API...")
    print("=" * 60)
    
    # Use longer timeout for RAG queries (embedding + vector search + LLM can take time)
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Health Check
        print("\n1. Testing health check...")
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                print("✅ Health check passed")
                print(f"   Response: {response.json()}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Could not connect to API: {e}")
            print("\n⚠ Make sure the application is running:")
            print("   python run.py")
            return False
        
        # 2. Generate test token
        print("\n2. Generating test JWT token...")
        try:
            from idiorag.utils import generate_test_token
            token = generate_test_token(
                user_id="test_fisher_123",
                email="fisher@example.com"
            )
            print("✅ Test token generated")
            print(f"   Token: {token[:50]}...")
        except Exception as e:
            print(f"❌ Token generation failed: {e}")
            return False
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Create a document
        print("\n3. Creating a test document...")
        doc_data = {
            "title": "Lake Michigan - Bass Fishing",
            "content": """
            Fishing Log: January 15, 2025
            Location: Lake Michigan, North Shore
            Weather: Sunny, 65°F, light wind
            
            Caught 3 largemouth bass using green pumpkin senko.
            Fish were active near weed edges in 8-10ft of water.
            Best bite was in the morning between 8-10 AM.
            Water temp: 68°F, slight chop on surface.
            """,
            "doc_type": "fishing_log",
            "source": "test_log_20250115",  # Add source for deduplication
            "metadata": {
                "location": "Lake Michigan",
                "date": "2025-01-15",
                "species": ["largemouth_bass"],
                "lures": ["senko"],
                "weather": "sunny"
            }
        }
        
        try:
            response = await client.post(
                f"{base_url}/api/v1/documents",
                json=doc_data,
                headers=headers,
                timeout=30.0  # Add explicit timeout
            )
            if response.status_code == 201:
                doc = response.json()
                doc_id = doc["id"]
                print("✅ Document created successfully")
                print(f"   Document ID: {doc_id}")
            else:
                print(f"❌ Document creation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Document creation error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # 4. List documents
        print("\n4. Listing documents...")
        try:
            response = await client.get(
                f"{base_url}/api/v1/documents",
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                print("✅ Documents retrieved successfully")
                print(f"   Total documents: {data['total']}")
            else:
                print(f"❌ List documents failed: {response.status_code}")
        except Exception as e:
            print(f"❌ List documents error: {e}")
        
        # 5. Get specific document
        print("\n5. Getting specific document...")
        try:
            response = await client.get(
                f"{base_url}/api/v1/documents/{doc_id}",
                headers=headers
            )
            if response.status_code == 200:
                doc = response.json()
                print("✅ Document retrieved successfully")
                print(f"   Title: {doc['title']}")
            else:
                print(f"❌ Get document failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Get document error: {e}")
        
        # 6. Query (will return placeholder until RAG is implemented)
        print("\n6. Testing query endpoint...")
        try:
            response = await client.post(
                f"{base_url}/api/v1/query/",
                json={
                    "query": "What lures work best for bass?",
                    "top_k": 5
                },
                headers=headers
            )
            if response.status_code == 200:
                result = response.json()
                answer = result['answer']
                metadata = result.get('metadata', {})
                print("✅ Query endpoint responded")
                print(f"   Answer: {answer[:100]}...")
                print(f"   Retrieval Metadata:")
                print(f"      Total documents in index: {metadata.get('total_documents_in_index', 'N/A')}")
                print(f"      Documents retrieved: {metadata.get('documents_retrieved', 'N/A')}")
                print(f"      Avg relevance score: {metadata.get('avg_relevance_score', 'N/A')}")
                if "Error processing query" in answer:
                    print("❌ Query returned an error instead of answer")
                    return False
            else:
                print(f"❌ Query failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Query error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # 7. Delete document
        print("\n7. Deleting test document...")
        try:
            response = await client.delete(
                f"{base_url}/api/v1/documents/{doc_id}",
                headers=headers
            )
            if response.status_code == 204:
                print("✅ Document deleted successfully")
            else:
                print(f"❌ Delete failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Delete error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ API testing completed!")
    print("\n📚 Next steps:")
    print("   - Check http://localhost:8000/docs for interactive API docs")
    print("   - Read DEVELOPMENT.md for detailed setup")
    print("   - Start building your RAG application!")
    return True


def main():
    """Main entry point."""
    print("IdioRAG Quick Start Test")
    print("=" * 60)
    print("\nThis script will test your IdioRAG setup.")
    print("Make sure the application is running (python run.py)")
    print("\nPress Ctrl+C to cancel, or Enter to continue...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        return 0
    
    success = asyncio.run(test_api())
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
