#!/usr/bin/env python3
"""Helper script to inspect JWT tokens from your fishing app.

This helps verify that your JWT tokens contain the required claims.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import json
from jose import jwt


def inspect_token(token: str, verify_signature: bool = False):
    """Decode and inspect a JWT token without verification.
    
    Args:
        token: JWT token string
        verify_signature: If True, will attempt to verify signature (requires key)
    """
    print("=" * 80)
    print("JWT TOKEN INSPECTOR")
    print("=" * 80)
    print()
    
    print(f"Token length: {len(token)} characters")
    print(f"Token preview: {token[:50]}...")
    print()
    
    try:
        # Decode without verification to inspect claims
        payload = jwt.decode(
            token,
            options={
                "verify_signature": False,
                "verify_exp": False,
                "verify_aud": False,
            }
        )
        
        print("✅ Token successfully decoded (without verification)")
        print()
        print("-" * 80)
        print("PAYLOAD CLAIMS:")
        print("-" * 80)
        print(json.dumps(payload, indent=2, default=str))
        print()
        
        print("-" * 80)
        print("USER ID DETECTION:")
        print("-" * 80)
        
        # Check for user_id in various claim names
        user_id_claims = {
            "sub": payload.get("sub"),
            "user_id": payload.get("user_id"),
            "userId": payload.get("userId"),
            "id": payload.get("id"),
        }
        
        found_user_id = None
        for claim_name, value in user_id_claims.items():
            if value:
                print(f"✅ Found in '{claim_name}': {value}")
                if not found_user_id:
                    found_user_id = value
            else:
                print(f"❌ Not found in '{claim_name}'")
        
        print()
        
        if found_user_id:
            print(f"✅ SUCCESS: IdioRAG will use user_id: {found_user_id}")
        else:
            print("❌ PROBLEM: No user_id found in any expected claim!")
            print()
            print("Available claims in your token:")
            for key in payload.keys():
                print(f"  - {key}: {payload[key]}")
            print()
            print("SOLUTION: You need to add one of these claims to your JWT:")
            print("  - 'sub' (standard JWT claim for user identifier)")
            print("  - 'user_id' or 'userId' or 'id'")
        
        print()
        print("-" * 80)
        print("EMAIL DETECTION:")
        print("-" * 80)
        
        email = payload.get("email") or payload.get("user_email")
        if email:
            print(f"✅ Found email: {email}")
        else:
            print("⚠️  No email found (optional, but recommended)")
        
        print()
        print("-" * 80)
        print("EXPIRATION CHECK:")
        print("-" * 80)
        
        if "exp" in payload:
            from datetime import datetime, timezone
            exp_timestamp = payload["exp"]
            exp_time = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            
            print(f"Expires at: {exp_time}")
            print(f"Current time: {now}")
            
            if exp_time > now:
                remaining = exp_time - now
                print(f"✅ Token is valid (expires in {remaining})")
            else:
                print(f"❌ Token is EXPIRED")
        else:
            print("⚠️  No expiration claim (exp) found")
        
        print()
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ ERROR: Failed to decode token: {e}")
        print()
        print("This could mean:")
        print("  1. Invalid JWT format")
        print("  2. Token is corrupted")
        print("  3. Token is not a valid JWT")


def main():
    """Main entry point."""
    print()
    print("JWT Token Inspector for IdioRAG")
    print()
    
    if len(sys.argv) > 1:
        # Token provided as command line argument
        token = sys.argv[1]
        inspect_token(token)
    else:
        # Interactive mode
        print("Paste your JWT token below (or provide it as a command line argument):")
        print()
        token = input("JWT Token: ").strip()
        print()
        
        if not token:
            print("❌ No token provided")
            return
        
        inspect_token(token)
    
    print()
    print("NEXT STEPS:")
    print("-" * 80)
    print("1. Make sure your JWT token includes one of: 'sub', 'user_id', 'userId', or 'id'")
    print("2. Configure IdioRAG's JWT settings in .env:")
    print("   - JWT_SECRET_KEY (for HS256) or JWT_PUBLIC_KEY (for RS256)")
    print("   - JWT_ALGORITHM (default: HS256)")
    print("3. Restart IdioRAG and try again")
    print("4. Check IdioRAG logs for authentication messages")
    print()


if __name__ == "__main__":
    main()
