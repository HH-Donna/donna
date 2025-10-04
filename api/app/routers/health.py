from fastapi import APIRouter, Depends
from app.auth import verify_token

router = APIRouter()


@router.get("/")
async def read_root():
    return {"message": "Hello World"}


@router.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}


# Protected route examples
@router.get("/protected")
async def protected_route(token: str = Depends(verify_token)):
    return {
        "message": "This is a protected endpoint", 
        "authenticated": True,
        "user": "NextJS Backend"
    }


@router.get("/protected/data")
async def get_protected_data(token: str = Depends(verify_token)):
    return {
        "data": [
            {"id": 1, "name": "Item 1", "value": "Secret data 1"},
            {"id": 2, "name": "Item 2", "value": "Secret data 2"},
        ],
        "message": "Protected data retrieved successfully"
    }


@router.post("/protected/create")
async def create_item(item_data: dict, token: str = Depends(verify_token)):
    return {
        "message": "Item created successfully",
        "created_item": item_data,
        "authenticated_user": "NextJS Backend"
    }
