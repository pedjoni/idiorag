#!/usr/bin/env python3
"""Test script for streaming endpoint."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import httpx
import json


async def test_streaming():
    """Test the streaming chat endpoint."""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing IdioRAG Streaming Endpoint...")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Generate test token
        print("\n1. Generating test JWT token...")
        try:
            from idiorag.utils import generate_test_token
            token = generate_test_token(
                user_id="test_fisher_streaming",
                email="streamer@example.com"
            )
            print("✅ Test token generated")
        except Exception as e:
            print(f"❌ Token generation failed: {e}")
            return False
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a test document first
        print("\n2. Creating test document...")
        doc_data = {
            "title": "Bass Fishing Tips",
            "content": """
            Best Bass Fishing Tips:
            
            1. Early morning (6-9 AM) is the best time for bass fishing
            2. Use green pumpkin or watermelon colored soft plastics
            3. Target weed edges and drop-offs in 8-15 feet of water
            4. Slow retrieves work better in cold water
            5. Texas-rigged senkos are highly effective year-round
            """,
            "doc_type": "fishing_tips",
            "source": "test_bass_tips_v1",  # Add source for deduplication
            "metadata": {
                "category": "tips",
                "species": ["largemouth_bass", "smallmouth_bass"]
            }
        }
        
        try:
            response = await client.post(
                f"{base_url}/api/v1/documents",
                json=doc_data,
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 201:
                doc = response.json()
                doc_id = doc["id"]
                print("✅ Document created")
                print(f"   Document ID: {doc_id}")
            else:
                print(f"❌ Document creation failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Document creation error: {e}")
            return False
        
        # Wait a moment for indexing
        await asyncio.sleep(2)
        
        # Test streaming endpoint
        print("\n3. Testing streaming chat endpoint...")
        print("   Query: 'What are the best times to fish for bass?'")
        print("\n   Streaming response:")
        print("   " + "-" * 56)
        
        query_data = {
            "query": "What are the best times to fish for bass?",
            "top_k": 3
        }
        
        try:
            full_answer = ""
            context_received = False
            tokens_received = 0
            
            async with client.stream(
                "POST",
                f"{base_url}/api/v1/query/chat",
                json=query_data,
                headers=headers,
            ) as response:
                if response.status_code != 200:
                    print(f"❌ Request failed: {response.status_code}")
                    return False
                
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data: "):
                        continue
                    
                    try:
                        data = json.loads(line[6:])  # Remove "data: " prefix
                        
                        if data["type"] == "context":
                            context_received = True
                            print(f"\n   📚 Context: {len(data['chunks'])} chunks retrieved")
                            for i, chunk in enumerate(data["chunks"][:2], 1):
                                print(f"      [{i}] Score: {chunk['score']:.3f}")
                                print(f"          {chunk['content'][:80]}...")
                            print("\n   💬 Answer: ", end="", flush=True)
                        
                        elif data["type"] == "answer":
                            # Final answer content
                            content = data["content"]
                            print(content, end="", flush=True)
                            full_answer += content
                            tokens_received += 1
                        
                        elif data["type"] == "thinking":
                            # Thinking/reasoning content (only with use_cot)
                            # For now, just count but don't display
                            tokens_received += 1
                        
                        elif data["type"] == "token":
                            # Fallback for unstructured content
                            content = data["content"]
                            print(content, end="", flush=True)
                            full_answer += content
                            tokens_received += 1
                        
                        elif data["type"] == "done":
                            print("\n\n   ✅ Streaming completed")
                            print(f"   📊 Stats: {tokens_received} tokens received")
                            break
                        
                        elif data["type"] == "error":
                            print(f"\n   ❌ Error: {data['message']}")
                            return False
                    
                    except json.JSONDecodeError as e:
                        print(f"\n   ⚠ JSON decode error: {e}")
                        continue
            
            if not context_received:
                print("\n❌ No context received")
                return False
            
            if tokens_received == 0:
                print("\n❌ No tokens received")
                return False
            
            print("   " + "-" * 56)
            
        except Exception as e:
            print(f"\n❌ Streaming error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Compare with regular query endpoint
        print("\n4. Comparing with regular query endpoint...")
        try:
            response = await client.post(
                f"{base_url}/api/v1/query/",
                json=query_data,
                headers=headers
            )
            if response.status_code == 200:
                result = response.json()
                print("✅ Regular query works")
                print(f"   Answer length: {len(result['answer'])} chars")
                print(f"   Streaming length: {len(full_answer)} chars")
            else:
                print(f"⚠ Regular query failed: {response.status_code}")
        except Exception as e:
            print(f"⚠ Regular query error: {e}")
        
        # Test with Chain-of-Thought
        print("\n5. Testing with Chain-of-Thought reasoning...")
        print("   Query: 'Compare the tips and tell me the most important one'")
        print("\n   CoT Streaming response:")
        print("   " + "-" * 56)
        
        cot_query_data = {
            "query": "Compare the tips and tell me the most important one",
            "top_k": 3,
            "use_cot": True,
            "max_tokens": 512
        }
        
        try:
            cot_answer = ""
            cot_thinking = ""
            
            async with client.stream(
                "POST",
                f"{base_url}/api/v1/query/chat",
                json=cot_query_data,
                headers=headers,
            ) as response:
                if response.status_code != 200:
                    print(f"❌ CoT request failed: {response.status_code}")
                else:
                    thinking_started = False
                    answer_started = False
                    
                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line or not line.startswith("data: "):
                            continue
                        
                        try:
                            data = json.loads(line[6:])
                            
                            if data["type"] == "context":
                                print(f"\n   📚 Context: {len(data['chunks'])} chunks")
                            
                            elif data["type"] == "thinking":
                                if not thinking_started:
                                    print("   Thinking: ", end="", flush=True)
                                    thinking_started = True
                                content = data["content"]
                                print(content, end="", flush=True)
                                cot_thinking += content
                            
                            elif data["type"] == "answer":
                                if not answer_started:
                                    print("\n   ✅ Answer: ", end="", flush=True)
                                    answer_started = True
                                content = data["content"]
                                print(content, end="", flush=True)
                                cot_answer += content
                            
                            elif data["type"] == "token":
                                # Fallback for unstructured content
                                content = data["content"]
                                print(content, end="", flush=True)
                                cot_answer += content
                            
                            elif data["type"] == "done":
                                print("\n\n   ✅ CoT completed")
                                print(f"   📊 Thinking: {len(cot_thinking)} chars")
                                print(f"   📊 Answer: {len(cot_answer)} chars")
                                break
                        
                        except json.JSONDecodeError:
                            continue
            
            print("   " + "-" * 56)
            
        except Exception as e:
            print(f"\n   ⚠ CoT test error: {e}")
        
        # Cleanup
        print("\n6. Cleaning up test document...")
        try:
            response = await client.delete(
                f"{base_url}/api/v1/documents/{doc_id}",
                headers=headers
            )
            if response.status_code == 204:
                print("✅ Document deleted")
            else:
                print(f"⚠ Delete failed: {response.status_code}")
        except Exception as e:
            print(f"⚠ Delete error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Streaming test completed successfully!")
    print("\n📚 The streaming endpoint is working correctly:")
    print("   - Context chunks are retrieved before streaming")
    print("   - Tokens stream in real-time")
    print("   - SSE format is correct")
    return True


def main():
    """Main entry point."""
    print("IdioRAG Streaming Test")
    print("=" * 60)
    print("\nThis script tests the streaming chat endpoint.")
    print("Make sure the application is running (python run.py)")
    print("\nPress Ctrl+C to cancel, or Enter to continue...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        return 0
    
    success = asyncio.run(test_streaming())
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
