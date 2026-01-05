"""Mock data factories for tests."""

from datetime import datetime, timedelta
from bson import ObjectId
from typing import List, Dict, Any, Optional
import random


class TaskFactory:
    """Factory for creating test tasks."""
    
    @staticmethod
    def create(
        title: str = "Test Task",
        context: str = "Test context",
        status: str = "todo",
        priority: Optional[str] = None,
        project_id: Optional[ObjectId] = None,
        project_name: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        activity_log: Optional[List[Dict]] = None,
        notes: Optional[List[Dict]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Create a test task."""
        task_id = ObjectId()
        now = datetime.utcnow()
        
        task = {
            "_id": task_id,
            "title": title,
            "context": context,
            "status": status,
            "created_at": created_at or now,
            "updated_at": updated_at or now,
        }
        
        if priority:
            task["priority"] = priority
        
        if project_id:
            task["project_id"] = project_id
        
        if project_name:
            task["project_name"] = project_name
        
        if embedding:
            task["embedding"] = embedding
        else:
            # Generate mock embedding
            task["embedding"] = [random.random() for _ in range(1024)]
        
        if activity_log:
            task["activity_log"] = activity_log
        else:
            task["activity_log"] = [
                {
                    "action": "created",
                    "timestamp": created_at or now
                }
            ]
        
        if notes:
            task["notes"] = notes
        else:
            task["notes"] = []
        
        return task
    
    @staticmethod
    def create_batch(count: int, **kwargs) -> List[Dict[str, Any]]:
        """Create multiple test tasks."""
        return [TaskFactory.create(**kwargs) for _ in range(count)]
    
    @staticmethod
    def create_with_project(project: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Create a task associated with a project."""
        return TaskFactory.create(
            project_id=project["_id"],
            project_name=project["name"],
            **kwargs
        )


class ProjectFactory:
    """Factory for creating test projects."""
    
    @staticmethod
    def create(
        name: str = "Test Project",
        description: str = "Test description",
        status: str = "active",
        embedding: Optional[List[float]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Create a test project."""
        project_id = ObjectId()
        now = datetime.utcnow()
        
        project = {
            "_id": project_id,
            "name": name,
            "description": description,
            "status": status,
            "created_at": created_at or now,
            "updated_at": updated_at or now,
        }
        
        if embedding:
            project["embedding"] = embedding
        else:
            # Generate mock embedding
            project["embedding"] = [random.random() for _ in range(1024)]
        
        return project
    
    @staticmethod
    def create_batch(count: int, **kwargs) -> List[Dict[str, Any]]:
        """Create multiple test projects."""
        return [ProjectFactory.create(**kwargs) for _ in range(count)]


class ConversationFactory:
    """Factory for creating test conversation histories."""
    
    @staticmethod
    def create_history(
        turns: int = 3,
        include_voice: bool = False,
        include_tool_calls: bool = True
    ) -> List[Dict[str, Any]]:
        """Create a multi-turn conversation history."""
        history = []
        
        for i in range(turns):
            # User message
            user_msg = {
                "role": "user",
                "content": f"Test query {i+1}"
            }
            if include_voice and i % 2 == 0:
                user_msg["input_type"] = "voice"
            
            history.append(user_msg)
            
            # Assistant message
            assistant_msg = {
                "role": "assistant",
                "content": f"Test response {i+1}"
            }
            
            if include_tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "name": "get_tasks",
                        "input": {"status": "in_progress"}
                    }
                ]
            
            history.append(assistant_msg)
        
        return history


class ActivityLogFactory:
    """Factory for creating activity log entries."""
    
    @staticmethod
    def create_entry(
        action: str = "created",
        timestamp: Optional[datetime] = None,
        **extra_fields
    ) -> Dict[str, Any]:
        """Create an activity log entry."""
        entry = {
            "action": action,
            "timestamp": timestamp or datetime.utcnow()
        }
        entry.update(extra_fields)
        return entry
    
    @staticmethod
    def create_timeline(
        actions: List[str],
        start_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Create a timeline of activity log entries."""
        if start_date is None:
            start_date = datetime.utcnow() - timedelta(days=7)
        
        timeline = []
        for i, action in enumerate(actions):
            timestamp = start_date + timedelta(hours=i*2)
            timeline.append(ActivityLogFactory.create_entry(action, timestamp))
        
        return timeline
