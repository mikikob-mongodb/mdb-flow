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

    # Test data flag (for filtering test data from production queries)
    is_test: bool = False

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

    # Test data flag (for filtering test data from production queries)
    is_test: bool = False

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


class ShortTermMemory(BaseModel):
    """Short-term memory for session context and working memory.

    TTL: 2 hours
    Use cases:
    - Current project/task context
    - Recent conversation topics
    - Temporary working state
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    session_id: str  # Session identifier
    agent: str  # Agent name that wrote this memory
    content: dict = Field(default_factory=dict)  # Memory content

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime  # Set to created_at + 2 hours

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


class LongTermMemory(BaseModel):
    """Long-term memory for persistent action history and learned facts.

    TTL: None (persistent)
    Use cases:
    - Action history (what tasks were completed when)
    - User preferences and patterns
    - Important facts and decisions
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: str = "default"  # User identifier
    type: Literal["action", "fact", "preference"] = "action"  # Memory type
    content: dict = Field(default_factory=dict)  # Memory content (structured)
    tags: List[str] = Field(default_factory=list)  # Tags for categorization
    embedding: Optional[List[float]] = None  # Vector embedding for semantic search

    # Memory strength and access tracking
    strength: float = 1.0  # Memory strength (for decay algorithms)
    access_count: int = 0  # How many times accessed
    last_accessed: datetime = Field(default_factory=datetime.utcnow)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

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


class SharedMemory(BaseModel):
    """Shared memory for agent-to-agent communication and handoffs.

    TTL: 5 minutes
    Use cases:
    - Passing context between agents
    - Multi-step workflows (retrieval → worklog)
    - Temporary data sharing
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    session_id: str  # Session identifier
    from_agent: str  # Source agent (e.g., "retrieval", "worklog")
    to_agent: str  # Target agent
    content: dict = Field(default_factory=dict)  # Handoff content
    status: Literal["pending", "consumed"] = "pending"  # Handoff status

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime  # Set to created_at + 5 minutes
    consumed_at: Optional[datetime] = None

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
