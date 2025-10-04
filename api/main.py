import os
from fastapi import FastAPI, HTTPException, Depends, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

app = FastAPI(title="Donna Backend API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://donna-web-app-chi.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_TOKEN = os.getenv("API_TOKEN")

if not API_TOKEN:
    raise ValueError("API_TOKEN environment variable is required")

security = HTTPBearer()

async def verify_token(authorization: Optional[str] = Header(None)):
    """
    Verify the authorization token from the request header.
    Expected format: Bearer <token>
    """
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

@app.get("/")
async def read_root():
    return {"message": "Hello World"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

# Protected route example 1: Simple protected endpoint
@app.get("/protected")
async def protected_route(token: str = Depends(verify_token)):
    return {
        "message": "This is a protected endpoint", 
        "authenticated": True,
        "user": "NextJS Backend"
    }

# Protected route example 2: Protected endpoint with data
@app.get("/protected/data")
async def get_protected_data(token: str = Depends(verify_token)):
    return {
        "data": [
            {"id": 1, "name": "Item 1", "value": "Secret data 1"},
            {"id": 2, "name": "Item 2", "value": "Secret data 2"},
        ],
        "message": "Protected data retrieved successfully"
    }

# Protected route example 3: POST endpoint
@app.post("/protected/create")
async def create_item(item_data: dict, token: str = Depends(verify_token)):
    return {
        "message": "Item created successfully",
        "created_item": item_data,
        "authenticated_user": "NextJS Backend"
    }