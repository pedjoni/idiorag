"""Utility functions for testing and development."""

from datetime import datetime, timedelta, timezone
from typing import Dict

from jose import jwt

from .config import get_settings


def generate_test_token(
    user_id: str = "test_user_123",
    email: str = "test@example.com",
    expires_in_minutes: int = 60,
) -> str:
    """Generate a test JWT token for development.
    
    Args:
        user_id: User identifier
        email: User email
        expires_in_minutes: Token expiration time in minutes
    
    Returns:
        str: Encoded JWT token
    """
    settings = get_settings()
    
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=expires_in_minutes)
    
    payload = {
        "sub": user_id,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
    }
    
    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    
    return token


def decode_test_token(token: str) -> Dict:
    """Decode a JWT token for inspection.
    
    Args:
        token: JWT token string
    
    Returns:
        Dict: Decoded token payload
    """
    settings = get_settings()
    
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        options={"verify_exp": False},  # Don't fail on expired tokens
    )
    
    return payload


def format_structured_content(
    date: str,
    location: str,
    context: str,
    events: list,
    notes: str = "",
) -> str:
    """Format structured data into a well-organized text.
    
    Args:
        date: Entry date
        location: Location description
        context: Contextual information (e.g., weather, conditions)
        events: List of event dictionaries
        notes: Additional notes
    
    Returns:
        str: Formatted content
    """
    content = f"""Entry: {date}
Location: {location}
Context: {context}

"""
    
    if notes:
        content += f"Notes: {notes}\n\n"
    
    content += "Events:\n"
    for i, event in enumerate(events, 1):
        content += f"\n{i}. {event['type'].upper()} - {event.get('time', 'N/A')}\n"
        
        # Add any additional event fields dynamically
        for key, value in event.items():
            if key not in ['type', 'time']:
                content += f"   - {key.replace('_', ' ').title()}: {value}\n"
    
    return content


if __name__ == "__main__":
    # Generate a test token
    token = generate_test_token()
    print("Test JWT Token:")
    print(token)
    print("\nDecoded:")
    print(decode_test_token(token))
    
    # Example fishing log
    print("\n" + "="*60)
    print("Example Fishing Log Content:")
    print("="*60)
    
    log = format_fishing_log_content(
        date="2024-01-15",
        location="Lake Michigan, North Shore",
        weather="Sunny, 65°F, Wind 5-10 mph NW",
        comments="Great morning bite, fish were active near weed edges",
        events=[
            {
                "type": "catch",
                "time": "8:30 AM",
                "species": "Largemouth Bass",
                "size": "3.5 lbs",
                "lure": "Green Pumpkin Senko",
                "structure": "Weed edge, 8ft depth",
                "details": "Hit on the fall"
            },
            {
                "type": "follow",
                "time": "9:15 AM",
                "species": "Northern Pike",
                "lure": "Silver spoon",
                "structure": "Open water"
            }
        ]
    )
    print(log)
