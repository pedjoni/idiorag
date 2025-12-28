"""JWT authentication and authorization."""

from datetime import datetime, timezone
from typing import Annotated, Any, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from .config import get_settings
from .logging_config import get_logger

logger = get_logger(__name__)
security = HTTPBearer()


class UserContext:
    """User context extracted from JWT token."""

    def __init__(self, user_id: str, email: str | None = None, claims: Dict[str, Any] | None = None):
        """Initialize user context.
        
        Args:
            user_id: Unique user identifier
            email: User email address
            claims: Additional JWT claims
        """
        self.user_id = user_id
        self.email = email
        self.claims = claims or {}

    def __repr__(self) -> str:
        return f"UserContext(user_id={self.user_id}, email={self.email})"


def decode_jwt_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Dict containing JWT claims
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    settings = get_settings()
    
    try:
        # Determine the key to use based on algorithm
        if settings.jwt_algorithm.upper() == "RS256":
            if not settings.jwt_public_key:
                logger.error("RS256 algorithm specified but no public key provided")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="JWT public key not configured",
                )
            key = settings.jwt_public_key
        else:  # HS256 or other symmetric algorithms
            key = settings.jwt_secret_key

        # Decode and validate the token
        payload = jwt.decode(
            token,
            key,
            algorithms=[settings.jwt_algorithm],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": False,  # Adjust based on your JWT configuration
            },
        )
        
        # Check expiration manually for better error messages
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
    
    except JWTError as e:
        logger.warning(f"JWT validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def extract_user_context(payload: Dict[str, Any]) -> UserContext:
    """Extract user context from JWT payload.
    
    This function should be customized based on your JWT structure.
    Common claim names:
    - user_id: sub, user_id, userId, id
    - email: email, user_email
    
    Args:
        payload: Decoded JWT payload
    
    Returns:
        UserContext object
    
    Raises:
        HTTPException: If required claims are missing
    """
    # Try to extract user_id from common claim names
    user_id = payload.get("sub") or payload.get("user_id") or payload.get("userId") or payload.get("id")
    
    if not user_id:
        logger.error(f"No user_id found in JWT payload: {list(payload.keys())}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token",
        )
    
    # Extract email (optional)
    email = payload.get("email") or payload.get("user_email")
    
    return UserContext(
        user_id=str(user_id),
        email=email,
        claims=payload,
    )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> UserContext:
    """FastAPI dependency to extract current user from JWT token.
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: UserContext = Depends(get_current_user)):
            return {"user_id": user.user_id}
    
    Args:
        credentials: HTTP Bearer token credentials
    
    Returns:
        UserContext: Current user context
    """
    token = credentials.credentials
    payload = decode_jwt_token(token)
    user = extract_user_context(payload)
    
    logger.debug(f"Authenticated user: {user.user_id}")
    return user


# Type alias for dependency injection
CurrentUser = Annotated[UserContext, Depends(get_current_user)]
