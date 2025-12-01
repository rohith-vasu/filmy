from datetime import datetime, timezone
from typing import Type, TypeVar, List, Generic

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

# Type variables for models
SqlModelType = TypeVar("SqlModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)


class CRUDManager(Generic[SqlModelType, CreateSchemaType, UpdateSchemaType, ResponseSchemaType]):
    def __init__(
        self, db: Session, model: Type[SqlModelType], response_schema: Type[BaseModel]
    ):
        self._db = db
        self._model = model
        self._response_schema = response_schema

    def create(self, obj_in: CreateSchemaType) -> ResponseSchemaType:
        """
        Create a new record.
        """
        db_obj = self._model(
            **obj_in.dict(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self._db.add(db_obj)
        self._db.commit()
        self._db.refresh(db_obj)
        return self._response_schema.model_validate(db_obj)

    def read(self, id: int) -> ResponseSchemaType:
        """
        Get a single record by ID.
        """
        try:
            db_obj = self._db.query(self._model).filter(self._model.id == id).one()
            return self._response_schema.model_validate(db_obj)
        except NoResultFound:
            raise HTTPException(status_code=404, detail="Record not found")

    def update(self, id: int, obj_in: UpdateSchemaType) -> ResponseSchemaType:
        """
        Update an existing record.
        """
        db_obj = (
            self._db.query(self._model).filter(self._model.id == id).one()
        )
        if not db_obj:
            raise Exception(
                f"Handler Update: Requested id: {id} not found in {self._model.__tablename__}"
            )
        update_data = obj_in.dict(
            exclude_unset=True, exclude_none=True
        )  # Update only the provided fields
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db_obj.updated_at = datetime.now(timezone.utc)  # Update timestamp
        self._db.commit()
        self._db.refresh(db_obj)
        return self._response_schema.model_validate(db_obj)

    def delete(self, id: int) -> dict:
        """
        Delete a record by ID.
        """
        db_obj = self._db.query(self._model).filter(self._model.id == id).one()
        if not db_obj:
            raise Exception(
                f"Handler Delete: Requested id: {id} not found in {self._model.__tablename__}"
            )
        self._db.delete(db_obj)
        self._db.commit()
        return {"id": id}

    def list_all(self, skip: int = 0, limit: int = 20) -> List[ResponseSchemaType]:
        """
        List all records.
        """
        db_objs = self._db.query(self._model).offset(skip).limit(limit).all()
        return [self._response_schema.model_validate(db_obj) for db_obj in db_objs]