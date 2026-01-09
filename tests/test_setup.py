"""Simple test script to verify setup."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from idiorag import __version__
        print(f"✓ idiorag version: {__version__}")
        
        from idiorag.config import get_settings
        print("✓ config module loaded")
        
        from idiorag.auth import UserContext
        print("✓ auth module loaded")
        
        from idiorag.database import Document
        print("✓ database module loaded")
        
        from idiorag.main import app
        print("✓ FastAPI app created")
        
        print("\n✅ All imports successful!")
        return True
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        return False


def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")
    
    try:
        from idiorag.config import get_settings
        
        # Check if .env exists
        if not Path(".env").exists():
            print("⚠ .env file not found (using defaults)")
        
        settings = get_settings()
        print(f"✓ App name: {settings.app_name}")
        print(f"✓ Environment: {settings.environment}")
        print(f"✓ API prefix: {settings.api_v1_prefix}")
        
        # Check required settings (will use defaults if not set)
        print(f"✓ Database URL configured: {bool(settings.database_url)}")
        print(f"✓ LLM URL configured: {bool(settings.llm_api_url)}")
        print(f"✓ JWT secret configured: {bool(settings.jwt_secret_key)}")
        
        print("\n✅ Configuration test passed!")
        return True
    except Exception as e:
        print(f"\n❌ Configuration test failed: {e}")
        return False


def test_jwt():
    """Test JWT encoding/decoding."""
    print("\nTesting JWT functionality...")
    
    try:
        from jose import jwt
        from idiorag.config import get_settings
        
        settings = get_settings()
        
        # Create a test token
        test_payload = {
            "sub": "test_user_123",
            "email": "test@example.com",
            "exp": 9999999999  # Far future
        }
        
        token = jwt.encode(
            test_payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
        
        print(f"✓ Token created: {token[:50]}...")
        
        # Decode it
        decoded = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        print(f"✓ Token decoded, user_id: {decoded['sub']}")
        print("\n✅ JWT test passed!")
        return True
    except Exception as e:
        print(f"\n❌ JWT test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("IdioRAG Setup Verification")
    print("=" * 60)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("JWT", test_jwt()))
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:20} {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All tests passed! You're ready to run the application.")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and configure your settings")
        print("2. Ensure PostgreSQL with pgvector is running")
        print("3. Run: python run.py")
        print("4. Visit: http://localhost:8000/docs")
    else:
        print("\n⚠ Some tests failed. Please check the errors above.")
        print("\nCommon issues:")
        print("- Missing .env file: Copy .env.example to .env")
        print("- Missing dependencies: Run 'pip install -r requirements.txt'")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
