import os
from typing import Optional
from fastapi import HTTPException, status, Header


async def verify_token(authorization: Optional[str] = Header(None)):
    """
    Verify the authorization token from the request header.
    Expected format: Bearer <token>
    """
    API_TOKEN = os.getenv("API_TOKEN")
    
    if not API_TOKEN:
        raise ValueError("API_TOKEN environment variable is required")
    
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if the header starts with "Bearer "
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization[7:]  # Remove "Bearer " prefix
    
    # Verify the token
    if token != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token
