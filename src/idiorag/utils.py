"""Utility functions for testing and development."""

from datetime import datetime, timedelta, timezone
from typing import Dict

from jose import jwt

from .config import get_settings


def generate_test_token(
    user_id: str = "5",
    email: str = "peja@pjcode.com",
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


def format_fishing_log_content(
    date: str,
    location: str,
    weather: str,
    events: list,
    comments: str = "",
) -> str:
    """Format fishing log data into a well-structured text.
    
    Args:
        date: Log date
        location: Fishing location
        weather: Weather description
        events: List of event dictionaries
        comments: Additional comments
    
    Returns:
        str: Formatted fishing log content
    """
    content = f"""Fishing Log: {date}
Location: {location}
Weather: {weather}

"""
    
    if comments:
        content += f"Comments: {comments}\n\n"
    
    content += "Events:\n"
    for i, event in enumerate(events, 1):
        content += f"\n{i}. {event['type'].upper()} - {event.get('time', 'N/A')}\n"
        
        if 'species' in event:
            content += f"   - Species: {event['species']}\n"
        if 'size' in event:
            content += f"   - Size: {event['size']}\n"
        if 'lure' in event:
            content += f"   - Lure: {event['lure']}\n"
        if 'structure' in event:
            content += f"   - Structure: {event['structure']}\n"
        if 'details' in event:
            content += f"   - Details: {event['details']}\n"
    
    return content


if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add parent directory to path for direct execution
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    from idiorag.config import get_settings
    
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
