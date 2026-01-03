"""Data models for Flow Companion."""

from datetime import datetime
from typing import List, Optional, Literal, Annotated, Any
from pydantic import BaseModel, Field, BeforeValidator
from bson import ObjectId


def validate_object_id(v: Any) -> ObjectId:
    """Validate and convert to ObjectId for Pydantic v2."""
    if isinstance(v, ObjectId):
        return v
    if ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError("Invalid ObjectId")


# Pydantic v2 compatible ObjectId type using Annotated
PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]


class ActivityLogEntry(BaseModel):
    """Activity log entry for tracking changes."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action: str
    note: Optional[str] = None

    # Voice-specific fields
    summary: Optional[str] = None  # Cleaned summary for voice_update
    raw_transcript: Optional[str] = None  # Original speech transcript
    extracted: Optional[dict] = None  # Parsed voice structure

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
