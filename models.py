from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Title")
    description: Optional[str] = Field(None, max_length=1000, description="Description")


class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    completed: Optional[bool] = None

class Task(TaskBase):
    id: int = Field(..., description = "ID of task")
    completed: bool = Field(default=False, description="Completed status")
    created_at: datetime = Field(..., description="Created task")
    updated_at: datetime = Field(..., description="Updated task")

    model_config = ConfigDict(
        from_attributes=True
    )