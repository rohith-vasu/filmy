from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.model_handlers.user_handler import UserHandler, UserUpdate, UserResponse
from app.dependencies.auth import get_current_user
from app.core.db import get_global_db_session
from app.core.qdrant import get_qdrant_client
from app.routes import AppResponse
from app.utils.auth import verify_password, hash_password

user_router = APIRouter(prefix="/users", tags=["users"])

@user_router.get("/", response_model=AppResponse)
async def get_users(skip: int = 0, limit: int = 20, db: Session = Depends(get_global_db_session)):
    """Get all users with pagination"""
    user_handler = UserHandler(db)
    return AppResponse(
        status="success",
        message="Users fetched successfully",
        data=user_handler.list_all(skip, limit)
    )

@user_router.get("/{user_id}", response_model=AppResponse)
async def get_user(user_id: str, db: Session = Depends(get_global_db_session)):
    """Get a specific user by ID"""
    user_handler = UserHandler(db)
    user = user_handler.read(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return AppResponse(
        status="success",
        message="User fetched successfully",
        data=user
    )

@user_router.patch("/{user_id}", response_model=AppResponse)
async def update_user(
    user_id: str, user_update: UserUpdate, 
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_global_db_session)
):
    """Update a user's information"""
    user_handler = UserHandler(db)
    user = user_handler.read(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Only allow updating own profile
    if user.id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return AppResponse(
        status="success",
        message="User updated successfully",
        data=user_handler.update(user_id, user_update)
    )

@user_router.post("/change-password", response_model=AppResponse)
async def change_password(
    current_password: str,
    new_password: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_global_db_session)
):
    user_handler = UserHandler(db)
    user = user_handler.read(current_user.id)
    
    if not verify_password(current_password, user.password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    hashed_new = hash_password(new_password)
    user_handler.update(user.id, UserUpdate(hashed_password=hashed_new))
    
    return AppResponse(
        status="success",
        message="Password changed successfully"
    )

@user_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str, 
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_global_db_session)
):
    """Delete a user"""
    user_handler = UserHandler(db)
    user = user_handler.read(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Only allow deleting own account
    if user.id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Delete all sessions and documents associated with the user
    user_handler.delete(user_id)
    return AppResponse(
        status="success",
        message="User deleted successfully"
    )