"""
Pydantic Models – request/response schemas
"""

from typing import List, Optional
from pydantic import BaseModel


class Task(BaseModel):
    task: str
    owner: str = "Unassigned"
    priority: str = "Medium"   # High / Medium / Low
    due_date: str = "Not specified"
    status: str = "Pending"


class MeetingResponse(BaseModel):
    meeting_id: int
    title: str
    transcript: str
    summary: str
    tasks: List[Task]
    action_items: List[str]


class TranscriptInput(BaseModel):
    transcript: str
    meeting_title: Optional[str] = "Untitled Meeting"
