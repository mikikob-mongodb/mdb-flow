"""Data models for Flow Companion."""

from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class ActivityLogEntry(BaseModel):
    """Activity log entry for tracking changes."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action: str
    note: Optional[str] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class Task(BaseModel):
    """Task data model."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    title: str
    status: Literal["todo", "in_progress", "done"] = "todo"
    priority: Optional[Literal["low", "medium", "high"]] = None
    project_id: Optional[PyObjectId] = None
    context: str = ""
    notes: List[str] = Field(default_factory=list)
    activity_log: List[ActivityLogEntry] = Field(default_factory=list)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_worked_on: Optional[datetime] = None

    # Vector embedding (1024 dimensions for voyage-3)
    embedding: Optional[List[float]] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

    def to_mongo(self) -> dict:
        """Convert to MongoDB document format."""
        data = self.model_dump(by_alias=True, exclude_none=True)
        if self.id is None and "_id" in data:
            del data["_id"]
        return data


class Project(BaseModel):
    """Project data model."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str
    description: str = ""
    status: Literal["active", "archived"] = "active"
    context: str = ""
    notes: List[str] = Field(default_factory=list)
    methods: List[str] = Field(default_factory=list)  # Technologies/approaches
    decisions: List[str] = Field(default_factory=list)
    activity_log: List[ActivityLogEntry] = Field(default_factory=list)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: Optional[datetime] = None

    # Vector embedding (1024 dimensions for voyage-3)
    embedding: Optional[List[float]] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

    def to_mongo(self) -> dict:
        """Convert to MongoDB document format."""
        data = self.model_dump(by_alias=True, exclude_none=True)
        if self.id is None and "_id" in data:
            del data["_id"]
        return data


class Settings(BaseModel):
    """User settings data model."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: str = "default"
    current_task_id: Optional[PyObjectId] = None
    current_project_id: Optional[PyObjectId] = None
    context_set_at: Optional[datetime] = None
    default_project_id: Optional[PyObjectId] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

    def to_mongo(self) -> dict:
        """Convert to MongoDB document format."""
        data = self.model_dump(by_alias=True, exclude_none=True)
        if self.id is None and "_id" in data:
            del data["_id"]
        return data
