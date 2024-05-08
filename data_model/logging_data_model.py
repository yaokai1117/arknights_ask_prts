from enum import Enum
from pydantic import BaseModel
from uuid import UUID
from .planner_data_model import PlannerOutput, ToolType
from .llm_data_model import Message
from typing import List, Optional

# Logging data models.


class SessionStatus(str, Enum):
    in_progress = 'in_progress'
    success = 'success'
    fail = 'fail'


class LogEntry(BaseModel):
    session_id: UUID
    status: SessionStatus
    error: Optional[str] = None
    initial_message: str
    final_response: Optional[str] = None
    messages: List[Message] = []
    planner_output: Optional[PlannerOutput] = None
    graphql_queries: List[str] = []
    graphql_results: List[dict] = []
    story_rag_query: str = None
    story_rag_result: str = None
    fall_back_tool: Optional[ToolType] = None

    class Config:
        use_enum_values = True
