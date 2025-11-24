from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound

from . import CRUDManager
from app.models.users import User


class UserCreate(BaseModel):
    email: str = Field(..., description="User's email address")
    firstname: str = Field(..., description="User's firstname")
    lastname: str = Field(..., description="User's lastname")
    hashed_password: str = Field(..., description="User's password")
    genre_preferences: Optional[str] = Field(None, description="User's genre preferences")

class UserUpdate(BaseModel):
    email: Optional[str] = Field(None, description="User's email address")
    firstname: Optional[str] = Field(None, description="User's firstname")
    lastname: Optional[str] = Field(None, description="User's lastname")
    hashed_password: Optional[str] = Field(None, description="User's password")
    genre_preferences: Optional[str] = Field(None, description="User's genre preferences")

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="Unique identifier for the user")
    email: str = Field(..., description="User's email address")
    firstname: str = Field(..., description="User's firstname")
    lastname: str = Field(..., description="User's lastname")
    hashed_password: Optional[str] = Field(None, description="User's password")
    genre_preferences: Optional[str] = Field(None, description="User's genre preferences")
    created_at: datetime = Field(..., description="Timestamp of user creation")


class UserHandler(CRUDManager[User, UserCreate, UserUpdate, UserResponse]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=User, response_schema=UserResponse)

    def create(self, obj_in: UserCreate) -> UserResponse:
        return super().create(obj_in)

    def read(self, id: int) -> UserResponse:
        return super().read(id)
        
    def update(self, id: int, obj_in: UserUpdate) -> UserResponse:
        return super().update(id, obj_in)
        
    def delete(self, id: int) -> dict:
        return super().delete(id)
    
    def list_all(self, skip: int = 0, limit: int = 20) -> List[UserResponse]:
        return super().list_all(skip, limit)

    def get_by_email(self, email: str, with_password: bool = False) -> Optional[UserResponse]:
        """Get user by email."""
        try:
            user = self._db.query(User).filter(User.email == email).one()
            user_data = self._response_schema.model_validate(user).model_dump()

            if not with_password:
                user_data.pop("hashed_password", None)

            return UserResponse(**user_data)
        except NoResultFound:
            return None

    def get_by_id(self, id: int) -> UserResponse:
        user = self._db.query(User).filter(User.id == id).one()
        return self._response_schema.model_validate(user)
