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

    def __init__(
        self, 
        user_id: str, 
        email: str | None = None, 
        username: str | None = None,
        claims: Dict[str, Any] | None = None
    ):
        """Initialize user context.
        
        Args:
            user_id: Unique user identifier (numeric ID)
            email: User email address
            username: Username for display/logging
            claims: Additional JWT claims
        """
        self.user_id = user_id
        self.email = email
        self.username = username
        self.claims = claims or {}

    def __repr__(self) -> str:
        return f"UserContext(user_id={self.user_id}, username={self.username}, email={self.email})"


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
    
    logger.info(f"Attempting to decode JWT token (length: {len(token)})")
    logger.debug(f"Token preview: {token[:50]}...")
    
    try:
        # Determine the key to use based on algorithm
        logger.debug(f"Using JWT algorithm: {settings.jwt_algorithm}")
        
        if settings.jwt_algorithm.upper() == "RS256":
            if not settings.jwt_public_key:
                logger.error("RS256 algorithm specified but no public key provided")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="JWT public key not configured",
                )
            key = settings.jwt_public_key
            logger.debug("Using RS256 with public key")
        else:  # HS256 or other symmetric algorithms
            key = settings.jwt_secret_key
            logger.debug(f"Using {settings.jwt_algorithm} with secret key")

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
        
        logger.info(f"JWT token decoded successfully")
        logger.debug(f"JWT payload keys: {list(payload.keys())}")
        logger.debug(f"JWT payload (sensitive data hidden): {', '.join(payload.keys())}")
        
        # Check expiration manually for better error messages
        exp = payload.get("exp")
        if exp:
            exp_time = datetime.fromtimestamp(exp, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            logger.debug(f"Token expiration: {exp_time}, Current time: {now}")
            
            if exp_time < now:
                logger.warning("Token has expired")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        return payload
    
    except JWTError as e:
        logger.error(f"JWT validation failed: {type(e).__name__}: {str(e)}")
        logger.debug(f"Token that failed: {token[:50]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error during JWT decode: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


def extract_user_context(payload: Dict[str, Any]) -> UserContext:
    """Extract user context from JWT payload.
    
    This function should be customized based on your JWT structure.
    Common claim names:
    - user_id: sub, user_id, userId, id, nameidentifier
    - username: name, preferred_username, unique_name, username
    - email: email, user_email
    
    Args:
        payload: Decoded JWT payload
    
    Returns:
        UserContext object
    
    Raises:
        HTTPException: If required claims are missing
    """
    logger.debug(f"Extracting user context from payload with keys: {list(payload.keys())}")
    
    # Try to extract user_id from common claim names (including ASP.NET claims)
    user_id = (
        payload.get("sub") or 
        payload.get("user_id") or 
        payload.get("userId") or 
        payload.get("id") or
        payload.get("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier")
    )
    
    if not user_id:
        logger.error(f"No user_id found in JWT payload!")
        logger.error(f"Available claims: {list(payload.keys())}")
        logger.error(f"Tried to find user_id in: 'sub', 'user_id', 'userId', 'id', 'nameidentifier'")
        # Log some sample values (be careful not to log sensitive data in production)
        for key in ["sub", "user_id", "userId", "id"]:
            logger.debug(f"  {key}: {payload.get(key)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token",
        )
    
    logger.info(f"Found user_id: {user_id}")
    
    # Extract username (for logging/display)
    username = (
        payload.get("name") or
        payload.get("preferred_username") or
        payload.get("unique_name") or
        payload.get("username") or
        payload.get("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name")
    )
    if username:
        logger.info(f"Found username: {username}")
    else:
        logger.debug("No username claim found in token")
    
    # Extract email (optional)
    email = (
        payload.get("email") or 
        payload.get("user_email") or
        payload.get("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress")
    )
    if email:
        logger.debug(f"Found email: {email}")
    else:
        logger.debug("No email claim found in token")
    
    return UserContext(
        user_id=str(user_id),
        email=email,
        username=username,
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
    
    logger.info("Authentication request received")
    
    payload = decode_jwt_token(token)
    user = extract_user_context(payload)
    
    if user.username:
        logger.info(f"Authentication successful for user: {user.user_id} ({user.username})")
    else:
        logger.info(f"Authentication successful for user: {user.user_id}")
    
    return user


# Type alias for dependency injection
CurrentUser = Annotated[UserContext, Depends(get_current_user)]
